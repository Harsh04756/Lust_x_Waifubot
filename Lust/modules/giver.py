from pyrogram import Client, filters
import asyncio
from . import db, collection, user_collection, app, sudo_filter

destroyed_users = {}

async def add_all_characters_for_user(user_id):
    user = await user_collection.find_one({'id': user_id})

    if user:
        all_characters_cursor = collection.find({})
        all_characters = await all_characters_cursor.to_list(length=None)

        existing_character_ids = {character['id'] for character in user['characters']}
        new_characters = [character for character in all_characters if 'id' in character and character['id'] not in existing_character_ids]

        if new_characters:
            await user_collection.update_one(
                {'id': user_id},
                {'$push': {'characters': {'$each': new_characters}}}
            )

            return f"Successfully added characters for user {user_id}"
        else:
            return f"No new characters to add for user {user_id}"
    else:
        return f"User with ID {user_id} not found."


async def kill_character(receiver_id, character_id):
    character = await collection.find_one({'id': character_id})

    if character:
        try:
            await user_collection.update_one(
                {'id': receiver_id},
                {'$pull': {'characters': {'id': character_id}}}
            )

            return f"Successfully removed character `{character_id}` from user `{receiver_id}`"
        except Exception as e:
            print(f"Error updating user: {e}")
            raise
    else:
        raise ValueError("Character not found.")

@app.on_message(filters.command(["kill"]) & filters.reply & sudo_filter)
async def remove_character_command(client, message):
    try:
        character_id = str(message.text.split()[1])
        receiver_id = message.reply_to_message.from_user.id

        result_message = await kill_character(receiver_id, character_id)

        await message.reply_text(result_message)
    except (IndexError, ValueError) as e:
        await message.reply_text(str(e))
    except Exception as e:
        print(f"Error in remove_character_command: {e}")
        await message.reply_text("An error occurred while processing the command.")

async def remove_all_characters_for_user(user_id):
    user = await user_collection.find_one({'id': user_id})

    if user:
        destroyed_users[user_id] = user['characters']

        await user_collection.update_one(
            {'id': user_id},
            {'$set': {'characters': []}}
        )

        return f"Successfully destroyed all data for user {user_id}"
    else:
        return f"User with ID {user_id} not found."

async def restore_user_data(user_id):
    if user_id in destroyed_users:
        await user_collection.update_one(
            {'id': user_id},
            {'$set': {'characters': destroyed_users[user_id]}}
        )
        del destroyed_users[user_id]
        return f"Successfully restored data for user {user_id}"
    else:
        return f"No data to restore for user {user_id}"

@app.on_message(filters.command(["destroy"]) & sudo_filter)
async def remove_characters_command(client, message):
    if len(message.command) == 2:
        try:
            user_id_to_remove_characters_for = int(message.command[1])
            result_message = await remove_all_characters_for_user(user_id_to_remove_characters_for)
            await message.reply_text(result_message)
        except ValueError:
            await message.reply_text("Invalid User Id/ User Not Found")
    else:
        await message.reply_text("Use like this: /destroy {id} to destroy data")

@app.on_message(filters.command(["restore"]) & sudo_filter)
async def restore_characters_command(client, message):
    if len(message.command) == 2:
        try:
            user_id_to_restore_data_for = int(message.command[1])
            result_message = await restore_user_data(user_id_to_restore_data_for)
            await message.reply_text(result_message)
        except ValueError:
            await message.reply_text("Invalid User Id/ User Not Found")
    else:
        await message.reply_text("Use like this: /restore {id} to restore data")