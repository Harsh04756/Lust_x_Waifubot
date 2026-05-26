from . import db, app, sudo_filter
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from pyrogram import Client, filters
import time
from . import capsify
from .watchers import block_watcher

dic1 = {}
dic2 = {}
t_block = {}
bdb = db.block

def temp_block(user_id):
    if user_id in t_block:
        if int(time.time() - t_block[user_id]) > 600:
            t_block.pop(user_id)
    return user_id in t_block

@app.on_message(filters.group, group=block_watcher)
async def block_cwf(_, m: Message):
    if m.from_user is None:
        return

    user_id = m.from_user.id

    if user_id in t_block:
        if time.time() - t_block[user_id] < 600:
            return
        t_block.pop(user_id)

    current_time = time.time()

    if user_id in dic1:
        if current_time - dic1[user_id] <= 1:
            dic2[user_id] = dic2.get(user_id, 0) + 1
            if dic2[user_id] >= 4:
                t_block[user_id] = current_time
                dic2[user_id] = 0
                txt = capsify("You have been blocked for 10 minutes due to flooding ⚠️")
                await m.reply(txt)
        else:
            dic2[user_id] = 0
    else:
        dic2[user_id] = 0

    dic1[user_id] = current_time

async def block(user_id):
    await bdb.insert_one({'user_id': user_id})

async def is_blocked(user_id) -> bool:
    x = await bdb.find_one({'user_id': user_id})
    return bool(x)

async def unblock(user_id):
    await bdb.delete_one({'user_id': user_id})

async def save_block_reason(user_id: int, reason: str):
    await bdb.update_one(
        {'user_id': user_id},
        {'$set': {'reason': reason}},
        upsert=True
    )
async def get_block_reason(user_id):
    result = await bdb.find_one(
        {'user_id': user_id},
        {'reason': 1}
    )
    return result.get('reason') if result else None

@app.on_message(filters.command("block") & sudo_filter)
async def block_command(client, message: Message):
    if message.reply_to_message:
        target_id = message.reply_to_message.from_user.id
    else:
        try:
            target_id = int(message.text.split()[1])
        except:
            return await message.reply(capsify("Either reply to a user or provide an ID."))

    reason = None
    if "-r" in message.text:
        reason_start_index = message.text.index("-r") + 3
        reason = message.text[reason_start_index:].strip()

    if await is_blocked(target_id):
        return await message.reply(capsify("User is already blocked."))

    await block(target_id)

    if reason:
        await save_block_reason(target_id, reason)

    await message.reply(capsify(f"User blocked permanently.\n Reason: {reason}" if reason else "User blocked permanently."))

@app.on_message(filters.command("unblock") & sudo_filter)
async def unblock_command(client, message: Message):
    if message.reply_to_message:
        target_id = message.reply_to_message.from_user.id
    else:
        try:
            target_id = int(message.text.split()[1])
        except:
            return await message.reply(capsify("Either reply to a user or provide an ID."))

    if not await is_blocked(target_id):
        return await message.reply(capsify("User was not blocked."))

    await unblock(target_id)
    await message.reply(capsify("User unblocked."))

block_dic = {}

def block_dec(func):
    async def wrapper(client, message: Message):
        user_id = message.from_user.id
        if await is_blocked(user_id) or user_id in block_dic:
            reason = await get_block_reason(user_id)
            if reason:
                return await message.reply(capsify(f"You have been blocked from using me.\n Reason: {reason}"))
            else:
                return await message.reply(capsify("You have been blocked from using me.\n Reason: Not specified."))
        return await func(client, message)
    return wrapper



def block_cbq(func):
    async def wrapper(client, callback_query: CallbackQuery):
        user_id = callback_query.from_user.id
        if await is_blocked(user_id) or user_id in block_dic:
            reason = await get_block_reason(user_id)
            if reason:
                return await callback_query.answer(capsify(f"You have been blocked from using me.\n Reason: {reason}"), show_alert=True)
            else:
                return await callback_query.answer(capsify("You have been blocked from using me.\n Reason: Not specified."), show_alert=True)
        return await func(client, callback_query)
    return wrapper

async def get_all_blocked_users():
    blocked_users = await db.block.find().to_list(None)
    return [user['user_id'] for user in blocked_users]

@app.on_message(filters.command("blocklist") & sudo_filter)
async def blocklist_command(client: Client, message: Message):
    blocked_users = await db.block.find().to_list(None)
    if not blocked_users:
        return await message.reply(capsify("No users are currently blocked."))

    user_list = "\n".join(
        [
            f"- User ID: {user['user_id']} (Reason: {user.get('reason', 'Not specified')})"
            for user in blocked_users
        ]
    )
    text = capsify(f"Blocked Users:\n{user_list}")
    await message.reply(
        text,
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("Close", callback_data="close_blocklist")]]
        )
    )

@app.on_callback_query(filters.regex("close_blocklist") & sudo_filter)
async def close_callback(client: Client, callback_query: CallbackQuery):
    command_user_id = callback_query.message.reply_to_message.from_user.id
    caller_user_id = callback_query.from_user.id

    if command_user_id != caller_user_id:
        reason = await get_block_reason(caller_user_id)
        reason_text = f"Reason: {reason}" if reason else "Reason: Not specified."
        await callback_query.answer(
            capsify(f"Who are you to tell me what to do?\n{reason_text}"), 
            show_alert=True
        )
        return

    await callback_query.message.delete()
    await callback_query.answer(capsify("Closed"), show_alert=False)

from telegram import Update
from telegram.ext import CallbackContext

def block_dec_ptb(func):
    async def wrapper(update: Update, context: CallbackContext):
        user_id = update.effective_user.id if update.effective_user else None
        if user_id and (await is_blocked(user_id) or user_id in block_dic):
            return
        return await func(update, context)
    return wrapper

def block_cbq_ptb(func):
    async def wrapper(update: Update, context: CallbackContext):
        user_id = update.effective_user.id if update.effective_user else None
        if user_id and (await is_blocked(user_id) or user_id in block_dic):
            reason = await get_block_reason(user_id)
            reason_text = f"Reason: {reason}" if reason else "Reason: Not specified."
            await update.callback_query.answer(
                capsify(f"You have been blocked.\n{reason_text}"), 
                show_alert=True
            )
            return
        return await func(update, context)
    return wrapper

def block_inl_ptb(func):
    async def wrapper(update: Update, context: CallbackContext):
        user_id = update.effective_user.id if update.effective_user else None
        if user_id and (await is_blocked(user_id) or user_id in block_dic):
            reason = await get_block_reason(user_id)
            reason_text = f"Reason: {reason}" if reason else "Reason: Not specified."
            await update.inline_query.answer(capsify(f"You have been blocked.\n{reason_text}"))
            return
        return await func(update, context)
    return wrapper