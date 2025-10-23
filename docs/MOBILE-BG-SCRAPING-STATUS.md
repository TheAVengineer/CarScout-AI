# 🚧 Mobile.bg Scraping - Status Update

**Date**: October 22, 2025  
**Current Challenge**: Mobile.bg uses JavaScript to load car listings  
**Status**: BLOCKED - Need alternative approach

---

## 🔍 What We Discovered

### Investigation Results

Running `scripts/debug_mobile_bg.py` revealed:

1. ✅ **Search page loads** (276,960 chars) without login
2. ✅ **Login form found** with correct fields (`usr`, `pwd`)
3. ❌ **Car listings loaded via JavaScript** - not in initial HTML
4. ❌ **Only pagination links found** (`/p-2`, `/p-3`) - no actual car URLs

### Technical Details

```
Page Content: 276,960 characters
Forms Found: 2
Login Fields: usr, pwd, act, logact, login_flag
Links Found: 13 total
  - 0 car listing URLs
  - 5 pagination links
  - 8 category links
```

**Root Cause**: Mobile.bg uses modern JavaScript framework (likely React/Vue) to dynamically load car listings after page renders. Scrapy's standard HTML parser can't see JavaScript-rendered content.

---

## 🛠️ Technical Challenges

### Challenge 1: JavaScript Rendering

**Problem**: Car listings are not in the initial HTML response  
**Evidence**: debug script found 0 car links in 276KB of HTML  
**Impact**: Standard Scrapy scraping won't work

**Solutions**:
1. **Playwright Integration** (Complex, 8-12 hours work):
   - Enable Playwright middleware in Scrapy
   - Wait for JavaScript to render listings
   - Extract data after DOM loads
   - Performance: Slower (browsers), higher resource usage

2. **Selenium** (Alternative, similar complexity):
   - Similar to Playwright
   - Slightly older technology
   - More examples available online

3. **API Reverse Engineering** (Advanced, risky):
   - Find Mobile.bg's internal API endpoints
   - Bypass HTML scraping entirely
   - Risk: APIs can change without notice

### Challenge 2: Login Authentication

**Progress**: Partially implemented  
**Status**: Login form fields identified (`usr`, `pwd`)  
**Blocker**: Even with successful login, JavaScript still required for listings

**Current Implementation**:
- ✅ Credentials load from `.env`
- ✅ Login page fetch works
- ✅ Form submission implemented
- ❌ Post-login scraping blocked by JavaScript
- ❌ Session persistence untested

---

## 📊 Current Database State

```
Total Raw Listings: 26 (after cleanup)
With raw_html: 12 listings
With parsed_data: 6 listings
Normalized: 24 listings
Brands: ~5-8
Models: ~10-15
```

**Quality**: Small but usable for testing pipeline functionality

---

## 🎯 Recommended Path Forward

### Option A: Work with Current Data (RECOMMENDED for now)

**Pros**:
- ✅ 26 listings ready to process
- ✅ Tests full pipeline end-to-end
- ✅ Validates scoring/pricing logic
- ✅ No additional scraping complexity

**Cons**:
- ❌ Limited dataset (not enough for price estimation)
- ❌ Only ~5-8 brands
- ❌ Can't test "large dataset" scenarios

**Action Items**:
1. Run `python scripts\process_all.py`
2. Monitor `python scripts\check_progress.py`
3. Verify pipeline works correctly
4. Fix any bugs discovered
5. Move to Option B when ready

**Time**: 30 minutes to verify everything works

---

### Option B: Implement Playwright for Mobile.bg

**Pros**:
- ✅ Full access to Mobile.bg listings
- ✅ Can scrape 500-1000 listings
- ✅ Most comprehensive Bulgarian car data

**Cons**:
- ❌ Complex implementation (8-12 hours)
- ❌ Requires browser automation
- ❌ Slower scraping (browsers are heavy)
- ❌ Higher resource usage (memory, CPU)

**Action Items**:
1. Install Playwright browsers: `playwright install chromium`
2. Enable Playwright middleware in spider settings
3. Update requests to use Playwright:
   ```python
   meta={"playwright": True, "playwright_include_page": True}
   ```
4. Add wait logic for JavaScript:
   ```python
   await page.wait_for_selector('.listing-item')
   ```
5. Extract data from rendered DOM
6. Test login flow with Playwright
7. Implement pagination handling
8. Test with 5, then 50, then 500 listings

