import os
import json
import tomllib
import tomli_w

from Telegram.TBot import TBot
from private.config import bot_token


# Эвенты для стейт-машины сценария:
# start - старт ноды
# button - пользователь нажал кнопку
# message - пользователь прислал сообщение

def main():
    bot = TBot(bot_token, download_path=os.path.abspath("private/downloads"), use_sessions=True)
    response = bot.send_question("820216855", "Выбери вариант ответа:", [["нет", "да"]])

    print(json.dumps(response, indent=2))

    def message_node_handler(runner, context, step, event, value):
        if step is None:
            return
        if "message" in step:
            bot.send(context["chat_id"], step["message"])

    def choice_node_handler(runner, context, step, event, value):
        if step is None:
            return
        if "choice" not in step:
            return
        choice = step["choice"]
        if event == "start":
            buttons = [answer[0] for answer in choice["answers"]]
            bot.send_question(context["chat_id"], choice["text"], [buttons])
        elif event == "button":
            for answer in choice["answers"]:
                if answer[0] == value:
                    runner.goto(context, answer[1])
                    return

    def input_node_handler(runner, context, step, event, value):
        if step is None:
            return
        if "input" not in step:
            return
        step_input = step["input"]
        if event == "start":
            bot.send(context["chat_id"], step_input["text"])
        elif event == "message":
            if "buttons" in step:
                for btn in step["buttons"]:
                    if btn[0] == value:
                        runner.goto(context, btn[1])
                        return



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


if __name__ == "__main__":
    # test_toml_conversion()
    main()
