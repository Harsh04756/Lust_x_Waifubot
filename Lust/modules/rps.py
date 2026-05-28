from telegram.ext import CommandHandler, CallbackQueryHandler
from Lust import application, user_collection
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import random
from . import add as add_balance, deduct as deduct_balance, show as show_balance
from .block import block_dec_ptb, temp_block

@block_dec_ptb
async def rps(update, context):
    try:
        amount = int(context.args[0])
        if amount < 1:
            raise ValueError("Invalid bet amount.")
    except (IndexError, ValueError):
        await update.message.reply_text("Use /rps [amount]")
        return

    user_id = update.effective_user.id
    if temp_block(user_id):
        return

    user_balance = await show_balance(user_id)


    if user_balance is None:
        await update.message.reply_text("You don't have any Exlix balance yet!")
        return

    if user_balance < amount:
        await update.message.reply_text("Insufficient balance to make the bet.")
        return

    keyboard = [
        [InlineKeyboardButton("Rock 🪨", callback_data='rock'),
         InlineKeyboardButton("Paper 📄", callback_data='paper')],
        [InlineKeyboardButton("Scissors ✂️", callback_data='scissors')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    message = await update.message.reply_text("Choose your move:", reply_markup=reply_markup)

    context.user_data['amount'] = amount
    context.user_data['message_id'] = message.message_id

async def rps_button(update, context):
    query = update.callback_query
    choice = query.data

    if choice == 'play_again':
        await play_again(update, context)
        return

    amount = context.user_data.get('amount')
    user_id = update.effective_user.id
    user_balance = await show_balance(user_id)

    # FIX: None check
    if user_balance is None or amount is None or user_balance < amount:
        await query.answer("Insufficient balance to make the bet.", show_alert=True)
        return

    computer_choice = random.choice(['rock', 'paper', 'scissors'])

    if choice == computer_choice:
        result_message = "It's a tie!"
    elif (choice == 'rock' and computer_choice == 'scissors') or \
         (choice == 'paper' and computer_choice == 'rock') or \
         (choice == 'scissors' and computer_choice == 'paper'):
        result_message = "🎉 You won!"
        await add_balance(user_id, amount)
    else:
        result_message = "😔 You lost!"
        await deduct_balance(user_id, amount)

    updated_balance = await show_balance(user_id)

    await query.message.edit_text(
        f"You chose {choice.capitalize()} and the computer chose {computer_choice.capitalize()}\n\n"
        f"{result_message} Your updated balance is {updated_balance} Exlix\n\nPlay again?",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Play Again 🔄", callback_data='play_again')]])
    )

async def play_again(update, context):
    query = update.callback_query
    keyboard = [
        [InlineKeyboardButton("Rock 🪨", callback_data='rock'),
         InlineKeyboardButton("Paper 📄", callback_data='paper')],
        [InlineKeyboardButton("Scissors ✂️", callback_data='scissors')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.edit_text("Choose your move:", reply_markup=reply_markup)

application.add_handler(CommandHandler("rps", rps))
application.add_handler(CallbackQueryHandler(rps_button, pattern='^(rock|paper|scissors|play_again)$'))
        
