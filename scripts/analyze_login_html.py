"""Analyze the login result HTML to find error messages."""
from pathlib import Path
import re

html_path = Path("C:/CarScout-AI/workers/scrape/login_result.html")

if not html_path.exists():
    print(f"File not found: {html_path}")
    exit(1)

with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

print(f"HTML file size: {len(content)} bytes")
print()

# Look for error messages
print("="*60)
print("Searching for error indicators:")
print("="*60)

# Search for "грешка"
if 'грешка' in content.lower():
    print("\n✓ Found 'грешка' (error) in page")
    # Find context around it
    matches = re.finditer(r'.{0,100}грешка.{0,100}', content, re.IGNORECASE)
    for i, match in enumerate(matches, 1):
        print(f"\nMatch {i}:")
        print(match.group(0))
        if i >= 3:
            break
else:
    print("\n✗ No 'грешка' found")

# Search for form validation errors
print("\n" + "="*60)
print("Form fields:")
print("="*60)

# Find all input fields
inputs = re.findall(r'<input[^>]*name="([^"]*)"[^>]*>', content)
print(f"\nInput fields found: {inputs}")

# Check if there's a "wrong credentials" type message
error_patterns = [
    r'невал[ие]дн',  # invalid
    r'неправилн',    # incorrect
    r'error',
    r'wrong',
]

print("\n" + "="*60)
print("Checking for specific error types:")
print("="*60)

for pattern in error_patterns:
    if re.search(pattern, content, re.IGNORECASE):
        print(f"\n✓ Found pattern '{pattern}'")
        matches = re.finditer(rf'.{{0,80}}{pattern}.{{0,80}}', content, re.IGNORECASE)
        for match in matches:
            print(f"  Context: {match.group(0)}")
            break

print("\n" + "="*60)
