"""
Test spider without login - just scrape public search pages
"""
import subprocess
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

print("="*70)
print("Testing Mobile.bg Spider WITHOUT Login (Public Listings)")
print("="*70)
print()

# Build scrapy command - no login
scrapy_cmd = [
    str(project_root / "venv" / "Scripts" / "scrapy.exe"),
    "crawl",
    "mobile_bg",
    "-s", "CLOSESPIDER_ITEMCOUNT=5",
    "-a", "requires_login=False",  # Skip login
]

print("Running spider without login...")
print(f"Command: scrapy crawl mobile_bg -s CLOSESPIDER_ITEMCOUNT=5 -a requires_login=False")
print()

# Change to scrape directory
scrape_dir = project_root / "workers" / "scrape"

# Run command
result = subprocess.run(
    scrapy_cmd,
    cwd=scrape_dir,
    capture_output=False,
)

print()
print("="*70)
if result.returncode == 0:
    print("Spider completed successfully!")
else:
    print(f"Spider failed with code {result.returncode}")
print("="*70)

sys.exit(result.returncode)