**Time**: 8-12 hours of development + testing

---

### Option C: Use Alternative Sources (EASIEST)

**Pros**:
- ✅ Simpler HTML structure (likely)
- ✅ Multiple sources = better coverage
- ✅ Already planned in roadmap (AGENTS.md Task 1.2, 1.3)

**Cons**:
- ❌ Still need to implement spiders
- ❌ Unknown complexity of each site

**Recommended Sources**:

1. **Cars.bg** (Task 1.2 from AGENTS.md):
   - Similar to Mobile.bg
   - Might have same JavaScript issues
   - Estimated: 6 hours

2. **OLX.bg** (Task 1.3 from AGENTS.md):
   - Often simpler structure
   - JSON-LD structured data common
   - Estimated: 6 hours

3. **Facebook Marketplace**:
   - Huge inventory
   - Very complex (JavaScript heavy)
   - Not recommended

**Action Items**:
1. Test Cars.bg with debug script
2. Test OLX.bg with debug script
3. Choose simpler source
4. Implement spider for that source
5. Scrape 100-500 listings
6. Process through pipeline

**Time**: 6-8 hours per source

---

### Option D: Manual Data Export

**Pros**:
- ✅ Fastest path to large dataset (hours not days)
- ✅ No scraping complexity
- ✅ Can get data immediately

**Cons**:
- ❌ Not automated (one-time only)
- ❌ Data goes stale quickly
- ❌ Doesn't help with future scraping

**Action Items**:
1. Use Mobile.bg while logged in
2. Use browser DevTools to export listings
3. Save as JSON or CSV
4. Import to database as `listing_raw`
5. Process through pipeline

**Time**: 2-3 hours for 500 listings

---

## 💡 My Recommendation

**Short-term (Today)**: Option A + Option D
1. Process the 26 existing listings (verify pipeline works)
2. Manually export 100-200 listings from Mobile.bg
3. Process those through pipeline
4. Get enough data to test price estimation (5+ listings per model)

**Medium-term (This Week)**: Option C
1. Test Cars.bg and OLX.bg (run debug script)
2. Implement spider for whichever is simpler
3. Automate scraping for 500+ listings
4. Build sustainable data pipeline

**Long-term (Later)**: Option B
1. Implement Playwright for Mobile.bg (when needed)
2. Full JavaScript support
3. Largest possible dataset
4. Production-ready scraping

---

## 📋 Immediate Next Steps

**What You Can Do Right Now** (30 min):

```powershell
# 1. Process existing 26 listings
python scripts\process_all.py

# 2. Check results
python scripts\check_progress.py

# 3. View what we have
# Should see: 24 normalized, scores calculated, prices estimated
```

**If You Want More Data Today** (2-3 hours):

1. **Manual Export from Mobile.bg**:
   - Open https://www.mobile.bg/obiavi/avtomobili-dzhipove in browser
   - Login with your account
   - Open DevTools (F12)
   - Go to Network tab
   - Refresh page
   - Find API request that loads listings (likely JSON)
   - Copy JSON response
   - Save to file: `manual_export_mobilebg.json`
   - Create import script to load into database

2. **Alternative**: I can create a script that uses Selenium/Playwright to do this semi-automatically

---

## 🆘 What Do You Want To Do?

**Option 1**: Process existing 26 listings, see what we have (30 min)
```powershell
python scripts\process_all.py
python scripts\check_progress.py
```

**Option 2**: I help you manually export 100-200 listings today (2-3 hours)

**Option 3**: I implement Cars.bg or OLX.bg spider (6-8 hours)

**Option 4**: I implement full Playwright for Mobile.bg (8-12 hours)

**Option 5**: Combination - do Option 1 now, decide on others after seeing results

---

## 📝 Files Updated

### Created:
- `scripts/debug_mobile_bg.py` - Page inspector script
- `docs/MOBILE-BG-SCRAPING-STATUS.md` - This file

### Modified:
- `workers/scrape/carscout/spiders/mobile_bg.py` - Partial login implementation

### Status:
- ✅ Credentials configured
- ✅ Login form identified
- ⚠️ JavaScript rendering blocks scraping
- ⏸️ Full implementation paused pending approach decision

---

**Waiting For**: Your decision on which option to pursue

**Recommendation**: Start with Option 1 (process 26 listings), see results, then decide based on what you learn

---

**Document Version**: 1.0  
**Last Updated**: October 22, 2025  
**Status**: Awaiting Direction
