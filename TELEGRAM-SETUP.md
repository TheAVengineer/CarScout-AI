# Telegram Integration Guide 🤖

## Overview

CarScout AI has two Telegram integrations:
1. **User Bot** - Interactive bot for users to create alerts and get notifications
2. **Public Channel** - Automated posting of top car deals

## Prerequisites

Before setting up, you need:
- Telegram account
- BotFather access to create bots
- (Optional) A Telegram channel for public posts

---

## Part 1: Create Your Telegram Bot

### Step 1: Talk to BotFather

1. Open Telegram and search for **@BotFather**
2. Start a chat and send `/newbot`
3. Choose a name: `CarScout AI` (display name)
4. Choose a username: `carscout_bg_bot` (must end in `bot`)
5. BotFather will give you an **API token** like:
   ```
   1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
   ```

### Step 2: Configure Bot Settings

Send these commands to @BotFather:

```
/setdescription
```
Description:
```
🚗 CarScout AI helps you find the best car deals in Bulgaria.
Get instant alerts for BMW, Mercedes, Audi and more!
```

```
/setabouttext
```
About:
```
AI-powered car deal finder for mobile.bg and cars.bg
```

```
/setcommands
```
Commands:
```
start - Start the bot
watch - Create a price alert
unwatch - Remove an alert
list - Show your alerts
plan - View subscription
upgrade - Upgrade plan
help - Show all commands
```

---

## Part 2: Configure CarScout AI

### Update Environment Files

Edit `.env` (for local testing):

```bash
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_WEBHOOK_SECRET=your_random_secret_string_here_min_32_chars
TELEGRAM_WEBHOOK_URL=https://your-domain.com/telegram/webhook

# Optional: Public Channel Configuration
TELEGRAM_CHANNEL_BOT_TOKEN=your_channel_bot_token
TELEGRAM_CHANNEL_ID=-1001234567890
```

Edit `.env.docker` (for Docker):
```bash
# Same configuration as above
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_WEBHOOK_SECRET=your_random_secret_string_here_min_32_chars
TELEGRAM_WEBHOOK_URL=https://your-domain.com/telegram/webhook
```

### Generate Webhook Secret

```bash
# Generate a secure random string
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## Part 3: Run the Bot

### Option A: Local Development (Polling)

Best for testing and development:

```bash
# Activate virtual environment
source .venv/bin/activate

# Run the bot directly
python3 -m apps.bot.main
```

The bot will start polling for updates (no webhook needed).

### Option B: Docker (Polling)

```bash
# Start the bot service
docker-compose up -d bot

# View logs
docker-compose logs -f bot
```

### Option C: Production (Webhook)

For production with a public domain:

1. Deploy your API to a server with HTTPS
2. Set the webhook URL in `.env`:
   ```bash
   TELEGRAM_WEBHOOK_URL=https://yourdomain.com/api/telegram/webhook
   ```

3. Set the webhook:
   ```bash
   curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" \
     -H "Content-Type: application/json" \
     -d '{
       "url": "https://yourdomain.com/api/telegram/webhook",
       "secret_token": "your_webhook_secret"
     }'
   ```

---

## Part 4: Create a Public Channel (Optional)

### Step 1: Create Channel

1. Open Telegram
2. Click "New Channel"
3. Name: `CarScout AI - Best Deals`
4. Description: Top car deals found by AI
5. Make it **Public** with username: `@carscout_deals`

### Step 2: Add Bot as Admin

1. Open your channel
2. Click on channel name → Administrators
3. Click "Add Administrator"
4. Search for your bot username: `@carscout_bg_bot`
5. Give permissions: "Post Messages"

### Step 3: Get Channel ID

```bash
# Send a message in your channel, then run:
curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates"
```

Look for `"chat":{"id":-1001234567890}` - that's your channel ID.

Update `.env`:
```bash
TELEGRAM_CHANNEL_ID=-1001234567890
```

---

## Part 5: Test the Integration

### Quick Test Script

```bash
# Create test script
cat > scripts/test_telegram.py << 'EOF'
#!/usr/bin/env python3
"""Test Telegram bot integration"""
import asyncio
from aiogram import Bot
from configs.settings import settings

async def test_bot():
    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
    
    # Get bot info
    me = await bot.get_me()
    print(f"✅ Bot connected: @{me.username}")
    print(f"   Name: {me.first_name}")
    print(f"   ID: {me.id}")
    
    # Test sending message (replace with your Telegram user ID)
    # Get your ID by messaging @userinfobot
    # await bot.send_message(chat_id=YOUR_USER_ID, text="🚗 CarScout AI is online!")
    
    await bot.session.close()

