# 📺 Telegram Channel Setup - SIMPLIFIED

**Date**: October 21, 2025  
**Bot**: @carscout_bg_bot (ONE bot for everything)

---

## 🚀 QUICK START (5 minutes)

### Method 1: Automated Script (Easiest) ⭐

1. **Create 3 channels** in Telegram (Public, Premium, VIP)
2. **Add @carscout_bg_bot as admin** to all channels
3. **Post "Test from admin"** in each channel
4. **Run**: `python scripts/get_channel_ids.py`
5. **Copy the channel IDs** to your `.env` file
6. **Done!** 🎉

### Method 2: Browser API (Manual)

1. Create channels and add bot as admin
2. Post test message in each channel
3. Open: `https://api.telegram.org/bot8475247422:AAHVDBEI5TPkFhwUGpHFoi-Vun_YyfF4-gs/getUpdates`
4. Find `"channel_post"` → `"chat"` → `"id"` in JSON
5. Copy the negative number (e.g., `-1001938475629`)
6. Update `.env` with channel IDs

---

## ✅ Current Status

Your bot `@carscout_bg_bot` is **ready and working**!
- ✅ Bot Token: Configured in `.env`
- ✅ Bot Username: @carscout_bg_bot
- ✅ Bot ID: 8475247422

---

## 📋 What You Need To Do Now

### Create 3 Telegram Channels

You need to create **three channels** for your three-tier business model:

1. **Public Channel** (FREE) - Anyone can see teasers
2. **Premium Channel** (€14.99/mo) - Paid subscribers get 10 deals/day
3. **VIP Channel** (€29.99/mo) - Premium subscribers get 20+ deals/day + early access

---

## 🔧 Step-by-Step Instructions

### Step 1: Create PUBLIC CHANNEL (Free Tier)

1. **Open Telegram** on your phone or desktop
2. Click **"New Channel"**
3. **Channel Name**: `CarScout Deals` (or your preferred name)
4. **Description**: 
   ```
   🚗 Best Car Deals in Bulgaria
   AI-powered listing analysis
   Subscribe for premium full details
   ```
5. **Channel Type**: Choose **PUBLIC**
6. **Username**: Choose a username like `@CarScoutDeals` or `@CarScoutBG`
   - Must be unique
   - Must be available
   - This is what users will see and can share
7. **Click "Create"**

8. **Make your bot an admin:**
   - Go to Channel Settings → Administrators
   - Click "Add Administrator"
   - Search for `@carscout_bg_bot`
   - Give it these permissions:
     - ✅ Post Messages
     - ✅ Edit Messages
     - ✅ Delete Messages
   - Click "Save"

9. **Get the channel username:**
   - It should be `@CarScoutDeals` (or whatever you chose)
   - Copy this username

10. **Update `.env` file:**
    ```env
    TELEGRAM_PUBLIC_CHANNEL=@CarScoutDeals
    ```

---

### Step 2: Create PREMIUM CHANNEL (€14.99/mo)

1. **Open Telegram**
2. Click **"New Channel"**
3. **Channel Name**: `CarScout Premium Deals`
4. **Description**:
   ```
   🌟 CarScout Premium
   10 verified deals per day
   Full contact details
   AI risk analysis
   ```
5. **Channel Type**: Choose **PRIVATE** (important!)
   - Do NOT set a username
   - Private channels use numeric IDs
6. **Click "Create"**

7. **Make your bot an admin:**
   - Channel Settings → Administrators → Add Administrator
   - Search for `@carscout_bg_bot`
   - Give permissions: Post Messages, Edit Messages, Delete Messages
   - Click "Save"

8. **Get the channel ID** (IMPORTANT - Use Bot API Method):
   
   **Method 1: Using Bot API (Recommended)**
   - **Post a test message** in your channel (e.g., "Test from admin")
   - Open your browser and go to:
     ```
     https://api.telegram.org/bot8475247422:AAHVDBEI5TPkFhwUGpHFoi-Vun_YyfF4-gs/getUpdates
     ```
   - Look for JSON response with `"channel_post"` → `"chat"` → `"id"`
   - Copy the **negative number** (e.g., `-1001938475629`)
   - This is your channel ID!
   
   **Method 2: Using PowerShell (Alternative)**
   ```powershell
   Invoke-RestMethod -Uri "https://api.telegram.org/bot8475247422:AAHVDBEI5TPkFhwUGpHFoi-Vun_YyfF4-gs/getUpdates" | ConvertTo-Json -Depth 10
   ```
   
   **Note**: RawDataBot doesn't work with private channels, so use the API method above.

9. **Update `.env` file:**
   ```env
   TELEGRAM_PREMIUM_CHANNEL=-1001234567890
   ```
   (Replace with your actual channel ID from RawDataBot)

