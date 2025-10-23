#!/usr/bin/env python3
"""
Generate comprehensive brand + model configuration for complete Mobile.bg coverage.
This will create searches for:
1. All brands (129 brands)
2. Popular brand models (BMW, Mercedes, Audi, etc.)
"""

import json
import requests
from bs4 import BeautifulSoup
import time

# Common car models for popular brands
BRAND_MODELS = {
    'bmw': [
        # 1 Series
        '114', '116', '118', '120', '125', '130', '135',
        # 2 Series  
        '218', '220', '225', '228', '230', '235',
        # 3 Series
        '316', '318', '320', '323', '325', '328', '330', '335', '340',
        # 4 Series
        '418', '420', '425', '428', '430', '435', '440',
        # 5 Series
        '520', '523', '525', '528', '530', '535', '540', '545', '550',
        # 6 Series
        '630', '635', '640', '645', '650',
        # 7 Series
        '730', '735', '740', '745', '750', '760',
        # 8 Series
        '840', '850',
        # X Series
        'x1', 'x2', 'x3', 'x4', 'x5', 'x6', 'x7',
        # Z Series
        'z3', 'z4', 'z8',
        # M Series
        'm2', 'm3', 'm4', 'm5', 'm6'
    ],
    
    'mercedes-benz': [
        # A-Class
        'a-140', 'a-150', 'a-160', 'a-170', 'a-180', 'a-200', 'a-220', 'a-250',
        # B-Class
        'b-150', 'b-160', 'b-170', 'b-180', 'b-200', 'b-220', 'b-250',
        # C-Class
        'c-180', 'c-200', 'c-220', 'c-230', 'c-240', 'c-250', 'c-270', 'c-280', 'c-300', 'c-320', 'c-350',
        # CLA-Class
        'cla-180', 'cla-200', 'cla-220', 'cla-250',
        # CLS-Class
        'cls-220', 'cls-250', 'cls-300', 'cls-320', 'cls-350', 'cls-400', 'cls-500', 'cls-550',
        # E-Class
        'e-200', 'e-220', 'e-230', 'e-240', 'e-250', 'e-270', 'e-280', 'e-300', 'e-320', 'e-350', 'e-400', 'e-500', 'e-550',
        # G-Class
        'g-270', 'g-320', 'g-350', 'g-400', 'g-500', 'g-550', 'g-63',
        # GLA-Class
        'gla-180', 'gla-200', 'gla-220', 'gla-250',
        # GLC-Class
        'glc-200', 'glc-220', 'glc-250', 'glc-300', 'glc-350',
        # GLE-Class
        'gle-250', 'gle-300', 'gle-320', 'gle-350', 'gle-400', 'gle-450', 'gle-500', 'gle-550',
        # GLS-Class
        'gls-320', 'gls-350', 'gls-400', 'gls-450', 'gls-500', 'gls-550',
        # ML-Class
        'ml-230', 'ml-270', 'ml-280', 'ml-300', 'ml-320', 'ml-350', 'ml-400', 'ml-420', 'ml-500', 'ml-550',
        # S-Class
        's-280', 's-300', 's-320', 's-350', 's-400', 's-420', 's-450', 's-500', 's-550', 's-600',
        # SL-Class
        'sl-280', 'sl-300', 'sl-320', 'sl-350', 'sl-400', 'sl-500', 'sl-550', 'sl-600',
        # SLK-Class
        'slk-200', 'slk-230', 'slk-250', 'slk-280', 'slk-300', 'slk-320', 'slk-350',
        # V-Class
        'v-200', 'v-220', 'v-250', 'v-280'
    ],
    
    'audi': [
        # A1
        'a1',
        # A3
        'a3',
        # A4
        'a4',
        # A5
        'a5',
        # A6
        'a6',
        # A7
        'a7',
        # A8
        'a8',
        # Q Series
        'q2', 'q3', 'q5', 'q7', 'q8',
        # TT
        'tt',
        # R8
        'r8',
        # S/RS Series
        's3', 's4', 's5', 's6', 's7', 's8',
        'rs3', 'rs4', 'rs5', 'rs6', 'rs7'
    ],
    
    'volkswagen': [
        # Golf
        'golf', 'golf-plus',
        # Polo
        'polo',
        # Passat
        'passat',
        # Jetta
        'jetta',
        # Tiguan
        'tiguan',
        # Touareg
        'touareg',
        # Touran
        'touran',
        # Sharan
        'sharan',
        # Caddy
        'caddy',
        # T-series
        't4', 't5', 't6',
        # Beetle
        'beetle',
        # Scirocco
        'scirocco',
        # Arteon
        'arteon',
        # ID series
        'id-3', 'id-4'
    ],
    
    'toyota': [
        'auris', 'avensis', 'aygo', 'camry', 'corolla', 'highlander', 'hilux', 
        'land-cruiser', 'prius', 'rav4', 'verso', 'yaris', 'c-hr'
    ],
    
    'opel': [
        'astra', 'corsa', 'insignia', 'meriva', 'mokka', 'vectra', 'zafira', 'adam', 'karl'
    ],
    
    'ford': [
        'fiesta', 'focus', 'mondeo', 'kuga', 'ecosport', 'edge', 'galaxy', 's-max', 'transit', 'mustang'
    ],
    
    'renault': [
        'clio', 'megane', 'scenic', 'laguna', 'captur', 'kadjar', 'koleos', 'talisman', 'twingo'
    ],
    
    'peugeot': [
        '206', '207', '208', '301', '307', '308', '407', '408', '508', '2008', '3008', '5008'
    ]
}

