from pymongo import ReturnDocument
from Lust import collection, user_collection

async def ac(user_id: int, character_id: int):
    try:
        character = await collection.find_one({'id': character_id})
        if not character:
            return

        await user_collection.find_one_and_update(
            {'id': user_id},
            {'$push': {'characters': character}},
            upsert=True,
            return_document=ReturnDocument.AFTER
        )
    except:
        pass

async def rc(user_id: int, character_id: int):
    try:
        await user_collection.find_one_and_update(
            {'id': user_id, 'characters.id': character_id},
            {'$pull': {'characters': {'id': character_id}}},
            return_document=ReturnDocument.AFTER
        )
    except:
        pass
