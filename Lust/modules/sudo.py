from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, Message 
from . import app, dev_filter, sudo_filter, capsify, db, user_collection
from Lust.config import OWNER_ID 

sudb = db.sudo
devb = db.dev
uploaderdb = db.uploader

NEGLECTED_IDS = {}

@app.on_message(filters.command("addsudo") & dev_filter)
async def add_sudo(client, message: Message):
    if message.reply_to_message:
        tar = message.reply_to_message.from_user.id
    else:
        try:
            tar = int(message.text.split()[1])
        except Exception:
            return await message.reply_text(capsify('Either reply to a user or provide an ID.'))

    if tar in NEGLECTED_IDS:
        return await message.reply_text(capsify('This user cannot be added to the sudo list.'))

    if await sudb.find_one({'user_id': tar}):
        return await message.reply_text(capsify('User is already a sudo user.'))

    try:
        await sudb.insert_one({'user_id': tar})
        await message.reply_text(capsify('User added to sudo list.'))
    except Exception:
        await message.reply_text(capsify('Failed to add user to sudo list.'))

@app.on_message(filters.command("rmsudo") & dev_filter)
async def remove_sudo(client, message: Message):
    if message.reply_to_message:
        tar = message.reply_to_message.from_user.id
    else:
        try:
            tar = int(message.text.split()[1])
        except Exception:
            return await message.reply_text(capsify('Either reply to a user or provide an ID.'))

    if not await sudb.find_one({'user_id': tar}):
        return await message.reply_text(capsify('User is not a sudo user.'))

    try:
        await sudb.delete_one({'user_id': tar})
        await message.reply_text(capsify('User removed from sudo list.'))
    except Exception:
        await message.reply_text(capsify('Failed to remove user from sudo list.'))

@app.on_message(filters.command("adddev") & (dev_filter | filters.user(OWNER_ID)))
async def add_dev(client, message: Message):
    if message.reply_to_message:
        tar = message.reply_to_message.from_user.id
    else:
        try:
            tar = int(message.text.split()[1])
        except Exception:
            return await message.reply_text(capsify('Either reply to a user or provide an ID.'))

    if tar in NEGLECTED_IDS:
        return await message.reply_text(capsify('This user cannot be added to the dev list.'))

    try:
        await devb.insert_one({'user_id': tar})
        await message.reply_text(capsify('User added to dev list.'))
    except Exception:
        await message.reply_text(capsify('Failed to add user to dev list.'))

@app.on_message(filters.command("rmdev") & dev_filter)
async def remove_dev(client, message: Message):
    if message.reply_to_message:
        tar = message.reply_to_message.from_user.id
    else:
        try:
            tar = int(message.text.split()[1])
        except Exception:
            return await message.reply_text(capsify('Either reply to a user or provide an ID.'))

    if tar == 6806897901:
        return await message.reply_text(capsify('This developer cannot be removed.'))

    if not await devb.find_one({'user_id': tar}):
        return await message.reply_text(capsify('User is not a developer.'))

    try:
        await devb.delete_one({'user_id': tar})
        await message.reply_text(capsify('User removed from dev list.'))
    except Exception:
        await message.reply_text(capsify('Failed to remove user from dev list.'))

@app.on_message(filters.command("adduploader") & (dev_filter | sudo_filter))  # Both can use
async def add_uploader(client, message: Message):
    user_id = message.from_user.id
    print(f"[DEBUG] User {user_id} using adduploader command")
    
    if message.reply_to_message:
        tar = message.reply_to_message.from_user.id
    else:
        try:
            tar = int(message.text.split()[1])
        except Exception:
            return await message.reply_text(capsify('Either reply to a user or provide an ID.'))

    if tar in NEGLECTED_IDS:
        return await message.reply_text(capsify('This user cannot be added to the uploader list.'))

    if await uploaderdb.find_one({'user_id': tar}):
        return await message.reply_text(capsify('User is already an uploader.'))

    try:
        await uploaderdb.insert_one({'user_id': tar})
        await message.reply_text(capsify(f'✅ User {tar} added to uploader list successfully!'))
    except Exception as e:
        print(f"Error adding uploader: {e}")
        await message.reply_text(capsify('Failed to add user to uploader list.'))
        
