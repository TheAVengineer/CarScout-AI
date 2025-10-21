# 🚀 Environment Setup Guide

This guide helps you configure the `.env` file for CarScout AI.

## 📋 Quick Start Checklist

### ✅ Required (Must Configure Before Launch)

1. **[ ] Telegram Bot Token** - Get from @BotFather
2. **[ ] Telegram Channels** - Create 3 channels (Public, Premium, VIP)
3. **[ ] OpenAI API Key** - For AI risk analysis
4. **[ ] Stripe Keys** - For payment processing
5. **[ ] Security Salts** - Generate random strings

### 🟡 Recommended (Can Configure Later)

6. **[ ] S3/R2 Storage** - For HTML/image storage
7. **[ ] Sentry DSN** - For error tracking
8. **[ ] Domain/SSL** - For production deployment

---

## 🔧 Step-by-Step Configuration

### 1️⃣ Create Telegram Bot (5 minutes)

**Steps:**
```bash
1. Open Telegram and search for @BotFather
2. Send: /newbot
3. Choose a name: "CarScout Deals Bot"
4. Choose a username: "CarScoutDealsBot" (must end with 'bot')
5. Copy the token (looks like: 1234567890:ABCdefGHIjklMNO...)
6. Paste in .env as TELEGRAM_BOT_TOKEN
```

**Commands to configure your bot:**
```bash
# Send these to @BotFather:
/setdescription - "Find the best car deals in Bulgaria"
/setabouttext - "AI-powered car listing aggregator"
/setcommands - Set these commands:
  start - Start the bot
  subscribe - View subscription plans
  help - Get help
```

---

### 2️⃣ Create Telegram Channels (10 minutes)

#### A. Public Channel (FREE users)
```bash
1. Open Telegram → New Channel
2. Name: "CarScout Deals" 
3. Username: @CarScoutDeals (must be unique)
4. Make it PUBLIC
5. Add your bot as ADMIN (give "Post Messages" permission)
6. Copy username to .env: TELEGRAM_PUBLIC_CHANNEL=@CarScoutDeals
```

#### B. Premium Channel (€14.99/mo)
```bash
1. Create new channel: "CarScout Premium"
2. Make it PRIVATE (no username)
3. Add your bot as ADMIN
4. Get channel ID:
   - Add @RawDataBot to the channel
   - It will show the chat ID (e.g., -1001234567890)
   - Copy to .env: TELEGRAM_PREMIUM_CHANNEL=-1001234567890
5. Remove @RawDataBot
```

#### C. VIP Channel (€29.99/mo)
```bash
1. Create new channel: "CarScout VIP"
2. Make it PRIVATE (no username)
3. Add your bot as ADMIN
4. Get channel ID using @RawDataBot (same as above)
5. Copy to .env: TELEGRAM_VIP_CHANNEL=-1009876543210
```

---

### 3️⃣ Get OpenAI API Key (5 minutes)

```bash
1. Go to: https://platform.openai.com/api-keys
2. Sign up or log in
3. Click "Create new secret key"
4. Name it: "CarScout AI"
5. Copy the key (starts with: sk-proj-...)
6. Paste in .env: OPENAI_API_KEY=sk-proj-...

💡 Cost: ~€20-50/month for 1,000-2,000 listings analyzed
```

---

### 4️⃣ Setup Stripe (15 minutes)

#### A. Create Stripe Account
```bash
1. Go to: https://dashboard.stripe.com/register
2. Sign up with your email
3. Complete business verification
```

#### B. Get API Keys
```bash
1. Go to: https://dashboard.stripe.com/apikeys
2. Copy "Secret key" (starts with: sk_test_...)
3. Paste in .env: STRIPE_API_KEY=sk_test_...
```

#### C. Create Subscription Products
```bash
1. Go to: https://dashboard.stripe.com/products
2. Click "Add product"

Premium Plan:
- Name: "CarScout Premium"
- Description: "Access to premium car deals"
- Pricing: €14.99/month (recurring)
- Click "Save product"
- Copy Price ID (starts with: price_...)
- Paste in .env: STRIPE_PRICE_PREMIUM=price_...

VIP Plan:
- Name: "CarScout VIP"
- Description: "VIP early access to all deals"
- Pricing: €29.99/month (recurring)
- Copy Price ID: STRIPE_PRICE_VIP=price_...
```

#### D. Setup Webhooks
```bash
1. Go to: https://dashboard.stripe.com/webhooks
2. Click "Add endpoint"
3. Endpoint URL: https://your-domain.com/api/stripe/webhook
   (For local testing: use ngrok - see below)
4. Select events:
   - checkout.session.completed
   - customer.subscription.created
   - customer.subscription.updated
   - customer.subscription.deleted
   - invoice.payment_succeeded
   - invoice.payment_failed
5. Copy "Signing secret" (starts with: whsec_...)
6. Paste in .env: STRIPE_WEBHOOK_SECRET=whsec_...
```

---

### 5️⃣ Generate Security Salts (2 minutes)

#### Windows PowerShell:
```powershell
# Generate API secret key (32 chars)
-join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | ForEach-Object {[char]$_})

# Generate password hash salt (16 chars)
-join ((48..57) + (65..90) + (97..122) | Get-Random -Count 16 | ForEach-Object {[char]$_})
```

#### Or use online tool:
```bash
Go to: https://randomkeygen.com/
Copy "Fort Knox Passwords" → API_SECRET_KEY
Copy "CodeIgniter Encryption Keys" → PASSWORD_HASH_SALT
```

