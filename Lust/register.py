from functools import wraps
from telegram import Update
from telegram.ext import CallbackContext
from telegram.error import Unauthorized
from Lust import user_collection, app
from functools import wraps
from pyrogram.errors import Forbidden
from . import capsify

def start_ptb(func):
    @wraps(func)
    async def wrapper(update: Update, context: CallbackContext, *args, **kwargs):
        user = update.effective_user
        if not user:
            return
        
        user_id = user.id
        user_data = await user_collection.find_one({"id": user_id})

        if not user_data:
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=capsify("❌ PLEASE START THE BOT FIRST BY USING /START.")
                )
            except Unauthorized:
                await update.message.reply_text(
                    capsify("❌ PLEASE START THE BOT IN YOUR DM FIRST.")
                )
            return
        return await func(update, context, *args, **kwargs)
    return wrapper


def start(func):
    @wraps(func)
    async def wrapper(client, message, *args, **kwargs):
        user_id = message.from_user.id
        user = await user_collection.find_one({"id": user_id})
        if not user:
            try:
                await client.send_message(
                    chat_id=user_id,
                    text=capsify("❌ PLEASE START THE BOT FIRST BY USING /START.")
                )
            except Forbidden:
                await message.reply_text(capsify("❌ PLEASE START THE BOT IN YOUR DM FIRST."))
            return
        return await func(client, message, *args, **kwargs)
    return wrapper
