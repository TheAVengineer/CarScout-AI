# Telegram Integration Architecture

## Complete Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER INTERACTION                         │
└─────────────────────────────────────────────────────────────────┘

    Telegram User
         │
         │ 1. /start
         ▼
    ┌─────────────┐
    │  Bot Handler│──────► Create/Update User Record
    │  (start.py) │        in PostgreSQL
    └──────┬──────┘
           │
           │ Welcome Message
           ▼
    Telegram User
         │
         │ 2. /watch BMW X5 diesel <30000
         ▼
    ┌─────────────┐
    │  Bot Handler│──────► Parse DSL Query
    │  (watch.py) │
    └──────┬──────┘
           │
           │ Parsed Filters
           ▼
    ┌─────────────┐
    │  Database   │──────► Save Alert Record
    └─────────────┘


┌─────────────────────────────────────────────────────────────────┐
│                      BACKGROUND PROCESSING                       │
└─────────────────────────────────────────────────────────────────┘

    ┌──────────────┐
    │   Scraper    │──────► Fetch new listings
    │   Worker     │        from mobile.bg, cars.bg
    └──────┬───────┘
           │
           │ Raw HTML
           ▼
    ┌──────────────┐
    │   Parser     │──────► Extract data
    │   Worker     │        (brand, model, price, etc.)
    └──────┬───────┘
           │
           │ Normalized Data
           ▼
    ┌──────────────┐
    │  Normalizer  │──────► Clean & standardize
    │   Worker     │
    └──────┬───────┘
           │
           │ Clean Listing
           ▼
    ┌──────────────┐
    │   Dedupe     │──────► Check for duplicates
    │   Worker     │        (images, description)
    └──────┬───────┘
           │
           │ Unique Listing
           ▼
    ┌──────────────┐
    │   Pricing    │──────► Estimate fair price
    │   Worker     │        using AI/comparables
    └──────┬───────┘
           │
           │ + Price Estimate
           ▼
    ┌──────────────┐
    │   Risk AI    │──────► GPT-4o mini analysis
    │   Worker     │        (scam detection)
    └──────┬───────┘
           │
           │ + Risk Score
           ▼
    ┌──────────────┐
    │   Scoring    │──────► Calculate final score
    │   Worker     │        (0-100)
    └──────┬───────┘
           │
           │ Scored Listing
           ▼
    ┌──────────────┐
    │   Matcher    │──────► Match against user alerts
    │   Worker     │
    └──────┬───────┘
           │
           │ Matched Alerts
           ▼
    ┌──────────────┐
    │  Notifier    │──────► Send Telegram message
    │   Worker     │
    └──────┬───────┘
           │
           ▼
    Telegram User
         │
         │ 🚗 New match: BMW X5...
         │
         │ 3. Click "View Listing"
         ▼
    Browser opens mobile.bg


┌─────────────────────────────────────────────────────────────────┐
│                      CHANNEL POSTING                             │
└─────────────────────────────────────────────────────────────────┘

    ┌──────────────┐
    │   Scoring    │
    │   Worker     │
    └──────┬───────┘
           │
           │ Score > 85?
           ▼
    ┌──────────────┐
    │  Channel     │──────► Format message
    │  Poster      │        with images, details
    └──────┬───────┘
           │
           │ Post to Channel
           ▼
    @carscout_deals
         │
         │ Public followers see post
         ▼
    Many Users
```

## Database Schema for Telegram

```sql
-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY,
    telegram_user_id BIGINT UNIQUE,
    email VARCHAR(255) UNIQUE,
    role user_role_enum,
    created_at TIMESTAMP
);

-- Alerts table
CREATE TABLE alerts (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    dsl_query TEXT,
    normalized_filters JSON,
    active BOOLEAN,
    created_at TIMESTAMP
);

-- Alert matches table
CREATE TABLE alert_matches (
    id UUID PRIMARY KEY,
    alert_id UUID REFERENCES alerts(id),
    listing_id UUID REFERENCES listings_normalized(id),
    matched_at TIMESTAMP,
    delivered_at TIMESTAMP,
    delivery_status delivery_status_enum,
    reason TEXT
);

-- Channel posts table
CREATE TABLE channel_posts (
    id UUID PRIMARY KEY,
    listing_id UUID REFERENCES listings_normalized(id),
    telegram_message_id BIGINT,
    posted_at TIMESTAMP,
    channel VARCHAR(100)
);
```

## Message Flow Examples

### 1. Alert Creation

```
User: /watch BMW X5 diesel automatic <30000 2018+ Sofia

