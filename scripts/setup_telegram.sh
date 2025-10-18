#!/bin/bash

# Telegram Bot Quick Start Script
# This script guides you through setting up your Telegram bot

echo "🤖 CarScout AI - Telegram Bot Setup"
echo "===================================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found"
    exit 1
fi

# Check if token is configured
TOKEN=$(grep "^TELEGRAM_BOT_TOKEN=" .env | cut -d '=' -f2)

if [ "$TOKEN" == "YOUR_BOT_TOKEN_HERE" ] || [ -z "$TOKEN" ]; then
    echo "📝 Bot token not configured yet."
    echo ""
    echo "Follow these steps:"
    echo ""
    echo "1️⃣  Open Telegram and search for: @BotFather"
    echo ""
    echo "2️⃣  Send this message: /newbot"
    echo ""
    echo "3️⃣  Choose a name: CarScout AI"
    echo ""
    echo "4️⃣  Choose a username: carscout_bg_bot"
    echo "    (or any name ending in 'bot')"
    echo ""
    echo "5️⃣  BotFather will give you a token like:"
    echo "    1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"
    echo ""
    echo "6️⃣  Copy that token and paste it here:"
    read -p "    Token: " NEW_TOKEN
    
    if [ -z "$NEW_TOKEN" ]; then
        echo "❌ No token provided"
        exit 1
    fi
    
    # Update .env
    sed -i '' "s|TELEGRAM_BOT_TOKEN=.*|TELEGRAM_BOT_TOKEN=$NEW_TOKEN|" .env
    
    # Update .env.docker
    if [ -f .env.docker ]; then
        sed -i '' "s|TELEGRAM_BOT_TOKEN=.*|TELEGRAM_BOT_TOKEN=$NEW_TOKEN|" .env.docker
    fi
    
    echo ""
    echo "✅ Token saved to .env!"
    echo ""
fi

# Generate webhook secret if needed
WEBHOOK_SECRET=$(grep "^TELEGRAM_WEBHOOK_SECRET=" .env | cut -d '=' -f2)

if [ "$WEBHOOK_SECRET" == "test_webhook_secret_12345" ]; then
    echo "🔐 Generating secure webhook secret..."
    NEW_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    
    sed -i '' "s|TELEGRAM_WEBHOOK_SECRET=.*|TELEGRAM_WEBHOOK_SECRET=$NEW_SECRET|" .env
    
    if [ -f .env.docker ]; then
        sed -i '' "s|TELEGRAM_WEBHOOK_SECRET=.*|TELEGRAM_WEBHOOK_SECRET=$NEW_SECRET|" .env.docker
    fi
    
    echo "✅ Webhook secret generated"
    echo ""
fi

# Test the connection
echo "🔄 Testing bot connection..."
echo ""

source .venv/bin/activate
python3 scripts/test_telegram.py

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 Success! Your bot is ready!"
    echo ""
    echo "To start the bot:"
    echo "  python3 -m apps.bot.main"
    echo ""
    echo "Or with Docker:"
    echo "  docker-compose up -d bot"
    echo ""
else
    echo ""
    echo "❌ Bot test failed. Check the error above."
    echo ""
    echo "For help, see: TELEGRAM-SETUP.md"
fi
