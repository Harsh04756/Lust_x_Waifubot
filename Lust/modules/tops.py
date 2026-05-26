from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton as IKB, InlineKeyboardMarkup as IKM
from Lust import user_collection
from . import app, capsify
from .profile import custom_format_number
from .block import block_dec, temp_block, block_cbq


@app.on_message(filters.command("tops"))
@block_dec
async def show_top_exlix(client, message):
    user_id = message.from_user.id
    if temp_block(user_id):
        return

    buttons = [
        [IKB(capsify("💰 Exlix Top"), callback_data="top_exlix")]
    ]
    reply_markup = IKM(buttons)

    await message.reply_text(
        capsify("🏆 Exlix Leaderboard 🏆"),
        reply_markup=reply_markup
    )


@app.on_callback_query(filters.regex(r"^top_exlix$"))
@block_cbq
async def show_exlix_list(client, callback_query):

    users = await user_collection.find(
        {},
        {'id': 1, 'balance': 1, 'first_name': 1}
    ).to_list(length=None)

    users_with_balance = [u for u in users if 'balance' in u]

    sorted_users = sorted(
        users_with_balance,
        key=lambda x: float(x['balance'].replace(',', '')) if isinstance(x['balance'], str) else x['balance'],
        reverse=True
    )[:10]

    text = f"{capsify('🏆 Top 10 Users by Exlix 🏆')}\n\n"

    for index, user in enumerate(sorted_users):
        balance = user['balance']
        value = custom_format_number(
            float(balance.replace(',', '')) if isinstance(balance, str) else balance
        )

        first_name = user.get('first_name', 'Unknown')
        first_word = first_name.split()[0]

        text += f"{index + 1}. {first_word} - 💰 {value} Exlix\n"

    buttons = [
        [IKB(capsify("🔙 Back"), callback_data="back_to_exlix_menu")]
    ]
    reply_markup = IKM(buttons)

    await callback_query.message.edit_text(text, reply_markup=reply_markup)


@app.on_callback_query(filters.regex(r"^back_to_exlix_menu$"))
@block_cbq
async def back_to_exlix_menu(client, callback_query):

    buttons = [
        [IKB(capsify("💰 Exlix Top"), callback_data="top_exlix")]
    ]
    reply_markup = IKM(buttons)

    await callback_query.message.edit_text(
        capsify("🏆 Exlix Leaderboard 🏆"),
        reply_markup=reply_markup
    )
