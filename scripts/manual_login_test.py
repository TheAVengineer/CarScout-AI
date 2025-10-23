"""
Manually test login to see what's happening
"""
from playwright.async_api import async_playwright
import asyncio
import sys
from pathlib import Path

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from configs.settings import settings

async def manual_login():
    email = settings.MOBILE_BG_EMAIL
    password = settings.MOBILE_BG_PASSWORD
    
    print(f"Email: {email}")
    print(f"Password: {'*' * len(password) if password else 'EMPTY'}")
    
    if not email or not password:
        print("\n❌ Credentials not configured in .env!")
        return
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=1000)
        page = await browser.new_page()
        
        print("\nLoading login page...")
        await page.goto('https://www.mobile.bg/users/login')
        await page.wait_for_load_state('networkidle')
        
        # Dismiss cookie dialog
        try:
            accept_button = await page.query_selector('[role="dialog"] div:has-text("Приемете всички")')
            if accept_button:
                await accept_button.click()
                print("✅ Dismissed cookie dialog")
                await page.wait_for_timeout(500)
        except:
            pass
        
        # Click radio button
        print("\nClicking 'За частни лица' radio...")
        await page.click('input[name="logtype"][value="2"]', force=True)
        await page.wait_for_timeout(500)
        
        # Fill form
        print(f"\nFilling email: {email}")
        await page.fill('input[name="usr"]', email)
        
        print("Filling password: ***")
        await page.fill('input[name="pwd"]', password)
        
        # Submit
        print("\nSubmitting form (press Enter)...")
        await page.press('input[name="pwd"]', 'Enter')
        
        # Wait and check result
        await page.wait_for_load_state('networkidle')
        await page.wait_for_timeout(2000)
        
        print(f"\nCurrent URL: {page.url}")
        
        # Check for success/error
        content = await page.content()
        
        if 'изход' in content.lower() or 'logout' in content.lower():
            print("✅ Login SUCCESSFUL!")
        elif 'грешка' in content.lower() or 'error' in content.lower():
            print("❌ Login FAILED - error message found")
            # Try to find the error message
            error_divs = await page.query_selector_all('.error, .alert, [class*="error"]')
            for div in error_divs:
                text = await div.text_content()
                if text.strip():
                    print(f"   Error: {text.strip()}")
        else:
            print("⚠️  Login status UNCLEAR")
        
        # Take screenshot
        await page.screenshot(path='login_result.png')
        print("\n📸 Screenshot saved: login_result.png")
        
        print("\nPress Enter to close...")
        input()
        
        await browser.close()

if __name__ == '__main__':
    asyncio.run(manual_login())
