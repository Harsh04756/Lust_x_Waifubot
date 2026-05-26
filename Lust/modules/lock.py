from pyrogram import filters
from pyrogram.types import ChatPermissions, Message
from . import app, db
from .block import block_dec

# Initialize collection for locks
locks_collection = db.locks

LOCK_TYPES = {
    "audio": "audio",
    "voice": "voice", 
    "document": "document",
    "video": "video",
    "contact": "contact",
    "photo": "photo",
    "url": "url",
    "bots": "bots",
    "forward": "forward",
    "sticker": "sticker",
    "gif": "gif",
    "poll": "poll",
    "other": "other",
    "previews": "previews"
}

LOCK_CHAT_RESTRICTION = {
    "all": ChatPermissions(
        can_send_messages=False,
        can_send_media_messages=False,
        can_send_polls=False,
        can_send_other_messages=False,
        can_add_web_page_previews=False
    ),
    "messages": ChatPermissions(can_send_messages=False),
    "media": ChatPermissions(can_send_media_messages=False),
    "sticker": ChatPermissions(can_send_other_messages=False),
    "gif": ChatPermissions(can_send_other_messages=False),
    "poll": ChatPermissions(can_send_polls=False),
    "other": ChatPermissions(can_send_other_messages=False),
    "previews": ChatPermissions(can_add_web_page_previews=False),
    "info": ChatPermissions(can_change_info=False),
    "invite": ChatPermissions(can_invite_users=False),
    "pin": ChatPermissions(can_pin_messages=False)
}

async def is_admin(client, chat_id, user_id):
    try:
        member = await client.get_chat_member(chat_id, user_id)
        return bool(member.privileges)
    except:
        return False

async def apply_locks(chat_id: int):
    """Apply locks to chat permissions"""
    try:
        data = await locks_collection.find_one({"chat_id": chat_id})
        locks = data.get("locks", {}) if data else {}
        
        # Start with FULL permissions
        new_perms = ChatPermissions(
            can_send_messages=True,
            can_send_media_messages=True,
            can_send_polls=True,
            can_send_other_messages=True,
            can_add_web_page_previews=True,
            can_change_info=True,
            can_invite_users=True,
            can_pin_messages=True
        )
        
        # Apply ONLY active locks
        if locks.get("all", False):
            new_perms = LOCK_CHAT_RESTRICTION["all"]
        else:
            if locks.get("messages", False): 
                new_perms.can_send_messages = False
            if locks.get("media", False): 
                new_perms.can_send_media_messages = False
            if locks.get("poll", False): 
                new_perms.can_send_polls = False
            if locks.get("sticker", False) or locks.get("gif", False) or locks.get("other", False):
                new_perms.can_send_other_messages = False
            if locks.get("previews", False): 
                new_perms.can_add_web_page_previews = False
            if locks.get("info", False): 
                new_perms.can_change_info = False
            if locks.get("invite", False): 
                new_perms.can_invite_users = False
            if locks.get("pin", False): 
                new_perms.can_pin_messages = False
        
        await app.set_chat_permissions(chat_id, new_perms)
        print(f"✅ Applied locks to chat {chat_id}")
    except Exception as e:
        print(f"❌ Apply locks error: {e}")

@app.on_message(filters.command("lock") & filters.group)
@block_dec
async def lock_handler(client, message: Message):
    chat_id = message.chat.id
    
    if not await is_admin(client, chat_id, message.from_user.id):
        return await message.reply("❌ Only admins can lock content!")
    
    if len(message.command) < 2:
        return await message.reply("Usage: `/lock <type>`\n\nSee available types with `/locktypes`")
    
    lock_type = message.command[1].lower()
    valid_locks = list(LOCK_TYPES.keys()) + list(LOCK_CHAT_RESTRICTION.keys())
    
    if lock_type not in valid_locks:
        return await message.reply(f"❌ Invalid lock type!\n\nSee available types with `/locktypes`")
    
    try:
        await locks_collection.update_one(
            {"chat_id": chat_id},
            {"$set": {f"locks.{lock_type}": True}},
            upsert=True
        )
        await apply_locks(chat_id)
        await message.reply(f"🔒 Locked **{lock_type}** for non-admins!")
        print(f"✅ LOCKED {lock_type} in {chat_id}")
    except Exception as e:
        print(f"❌ LOCK ERROR: {e}")
        await message.reply("❌ Lock failed!")

