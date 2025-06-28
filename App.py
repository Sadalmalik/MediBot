import os
import json
import tomllib
import tomli_w

from Telegram.TBot import TBot, get_urls
from private.config import bot_token


def main():

    with open("Script/test_script.json", "r", encoding="utf8") as script_in:
        script = json.load(script_in)

    with open("Script/test_script.toml", "wb") as script_out:
        tomli_w.dump(script, script_out)

    with open("Script/test_script.toml", "rb") as script_in:
        script = tomllib.load(script_in)

    with open("Script/test_script-2.json", "w") as script_out:
        json.dump(script, script_out, indent=2)

    return
    bot = TBot(bot_token, download_path=os.path.abspath("private/downloads"))
    response = bot.send({
        'chat_id': "820216855",
        'text': "Выбери вариант ответа:",
        'reply_markup': json.dumps({
            "inline_keyboard": [
                [
                    {"text": "нет", "callback_data": "нет"},
                    {"text": "да", "callback_data": "да"}
                ]
            ]
        })
    })

    print(json.dumps(response, indent=2))

    @bot.on_message
    def handler(message):
        print(json.dumps(message, indent=2))

    bot.run()


if __name__ == "__main__":
    main()
