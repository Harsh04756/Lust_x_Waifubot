from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton as IKB, InlineKeyboardMarkup as IKM
from PIL import Image, ImageDraw, ImageFont
import random
import io
import time
from . import add, deduct, show, sudb, app, gend_watcher
from . import group_user_totals_collection
from words import words

BG_IMAGE_PATH = "Images/tempest.jpg"
DEFAULT_MESSAGE_LIMIT = 30
DEFAULT_MODE_SETTINGS = {
    "words": True
}
group_message_counts = {}
alpha_dict = {}
guess_start_time = {}

async def get_sudo_user_ids():
    sudo_users = await sudb.find({}, {'user_id': 1}).to_list(length=None)
    return [user['user_id'] for user in sudo_users]

async def set_message_limit(client: Client, message):
    sudo_user_ids = await get_sudo_user_ids()
    user_id = message.from_user.id
    if user_id not in sudo_user_ids:
        await message.reply("Only sudo users can set the message limit!")
        return

    try:
        limit = int(message.command[1])
        if limit <= 0:
            await message.reply("Message limit must be a positive integer!")
            return

        group_message_counts[message.chat.id] = {'count': 0, 'limit': limit}
        await message.reply(f"Message limit set to {limit}. Now spawning images every {limit} messages!")
    except (IndexError, ValueError):
        await message.reply("Please provide a valid message limit (integer).")

def generate_random_image(word: str) -> io.BytesIO:
    img = Image.open(BG_IMAGE_PATH)
    d = ImageDraw.Draw(img)
    fnt = ImageFont.truetype('Font/font.ttf', 76)
    text_width, text_height = d.textsize(word, font=fnt)
    text_x = (img.width - text_width) / 2
    text_y = (img.height - text_height) / 2
    d.text((text_x, text_y), word, font=fnt, fill=(0, 0, 0))

    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)

    return img_byte_arr

async def handle_guess(client: Client, message):
    if not message.text or not message.from_user:
        return

    message_text = message.text.strip().lower()
    chat_id = message.chat.id
    user_id = message.from_user.id
    user_name = message.from_user.first_name

    if chat_id in alpha_dict:
        correct_word = alpha_dict[chat_id]

        if message_text == correct_word:
            reward_amount = random.randint(20000, 40000)
            alpha_dict.pop(chat_id)

            end_time = time.time()
            time_taken = int(end_time - guess_start_time.pop(chat_id))

            await message.reply(f"{user_name}, you got {reward_amount} 🔖 for completing the word!\n\nTime taken: {time_taken}s")
            await add(user_id, reward_amount)

async def handle_messages(client: Client, message):
    await handle_guess(client, message)
    chat_id = message.chat.id

    if chat_id in group_message_counts:
        group_message_counts[chat_id]['count'] += 1
    else:
        group_message_counts[chat_id] = {'count': 1, 'limit': DEFAULT_MESSAGE_LIMIT}

    if group_message_counts[chat_id]['limit'] and group_message_counts[chat_id]['count'] >= group_message_counts[chat_id]['limit']:
        group_message_counts[chat_id]['count'] = 0

        chat_modes = await group_user_totals_collection.find_one({"chat_id": chat_id})
        if not chat_modes:
            chat_modes = DEFAULT_MODE_SETTINGS.copy()
            await group_user_totals_collection.insert_one(chat_modes)

        if not chat_modes.get('words', True):
            return

        random_word = random.choice(words)
        image_bytes = generate_random_image(random_word)

        alpha_dict[chat_id] = random_word
        guess_start_time[chat_id] = time.time()

        keyboard = [
            [IKB("Join", url="https://t.me/LustXGroups")]
        ]
        reply_markup = IKM(keyboard)

        await client.send_photo(chat_id, photo=image_bytes, caption="Guess the word in the image to win!", reply_markup=reply_markup)

@app.on_message(filters.command("wtime"))
async def on_wtime(client: Client, message):
    await set_message_limit(client, message)

@app.on_message(filters.text, group=gend_watcher)
async def on_message(client: Client, message):
    await handle_messages(client, message)
