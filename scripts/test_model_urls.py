#!/usr/bin/env python3
"""
Test model-specific URLs to see if they provide access to more listings.
"""

import requests
from bs4 import BeautifulSoup
import time

def test_model_urls():
    # Test some common BMW models to see if model-specific URLs work
    bmw_models = ['318', '320', '325', '330', '520', '525', '530', 'x3', 'x5', '116', '118', '730', 'x1', 'z4']
    
    print('🚗 Testing BMW model-specific URLs:')
    working_models = []
    
    for model in bmw_models:
        url = f'https://www.mobile.bg/obiavi/avtomobili-dzhipove/bmw/{model}/namira-se-v-balgariya?sort=6'
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                listings = soup.find_all('a', href=lambda x: x and '/obiava-' in x)
                
                if listings:
                    working_models.append({'model': model, 'listings': len(listings)})
                    print(f'  ✅ {model:4}: {len(listings):3} listings found')
                else:
                    print(f'  ❌ {model:4}: No listings')
            else:
                print(f'  ❌ {model:4}: HTTP {response.status_code}')
        except Exception as e:
            print(f'  ❌ {model:4}: Error - {str(e)[:30]}')
        
        time.sleep(0.3)  # Be nice to the server
    
    print(f'\n📊 Working BMW models: {len(working_models)}')
    total_model_listings = 0
    for model_info in working_models:
        model = model_info['model']
        listings = model_info['listings']
        total_model_listings += listings
        print(f'   {model:4}: {listings:3} listings')
    
    print(f'\n🔍 Analysis:')
    print(f'   Total model-specific listings found: {total_model_listings}')
    print(f'   Average per working model: {total_model_listings // len(working_models) if working_models else 0}')
    
    # Compare with brand-level search
    print(f'\n🔄 Comparing with brand-level search...')
    brand_url = 'https://www.mobile.bg/obiavi/avtomobili-dzhipove/bmw/namira-se-v-balgariya?sort=6'
    try:
        response = requests.get(brand_url, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            brand_listings = soup.find_all('a', href=lambda x: x and '/obiava-' in x)
            print(f'   Brand-level search (page 1): {len(brand_listings)} listings')
            print(f'   Brand-level estimated total: {len(brand_listings) * 150} listings (150 pages)')
            
            if total_model_listings > len(brand_listings):
                print(f'   ✅ Model-specific searches may provide MORE coverage!')
            else:
                print(f'   ⚠️  Model-specific searches may have LESS coverage')
    except Exception as e:
        print(f'   ❌ Error checking brand-level: {str(e)}')
    
    return working_models

if __name__ == "__main__":
    models = test_model_urls()