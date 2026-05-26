import random
from pyrogram import Client, filters
from Lust import user_collection
from . import add, deduct, show, abank, dbank, sbank, app, capsify
from .block import block_dec, temp_block

@app.on_message(filters.command("gamble"))
@block_dec
async def gamble(client, message):
    user_id = message.from_user.id
    if temp_block(user_id):
        return
    user = await user_collection.find_one({'id': user_id})
    balance = int(user.get('balance', 0))

    args = message.text.split()[1:]
    if len(args) != 2:
        await message.reply_text(capsify("Usage: /gamble <amount> <l/r>"))
        return

    try:
        amount = int(args[0])
        choice = args[1].lower()
    except ValueError:
        await message.reply_text(capsify("Invalid amount."))
        return

    if choice not in ['l', 'r']:
        await message.reply_text(capsify("Invalid choice. Please use /gamble l/r."))
        return

    min_bet = int(balance * 0.07)
    if amount < min_bet:
        await message.reply_text(capsify(f"Please gamble at least 7% of your balance, which is {min_bet} Exlix."))
        return

    if amount > balance:
        await message.reply_text(capsify(f"You do not have enough balance to gamble {amount} Exlix. Your current balance is {balance} Exlix."))
        return

    # Winning chance is now 10 out of 100
    if random.randint(1, 100) <= 10:  # 10% chance to win
        coin_side = choice
        new_balance = amount  # Amount to add
        message_text = capsify(f"🤩 You chose {choice} and won {amount} Exlix.\nCoin was in {coin_side} hand.")
    else:
        coin_side = 'l' if choice == 'r' else 'r'
        new_balance = -amount  # Amount to deduct
        message_text = capsify(f"🥲 You chose {choice} and lost {amount} Exlix.\nCoin was in {coin_side} hand.")

    await add(user_id, new_balance)

    photo_url = "https://telegra.ph/file/889fb66c41a9ead354c59.jpg" if coin_side == choice else "https://telegra.ph/file/99a98f60b22759857056a.jpg"
    await message.reply_photo(photo=photo_url, caption=message_text)
