import os
import json
import tomllib
import tomli_w

from Scripting import ScriptableStateMachine, format_text
from Telegram.TBot import TBot
from private.config import bot_token


# Эвенты для стейт-машины сценария:
# start - старт ноды
# button - пользователь нажал кнопку
# message - пользователь прислал сообщение

def main():
    bot = TBot(bot_token, download_path=os.path.abspath("private/downloads"), use_sessions=True)
    bot.global_session["users"]["820216855"] = {"is_admin": True}

    # response = bot.send_question("820216855", "Выбери вариант ответа:", [["нет", "да"]])
    #
    # print(json.dumps(response, indent=2))

    def message_node_handler(runner, context, step, event, value):
        if step is None:
            return
        if "message" not in step:
            return
        step_message = step["message"]
        if event == "start":
            bot.send(context["chat_id"], format_text(step_message, context))

    def choice_node_handler(runner, context, step, event, value):
        if step is None:
            return
        if "choice" not in step:
            return
        choice = step["choice"]
        text = format_text(choice["text"], context)
        if event == "start":
            message = bot.send_question(context["chat_id"], text, [choice["answers"]])
            context["last_message_id"] = message["result"]["message_id"]
        elif event == "button":
            for answer in choice["answers"]:
                if answer[1] == value:
                    bot.edit_message(context["chat_id"], context["last_message_id"], f"{text}\n\n-- {answer[0]}", None)
                    del context["last_message_id"]
                    runner.goto(context, answer[1])
                    return

    def range_node_handler(runner, context, step, event, value):
        if step is None:
            return
        if "range" not in step:
            return
        step_range = step["range"]
        text = format_text(step_range["text"], context)
        if event == "start":
            message = bot.send_question(context["chat_id"], text, [step_range["values"]])
            context["last_message_id"] = message["result"]["message_id"]
        elif event == "button":
            result = int(value)
            context["variables"][step_range["variable"]] = result
            bot.edit_message(context["chat_id"], context["last_message_id"], f"{text}\n\n-- {result}", None)
            del context["last_message_id"]
            runner.goto(context, step_range["next"])

    def input_node_handler(runner, context, step, event, value):
        if step is None:
            return
        if "input" not in step:
            return
        step_input = step["input"]
        text = format_text(step_input["text"], context)
        if event == "start":
            message = bot.send(context["chat_id"], text)
            context["last_message_id"] = message["result"]["message_id"]
        elif event == "message":
            result = None
            var_type = step_input["type"]
            if var_type == "string":
                result = value
            elif var_type == "number":
                result = float(value)
            elif var_type == "bool":
                result = value in ["true", "True", "yes", "Yes", "да", "Да"]
            context["variables"][step_input["variable"]] = result
            del context["last_message_id"]
            runner.goto(context, step_input["next"])

    sr = ScriptableStateMachine("Script/bot_script_test.toml")
    sr.add_handler(10, ["start"], message_node_handler)
    sr.add_handler(20, ["start", "button"], choice_node_handler)
    sr.add_handler(30, ["start", "button"], range_node_handler)
    sr.add_handler(40, ["start", "message"], input_node_handler)

    def get_context(session):
        if "context" not in session:
            session["context"] = sr.create_context()
        return session["context"]

    @bot.on_message
    def handle_message(message, session):
        context = get_context(session)
        sr.event(context, "message", message["text"])

    @bot.on_callback
    def handle_callback(callback, session):
        context = get_context(session)
        data = callback["data"]
        sr.event(context, "button", data)

    for user in bot.global_session["users"]:
        user_session = bot.get_session(user)
        user_context = get_context(user_session)
        sr.technical_event(user_context, "on_reload", "start", None)

    bot.run()


if __name__ == "__main__":
    # test_toml_conversion()
    main()
