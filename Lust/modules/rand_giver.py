from pyrogram import Client, filters
from pyrogram.types import Message
from random import choices
from . import db, collection, user_collection, app, dev_filter

# Rarity weights for the 1-9 system
rarity_percentages = {
    "⚪ Common":    55,   # 1
    "☘️ Medium":   22,   # 2
    "🔴 Rare":     12,   # 3
    "🟡 Legendary": 6,   # 4
    "💋 Nude":      2,   # 5
    "🔮 Limited":   1,   # 6
    "🐦‍🔥 Exotic":  1,   # 7
    "🎐 Devine":    0,   # 8 — not given via rand giver
    "💦 Wet":       1,   # 9
}

@app.on_message(filters.command("giver") & dev_filter)
async def giverandom(client: Client, message: Message):
    try:
        args = message.text.split()[1:]
        if len(args) != 2:
            await message.reply_text('Please provide a valid user ID and the number of slaves to give.')
            return

        try:
            receiver_id = int(args[0])
            slave_count = int(args[1])
        except ValueError:
            await message.reply_text('Invalid user ID or slave count provided.')
            return

        receiver = await user_collection.find_one({'id': receiver_id})
        if not receiver:
            await message.reply_text(f'Receiver with ID {receiver_id} not found.')
            return

        all_slaves = await collection.find({}).to_list(None)
        valid_slaves = [slave for slave in all_slaves if 'rarity' in slave and rarity_percentages.get(slave['rarity'], 0) > 0]
        slave_weights = [rarity_percentages.get(slave['rarity'], 0) for slave in valid_slaves]
        random_slaves = choices(valid_slaves, weights=slave_weights, k=slave_count)

        receiver_slaves = receiver.get('characters', [])
        receiver_slaves.extend(random_slaves)

        await user_collection.update_one({'id': receiver_id}, {'$set': {'characters': receiver_slaves}})

        await message.reply_text(f'Successfully gave {slave_count} random slaves to user {receiver_id}!')

    except Exception as e:
        await message.reply_text(f'An error occurred: {e}')
