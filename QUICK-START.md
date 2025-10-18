# 🚀 Quick Setup Guide

## ✅ Step 1: Configure Environment Variables

I've created a `.env` file for you with default values. You need to configure a few keys:

### Required for Full Functionality

#### 1. **OpenAI API Key** (Required for AI Risk Classification)
```bash
# Get your key from: https://platform.openai.com/api-keys
OPENAI_API_KEY=sk-proj-xxxxx...
```

**To update:**
```bash
# Open .env file
nano .env

# Or use sed
sed -i '' 's/YOUR_OPENAI_KEY_HERE/sk-proj-your-actual-key/' .env
```

#### 2. **Telegram Bot Token** (Required for Notifications)
```bash
# Create a bot: https://t.me/botfather
# Send /newbot and follow instructions
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
```

**To update:**
```bash
sed -i '' 's/YOUR_BOT_TOKEN_HERE/your-actual-token/' .env
```

#### 3. **Telegram Channel ID** (Required for Public Channel)
```bash
# Create a public channel
# Add your bot as admin
# Get channel ID (starts with -100)
TELEGRAM_CHANNEL_ID=-1001234567890
```

---

## ⚡ Quick Start (Testing Without External APIs)

You can run tests **without** configuring OpenAI/Telegram:

### Option 1: Minimal Testing (No External Dependencies)
```bash
# 1. Start services
docker-compose up -d db redis

# 2. Wait for services to be ready
sleep 10

# 3. Run setup test (doesn't need OpenAI/Telegram)
python scripts/test_setup.py
```

### Option 2: Full Pipeline (Skips AI Task if No API Key)
```bash
# 1. Start all services
docker-compose up -d

# 2. Run pipeline test
# (AI risk task will use rule-based fallback if no OpenAI key)
python scripts/test_pipeline.py
```

---

## 🔧 Step 2: Start Services

```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# Expected output:
# NAME                          STATUS
# carscout-ai-db-1              Up
# carscout-ai-redis-1           Up
# carscout-ai-worker-1          Up
# carscout-ai-beat-1            Up
# carscout-ai-api-1             Up
```

---

## 🧪 Step 3: Run Tests

### Quick Test (5 seconds)
```bash
python scripts/test_setup.py
```

**Expected:**
```
✅ Database Connection
✅ Sources (3 found)
✅ Plans (Free, Premium, Pro)
✅ Brand/Model Mappings (17+ mappings)
🎉 All tests passed!
```

### Full Pipeline Test (30 seconds)
```bash
python scripts/test_pipeline.py
```

**Expected:**
```
✅ Parse complete
✅ Normalize complete
✅ Dedupe complete
⚠️  Price complete (may fail - needs data)
✅ AI Risk complete (or uses fallback)
✅ Score complete
🎉 Pipeline test PASSED!
```

### Alert Matcher Test (10 seconds)
```bash
python scripts/test_alert_matcher.py
```

**Expected:**
```
✅ DSL Parser (8 queries parsed)
✅ Alert Matching (1 match found)
🎉 All tests PASSED!
```

---

## 🐛 Troubleshooting

### Issue: Services won't start
```bash
# Check if ports are already in use
lsof -i :5432  # PostgreSQL
lsof -i :6379  # Redis
lsof -i :8000  # API

# Kill conflicting processes or change ports in docker-compose.yml
```

### Issue: "env file not found"
```bash
# Verify .env file exists
ls -la .env

# If missing, copy from example
cp .env.example .env
```

### Issue: Database connection failed
```bash
# Check if database is running
docker-compose ps db

# View database logs
docker-compose logs db

# Restart database
docker-compose restart db
```

### Issue: Import errors (bs4, numpy, etc.)
```bash
# Install Python dependencies
pip install -e ".[dev]"

# Or use the dev setup script
./scripts/dev_setup.sh
```

---

## 📋 Configuration Checklist

### Minimal (For Local Testing)
- [x] `.env` file created
- [x] Database credentials (default: carscout_user/carscout_password)
- [x] Redis URL (default: redis://redis:6379)
- [ ] OpenAI API Key (optional - will use fallback)
- [ ] Telegram tokens (optional - skip notifications)

### Full (For Production)
- [ ] OpenAI API Key (required for AI risk)
- [ ] Telegram Bot Token (required for bot)
- [ ] Telegram Channel ID (required for public channel)
- [ ] Stripe API Key (required for payments)
- [ ] S3/R2 credentials (required for image storage)
- [ ] Sentry DSN (optional - for error tracking)

---

## 🎯 Next Steps

### 1. **Without External APIs** (Recommended First)
```bash
# Start minimal services
docker-compose up -d db redis

# Run basic tests
python scripts/test_setup.py
python scripts/test_pipeline.py
```

### 2. **With OpenAI API** (For AI Features)
```bash
# Add OpenAI key to .env
nano .env  # Edit OPENAI_API_KEY

# Restart services
docker-compose restart

# Run full tests
./scripts/run_tests.sh
```

### 3. **With Telegram** (For Notifications)
```bash
# Add Telegram tokens to .env
nano .env  # Edit TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID

# Restart services
docker-compose restart

# Test scraping with notifications
docker-compose exec worker scrapy crawl mobile_bg -a pages=1
```

---

## 💡 Pro Tips

1. **Start Simple**: Test without external APIs first
2. **Use Fallbacks**: AI risk classification has rule-based fallback
3. **Check Logs**: `docker-compose logs -f` to see what's happening
4. **Use Flower**: Monitor tasks at http://localhost:5555
5. **Test Incrementally**: Add one API at a time

---

## 📞 Getting Help

If you're stuck:

1. **Check logs**: `docker-compose logs -f worker`
2. **Verify services**: `docker-compose ps`
3. **Test connectivity**: `docker-compose exec worker ping db`
4. **Reset everything**:
   ```bash
   docker-compose down -v
   docker-compose up -d
   python scripts/seed_database.py
   ```

---

## ✅ You're Ready When...

```bash
# This command completes successfully:
python scripts/test_setup.py

# Output shows:
✅ Database Connection
✅ Sources (3 found)
✅ Plans (Free, Premium, Pro)
🎉 All tests passed!
```

**Then you can proceed with full testing! 🚀**
