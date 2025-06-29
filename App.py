import os
import json
import tomllib
import tomli_w

from Telegram.TBot import TBot
from private.config import bot_token
from Scenarist import ScriptRunner


def main():
    bot = TBot(bot_token, download_path=os.path.abspath("private/downloads"))
    response = bot.send_question("820216855", "Выбери вариант ответа:", [["нет", "да"]])

    print(json.dumps(response, indent=2))

    @bot.on_message
    def handle_message(message):
        print(json.dumps(message, indent=2))

    @bot.on_callback
    def handle_callback(callback):
        data = callback["data"]
        chat_id = callback["message"]["chat"]["id"]
        message_id = callback["message"]["message_id"]
        text = callback["message"]["text"]
        bot.edit_message(chat_id, message_id, f"{text}\n\nВаш ответ: {data}", None)

    bot.run()


def test_toml_conversion():
    with open("Script/test_script.json", "r", encoding="utf8") as script_in:
        script = json.load(script_in)

    with open("Script/test_script.toml", "wb") as script_out:
        tomli_w.dump(script, script_out)

    with open("Script/test_script.toml", "rb") as script_in:
        script = tomllib.load(script_in)

    with open("Script/test_script-2.json", "w") as script_out:
        json.dump(script, script_out, indent=2)


def test_script_runner():
    runner = ScriptRunner("Script/bot_script.toml")
    context = runner.create_context()
    print(context)


if __name__ == "__main__":
    test_script_runner()
    # test_toml_conversion()
    # main()
