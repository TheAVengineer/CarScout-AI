"""Quick script to inspect Mobile.bg pagination structure"""
import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        print("Loading Mobile.bg search page...")
        await page.goto('https://www.mobile.bg/obiavi/avtomobili-dzhipove')
        await page.wait_for_load_state('networkidle')
        
        # Dismiss cookie consent
        try:
            await page.click('[role="dialog"] div:has-text("Приемете всички")', timeout=3000)
            print("Dismissed cookie dialog")
        except:
            pass
        
        # Wait for page to load
        await asyncio.sleep(2)
        
        # Find pagination elements
        print("\n=== Looking for pagination ===")
        
        # Try different selectors
        selectors = [
            'div.pager a',
            'div.paging a',
            'a[href*="/p-"]',
            'ul.pagination a',
            '.pagination a',
            'a:has-text("Следваща")',
            'a:has-text(">")',
            'a[title*="страница"]',
        ]
        
        for selector in selectors:
            try:
                elements = await page.query_selector_all(selector)
                if elements:
                    print(f"\n✅ Found {len(elements)} elements with selector: {selector}")
                    for i, el in enumerate(elements[:5]):  # Show first 5
                        text = await el.inner_text()
                        href = await el.get_attribute('href')
                        print(f"  [{i}] Text: '{text}' | Href: {href}")
            except Exception as e:
                print(f"❌ Selector '{selector}' failed: {e}")
        
        # Save HTML for manual inspection
        html = await page.content()
        with open('pagination_page.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"\n💾 Saved HTML to pagination_page.html ({len(html)} chars)")
        
        input("\nPress Enter to close browser...")
        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