@app.on_message(filters.command("rmuploader") & sudo_filter)
async def remove_uploader(client, message: Message):
    if message.reply_to_message:
        tar = message.reply_to_message.from_user.id
    else:
        try:
            tar = int(message.text.split()[1])
        except Exception:
            return await message.reply_text(capsify('Either reply to a user or provide an ID.'))

    if not await uploaderdb.find_one({'user_id': tar}):
        return await message.reply_text(capsify('User is not an uploader.'))

    try:
        await uploaderdb.delete_one({'user_id': tar})
        await message.reply_text(capsify('User removed from uploader list.'))
    except Exception:
        await message.reply_text(capsify('Failed to remove user from uploader list.'))

@app.on_message(filters.command("sudolist") & sudo_filter)
async def sudo_list(client, message: Message):
    try:
        sudo_list = await sudb.distinct('user_id')
        if not sudo_list:
            return await message.reply_text(capsify('No sudo users found.'))

        user_list = []
        for user_id in sudo_list:
            user_data = await user_collection.find_one({'id': user_id})
            if user_data:
                first_name = user_data.get('first_name', 'Unknown')
                user_list.append(f"• {first_name} (`{user_id}`)")
            else:
                user_list.append(f"• User ID: {user_id} (`{user_id}`)")

        if not user_list:
            return await message.reply_text(capsify('No valid sudo users found.'))

        response_text = f'Total sudos: {len(user_list)}\n\n' + '\n'.join(user_list)
        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton("close", callback_data=f"sud_clos_{message.from_user.id}")]]
        )
        await message.reply_text(capsify(response_text), reply_markup=keyboard)
    except Exception as e:
        await message.reply_text(capsify(f'Error fetching sudo list: {str(e)}'))

@app.on_message(filters.command("devlist") & dev_filter)
async def dev_list(client, message: Message):
    try:
        dev_users_list = await devb.distinct('user_id')
        if not dev_users_list:
            return await message.reply_text(capsify('No developers found.'))

        user_list = []
        for user_id in dev_users_list:
            user_data = await user_collection.find_one({'id': user_id})
            if user_data:
                first_name = user_data.get('first_name', 'Unknown')
                user_list.append(f"• {first_name} (`{user_id}`)")
            else:
                user_list.append(f"• User ID: {user_id} (`{user_id}`)")

        if not user_list:
            return await message.reply_text(capsify('No valid developers found.'))

        response_text = f'Total developers: {len(user_list)}\n\n' + '\n'.join(user_list)
        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton("close", callback_data=f"sud_clos_{message.from_user.id}")]]
        )
        await message.reply_text(capsify(response_text), reply_markup=keyboard)
    except Exception as e:
        await message.reply_text(capsify(f'Error fetching developer list: {str(e)}'))

@app.on_message(filters.command("uploaderlist") & sudo_filter)
async def uploader_list(client, message: Message):
    try:
        uploader_users_list = await uploaderdb.distinct('user_id')
        if not uploader_users_list:
            return await message.reply_text(capsify('No uploaders found.'))

        user_list = []
        for user_id in uploader_users_list:
            user_data = await user_collection.find_one({'id': user_id})
            if user_data:
                first_name = user_data.get('first_name', 'Unknown')
                user_list.append(f"• {first_name} (`{user_id}`)")
            else:
                user_list.append(f"• User ID: {user_id} (`{user_id}`)")

        if not user_list:
            return await message.reply_text(capsify('No valid uploaders found.'))

        response_text = f'Total uploaders: {len(user_list)}\n\n' + '\n'.join(user_list)
        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton("close", callback_data=f"sud_clos_{message.from_user.id}")]]
        )
        await message.reply_text(capsify(response_text), reply_markup=keyboard)
    except Exception as e:
        await message.reply_text(capsify(f'Error fetching uploader list: {str(e)}'))

@app.on_callback_query(filters.regex(r"sud_clos_\d+"))
async def close_callback(client, callback_query: CallbackQuery):
    callback_user_id = int(callback_query.data.split("_")[-1])
    if callback_query.from_user.id != callback_user_id:
        return await callback_query.answer("This is not for you baka ❗", show_alert=True)
    await callback_query.message.delete()
