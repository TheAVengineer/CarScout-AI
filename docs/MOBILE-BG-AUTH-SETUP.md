# 🔐 Mobile.bg Authentication Setup Guide

**Last Updated**: October 22, 2025  
**Purpose**: Enable authenticated scraping from Mobile.bg to access all listings

---

## 📋 Overview

Mobile.bg now requires user authentication to view car listings. This guide walks you through:
1. Creating a Mobile.bg account (if you don't have one)
2. Configuring credentials in CarScout AI
3. Testing authenticated scraping
4. Troubleshooting common issues

---

## 🚀 Quick Start (3 Steps)

### Step 1: Get Mobile.bg Account

**Option A: Use Existing Account**
- If you already have a Mobile.bg account, skip to Step 2
- You'll need your email and password

**Option B: Create New Account**
1. Go to: https://www.mobile.bg
2. Click "Регистрация" (Register) in top-right
3. Fill in the registration form:
   - Email address
   - Password (choose a strong one)
   - Name (can be anything)
   - Phone number (optional for basic account)
4. Verify your email (check inbox/spam)
5. Login to confirm account works

**Account Requirements**:
- ✅ Free account is sufficient (no payment needed)
- ✅ Email verification required
- ✅ No special permissions needed
- ✅ One account can be shared across all scrapers

---

### Step 2: Configure Credentials

**Method 1: Environment Variables (RECOMMENDED for production)**

1. Open `.env` file in project root:
   ```bash
   notepad .env
   ```

2. Add these lines at the end:
   ```bash
   # Mobile.bg Authentication
   MOBILE_BG_EMAIL=your.email@example.com
   MOBILE_BG_PASSWORD=your_password_here
   ```

3. Save and close

4. Restart Celery worker to load new settings:
   ```powershell
   # Stop Celery (Ctrl+C in terminal)
   # Then restart:
   .\restart_celery.ps1
   ```

**Method 2: Spider Arguments (for testing)**

Pass credentials directly when running spider:
```bash
cd workers/scrape
scrapy crawl mobile_bg \
  -a login_email="your.email@example.com" \
  -a login_password="your_password" \
  -s CLOSESPIDER_ITEMCOUNT=5
```

**Security Notes**:
- ⚠️  Never commit `.env` file to git (already in `.gitignore`)
- ⚠️  Use environment variables in production
- ⚠️  Rotate passwords regularly
- ✅ Spider arguments are useful for testing only

---

### Step 3: Test Authentication

**Test Script** (creates `scripts/test_mobile_auth.py`):

```python
"""
Test Mobile.bg authentication
"""
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_credentials():
    """Check if credentials are configured"""
    from configs.settings import settings
    
    print("🔍 Checking Mobile.bg credentials...")
    print(f"   Email: {settings.MOBILE_BG_EMAIL or '❌ NOT SET'}")
    print(f"   Password: {'✅ SET' if settings.MOBILE_BG_PASSWORD else '❌ NOT SET'}")
    
    if settings.MOBILE_BG_EMAIL and settings.MOBILE_BG_PASSWORD:
        print("\n✅ Credentials configured!")
        print("\n📝 Next steps:")
        print("   1. Run test scrape: cd workers/scrape && scrapy crawl mobile_bg -s CLOSESPIDER_ITEMCOUNT=5")
        print("   2. Check logs for '✅ Login successful!'")
        return True
    else:
        print("\n❌ Credentials missing!")
        print("\n📝 To fix:")
        print("   1. Add MOBILE_BG_EMAIL and MOBILE_BG_PASSWORD to .env")
        print("   2. Restart Celery worker")
        print("   3. Run this script again")
        return False

if __name__ == "__main__":
    test_credentials()
```

**Run test**:
```powershell
$env:PYTHONPATH="C:\CarScout-AI"
C:\CarScout-AI\venv\Scripts\python.exe scripts\test_mobile_auth.py
```

**Expected output**:
```
🔍 Checking Mobile.bg credentials...
   Email: your.email@example.com
   Password: ✅ SET

✅ Credentials configured!

📝 Next steps:
   1. Run test scrape: cd workers/scrape && scrapy crawl mobile_bg -s CLOSESPIDER_ITEMCOUNT=5
   2. Check logs for '✅ Login successful!'
```

---

## 🧪 Testing Authenticated Scraping

### Test 1: 5 Listings (Quick Test)

```powershell
cd workers/scrape
scrapy crawl mobile_bg -s CLOSESPIDER_ITEMCOUNT=5
```

**What to look for**:
```
🔐 Login credentials provided - will authenticate before scraping
Step 1: Fetching login page...
Step 2: Submitting login form...
✅ Login successful! Starting scraping...
Found listing URL: https://www.mobile.bg/...
```

**Success indicators**:
- ✅ "Login successful" message appears
- ✅ Listing URLs are found
- ✅ Raw HTML is saved to database
- ✅ No "access denied" or "login required" errors

**Failure indicators**:
- ❌ "Login failed - check credentials"
- ❌ No listings found after login
- ❌ "грешка" (error) in Bulgarian
- ❌ Redirected to login page repeatedly

### Test 2: Check Database

After scraping 5 listings, verify they were saved:

```powershell
$env:PYTHONPATH="C:\CarScout-AI"
C:\CarScout-AI\venv\Scripts\python.exe scripts\check_progress.py
```

**Expected output**:
```
📊 Overall Statistics:
   Total raw listings: 31 (was 26, +5 new)
   Total normalized: 24
   Unprocessed: 7
   
📦 Recent listings:
   - BMW 320d (raw_html: 25,432 bytes)
   - Audi A4 (raw_html: 28,901 bytes)
   ...
```

---

## 🔧 How Authentication Works

### Technical Flow

```
1. Spider Start
   ↓
2. Check for credentials (MOBILE_BG_EMAIL, MOBILE_BG_PASSWORD)
   ↓
3. If credentials exist:
   a. Request login page: GET https://www.mobile.bg/pcgi/mobile.cgi?act=3
   b. Parse login form (extract hidden fields, CSRF tokens)
   c. Submit credentials: POST with usr=email, pass=password
   d. Verify success (look for "изход" or "logout" in response)
   e. Proceed to scraping with authenticated session
   ↓
4. If no credentials:
   a. Try unauthenticated scraping
   b. May fail if login required
```

### Login Form Fields

Mobile.bg login form (as of Oct 2025):
- **URL**: `https://www.mobile.bg/pcgi/mobile.cgi?act=3`
- **Method**: POST
- **Fields**:
  - `usr`: Email address
  - `pass`: Password
  - Hidden fields (auto-extracted by spider)

### Session Management

- **Cookies**: Scrapy automatically handles cookies via `COOKIES_ENABLED=True`
- **Session duration**: Typically 24 hours
- **Re-authentication**: Spider re-logins on each run (safe for production)
- **Concurrent scrapers**: Each spider instance has its own session

---

## 🐛 Troubleshooting

### Issue 1: "No login credentials" Warning

**Symptom**:
```
⚠️  No login credentials - will try unauthenticated scraping
```

**Solutions**:
1. Check `.env` file has `MOBILE_BG_EMAIL` and `MOBILE_BG_PASSWORD`
2. Restart Celery worker to reload settings
3. Verify no typos in variable names (case-sensitive)
4. Check settings are loaded: `python scripts/test_mobile_auth.py`

### Issue 2: "Login failed - check credentials"

**Symptom**:
```
❌ Login failed - check credentials
Response preview: <html>...грешка...
```

**Solutions**:
1. **Verify credentials**: Login manually at mobile.bg to confirm they work
2. **Check for typos**: Email and password must be exact
3. **Special characters**: If password has special chars, ensure proper escaping in `.env`
4. **Account status**: Verify account is active and email verified
5. **2FA/Captcha**: Mobile.bg may have added 2FA (will need manual intervention)

### Issue 3: No Listings Found After Login

**Symptom**:
```
✅ Login successful! Starting scraping...
No listing links found on https://m.mobile.bg/...
```

**Solutions**:
1. **Mobile.bg structure changed**: Inspect search page HTML manually
2. **Different mobile URL**: Try desktop site instead:
   ```python
   # In spider, change:
   base_url = "https://www.mobile.bg/obiavi/avtomobili-dzhipove"
   ```
3. **Update CSS selectors**: Links may use different classes/IDs now
4. **Run spider with logging**:
   ```bash
   scrapy crawl mobile_bg -s LOG_LEVEL=DEBUG -s CLOSESPIDER_ITEMCOUNT=1
   ```

### Issue 4: CAPTCHA Required

**Symptom**:
```
Response contains: "Моля, потвърдете, че не сте робот" (Please confirm you're not a robot)
```

**Solutions**:
1. **Manual login**: Login at mobile.bg in browser first, then scrape (shares cookies if on same IP)
2. **Wait and retry**: CAPTCHA may be triggered by rapid requests
3. **Increase delays**: Set `DOWNLOAD_DELAY=10` in spider settings
4. **Rotate IPs**: Use proxy service (expensive, last resort)
5. **2Captcha integration**: Automate CAPTCHA solving (requires paid service)

### Issue 5: "Access Denied" on Listing Pages

**Symptom**:
```
Found listing URL: https://www.mobile.bg/...
Request failed: 403 Forbidden
```

**Solutions**:
1. **Session expired**: Increase `DOWNLOAD_DELAY` to avoid session timeout
2. **Rate limiting**: Reduce `CONCURRENT_REQUESTS` to 1
3. **User agent**: Update to latest browser UA in spider headers
4. **Cookies lost**: Check `COOKIES_ENABLED=True` in spider settings

---

## 📊 Production Deployment

### Environment Variables

In production (Kubernetes/Docker), set these environment variables:

```yaml
# Kubernetes Secret
apiVersion: v1
kind: Secret
metadata:
  name: mobile-bg-credentials
type: Opaque
stringData:
  MOBILE_BG_EMAIL: "your.email@example.com"
  MOBILE_BG_PASSWORD: "your_password"
```

Reference in deployment:
```yaml
env:
  - name: MOBILE_BG_EMAIL
    valueFrom:
      secretKeyRef:
        name: mobile-bg-credentials
        key: MOBILE_BG_EMAIL
  - name: MOBILE_BG_PASSWORD
    valueFrom:
      secretKeyRef:
        name: mobile-bg-credentials
        key: MOBILE_BG_PASSWORD
```

### Monitoring

**Check authentication status**:
```python
# In libs/observability/metrics.py
mobile_bg_login_success = Counter('mobile_bg_login_success_total', 'Login successes')
mobile_bg_login_failure = Counter('mobile_bg_login_failure_total', 'Login failures')
```

**Alert on failures**:
```yaml
# Prometheus alert
- alert: MobileBgLoginFailure
  expr: rate(mobile_bg_login_failure_total[5m]) > 0.1
  annotations:
    summary: "Mobile.bg authentication failing"
```

### Security Best Practices

1. ✅ **Rotate credentials** every 90 days
2. ✅ **Use dedicated account** (not personal)
3. ✅ **Monitor for breaches** (haveibeenpwned.com)
4. ✅ **Log authentication** (but not credentials!)
5. ✅ **Encrypt secrets** in production (use secrets manager)
6. ✅ **Limit access** to `.env` file (chmod 600)

---

## 🎯 Next Steps After Setup

Once authentication is working:

### 1. Bulk Scraping (500-1000 listings)

```powershell
cd workers/scrape
scrapy crawl mobile_bg -s CLOSESPIDER_ITEMCOUNT=500
```

**Recommended settings**:
- Start with 100, then 500, then 1000
- Monitor database size
- Check for duplicates

### 2. Process Through Pipeline

```powershell
$env:PYTHONPATH="C:\CarScout-AI"
C:\CarScout-AI\venv\Scripts\python.exe scripts\process_all.py
```

This will:
- Parse all raw HTML
- Normalize data
- Detect duplicates
- Calculate prices
- Score listings
- Send notifications

### 3. Monitor Progress

```powershell
# Real-time monitoring
C:\CarScout-AI\venv\Scripts\python.exe scripts\check_progress.py

# Watch mode (refresh every 10 seconds)
while ($true) { 
    cls; 
    python scripts\check_progress.py; 
    sleep 10 
}
```

### 4. Verify Dataset Quality

**Goals**:
- ✅ 500-1000 listings scraped
- ✅ 20+ brand/model combinations
- ✅ 5+ listings per popular model (for price estimation)
- ✅ <5% duplicate rate
- ✅ >90% parsing success rate

**Check with**:
```sql
-- Brand/model distribution
SELECT brand_id, model_id, COUNT(*) as count
FROM listings_normalized
WHERE is_duplicate = false
GROUP BY brand_id, model_id
HAVING COUNT(*) >= 5
ORDER BY count DESC;
```

---

## 📚 Additional Resources

- **Mobile.bg Homepage**: https://www.mobile.bg
- **Registration Page**: https://www.mobile.bg/pcgi/mobile.cgi?act=3&new=1
- **Scrapy FormRequest Docs**: https://docs.scrapy.org/en/latest/topics/request-response.html#formrequest
- **CarScout Seeding Guide**: `docs/SEEDING-GUIDE.md`
- **Database Monitoring**: `scripts/check_progress.py`

---

## 🆘 Getting Help

If you encounter issues not covered here:

1. **Check logs**: Look for specific error messages
2. **Test manually**: Try logging in at mobile.bg in browser
3. **Search issues**: Check if others had similar problems
4. **Ask for help**: Provide error logs and steps you've tried

**Common log locations**:
- Scrapy logs: `workers/scrape/scrapy.log`
- Celery logs: Terminal where worker is running
- Application logs: `logs/carscout.log`

---

**Document Version**: 1.0  
**Last Updated**: October 22, 2025  
**Tested With**: Mobile.bg (Oct 2025), Scrapy 2.11.0
