from pyrogram import Client, filters
from pyrogram.types import Message
from . import Lusts as app, user_collection, show, sbank, capsify
from datetime import datetime
from .block import block_dec, temp_block

@app.on_message(filters.command("bal"))
@block_dec
async def balance(client: Client, message: Message):
    if not message.from_user:
        await message.reply_text(capsify("COULDN'T RETRIEVE USER INFORMATION."))
        return

    user_id = message.from_user.id
    username = message.from_user.first_name or "None"
    
    if temp_block(user_id):
        return
    
    user_data = await user_collection.find_one(
        {'id': user_id}, 
        projection={'balance': 1, 'saved_amount': 1, 'loan_amount': 1}
    )

    if user_data:
        ub = await show(user_id)
        balance_amount = int(ub)
        bb = await sbank(user_id)
        saved_amount = int(bb)
        loan_amount = user_data.get('loan_amount', 0)
        
        # Calculate total worth
        total_worth = balance_amount + saved_amount

        # Create the formatted message
        caption = "✦━═❖ ᴇʟɪxɪʀ ᴀᴄᴄᴏᴜɴᴛ ❖═━✦\n"
        caption += "╭────────────────────╮\n"
        caption += f"• ɴᴀᴍᴇ     : {username}\n"
        caption += f"• ɪᴅ       : {user_id}\n"
        caption += f"• ᴇʟɪxɪʀ   : {balance_amount:,} ᴇʟɪxɪʀ 💸\n"
        caption += f"• sᴀᴠɪɴɢs  : {saved_amount:,} 💾\n"
        caption += f"• ʟᴏᴀɴ     : {loan_amount:,} 📝\n"
        caption += f"• ᴛᴏᴛᴀʟ ᴡᴏʀᴛʜ : {total_worth:,} 💸\n"
        caption += "╰────────────────────╯\n"
        caption += "✦━═❖ ᴇɴᴊᴏʏ ʏᴏᴜʀ ʜᴜɴᴛ ❖═━✦"

        await message.reply_text(caption)
    else:
        # Create error message
        error_caption = "✦━═❖ ᴇʟɪxɪʀ ᴀᴄᴄᴏᴜɴᴛ ❖═━✦\n"
        error_caption += "╭────────────────────╮\n"
        error_caption += f"• ɴᴀᴍᴇ     : {username}\n"
        error_caption += f"• ɪᴅ       : {user_id}\n"
        error_caption += "• sᴛᴀᴛᴜs   : ɴᴏᴛ ʀᴇɢɪsᴛᴇʀᴇᴅ ⚠️\n"
        error_caption += "╰────────────────────╯\n"
        error_caption += "✦━═❖ ʀᴇɢɪsᴛᴇʀ ɪɴ ʙᴏᴛ ᴅᴍ ❖═━✦\n\n"
        error_caption += "ᴘʟᴇᴀsᴇ sᴛᴀʀᴛ ᴛʜᴇ ʙᴏᴛ ɪɴ ᴅᴍ ᴛᴏ ʀᴇɢɪsᴛᴇʀ."

        await message.reply_text(error_caption)
