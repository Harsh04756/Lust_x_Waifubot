import asyncio
import time
from Lust import global_ban_users_collection, top_global_groups_collection


async def add_to_global_ban(user_id, reason):
    await global_ban_users_collection.update_one(
        {'_id': user_id},
        {'$set': {'reason': reason}},
        upsert=True
    )

async def remove_from_global_ban(user_id):
    await global_ban_users_collection.delete_one({"_id": user_id})

async def is_user_globally_banned(user_id):
    user = await global_ban_users_collection.find_one({"_id": user_id})
    return bool(user)

async def fetch_globally_banned_users():
    banned_users = []
    async for user in global_ban_users_collection.find({}):
        user_id = user.get('_id')
        reason = user.get('reason')
        if user_id:
            banned_users.append({"user_id": user_id, "reason": reason})
    return banned_users

async def get_all_chats():
    return await top_global_groups_collection.distinct("group_id")

async def ban_user_in_chats(client, user_id, all_chats):
    ban_count = 0
    for chat_id in all_chats:
        try:
            await client.kick_chat_member(chat_id, user_id)
            ban_count += 1
            await asyncio.sleep(0.5)
        except Exception as e:
            print(f"Failed to ban user {user_id} in chat {chat_id}: {e}")
    return ban_count

async def unban_user_in_chats(client, user_id, all_chats):
    unban_count = 0
    for chat_id in all_chats:
        try:
            await client.unban_chat_member(chat_id, user_id)
            unban_count += 1
            await asyncio.sleep(0.5)
        except Exception as e:
            print(f"Failed to unban user {user_id} in chat {chat_id}: {e}")
    return unban_count
