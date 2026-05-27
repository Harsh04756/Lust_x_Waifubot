from pyrogram import filters
from . import collection, user_collection, sudo_filter, app, capsify

LOG_CHAT_ID = -1002992299647


def clean_char(character):
    """Remove MongoDB _id before storing in user array"""
    c = dict(character)
    c.pop('_id', None)
    return c


async def send_media(message, media, caption):
    try:
        await message.reply_photo(photo=media, caption=caption)
        return
    except:
        pass
    try:
        await message.reply_video(video=media, caption=caption)
        return
    except:
        pass
    try:
        await message.reply_animation(animation=media, caption=caption)
        return
    except:
        pass
    await message.reply_document(document=media, caption=caption)


async def give_character(receiver_id, character_id):
    """Character do user ko - proper insert like marry command"""
    character = await collection.find_one({'id': character_id})
    if not character:
        raise ValueError(f"ᴄʜᴀʀᴀᴄᴛᴇʀ `{character_id}` ɴᴏᴛ ғᴏᴜɴᴅ.")
    
    user = await user_collection.find_one({'id': receiver_id})
    if user and 'characters' in user:
        for existing_char in user['characters']:
            if existing_char.get('id') == character_id:
                raise ValueError(f"ᴜꜱᴇʀ ᴀʟʀᴇᴀᴅʏ ʜᴀꜱ ᴄʜᴀʀᴀᴄᴛᴇʀ: {character['name']}")
    
    clean_char_data = clean_char(character)
    

    await user_collection.update_one(
        {'id': receiver_id},
        {'$push': {'characters': clean_char_data}},
        upsert=True
    )
    

    verify_user = await user_collection.find_one({'id': receiver_id})
    character_added = False
    for char in verify_user.get('characters', []):
        if char.get('id') == character_id:
            character_added = True
            break
    
    if not character_added:
        raise ValueError("ғᴀɪʟᴇᴅ ᴛᴏ ᴀᴅᴅ ᴄʜᴀʀᴀᴄᴛᴇʀ.")
    
    media = character['img_url']
    caption = capsify(
        f"✅ ᴄʜᴀʀᴀᴄᴛᴇʀ ᴀᴅᴅᴇᴅ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ!\n\n"
        f"👤 ᴜꜱᴇʀ ɪᴅ: `{receiver_id}`\n"
        f"🫂 ᴀɴɪᴍᴇ: {character['anime']}\n"
        f"💕 ɴᴀᴍᴇ: {character['name']}\n"
        f"🍿 ɪᴅ: `{character['id']}`\n"
        f"🌟 ʀᴀʀɪᴛʏ: {character.get('rarity', 'ᴜɴᴋɴᴏᴡɴ')}"
    )
    return media, caption, character


@app.on_message(filters.command(["addchar"]) & sudo_filter)
async def give_character_command(client, message):
    if not message.reply_to_message:
        await message.reply_text(capsify("❌ ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴜꜱᴇʀ ᴛᴏ ɢɪᴠᴇ ᴄʜᴀʀᴀᴄᴛᴇʀ."))
        return
    
    try:
        args = message.text.split()
        if len(args) < 2:
            await message.reply_text(capsify("❌ ᴘʀᴏᴠɪᴅᴇ ᴄʜᴀʀᴀᴄᴛᴇʀ ɪᴅ.\nᴜꜱᴀɢᴇ: `/ᴀᴅᴅᴄʜᴀʀ <ᴄʜᴀʀᴀᴄᴛᴇʀ_ɪᴅ>`"))
            return
        
        character_id = str(args[1])
        receiver_id = message.reply_to_message.from_user.id
        receiver_name = message.reply_to_message.from_user.first_name
        giver_name = message.from_user.first_name
        
        media, caption, character = await give_character(receiver_id, character_id)
        await send_media(message, media, caption)
        
        await client.send_message(
            LOG_CHAT_ID, 
            f"📦 {giver_name} ɢᴀᴠᴇ ᴄʜᴀʀᴀᴄᴛᴇʀ `{character_id}` ({character['name']}) ᴛᴏ {receiver_name} (`{receiver_id}`)"
        )
        
    except IndexError:
        await message.reply_text(capsify("❌ ᴘʀᴏᴠɪᴅᴇ ᴄʜᴀʀᴀᴄᴛᴇʀ ɪᴅ.\nᴜꜱᴀɢᴇ: `/ᴀᴅᴅᴄʜᴀʀ <ᴄʜᴀʀᴀᴄᴛᴇʀ_ɪᴅ>`"))
    except ValueError as e:
        await message.reply_text(capsify(f"❌ {str(e)}"))
    except Exception as e:
        print(e)
        await message.reply_text(capsify("❌ ᴇʀʀᴏʀ ᴡʜɪʟᴇ ᴘʀᴏᴄᴇꜱꜱɪɴɢ ᴄᴏᴍᴍᴀɴᴅ."))


