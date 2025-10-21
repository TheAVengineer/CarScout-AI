"""
Deduplication task - Detect and mark duplicates using multiple methods
"""
import hashlib
import logging
from typing import Optional, List, Tuple
from uuid import UUID
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import text

from workers.pipeline.celery_app import celery_app
from libs.domain.database import get_sync_session
from libs.domain.models import (
    ListingNormalized, 
    DedupeSignature, 
    DuplicateLog,
    Seller,
    Image
)
from workers.pipeline.tasks.price import estimate_price

logger = logging.getLogger(__name__)


class DeduplicationEngine:
    """Multi-method deduplication engine"""
    
    def __init__(self, session):
        self.session = session
    
    def generate_text_signature(self, listing: ListingNormalized) -> str:
        """Generate text-based signature for similarity matching"""
        # Combine key fields
        parts = []
        
        if listing.brand_id:
            parts.append(listing.brand_id.lower())
        if listing.model_id:
            parts.append(listing.model_id.lower())
        if listing.year:
            parts.append(str(listing.year))
        if listing.fuel:
            parts.append(listing.fuel.lower())
        if listing.gearbox:
            parts.append(listing.gearbox.lower())
        
        signature = ' '.join(parts)
        return signature
    
    def generate_description_hash(self, description: str) -> str:
        """Generate hash of description (first 500 chars)"""
        if not description:
            return None
        
        # Normalize: lowercase, remove extra spaces
        normalized = ' '.join(description.lower().split())[:500]
        return hashlib.md5(normalized.encode()).hexdigest()
    
    def check_phone_duplicate(self, listing: ListingNormalized) -> Optional[UUID]:
        """Check for duplicate based on phone hash"""
        if not listing.seller or not listing.seller.phone_hash:
            return None
        
        # Find listings with same phone hash, brand, model, similar price
        similar = self.session.query(ListingNormalized).join(Seller).filter(
            Seller.phone_hash == listing.seller.phone_hash,
            ListingNormalized.id != listing.id,
            ListingNormalized.is_duplicate == False,
            ListingNormalized.brand_id == listing.brand_id,
            ListingNormalized.model_id == listing.model_id,
        ).filter(
            # Price within 10%
            ListingNormalized.price_bgn.between(
                listing.price_bgn * Decimal('0.9'),
                listing.price_bgn * Decimal('1.1')
            ) if listing.price_bgn else True
        ).order_by(
            ListingNormalized.created_at.desc()
        ).first()
        
        if similar:
            logger.info(f"Found phone duplicate: {listing.id} -> {similar.id}")
            return similar.id
        
        return None
    
    def check_text_similarity(self, listing: ListingNormalized, threshold: float = 0.7) -> Optional[UUID]:
        """Check for duplicate based on text similarity using pg_trgm"""
        signature = self.generate_text_signature(listing)
        
        if not signature or len(signature) < 10:
            return None
        
        # Use PostgreSQL trigram similarity
        # Find listings with similar text signature
        query = text("""
            SELECT ln.id, similarity(ds.title_trgm, :signature) AS sim
            FROM dedupe_signatures ds
            JOIN listings_normalized ln ON ds.listing_id = ln.id
            WHERE ln.id != :listing_id
              AND ln.is_duplicate = false
              AND ds.title_trgm IS NOT NULL
              AND similarity(ds.title_trgm, :signature) > :threshold
            ORDER BY sim DESC
            LIMIT 1
        """)
        
        result = self.session.execute(
            query,
            {
                'signature': signature,
                'listing_id': listing.id,
                'threshold': threshold,
                'source_id': listing.source_id,
                'created_at': listing.created_at
            }
        ).first()
        
        if result:
            logger.info(f"Found text similarity duplicate: {listing.id} -> {result[0]} (sim={result[1]:.2f})")
            return UUID(str(result[0]))
        
        return None
    
    def check_image_similarity(self, listing: ListingNormalized) -> Optional[UUID]:
        """Check for duplicate based on image hashing (pHash)"""
        # Get listing images
        images = self.session.query(Image).filter_by(listing_id=listing.id).all()
        
        if not images:
            return None
        
        # For now, simple approach: check if any image URL matches
        # TODO: Implement perceptual hashing (pHash) for more robust matching
        
        for image in images[:3]:  # Check first 3 images
            # Find listings with same image URL
            similar_image = self.session.query(Image).filter(
                Image.url == image.url,
                Image.listing_id != listing.id
            ).join(ListingNormalized).filter(
                ListingNormalized.is_duplicate == False,
                ListingNormalized.source_id == listing.source_id
            ).first()
            
            if similar_image:
                logger.info(f"Found image duplicate: {listing.id} -> {similar_image.listing_id}")
                return similar_image.listing_id
        
        return None
    
    def check_embedding_similarity(self, listing: ListingNormalized, threshold: float = 0.85) -> Optional[UUID]:
        """Check for duplicate based on embedding similarity using pgvector"""
        # Get signature with embedding
        signature = self.session.query(DedupeSignature).filter_by(
            listing_id=listing.id
        ).first()
        
        if not signature or not signature.embedding:
            return None
        
        # Use pgvector cosine similarity
        # Find listings with similar embeddings
        query = text("""
            SELECT ds.listing_id, 1 - (ds.embedding <=> :embedding) AS similarity
            FROM dedupe_signature ds
            JOIN listing_normalized ln ON ds.listing_id = ln.id
            WHERE ln.id != :listing_id
              AND ln.is_duplicate = false
              AND ds.embedding IS NOT NULL
              AND 1 - (ds.embedding <=> :embedding) > :threshold
              AND ln.source_id = :source_id
            ORDER BY ds.embedding <=> :embedding
            LIMIT 1
        """)
        
        # Convert embedding list to PostgreSQL vector format
        embedding_str = '[' + ','.join(map(str, signature.embedding)) + ']'
        
        result = self.session.execute(
            query,
            {
                'embedding': embedding_str,
                'listing_id': listing.id,
                'threshold': threshold,
                'source_id': listing.source_id
            }
        ).first()
        
        if result:
            logger.info(f"Found embedding duplicate: {listing.id} -> {result[0]} (sim={result[1]:.2f})")
            return UUID(str(result[0]))
        
        return None
    
    def create_signature(self, listing: ListingNormalized):
        """Create deduplication signature for listing"""
        # Check if signature already exists
        existing = self.session.query(DedupeSignature).filter_by(
            listing_id=listing.id
        ).first()
        
        if existing:
            return existing
        
        # Generate signatures
        text_signature = self.generate_text_signature(listing)
        description_hash = self.generate_description_hash(listing.description)
        
        # TODO: Generate embedding using sentence-transformers
        # For now, leave it as None
        embedding = None
        
        # Create signature
        signature = DedupeSignature(
            listing_id=listing.id,
            title_trgm=text_signature,  # Use title_trgm for text similarity
            title_minhash=None,  # TODO: Generate minhash
            desc_minhash=description_hash,
            first_image_phash=None,  # TODO: Generate from images
        )
        
        self.session.add(signature)
        return signature
    
    def find_duplicate(self, listing: ListingNormalized) -> Optional[UUID]:
        """Find duplicate using multiple methods in order of reliability"""
        
        # Method 1: Phone hash (highest confidence)
        duplicate_id = self.check_phone_duplicate(listing)
        if duplicate_id:
            return duplicate_id, 'phone_hash', 0.95
        
        # Method 2: Image similarity (high confidence)
        duplicate_id = self.check_image_similarity(listing)
        if duplicate_id:
            return duplicate_id, 'image_hash', 0.90
        
        # Method 3: Text similarity (medium confidence)
        duplicate_id = self.check_text_similarity(listing, threshold=0.8)
        if duplicate_id:
            return duplicate_id, 'text_similarity', 0.75
        
        # Method 4: Embedding similarity (medium confidence)
        # TODO: Enable when embeddings are generated
        # duplicate_id = self.check_embedding_similarity(listing, threshold=0.85)
        # if duplicate_id:
        #     return duplicate_id, 'embedding', 0.80
        
        return None, None, 0.0


