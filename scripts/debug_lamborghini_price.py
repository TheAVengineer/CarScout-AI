"""Debug why Lamborghini price shows 98 instead of 380406"""
import re

# Actual text from the listing
price_texts = ['\n  194 499 €', '380 406.98 лв.\n  \n    ', '\n    ', '\n  \n']
price_text = ' '.join(price_texts)

print(f"Price text: {repr(price_text)}")
print(f"Length: {len(price_text)}")
print()

# Test current regex
bgn_match = re.search(r'(\d+(?:\s+\d+)*)\s*лв', price_text)
if bgn_match:
    print(f"Match found!")
    print(f"Full match: {repr(bgn_match.group(0))}")
    print(f"Captured group 1: {repr(bgn_match.group(1))}")
    print(f"Match span: {bgn_match.span()}")
    print()
    
    # Show what's around the match
    start, end = bgn_match.span()
    print(f"Context before: {repr(price_text[max(0, start-10):start])}")
    print(f"Match: {repr(price_text[start:end])}")
    print(f"Context after: {repr(price_text[end:min(len(price_text), end+10)])}")
else:
    print("No match found!")

print("\n" + "="*50 + "\n")

# Test with different regex - match numbers before decimal
bgn_match2 = re.search(r'(\d+(?:[\s\xa0]+\d+)*)\s*лв', price_text)
if bgn_match2:
    print(f"Alternative regex match:")
    print(f"Full match: {repr(bgn_match2.group(0))}")
    print(f"Captured: {repr(bgn_match2.group(1))}")
else:
    print("Alternative: No match")

print("\n" + "="*50 + "\n")

# Try to find all numbers before 'лв'
print("Looking for pattern: [number].лв")
all_matches = re.finditer(r'(\d+(?:[\s\xa0.]+\d+)*)\s*лв', price_text)
for i, match in enumerate(all_matches, 1):
    print(f"Match {i}: {repr(match.group(1))}")
