from pyrogram import Client as PyrogramClient
from telegram.ext import Application
from motor.motor_asyncio import AsyncIOMotorClient
from resolve_peer import ResolvePeer
from .config import *

class Client(PyrogramClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def resolve_peer(self, id):
        obj = ResolvePeer(self)
        return await obj.resolve_peer(id)


application = Application.builder().token(TOKEN).build()
Lusts = Client(
    "Lust",
    api_id=api_id,
    api_hash=api_hash,
    bot_token=TOKEN)
app = Lusts
client = AsyncIOMotorClient(MONGO_URL)
db = client['Character_catcher']

# Your existing collections
collection = db['anime_characters']
user_totals_collection = db['user_totals']
user_collection = db["user_collection"]
safari_cooldown_collection = db['safari_cooldown_collection']
safari_users_collection = db['safari_users_collection']
group_user_totals_collection = db['group_user_total']
top_global_groups_collection = db['top_global_groups']
guild = db["guild_team"]
gban = db["gban"]
clan_collection = db['clans']
join_requests_collection = db['join_requests']
global_ban_users_collection = db['global_ban_users']
users_collection = db['user']
videos_collection = db['videos']
sales_collection = db['sales']
blocked_users_collection = db["blocked_users"]
locks_collection = db["locks_collection"]
velora_collection = db["velora_store"]
nightmode_collection = db["nightmode"]
warn_collection = db["warnusers"]
