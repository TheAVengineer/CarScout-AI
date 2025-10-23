"""
Mobile.bg spider with Playwright browser automation for JavaScript rendering
"""
import re
import hashlib
from datetime import datetime
from uuid import uuid4

import scrapy
from scrapy.http import FormRequest


class MobileBgSpider(scrapy.Spider):
    name = "mobile_bg"
    allowed_domains = ["mobile.bg"]
    source_id = "mobile_bg"
    
    custom_settings = {
        "CONCURRENT_REQUESTS": 1,  # Keep low for Playwright (browsers are heavy)
        "DOWNLOAD_DELAY": 5.0,  # Increase delay for browser automation
        "ROBOTSTXT_OBEY": False,
        "COOKIES_ENABLED": True,
        "RETRY_TIMES": 3,
        "RETRY_HTTP_CODES": [500, 502, 503, 504, 408, 429],
        # Playwright-specific settings
        "PLAYWRIGHT_BROWSER_TYPE": "chromium",
        "PLAYWRIGHT_LAUNCH_OPTIONS": {
            "headless": True,  # Run without UI (set False for debugging)
            "timeout": 30000,  # 30 second timeout
        },
        "PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT": 30000,
        # Use persistent context to share cookies across requests
        "PLAYWRIGHT_CONTEXTS": {
            "default": {
                "viewport": {"width": 1920, "height": 1080},
                "ignore_https_errors": True,
            }
        },
        # Add random delays
        "AUTOTHROTTLE_ENABLED": True,
        "AUTOTHROTTLE_START_DELAY": 5,
        "AUTOTHROTTLE_MAX_DELAY": 15,
        "AUTOTHROTTLE_TARGET_CONCURRENCY": 1.0,
    }
    
    def __init__(self, *args, **kwargs):
        """Initialize spider with login credentials"""
        super().__init__(*args, **kwargs)
        
        # Check if login should be skipped (explicit parameter)
        skip_login_param = kwargs.get('skip_login', '').lower()
        skip_login = skip_login_param in ('true', '1', 'yes')
        
        # Get credentials from spider arguments or settings
        # Priority: spider args > settings > environment
        import os
        
        # Try spider arguments first (for testing)
        self.login_email = kwargs.get('login_email')
        self.login_password = kwargs.get('login_password')
        
        # If not in args, try to import from settings
        if not self.login_email or not self.login_password:
            try:
                # Add project root to path for config import
                import sys
                from pathlib import Path
                project_root = Path(__file__).parent.parent.parent.parent.parent
                if str(project_root) not in sys.path:
                    sys.path.insert(0, str(project_root))
                
                from configs.settings import settings
                self.login_email = self.login_email or settings.MOBILE_BG_EMAIL
                self.login_password = self.login_password or settings.MOBILE_BG_PASSWORD
            except Exception as e:
                self.logger.debug(f"Could not load from settings: {e}")
        
        # Last resort: environment variables (direct os.getenv)
        if not self.login_email or not self.login_password:
            self.login_email = self.login_email or os.getenv('MOBILE_BG_EMAIL')
            self.login_password = self.login_password or os.getenv('MOBILE_BG_PASSWORD')
        
        # Flag to track if login is required/enabled
        self.requires_login = not skip_login and bool(self.login_email and self.login_password)
        
        if self.requires_login:
            self.logger.info("🔐 Login credentials provided - will authenticate before scraping")
            self.logger.debug(f"Login email: {self.login_email}")
        else:
            self.logger.warning("⚠️  No login credentials - will try unauthenticated scraping")
    
    def start_requests(self):
        """Start scraping - login first if credentials provided"""
        if self.requires_login:
            # Step 1: Navigate to login page with Playwright
            self.logger.info("🔐 Step 1: Fetching login page with Playwright...")
            yield scrapy.Request(
                'https://www.mobile.bg/users/login',
                callback=self.parse_login_page,
                dont_filter=True,
                errback=self.errback_listing,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,  # Access page object for JavaScript
                    "playwright_page_goto_kwargs": {
                        "wait_until": "networkidle",  # Wait for page to fully load
                    },
                },
            )
        else:
            # No login - proceed directly to scraping
            yield from self.start_scraping()
    
    async def parse_login_page(self, response):
        """Parse login page and submit credentials using Playwright"""
        page = response.meta["playwright_page"]
        
        try:
            # First, dismiss the cookie consent dialog if present
            try:
                self.logger.info("🔐 Step 2: Checking for cookie consent dialog...")
                # Look for "Приемете всички" (Accept all) button in cookie dialog
                accept_button = await page.query_selector('[role="dialog"] div:has-text("Приемете всички")')
                if accept_button:
                    await accept_button.click()
                    self.logger.info("✅ Clicked accept on cookie consent dialog")
                    
                    # Wait for the dialog wrapper to be removed from DOM
                    await page.wait_for_selector('#cookiescript_injected_wrapper', state='hidden', timeout=5000)
                    self.logger.info("✅ Cookie consent dialog fully removed")
            except Exception as e:
                self.logger.debug(f"No cookie dialog or error dismissing: {e}")
            
            self.logger.info("🔐 Step 3: Clicking 'За частни лица' (For individuals) radio button...")
            
            # Click the "За частни лица" radio button to reveal the login form
            await page.click('input[name="logtype"][value="2"]', force=True)  # force=True to bypass overlays
            await page.wait_for_timeout(500)  # Wait for form to appear
            
            self.logger.info("🔐 Step 4: Filling login form with Playwright...")
            
            # Fill in email/username field
            await page.fill('input[name="usr"]', self.login_email)
            self.logger.info(f"DEBUG: Filled email field with: {self.login_email}")
            
            # Verify the field was filled
            email_value = await page.input_value('input[name="usr"]')
            self.logger.info(f"DEBUG: Email field value is now: {email_value}")
            
            # Fill in password field
            await page.fill('input[name="pwd"]', self.login_password)
            self.logger.info(f"DEBUG: Filled password field")
            
            # Verify password field was filled (show length, not actual password)
            pwd_value = await page.input_value('input[name="pwd"]')
            self.logger.info(f"DEBUG: Password field has {len(pwd_value)} characters")
            
            # Submit the form - Mobile.bg uses a JavaScript link, not a submit button
            # <a href="javascript:document.login.submit()" class="loginButton">Вход</a>
            self.logger.info("🔐 Step 5: Clicking login button...")
            
            # Force remove cookie dialog if still present (just to be safe)
            try:
                await page.evaluate("() => { const el = document.querySelector('#cookiescript_injected_wrapper'); if (el) el.remove(); }")
                self.logger.info("🧹 Force-removed any lingering cookie dialog")
            except:
                pass
            
            # Try submitting the form directly with JavaScript instead of clicking
            # This avoids issues with overlapping elements
            try:
                self.logger.info("📝 Submitting form with JavaScript...")
                await page.evaluate("() => document.login.submit()")
                self.logger.info("✅ Form submitted successfully")
            except Exception as submit_error:
                self.logger.error(f"❌ JavaScript submit failed: {submit_error}")
                # Fallback: try clicking with force
                self.logger.warning("⚠️ Falling back to force-click on login button...")
                await page.click('a.loginButton', force=True)
            
            # Wait for navigation after login
            # Strategy: Wait for either success redirect OR error message to appear
            try:
                # Increased timeout and better condition checking
                self.logger.info("⏳ Waiting for login response (up to 20 seconds)...")
                
                # Wait for network to settle after form submission
                await page.wait_for_load_state("networkidle", timeout=20000)
                
                # Give additional time for any JavaScript redirects
                await page.wait_for_timeout(2000)
                
                self.logger.info("🔐 Step 6: Login form submitted, checking result...")
                
            except Exception as wait_error:
                self.logger.warning(f"⚠️  Wait timeout (might be okay): {wait_error}")
                # Continue anyway - we'll check the result below
            
            # Check if login was successful by URL or content
            current_url = page.url
            page_content = await page.content()
            
            # Take screenshot and save HTML for debugging
            screenshot_path = "login_result.png"
            html_path = "login_result.html"
            await page.screenshot(path=screenshot_path)
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(page_content)
            self.logger.info(f"DEBUG: Screenshot saved to {screenshot_path}")
            self.logger.info(f"DEBUG: HTML saved to {html_path}")
            
            # Success indicators: redirected away from login page or contains logout link
            # Note: Mobile.bg might redirect to /users/adverts or back to homepage
            is_login_page = '/users/login' in current_url
            has_logout = 'изход' in page_content.lower() or 'logout' in page_content.lower()
            
            # Look for VISIBLE error messages
            # Mobile.bg shows login errors in <div class="sendPassError">
            has_visible_error = bool(re.search(r'<div[^>]*class="sendPassError"[^>]*>([^<]+)</div>', page_content, re.IGNORECASE))
            if has_visible_error:
                # Extract the actual error message
                error_match = re.search(r'<div[^>]*class="sendPassError"[^>]*>([^<]+)</div>', page_content, re.IGNORECASE)
                error_text = error_match.group(1).strip() if error_match else "Unknown error"
                self.logger.error(f"🚫 Login error message: {error_text}")
            
            # DEBUG: Log what we found
            self.logger.info(f"DEBUG: Current URL: {current_url}")
            self.logger.info(f"DEBUG: Is login page: {is_login_page}")
            self.logger.info(f"DEBUG: Has logout link: {has_logout}")
            self.logger.info(f"DEBUG: Has visible error: {has_visible_error}")
            
            # Search for specific error messages in HTML
            if has_visible_error:
                # Look for error div or message
                error_patterns = [
                    r'<div[^>]*class="[^"]*error[^"]*"[^>]*>([^<]+)</div>',
                    r'<span[^>]*class="[^"]*error[^"]*"[^>]*>([^<]+)</span>',
                    r'грешка:?\s*([^<]+)',
                ]
                for pattern in error_patterns:
                    error_match = re.search(pattern, page_content, re.IGNORECASE)
                    if error_match:
                        self.logger.error(f"DEBUG: Error found: {error_match.group(1).strip()}")
                        break
            
            if not is_login_page and (has_logout or '/users/' in current_url):
                self.logger.info(f"✅ Login successful! Current URL: {current_url}")
            elif has_visible_error or is_login_page:
                self.logger.error(f"❌ Login failed - URL: {current_url}")
                self.logger.debug(f"Has logout link: {has_logout}, Has visible error: {has_visible_error}")
                self.logger.debug(f"Page content snippet: {page_content[:500]}")
                await page.close()
                return
            else:
                # Unclear but let's try to proceed
                self.logger.warning(f"⚠️  Login status unclear but proceeding - URL: {current_url}")
                self.logger.debug(f"Has logout: {has_logout}, Is login page: {is_login_page}")
            
            # Close this page - Scrapy will create new ones for scraping
            await page.close()
            
            # Start scraping after successful login
            for request in self.start_scraping():
                yield request
                
        except Exception as e:
            self.logger.error(f"❌ Error during login: {e}")
            await page.close()
            return
    
    def start_scraping(self):
        """Start scraping car listings using hybrid brand+model searches for complete coverage"""
        
        # Load hybrid configuration
        import json
        from pathlib import Path
        
        try:
            # Get absolute path to project root
            spider_file = Path(__file__).resolve()
            project_root = spider_file.parent.parent.parent.parent.parent
            
            # Try hybrid config first, fallback to brand config
            hybrid_config_path = project_root / "mobile_bg_hybrid_config.json"
            brand_config_path = project_root / "mobile_bg_brand_config.json"
            
            search_urls = []
            
            if hybrid_config_path.exists():
                self.logger.info(f"📱 Using hybrid brand+model configuration")
                with open(hybrid_config_path, 'r', encoding='utf-8') as f:
                    hybrid_config = json.load(f)
                
                # Get all search URLs from hybrid config
                all_searches = hybrid_config.get('search_urls', [])
                
                # Filter based on target and priority
                target_listings = int(getattr(self, 'target_listings', 0))
                
                if target_listings > 0 and target_listings < 500:
                    # Small test - use only high-priority model searches
                    search_urls = [s for s in all_searches if s.get('priority', False) and s['type'] == 'model'][:20]
                    self.logger.info(f"🧪 Test mode: Using {len(search_urls)} priority model searches")
                elif target_listings > 0 and target_listings < 5000:
                    # Medium test - use priority searches (brands + models)
                    search_urls = [s for s in all_searches if s.get('priority', False)]
                    self.logger.info(f"🎯 Medium mode: Using {len(search_urls)} priority searches")
                else:
                    # Full mode - ONLY use model-specific searches to bypass 150-page limit
                    # Brand-only searches hit the limit and miss thousands of listings
                    search_urls = [s for s in all_searches if s['type'] == 'model']
                    
                    # Count skipped brand-only searches
                    skipped_brands = [s for s in all_searches if s['type'] == 'brand']
                    
                    self.logger.info(f"🚀 Full mode: Model-first strategy for complete coverage")
                    self.logger.info(f"   ✅ Using {len(search_urls)} model-specific searches")
                    self.logger.info(f"   ⏭️  Skipping {len(skipped_brands)} brand-only searches (would hit 150-page limit)")
                    
                    if skipped_brands:
                        skipped_brand_names = ', '.join(set(s['brand'] for s in skipped_brands[:10]))
                        if len(skipped_brands) > 10:
                            skipped_brand_names += f"... (+{len(skipped_brands) - 10} more)"
                        self.logger.info(f"   📝 Skipped brands: {skipped_brand_names}")
                
                estimated_total = sum(s.get('estimated_listings', 0) for s in search_urls)
                self.logger.info(f"📊 Strategy: Hybrid brand+model searches")
                self.logger.info(f"   - Brand-only searches: {len([s for s in search_urls if s['type'] == 'brand'])}")
                self.logger.info(f"   - Model-specific searches: {len([s for s in search_urls if s['type'] == 'model'])}")
                self.logger.info(f"   - Estimated total listings: {estimated_total:,}")
                
            else:
                self.logger.warning(f"⚠️ Hybrid config not found, falling back to brand-only config")
                with open(brand_config_path, 'r', encoding='utf-8') as f:
                    brand_config = json.load(f)
                
                # Convert brand config to search URLs format
                brands_to_scrape = brand_config.get('priority_brands', [])
                if not hasattr(self, 'target_listings') or int(getattr(self, 'target_listings', 0)) > 1000:
                    brands_to_scrape.extend([b for b in brand_config.get('all_brands', []) if not b.get('priority')])
                
                search_urls = [{
                    'type': 'brand',
                    'brand': brand['brand'],
                    'brand_slug': brand['slug'],
                    'model': None,
                    'model_slug': None,
                    'url': brand['url'],
                    'priority': brand.get('priority', False)
                } for brand in brands_to_scrape]
                
                self.logger.info(f"�️ Using {len(search_urls)} brand-only searches")
            
        except Exception as e:
            self.logger.warning(f"⚠️ Could not load search config: {e}")
            # Fallback to simple searches
            search_urls = [
                {'type': 'brand', 'brand': 'BMW', 'url': 'https://www.mobile.bg/obiavi/avtomobili-dzhipove/bmw/namira-se-v-balgariya?sort=6'},
                {'type': 'brand', 'brand': 'Mercedes-Benz', 'url': 'https://www.mobile.bg/obiavi/avtomobili-dzhipove/mercedes-benz/namira-se-v-balgariya?sort=6'},
                {'type': 'brand', 'brand': 'Audi', 'url': 'https://www.mobile.bg/obiavi/avtomobili-dzhipove/audi/namira-se-v-balgariya?sort=6'},
            ]
        
        # Generate requests for each search URL
        for search_info in search_urls:
            search_type = search_info.get('type', 'brand')
            brand_name = search_info.get('brand', 'Unknown')
            model_name = search_info.get('model', None)
            search_url = search_info.get('url', '')
            
            if search_url:
                if search_type == 'model':
                    search_description = f"{brand_name} {model_name}"
                    self.logger.info(f"🎯 Queuing model search: {search_description}")
                else:
                    search_description = brand_name
                    self.logger.info(f"🔍 Queuing brand search: {search_description}")
                
                yield scrapy.Request(
                    search_url,
                    callback=self.parse_search_page,
                    dont_filter=True,
                    errback=self.errback_listing,
                    meta={
                        "playwright": True,
                        "playwright_include_page": True,
                        "playwright_page_goto_kwargs": {
                            "wait_until": "networkidle",
                        },
                        "page_number": 1,  # Track current page within this search
                        "total_listings": 0,  # Track total listings across pages
                        "search_type": search_type,  # Track if this is brand or model search
                        "brand_name": brand_name,  # Track which brand we're scraping
                        "model_name": model_name,  # Track which model (if any)
                        "search_description": search_description,  # Human-readable description
                        "search_url": search_url,  # Base URL for this search
                    },
                )
    
    async def parse_search_page(self, response):
        """Parse search results to find listing URLs (with Playwright for JavaScript content)"""
        page = response.meta.get("playwright_page")
        page_number = response.meta.get("page_number", 1)
        total_listings = response.meta.get("total_listings", 0)
        search_type = response.meta.get("search_type", "brand")
        brand_name = response.meta.get("brand_name", "Unknown")
        model_name = response.meta.get("model_name", None)
        search_description = response.meta.get("search_description", brand_name)
        search_url = response.meta.get("search_url", "")
        
        if search_type == "model":
            self.logger.info(f"📄 Processing {search_description} page {page_number} (total listings so far: {total_listings})")
        else:
            self.logger.info(f"📄 Processing {brand_name} page {page_number} (total listings so far: {total_listings})")
        
        if page:
            self.logger.info("🔍 Waiting for car listings to load via JavaScript...")
            
            try:
                # Wait for Mobile.bg listing links (format: /obiava-XXXXXXXXXXXXXXXXX-brand-model)
                await page.wait_for_selector('a[href*="/obiava-"]', timeout=10000)
                self.logger.info("✅ Listings loaded!")
                
                # Get updated HTML after JavaScript rendering
                html_content = await page.content()
                response = response.replace(body=html_content.encode('utf-8'))
                
                await page.close()
                
            except Exception as e:
                self.logger.warning(f"⚠️  Timeout waiting for listings: {e}")
                self.logger.info("Proceeding with available content...")
                if page:
                    await page.close()
        
        self.logger.info(f"📄 Parsing search page, response length: {len(response.text)} chars")
        
        # Extract all links
        links = response.css('a::attr(href)').getall()
        self.logger.debug(f"Found {len(links)} total links on page")
        
        # Track unique listings (each listing appears 6+ times in HTML)
        seen_urls = set()
        listing_count = 0
        
        for link in links:
            # Look for car listing URLs with new pattern
            if self._is_listing_url(link):
                full_url = response.urljoin(link)
                
                # Skip duplicates
                if full_url in seen_urls:
                    continue
                seen_urls.add(full_url)
                
                self.logger.info(f"🚗 Found listing URL: {full_url}")
                listing_count += 1
                
                yield scrapy.Request(
                    full_url,
                    callback=self.parse_listing_detail,
                    dont_filter=True,
                    errback=self.errback_listing,
                    meta={
                        "playwright": True,
                        "playwright_include_page": True,
                        "playwright_page_goto_kwargs": {
                            "wait_until": "networkidle",
                        },
                    },
                )
        
        self.logger.info(f"✅ Found {listing_count} car listings on page {page_number}")
        total_listings += listing_count
        
        # Pagination: Look for "Next Page" link
        # Mobile.bg uses format: /obiavi/avtomobili-dzhipove/p-2, /p-3, etc.
        next_page = None
        
        # Look for pagination links - Mobile.bg uses .pagination class
        next_page = None
        
        # Look for "Напред" (Next) button in pagination
        next_page_link = response.css('.pagination a')
        for link in next_page_link:
            link_text = link.css('::text').get()
            if link_text and 'Напред' in link_text:
                next_page_url = link.css('::attr(href)').get()
                if next_page_url:
                    next_page = response.urljoin(next_page_url)
                    break
        
        # Follow next page if found and not at limit
        # Mobile.bg limits to 150 pages (max ~3000 listings per search)
        MAX_PAGES = 150
        
        if next_page and page_number < MAX_PAGES:
            next_page_number = page_number + 1
            self.logger.info(f"📄 Following {search_description} to page {next_page_number}: {next_page}")
            
            yield scrapy.Request(
                next_page,
                callback=self.parse_search_page,
                dont_filter=True,
                errback=self.errback_listing,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                    "playwright_page_goto_kwargs": {
                        "wait_until": "networkidle",
                    },
                    "page_number": next_page_number,
                    "total_listings": total_listings,
                    "search_type": search_type,  # Pass search info to next page
                    "brand_name": brand_name,
                    "model_name": model_name,
                    "search_description": search_description,
                    "search_url": search_url,
                },
            )
        elif next_page and page_number >= MAX_PAGES:
            self.logger.warning(f"⚠️ {search_description} hit {MAX_PAGES}-page limit (Mobile.bg VIP restriction). Total listings: {total_listings}")
            self.logger.warning(f"💡 Consider using model-specific searches to bypass this limit")
        else:
            self.logger.info(f"✅ {search_description} completed. Total listings found: {total_listings}")
        
        if listing_count == 0:
            self.logger.warning(f"❌ No listing links found on page {page_number}")
            # Save page HTML for debugging
            self.logger.debug(f"Response preview (first 1000 chars):\n{response.text[:1000]}")
    
    def _is_listing_url(self, url):
        """
        Check if URL is a car listing detail page.
        
        Mobile.bg format: /obiava-XXXXXXXXXXXXXXXXX-brand-model-details
        Example: /obiava-11758305565394920-audi-a6-45tdi-3-0-matrix-s-line
        """
        if not url:
            return False
        
        # Exclude non-listing pages
        if any(x in url.lower() for x in ['users', 'login', 'register', 'check-phone', 'javascript:', '#', '/p-', 'mailto:']):
            return False
        
        # Match Mobile.bg listing URL pattern: /obiava-XXXXXXXXXXXXXXXXX-...
        if '/obiava-' in url:
            # Extract the ID part after /obiava-
            try:
                id_part = url.split('/obiava-')[1].split('-')[0]
                # Check if it's a numeric ID (17-20 digits)
                if id_part.isdigit() and len(id_part) >= 17:
                    return True
            except:
                pass
        
        return False
    
    def errback_listing(self, failure):
        """Handle request failures"""
        self.logger.warning(f"Request failed: {failure.request.url} - {failure.value}")
    
    async def parse_listing_detail(self, response):
        """Parse individual listing detail page with Playwright support"""
        # If Playwright was used, get rendered content
        page = response.meta.get("playwright_page")
        if page:
            self.logger.debug(f"📄 Waiting for listing detail page to load...")
            try:
                # Wait for main content to load
                await page.wait_for_selector('body', timeout=10000)
                html_content = await page.content()
                response = response.replace(body=html_content.encode('utf-8'))
                await page.close()
            except Exception as e:
                self.logger.warning(f"⚠️  Error getting Playwright content: {e}")
                if page:
                    await page.close()
        
        self.logger.info(f"🔍 Parsing listing detail from: {response.url}")
        
        # Extract site_ad_id from URL
        # Mobile.bg format: /obiava-XXXXXXXXXXXXXXXXX-brand-model
        # Example: /obiava-11758305565394920-audi-a6-45tdi-3-0-matrix-s-line
        site_ad_id_match = re.search(r'/obiava-(\d+)', response.url)
        site_ad_id = site_ad_id_match.group(1) if site_ad_id_match else None
        
        if not site_ad_id:
            self.logger.warning(f"❌ Could not extract ad ID from {response.url}")
            return
        
        self.logger.info(f"✅ Extracted listing ID: {site_ad_id}")
        
        # HTML extraction with improved selectors
        title_full = response.css('h1::text, .adTitle::text, .title::text').get() or response.css('title::text').get() or ''
        title_full = title_full.strip()
        
        # Try to extract brand and model from title
        title_parts = title_full.split()
        brand = title_parts[0] if len(title_parts) > 0 else None
        model = ' '.join(title_parts[1:3]) if len(title_parts) > 1 else None
        
        # Price extraction - Mobile.bg uses .Price class
        # Format: "42 948.01 €<br>83 999 лв." (EUR and BGN in separate text nodes)
        # NOTE: Must use getall() to get both text nodes
        price_texts = response.css('.Price::text').getall()
        price_text = ' '.join(price_texts) if price_texts else ''
        
        # Try to extract BGN price first (more reliable for Bulgarian market)
        # Pattern handles both "83 999 лв" and "380 406.98 лв" (with decimals)
        bgn_match = re.search(r'(\d+(?:[\s\xa0]+\d+)*(?:\.\d+)?)\s*лв', price_text)
        if bgn_match:
            # Split on decimal point and take only integer part
            price_str = bgn_match.group(1).split('.')[0].replace(' ', '').replace('\xa0', '').strip()
            price = int(price_str) if price_str.isdigit() else None
            currency = 'BGN'
        else:
            # Fallback to EUR price (with decimals)
            eur_match = re.search(r'(\d+(?:[\s\xa0]+\d+)*(?:\.\d+)?)\s*€', price_text)
            if eur_match:
                # Split on decimal point and take only integer part
                price_str = eur_match.group(1).split('.')[0].replace(' ', '').replace('\xa0', '').strip()
                price = int(price_str) if price_str.isdigit() else None
                currency = 'EUR'
            else:
                price = None
                currency = 'BGN'
        
        # Year extraction
        year_match = re.search(r'(\d{4})\s*г', response.text)
        year = int(year_match.group(1).strip()) if year_match else None
        
        # Mileage extraction
        mileage_match = re.search(r'(\d+)\s*км', response.text)
        mileage_km = int(mileage_match.group(1).strip()) if mileage_match else None
        
        # Fuel type detection
        fuel = None
        if 'Дизел' in response.text:
            fuel = 'diesel'
        elif 'Бензин' in response.text:
            fuel = 'petrol'
        elif 'Газ' in response.text or 'ГАЗ' in response.text:
            fuel = 'gas'
        elif 'Електро' in response.text:
            fuel = 'electric'
        elif 'Хибрид' in response.text:
            fuel = 'hybrid'
        
        # Gearbox detection
        gearbox = None
        if 'Автоматична' in response.text:
            gearbox = 'automatic'
        elif 'Ръчна' in response.text:
            gearbox = 'manual'
        
        # Description
        description = response.css('.description::text, .adDescription::text, [class*="description"]::text').get() or ''
        description = description.strip()
        
        # Images
        images = response.css('img[src*="jpg"]::attr(src), img[src*="jpeg"]::attr(src), img[src*="png"]::attr(src)').getall()
        # Filter out small images (icons, etc.)
        images = [img for img in images if 'logo' not in img.lower() and 'icon' not in img.lower()]
        
        # Phone hash (if available)
        phone_text = response.css('.phone::text, [class*="phone"]::text').get() or ''
        phone_hash = hashlib.sha256(phone_text.encode()).hexdigest() if phone_text else None
        
        # Region/location
        region_text = response.css('.region::text, .location::text, [class*="location"]::text').get() or ''
        region = region_text.strip() if region_text else None
        
        # Save raw HTML path
        raw_html_path = f"raw/{self.source_id}/{site_ad_id}.html"
        
        self.logger.info(f"✅ Scraped: {brand} {model} {year} - {price} {currency}")
        
        yield {
            'listing_id': str(uuid4()),
            'source_id': self.source_id,
            'site_ad_id': site_ad_id,
            'url': response.url,
            'raw_html_path': raw_html_path,
            'raw_html': response.text,  # In production, upload to S3
            
            # Parsed fields
            'brand': brand,
            'model': model,
            'year': year,
            'mileage_km': mileage_km,
            'fuel': fuel,
            'gearbox': gearbox,
            'price': price,
            'currency': currency,
            'region': region,
            'title': title_full,
            'description': description,
            'images': images,
            'phone_hash': phone_hash,
            
            'first_seen_at': datetime.utcnow().isoformat(),
            'last_seen_at': datetime.utcnow().isoformat(),
            'is_active': True,
        }
