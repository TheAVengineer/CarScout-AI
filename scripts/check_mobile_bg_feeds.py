"""
Check if Mobile.bg has RSS feeds or sitemaps we can use
"""
import requests

urls_to_check = [
    "https://www.mobile.bg/rss",
    "https://www.mobile.bg/feed",
    "https://www.mobile.bg/sitemap.xml",
    "https://www.mobile.bg/robots.txt",
    "https://m.mobile.bg/",  # Mobile version
]

print("🔍 Checking Mobile.bg for alternative data sources...\n")

for url in urls_to_check:
    try:
        response = requests.get(url, timeout=10, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        print(f"✅ {url}")
        print(f"   Status: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('Content-Type', 'unknown')}")
        print(f"   Length: {len(response.text)} bytes")
        
        # Show first 200 chars
        preview = response.text[:200].replace('\n', ' ')
        print(f"   Preview: {preview}...")
        print()
        
    except Exception as e:
        print(f"❌ {url}")
        print(f"   Error: {e}")
        print()

print("\n💡 Recommendation:")
print("   1. If mobile site works → Use it!")
print("   2. If robots.txt shows allowed paths → Use those")
print("   3. If sitemap exists → Crawl from sitemap")
print("   4. Otherwise → Need proxy rotation or residential IPs")