@celery_app.task(bind=True, max_retries=3)
def deduplicate_listing(self, listing_id: str):
    """Check if listing is a duplicate"""
    session = get_sync_session()
    
    try:
        # Get listing
        listing = session.query(ListingNormalized).filter_by(id=UUID(listing_id)).first()
        
        if not listing:
            logger.error(f"Listing {listing_id} not found")
            return
        
        # Initialize deduplication engine
        engine = DeduplicationEngine(session)
        
        # Create signature for this listing
        engine.create_signature(listing)
        session.commit()
        
        # Find duplicates
        duplicate_id, method, confidence = engine.find_duplicate(listing)
        
        if duplicate_id:
            # Mark as duplicate
            listing.is_duplicate = True
            listing.duplicate_of = duplicate_id
            listing.updated_at = datetime.now(timezone.utc)
            
            # Log duplicate
            dup_log = DuplicateLog(
                listing_id=listing.id,
                original_listing_id=duplicate_id,
                method=method,
                confidence=confidence,
            )
            session.add(dup_log)
            session.commit()
            
            logger.info(f"Marked listing {listing_id} as duplicate of {duplicate_id} (method={method}, conf={confidence})")
            
            return {
                "status": "duplicate",
                "listing_id": listing_id,
                "duplicate_of": str(duplicate_id),
                "method": method,
                "confidence": confidence
            }
        
        else:
            # Not a duplicate, continue pipeline
            logger.info(f"Listing {listing_id} is not a duplicate")
            
            # Trigger price estimation
            estimate_price.delay(listing_id)
            
            return {
                "status": "unique",
                "listing_id": listing_id,
                "is_duplicate": False
            }
        
    except Exception as e:
        session.rollback()
        logger.error(f"Error deduplicating listing {listing_id}: {e}", exc_info=True)
        
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))
    
    finally:
        session.close()
