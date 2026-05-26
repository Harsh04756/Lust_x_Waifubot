import random
import sys
import time
from Lust import *
from functools import wraps
from telegram import Update
from Lust.utils import * 
from .watchers import *

StartTime = time.time()

sudb = db.sudo
devb = db.dev 
app = Lusts

dev_users = {6919722801}

ALPHABETS = "abcdefghijklmnopqrstuvwxyz"
ALL_CAPS = "ᴀʙᴄᴅᴇғɢʜɪᴊᴋʟᴍɴᴏᴘǫʀsᴛᴜᴠᴡxʏᴢ"

def capsify(text: str) -> str:
    txt = ""
    for x in text:
        if x == '\n':
            txt += '\n'
        elif x == ' ':
            txt += ' '
        else:
            if x.lower() in ALPHABETS:
                ind = ALPHABETS.index(x.lower())
                txt += ALL_CAPS[ind]
            else:
                txt += x
    return txt

async def acapsify(text: str) -> str:
    return capsify(text)

async def get_price(id: int):
    character = await collection.find_one({'id': id})
    if character:
        return character.get('price')
    return None

async def get_character(id: int):
    return await collection.find_one({
        'id': id,
        'rarity': {'$nin': ['💋 Aura', '❄️ Winter']}  
    })

async def get_character_ids() -> list:
    all_characters = await collection.find({
        'rarity': {'$nin': ['💋 Aura', '❄️ Winter']}  
    }).to_list(length=None)
    return [x['id'] for x in all_characters]

async def get_image_and_caption(id: int):
    char = await get_character(id)
    if not char:
        raise ValueError(f"Character with ID {id} not found or is excluded")

    price = await get_price(id)
    form = 'ɴᴀᴍᴇ : {}\n\nᴀɴɪᴍᴇ : {}\n\nɪᴅ: {}\n\nᴘʀɪᴄᴇ : {} coins\n'
    return char['img_url'], capsify(form.format(char['name'], char['anime'], char['id'], price))

# if version < 3.6, stop bot.
if sys.version_info[0] < 3 or sys.version_info[1] < 6:
    print(
        "You MUST have a python version of at least 3.6! Multiple features depend on this. Bot quitting."
    )
    quit(1)

LOAD = []
NO_LOAD = []

def __list_all_modules():
    import glob
    from os.path import basename, dirname, isfile

    mod_paths = glob.glob(dirname(__file__) + "/*.py")
    all_modules = [
        basename(f)[:-3]
        for f in mod_paths
        if isfile(f) and f.endswith(".py") and not f.endswith("__init__.py")
    ]

    if LOAD or NO_LOAD:
        to_load = LOAD
        if to_load:
            if not all(
                any(mod == module_name for module_name in all_modules)
                for mod in to_load
            ):
                print("Invalid loadorder names, Quitting...")
                quit(1)

            all_modules = sorted(set(all_modules) - set(to_load))
            to_load = list(all_modules) + to_load

        else:
            to_load = all_modules

        if NO_LOAD:
            print("Not loading: {}".format(NO_LOAD))
            return [item for item in to_load if item not in NO_LOAD]

        return to_load

    return all_modules

async def get_group_spawn_limit(chat_id):
    group_data = await db.groups.find_one({"chat_id": chat_id}, {"spawn_limit": 1})
    return group_data['spawn_limit'] if group_data and 'spawn_limit' in group_data else None

async def set_group_spawn_limit(chat_id, limit):
    await db.groups.update_one({"chat_id": chat_id}, {"$set": {"spawn_limit": limit}}, upsert=True)

ALL_MODULES = __list_all_modules()
print("Modules to load: %s", str(ALL_MODULES))
__all__ = ALL_MODULES + ["ALL_MODULES"]
