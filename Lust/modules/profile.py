import math
import os
import aiohttp
import aiofiles
from pyrogram import Client, filters
from datetime import datetime
import pytz
from . import user_collection, collection, app, capsify
from .block import block_dec, temp_block

def custom_format_number(num):
    if int(num) >= 10**6:
        exponent = int(math.log10(num)) - 5
        base = num // (10 ** exponent)
        return f"{base:,.0f}({exponent:+})"
    return f"{num:,.0f}"

def parse_amount(amount_str):
    if "+" in amount_str:
        base_str, exponent_str = amount_str.split("+")
        base = int(base_str.replace(",", ""))
        exponent = int(exponent_str)
        return base * (10 ** exponent)
    return int(amount_str.replace(",", ""))

async def download_image(url, file_path):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                async with aiofiles.open(file_path, 'wb') as f:
                    await f.write(await response.read())

def calculate_days_old(created_at):
    now = datetime.now(pytz.timezone('Asia/Kolkata'))
    days_old = (now - created_at).days
    return days_old

@app.on_message(filters.command('profile'))
@block_dec
async def xprofile(client, message):
    user_id = message.from_user.id
    if temp_block(user_id):
        return

    try:
        user_data = await user_collection.find_one(
            {'id': user_id},
            projection={'balance': 1, 'saved_amount': 1, 'characters': 1, 'gender': 1, 'profile_media': 1, 'created_at': 1}
        )

        if user_data:
            balance_amount = int(user_data.get('balance', 0))
            bank_balance = int(user_data.get('saved_amount', 0))
            characters = user_data.get('characters', [])
            gender = user_data.get('gender')
            profile_media = user_data.get('profile_media')
            created_at = user_data.get('created_at')

            if created_at:
                created_at = created_at.replace(tzinfo=pytz.timezone('Asia/Kolkata'))
                days_old = calculate_days_old(created_at)
            else:
                days_old = "N/A"

            total_characters = len(characters)
            all_characters = await collection.find({}).to_list(length=None)
            total_database_characters = len(all_characters)

            gender_icon = '👦🏻' if gender == 'male' else '👧🏻' if gender == 'female' else '👶🏻'

            balance_message = capsify(
                f"PROFILE\n\n"
                f"Name: {message.from_user.first_name or ''} {message.from_user.last_name or ''} [{gender_icon}]\n"
                f"ID: `{user_id}`\n\n"
                f"Exlix: `{custom_format_number(balance_amount)}`\n"
                f"Bank: `{custom_format_number(bank_balance)}` Exlix\n"
                f"Characters: `{total_characters}/{total_database_characters}`\n"
                f"Days Old: `{days_old}`\n"
            )

            if profile_media:
                temp_file_path = "temp_profile_image.jpg"
                await download_image(profile_media, temp_file_path)

                await message.reply_photo(
                    photo=temp_file_path,
                    caption=balance_message
                )

                os.remove(temp_file_path)
            else:
                await message.reply_text(balance_message)

        else:
            await message.reply_text(capsify("Claim bonus first using /claim"))

    except Exception as e:
        await message.reply_text(capsify(f"An error occurred: {e}"))
