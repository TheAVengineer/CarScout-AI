"""
Watch/alert management handlers
"""
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router()


@router.message(Command("watch"))
async def cmd_watch(message: Message):
    """Create a new price alert"""
    # TODO: Parse DSL query and create alert
    await message.answer(
        "📝 To create an alert, send me your criteria like:\n\n"
        "<code>BMW X5 diesel <25000 2016+ <180000km automatic</code>"
    )


@router.message(Command("unwatch"))
async def cmd_unwatch(message: Message):
    """Remove an alert"""
    # TODO: Show list of alerts and handle removal
    await message.answer("Select an alert to remove:")


@router.message(Command("list"))
async def cmd_list_alerts(message: Message):
    """List all active alerts"""
    # TODO: Fetch user alerts from database
    await message.answer("Your active alerts:\n\n(No alerts yet)")
