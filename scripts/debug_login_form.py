"""
Debug Mobile.bg login form structure
"""
from playwright.async_api import async_playwright
import asyncio

async def debug_login_form():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        print("Loading login page...")
        await page.goto('https://www.mobile.bg/users/login')
        await page.wait_for_load_state('networkidle')
        
        # Get all elements with role=button
        buttons = await page.query_selector_all('[role="button"]')
        print(f"\nFound {len(buttons)} elements with role='button':")
        for i, button in enumerate(buttons):
            tag = await button.evaluate('el => el.tagName')
            class_attr = await button.evaluate('el => el.className')
            text = await button.text_content()
            onclick = await button.evaluate('el => el.getAttribute("onclick")')
            print(f"  {i+1}. <{tag}> class='{class_attr}' text='{text}' onclick='{onclick}'")
        
        # Get the full HTML of the main form
        form = await page.query_selector('form')
        if form:
            form_html = await form.inner_html()
            print("\n" + "="*70)
            print("FULL FORM HTML:")
            print("="*70)
            print(form_html)
        
        print("\nPress Enter to close...")
        input()
        
        await browser.close()

if __name__ == '__main__':
    asyncio.run(debug_login_form())
