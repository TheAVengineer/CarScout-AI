"""
Test Playwright spider with credentials from settings
"""
import subprocess
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load settings
from configs.settings import settings

print("=" * 70)
print("🧪 Testing Mobile.bg Spider with Playwright")
print("=" * 70)
print()

# Check credentials
if not settings.MOBILE_BG_EMAIL or not settings.MOBILE_BG_PASSWORD:
    print("❌ Credentials not configured!")
    print("Please add MOBILE_BG_EMAIL and MOBILE_BG_PASSWORD to .env")
    sys.exit(1)

print(f"✅ Email: {settings.MOBILE_BG_EMAIL}")
print(f"✅ Password: {'*' * len(settings.MOBILE_BG_PASSWORD)}")
print()

# Build scrapy command
scrapy_cmd = [
    str(project_root / "venv" / "Scripts" / "scrapy.exe"),
    "crawl",
    "mobile_bg",
    "-s", "CLOSESPIDER_ITEMCOUNT=5",
    "-a", f"login_email={settings.MOBILE_BG_EMAIL}",
    "-a", f"login_password={settings.MOBILE_BG_PASSWORD}",
]

print("🚀 Running spider...")
print(f"Command: scrapy crawl mobile_bg -s CLOSESPIDER_ITEMCOUNT=5 -a login_email=*** -a login_password=***")
print()

# Change to scrape directory
scrape_dir = project_root / "workers" / "scrape"

# Run command
result = subprocess.run(
    scrapy_cmd,
    cwd=scrape_dir,
    capture_output=False,  # Show output in real-time
)

print()
print("=" * 70)
if result.returncode == 0:
    print("✅ Spider completed successfully!")
else:
    print(f"❌ Spider failed with code {result.returncode}")
print("=" * 70)

sys.exit(result.returncode)
