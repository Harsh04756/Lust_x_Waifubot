from Lust import db
from telegram import Update
from functools import wraps

devb = db.dev
disabledb = db.disabledb

async def is_enabled(module_name):
    module_state = await disabledb.find_one({"module_name": module_name})
    return not module_state or module_state.get("enabled", True)

def disable(module_name):
    def decorator(func):
        @wraps(func)
        async def wrapper(update: Update, context):
            if not await is_enabled(module_name):
                await update.message.reply_text(f"The module '{module_name}' is currently disabled.")
                return
            return await func(update, context)
        return wrapper
    return decorator
