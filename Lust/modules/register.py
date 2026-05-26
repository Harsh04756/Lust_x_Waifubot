import random
import string
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton as IKB, InlineKeyboardMarkup as IKM
from . import user_collection, capsify, app

async def generate_unique_password(user_id):
    while True:
        password = f"{user_id}_" + ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        existing_user = await user_collection.find_one({'password': password})  # Use await here
        if not existing_user:
            return password

@app.on_message(filters.command("register") & filters.group)
async def register_group(client, message):
    user_id = message.from_user.id
    keyboard = [[IKB(capsify("DM Me"), url=f"https://t.me/{client.me.username}")]]
    await message.reply_text(
        capsify("For security reasons, please use this command in a direct message (DM) with me."),
        reply_markup=IKM(keyboard)
    )

@app.on_message(filters.command("register") & filters.private)
async def register_private(client, message):
    user_id = message.from_user.id
    user = await user_collection.find_one({'id': user_id})

    if user and 'password' in user:
        await message.reply_text(capsify("You already have a password."))
        return

    password = await generate_unique_password(user_id)  # Await the async function
    await user_collection.update_one(
        {'id': user_id},
        {'$set': {'password': password}},
        upsert=True
    )

    await message.reply_text(
        capsify(f"Your unique password is: {password}\n\nPlease store it carefully, as you won't get it again!")
    )