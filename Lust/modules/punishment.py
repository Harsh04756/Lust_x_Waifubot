import asyncio
from datetime import datetime, timedelta
from pyrogram import Client, filters
from pyrogram.types import Message, ChatPermissions
from pyrogram.errors import UserAdminInvalid, ChatAdminRequired
import time
import re

# Import app from your main module
from . import app

# Helper function to extract user from message
async def extract_user(message: Message):
    user_id = None
    user_name = None
    
    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        user_name = message.reply_to_message.from_user.mention
    elif len(message.command) > 1:
        user_arg = message.command[1]
        
        # Remove @ if present
        if user_arg.startswith('@'):
            user_arg = user_arg[1:]
        
        # Try to get user from mention or ID
        try:
            user_id = int(user_arg)
        except ValueError:
            # Try to get user by username
            try:
                user = await message._client.get_users(user_arg)
                user_id = user.id
                user_name = user.mention
            except Exception:
                return None, "User not found"
    
    return user_id, user_name

# KICK command
@app.on_message(filters.command(["kick", "remove"]) & filters.group)
async def kick_user(client: Client, message: Message):
    if not message.from_user:
        return
    
    # Check if user is admin
    try:
        member = await message.chat.get_member(message.from_user.id)
        if not member.privileges and not member.status == "creator":
            await message.reply_text("❌ You need to be an admin to use this command.")
            return
    except:
        await message.reply_text("❌ You need to be an admin to use this command.")
        return
    
    user_id, user_name = await extract_user(message)
    
    if not user_id:
        await message.reply_text("❌ Please reply to a user or provide user ID/username.\nUsage: `/kick @username` or reply to message.")
        return
    
    try:
        # Try to kick the user
        await message.chat.ban_member(user_id)
        
        # Auto unban after 2 seconds
        await message.reply_text(f"👢 {user_name or user_id} has been kicked from the group!")
        
        # Unban after 2 seconds
        await asyncio.sleep(2)
        await message.chat.unban_member(user_id)
        
    except ChatAdminRequired:
        await message.reply_text("❌ I need admin permissions to kick users!")
    except Exception as e:
        await message.reply_text(f"❌ Error: {str(e)}")

# KICKME command
@app.on_message(filters.command(["kickme", "leave"]) & filters.group)
async def kick_me(client: Client, message: Message):
    user_id = message.from_user.id
    
    try:
        # Check if user is admin (admins can't kick themselves)
        member = await message.chat.get_member(user_id)
        if member.privileges or member.status == "creator":
            await message.reply_text("❌ Admins can't kick themselves!")
            return
        
        # Kick the user
        await message.chat.ban_member(user_id)
        await message.reply_text("👋 See you later!")
        
        # Auto unban after 3 seconds
        await asyncio.sleep(3)
        await message.chat.unban_member(user_id)
        
    except Exception as e:
        await message.reply_text(f"❌ Error: {str(e)}")

# MUTE command
@app.on_message(filters.command(["mute", "silence"]) & filters.group)
async def mute_user(client: Client, message: Message):
    if not message.from_user:
        return
    
    # Check if user is admin
    try:
        member = await message.chat.get_member(message.from_user.id)
        if not member.privileges and not member.status == "creator":
            await message.reply_text("❌ You need to be an admin to use this command.")
            return
    except:
        await message.reply_text("❌ You need to be an admin to use this command.")
        return
    
    user_id, user_name = await extract_user(message)
    
    if not user_id:
        await message.reply_text("❌ Please reply to a user or provide user ID/username.\nUsage: `/mute @username` or reply to message.")
        return
    
    try:
        # Apply mute permissions
        await message.chat.restrict_member(
            user_id,
            ChatPermissions(
                can_send_messages=False,
                can_send_media_messages=False,
                can_send_other_messages=False,
                can_add_web_page_previews=False
            )
        )
        
        await message.reply_text(f"🔇 {user_name or user_id} has been muted!")
        
    except ChatAdminRequired:
        await message.reply_text("❌ I need admin permissions to mute users!")
    except Exception as e:
        await message.reply_text(f"❌ Error: {str(e)}")

# UNMUTE command
@app.on_message(filters.command(["unmute", "unsilence"]) & filters.group)
async def unmute_user(client: Client, message: Message):
    if not message.from_user:
        return
    
    # Check if user is admin
    try:
        member = await message.chat.get_member(message.from_user.id)
        if not member.privileges and not member.status == "creator":
            await message.reply_text("❌ You need to be an admin to use this command.")
            return
    except:
        await message.reply_text("❌ You need to be an admin to use this command.")
        return
    
    user_id, user_name = await extract_user(message)
    
    if not user_id:
        await message.reply_text("❌ Please reply to a user or provide user ID/username.\nUsage: `/unmute @username` or reply to message.")
        return
    
    try:
        # Restore full permissions
        await message.chat.restrict_member(
            user_id,
            ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True
            )
        )
        
        await message.reply_text(f"🔊 {user_name or user_id} has been unmuted!")
        
    except ChatAdminRequired:
        await message.reply_text("❌ I need admin permissions to unmute users!")
    except Exception as e:
        await message.reply_text(f"❌ Error: {str(e)}")

