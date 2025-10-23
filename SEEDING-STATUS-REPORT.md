# 🚨 Database Seeding Status Report

**Date**: October 22, 2025  
**Status**: ⚠️ BLOCKED - Need New Scraping Strategy

---

## 📊 Current State

### Raw Listings: 1,127 total

| Category | Count | Usable? | Notes |
|----------|-------|---------|-------|
| With `parsed_data` | 6 | ✅ Yes | Spider-extracted data, already processed |
| With `raw_html` | ~5 | ✅ Yes | Recent listings with HTML in database |
| With `raw_html_path` only | 1,121 | ❌ No | Files don't exist on disk |

### Processed Listings: 24 total

| Metric | Value |
|--------|-------|
| Non-duplicates | 14 |
| Unique brands | 5 (BMW, Toyota, Audi, Unknown) |
| Ready for pricing | 1 model (BMW X5 with 5 listings) |

---

## ⚠️ Problem Discovered

1. **Old listings are unusable** (1,121 of 1,127)
   - Have `raw_html_path` set but `raw_html` is NULL
   - HTML files were never saved to disk (or were deleted)
   - Can't process without HTML content

2. **Mobile.bg blocks scraping**
   - Now requires login/authentication
   - Redirects to `/users/login`
   - Fresh scraping not possible without bypass

3. **Not enough data for comparisons**
   - Need 5+ listings per brand/model for price estimation
   - Currently only BMW X5 has 5 listings
   - Most listings score 1.0/10 due to "Limited comparables"

---

## 🎯 Options Forward

### Option 1: Clean Database & Scrape with Login (RECOMMENDED)

**Steps**:
1. Delete the 1,121 unusable listings
2. Configure Mobile.bg authentication in Scrapy
3. Scrape 500-1,000 fresh listings with `raw_html` saved
4. Process all through pipeline
5. Build comparative dataset

**Pros**:
- Fresh, clean data
- All listings processable
- Can build large dataset (1000+)
- Price estimation will work properly

**Cons**:
- Requires Mobile.bg account
- May need cookies/session management
- Could take 1-2 hours to scrape

**Effort**: 4-6 hours

---

### Option 2: Use Alternative Sources

**Sources to try**:
- **Cars.bg** (implement spider)
- **OLX.bg** (implement spider)
- **AutoScout24** (may have API)

**Pros**:
- Avoid Mobile.bg login issues
- Diversify data sources
- May have better scraping policies

**Cons**:
- Need to write new spiders
- Unknown if they block scraping
- Different HTML structures to parse

**Effort**: 6-10 hours per source

---

### Option 3: Work with Limited Data (TEMPORARY)

**Current usable data**:
- 14 non-duplicate listings
- 5 BMW X5 for comparisons
- 1 Audi A4, 1 Toyota, 3 BMW (other models)

**What works**:
- Pipeline stages (parse → normalize → dedupe → price → score)
- BMW X5 gets price estimates and real scores
- All other listings score low (expected with limited data)

**Pros**:
- Can test all features
- Validates pipeline logic
- No scraping needed now

**Cons**:
- Not representative of production
- Can't test diverse brands/models
- Limited demo value

**Effort**: 0 hours (use current state)

---

### Option 4: Delete Unusable Data & Re-scrape Later

**Steps**:
1. Clean database (remove 1,121 unusable listings)
2. Keep 24 processed + 6 with parsed_data
3. Document scraping requirements
4. Implement Mobile.bg login later
5. Do bulk scraping when ready

**Pros**:
- Clean database
- Clear what needs to be done
- Can move forward with other tasks
- Come back to scraping when ready

**Cons**:
- Still limited data for now
- Postpones the problem

**Effort**: 1 hour cleanup, 6 hours for future scraping

---

## 🔧 Implementation Guide

### If choosing Option 1 (Scrape with Login):

**1. Get Mobile.bg credentials**:
```python
# Add to workers/scrape/carscout/settings.py
MOBILE_BG_USERNAME = "your_email@example.com"
MOBILE_BG_PASSWORD = "your_password"
```

**2. Update spider to login**:
```python
# workers/scrape/carscout/spiders/mobile_bg.py
def start_requests(self):
    # Login first
    yield scrapy.Request(
        'https://www.mobile.bg/users/login',
        callback=self.login,
    )

def login(self, response):
    return scrapy.FormRequest.from_response(
        response,
        formdata={
            'email': settings.MOBILE_BG_USERNAME,
            'password': settings.MOBILE_BG_PASSWORD,
        },
        callback=self.after_login
    )

def after_login(self, response):
    # Check login succeeded
    if "logout" in response.text.lower():
        # Start scraping
        yield from self.start_scraping()
    else:
        self.logger.error("Login failed!")
```

**3. Clean database**:
```sql
-- Delete unusable listings
DELETE FROM listings_raw 
WHERE raw_html IS NULL 
AND raw_html_path IS NOT NULL 
AND parsed_data IS NULL;
```

**4. Scrape fresh**:
```bash
cd workers/scrape
scrapy crawl mobile_bg -s CLOSESPIDER_ITEMCOUNT=1000
```

**5. Process all**:
```bash
python scripts/process_all.py
```

---

### If choosing Option 4 (Clean & Postpone):

**Run cleanup script**:
```python
# scripts/cleanup_unusable.py (create this)
from libs.domain.database import get_sync_session
from libs.domain.models import ListingRaw

session = get_sync_session()

# Find unusable listings
unusable = session.query(ListingRaw).filter(
    ListingRaw.raw_html == None,
    ListingRaw.raw_html_path != None,
    ListingRaw.parsed_data == None
).all()

print(f"Found {len(unusable)} unusable listings")
print("Deleting...")

for listing in unusable:
    session.delete(listing)

session.commit()
print(f"✅ Deleted {len(unusable)} unusable listings")
```

---

## 💡 Recommendation

**Go with Option 1** if you want to test with real data soon.

**Go with Option 4** if you want to focus on other features first (alerts, payments, testing) and come back to scraping later.

The pipeline is fully functional - we just need more data to see it shine! 🚀

---

## 📝 Files Created

1. `parse.py` - ✅ Updated to load HTML from files (but files don't exist)
2. `check_progress.py` - ✅ Monitor database seeding progress
3. `process_all.py` - ✅ Queue unprocessed listings (but they're unusable)
4. `SEEDING-GUIDE.md` - ✅ Comprehensive scraping documentation
5. `restart_celery.ps1` - ✅ Restart worker script
6. **This file** - `SEEDING-STATUS-REPORT.md` - Current situation analysis

---

**Next Decision**: Choose which option to pursue and update the plan accordingly.
