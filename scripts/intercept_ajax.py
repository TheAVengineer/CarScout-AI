"""
Wait longer and check for AJAX requests that might load listings
"""
from playwright.async_api import async_playwright
import asyncio

async def intercept_requests():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        # Track XHR/Fetch requests
        requests = []
        
        async def log_request(request):
            if request.resource_type in ('xhr', 'fetch'):
                requests.append({
                    'url': request.url,
                    'method': request.method,
                    'type': request.resource_type
                })
                print(f"XHR/Fetch: {request.method} {request.url}")
        
        page.on('request', log_request)
        
        print("Loading search page...")
        await page.goto('https://www.mobile.bg/obiavi/avtomobili-dzhipove')
        
        print("\nWaiting 10 seconds for all content to load...")
        await page.wait_for_timeout(10000)
        
        print(f"\n\nCaptured {len(requests)} XHR/Fetch requests:")
        for req in requests:
            print(f"  {req['method']} {req['url']}")
        
        # Now check for car listing links
        links_with_adv = await page.query_selector_all('a[href*="adv"]')
        print(f"\n\nLinks containing 'adv': {len(links_with_adv)}")
        
        for i, link in enumerate(links_with_adv[:5]):
            href = await link.get_attribute('href')
            print(f"  {i+1}. {href}")
        
        print("\n\nPress Enter to close...")
        input()
        
        await browser.close()

if __name__ == '__main__':
    asyncio.run(intercept_requests())
