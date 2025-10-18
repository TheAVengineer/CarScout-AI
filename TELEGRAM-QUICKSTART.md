# 🤖 Telegram Integration - Quick Summary

## What You Need to Do

### Step 1: Create Your Bot (5 minutes)

1. Open Telegram, search for **@BotFather**
2. Send `/newbot`
3. Name it: `CarScout AI`
4. Username: `carscout_bg_bot` (or similar, must end in 'bot')
5. Copy the token you receive

### Step 2: Configure CarScout (2 minutes)

**Option A: Use the setup script**
```bash
./scripts/setup_telegram.sh
```
(Paste your token when prompted)

**Option B: Manual configuration**

Edit `.env`:
```bash
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHI...  # Paste your token here
```

Edit `.env.docker`:
```bash
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHI...  # Same token
```

### Step 3: Test It (1 minute)

```bash
# Test the connection
python3 scripts/test_telegram.py

# If successful, start the bot
python3 -m apps.bot.main
```

### Step 4: Try It Out

1. Open Telegram
2. Search for your bot: `@carscout_bg_bot`
3. Send `/start`
4. You should see the welcome message! 🎉

---

## How It Works

### User Experience

```
User                Bot                    System
 │                   │                      │
 │─── /start ───────>│                      │
 │                   │                      │
 │<── Welcome! ──────│                      │
 │                   │                      │
 │─── /watch ───────>│                      │
 │    BMW X5         │                      │
 │                   │─── Create Alert ───>│
 │                   │                      │
 │<── Alert saved! ──│                      │
 │                   │                      │
 │                   │                      │
 │                   │      (background)    │
 │                   │<─── New Match! ─────│
 │                   │                      │
 │<── 🚗 BMW X5 ─────│                      │
 │    found!         │                      │
```

### What's Included

✅ **Bot Framework**: Aiogram (async Telegram bot library)
✅ **Bot Handlers**: `/start`, `/help`, `/watch`, `/unwatch`, `/list`, `/plan`
✅ **Database Integration**: User management, alerts, notifications
✅ **Worker Tasks**: Alert matching, notification delivery
✅ **Channel Posting**: Automated posts of top deals (optional)

### What Needs Completion

🚧 **Alert Parsing**: Parse DSL query (e.g., "BMW X5 <30000")
🚧 **Alert Storage**: Save parsed alerts to database
🚧 **Alert Matching**: Background worker to match listings
🚧 **Notifications**: Send Telegram messages when matches found

---

## Files Created/Modified

**Documentation:**
- ✅ `TELEGRAM-SETUP.md` - Complete setup guide
- ✅ `TELEGRAM-ARCHITECTURE.md` - Technical architecture
- ✅ `scripts/test_telegram.py` - Connection test
- ✅ `scripts/setup_telegram.sh` - Automated setup

**Existing Bot Code:**
- `apps/bot/main.py` - Bot entry point
- `apps/bot/handlers/start.py` - Start/help commands
- `apps/bot/handlers/watch.py` - Alert management
- `apps/bot/handlers/plan.py` - Subscription management
- `apps/api/routers/telegram.py` - Webhook endpoint

---

## Example Alert Flow

### 1. User Creates Alert

```
User: /watch BMW X5 diesel automatic <30000 2018+ Sofia

Bot: ✅ Alert created!
     Brand: BMW X5
     Fuel: Diesel
     Gearbox: Automatic
     Price: Under 30,000 BGN
     Year: 2018 or newer
     Location: Sofia
```

### 2. System Finds Match (Background)

```python
# Scraper finds new listing
listing = {
    "brand": "BMW",
    "model": "X5",
    "fuel": "diesel",
    "gearbox": "automatic",
    "price": 28500,
    "year": 2019,
    "region": "Sofia"
}

# Matcher checks alerts
if matches_alert(listing, user_alert):
    send_notification(user_id, listing)
```

### 3. User Gets Notification

```
Bot: 🚗 New match for your alert!

     BMW X5 3.0d xDrive
     📅 2019 | ⛽ Diesel | 🔧 Automatic
     📍 Sofia | 🏃 45,000 km
     💰 28,500 BGN

     🎯 Score: 87/100
     ✅ Below your budget by 1,500 BGN

     🔗 View: https://mobile.bg/...

     [Reserve] [Contact] [Dismiss]
```

