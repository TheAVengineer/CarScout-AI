#!/usr/bin/env python3
"""
Manual inspection of Mobile.bg page to find filter structure
"""

import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from playwright.async_api import async_playwright

async def inspect_mobile_bg_page():
    """Inspect Mobile.bg search page structure to understand filters"""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Show browser
        page = await browser.new_page()
        
        print("🔍 Loading Mobile.bg search page...")
        await page.goto("https://www.mobile.bg/search/avtomobili-dzhipove/namira-se-v-balgariya?sort=6")
        
        # Dismiss cookie consent if present
        try:
            await page.wait_for_selector('[role="dialog"] div:has-text("Приемете всички")', timeout=3000)
            await page.click('[role="dialog"] div:has-text("Приемете всички")')
            print("✅ Dismissed cookie consent")
            await page.wait_for_timeout(2000)
        except:
            print("ℹ️ No cookie consent dialog found")
        
        # Save page HTML for analysis
        content = await page.content()
        with open("mobile_bg_search_page.html", 'w', encoding='utf-8') as f:
            f.write(content)
        print("💾 Saved page HTML to mobile_bg_search_page.html")
        
        # Look for any filter-related elements
        print("\n🔍 Looking for filter elements...")
        
        # Check for select dropdowns
        selects = await page.query_selector_all('select')
        print(f"Found {len(selects)} select dropdowns:")
        for i, select in enumerate(selects):
            name = await select.get_attribute('name')
            id_attr = await select.get_attribute('id')
            print(f"  [{i}] Name: {name}, ID: {id_attr}")
        
        # Check for any brand/model related links
        print(f"\n🔍 Looking for brand-related links...")
        all_links = await page.query_selector_all('a')
        brand_links = []
        for link in all_links:
            href = await link.get_attribute('href')
            text = (await link.text_content() or '').strip()
            if href and ('bmw' in href.lower() or 'audi' in href.lower() or 'mercedes' in href.lower()):
                brand_links.append({'text': text, 'href': href})
        
        print(f"Found {len(brand_links)} brand-related links:")
        for link in brand_links[:10]:
            print(f"  - {link['text']}: {link['href']}")
        
        # Check for any elements containing "марка" (brand in Bulgarian)
        print(f"\n🔍 Looking for 'марка' (brand) elements...")
        brand_elements = await page.query_selector_all('*:has-text("марка")')
        print(f"Found {len(brand_elements)} elements containing 'марка'")
        
        # Take a screenshot
        await page.screenshot(path="mobile_bg_search_page.png")
        print("📸 Saved screenshot to mobile_bg_search_page.png")
        
        print("\n⏸️ Page loaded. Check the browser window and HTML file to understand the filter structure.")
        print("Press Enter when ready to close...")
        input()
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(inspect_mobile_bg_page())