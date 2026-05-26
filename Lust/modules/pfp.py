import os
import requests
from pyrogram import Client, filters
from pyrogram.types import Message
from . import user_collection, app
from .block import block_dec, temp_block

CATBOX_API_URL = "https://catbox.moe/user/api.php"

def upload_to_catbox(file_path):
    with open(file_path, 'rb') as file:
        files = {'fileToUpload': file}
        data = {'reqtype': 'fileupload'}
        response = requests.post(CATBOX_API_URL, files=files, data=data)

    response_text = response.text.strip()

    if response.status_code == 200 and response_text.startswith('https://'):
        return response_text
    else:
        raise Exception(f"Catbox upload failed: {response_text}")

@app.on_message(filters.command("setpfp"))
@block_dec
async def set_profile_media(client: Client, message: Message):
    user_id = message.from_user.id
    if temp_block(user_id):
        return
    reply_message = message.reply_to_message

    if not reply_message or not reply_message.photo:
        await message.reply_text("**Please reply to a photo to set it as your profile media.**")
        return

    photo = reply_message.photo
    photo_path = await client.download_media(photo.file_id)

    try:
        img_url = upload_to_catbox(photo_path)
        await user_collection.update_one({'id': user_id}, {'$set': {'profile_media': img_url}})
        await message.reply_text("**Profile media has been set!**")
    except Exception as e:
        await message.reply_text(f"Failed to upload image to Catbox: {e}")
    finally:
        if os.path.exists(photo_path):
            os.remove(photo_path)

@app.on_message(filters.command("delpfp"))
@block_dec
async def delete_profile_media(client: Client, message: Message):
    user_id = message.from_user.id
    user_data = await user_collection.find_one({'id': user_id})

    if not user_data or 'profile_media' not in user_data:
        await message.reply_text("No profile media found to delete.")
        return

    await user_collection.update_one({'id': user_id}, {'$unset': {'profile_media': ""}})
    await message.reply_text("**Profile media has been deleted.**")