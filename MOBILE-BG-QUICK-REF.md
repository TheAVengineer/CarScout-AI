# 🚀 Quick Reference - Mobile.bg Authentication Setup

**Last Updated**: October 22, 2025

---

## ⚡ Quick Commands

### Check Configuration Status
```powershell
python scripts\test_mobile_auth.py
```

### Test Scraping (5 listings)
```powershell
cd workers/scrape
scrapy crawl mobile_bg -s CLOSESPIDER_ITEMCOUNT=5
```

### Check Database Progress
```powershell
python scripts\check_progress.py
```

### Bulk Scrape (500 listings)
```powershell
cd workers/scrape
scrapy crawl mobile_bg -s CLOSESPIDER_ITEMCOUNT=500
```

### Process All Through Pipeline
```powershell
python scripts\process_all.py
```

---

## 📝 Setup Checklist

- [ ] **Get Mobile.bg account**
  - Go to: https://www.mobile.bg
  - Click "Регистрация" (Register)
  - Verify email

- [ ] **Configure credentials**
  - Open `.env` file: `notepad .env`
  - Add:
    ```
    MOBILE_BG_EMAIL=your.email@example.com
    MOBILE_BG_PASSWORD=your_password_here
    ```
  - Save file

- [ ] **Restart Celery**
  - Run: `.\restart_celery.ps1`

- [ ] **Test configuration**
  - Run: `python scripts\test_mobile_auth.py`
  - Should show: ✅ Credentials are configured!

- [ ] **Test scraping**
  - Run: `cd workers/scrape` then `scrapy crawl mobile_bg -s CLOSESPIDER_ITEMCOUNT=5`
  - Look for: ✅ Login successful!

- [ ] **Bulk scrape**
  - Run: `scrapy crawl mobile_bg -s CLOSESPIDER_ITEMCOUNT=500`
  - Monitor: `python scripts\check_progress.py`

- [ ] **Process pipeline**
  - Run: `python scripts\process_all.py`
  - Wait for processing to complete

- [ ] **Verify quality**
  - Run: `python scripts\check_progress.py`
  - Check for: 20+ brands, 5+ listings per model

---

## ✅ Success Indicators

### When Testing (5 listings)
```
🔐 Login credentials provided - will authenticate before scraping
Step 1: Fetching login page...
Step 2: Submitting login form...
✅ Login successful! Starting scraping...
Found listing URL: https://www.mobile.bg/...
Scraped 5 listings
```

### When Checking Database
```
📊 Overall Statistics:
   Total raw listings: 31 (was 26, +5 new)
   With raw_html: 17 (was 12, +5 new)
   Processing rate: 85%+
```

### After Bulk Scraping (500)
```
📊 Overall Statistics:
   Total raw listings: 526
   Total normalized: 450+
   Brands: 20-30
   Models: 50-100
```

---

## 🚨 Common Issues

### "No login credentials" Warning
- **Fix**: Add credentials to `.env`, restart Celery
- **Test**: `python scripts\test_mobile_auth.py`

### "Login failed - check credentials"
- **Fix**: Try logging in at mobile.bg manually
- **Check**: Email verified, no typos in `.env`

### No listings found after login
- **Fix**: See `docs/MOBILE-BG-AUTH-SETUP.md` (Issue 3)
- **Debug**: Run with `scrapy crawl mobile_bg -s LOG_LEVEL=DEBUG`

---

## 📚 Documentation

- **Full Setup Guide**: `docs/MOBILE-BG-AUTH-SETUP.md`
- **Implementation Summary**: `docs/MOBILE-BG-AUTH-IMPLEMENTATION.md`
- **Seeding Guide**: `docs/SEEDING-GUIDE.md`

---

## 🎯 Your Next Steps

**Right Now** (15 minutes):
1. Create Mobile.bg account → https://www.mobile.bg
2. Add credentials to `.env`
3. Restart Celery: `.\restart_celery.ps1`
4. Test: `python scripts\test_mobile_auth.py`
5. Scrape 5 listings: `cd workers/scrape; scrapy crawl mobile_bg -s CLOSESPIDER_ITEMCOUNT=5`

**Then** (1-2 hours):
1. Bulk scrape 500: `scrapy crawl mobile_bg -s CLOSESPIDER_ITEMCOUNT=500`
2. Process: `python scripts\process_all.py`
3. Verify: `python scripts\check_progress.py`

**Goal**: 500+ listings, 20+ brands, ready for price comparisons! 🚀

---

**Status**: ✅ Implementation Complete - Waiting for Your Credentials
