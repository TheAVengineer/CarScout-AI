"""
Test Mobile.bg authentication configuration
"""
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_credentials():
    """Check if Mobile.bg credentials are configured"""
    from configs.settings import settings
    
    print("=" * 70)
    print("🔍 Mobile.bg Authentication Test")
    print("=" * 70)
    print()
    
    # Check if credentials are set
    email_set = bool(settings.MOBILE_BG_EMAIL)
    password_set = bool(settings.MOBILE_BG_PASSWORD)
    
    print("📋 Configuration Status:")
    print(f"   Email: {settings.MOBILE_BG_EMAIL if email_set else '❌ NOT SET'}")
    print(f"   Password: {'✅ SET (' + '*' * len(settings.MOBILE_BG_PASSWORD) + ')' if password_set else '❌ NOT SET'}")
    print()
    
    if email_set and password_set:
        print("✅ Credentials are configured!")
        print()
        print("=" * 70)
        print("📝 Next Steps:")
        print("=" * 70)
        print()
        print("1. Test scraping with authentication:")
        print("   cd workers/scrape")
        print("   scrapy crawl mobile_bg -s CLOSESPIDER_ITEMCOUNT=5")
        print()
        print("2. Look for these messages in the logs:")
        print("   🔐 Login credentials provided - will authenticate before scraping")
        print("   Step 1: Fetching login page...")
        print("   Step 2: Submitting login form...")
        print("   ✅ Login successful! Starting scraping...")
        print()
        print("3. Verify listings were scraped:")
        print("   python scripts\\check_progress.py")
        print()
        print("4. If login fails, check:")
        print("   - Credentials are correct (try logging in at mobile.bg)")
        print("   - Account email is verified")
        print("   - No typos in .env file")
        print()
        return True
    else:
        print("❌ Credentials are missing!")
        print()
        print("=" * 70)
        print("📝 How to Fix:")
        print("=" * 70)
        print()
        print("1. Open your .env file:")
        print("   notepad .env")
        print()
        print("2. Add these lines (replace with your actual credentials):")
        print()
        print("   # Mobile.bg Authentication")
        print("   MOBILE_BG_EMAIL=your.email@example.com")
        print("   MOBILE_BG_PASSWORD=your_password_here")
        print()
        print("3. Save and close the file")
        print()
        print("4. Restart Celery worker:")
        print("   .\\restart_celery.ps1")
        print()
        print("5. Run this test again:")
        print("   python scripts\\test_mobile_auth.py")
        print()
        print("=" * 70)
        print("🆘 Need a Mobile.bg Account?")
        print("=" * 70)
        print()
        print("1. Go to: https://www.mobile.bg")
        print("2. Click 'Регистрация' (Register)")
        print("3. Fill in email and password")
        print("4. Verify your email")
        print("5. Use those credentials in .env")
        print()
        print("Free account is sufficient - no payment needed!")
        print()
        return False


if __name__ == "__main__":
    success = test_credentials()
    sys.exit(0 if success else 1)
