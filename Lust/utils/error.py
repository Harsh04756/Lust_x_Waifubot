from functools import wraps
from telegram.ext import CallbackContext
from telegram import Update

def error(func):
    @wraps(func)
    async def wrapper(update: Update, context: CallbackContext, *args, **kwargs):
        try:
            return await func(update, context, *args, **kwargs)
        except Exception as e:
            error_message = f"An error occurred: {e}"
            if update.message:
                await update.message.reply_text(error_message, parse_mode='HTML')
            elif update.callback_query:
                await update.callback_query.message.reply_text(error_message, parse_mode='HTML')
            else:
                context.bot.logger.error(f"Unhandled error: {error_message}")
    return wrapper