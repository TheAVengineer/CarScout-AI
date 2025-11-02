#!/usr/bin/env python3
"""
Extract model information for popular brands that hit pagination limits.
"""

import requests
from bs4 import BeautifulSoup
import re
import json

def extract_models_from_brand_page(brand_slug):
    """Extract available models by looking at the brand page filters or existing links"""
    url = f'https://www.mobile.bg/obiavi/avtomobili-dzhipove/{brand_slug}/namira-se-v-balgariya?sort=6'
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            print(f'❌ Failed to fetch {brand_slug}: HTTP {response.status_code}')
            return []
            
        soup = BeautifulSoup(response.text, 'html.parser')
        models = []
        
        # Look for model links in the page
        # Pattern: /obiavi/avtomobili-dzhipove/bmw/318/...
        all_links = soup.find_all('a', href=True)
        model_pattern = re.compile(f'/obiavi/avtomobili-dzhipove/{brand_slug}/([^/]+)/.*')
        
        seen_models = set()
        for link in all_links:
            href = link.get('href', '')
            match = model_pattern.search(href)
            if match:
                model_slug = match.group(1)
                # Skip generic pages
                if model_slug not in ['namira-se-v-balgariya', 'page', 'p-2', 'p-3']:
                    if model_slug not in seen_models:
                        seen_models.add(model_slug)
                        # Try to get model name from link text or nearby elements
                        model_name = link.get_text(strip=True)
                        if not model_name or len(model_name) > 50:
                            model_name = model_slug
                        
                        models.append({
                            'slug': model_slug,
                            'name': model_name,
                            'url': f'https://www.mobile.bg/obiavi/avtomobili-dzhipove/{brand_slug}/{model_slug}/namira-se-v-balgariya?sort=6'
                        })
        
        return sorted(models, key=lambda x: x['slug'])
        
    except Exception as e:
        print(f'❌ Error extracting models for {brand_slug}: {str(e)}')
        return []

def main():
    # Extract models for brands that hit pagination limits
    brands_to_analyze = ['bmw', 'mercedes-benz', 'audi']
    
    all_brand_models = {}
    for brand in brands_to_analyze:
        print(f'\n🔍 Extracting models for {brand.upper()}...')
        models = extract_models_from_brand_page(brand)
        
        if models:
            all_brand_models[brand] = models
            print(f'   📋 Found {len(models)} models:')
            for i, model in enumerate(models[:10]):  # Show first 10
                slug = model['slug']
                name = model['name']
                print(f'      {i+1:2}. {slug:15} -> {name}')
            if len(models) > 10:
                print(f'      ... and {len(models) - 10} more models')
        else:
            print(f'   ❌ No models found for {brand}')
    
    print(f'\n📊 SUMMARY:')
    for brand, models in all_brand_models.items():
        print(f'   {brand:15}: {len(models):3} models found')
    
    # Save results
    output_file = 'extracted_models.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_brand_models, f, indent=2, ensure_ascii=False)
    
    print(f'\n✅ Model data saved to {output_file}')
    return all_brand_models

if __name__ == "__main__":
    models = main()