# TEMP MUTE command
@app.on_message(filters.command(["tmute"]) & filters.group)
async def temp_mute_user(client: Client, message: Message):
    if not message.from_user:
        return
    
    # Check if user is admin
    try:
        member = await message.chat.get_member(message.from_user.id)
        if not member.privileges and not member.status == "creator":
            await message.reply_text("❌ You need to be an admin to use this command.")
            return
    except:
        await message.reply_text("❌ You need to be an admin to use this command.")
        return
    
    if len(message.command) < 3:
        await message.reply_text("❌ Usage: `/tmute @username 10m` (m=minutes, h=hours, d=days)")
        return
    
    user_id, user_name = await extract_user(message)
    
    if not user_id:
        await message.reply_text("❌ User not found!")
        return
    
    # Parse time duration
    time_arg = message.command[2].lower()
    try:
        if time_arg.endswith('m'):  # minutes
            minutes = int(time_arg[:-1])
            duration = timedelta(minutes=minutes)
            time_text = f"{minutes} minute(s)"
        elif time_arg.endswith('h'):  # hours
            hours = int(time_arg[:-1])
            duration = timedelta(hours=hours)
            time_text = f"{hours} hour(s)"
        elif time_arg.endswith('d'):  # days
            days = int(time_arg[:-1])
            duration = timedelta(days=days)
            time_text = f"{days} day(s)"
        else:
            minutes = int(time_arg)
            duration = timedelta(minutes=minutes)
            time_text = f"{minutes} minute(s)"
    except:
        await message.reply_text("❌ Invalid time format! Use: 10m, 2h, 1d")
        return
    
    try:
        # Apply mute
        await message.chat.restrict_member(
            user_id,
            ChatPermissions(
                can_send_messages=False,
                can_send_media_messages=False,
                can_send_other_messages=False,
                can_add_web_page_previews=False
            ),
            until_date=datetime.now() + duration
        )
        
        await message.reply_text(f"⏰ {user_name or user_id} has been muted for {time_text}!")
        
    except ChatAdminRequired:
        await message.reply_text("❌ I need admin permissions to mute users!")
    except Exception as e:
        await message.reply_text(f"❌ Error: {str(e)}")

# TEMP BAN command
@app.on_message(filters.command(["tban"]) & filters.group)
async def temp_ban_user(client: Client, message: Message):
    if not message.from_user:
        return
    
    # Check if user is admin
    try:
        member = await message.chat.get_member(message.from_user.id)
        if not member.privileges and not member.status == "creator":
            await message.reply_text("❌ You need to be an admin to use this command.")
            return
    except:
        await message.reply_text("❌ You need to be an admin to use this command.")
        return
    
    if len(message.command) < 3:
        await message.reply_text("❌ Usage: `/tban @username 10m` (m=minutes, h=hours, d=days)")
        return
    
    user_id, user_name = await extract_user(message)
    
    if not user_id:
        await message.reply_text("❌ User not found!")
        return
    
    # Parse time duration
    time_arg = message.command[2].lower()
    try:
        if time_arg.endswith('m'):  # minutes
            minutes = int(time_arg[:-1])
            duration = timedelta(minutes=minutes)
            time_text = f"{minutes} minute(s)"
        elif time_arg.endswith('h'):  # hours
            hours = int(time_arg[:-1])
            duration = timedelta(hours=hours)
            time_text = f"{hours} hour(s)"
        elif time_arg.endswith('d'):  # days
            days = int(time_arg[:-1])
            duration = timedelta(days=days)
            time_text = f"{days} day(s)"
        else:
            minutes = int(time_arg)
            duration = timedelta(minutes=minutes)
            time_text = f"{minutes} minute(s)"
    except:
        await message.reply_text("❌ Invalid time format! Use: 10m, 2h, 1d")
        return
    
    try:
        # Apply temp ban
        await message.chat.ban_member(
            user_id,
            until_date=datetime.now() + duration
        )
        
        await message.reply_text(f"⏰ {user_name or user_id} has been banned for {time_text}!")
        
    except ChatAdminRequired:
        await message.reply_text("❌ I need admin permissions to ban users!")
    except Exception as e:
        await message.reply_text(f"❌ Error: {str(e)}")

# SILENT BAN command
@app.on_message(filters.command(["sban", "stealthban"]) & filters.group)
async def silent_ban_user(client: Client, message: Message):
    if not message.from_user:
        return
    
    # Check if user is admin
    try:
        member = await message.chat.get_member(message.from_user.id)
        if not member.privileges and not member.status == "creator":
            await message.reply_text("❌ You need to be an admin to use this command.")
            return
    except:
        await message.reply_text("❌ You need to be an admin to use this command.")
        return
    
    user_id, user_name = await extract_user(message)
    
    if not user_id:
        await message.reply_text("❌ Please reply to a user or provide user ID/username.")
        return
    
    try:
        # Silent ban (no notification)
        await message.chat.ban_member(user_id)
        
        # Delete the command message
        await message.delete()
        
    except ChatAdminRequired:
        await message.reply_text("❌ I need admin permissions to ban users!")
    except Exception as e:
        await message.reply_text(f"❌ Error: {str(e)}")

