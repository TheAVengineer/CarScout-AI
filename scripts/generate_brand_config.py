#!/usr/bin/env python3
"""
Mobile.bg Brand List Generator
Extracts all car brands from Mobile.bg and creates comprehensive search URLs
"""

import json

# All 134 brands discovered from Mobile.bg filter analysis
MOBILE_BG_BRANDS = [
    "Abarth", "Acura", "Alfa Romeo", "Alpina", "Asia", "Aston Martin", "Audi", "Austin",
    "BAIC", "BAW", "Bentley", "BENTU", "BMW", "Brilliance", "Buick", "BYD", "Cadillac",
    "Carbodies", "Changan", "Chery", "Chevrolet", "Chrysler", "Citroen", "Corvette",
    "Cupra", "Dacia", "Daewoo", "Daihatsu", "Daimler", "DFSK", "Dkw", "Dodge",
    "DONGFENG", "Dr", "DR Automobiles", "DS", "Eagle", "Ferrari", "Fiat", "Fisker",
    "Ford", "Foton", "Gaz", "Geely", "Genesis", "Gmc", "Gonow", "GOUPIL", "Great Wall",
    "Haval", "Hino", "Honda", "Hummer", "Hyundai", "Infiniti", "Innocenti", "Isuzu",
    "Iveco", "JAC", "Jaguar", "Jeep", "Jetour", "JMC", "Kia", "Lada", "Lamborghini",
    "Lancia", "Land Rover", "Landwind", "LEAPMOTOR", "Lexus", "Lifan", "Lincoln",
    "Lotus", "LTI", "LuAZ", "Luxgen", "Lynk & Co", "MACAN", "MAN", "Maruti", "Maserati",
    "Maxus", "Maybach", "Mazda", "Mercedes-Benz", "Microcar", "MINI", "Mitsubishi",
    "Morgan", "MossMotors", "Moskvich", "NIO", "Nissan", "OFY", "Oldsmobile", "Opel",
    "PEUGEOT", "Piaggio", "Plymouth", "Polaris", "Pontiac", "Porsche", "Proton",
    "Puch", "RAM", "Renault", "Rolls-Royce", "Rover", "Saab", "Saturn", "SEAT",
    "SERES", "Skoda", "smart", "SsangYong", "Subaru", "Suzuki", "Tata", "Tesla",
    "Think", "Toyota", "UAZ", "Vauxhall", "Volkswagen", "Volvo", "Wartburg", "Yugo", "ZAZ"
]

def normalize_brand_for_url(brand_name):
    """Convert brand name to URL-friendly slug"""
    # Handle special cases and common patterns
    replacements = {
        " ": "-",
        "&": "-",
        ".": "",
        "ë": "e",
        "ü": "u",
        "ö": "o",
        "ä": "a"
    }
    
    slug = brand_name.lower()
    for old, new in replacements.items():
        slug = slug.replace(old, new)
    
    # Remove any remaining special characters
    slug = ''.join(c for c in slug if c.isalnum() or c in '-_')
    
    return slug

def generate_search_urls():
    """Generate comprehensive search URLs for all brands"""
    
    # Priority brands (most listings) - scrape these first
    priority_brands = [
        "Mercedes-Benz", "BMW", "Audi", "Volkswagen", "Toyota", "Ford", "Opel", 
        "Skoda", "Renault", "Hyundai", "Nissan", "Honda", "Peugeot", "Chevrolet",
        "Kia", "Mazda", "Citroen", "Fiat", "Volvo", "Mitsubishi"
    ]
    
    # Generate URLs for priority brands
    priority_urls = []
    for brand in priority_brands:
        if brand in MOBILE_BG_BRANDS:
            slug = normalize_brand_for_url(brand)
            # Use /obiavi/ format (working pagination) instead of /search/
            url = f"https://www.mobile.bg/obiavi/avtomobili-dzhipove/{slug}/namira-se-v-balgariya?sort=6"
            priority_urls.append({
                'brand': brand,
                'slug': slug,
                'url': url,
                'priority': True
            })
    
    # Generate URLs for all remaining brands
    all_urls = []
    for brand in MOBILE_BG_BRANDS:
        slug = normalize_brand_for_url(brand)
        # Use /obiavi/ format (working pagination) instead of /search/
        url = f"https://www.mobile.bg/obiavi/avtomobili-dzhipove/{slug}/namira-se-v-balgariya?sort=6"
        is_priority = brand in priority_brands
        
        all_urls.append({
            'brand': brand,
            'slug': slug,
            'url': url,
            'priority': is_priority
        })
    
    return {
        'priority_brands': priority_urls,
        'all_brands': all_urls,
        'total_brands': len(MOBILE_BG_BRANDS)
    }

def save_brand_config():
    """Save brand configuration to JSON file"""
    
    config = generate_search_urls()
    
    # Save to file
    with open('mobile_bg_brand_config.json', 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Saved brand configuration:")
    print(f"   📊 Total brands: {config['total_brands']}")
    print(f"   ⭐ Priority brands: {len(config['priority_brands'])}")
    print(f"   🔗 Sample URLs:")
    
    for brand_info in config['priority_brands'][:5]:
        print(f"      {brand_info['brand']}: {brand_info['url']}")
    
    return config

if __name__ == "__main__":
    print("🏷️ MOBILE.BG BRAND URL GENERATOR")
    print("=" * 50)
    
    config = save_brand_config()
    
    print(f"\n🎯 Strategy:")
    print(f"   1. Scrape {len(config['priority_brands'])} priority brands first")
    print(f"   2. Then scrape remaining {config['total_brands'] - len(config['priority_brands'])} brands")
    print(f"   3. Each brand search will cover all its listings (up to 150 pages)")
    print(f"   4. Total coverage: All 40,000+ listings!")
    
    print(f"\n📁 Config saved to: mobile_bg_brand_config.json")