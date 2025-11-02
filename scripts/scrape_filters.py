#!/usr/bin/env python3
"""
Script to scrape all available filters (brands, models) from Mobile.bg
This will help us generate comprehensive search URLs to capture all listings.
"""

import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from playwright.async_api import async_playwright
import json
import re

async def scrape_mobile_bg_filters():
    """Scrape all available car brands and models from Mobile.bg filters"""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print("🔍 Loading Mobile.bg search page...")
        await page.goto("https://www.mobile.bg/search/avtomobili-dzhipove/namira-se-v-balgariya?sort=6")
        
        # Dismiss cookie consent if present
        try:
            await page.wait_for_selector('[role="dialog"] div:has-text("Приемете всички")', timeout=3000)
            await page.click('[role="dialog"] div:has-text("Приемете всички")')
            print("✅ Dismissed cookie consent")
            await page.wait_for_timeout(1000)
        except:
            print("ℹ️ No cookie consent dialog found")
        
        filters = {}
        
        # 1. Scrape car brands (makes)
        print("\n🏷️ Scraping car brands...")
        brands = []
        
        # Look for brand dropdown or links
        try:
            # Try to find brand selection elements
            brand_elements = await page.query_selector_all('select[name="brand"] option, .filter-brands a, .brands-list a')
            
            if not brand_elements:
                # Alternative: look for any links that contain brand names in URLs
                all_links = await page.query_selector_all('a[href*="/search/avtomobili-dzhipove/"]')
                for link in all_links[:50]:  # Limit to avoid too many
                    href = await link.get_attribute('href')
                    text = (await link.text_content() or '').strip()
                    if href and text and len(text) > 1 and len(text) < 20:
                        # Extract brand from URL pattern like /bmw/ or /mercedes-benz/
                        match = re.search(r'/search/avtomobili-dzhipove/([^/]+)/', href)
                        if match:
                            brand_slug = match.group(1)
                            if brand_slug not in ['namira-se-v-balgariya', 'filter']:
                                brands.append({
                                    'name': text,
                                    'slug': brand_slug,
                                    'url': href
                                })
            else:
                for element in brand_elements:
                    value = await element.get_attribute('value')
                    text = (await element.text_content() or '').strip()
                    if value and text and value != '' and text != '':
                        brands.append({
                            'name': text,
                            'slug': value,
                            'url': f"/search/avtomobili-dzhipove/{value}/namira-se-v-balgariya?sort=6"
                        })
        except Exception as e:
            print(f"⚠️ Error scraping brands: {e}")
        
        # Remove duplicates
        seen_slugs = set()
        unique_brands = []
        for brand in brands:
            if brand['slug'] not in seen_slugs:
                seen_slugs.add(brand['slug'])
                unique_brands.append(brand)
        
        brands = unique_brands[:50]  # Limit to top 50 brands
        filters['brands'] = brands
        
        print(f"✅ Found {len(brands)} brands:")
        for brand in brands[:10]:  # Show first 10
            print(f"   - {brand['name']} ({brand['slug']})")
        if len(brands) > 10:
            print(f"   ... and {len(brands) - 10} more")
        
        # 2. Scrape models for top brands
        print(f"\n🚗 Scraping models for top brands...")
        brand_models = {}
        
        # Test with a few popular brands to get models
        test_brands = ['bmw', 'mercedes-benz', 'audi', 'volkswagen', 'toyota']
        
        for brand_slug in test_brands:
            if any(b['slug'] == brand_slug for b in brands):
                print(f"   Checking models for {brand_slug}...")
                try:
                    # Navigate to brand-specific page
                    brand_url = f"https://www.mobile.bg/search/avtomobili-dzhipove/{brand_slug}/namira-se-v-balgariya?sort=6"
                    await page.goto(brand_url)
                    await page.wait_for_timeout(2000)
                    
                    models = []
                    
                    # Look for model dropdown or links
                    model_elements = await page.query_selector_all('select[name="model"] option, .filter-models a, .models-list a')
                    
                    if not model_elements:
                        # Alternative: look for model links in the page
                        all_links = await page.query_selector_all(f'a[href*="/{brand_slug}/"]')
                        for link in all_links[:30]:
                            href = await link.get_attribute('href')
                            text = (await link.text_content() or '').strip()
                            if href and text and len(text) > 1:
                                # Extract model from URL pattern like /bmw/x5/
                                match = re.search(f'/{brand_slug}/([^/]+)/', href)
                                if match:
                                    model_slug = match.group(1)
                                    if model_slug not in ['namira-se-v-balgariya']:
                                        models.append({
                                            'name': text,
                                            'slug': model_slug,
                                            'url': href
                                        })
                    else:
                        for element in model_elements:
                            value = await element.get_attribute('value')
                            text = (await element.text_content() or '').strip()
                            if value and text and value != '' and text != '':
                                models.append({
                                    'name': text,
                                    'slug': value,
                                    'url': f"/search/avtomobili-dzhipove/{brand_slug}/{value}/namira-se-v-balgariya?sort=6"
                                })
                    
                    # Remove duplicates
                    seen_model_slugs = set()
                    unique_models = []
                    for model in models:
                        if model['slug'] not in seen_model_slugs:
                            seen_model_slugs.add(model['slug'])
                            unique_models.append(model)
                    
                    models = unique_models[:20]  # Limit to top 20 models per brand
                    brand_models[brand_slug] = models
                    
                    print(f"      Found {len(models)} models for {brand_slug}")
                    for model in models[:5]:
                        print(f"         - {model['name']} ({model['slug']})")
                
                except Exception as e:
                    print(f"      ⚠️ Error scraping models for {brand_slug}: {e}")
        
        filters['brand_models'] = brand_models
        
        # 3. Save results
        output_file = "mobile_bg_filters.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(filters, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 Saved filters to {output_file}")
        print(f"📊 Total brands: {len(filters['brands'])}")
        print(f"📊 Brands with models: {len(filters['brand_models'])}")
        
        # 4. Generate sample search URLs
        print(f"\n🔗 Sample search URLs:")
        count = 0
        for brand in filters['brands'][:5]:
            brand_url = f"https://www.mobile.bg/search/avtomobili-dzhipove/{brand['slug']}/namira-se-v-balgariya?sort=6"
            print(f"   {brand['name']}: {brand_url}")
            count += 1
            
            # Show models if available
            if brand['slug'] in filters['brand_models']:
                for model in filters['brand_models'][brand['slug']][:3]:
                    model_url = f"https://www.mobile.bg/search/avtomobili-dzhipove/{brand['slug']}/{model['slug']}/namira-se-v-balgariya?sort=6"
                    print(f"      └─ {model['name']}: {model_url}")
                    count += 1
        
        print(f"\n🎯 This approach will generate {count * 20}+ search URLs to capture ALL listings!")
        
        await browser.close()
        return filters

if __name__ == "__main__":
    print("=" * 60)
    print("🔍 MOBILE.BG FILTER SCRAPER")
    print("=" * 60)
    
    filters = asyncio.run(scrape_mobile_bg_filters())
    
    print("\n" + "=" * 60)
    print("✅ FILTER SCRAPING COMPLETE!")
    print("=" * 60)