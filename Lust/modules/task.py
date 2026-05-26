from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from . import app, capsify, user_collection, collection
from .watchers import suggest_watcher
import asyncio

SUPPORT_CHAT_ID = -1003551781050
SUGGESTION_CHANNEL_ID = -1003551781050

@app.on_message(filters.text | filters.photo, group=suggest_watcher)
async def suggestion_command(client, message):
    if message.from_user is None:
        return

    user_id = message.from_user.id
    chat_id = message.chat.id

    # Handle text or photo caption gracefully
    if message.photo:
        text = message.caption.strip() if message.caption else ""
    else:
        text = message.text.strip() if message.text else ""

    if "#suggestion" not in text.lower():
        return

    if chat_id == SUPPORT_CHAT_ID:
        if not text:
            await message.reply(capsify("Please provide a suggestion in your message after #suggestion."))
            return

        if message.photo:
            # Send message with photo to the suggestion channel
            sent_message = await client.send_photo(
                chat_id=SUGGESTION_CHANNEL_ID,
                photo=message.photo.file_id,
                caption=f"{capsify('#new_suggestion')}\n{capsify(text)}\n{capsify('Status: pending...')}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(capsify("Check Status"), url=f"https://t.me/fetcher_X/{message.id}")]
                ])
            )
        else:
            # Send text message to the suggestion channel
            sent_message = await client.send_message(
                chat_id=SUGGESTION_CHANNEL_ID,
                text=f"{capsify('#new_suggestion')}\n{capsify(text)}\n{capsify('Status: pending...')}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(capsify("Check Status"), url=f"https://t.me/fetcher_X/{message.id}")]
                ])
            )

        await message.reply(
            capsify(f"Your suggestion has been added! Please check the status using the button below."),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(capsify("Check Status"), url=f"https://t.me/fetcher_X/{sent_message.id}")]
            ])
        )
    else:
        await message.reply(
            capsify("You can only submit suggestions in the official suggestions group."),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(capsify("here"), url="https://t.me/fetcher_X")]
            ])
        )
