import sys
sys.path.insert(0, r'C:\CarScout-AI')

from libs.domain.database import sync_engine
from sqlalchemy import text

with sync_engine.connect() as conn:
    # Add parsed_data JSONB column
    conn.execute(text('ALTER TABLE listings_raw ADD COLUMN IF NOT EXISTS parsed_data JSONB'))
    conn.commit()
    print('✅ Column parsed_data (JSONB) added successfully!')
