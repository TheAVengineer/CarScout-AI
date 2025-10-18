"""
Start command handler
"""
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message):
    """Handle /start command"""
    welcome_text = """
🚗 <b>Welcome to CarScout AI!</b>

I help you find the best car deals on Bulgarian marketplaces.

Available commands:
/watch - Create a new price alert
/unwatch - Remove an alert
/plan - View and upgrade your subscription
/help - Show all commands

Let's find your perfect car! 🎯
"""
    await message.answer(welcome_text)


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Handle /help command"""
    help_text = """
<b>CarScout AI Commands:</b>

🔍 <b>Alerts:</b>
/watch - Create a new price alert
/unwatch - Remove an existing alert
/list - Show your active alerts

💳 <b>Subscription:</b>
/plan - View current plan
/upgrade - Upgrade to Premium/Pro

🚗 <b>Actions:</b>
/reserve - Reserve a car listing
/contact - Get seller contact info

❓ <b>Help:</b>
/help - Show this message
"""
    await message.answer(help_text)
