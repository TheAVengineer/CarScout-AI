"""
Inspect the full login page after clicking "За частни лица" (For individuals)
"""
from playwright.async_api import async_playwright
import asyncio

async def inspect_login_page():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        print("Loading login page...")
        await page.goto('https://www.mobile.bg/users/login')
        await page.wait_for_load_state('networkidle')
        
        # Click the "За частни лица" radio button
        print("\nClicking 'За частни лица' radio button...")
        await page.click('input[name="logtype"][value="2"]')
        await page.wait_for_timeout(1000)  # Wait for any JS to execute
        
        # Now check for the login form
        print("\nLooking for login form fields...")
        
        # Check for username field
        usr = await page.query_selector('input[name="usr"]')
        if usr:
            print("✅ Found username field")
            is_visible = await usr.is_visible()
            is_enabled = await usr.is_enabled()
            print(f"   Visible: {is_visible}, Enabled: {is_enabled}")
        
        # Check for password field
        pwd = await page.query_selector('input[name="pwd"]')
        if pwd:
            print("✅ Found password field")
            is_visible = await pwd.is_visible()
            is_enabled = await pwd.is_enabled()
            print(f"   Visible: {is_visible}, Enabled: {is_enabled}")
        
        # Look for all input elements
        all_inputs = await page.query_selector_all('input')
        print(f"\nAll input elements ({len(all_inputs)}):")
        for i, inp in enumerate(all_inputs):
            type_attr = await inp.evaluate('el => el.type')
            name_attr = await inp.evaluate('el => el.name')
            id_attr = await inp.evaluate('el => el.id')
            value_attr = await inp.evaluate('el => el.value')
            is_visible = await inp.is_visible()
            is_enabled = await inp.is_enabled()
            print(f"  {i+1}. type='{type_attr}' name='{name_attr}' id='{id_attr}' value='{value_attr}' visible={is_visible} enabled={is_enabled}")
        
        # Look for all buttons
        all_buttons = await page.query_selector_all('button, input[type="submit"], input[type="button"], a.button, .btn, [onclick*="submit"]')
        print(f"\nAll buttons/submit elements ({len(all_buttons)}):")
        for i, btn in enumerate(all_buttons):
            tag = await btn.evaluate('el => el.tagName')
            type_attr = await btn.evaluate('el => el.type || "N/A"')
            text = await btn.text_content()
            onclick = await btn.evaluate('el => el.getAttribute("onclick") || el.onclick?.toString() || "N/A"')
            is_visible = await btn.is_visible()
            print(f"  {i+1}. <{tag}> type='{type_attr}' text='{text[:50]}' onclick='{onclick[:50]}' visible={is_visible}")
        
        # Try to find the form
        form = await page.query_selector('form')
        if form:
            action = await form.evaluate('el => el.action')
            method = await form.evaluate('el => el.method')
            onsubmit = await form.evaluate('el => el.onsubmit?.toString() || "N/A"')
            print(f"\nForm found: action='{action}' method='{method}' onsubmit='{onsubmit[:100]}'")
        
        print("\nPress Enter to close...")
        input()
        
        await browser.close()

if __name__ == '__main__':
    asyncio.run(inspect_login_page())
