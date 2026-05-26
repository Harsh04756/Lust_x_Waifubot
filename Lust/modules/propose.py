import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
import random
from datetime import datetime, timedelta
from Lust import collection, user_collection, user_totals_collection
from . import add as add_balance, deduct as deduct_balance, app, capsify
from .block import block_dec, temp_block

# Updated rarity map for new system — False means cannot be proposed
rarity_map = {
    "⚪ Common":    True,
    "☘️ Medium":   True,
    "🔴 Rare":     True,
    "🟡 Legendary": True,
    "💋 Nude":     False,
    "🔮 Limited":  False,
    "🐦‍🔥 Exotic": False,
    "🎐 Devine":   False,
    "💦 Wet":      False,
}

last_propose_times = {}
proposing_users = {}

@app.on_message(filters.command("propose"))
@block_dec
async def propose(client, message: Message):
    user_id = message.from_user.id
    if temp_block(user_id):
        return

    user_data = await user_collection.find_one({'id': user_id})

    if not user_data or int(user_data.get('balance', 0)) < 10:
        await message.reply_text(capsify("You need at least 10 Exlix to propose."))
        proposing_users[user_id] = False
        return

    if proposing_users.get(user_id):
        await message.reply_text(capsify("You are already proposing. Please wait for the current proposal to finish."))
        proposing_users[user_id] = False
        return
    else:
        proposing_users[user_id] = True

    last_propose_time = last_propose_times.get(user_id)
    if last_propose_time:
        time_since_last_propose = datetime.now() - last_propose_time
        if time_since_last_propose < timedelta(minutes=5):
            remaining_cooldown = timedelta(minutes=5) - time_since_last_propose
            remaining_cooldown_minutes = remaining_cooldown.total_seconds() // 60
            remaining_cooldown_seconds = remaining_cooldown.total_seconds() % 60
            await message.reply_text(capsify(f"Cooldown! Please wait {int(remaining_cooldown_minutes)}m {int(remaining_cooldown_seconds)}s before proposing again."))
            proposing_users[user_id] = False
            return

    await deduct_balance(user_id, 10)

    proposal_message = capsify("✨ Time to Propose ✨")
    photo_path = 'https://telegra.ph/file/68491359070e2e045c919.jpg'
    await message.reply_photo(photo=photo_path, caption=proposal_message)

    await asyncio.sleep(2)

    await message.reply_text(capsify("Asking for Her Hand 💍"))

    await asyncio.sleep(2)

    if random.random() < 0.6:
        rejection_message = capsify("She pushed you away and screamed 😂")
        rejection_photo_path = 'https://graph.org/file/43ac16b34453bafe480d9.jpg'
        await message.reply_photo(photo=rejection_photo_path, caption=rejection_message)
    else:
        all_characters = list(await collection.find({}).to_list(length=None))
        valid_characters = [char for char in all_characters if char.get('rarity') in rarity_map.keys()]

        if not valid_characters:
            await message.reply_text(capsify("No characters available with the specified rarity."))
            return

        character = random.choice(valid_characters)
        await user_collection.update_one({'id': user_id}, {'$push': {'characters': character}})
        await message.reply_photo(photo=character['img_url'], caption=capsify(f"{character['name']} accepted your proposal!"))

    last_propose_times[user_id] = datetime.now()
    proposing_users[user_id] = False