def test_model_url(brand, model):
    """Test if a brand+model URL returns listings."""
    url = f'https://www.mobile.bg/obiavi/avtomobili-dzhipove/{brand}/{model}/namira-se-v-balgariya?sort=6'
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            listings = soup.find_all('a', href=lambda x: x and '/obiava-' in x)
            return len(listings) if listings else 0
        return 0
    except:
        return 0

def generate_model_config():
    """Generate configuration with brand+model combinations."""
    
    print("🔍 Generating comprehensive brand+model configuration...")
    
    # Load existing brand config
    try:
        with open('mobile_bg_brand_config.json', 'r', encoding='utf-8') as f:
            brand_config = json.load(f)
    except:
        print("❌ Could not load brand config. Please run generate_brand_config.py first.")
        return
    
    # Start with brand-only searches (for brands without specific models)
    search_urls = []
    
    # Add all brand-only searches first
    for brand_info in brand_config.get('all_brands', []):
        search_urls.append({
            'type': 'brand',
            'brand': brand_info['brand'],
            'brand_slug': brand_info['slug'],
            'model': None,
            'model_slug': None,
            'url': brand_info['url'],
            'priority': brand_info.get('priority', False),
            'estimated_listings': 3000 if brand_info.get('priority', False) else 1000
        })
    
    # Now add model-specific searches for popular brands
    model_searches = []
    for brand_slug, models in BRAND_MODELS.items():
        print(f"\n🚗 Testing {brand_slug.upper()} models...")
        
        brand_display = brand_slug.replace('-', '-').title()
        working_models = []
        
        for i, model in enumerate(models):
            print(f"   Testing {model}... ({i+1}/{len(models)})", end='')
            
            listings_count = test_model_url(brand_slug, model)
            if listings_count > 0:
                working_models.append({
                    'model': model,
                    'listings_count': listings_count
                })
                print(f" ✅ {listings_count} listings")
                
                # Add to model searches
                model_searches.append({
                    'type': 'model',
                    'brand': brand_display,
                    'brand_slug': brand_slug,
                    'model': model.upper(),
                    'model_slug': model,
                    'url': f'https://www.mobile.bg/obiavi/avtomobili-dzhipove/{brand_slug}/{model}/namira-se-v-balgariya?sort=6',
                    'priority': True,  # Model searches are high priority
                    'estimated_listings': listings_count * 50  # Estimate based on page 1
                })
            else:
                print(f" ❌")
            
            time.sleep(0.2)  # Be nice to the server
        
        print(f"   📊 {brand_slug}: {len(working_models)} working models")
    
    # Combine brand and model searches
    all_searches = search_urls + model_searches
    
    # Create final configuration
    final_config = {
        'generation_date': '2025-10-22',
        'strategy': 'hybrid_brand_model',
        'description': 'Brand-level searches for comprehensive coverage + model-level searches for popular brands to bypass pagination limits',
        'search_urls': all_searches,
        'summary': {
            'total_searches': len(all_searches),
            'brand_only_searches': len(search_urls),
            'model_specific_searches': len(model_searches),
            'priority_searches': len([s for s in all_searches if s.get('priority', False)]),
            'estimated_total_listings': sum(s.get('estimated_listings', 0) for s in all_searches)
        }
    }
    
    # Save configuration
    output_file = 'mobile_bg_hybrid_config.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(final_config, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Hybrid configuration saved to {output_file}")
    print(f"📊 Summary:")
    print(f"   Total search URLs: {final_config['summary']['total_searches']}")
    print(f"   Brand-only searches: {final_config['summary']['brand_only_searches']}")
    print(f"   Model-specific searches: {final_config['summary']['model_specific_searches']}")
    print(f"   Priority searches: {final_config['summary']['priority_searches']}")
    print(f"   Estimated total listings: {final_config['summary']['estimated_total_listings']:,}")
    
    return final_config

if __name__ == "__main__":
    config = generate_model_config()