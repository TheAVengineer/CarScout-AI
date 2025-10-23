"""
Inspect what URLs are actually on the search page after JavaScript loads
"""
from playwright.async_api import async_playwright
import asyncio

async def inspect_search_page():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        print("Loading search page...")
        await page.goto('https://www.mobile.bg/obiavi/avtomobili-dzhipove')
        await page.wait_for_load_state('networkidle')
        
        # Wait for listings to load
        print("\nWaiting for listings...")
        await page.wait_for_selector('table.tablereset', timeout=10000)
        
        # Get all links
        all_links = await page.query_selector_all('a')
        print(f"\nFound {len(all_links)} total links")
        
        # Filter to car listing links
        car_links = []
        for link in all_links:
            href = await link.get_attribute('href')
            if href and ('adv=' in href or 'mobile.cgi' in href):
                text = await link.text_content()
                car_links.append((href, text.strip()[:50] if text else ''))
        
        print(f"\nFound {len(car_links)} potential car listing links:")
        for i, (href, text) in enumerate(car_links[:20]):  # Show first 20
            print(f"  {i+1}. {href}")
            if text:
                print(f"      Text: {text}")
        
        # Look for table structure
        tables = await page.query_selector_all('table.tablereset')
        print(f"\n\nFound {len(tables)} tables with class 'tablereset'")
        
        if tables:
            # Get links from first table
            table = tables[0]
            table_links = await table.query_selector_all('a')
            print(f"First table has {len(table_links)} links")
            
            for i, link in enumerate(table_links[:10]):
                href = await link.get_attribute('href')
                text = await link.text_content()
                print(f"  {i+1}. {href} - {text.strip()[:30] if text else ''}")
        
        print("\n\nPress Enter to close...")
        input()
        
        await browser.close()

if __name__ == '__main__':
    asyncio.run(inspect_search_page())
