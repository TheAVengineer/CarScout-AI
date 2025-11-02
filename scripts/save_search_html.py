"""
Save the actual HTML content to see what's on the page
"""
from playwright.async_api import async_playwright
import asyncio

async def save_page_html():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        print("Loading search page...")
        await page.goto('https://www.mobile.bg/obiavi/avtomobili-dzhipove')
        await page.wait_for_load_state('networkidle')
        await page.wait_for_timeout(3000)
        
        print("Getting page content...")
        content = await page.content()
        
        # Save to file
        with open('search_page.html', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"\nSaved HTML ({len(content)} chars) to search_page.html")
        print(f"\nFirst 1000 chars:")
        print(content[:1000])
        
        # Count specific patterns
        adv_count = content.count('adv=')
        mobile_cgi_count = content.count('mobile.cgi')
        table_count = content.count('<table')
        
        print(f"\n\nPattern counts:")
        print(f"  'adv=' appears {adv_count} times")
        print(f"  'mobile.cgi' appears {mobile_cgi_count} times")
        print(f"  '<table' appears {table_count} times")
        
        print("\n\nPress Enter to close...")
        input()
        
        await browser.close()

if __name__ == '__main__':
    asyncio.run(save_page_html())