Bot: ✅ Alert created!

🔔 BMW X5
⛽ Diesel
🔧 Automatic
💰 Under 30,000 BGN
📅 2018 or newer
📍 Sofia

You'll get notified when matches are found.
```

### 2. Match Notification

```
Bot: 🚗 New match for your alert!

BMW X5 3.0d xDrive
📅 2019 | ⛽ Diesel | 🔧 Automatic
📍 Sofia | 🏃 45,000 km
💰 28,500 BGN

🎯 Score: 87/100
✅ Below your budget by 1,500 BGN
⚠️ Mileage is average for year

🔗 View listing: https://mobile.bg/...

[Reserve] [Contact Seller] [Dismiss]
```

### 3. Channel Post

```
🔥 TOP DEAL ALERT

BMW X5 3.0d xDrive (2019)

📊 Our AI Score: 92/100

💰 Price: 28,500 BGN
💵 Fair Price: 32,000 BGN
🎯 You save: 3,500 BGN (11%)

⛽ Diesel | 🔧 Automatic
🏃 45,000 km | 📍 Sofia

✅ Full service history
✅ Single owner
✅ Recent inspection
⚠️ Minor cosmetic wear

🔗 mobile.bg/listing/123456

#BMW #X5 #Diesel #Sofia #Deal
```

## Bot Commands Detail

### /start
- Check if user exists in database
- Create user record if new (telegram_user_id)
- Assign Free plan by default
- Send welcome message with commands

### /watch [query]
- Parse DSL query (e.g., "BMW X5 diesel <30000")
- Validate against user's plan limits (Free = 3 alerts)
- Save alert to database
- Return confirmation with parsed filters

### /unwatch
- Fetch user's alerts from database
- Show inline keyboard with alert list
- Handle callback for deletion
- Confirm deletion

### /list
- Query alerts table for user_id
- Format each alert nicely
- Show active/inactive status
- Show match count

### /plan
- Query subscription table
- Show current plan (Free/Premium/Pro)
- Show limits (alerts, delay, daily cap)
- Show upgrade options

## Worker Tasks

### Alert Matcher (Celery Task)
```python
@celery_app.task
def match_alerts():
    # Get new listings (last 5 minutes)
    new_listings = get_recent_listings()
    
    # Get all active alerts
    alerts = get_active_alerts()
    
    for listing in new_listings:
        for alert in alerts:
            if matches(listing, alert.filters):
                # Create match record
                create_match(alert.id, listing.id)
                
                # Queue notification
                notify_user.delay(alert.user_id, listing.id)
```

### Notification Sender (Celery Task)
```python
@celery_app.task
def notify_user(user_id, listing_id):
    user = get_user(user_id)
    listing = get_listing(listing_id)
    
    # Format message
    message = format_listing_message(listing)
    
    # Send via Telegram
    await bot.send_message(
        chat_id=user.telegram_user_id,
        text=message,
        parse_mode="HTML",
        reply_markup=get_listing_keyboard(listing.id)
    )
    
    # Mark as delivered
    update_delivery_status(match_id, "delivered")
```

### Channel Poster (Celery Task)
```python
@celery_app.task
def post_to_channel():
    # Get top deals (score > 85, not posted)
    top_deals = get_top_unposted_deals()
    
    for listing in top_deals:
        # Format channel message
        message = format_channel_message(listing)
        
        # Post to channel
        msg = await bot.send_message(
            chat_id=settings.TELEGRAM_CHANNEL_ID,
            text=message,
            parse_mode="HTML"
        )
        
        # Save post record
        save_channel_post(listing.id, msg.message_id)
```

## Security Considerations

1. **Webhook Secret**: Verify all webhook requests
2. **Rate Limiting**: Limit alerts per user per plan
3. **User Validation**: Check telegram_user_id ownership
4. **Data Privacy**: Don't expose other users' data
5. **Spam Protection**: Limit message frequency

## Deployment Checklist

- [ ] Create bot with @BotFather
- [ ] Configure bot token in .env
- [ ] Generate webhook secret
- [ ] Set up webhook URL (production)
- [ ] Create Telegram channel (optional)
- [ ] Add bot as channel admin
- [ ] Get channel ID
- [ ] Test bot locally (polling)
- [ ] Test alerts creation
- [ ] Test notification delivery
- [ ] Deploy to production
- [ ] Set webhook
- [ ] Monitor logs

Ready to integrate? Run: `./scripts/setup_telegram.sh` 🚀
