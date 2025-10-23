#!/usr/bin/env python3
"""
Analyze brand pages to extract available models and understand pagination structure.
This will help us implement model-level searches for complete coverage.
"""

import requests
from bs4 import BeautifulSoup
import time
import json
import re
from urllib.parse import urljoin, urlparse

def extract_models_from_brand_page(brand_name, brand_url):
    """Extract all available models for a brand from the search page."""
    try:
        print(f"\n🔍 Analyzing {brand_name}...")
        response = requests.get(brand_url, timeout=10)
        if response.status_code != 200:
            print(f"❌ Failed to fetch {brand_name}: HTTP {response.status_code}")
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for model filters in the left sidebar
        models = []
        
        # Method 1: Look for model checkboxes in filters
        model_checkboxes = soup.find_all('input', {'name': 'model[]'})
        for checkbox in model_checkboxes:
            if 'value' in checkbox.attrs:
                model_id = checkbox['value']
                # Find the label for this checkbox
                label = checkbox.find_next('label') or checkbox.find_parent().find_next('label')
                if label:
                    model_name = label.get_text(strip=True)
                    models.append({
                        'model_id': model_id,
                        'model_name': model_name,
                        'brand': brand_name
                    })
        
        # Method 2: Look for model links in sidebar
        if not models:
            model_links = soup.find_all('a', href=re.compile(f'/obiavi/avtomobili-dzhipove/{brand_name.lower().replace("-", "-")}/'))
            for link in model_links:
                href = link.get('href', '')
                model_match = re.search(f'/obiavi/avtomobili-dzhipove/{brand_name.lower()}/([^/]+)/', href)
                if model_match:
                    model_slug = model_match.group(1)
                    model_name = link.get_text(strip=True)
                    if model_name and model_slug != 'namira-se-v-balgariya':
                        models.append({
                            'model_slug': model_slug,
                            'model_name': model_name,
                            'brand': brand_name
                        })
        
        # Method 3: Check if there's a model dropdown or select
        model_selects = soup.find_all('select', {'name': re.compile('model')})
        for select in model_selects:
            options = select.find_all('option')
            for option in options:
                if option.get('value') and option.get('value') != '':
                    model_id = option.get('value')
                    model_name = option.get_text(strip=True)
                    if model_name.lower() not in ['всички модели', 'all models', '']:
                        models.append({
                            'model_id': model_id,
                            'model_name': model_name,
                            'brand': brand_name
                        })
        
        print(f"📋 Found {len(models)} models for {brand_name}")
        if models:
            for i, model in enumerate(models[:5]):  # Show first 5
                print(f"   {i+1}. {model}")
            if len(models) > 5:
                print(f"   ... and {len(models) - 5} more")
        
        return models
        
    except Exception as e:
        print(f"❌ Error analyzing {brand_name}: {str(e)}")
        return []

def check_pagination_depth(brand_url, brand_name):
    """Check how deep the pagination actually goes."""
    try:
        print(f"\n🔍 Checking pagination depth for {brand_name}...")
        
        # Try to access page 50 and 100 to see if they exist
        base_url = brand_url.split('?')[0]  # Remove query params
        query_params = "?sort=6"
        
        test_pages = [1, 10, 50, 100, 150]
        valid_pages = []
        
        for page_num in test_pages:
            test_url = f"{base_url}/page{page_num}{query_params}"
            response = requests.get(test_url, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                listing_links = soup.find_all('a', href=lambda x: x and '/obiava-' in x)
                
                if listing_links:
                    valid_pages.append(page_num)
                    print(f"   📄 Page {page_num}: ✅ Found {len(listing_links)} listings")
                else:
                    print(f"   📄 Page {page_num}: ❌ No listings found")
            else:
                print(f"   📄 Page {page_num}: ❌ HTTP {response.status_code}")
            
            time.sleep(0.5)  # Be nice to the server
        
        if valid_pages:
            print(f"📊 {brand_name} has valid pages up to: {max(valid_pages)}")
            return max(valid_pages)
        else:
            return 1
            
    except Exception as e:
        print(f"❌ Error checking pagination for {brand_name}: {str(e)}")
        return 1

def main():
    """Analyze popular brands to understand model structure and pagination."""
    
    # Focus on the most popular brands that likely hit pagination limits
    popular_brands = [
        {'name': 'bmw', 'display_name': 'BMW'},
        {'name': 'mercedes-benz', 'display_name': 'Mercedes-Benz'},
        {'name': 'audi', 'display_name': 'Audi'},
        {'name': 'volkswagen', 'display_name': 'Volkswagen'},
        {'name': 'toyota', 'display_name': 'Toyota'},
        {'name': 'opel', 'display_name': 'Opel'},
    ]
    
    all_models = {}
    pagination_info = {}
    
    for brand in popular_brands:
        brand_url = f"https://www.mobile.bg/obiavi/avtomobili-dzhipove/{brand['name']}/namira-se-v-balgariya?sort=6"
        
        # Extract models
        models = extract_models_from_brand_page(brand['display_name'], brand_url)
        if models:
            all_models[brand['name']] = models
        
        # Check pagination depth
        max_pages = check_pagination_depth(brand_url, brand['display_name'])
        pagination_info[brand['name']] = max_pages
        
        time.sleep(2)  # Be respectful to the server
    
    # Save results
    results = {
        'analysis_date': '2025-10-22',
        'models_by_brand': all_models,
        'pagination_limits': pagination_info,
        'summary': {
            'total_brands_analyzed': len(popular_brands),
            'brands_with_models': len(all_models),
            'max_pagination_found': max(pagination_info.values()) if pagination_info else 0
        }
    }
    
    output_file = 'brand_model_analysis.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Analysis complete! Results saved to {output_file}")
    print(f"📊 Summary:")
    print(f"   - Brands analyzed: {results['summary']['total_brands_analyzed']}")
    print(f"   - Brands with model data: {results['summary']['brands_with_models']}")
    print(f"   - Max pagination depth: {results['summary']['max_pagination_found']}")
    
    # Show pagination limits
    print(f"\n📄 Pagination limits found:")
    for brand, max_page in pagination_info.items():
        print(f"   {brand:15}: {max_page:3} pages")

if __name__ == "__main__":
    main()