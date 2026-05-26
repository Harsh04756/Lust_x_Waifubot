from pyrogram import Client, filters
from pyrogram.types import Message, ChatPrivileges
from pyrogram.errors import RPCError
from . import app


async def is_admin(client, chat_id: int, user_id: int):
    try:
        member = await client.get_chat_member(chat_id, user_id)
        return bool(member.privileges)
    except:
        return False


async def get_user_info(client, chat_id: int, user_id: int):
    try:
        member = await client.get_chat_member(chat_id, user_id)
        name = f"{member.user.first_name or ''} {member.user.last_name or ''}".strip()
        username = f"@{member.user.username}" if member.user.username else ""
        return f"{name} {username}".strip()
    except:
        return str(user_id)


async def resolve_username(username: str):
    try:
        user = await app.get_users(username)
        return user.id
    except:
        return None


async def extract_target_id(message: Message):
    if message.reply_to_message and message.reply_to_message.from_user:
        return message.reply_to_message.from_user.id

    if len(message.command) > 1:
        arg = message.command[1]

        if arg.isdigit():
            return int(arg)

        if arg.startswith("@"):
            return await resolve_username(arg[1:])

    return None


@app.on_message(filters.command("promote") & filters.group)
async def promote_handler(client: Client, message: Message):
    chat_id = message.chat.id

    try:
        admin = await client.get_chat_member(chat_id, message.from_user.id)
        if not admin.privileges or not admin.privileges.can_promote_members:
            return await message.reply("❌ You need promote permission!")
    except:
        return await message.reply("❌ Failed to verify admin permissions!")

    target_id = await extract_target_id(message)
    if not target_id:
        return await message.reply("Usage: /promote [reply | user_id | @username]")

    if target_id == message.from_user.id:
        return await message.reply("❌ You cannot promote yourself!")

    if await is_admin(client, chat_id, target_id):
        user_info = await get_user_info(client, chat_id, target_id)
        return await message.reply(f"❌ {user_info} is already an admin!")

    title = "Admin"
    if len(message.command) > 2:
        title = " ".join(message.command[2:])
        if len(title) > 16:
            return await message.reply("❌ Title must be 16 characters or less!")

    try:
        await client.promote_chat_member(
            chat_id=chat_id,
            user_id=target_id,
            privileges=ChatPrivileges(
                can_manage_chat=True,
                can_delete_messages=True,
                can_manage_video_chats=True,
                can_restrict_members=True,
                can_change_info=True,
                can_invite_users=True,
                can_pin_messages=True,
                can_promote_members=False
            )
        )

        await client.set_administrator_title(chat_id, target_id, title)

        user_info = await get_user_info(client, chat_id, target_id)
        await message.reply(f" Promoted  {user_info} !")

    except RPCError:
        await message.reply("❌ Promotion failed. Ensure bot has admin rights!")


@app.on_message(filters.command("demote") & filters.group)
async def demote_handler(client: Client, message: Message):
    chat_id = message.chat.id

    try:
        admin = await client.get_chat_member(chat_id, message.from_user.id)
        if not admin.privileges or not admin.privileges.can_promote_members:
            return await message.reply("❌ You need promote permission!")
    except:
        return await message.reply("❌ Failed to verify admin permissions!")

    target_id = await extract_target_id(message)
    if not target_id:
        return await message.reply("Usage: /demote [reply | user_id | @username]")

    if target_id == message.from_user.id:
        return await message.reply("❌ You cannot demote yourself!")

    if not await is_admin(client, chat_id, target_id):
        user_info = await get_user_info(client, chat_id, target_id)
        return await message.reply(f"❌ {user_info} is not an admin!")

    if target_id == (await client.get_me()).id:
        return await message.reply("❌ You cannot demote the bot!")

    try:
        await client.promote_chat_member(
            chat_id=chat_id,
            user_id=target_id,
            privileges=ChatPrivileges(
                can_manage_chat=False,
                can_delete_messages=False,
                can_manage_video_chats=False,
                can_restrict_members=False,
                can_change_info=False,
                can_invite_users=False,
                can_pin_messages=False,
                can_promote_members=False
            )
        )

        user_info = await get_user_info(client, chat_id, target_id)
        await message.reply(f"✅ Demoted {user_info} successfully!")

    except RPCError:
        await message.reply("❌ Demotion failed. Ensure bot has admin rights!")


print("✅ Promote / Demote system loaded")
