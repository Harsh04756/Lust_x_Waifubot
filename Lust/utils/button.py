from typing import Optional
from telegram import Update
from telegram.ext import CallbackContext
last_characters = {}
from Lust import user_collection



async def show(user_id):
    user = await user_collection.find_one({"id": user_id})
    if user:
        return int(user.get("balance", 0))
    return 0

async def add(user_id, balance):
    x = await user_collection.find_one({'id': user_id})
    if not x:
        return
    x['balance'] = str(int(x.get('balance', 0)) + balance)
    x.pop('_id')
    await user_collection.update_one({'id': user_id}, {'$set': x}, upsert=True)

async def deduct(user_id, balance):
    x = await user_collection.find_one({'id': user_id})
    if not x:
        return
    x['balance'] = str(int(x.get('balance')) - balance)
    x.pop('_id')
    await user_collection.update_one({'id': user_id}, {'$set': x}, upsert=True)


async def button_click(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    chat_id = query.message.chat_id

    user_balance = await show(user_id)

    if user_balance is not None:
        if user_balance >= 10000:
            await deduct(user_id, 10000)
            name = last_characters.get(chat_id, {}).get('name', 'Unknown')
            await query.answer(text=f"ᴛʜᴇ  ɴᴀᴍᴇ ɪs: {name}", show_alert=True)
        else:
            await query.answer(text="ʏᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ sᴜғғɪᴄɪᴇɴᴛ ʙᴀʟᴀɴᴄᴇ.", show_alert=True)
    else:
        await add(user_id, 50000)
        name = last_characters.get(chat_id, {}).get('name', 'Unknown')
        await query.answer(text=f"ᴡᴇʟᴄᴏᴍᴇ, ᴜsᴇʀ ! ʏᴏᴜ'ᴠᴇ ʙᴇᴇɴ ᴀᴅᴅᴇᴅ ᴛᴏ ᴏᴜʀ sʏsᴛᴇᴍ ᴡɪᴛʜ ᴀɴ ɪɴɪᴛɪᴀʟ ʙᴀʟᴀɴᴄᴇ ᴏғ 50ᴋ", show_alert=True)
