from pyrogram import filters
from pyrogram.types import Message
from pyrogram.errors import RPCError
from datetime import datetime
import asyncio

from . import app, db
from .block import block_dec

# Initialize collection for warns
warn_collection = db.warns

async def get_warn_count(chat_id: int, user_id: int):
    warn_data = await warn_collection.find_one({"chat_id": chat_id, "user_id": user_id})
    return warn_data["count"] if warn_data else 0

async def add_warn(chat_id: int, user_id: int, reason: str = "No reason"):
    current_warns = await get_warn_count(chat_id, user_id)
    new_count = current_warns + 1
    await warn_collection.update_one(
        {"chat_id": chat_id, "user_id": user_id},
        {"$set": {"chat_id": chat_id, "user_id": user_id, "count": new_count, "last_warned": datetime.now(), "reason": reason}},
        upsert=True
    )
    return new_count

async def clear_warns(chat_id: int, user_id: int):
    await warn_collection.delete_one({"chat_id": chat_id, "user_id": user_id})

async def get_user_info(client, chat_id: int, user_id: int):
    try:
        member = await client.get_chat_member(chat_id, user_id)
        name = f"{member.user.first_name or ''} {member.user.last_name or ''}".strip()
        username = f"@{member.user.username}" if member.user.username else ""
        return f"{name} {username}".strip() or str(user_id)
    except:
        return str(user_id)

async def is_admin(client, chat_id: int, user_id: int):
    try:
        member = await client.get_chat_member(chat_id, user_id)
        return bool(member.privileges)
    except:
        return False

def extract_target_id(message):
    if message.reply_to_message and message.reply_to_message.from_user:
        return message.reply_to_message.from_user.id
    if len(message.command) > 1:
        target_str = message.command[1]
        if target_str.isdigit():
            return int(target_str)
    return None

@app.on_message(filters.command("warn") & filters.group)
@block_dec
async def warn_handler(client, message: Message):
    chat_id = message.chat.id
    try:
        admin_member = await client.get_chat_member(chat_id, message.from_user.id)
        if not admin_member.privileges or not admin_member.privileges.can_restrict_members:
            return await message.reply("❌ Only admins can warn users!")
    except:
        return await message.reply("❌ Error checking admin status!")

    target_id = extract_target_id(message)
    if not target_id:
        return await message.reply("Usage: /warn [reply] or /warn <user_id> [reason]")

    if target_id == message.from_user.id:
        return await message.reply("❌ You can't warn yourself!")

    if await is_admin(client, chat_id, target_id):
        return await message.reply("❌ Can't warn admin!")

    user_info = await get_user_info(client, chat_id, target_id)
    reason = " ".join(message.command[2:]) if len(message.command) > 2 else "No reason"
    warn_count = await add_warn(chat_id, target_id, reason)
    
    warn_text = f"⚠️ **Warned User:** {user_info}\n"
    warn_text += f"**Warnings:** {warn_count}/3\n"
    warn_text += f"**Reason:** {reason}"
    await message.reply(warn_text)
    
    if warn_count == 2:
        await message.reply(f"🚨 {user_info} has 2/3 warns! Next warn = kick")
    elif warn_count == 3:
        try:
            await client.ban_chat_member(chat_id, target_id)
            await asyncio.sleep(1)
            await client.unban_chat_member(chat_id, target_id)
            await message.reply(f"👢 Auto kicked {user_info}! (3/3 warnings)")
        except:
            await message.reply(f"❌ Kick failed for {user_info}")

@app.on_message(filters.command("warns") & filters.group)
@block_dec
async def warns_handler(client, message: Message):
    chat_id = message.chat.id
    try:
        admin_member = await client.get_chat_member(chat_id, message.from_user.id)
        if not admin_member.privileges:
            return await message.reply("❌ Only admins can check warns!")
    except:
        return await message.reply("❌ Error checking admin status!")

    target_id = extract_target_id(message)
    if not target_id:
        return await message.reply("Usage: /warns [reply] or /warns <user_id>")

    user_info = await get_user_info(client, chat_id, target_id)
    warn_count = await get_warn_count(chat_id, target_id)
    
    if warn_count > 0:
        warn_data = await warn_collection.find_one({"chat_id": chat_id, "user_id": target_id})
        last_warned = warn_data.get('last_warned', datetime.now()).strftime("%Y-%m-%d %H:%M")
        status = f"📊 **User:** {user_info}\n"
        status += f"**Warnings:** {warn_count}/3\n"
        status += f"**Last Warned:** {last_warned}"
    else:
        status = f"📊 **User:** {user_info}\n**Warnings:** 0/3\n✅ No warnings!"
    
    await message.reply(status)

@app.on_message(filters.command("clearwarns") & filters.group)
@block_dec
async def clearwarns_handler(client, message: Message):
    chat_id = message.chat.id
    try:
        admin_member = await client.get_chat_member(chat_id, message.from_user.id)
        if not admin_member.privileges or not admin_member.privileges.can_restrict_members:
            return await message.reply("❌ Only admins can clear warns!")
    except:
        return await message.reply("❌ Error checking admin status!")

    target_id = extract_target_id(message)
    if not target_id:
        return await message.reply("Usage: /clearwarns [reply] or /clearwarns <user_id>")

    user_info = await get_user_info(client, chat_id, target_id)
    result = await warn_collection.delete_many({"chat_id": chat_id, "user_id": target_id})
    await message.reply(f"✅ Cleared {result.deleted_count} warning(s) for {user_info}!")

@app.on_message(filters.command("warnlist") & filters.group)
@block_dec
async def warnlist_handler(client, message: Message):
    chat_id = message.chat.id
    try:
        admin_member = await client.get_chat_member(chat_id, message.from_user.id)
        if not admin_member.privileges:
            return await message.reply("❌ Only admins can view warn list!")
    except:
        return await message.reply("❌ Error checking admin status!")

    warned_users = await warn_collection.find({"chat_id": chat_id}).sort("count", -1).to_list(length=10)
    if not warned_users:
        return await message.reply("📭 No users have been warned in this group!")
    
    text = "🔥 **Top 10 Warned Users:**\n\n"
    for idx, user in enumerate(warned_users, 1):
        user_info = await get_user_info(client, chat_id, user["user_id"])
        text += f"**{idx}.** {user_info} - {user['count']}/3 warns\n"
    
    await message.reply(text)

print("✅ Warning system loaded!")