if __name__ == "__main__":
    asyncio.run(test_bot())
EOF

# Run test
python3 scripts/test_telegram.py
```

### Manual Test

1. Open Telegram
2. Search for your bot: `@carscout_bg_bot`
3. Send `/start`
4. You should get the welcome message!

---

## How It Works

### User Flow

1. **User starts bot** → `/start`
   - Bot creates user record in database
   - Shows welcome message and commands

2. **User creates alert** → `/watch`
   - User sends: `BMW X5 diesel <25000 2016+ <180000km`
   - Bot parses DSL query
   - Saves alert to database

3. **Alert matching** → Background worker
   - Worker checks new listings against alerts
   - When match found → creates alert_match record

4. **Notification** → Background worker
   - Worker sends Telegram message with listing details
   - Includes images, price, link
   - Marks delivery status

### Channel Flow

1. **Scoring** → Background worker
   - Listings get scored (0-100)
   - Top deals (score > 85) marked for posting

2. **Channel posting** → Background worker
   - Worker creates formatted message
   - Posts to channel with images
   - Saves post record

---

## Bot Commands Implementation

### Current Status

| Command | Status | Description |
|---------|--------|-------------|
| `/start` | ✅ Implemented | Welcome message |
| `/help` | ✅ Implemented | Show commands |
| `/watch` | 🚧 Partial | TODO: Parse DSL and save alert |
| `/unwatch` | 🚧 Partial | TODO: Show alerts and remove |
| `/list` | 🚧 Partial | TODO: Fetch user alerts |
| `/plan` | 🚧 Partial | TODO: Show subscription |

### Completing the Implementation

The bot handlers are in `apps/bot/handlers/`. To complete them:

1. **Watch command** - Parse user query and create alert
2. **Database integration** - Connect to PostgreSQL
3. **User management** - Create/update user records
4. **Alert delivery** - Worker to send notifications

---

## Architecture

```
┌─────────────────┐
│  Telegram User  │
└────────┬────────┘
         │ /watch BMW X5
         ▼
┌─────────────────┐
│   Bot Handler   │────► Parse DSL Query
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Database      │────► Save Alert
└─────────────────┘

Background Workers:
┌──────────────────┐
│  Scraper Worker  │────► Fetch new listings
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Matcher Worker   │────► Match alerts
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Notify Worker   │────► Send Telegram message
└──────────────────┘
```

---

## Troubleshooting

### Bot doesn't respond

```bash
# Check bot logs
docker-compose logs -f bot

# Verify token
curl "https://api.telegram.org/bot<TOKEN>/getMe"
```

### Database connection errors

```bash
# Check if bot can reach database
docker-compose exec bot python -c "from libs.domain.database import sync_engine; print(sync_engine)"
```

### Webhook issues

```bash
# Check webhook status
curl "https://api.telegram.org/bot<TOKEN>/getWebhookInfo"

# Delete webhook (for polling mode)
curl "https://api.telegram.org/bot<TOKEN>/deleteWebhook"
```

---

## Next Steps

1. **Get bot token from @BotFather**
2. **Update `.env` and `.env.docker`**
3. **Test bot locally**: `python3 -m apps.bot.main`
4. **Complete watch/unwatch handlers**
5. **Set up notification workers**
6. **Create public channel** (optional)
7. **Deploy to production** with webhook

---

## Example: Complete Alert Flow

```python
# User sends in Telegram:
/watch BMW X5 diesel automatic <30000 2018+ Sofia

# Bot parses and saves:
Alert(
    user_id=user.id,
    dsl_query="BMW X5 diesel automatic <30000 2018+ Sofia",
    normalized_filters={
        "brand": "bmw",
        "model": "x5",
        "fuel": "diesel",
        "gearbox": "automatic",
        "price_max": 30000,
        "year_min": 2018,
        "region": "Sofia"
    }
)

# Worker finds match:
Listing(
    brand="BMW",
    model="X5",
    price=28500,
    year=2019,
    fuel="diesel",
    gearbox="automatic",
    region="Sofia"
)

# Bot sends notification:
🚗 New match for your alert!

BMW X5 3.0d xDrive
📅 2019 | ⛽ Diesel | 🔧 Automatic
📍 Sofia | 🏃 45,000 km
💰 28,500 BGN

🎯 Score: 87/100
✅ Below your budget by 1,500 BGN
🔗 View listing: https://mobile.bg/...
```

Ready to set up your bot? Start with Step 1! 🚀
