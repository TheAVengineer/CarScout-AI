"""
Subscription plan handlers
"""
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

router = Router()


@router.message(Command("plan"))
async def cmd_plan(message: Message):
    """Show current subscription plan"""
    # TODO: Fetch user subscription from database
    plan_info = """
📊 <b>Your Plan: Free</b>

✅ 3 price alerts
✅ Channel updates
⏰ 30 min delay on alerts

Upgrade to Premium for:
⚡ Instant alerts
📈 10 price alerts
🎯 Priority reservations
"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬆️ Upgrade to Premium", callback_data="upgrade_premium")],
        [InlineKeyboardButton(text="🚀 Upgrade to Pro", callback_data="upgrade_pro")]
    ])
    
    await message.answer(plan_info, reply_markup=keyboard)


@router.message(Command("upgrade"))
async def cmd_upgrade(message: Message):
    """Show upgrade options"""
    upgrade_text = """
💎 <b>Choose Your Plan:</b>

<b>Premium - 19.99 BGN/month</b>
⚡ Instant alerts (0 delay)
📈 Up to 10 price alerts
🎯 Priority on reservations

<b>Pro - 39.99 BGN/month</b>
⚡ Instant alerts
📈 Unlimited price alerts
🎯 Highest priority
📞 Direct seller contacts
🤖 Custom AI insights
"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Premium - 19.99 BGN", callback_data="checkout_premium")],
        [InlineKeyboardButton(text="Pro - 39.99 BGN", callback_data="checkout_pro")]
    ])
    
    await message.answer(upgrade_text, reply_markup=keyboard)