@app.on_message(filters.command("unlock") & filters.group)
@block_dec
async def unlock_handler(client, message: Message):
    chat_id = message.chat.id
    
    if not await is_admin(client, chat_id, message.from_user.id):
        return await message.reply("❌ Only admins can unlock content!")
    
    if len(message.command) < 2:
        return await message.reply("Usage: `/unlock <type>`\n\nSee available types with `/locktypes`")
    
    unlock_type = message.command[1].lower()
    valid_locks = list(LOCK_TYPES.keys()) + list(LOCK_CHAT_RESTRICTION.keys())
    
    if unlock_type not in valid_locks:
        return await message.reply(f"❌ Invalid unlock type!\n\nSee available types with `/locktypes`")
    
    try:
        # Remove specific lock
        await locks_collection.update_one(
            {"chat_id": chat_id},
            {"$unset": {f"locks.{unlock_type}": ""}}
        )
        # Clean up dead entries and re-save
        data = await locks_collection.find_one({"chat_id": chat_id})
        if data and data.get("locks"):
            clean_locks = {k: v for k, v in data["locks"].items() if v is True}
            await locks_collection.update_one(
                {"chat_id": chat_id},
                {"$set": {"locks": clean_locks}},
                upsert=True
            )
        await apply_locks(chat_id)
        await message.reply(f"🔓 Unlocked **{unlock_type}**!")
        print(f"✅ UNLOCKED {unlock_type} in {chat_id}")
    except Exception as e:
        print(f"❌ UNLOCK ERROR: {e}")
        await message.reply("❌ Unlock failed!")

@app.on_message(filters.command("locktypes") & filters.group)
@block_dec
async def locktypes_handler(client, message: Message):
    chat_id = message.chat.id
    
    if not await is_admin(client, chat_id, message.from_user.id):
        return await message.reply("❌ Only admins can view lock types!")
    
    try:
        data = await locks_collection.find_one({"chat_id": chat_id})
        locks = data.get("locks", {}) if data else {}
        
        chat = await client.get_chat(chat_id)
        perms = chat.permissions or ChatPermissions(
            can_send_messages=True,
            can_send_media_messages=True,
            can_send_polls=True,
            can_send_other_messages=True,
            can_add_web_page_previews=True,
            can_change_info=True,
            can_invite_users=True,
            can_pin_messages=True
        )
        
        # Create lock types list
        lock_types_text = "**Available Lock Types:**\n\n"
        lock_types_text += "**Content Types:**\n"
        content_types = ["audio", "voice", "document", "video", "contact", "photo", "url", 
                        "bots", "forward", "sticker", "gif", "poll", "other", "previews"]
        for ltype in content_types:
            lock_types_text += f"• `{ltype}`\n"
        
        lock_types_text += "\n**Permission Types:**\n"
        perm_types = ["all", "messages", "media", "info", "invite", "pin"]
        for ptype in perm_types:
            lock_types_text += f"• `{ptype}`\n"
        
        # Current status
        status_text = "**Current Lock Status:**\n\n"
        if locks:
            locked_items = [k for k, v in locks.items() if v]
            if locked_items:
                status_text += "🔒 **Currently Locked:**\n"
                for item in locked_items:
                    status_text += f"• `{item}`\n"
            else:
                status_text += "✅ No locks active\n"
        else:
            status_text += "✅ No locks active\n"
        
        # Send as two separate messages for clarity
        await message.reply(lock_types_text)
        await message.reply(status_text)
        
    except Exception as e:
        print(f"Error in locktypes: {e}")
        await message.reply("❌ Failed to fetch lock information!")

print("✅ Lock System Module Loaded!")
