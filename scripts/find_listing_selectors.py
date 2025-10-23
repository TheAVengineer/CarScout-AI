"""
Find the correct selectors for car listings
"""
from playwright.async_api import async_playwright
import asyncio

async def find_selectors():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        print("Loading search page...")
        await page.goto('https://www.mobile.bg/obiavi/avtomobili-dzhipove')
        await page.wait_for_load_state('networkidle')
        await page.wait_for_timeout(2000)
        
        # Try different selectors
        selectors_to_try = [
            'a[href*="adv="]',
            'a[href*="mobile.cgi"]',
            '.listing',
            '.advert',
            '.car-item',
            'table',
            'tr',
            '.result',
        ]
        
        print("\nTrying selectors:")
        for selector in selectors_to_try:
            try:
                elements = await page.query_selector_all(selector)
                print(f"  '{selector}': {len(elements)} elements")
                if len(elements) > 0 and len(elements) < 100:
                    element = elements[0]
                    html = await element.inner_html()
                    print(f"    First element HTML (first 200 chars): {html[:200]}")
            except Exception as e:
                print(f"  '{selector}': Error - {e}")
        
        # Get all links with adv=
        print("\n\nLooking for links with 'adv=':")
        links = await page.query_selector_all('a[href*="adv="]')
        print(f"Found {len(links)} links")
        
        for i, link in enumerate(links[:10]):
            href = await link.get_attribute('href')
            text = await link.text_content()
            print(f"  {i+1}. {href}")
            print(f"      Text: {text.strip()[:50] if text else 'NO TEXT'}")
        
        print("\n\nPress Enter to close...")
        input()
        
        await browser.close()

if __name__ == '__main__':
    asyncio.run(find_selectors())
