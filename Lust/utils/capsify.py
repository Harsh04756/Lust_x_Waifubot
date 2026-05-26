
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