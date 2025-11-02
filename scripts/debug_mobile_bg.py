"""
Debug script to inspect Mobile.bg pages and understand their structure
"""
import requests
from bs4 import BeautifulSoup

print("=" * 70)
print("Mobile.bg Page Inspector")
print("=" * 70)
print()

# Test 1: Check main car listings page
print("1️⃣ Testing search page (without login)...")
url = "https://m.mobile.bg/obiavi/avtomobili-dzhipove"
try:
    response = requests.get(url, headers={
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15'
    })
    print(f"   Status: {response.status_code}")
    print(f"   URL: {response.url}")
    print(f"   Length: {len(response.text)} chars")
    
    # Parse and find listing links
    soup = BeautifulSoup(response.text, 'html.parser')
    links = soup.find_all('a', href=True)
    
    car_links = []
    for link in links[:50]:  # Check first 50 links
        href = link['href']
        # Look for patterns that might be car listings
        if any(pattern in href for pattern in ['/obiavi/', '/pcgi/', 'adv=']):
            if 'users' not in href and 'login' not in href:
                car_links.append(href)
    
    print(f"   Found {len(car_links)} potential listing links")
    if car_links:
        print("   Sample links:")
        for link in car_links[:5]:
            print(f"      - {link}")
    else:
        print("   ❌ No car listing links found!")
        print("   This might mean:")
        print("      - Mobile.bg requires login to view listings")
        print("      - URL pattern changed")
        print("      - JavaScript loads listings dynamically")
    print()
    
except Exception as e:
    print(f"   ❌ Error: {e}")
    print()

# Test 2: Check login page
print("2️⃣ Testing login page...")
login_url = "https://www.mobile.bg/users/login"
try:
    response = requests.get(login_url, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    print(f"   Status: {response.status_code}")
    print(f"   URL: {response.url}")
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find forms
    forms = soup.find_all('form')
    print(f"   Found {len(forms)} forms")
    
    if forms:
        for i, form in enumerate(forms, 1):
            print(f"\n   Form {i}:")
            print(f"      Action: {form.get('action', 'N/A')}")
            print(f"      Method: {form.get('method', 'N/A')}")
            
            # Find input fields
            inputs = form.find_all('input')
            print(f"      Inputs: {len(inputs)}")
            for inp in inputs[:10]:  # Show first 10
                field_type = inp.get('type', 'text')
                field_name = inp.get('name', 'N/A')
                field_value = inp.get('value', '')
                print(f"         - {field_type:15s} | {field_name:20s} | {field_value[:30]}")
    else:
        print("   ❌ No forms found!")
        print("   Login might be JavaScript-based or AJAX")
    print()
    
except Exception as e:
    print(f"   ❌ Error: {e}")
    print()

# Test 3: Try desktop version
print("3️⃣ Testing desktop search page...")
desktop_url = "https://www.mobile.bg/obiavi/avtomobili-dzhipove"
try:
    response = requests.get(desktop_url, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    print(f"   Status: {response.status_code}")
    print(f"   Length: {len(response.text)} chars")
    
    soup = BeautifulSoup(response.text, 'html.parser')
    links = soup.find_all('a', href=True)
    
    car_links = []
    for link in links[:100]:
        href = link['href']
        if any(pattern in href for pattern in ['/obiavi/', '/pcgi/', 'adv=']):
            if 'users' not in href and 'login' not in href:
                car_links.append(href)
    
    print(f"   Found {len(car_links)} potential listing links")
    if car_links:
        print("   Sample links:")
        for link in car_links[:5]:
            print(f"      - {link}")
    print()
    
except Exception as e:
    print(f"   ❌ Error: {e}")
    print()

print("=" * 70)
print("Summary & Recommendations")
print("=" * 70)
print()
print("Based on the results above:")
print("1. If no links found → Mobile.bg requires login OR uses JavaScript")
print("2. If links found → Update spider URL patterns to match")
print("3. If login is JS-based → Consider using Playwright/Selenium")
print("4. Alternative → Use Mobile.bg API if available")
print()