---

## Running the Bot

### Development (Local)

```bash
# Activate environment
source .venv/bin/activate

# Run bot (polling mode)
python3 -m apps.bot.main
```

The bot will continuously check for updates (polling).

### Docker

```bash
# Start bot service
docker-compose up -d bot

# View logs
docker-compose logs -f bot

# Restart after changes
docker-compose restart bot
```

### Production (Webhook)

For production, use webhooks instead of polling:

```bash
# Set webhook URL in .env
TELEGRAM_WEBHOOK_URL=https://yourdomain.com/api/telegram/webhook

# Set webhook via API
curl -X POST "https://api.telegram.org/bot<TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://yourdomain.com/api/telegram/webhook",
    "secret_token": "your_webhook_secret"
  }'
```

---

## Available Commands

| Command | Status | Description |
|---------|--------|-------------|
| `/start` | ✅ Working | Welcome message |
| `/help` | ✅ Working | Show commands |
| `/watch` | 🚧 Partial | Create alert (needs completion) |
| `/unwatch` | 🚧 Partial | Remove alert |
| `/list` | 🚧 Partial | Show your alerts |
| `/plan` | 🚧 Partial | View subscription |

---

## Next Steps to Complete Integration

### 1. Complete Alert Parser

```python
# In apps/bot/handlers/watch.py
from libs.alert_dsl.parser import parse_dsl

@router.message(Command("watch"))
async def cmd_watch(message: Message):
    query = message.text.replace("/watch", "").strip()
    
    # Parse the query
    filters = parse_dsl(query)
    
    # Save to database
    alert = create_alert(
        user_id=message.from_user.id,
        dsl_query=query,
        filters=filters
    )
    
    # Confirm to user
    await message.answer(f"✅ Alert created!\n{format_alert(alert)}")
```

### 2. Add Database Integration

```python
# Connect to database in handlers
from libs.domain.database import get_sync_session
from libs.domain.models import User, Alert

def get_or_create_user(telegram_id):
    session = get_sync_session()
    user = session.query(User).filter_by(telegram_user_id=telegram_id).first()
    
    if not user:
        user = User(telegram_user_id=telegram_id)
        session.add(user)
        session.commit()
    
    return user
```

### 3. Implement Matcher Worker

```python
# In workers/pipeline/tasks/alerts.py
@celery_app.task
def match_new_listings():
    # Get listings from last 5 minutes
    recent = get_recent_listings()
    
    # Get all active alerts
    alerts = get_active_alerts()
    
    # Match them
    for listing in recent:
        for alert in alerts:
            if matches(listing, alert):
                notify_user.delay(alert.user_id, listing.id)
```

### 4. Implement Notifier

```python
@celery_app.task
async def notify_user(user_id, listing_id):
    from aiogram import Bot
    
    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
    user = get_user(user_id)
    listing = get_listing(listing_id)
    
    message = format_notification(listing)
    
    await bot.send_message(
        chat_id=user.telegram_user_id,
        text=message,
        parse_mode="HTML"
    )
```

---

## Resources

📖 **Full Guides:**
- `TELEGRAM-SETUP.md` - Step-by-step setup
- `TELEGRAM-ARCHITECTURE.md` - Technical details

🔧 **Scripts:**
- `scripts/setup_telegram.sh` - Automated setup
- `scripts/test_telegram.py` - Test connection

💻 **Code:**
- `apps/bot/` - Bot application
- `apps/api/routers/telegram.py` - Webhook handler

---

## Quick Start Right Now

```bash
# 1. Run setup script
./scripts/setup_telegram.sh

# 2. Follow the prompts to enter your bot token

# 3. Test the connection
python3 scripts/test_telegram.py

# 4. Start the bot
python3 -m apps.bot.main

# 5. Open Telegram and message your bot!
```

That's it! Your Telegram bot is ready to receive commands. The alert matching and notification features need completion, but the foundation is solid. 🚀

---

**Questions? Check `TELEGRAM-SETUP.md` for detailed instructions!**
