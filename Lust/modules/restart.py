import os
import sys
import requests
import tempfile
from pyrogram import Client, filters
from pyrogram.types import Message
from . import capsify, app, dev_filter

@app.on_message(filters.command("gitpull") & dev_filter)
async def git_pull(client, message: Message):
    HEROKU_API_KEY = os.getenv('HEROKU_API_KEY')
    HEROKU_APP_NAME = os.getenv('HEROKU_APP_NAME')

    if not HEROKU_API_KEY or not HEROKU_APP_NAME:
        await message.reply_text(capsify("Heroku API key or app name not configured."))
        return

    headers = {
        'Authorization': f'Bearer {HEROKU_API_KEY}',
        'Accept': 'application/vnd.heroku.v3+json; version=3',  # Added version here
    }

    response = requests.post(
        f'https://api.heroku.com/apps/{HEROKU_APP_NAME}/builds',
        headers=headers,
        json={
            "source_blob": {
                "url": "https://git.heroku.com/pickgamebot.git",
                "version": "main"
            },
            "buildpacks": [{"url": "heroku/python"}]
        }
    )

    if response.status_code == 201:
        await message.reply_text(capsify("Git pull initiated successfully!"))
    else:
        await message.reply_text(capsify(f"Failed to initiate git pull: {response.status_code} - {response.text}"))

@app.on_message(filters.command("restart") & dev_filter)
async def restart_bot(client, message: Message):
    await message.reply_text(capsify("♻️ Restarting the bot..."))
    os.execv(sys.executable, ['python3'] + sys.argv)

@app.on_message(filters.command("logs") & dev_filter)
async def send_logs(client, message: Message):
    HEROKU_API_KEY = os.getenv('HEROKU_API_KEY')
    HEROKU_APP_NAME = os.getenv('HEROKU_APP_NAME')

    if not HEROKU_API_KEY or not HEROKU_APP_NAME:
        await message.reply_text(capsify("Heroku API key or app name not configured."))
        return

    headers = {
        'Authorization': f'Bearer {HEROKU_API_KEY}',
        'Accept': 'application/vnd.heroku.v3+json; version=3',  
    }

    response = requests.get(f'https://api.heroku.com/apps/{HEROKU_APP_NAME}/log-sessions', headers=headers)

    if response.status_code == 200:
        log_session_url = response.json().get("logplex_url")
        if log_session_url:
            logs_response = requests.get(log_session_url, headers=headers, stream=True)  
            logs_text = logs_response.text

            with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as temp_file:
                temp_file.write(logs_text.encode())
                temp_file_path = temp_file.name

            await message.reply_document(temp_file_path, caption=capsify("Here are the Heroku logs:"))
            os.remove(temp_file_path)
        else:
            await message.reply_text(capsify("Failed to retrieve log session URL."))
    else:
        await message.reply_text(capsify(f"Failed to retrieve logs: {response.status_code} - {response.text}"))