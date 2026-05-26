from pyrogram import filters
from pyrogram.types import Message
from pyrogram.errors import RPCError
from datetime import datetime, timedelta
import asyncio
import re

from . import app, db
from .block import block_dec

def extract_user_id(arg: str):
    """Extract user_id from username or ID"""
    try:
        # Direct user ID
        if arg.isdigit():
            return int(arg)
        
        # Username (@username)
        if arg.startswith('@'):
            # Remove @ and try to resolve
            username = arg[1:]
            return None  # We'll handle username differently
        
        return None
    except:
        return None

async def delete_user_messages(chat_id: int, user_id: int, minutes: int = 5):
    """Delete user's recent messages for specified minutes"""
    deleted_count = 0
    cutoff_time = datetime.now() - timedelta(minutes=minutes)
    
    try:
        async for message in app.get_chat_history(chat_id, limit=500):
            if (message.from_user and message.from_user.id == user_id and 
                message.date and message.date > cutoff_time):
                try:
                    await app.delete_messages(chat_id, message.id)
                    deleted_count += 1
                    await asyncio.sleep(0.05)  # Small delay to avoid flood
                except RPCError:
                    continue
                except Exception:
                    break
    except Exception:
        pass
    
    return deleted_count

async def ban_user(chat_id: int, user_id: int):
    try:
        await app.ban_chat_member(chat_id, user_id)
        return True
    except RPCError:
        return False

async def unban_user(chat_id: int, user_id: int):
    try:
        await app.unban_chat_member(chat_id, user_id)
        return True
    except RPCError:
        return False

async def get_user_info(chat_id: int, user_id: int):
    """Get user display name"""
    try:
        member = await app.get_chat_member(chat_id, user_id)
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

async def resolve_username(username: str):
    """Try to resolve username to user ID"""
    try:
        user = await app.get_users(username)
        return user.id
    except:
        return None

@app.on_message(filters.command("ban") & filters.group)
@block_dec
async def ban_handler(client, message: Message):
    chat_id = message.chat.id
    
    try:
        admin_member = await client.get_chat_member(chat_id, message.from_user.id)
        if not admin_member.privileges or not admin_member.privileges.can_restrict_members:
            return await message.reply("❌ Only admins can ban users!")
    except:
        return await message.reply("❌ Error checking admin status!")

    # Extract target from reply, command arg, or username
    target_id = None
    
    # Check reply first
    if message.reply_to_message and message.reply_to_message.from_user:
        target_id = message.reply_to_message.from_user.id
    # Check command arguments
    elif len(message.command) > 1:
        arg = message.command[1]
        
        # Check if it's a direct ID
        if arg.isdigit():
            target_id = int(arg)
        # Check if it's a username
        elif arg.startswith('@'):
            target_id = await resolve_username(arg[1:])
    
    if not target_id:
        return await message.reply("Usage: `/ban [reply]` or `/ban <user_id>` or `/ban @username`")

    # Check if trying to ban admin
    if await is_admin(client, chat_id, target_id):
        return await message.reply("❌ Can't ban admin!")

    try:
        success = await ban_user(chat_id, target_id)
        user_info = await get_user_info(chat_id, target_id)
        
        if success:
            await message.reply(f"✅ Banned {user_info}!")
        else:
            await message.reply(f"❌ Failed to ban {user_info}!")
        
    except Exception as e:
        await message.reply("❌ Error occurred!")

@app.on_message(filters.command("unban") & filters.group)
@block_dec
async def unban_handler(client, message: Message):
    chat_id = message.chat.id
    
    try:
        admin_member = await client.get_chat_member(chat_id, message.from_user.id)
        if not admin_member.privileges or not admin_member.privileges.can_restrict_members:
            return await message.reply("❌ Only admins can unban users!")
    except:
        return await message.reply("❌ Error checking admin status!")

    # Extract target
    target_id = None
    
    if message.reply_to_message and message.reply_to_message.from_user:
        target_id = message.reply_to_message.from_user.id
    elif len(message.command) > 1:
        arg = message.command[1]
        
        if arg.isdigit():
            target_id = int(arg)
        elif arg.startswith('@'):
            target_id = await resolve_username(arg[1:])
    
    if not target_id:
        return await message.reply("Usage: `/unban [reply]` or `/unban <user_id>` or `/unban @username`")

    try:
        success = await unban_user(chat_id, target_id)
        user_info = await get_user_info(chat_id, target_id)
        
        if success:
            await message.reply(f"✅ Unbanned {user_info}!")
        else:
            await message.reply(f"❌ Failed to unban {user_info}!")
        
    except Exception:
        await message.reply("❌ Error occurred!")

@app.on_message(filters.command("deluser") & filters.group)
@block_dec
async def deluser_handler(client, message: Message):
    chat_id = message.chat.id
    
    try:
        admin_member = await client.get_chat_member(chat_id, message.from_user.id)
        if not admin_member.privileges or not admin_member.privileges.can_delete_messages:
            return await message.reply("❌ Only admins with delete permissions can use this!")
    except:
        return await message.reply("❌ Error checking admin status!")

    # Extract target and minutes
    target_id = None
    minutes = 5
    
    # Check reply
    if message.reply_to_message and message.reply_to_message.from_user:
        target_id = message.reply_to_message.from_user.id
        if len(message.command) > 1 and message.command[1].isdigit():
            minutes = int(message.command[1])
    # Check command arguments
    elif len(message.command) > 1:
        arg = message.command[1]
        
        if arg.isdigit():
            target_id = int(arg)
            if len(message.command) > 2 and message.command[2].isdigit():
                minutes = int(message.command[2])
        elif arg.startswith('@'):
            target_id = await resolve_username(arg[1:])
            if len(message.command) > 2 and message.command[2].isdigit():
                minutes = int(message.command[2])
    
    if not target_id:
        return await message.reply(
            "Usage:\n`/deluser [reply] [minutes]`\n"
            "`/deluser <user_id> [minutes]`\n"
            "`/deluser @username [minutes]`\n"
            "(Default: 5 minutes)"
        )

    if minutes > 60:
        return await message.reply("❌ Maximum 60 minutes allowed!")

    try:
        user_info = await get_user_info(chat_id, target_id)
        status_msg = await message.reply(f"🧹 Deleting messages from {user_info} (last {minutes} mins)...")
        
        deleted = await delete_user_messages(chat_id, target_id, minutes)
        
        await status_msg.edit(f"✅ Done! Deleted {deleted} messages from {user_info}")
        
    except Exception:
        await message.reply("❌ Error occurred!")

print("✅ Advanced Ban/Unban/DelUser system loaded!")
