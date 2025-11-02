#!/usr/bin/env python3
"""
Test a single brand search URL to debug the brand-based approach
"""

import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from playwright.async_api import async_playwright

async def test_brand_url():
    """Test a single Mercedes-Benz search URL"""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        # Test URL from our brand config (corrected /obiavi/ format)
        test_url = "https://www.mobile.bg/obiavi/avtomobili-dzhipove/bmw/namira-se-v-balgariya?sort=6"
        
        print(f"🔍 Testing brand URL: {test_url}")
        await page.goto(test_url)
        
        # Dismiss cookie consent
        try:
            await page.wait_for_selector('[role="dialog"] div:has-text("Приемете всички")', timeout=3000)
            await page.click('[role="dialog"] div:has-text("Приемете всички")')
            print("✅ Dismissed cookie consent")
            await page.wait_for_timeout(2000)
        except:
            print("ℹ️ No cookie consent dialog")
        
        # Wait for listings to load
        print("⏳ Waiting for listings...")
        await page.wait_for_timeout(5000)
        
        # Check for car listing links
        listing_links = await page.query_selector_all('a[href*="/obiava-"]')
        print(f"🚗 Found {len(listing_links)} listing links")
        
        # Show first few
        for i, link in enumerate(listing_links[:5]):
            href = await link.get_attribute('href')
            text = (await link.text_content() or '').strip()
            print(f"  [{i+1}] {text[:50]}... -> {href}")
        
        # Check for pagination
        pagination_links = await page.query_selector_all('.pagination a')
        print(f"📄 Found {len(pagination_links)} pagination links")
        
        for link in pagination_links:
            text = (await link.text_content() or '').strip()
            href = await link.get_attribute('href')
            if text:
                print(f"  - {text}: {href}")
        
        # Take screenshot
        await page.screenshot(path="test_brand_page.png")
        print("📸 Screenshot saved to test_brand_page.png")
        
        print("\n⏸️ Check the browser window. Press Enter to close...")
        input()
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_brand_url())