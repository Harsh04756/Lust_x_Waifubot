import pytz
import datetime
from pyrogram import Client, filters
from pyrogram.types import Message
from . import collection, user_collection, sudo_filter, app, capsify
from .block import block_dec, temp_block

async def exchange_command(client: Client, message: Message, args: list[str]) -> None:
    user_id = message.from_user.id
    if temp_block(user_id):
        return
    tz = pytz.timezone('Asia/Kolkata')
    now = datetime.datetime.now(tz)

    if now.weekday() != 5:
        await message.reply_text(capsify("The /exchange command is only available on Saturdays."))
        return

    start_time = tz.localize(datetime.datetime.combine(now.date(), datetime.time(5, 30)))
    end_time = tz.localize(datetime.datetime.combine(now.date(), datetime.time(0, 30))) + datetime.timedelta(days=1)

    if not (start_time <= now <= end_time):
        await message.reply_text(capsify("The /exchange command is only available between 5:30 am and 12:30 midnight on Saturdays."))
        return

    user_data = await user_collection.find_one({'id': user_id})
    if not user_data:
        await user_collection.insert_one({
            'id': user_id,
            'exchange_count': 0,
            'last_exchange': datetime.datetime.combine(now.date(), datetime.time.min, tz)
        })
        exchange_count = 0
    else:
        exchange_count = user_data.get('exchange_count', 0)
        last_exchange = user_data.get('last_exchange', None)
        if last_exchange is None or last_exchange.date() != now.date():
            # Reset exchange count and update the last_exchange date for a new day
            exchange_count = 0
            await user_collection.update_one(
                {'id': user_id},
                {
                    '$set': {
                        'exchange_count': 0,
                        'last_exchange': datetime.datetime.combine(now.date(), datetime.time.min, tz)
                    }
                }
            )

    if exchange_count >= 3:
        await message.reply_text(capsify("You have reached the limit of 3 exchanges."))
        return

    if len(args) != 2:
        await message.reply_text(capsify("Usage: /exchange <your_character_id> <desired_character_id>"))
        return

    your_character_id = args[0]
    desired_character_id = args[1]

    if not user_data or 'characters' not in user_data:
        await message.reply_text(capsify("You don't have any characters to exchange."))
        return

    user_characters = user_data['characters']
    character_to_exchange = next((char for char in user_characters if char['id'] == your_character_id), None)

    if not character_to_exchange:
        await message.reply_text(capsify("You don't own the specified character."))
        return

    desired_character = await collection.find_one({'id': desired_character_id})
    if not desired_character:
        await message.reply_text(capsify("Desired character not found. Please provide a valid character ID."))
        return

    if desired_character.get('rarity') in ['💋 Aura', '❄️ Winter']:
        await message.reply_text(capsify("You cannot exchange for a character with 💋 Aura or ❄️ Winter rarity."))
        return

    index_to_remove = next((i for i, char in enumerate(user_characters) if char['id'] == your_character_id), None)

    if index_to_remove is None:
        await message.reply_text(capsify("An error occurred while processing the exchange."))
        return

    new_characters = user_characters[:index_to_remove] + user_characters[index_to_remove + 1:]

    await user_collection.update_one(
        {'id': user_id},
        {'$set': {'characters': new_characters}}
    )

    await user_collection.update_one(
        {'id': user_id},
        {'$push': {'characters': desired_character}}
    )

    updated_exchange_count = exchange_count + 1
    remaining_exchanges = 3 - updated_exchange_count

    # Update exchange count and last_exchange
    await user_collection.update_one(
        {'id': user_id},
        {'$set': {'exchange_count': updated_exchange_count, 'last_exchange': now}}
    )

    await message.reply_text(capsify(f"Exchange successful! You exchanged {your_character_id} for {desired_character['name']}."))
    await message.reply_text(capsify(f"You have {remaining_exchanges} exchanges remaining."))

@app.on_message(filters.command("exchange"))
@block_dec
async def handle_exchange_command(client: Client, message: Message):
    args = message.text.split()[1:]
    await exchange_command(client, message, args)

@app.on_message(filters.command("ce") & sudo_filter)
async def handle_reset_exchange_counts(client: Client, message: Message):
    await user_collection.update_many({}, {'$set': {'exchange_count': 0, 'last_exchange': None}})
    await message.reply_text(capsify("All users' exchange counts have been reset."))