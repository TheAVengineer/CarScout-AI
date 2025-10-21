"""Add raw_html column to listings_raw table"""
from libs.domain.database import sync_engine
from sqlalchemy import text

with sync_engine.connect() as conn:
    conn.execute(text('ALTER TABLE listings_raw ADD COLUMN IF NOT EXISTS raw_html TEXT'))
    conn.commit()
    print('✅ Column raw_html added successfully!')
