"""
Create database tables manually
"""
import sys
import os
import asyncio
from sqlalchemy import text

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from libs.domain.database import async_engine
from libs.domain.models import Base  # Base is in models.py
from libs.domain.models import *  # Import all models

async def create_tables():
    """Create all tables"""
    print("Creating database tables...")
    
    async with async_engine.begin() as conn:
        # Enable extensions
        await conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
        await conn.execute(text('CREATE EXTENSION IF NOT EXISTS "pg_trgm"'))
        await conn.execute(text('CREATE EXTENSION IF NOT EXISTS "vector"'))
        print("✅ Extensions created")
        
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
        print("✅ Tables created")
    
    print()
    print("=" * 70)
    print("✅ Database initialized successfully!")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(create_tables())
