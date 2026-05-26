from pyrogram import filters, types as t
import random
import time
import asyncio
from pyrogram import Client
from Lust import user_collection
from . import add, deduct, show, app
from .block import block_dec, temp_block

cooldown_duration_roll = 600
last_usage_time_roll = {}

@app.on_message(filters.command(["lever"]))
@block_dec
async def roll_dart(client: Client, message: t.Message):
    user_id = message.from_user.id
    if temp_block(user_id):
        return
    current_time = time.time()

    if not await user_collection.find_one({'id': user_id}):
        await message.reply("You need to grab some slave first.")
        return

    command_parts = message.text.split()
    if len(command_parts) != 2:
        return await message.reply_text("Invalid command.\nUsage: /lever 99999")

    try:
        slot_amount = int(command_parts[1])
    except ValueError:
        return await message.reply_text("Invalid amount.")

    bal = await show(user_id)
    if bal is None:
        return await message.reply_text("You don't have enough cash to place this bet.")

    if slot_amount > bal:
        return await message.reply_text("Insufficient cash to place this bet.")

    min_bet_amount = int(bal * 0.07)

    if slot_amount < min_bet_amount:
        return await message.reply_text(f"Please bet at least 7% of your balance, which is {min_bet_amount} Exlix.")

    max_bet_amount = int(bal * 0.4)
    if slot_amount > max_bet_amount:
        return await message.reply_text(f"Can't bet more than 40% of your balance, which is {max_bet_amount} Exlix.")

    if user_id in last_usage_time_roll:
        time_elapsed = current_time - last_usage_time_roll[user_id]
        remaining_time = max(0, cooldown_duration_roll - time_elapsed)
        if remaining_time > 0:
            return await message.reply_text(f"You're on cooldown. Please wait {int(remaining_time)} seconds.")

    last_usage_time_roll[user_id] = current_time

    value = await client.send_dice(chat_id=message.chat.id, emoji="🎰")
    await asyncio.sleep(random.uniform(1, 5))
    slot_value = value.dice.value

    jackpot_multiplier = 2
    two_equal_multiplier = 1

    # Adjust winning conditions
    if slot_value == 1:  # Only 1 is a jackpot now
        reward = jackpot_multiplier * slot_amount
        await add(user_id, reward)
        await message.reply_text(f"[🎰](https://files.catbox.moe/m19qnp.jpg) You hit the jackpot!\nYou won {reward} Exlix!")
        await add_xp(user_id, 6)
    elif slot_value == 2:  # Only 2 is a two-equal win
        reward = two_equal_multiplier * slot_amount
        await add(user_id, reward)
        await message.reply_text(f"[🎰](https://files.catbox.moe/m19qnp.jpg) Two signs came out equal!\nYou won {reward} Exlix!")
        await add_xp(user_id, 4)
    else:
        await deduct(user_id, slot_amount)
        await message.reply_text(f"[🍷](https://files.catbox.moe/vekcyg.jpg) Nothing got matched!\nYou lost {slot_amount} Exlix.")
        await deduct_xp(user_id, 2)

async def add_xp(user_id, xp_amount):
    await user_collection.update_one({'id': user_id}, {'$inc': {'xp': xp_amount}}, upsert=True)

async def deduct_xp(user_id, xp_amount):
    await user_collection.update_one({'id': user_id}, {'$inc': {'xp': -xp_amount}}, upsert=True)
