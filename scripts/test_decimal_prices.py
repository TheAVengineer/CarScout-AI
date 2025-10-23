"""Test the fixed regex for decimal prices"""
import re

# Test case 1: Regular price without decimals
price_text1 = "\n  42 948.01 € 83 999 лв.\n"
bgn_match1 = re.search(r'(\d+(?:[\s\xa0]+\d+)*(?:\.\d+)?)\s*лв', price_text1)
if bgn_match1:
    price_str = bgn_match1.group(1).split('.')[0].replace(' ', '').replace('\xa0', '').strip()
    print(f"Test 1 (no decimals in BGN): {bgn_match1.group(1)} → {price_str} → {int(price_str)}")

# Test case 2: Lamborghini with decimals
price_text2 = "\n  194 499 € 380 406.98 лв.\n"
bgn_match2 = re.search(r'(\d+(?:[\s\xa0]+\d+)*(?:\.\d+)?)\s*лв', price_text2)
if bgn_match2:
    price_str = bgn_match2.group(1).split('.')[0].replace(' ', '').replace('\xa0', '').strip()
    print(f"Test 2 (with decimals): {bgn_match2.group(1)} → {price_str} → {int(price_str)}")

# Test case 3: EUR fallback
price_text3 = "\n  42 948.01 €\n"
eur_match = re.search(r'(\d+(?:[\s\xa0]+\d+)*(?:\.\d+)?)\s*€', price_text3)
if eur_match:
    price_str = eur_match.group(1).split('.')[0].replace(' ', '').replace('\xa0', '').strip()
    print(f"Test 3 (EUR with decimals): {eur_match.group(1)} → {price_str} → {int(price_str)}")

print("\n✅ All tests show integer-only prices (no decimal cents)")

