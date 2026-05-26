import importlib
import time
import re
import asyncio
from telegram import Update
from telegram.ext import CommandHandler, CallbackContext, MessageHandler, filters

from Lust import collection, Lusts, top_global_groups_collection, group_user_totals_collection, user_collection, user_totals_collection
from Lust import application, app, db
from Lust.modules import ALL_MODULES

try:
    from Lust.modules import nightmode
    if hasattr(nightmode, 'initialize_nightmode'):
        nightmode.initialize_nightmode()
        print("✅ Night Mode scheduler initialized")
except ImportError:
    print("⚠️  Night Mode module not found")

for module_name in ALL_MODULES:
    imported_module = importlib.import_module("Lust.modules." + module_name)
    print(f"✅ Loaded module: {module_name}")

def escape_markdown(text):
    escape_chars = r'\*_`\\~>#+-=|{}.!'
    return re.sub(r'([%s])' % re.escape(escape_chars), r'\\\1', text)


def main() -> None:
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    if Lusts:
        Lusts.start()
    
    print('🤖 Bot Starting...')
    
    async def startup_tasks():
        print("✅ Startup tasks completed")
    
    loop = asyncio.get_event_loop()
    if loop.is_running():
        asyncio.create_task(startup_tasks())
    else:
        loop.run_until_complete(startup_tasks())
    
    print('✅ Bot Started Successfully')
    main()
