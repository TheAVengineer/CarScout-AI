"""
Debug Mobile.bg login page to find the correct submit button selector
"""
from playwright.async_api import async_playwright
import asyncio

async def debug_login_page():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        print("Loading login page...")
        await page.goto('https://www.mobile.bg/users/login')
        await page.wait_for_load_state('networkidle')
        
        print("\nPage title:", await page.title())
        print("URL:", page.url)
        
        # Find all forms
        forms = await page.query_selector_all('form')
        print(f"\nFound {len(forms)} forms")
        
        # Find all buttons
        buttons = await page.query_selector_all('button, input[type="submit"], input[type="button"]')
        print(f"\nFound {len(buttons)} buttons/inputs:")
        for i, button in enumerate(buttons):
            tag = await button.evaluate('el => el.tagName')
            type_attr = await button.evaluate('el => el.type')
            id_attr = await button.evaluate('el => el.id')
            class_attr = await button.evaluate('el => el.className')
            text = await button.text_content()
            print(f"  {i+1}. <{tag}> type='{type_attr}' id='{id_attr}' class='{class_attr}' text='{text}'")
        
        # Find username field
        usr_field = await page.query_selector('input[name="usr"]')
        if usr_field:
            print("\n✅ Found username field: input[name='usr']")
        
        # Find password field
        pwd_field = await page.query_selector('input[name="pwd"]')
        if pwd_field:
            print("✅ Found password field: input[name='pwd']")
        
        # Look for specific submit patterns
        patterns = [
            'button[type="submit"]',
            'input[type="submit"]',
            'button',
            'input[type="button"]',
            'form button',
            '[role="button"]',
        ]
        
        print("\nTesting selectors:")
        for pattern in patterns:
            elements = await page.query_selector_all(pattern)
            if elements:
                print(f"  ✅ '{pattern}' found {len(elements)} element(s)")
            else:
                print(f"  ❌ '{pattern}' not found")
        
        # Get the HTML of the form
        form = await page.query_selector('form')
        if form:
            form_html = await form.inner_html()
            print("\nForm HTML:")
            print(form_html[:500])  # First 500 chars
        
        print("\nPress Enter to close...")
        input()
        
        await browser.close()

if __name__ == '__main__':
    asyncio.run(debug_login_page())
