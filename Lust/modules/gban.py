import asyncio
from pyrogram import filters
from Lust.utils.gban import add_to_global_ban, remove_from_global_ban, fetch_globally_banned_users, get_all_chats, is_user_globally_banned
import time
from . import sudo_filter, capsify, app
from .watchers import gban_watcher

@app.on_message(filters.command(["gban"]) & sudo_filter)
async def gban_user(client, message):
    if len(message.command) < 2 and not message.reply_to_message:
        await message.reply_text(capsify("Usage: `/gban <reason>`."))
        return

    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        reason = " ".join(message.command[1:]) if len(message.command) > 1 else "No reason provided"
    else:
        try:
            user_id = int(message.command[1])
            reason = " ".join(message.command[2:]) if len(message.command) > 2 else "No reason provided"
        except ValueError:
            await message.reply_text(capsify("Invalid user ID. Please provide a valid user ID."))
            return

    await add_to_global_ban(user_id, reason)
    all_chats = await get_all_chats()
    ban_count = 0

    estimated_duration = len(all_chats) * 0.5
    await message.reply_text(capsify(f"Starting global ban. Estimated time: `{estimated_duration}` seconds."))

    start_time = time.time()

    for chat_id in all_chats:
        try:
            await client.kick_chat_member(chat_id, user_id)
            ban_count += 1
            await asyncio.sleep(0.5)
        except Exception as e:
            print(f"Failed to ban user {user_id} in chat {chat_id}: {e}")

    end_time = time.time()
    duration = end_time - start_time

    await message.reply_text(capsify(f"User `{user_id}` has been globally banned in `{ban_count}` chat(s) in `{duration:.2f}` seconds."))

@app.on_message(filters.command(["ungban"]) & sudo_filter)
async def ungban_user(client, message):
    if len(message.command) < 2 and not message.reply_to_message:
        await message.reply_text(capsify("Usage: `/ungban id`."))
        return

    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
    else:
        try:
            user_id = int(message.command[1])
        except ValueError:
            await message.reply_text(capsify("Invalid user ID. Please provide a valid user ID."))
            return

    await remove_from_global_ban(user_id)
    all_chats = await get_all_chats()
    unban_count = 0

    estimated_duration = len(all_chats) * 0.5
    await message.reply_text(capsify(f"Starting global unban. Estimated time: `{estimated_duration}` seconds."))

    start_time = time.time()

    for chat_id in all_chats:
        try:
            await client.unban_chat_member(chat_id, user_id)
            unban_count += 1
            await asyncio.sleep(0.5)
        except Exception as e:
            print(f"Failed to unban user {user_id} in chat {chat_id}: {e}")

    end_time = time.time()
    duration = end_time - start_time

    await message.reply_text(capsify(f"User `{user_id}` has been globally unbanned in `{unban_count}` chat(s) in `{duration:.2f}` seconds."))

@app.on_message(filters.command(["gbanlist"]) & sudo_filter)
async def gban_list(client, message):
    banned_users = await fetch_globally_banned_users()
    if not banned_users:
        await message.reply_text(capsify("No users are globally banned."))
        return

    response_text = "Globally Banned Users:\n\n"
    for user in banned_users:
        response_text += f"User ID: `{user['user_id']}`, Reason: `{user['reason']}`\n"

    await message.reply_text(capsify(response_text))

@app.on_message(filters.group, group=gban_watcher)
async def check_global_ban(client, message):
    if not message.from_user:
        return  # Skip non-user messages

    user_id = message.from_user.id
    if await is_user_globally_banned(user_id):
        try:
            await client.kick_chat_member(message.chat.id, user_id)
            await message.reply_text(capsify(f"User `{user_id}` is globally banned and has been removed from this chat."))
        except Exception as e:
            print(f"Failed to ban globally banned user {user_id} in chat {message.chat.id}: {e}")