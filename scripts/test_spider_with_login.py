"""
Test Mobile.bg spider WITH login enabled.

This script tests the full authentication flow:
1. Navigate to login page
2. Fill credentials
3. Submit form
4. Wait for redirect
5. Verify login success
6. Scrape listings
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import asyncio
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

# Import settings
sys.path.insert(0, str(project_root / 'workers' / 'scrape'))
from carscout.spiders.mobile_bg import MobileBgSpider

def main():
    """Run spider with login enabled"""
    
    # Change to scrapy project directory
    import os
    scrapy_dir = project_root / 'workers' / 'scrape'
    os.chdir(scrapy_dir)
    
    # Get Scrapy settings (now from correct directory)
    settings = get_project_settings()
    
    # Override settings for testing
    settings.update({
        'CLOSESPIDER_ITEMCOUNT': 5,  # Stop after 5 items for testing
        'CONCURRENT_REQUESTS': 1,
        'DOWNLOAD_DELAY': 2,
        'LOG_LEVEL': 'INFO',
        'PLAYWRIGHT_LAUNCH_OPTIONS': {
            'headless': True,  # Set to False to see browser
            'args': [
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
            ]
        },
    })
    
    # IMPORTANT: Enable login for this test
    # Make sure these environment variables are set:
    # - MOBILE_BG_LOGIN_EMAIL
    # - MOBILE_BG_LOGIN_PASSWORD
    
    print("="*60)
    print("[LOGIN TEST] Testing Mobile.bg Spider WITH LOGIN")
    print("="*60)
    print()
    print("This test will:")
    print("  1. Navigate to login page")
    print("  2. Fill credentials from environment variables")
    print("  3. Submit login form")
    print("  4. Wait for redirect (up to 20 seconds)")
    print("  5. Scrape 5 listings if login succeeds")
    print()
    
    import os
    login_email = os.getenv('MOBILE_BG_LOGIN_EMAIL')
    login_password = os.getenv('MOBILE_BG_LOGIN_PASSWORD')
    
    if not login_email or not login_password:
        print("[ERROR] Login credentials not found!")
        print()
        print("Please set environment variables:")
        print("  $env:MOBILE_BG_LOGIN_EMAIL='your-email@example.com'")
        print("  $env:MOBILE_BG_LOGIN_PASSWORD='your-password'")
        print()
        return 1
    
    print("[OK] Login email found: {0}".format(login_email))
    print("[OK] Password found: {0}".format('*' * len(login_password)))
    print()
    print("[START] Starting spider...")
    print("="*60)
    print()
    
    # Create process and run spider
    process = CrawlerProcess(settings)
    process.crawl(MobileBgSpider)
    process.start()
    
    print()
    print("="*60)
    print("[DONE] Spider finished!")
    print("="*60)

if __name__ == "__main__":
    sys.exit(main() or 0)
