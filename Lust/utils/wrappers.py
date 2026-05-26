from pyrogram import Client, filters
from pyrogram.types import Message
from functools import wraps
from .capsify import capsify 
from Lust import user_collection, db

sudb = db.sudo
devb = db.dev

def sudocmd(func):
    @wraps(func)
    async def wrapper(client: Client, message: Message):
        user_id = message.from_user.id
        sudo_user = await sudb.find_one({"user_id": user_id})
        if not sudo_user:
            return
        return await func(client, message)
    return wrapper

from telegram import Update
from telegram.ext import CallbackContext

def devcmd(func):
    @wraps(func)
    async def wrapper(update: Update, context: CallbackContext):
        user_id = update.effective_user.id
        dev_user = await devb.find_one({"user_id": user_id})  
        if not dev_user:
            await context.bot.send_message(chat_id=update.effective_chat.id, text="You are not authorized to use this command.")
            return
        return await func(update, context)
    return wrapper

def nopvt(func):
    @wraps(func)
    async def wrapper(client: Client, message: Message):
        if message.chat.type == 'private':
            await message.reply_text("This command cannot be used in private messages.")
            return
        return await func(client, message)
    return wrapper

async def get_chat_id(message: Message):
    return message.chat.id

def limit(func):
    @wraps(func)
    async def wrapper(client: Client, message: Message):
        current_chat_id = message.chat.id
        allowed_chat_id = -1002413377777

        if current_chat_id != allowed_chat_id:
            await message.reply_text("This command only works in @dragona_support.")
            return

        return await func(client, message)

    return wrapper


