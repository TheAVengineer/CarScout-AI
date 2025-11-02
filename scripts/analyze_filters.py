#!/usr/bin/env python3
"""
Check Mobile.bg main page for filter structure.
"""

import requests
from bs4 import BeautifulSoup

def analyze_filters():
    # Check the main search page to see model filters
    url = 'https://www.mobile.bg/obiavi/avtomobili-dzhipove'
    response = requests.get(url)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        
        print("🔍 Analyzing Mobile.bg filter structure...")
        
        # Method 1: Look for select elements
        selects = soup.find_all('select')
        for select in selects:
            name = select.get('name', '')
            id_attr = select.get('id', '')
            print(f'Select: name="{name}" id="{id_attr}"')
            
            options = select.find_all('option')
            if len(options) > 1 and len(options) < 200:  # Reasonable number of options
                print(f'  Options ({len(options)}):')
                for opt in options[:15]:
                    value = opt.get('value', '')
                    text = opt.get_text(strip=True)
                    print(f'    {value}: {text}')
                if len(options) > 15:
                    print(f'    ... and {len(options) - 15} more')
            print()
        
        # Method 2: Look for JavaScript that might load models dynamically
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string and ('model' in script.string.lower() or 'brand' in script.string.lower()):
                content = script.string[:500]  # First 500 chars
                print(f"📜 Script with model/brand references:\n{content}...\n")
    else:
        print(f"❌ Failed to fetch main page: {response.status_code}")

if __name__ == "__main__":
    analyze_filters()