# DELETE AND BAN command
@app.on_message(filters.command(["dban", "deleteban"]) & filters.group)
async def delete_and_ban(client: Client, message: Message):
    if not message.from_user:
        return
    
    # Check if user is admin
    try:
        member = await message.chat.get_member(message.from_user.id)
        if not member.privileges and not member.status == "creator":
            await message.reply_text("❌ You need to be an admin to use this command.")
            return
    except:
        await message.reply_text("❌ You need to be an admin to use this command.")
        return
    
    if not message.reply_to_message:
        await message.reply_text("❌ Please reply to a message to use this command.")
        return
    
    user_id = message.reply_to_message.from_user.id
    user_name = message.reply_to_message.from_user.mention
    
    try:
        # Delete the replied message
        await message.reply_to_message.delete()
        
        # Delete the command message
        await message.delete()
        
        # Ban the user
        await message.chat.ban_member(user_id)
        
        # Send silent notification to admin only
        await client.send_message(
            message.from_user.id,
            f"✅ Message deleted and {user_name} has been banned."
        )
        
    except ChatAdminRequired:
        await message.reply_text("❌ I need admin permissions to delete messages and ban users!")
    except Exception as e:
        await message.reply_text(f"❌ Error: {str(e)}")

# HELP command for moderation
@app.on_message(filters.command(["banhelp", "help"]) & filters.group)
async def mod_help(client: Client, message: Message):
    help_text = """
🎯 **ᴘᴜɴɪꜱʜᴍᴇɴᴛ ⁄ ᴘᴏʟɪᴄɪɴɢ**
ᴀᴠᴀɪʟᴀʙʟᴇ ᴄᴏᴍᴍᴀɴᴅꜱ ꜰᴏʀ ᴍᴏᴅᴇʀᴀᴛɪᴏɴ:

• /ban <ᴜꜱᴇʀ> : ᴘᴇʀᴍᴀɴᴇɴᴛʟʏ ʙᴀɴꜱ ᴛʜᴇ ᴜꜱᴇʀ
• /unban <ᴜꜱᴇʀ> : ʀᴇᴠᴏᴋᴇꜱ ᴀ ʙᴀɴ
• /kick <ᴜꜱᴇʀ> : ᴛᴇᴍᴘᴏʀᴀʀɪʟʏ ʀᴇᴍᴏᴠᴇꜱ ᴀ ᴜꜱᴇʀ (ᴀᴜᴛᴏ-ᴜɴʙᴀɴ ᴀꜰᴛᴇʀ 2ꜱ)
• /kickme : ꜱᴇʟꜰ-ᴇᴊᴇᴄᴛ ꜰʀᴏᴍ ɢʀᴏᴜᴘ (ᴀᴜᴛᴏ-ᴜɴʙᴀɴ ᴀꜰᴛᴇʀ 3ꜱ)
• /mute <ᴜꜱᴇʀ> : ᴘʀᴇᴠᴇɴᴛꜱ ᴀ ᴜꜱᴇʀ ꜰʀᴏᴍ ꜱᴇɴᴅɪɴɢ ᴍᴇꜱꜱᴀɢᴇꜱ
• /tmute <ᴜꜱᴇʀ> x(ᴍ/ʜ/ᴅ) : ᴛᴇᴍᴘ ᴍᴜᴛᴇ ꜰᴏʀ x ᴛɪᴍᴇ
• /unmute <ᴜꜱᴇʀ> : ʟɪꜰᴛꜱ ᴀ ᴍᴜᴛᴇ
• /tban <ᴜꜱᴇʀ> x(ᴍ/ʜ/ᴅ) : ᴛᴇᴍᴘᴏʀᴀʀʏ ʙᴀɴ ᴡɪᴛʜ ᴅᴜʀᴀᴛɪᴏɴ
• /sban <ᴜꜱᴇʀ> : ꜱɪʟᴇɴᴛ ʙᴀɴ ᴡɪᴛʜᴏᴜᴛ ɴᴏᴛɪꜰɪᴄᴀᴛɪᴏɴ
• /dban (ʀᴇᴘʟʏ ᴏɴʟʏ) : ᴅᴇʟᴇᴛᴇꜱ ᴀ ᴍᴇꜱꜱᴀɢᴇ ᴀɴᴅ ʙᴀɴꜱ ᴛʜᴇ ꜱᴇɴᴅᴇʀ

📝 **ᴜꜱᴀɢᴇ:**
• Reply to a user's message
• Use @username
• Or provide user ID

⚡ **ɴᴏᴛᴇ:** ᴏɴʟʏ ᴀᴅᴍɪɴꜱ ᴄᴀɴ ᴜꜱᴇ ᴛʜᴇꜱᴇ ᴄᴏᴍᴍᴀɴᴅꜱ
    """
    
    await message.reply_text(help_text)
