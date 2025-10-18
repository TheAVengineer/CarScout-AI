"""Initial schema

Revision ID: 001
Revises: 
Create Date: 2024-10-18 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable extensions
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pg_trgm"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "vector"')
    
    # Create enums
    op.execute("CREATE TYPE risk_level_enum AS ENUM ('low', 'medium', 'high')")
    op.execute("CREATE TYPE final_state_enum AS ENUM ('draft', 'approved', 'rejected')")
    op.execute("CREATE TYPE user_role_enum AS ENUM ('user', 'admin')")
    op.execute("CREATE TYPE plan_name_enum AS ENUM ('Free', 'Premium', 'Pro')")
    op.execute("CREATE TYPE subscription_status_enum AS ENUM ('active', 'past_due', 'canceled')")
    op.execute("CREATE TYPE billing_provider_enum AS ENUM ('Stripe', 'Telegram')")
    op.execute("CREATE TYPE delivery_status_enum AS ENUM ('pending', 'delivered', 'skipped', 'failed')")
    op.execute("CREATE TYPE dedupe_method_enum AS ENUM ('heuristic', 'embedding', 'image')")
    
    # Sources table
    op.create_table(
        'sources',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False, unique=True),
        sa.Column('base_url', sa.String(255), nullable=False),
        sa.Column('robots_cache', postgresql.JSON),
        sa.Column('enabled', sa.Boolean, default=True),
        sa.Column('crawl_interval_s', sa.Integer, default=120),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
    )
    
    # Listings raw table
    op.create_table(
        'listings_raw',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('source_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('sources.id'), nullable=False),
        sa.Column('site_ad_id', sa.String(100), nullable=False),
        sa.Column('url', sa.String(500), nullable=False),
        sa.Column('raw_html_path', sa.String(500)),
        sa.Column('first_seen_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('last_seen_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('http_status', sa.Integer),
        sa.Column('etag', sa.String(100)),
        sa.Column('last_modified', sa.String(100)),
        sa.Column('parse_errors', sa.Text),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('idx_source_site_ad', 'listings_raw', ['source_id', 'site_ad_id'], unique=True)
    op.create_index('idx_is_active', 'listings_raw', ['is_active'])
    op.create_index('idx_first_seen', 'listings_raw', ['first_seen_at'])
    
    # Brand models table
    op.create_table(
        'brand_models',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('brand', sa.String(100), nullable=False),
        sa.Column('model', sa.String(100), nullable=False),
        sa.Column('aliases', postgresql.JSON, default=[]),
        sa.Column('locale', sa.String(10), default='bg'),
        sa.Column('normalized_brand', sa.String(100), nullable=False),
        sa.Column('normalized_model', sa.String(100), nullable=False),
        sa.Column('active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('idx_brand_model', 'brand_models', ['normalized_brand', 'normalized_model'])
    
    # Sellers table
    op.create_table(
        'sellers',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('phone_hash', sa.String(64), unique=True, nullable=False),
        sa.Column('name', sa.String(200)),
        sa.Column('site_profile_url', sa.String(500)),
        sa.Column('contact_count', sa.Integer, default=0),
        sa.Column('blacklist', sa.Boolean, default=False),
        sa.Column('notes', sa.Text),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('idx_blacklist', 'sellers', ['blacklist'], postgresql_where=sa.text('blacklist = true'))
    
    # Listings normalized table
    op.create_table(
        'listings_normalized',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('raw_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('listings_raw.id'), nullable=False),
        sa.Column('brand_id', sa.String(100)),
        sa.Column('model_id', sa.String(100)),
        sa.Column('year', sa.Integer),
        sa.Column('mileage_km', sa.Integer),
        sa.Column('fuel', sa.String(50)),
        sa.Column('gearbox', sa.String(50)),
        sa.Column('body', sa.String(50)),
        sa.Column('price_bgn', sa.Numeric(10, 2)),
        sa.Column('currency', sa.String(10)),
        sa.Column('region', sa.String(100)),
        sa.Column('title', sa.Text),
        sa.Column('description', sa.Text),
        sa.Column('features', postgresql.JSON),
        sa.Column('description_hash', sa.String(64)),
        sa.Column('first_image_hash', sa.String(64)),
        sa.Column('listing_version', sa.Integer, default=1),
        sa.Column('is_duplicate', sa.Boolean, default=False),
        sa.Column('duplicate_of', postgresql.UUID(as_uuid=True), sa.ForeignKey('listings_normalized.id')),
        sa.Column('seller_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('sellers.id')),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('idx_brand_model_year', 'listings_normalized', ['brand_id', 'model_id', 'year'])
    op.create_index('idx_price', 'listings_normalized', ['price_bgn'])
    op.create_index('idx_is_duplicate', 'listings_normalized', ['is_duplicate'])
    op.create_index('idx_description_hash', 'listings_normalized', ['description_hash'])
    
    # Images table
    op.create_table(
        'images',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('listing_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('listings_normalized.id'), nullable=False),
        sa.Column('url', sa.String(500), nullable=False),
        sa.Column('object_key', sa.String(500)),
        sa.Column('hash', sa.String(64)),
        sa.Column('width', sa.Integer),
        sa.Column('height', sa.Integer),
        sa.Column('index', sa.Integer, default=0),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )
    
    # Price history table
    op.create_table(
        'prices_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('listing_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('listings_normalized.id'), nullable=False),
        sa.Column('price_bgn', sa.Numeric(10, 2), nullable=False),
        sa.Column('seen_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index('idx_listing_seen', 'prices_history', ['listing_id', 'seen_at'])
    
    # Comps cache table
    op.create_table(
        'comps_cache',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('listing_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('listings_normalized.id'), nullable=False),
        sa.Column('predicted_price_bgn', sa.Numeric(10, 2)),
        sa.Column('discount_pct', sa.Float),
        sa.Column('sample_size', sa.Integer),
        sa.Column('p50', sa.Numeric(10, 2)),
        sa.Column('p10', sa.Numeric(10, 2)),
        sa.Column('p90', sa.Numeric(10, 2)),
        sa.Column('features', postgresql.JSON),
        sa.Column('computed_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('model_version', sa.String(50)),
    )
    
    # Evaluations table
    op.create_table(
        'evaluations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('listing_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('listings_normalized.id'), nullable=False),
        sa.Column('flags', postgresql.JSON),
        sa.Column('risk_level', postgresql.ENUM('low', 'medium', 'high', name='risk_level_enum')),
        sa.Column('llm_summary', sa.Text),
        sa.Column('llm_confidence', sa.Float),
        sa.Column('rule_confidence', sa.Float),
        sa.Column('model_versions', postgresql.JSON),
        sa.Column('evaluated_at', sa.DateTime, server_default=sa.func.now()),
    )
    
    # Scores table
    op.create_table(
        'scores',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('listing_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('listings_normalized.id'), nullable=False),
        sa.Column('score', sa.Float, nullable=False),
        sa.Column('reasons', postgresql.JSON),
        sa.Column('freshness_bonus', sa.Float),
        sa.Column('liquidity', sa.Float),
        sa.Column('risk_penalty', sa.Float),
        sa.Column('final_state', postgresql.ENUM('draft', 'approved', 'rejected', name='final_state_enum')),
        sa.Column('scored_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('idx_score_state', 'scores', ['score', 'final_state'])
    
    # Users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('telegram_user_id', sa.BigInteger, unique=True),
        sa.Column('email', sa.String(255), unique=True),
        sa.Column('role', postgresql.ENUM('user', 'admin', name='user_role_enum'), default='user'),
        sa.Column('status', sa.String(50), default='active'),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
    )
    
    # Plans table
    op.create_table(
        'plans',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', postgresql.ENUM('Free', 'Premium', 'Pro', name='plan_name_enum'), nullable=False, unique=True),
        sa.Column('limits', postgresql.JSON),
        sa.Column('price_bgn', sa.Numeric(10, 2)),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )
    
    # Subscriptions table
    op.create_table(
        'subscriptions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('plan_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('plans.id'), nullable=False),
        sa.Column('status', postgresql.ENUM('active', 'past_due', 'canceled', name='subscription_status_enum')),
        sa.Column('billing_provider', postgresql.ENUM('Stripe', 'Telegram', name='billing_provider_enum')),
        sa.Column('provider_customer_id', sa.String(100)),
        sa.Column('provider_sub_id', sa.String(100)),
        sa.Column('current_period_end', sa.DateTime),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
    )
    
    # Alerts table
    op.create_table(
        'alerts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('dsl_query', sa.Text, nullable=False),
        sa.Column('normalized_filters', postgresql.JSON, nullable=False),
        sa.Column('plan_required', sa.String(50)),
        sa.Column('active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
    )
    
    # Alert matches table
    op.create_table(
        'alert_matches',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('alert_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('alerts.id'), nullable=False),
        sa.Column('listing_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('listings_normalized.id'), nullable=False),
        sa.Column('matched_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('delivered_at', sa.DateTime),
        sa.Column('delivery_status', postgresql.ENUM('pending', 'delivered', 'skipped', 'failed', name='delivery_status_enum')),
        sa.Column('reason', sa.Text),
    )
    
    # Channel posts table
    op.create_table(
        'channel_posts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('listing_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('listings_normalized.id'), nullable=False),
        sa.Column('telegram_message_id', sa.BigInteger, nullable=False),
        sa.Column('posted_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('channel', sa.String(100)),
        sa.Column('status', sa.String(50)),
    )
    op.create_index('idx_listing_channel', 'channel_posts', ['listing_id', 'channel'], unique=True)
    
    # Dedupe signatures table
    op.create_table(
        'dedupe_signatures',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('listing_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('listings_normalized.id'), nullable=False, unique=True),
        sa.Column('title_trgm', sa.Text),
        sa.Column('title_minhash', sa.String(256)),
        sa.Column('desc_minhash', sa.String(256)),
        sa.Column('first_image_phash', sa.BigInteger),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )
    
    # Add vector column for embeddings (pgvector)
    op.execute('ALTER TABLE dedupe_signatures ADD COLUMN embeddings vector(384)')
    
    # Duplicates log table
    op.create_table(
        'duplicates_log',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('listing_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('listings_normalized.id'), nullable=False),
        sa.Column('duplicate_of', postgresql.UUID(as_uuid=True), sa.ForeignKey('listings_normalized.id'), nullable=False),
        sa.Column('method', postgresql.ENUM('heuristic', 'embedding', 'image', name='dedupe_method_enum')),
        sa.Column('score', sa.Float),
        sa.Column('decided_at', sa.DateTime, server_default=sa.func.now()),
    )
    
    # Insert default plans
    op.execute("""
        INSERT INTO plans (id, name, limits, price_bgn) VALUES
        (gen_random_uuid(), 'Free', '{"max_alerts": 3, "delay_minutes": 30}', 0),
        (gen_random_uuid(), 'Premium', '{"max_alerts": 10, "delay_minutes": 0}', 19.99),
        (gen_random_uuid(), 'Pro', '{"max_alerts": 999, "delay_minutes": 0}', 39.99)
    """)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('duplicates_log')
    op.drop_table('dedupe_signatures')
    op.drop_table('channel_posts')
    op.drop_table('alert_matches')
    op.drop_table('alerts')
    op.drop_table('subscriptions')
    op.drop_table('plans')
    op.drop_table('users')
    op.drop_table('scores')
    op.drop_table('evaluations')
    op.drop_table('comps_cache')
    op.drop_table('prices_history')
    op.drop_table('images')
    op.drop_table('listings_normalized')
    op.drop_table('sellers')
    op.drop_table('brand_models')
    op.drop_table('listings_raw')
    op.drop_table('sources')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS dedupe_method_enum')
    op.execute('DROP TYPE IF EXISTS delivery_status_enum')
    op.execute('DROP TYPE IF EXISTS billing_provider_enum')
    op.execute('DROP TYPE IF EXISTS subscription_status_enum')
    op.execute('DROP TYPE IF EXISTS plan_name_enum')
    op.execute('DROP TYPE IF EXISTS user_role_enum')
    op.execute('DROP TYPE IF EXISTS final_state_enum')
    op.execute('DROP TYPE IF EXISTS risk_level_enum')