**Paste in .env:**
```env
API_SECRET_KEY=your-generated-32-char-secret-here
PASSWORD_HASH_SALT=your-generated-16-char-salt-here
```

---

### 6️⃣ Optional: Cloudflare R2 Storage (10 minutes)

**Why?** Store raw HTML and images (free 10GB/month)

```bash
1. Go to: https://dash.cloudflare.com/
2. Sign up/log in
3. Go to R2 → Create bucket
4. Bucket name: "carscout-raw-data"
5. Go to "Manage R2 API Tokens"
6. Create API token with "Edit" permissions
7. Copy:
   - Access Key ID → S3_ACCESS_KEY_ID
   - Secret Access Key → S3_SECRET_ACCESS_KEY
   - Endpoint → S3_ENDPOINT_URL
```

---

### 7️⃣ Optional: Sentry Error Tracking (5 minutes)

```bash
1. Go to: https://sentry.io/signup/
2. Create account
3. Create new project: "CarScout AI"
4. Platform: Python
5. Copy DSN (looks like: https://xxx@xxx.ingest.sentry.io/xxx)
6. Paste in .env: SENTRY_DSN=https://...
```

---

## 🧪 Testing Your Configuration

### Test Database Connection:
```powershell
# Start PostgreSQL
docker-compose up -d postgres

# Wait 10 seconds
Start-Sleep -Seconds 10

# Test connection
python -c "from libs.domain.database import engine; print('✅ Database connected!')"
```

### Test Telegram Bot:
```powershell
# Set your bot token in .env first!

# Test bot connection
python -c "from aiogram import Bot; import asyncio; bot = Bot(token='YOUR_TOKEN'); asyncio.run(bot.get_me())"

# Expected output: User(id=123456789, is_bot=True, first_name='CarScout Bot', ...)
```

### Test OpenAI API:
```powershell
# Test API key
python -c "from openai import OpenAI; client = OpenAI(); print('✅ OpenAI connected!')"
```

### Test Stripe:
```powershell
# Test Stripe connection
python -c "import stripe; stripe.api_key='YOUR_KEY'; print(stripe.Account.retrieve())"
```

---

## 🚀 Start All Services

```powershell
# 1. Start infrastructure
docker-compose up -d postgres redis

# 2. Run migrations
alembic upgrade head

# 3. Seed initial data
python scripts/seed_database.py

# 4. Start all services
docker-compose up -d

# 5. Check status
docker-compose ps

# 6. View logs
docker-compose logs -f
```

---

## 🔍 Troubleshooting

### Bot Not Responding?
```powershell
# Check bot token
docker-compose logs bot | Select-String "token"

# Test bot manually
curl https://api.telegram.org/bot<YOUR_TOKEN>/getMe
```

### Database Connection Error?
```powershell
# Check if PostgreSQL is running
docker-compose ps postgres

# Check connection string
$env:DATABASE_URL
```

### Stripe Webhooks Not Working?
```powershell
# For local testing, use ngrok:
# 1. Install ngrok: https://ngrok.com/download
# 2. Run: ngrok http 8000
# 3. Copy HTTPS URL (https://xxx.ngrok.io)
# 4. Update Stripe webhook endpoint: https://xxx.ngrok.io/api/stripe/webhook
```

---

## 📝 Environment Variables Summary

### ✅ Critical (Must Set):
- `TELEGRAM_BOT_TOKEN` - From @BotFather
- `TELEGRAM_PUBLIC_CHANNEL` - @YourChannel
- `TELEGRAM_PREMIUM_CHANNEL` - Chat ID
- `TELEGRAM_VIP_CHANNEL` - Chat ID
- `OPENAI_API_KEY` - From OpenAI
- `STRIPE_API_KEY` - From Stripe
- `STRIPE_WEBHOOK_SECRET` - From Stripe
- `API_SECRET_KEY` - Random 32 chars
- `PASSWORD_HASH_SALT` - Random 16 chars

### 🟡 Recommended:
- `STRIPE_PRICE_PREMIUM` - Stripe Price ID
- `STRIPE_PRICE_VIP` - Stripe Price ID
- `S3_*` - For storage (optional)

### 🟢 Optional:
- `SENTRY_DSN` - For error tracking
- `TELEGRAM_WEBHOOK_URL` - For production
- Feature flags as needed

---

## 🎯 Next Steps

After configuring `.env`:

1. ✅ Test database connection
2. ✅ Test Telegram bot
3. ✅ Run migrations: `alembic upgrade head`
4. ✅ Seed data: `python scripts/seed_database.py`
5. ✅ Start services: `docker-compose up -d`
6. ✅ Test end-to-end: `python scripts/test_pipeline.py`
7. 🚀 Launch!

---

## 🔒 Security Reminders

**NEVER commit `.env` to git!**

```bash
# .env should already be in .gitignore
# Verify:
cat .gitignore | Select-String ".env"

# If not, add it:
echo ".env" >> .gitignore
```

**For production:**
- Use environment variables in hosting platform
- Never use test Stripe keys in production
- Enable SSL/TLS for all connections
- Rotate secrets regularly

---

## 📞 Need Help?

- Telegram Bot issues: https://core.telegram.org/bots/faq
- Stripe setup: https://stripe.com/docs/development/quickstart
- OpenAI API: https://platform.openai.com/docs

Good luck! 🚀