async def add_all_characters_for_user(user_id):
    """Add all characters for user - proper insert"""
    user = await user_collection.find_one({'id': user_id})
    if not user:
        await user_collection.insert_one({'id': user_id, 'characters': []})
        user = await user_collection.find_one({'id': user_id})
    
    all_chars = await collection.find({}).to_list(length=None)
    existing_ids = {c.get('id') for c in user.get('characters', []) if c.get('id')}
    
    new_chars = []
    for c in all_chars:
        if c.get('id') not in existing_ids:
            new_chars.append(clean_char(c))
    
    if not new_chars:
        return capsify(f"ℹ️ ɴᴏ ɴᴇᴡ ᴄʜᴀʀᴀᴄᴛᴇʀꜱ ᴛᴏ ᴀᴅᴅ ꜰᴏʀ ᴜꜱᴇʀ `{user_id}`.")
    
    await user_collection.update_one(
        {'id': user_id},
        {'$push': {'characters': {'$each': new_chars}}}
    )
    
    return capsify(f"✅ ᴀᴅᴅᴇᴅ {len(new_chars)} ɴᴇᴡ ᴄʜᴀʀᴀᴄᴛᴇʀꜱ ᴛᴏ ᴜꜱᴇʀ `{user_id}`")


@app.on_message(filters.command(["ad"]) & sudo_filter)
async def add_characters_command(client, message):
    if not message.reply_to_message:
        await message.reply_text(capsify("❌ ʀᴇᴘʟʏ ᴛᴏ ᴜꜱᴇʀ ᴛᴏ ᴀᴅᴅ ᴀʟʟ ᴄʜᴀʀᴀᴄᴛᴇʀꜱ."))
        return
    
    uid = message.reply_to_message.from_user.id
    res = await add_all_characters_for_user(uid)
    await message.reply_text(res)


async def kill_character(receiver_id, character_id):
    """Remove character from user - proper delete"""
    character = await collection.find_one({'id': character_id})
    if not character:
        raise ValueError(f"ᴄʜᴀʀᴀᴄᴛᴇʀ `{character_id}` ɴᴏᴛ ғᴏᴜɴᴅ.")
    
    user = await user_collection.find_one({'id': receiver_id})
    if not user:
        raise ValueError(f"ᴜꜱᴇʀ `{receiver_id}` ɴᴏᴛ ғᴏᴜɴᴅ.")
    
    character_exists = False
    for char in user.get('characters', []):
        if char.get('id') == character_id:
            character_exists = True
            break
    
    if not character_exists:
        raise ValueError(f"ᴜꜱᴇʀ ᴅᴏᴇꜱ ɴᴏᴛ ʜᴀᴠᴇ ᴄʜᴀʀᴀᴄᴛᴇʀ `{character_id}`.")
    
    result = await user_collection.update_one(
        {'id': receiver_id},
        {'$pull': {'characters': {'id': character_id}}}
    )
    
    if result.modified_count == 0:
        raise ValueError(f"ғᴀɪʟᴇᴅ ᴛᴏ ʀᴇᴍᴏᴠᴇ ᴄʜᴀʀᴀᴄᴛᴇʀ `{character_id}`.")
    
    updated_user = await user_collection.find_one({'id': receiver_id})
    for char in updated_user.get('characters', []):
        if char.get('id') == character_id:
            raise ValueError(f"ᴄʜᴀʀᴀᴄᴛᴇʀ `{character_id}` ꜱᴛɪʟʟ ᴇxɪꜱᴛꜱ ᴀғᴛᴇʀ ʀᴇᴍᴏᴠᴀʟ.")
    
    return capsify(f"✅ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ʀᴇᴍᴏᴠᴇᴅ ᴄʜᴀʀᴀᴄᴛᴇʀ `{character_id}` ({character['name']}) ғʀᴏᴍ ᴜꜱᴇʀ `{receiver_id}`.")


