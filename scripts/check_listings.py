#!/usr/bin/env python3
"""Quick script to check listing statistics in the database."""

from libs.domain.database import get_sync_session
from libs.domain.models import ListingRaw
from sqlalchemy import func

def main():
    session = get_sync_session()
    
    # Get counts
    total = session.query(func.count(ListingRaw.id)).scalar()
    active = session.query(func.count(ListingRaw.id)).filter(ListingRaw.is_active == True).scalar()
    inactive = session.query(func.count(ListingRaw.id)).filter(ListingRaw.is_active == False).scalar()
    
    print("\n" + "="*60)
    print("DATABASE STATISTICS")
    print("="*60)
    print(f"Total listings:   {total}")
    print(f"Active:           {active}")
    print(f"Inactive:         {inactive}")
    print("="*60)
    
    # Get recent listings
    print("\nRECENT LISTINGS (Last 10):")
    print("-"*60)
    recent = session.query(ListingRaw).order_by(ListingRaw.created_at.desc()).limit(10).all()
    
    for i, listing in enumerate(recent, 1):
        brand = listing.parsed_data.get("brand", "N/A")
        model = listing.parsed_data.get("model", "N/A")
        year = listing.parsed_data.get("year", "N/A")
        price = listing.parsed_data.get("price", "N/A")
        currency = listing.parsed_data.get("currency", "N/A")
        
        print(f"{i:2}. {brand} {model} {year} - {price} {currency}")
        print(f"    ID: {listing.site_ad_id} | Active: {listing.is_active}")
        print(f"    URL: {listing.url}")
    
    print("-"*60)
    
    # Brand breakdown
    print("\nBRAND BREAKDOWN (Active listings):")
    print("-"*60)
    brands = session.query(
        func.jsonb_extract_path_text(ListingRaw.parsed_data, 'brand').label('brand'),
        func.count(ListingRaw.id).label('count')
    ).filter(
        ListingRaw.is_active == True
    ).group_by(
        'brand'
    ).order_by(
        func.count(ListingRaw.id).desc()
    ).limit(10).all()
    
    for brand, count in brands:
        brand_name = brand if brand else "(Unknown)"
        print(f"  {brand_name:20} {count:5} listings")
    
    print("-"*60)
    print()
    
    session.close()

if __name__ == "__main__":
    main()