---

### Step 3: Create VIP CHANNEL (€29.99/mo)

1. **Open Telegram**
2. Click **"New Channel"**
3. **Channel Name**: `CarScout VIP Deals`
4. **Description**:
   ```
   💎 CarScout VIP
   20+ verified deals per day
   15-minute early access
   Priority support
   ```
5. **Channel Type**: Choose **PRIVATE** (important!)
   - Do NOT set a username
6. **Click "Create"**

7. **Make your bot an admin:**
   - Channel Settings → Administrators → Add Administrator
   - Search for `@carscout_bg_bot`
   - Give permissions: Post Messages, Edit Messages, Delete Messages
   - Click "Save"

8. **Get the channel ID** (IMPORTANT - Use Bot API Method):
   
   **Method 1: Using Bot API (Recommended)**
   - **Post a test message** in your channel (e.g., "Test from admin")
   - Open your browser and go to:
     ```
     https://api.telegram.org/bot8475247422:AAHVDBEI5TPkFhwUGpHFoi-Vun_YyfF4-gs/getUpdates
     ```
   - Look for JSON response with `"channel_post"` → `"chat"` → `"id"`
   - Copy the **negative number** (e.g., `-1001938475629`)
   - This is your channel ID!
   
   **Method 2: Using PowerShell (Alternative)**
   ```powershell
   Invoke-RestMethod -Uri "https://api.telegram.org/bot8475247422:AAHVDBEI5TPkFhwUGpHFoi-Vun_YyfF4-gs/getUpdates" | ConvertTo-Json -Depth 10
   ```
   
   **Note**: RawDataBot doesn't work with private channels, so use the API method above.

9. **Update `.env` file:**
   ```env
   TELEGRAM_VIP_CHANNEL=-1009876543210
   ```
   (Replace with your actual channel ID)

---

## 📝 Final .env Configuration

After creating all three channels, your `.env` should look like:

```env
# ============================================
# TELEGRAM BOT (CONFIGURED)
# ============================================
TELEGRAM_BOT_TOKEN=8475247422:AAHVDBEI5TPkFhwUGpHFoi-Vun_YyfF4-gs

# ============================================
# TELEGRAM CHANNELS (UPDATE THESE!)
# ============================================
# Public Channel (FREE - Teaser Posts)
TELEGRAM_PUBLIC_CHANNEL=@CarScoutDeals

# Premium Channel (€14.99/mo subscribers only)
TELEGRAM_PREMIUM_CHANNEL=-1001234567890

# VIP Channel (€29.99/mo subscribers only)
TELEGRAM_VIP_CHANNEL=-1009876543210
```

---

## ✅ Testing

Once you've updated `.env` with all three channel IDs, run:

```bash
# Automated helper script to get channel IDs
python scripts/get_channel_ids.py

# After you have the IDs, test posting
python scripts/test_channel_posting.py
```

The `get_channel_ids.py` script will:
1. ✅ Connect to your bot
2. ✅ Fetch recent updates from Telegram
3. ✅ Show you all channel IDs where your bot posted
4. ✅ Generate the `.env` configuration for you

**Important**: Before running the script:
- Create your channels
- Add @carscout_bg_bot as admin
- **Post a test message** in each channel (e.g., "Test from admin")
- Wait 10 seconds, then run the script

---

## 🎯 Business Model Summary

| Tier | Price | Features | Channel Type | Posts/Day |
|------|-------|----------|--------------|-----------|
| **Free** | €0 | Blurred images, no contact | Public (@CarScoutDeals) | Unlimited teasers |
| **Premium** | €14.99/mo | Full details, 10 deals | Private (-100xxx) | 10 verified deals |
| **VIP** | €29.99/mo | Everything + early access | Private (-100yyy) | 20+ deals + 15min early |

---

## 🔐 Important Notes

1. **Private channels are better for paid tiers** because:
   - Only invited members can see posts
   - Bot can add/remove users automatically
   - Can't be shared publicly
   - More exclusive feeling

2. **Public channel is better for free tier** because:
   - Acts as marketing funnel
   - Users can share with friends
   - Shows value proposition
   - Drives paid conversions

3. **Bot permissions**:
   - Bot needs "Post Messages" to send deals
   - Bot needs "Manage Users" to add paid subscribers (for Premium/VIP)

---

## 📞 Need Help?

If you have issues:

1. Make sure bot is admin in ALL channels
2. Make sure private channel IDs are negative numbers
3. Make sure public channel starts with `@`
4. Run the test script to verify everything works

---

**Next**: After setup, tell me the three channel IDs and I'll create the posting test script! 🚀