@app.on_message(filters.command(["blank"]) & sudo_filter)
async def remove_character_command(client, message):
    try:
        args = message.text.split()
        
        if len(args) == 3:
            receiver_id = int(args[1])
            character_id = str(args[2])
        elif len(args) == 2 and message.reply_to_message:
            receiver_id = message.reply_to_message.from_user.id
            character_id = str(args[1])
        else:
            await message.reply_text(
                capsify("❌ ᴜꜱᴀɢᴇ:\n1. ʀᴇᴘʟʏ ᴛᴏ ᴜꜱᴇʀ: `/ʙʟᴀɴᴋ <ᴄʜᴀʀᴀᴄᴛᴇʀ_ɪᴅ>`\n2. ᴅɪʀᴇᴄᴛ: `/ʙʟᴀɴᴋ <ᴜꜱᴇʀ_ɪᴅ> <ᴄʜᴀʀᴀᴄᴛᴇʀ_ɪᴅ>`")
            )
            return
        
        res = await kill_character(receiver_id, character_id)
        await message.reply_text(res)
        
        await client.send_message(
            LOG_CHAT_ID, 
            f"🗑️ ᴄʜᴀʀᴀᴄᴛᴇʀ `{character_id}` ʀᴇᴍᴏᴠᴇᴅ ғʀᴏᴍ ᴜꜱᴇʀ `{receiver_id}` ʙʏ {message.from_user.first_name}"
        )
        
    except ValueError as e:
        await message.reply_text(capsify(f"❌ {str(e)}"))
    except Exception as e:
        print(e)
        await message.reply_text(capsify("❌ ᴇʀʀᴏʀ ᴡʜɪʟᴇ ʀᴇᴍᴏᴠɪɴɢ ᴄʜᴀʀᴀᴄᴛᴇʀ."))


@app.on_message(filters.command(["checkchars"]) & sudo_filter)
async def check_user_characters(client, message):
    if not message.reply_to_message:
        await message.reply_text(capsify("❌ ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴜꜱᴇʀ ᴛᴏ ᴄʜᴇᴄᴋ ᴄʜᴀʀᴀᴄᴛᴇʀꜱ."))
        return
    
    uid = message.reply_to_message.from_user.id
    user = await user_collection.find_one({'id': uid})
    
    if not user:
        await message.reply_text(capsify(f"❌ ᴜꜱᴇʀ `{uid}` ɴᴏᴛ ғᴏᴜɴᴅ ɪɴ ᴅᴀᴛᴀʙᴀꜱᴇ."))
        return
    
    characters = user.get('characters', [])
    char_count = len(characters)
    
    char_list = "\n".join([f"• {c.get('name', 'ᴜɴᴋɴᴏᴡɴ')} (`{c.get('id', 'ɴᴏ ɪᴅ')}`)" for c in characters[:10]])
    
    text = capsify(
        f"📊 ᴜꜱᴇʀ ᴄʜᴀʀᴀᴄᴛᴇʀ ɪɴꜰᴏ\n\n"
        f"👤 ᴜꜱᴇʀ ɪᴅ: `{uid}`\n"
        f"📦 ᴛᴏᴛᴀʟ ᴄʜᴀʀᴀᴄᴛᴇʀꜱ: {char_count}\n\n"
    )
    
    if char_count > 0:
        text += capsify(f"**ʀᴇᴄᴇɴᴛ ᴄʜᴀʀᴀᴄᴛᴇʀꜱ (ꜰɪʀꜱᴛ 10):**\n{char_list}")
        if char_count > 10:
            text += capsify(f"\n... ᴀɴᴅ {char_count - 10} ᴍᴏʀᴇ")
    else:
        text += capsify("❌ ɴᴏ ᴄʜᴀʀᴀᴄᴛᴇʀꜱ ғᴏᴜɴᴅ.")
    
    await message.reply_text(text)
