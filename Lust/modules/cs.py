from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import Message
from . import user_collection, sudo_filter, app

@app.on_message(filters.command("cs") & sudo_filter)
def reset_all_win_counts_command(client: Client, message: Message):
    try:
        user_collection.update_many({}, {'$set': {'wins': 0, 'last_win_time': datetime.min}})
        message.reply_text("Win counts have been reset for all users.")
    except Exception as e:
        message.reply_text(f"An error occurred while resetting win counts: {e}")

