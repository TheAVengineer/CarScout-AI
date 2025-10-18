#!/usr/bin/env python3
"""
Simple database setup script
Creates tables directly using SQLAlchemy and seeds data
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from libs.domain.database import sync_engine
from libs.domain.models import Base

print("🚀 CarScout AI - Simple Setup")
print("=" * 60)
print()

# Create all tables
print("📦 Creating database tables...")
Base.metadata.create_all(sync_engine)

print("✅ All tables created successfully!")
print()
print("Next step: Run seed script")
print("  python3 scripts/seed_database.py")

