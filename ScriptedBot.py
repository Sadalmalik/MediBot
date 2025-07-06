from threading import Timer

from Evaluator import ExpressionEvaluator
from Telegram import TBot
from Scripting import ScriptableStateMachine, format_text


# Эвенты для стейт-машины сценария:
# start - старт ноды
# button - пользователь нажал кнопку
# message - пользователь прислал сообщение

class ScriptedBot:
    def __init__(self, bot_token: str, working_directory: str, script_path: str, force_admins: list[str]):
        self._eval = ExpressionEvaluator()

        self._bot = TBot(bot_token, working_directory=working_directory, use_sessions=True)
        self._bot.on_message(self.handle_telegram_message)
        self._bot.on_callback(self.handle_telegram_callback)

        for uid in force_admins:
            self._bot.global_session["users"][uid] = {"is_admin": True}
        self._script = ScriptableStateMachine(script_path)
        self._script.add_handler("end", ["start"], self.end_node_handler)
        self._script.add_handler("wait", ["start"], self.wait_node_handler)
        self._script.add_handler("message", ["start"], self.message_node_handler)
        self._script.add_handler("choice", ["start", "button"], self.choice_node_handler)
        self._script.add_handler("range", ["start", "button"], self.range_node_handler)
        self._script.add_handler("input", ["start", "message"], self.input_node_handler)
        self._script.add_handler("condition", ["start"], self.condition_node_handler)
        self._script.add_handler("calculate", ["start"], self.calculation_node_handler)
        self._script.add_handler("send_form", ["start"], self.send_node_handler())

    def run(self):
        for user in self._bot.global_session["users"]:
            user_session = self._bot.get_session(user)
            user_context = self._get_context(user_session)
            self._script.technical_event(user_context, "on_reload", "start", None)

            # restart timers in case bot was reloaded during some timers
            node = self._script[user_context["node"]]
            if "waiting" in user_context and node["type"] == "wait":
                del user_context["waiting"]
                self._script.event(user_context, "start", None)

        self._bot.run()

    # ------------------------------------------------------------------------------
    # region: Telegram bindings ----------------------------------------------------
    # ------------------------------------------------------------------------------

    def _get_context(self, session):
        if "context" not in session:
            context = self._script.create_context()
            session["context"] = context
            context["chat_id"] = session["sid"]
            context["username"] = session["username"]
        return session["context"]

    def handle_telegram_message(self, message, session):
        context = self._get_context(session)
        text = message["text"].strip()
        if text.startswith("/"):
            command = text[1:].split()[0]
            if self._script.is_command_allowed(command):
                self._script.goto(context, command)
            else:
                self._script.technical_event(context, "unknown_command", "start", None)
        else:
            self._script.event(context, "message", text)

    def handle_telegram_callback(self, callback, session):
        context = self._get_context(session)
        data = callback["data"]
        self._script.event(context, "button", data)

    # ------------------------------------------------------------------------------
    # region: script nodes ---------------------------------------------------------
    # ------------------------------------------------------------------------------

    def end_node_handler(self, runner, context, step, event, data):
        self._script.goto(context, None)

    def wait_node_handler(self, runner, context, step, event, data):
        if "waiting" in context and context["waiting"]:
            print("Waiting node already in waiting state!")
            return
        if event != "start":
            return

        if "show_status" in step and step["show_status"]:
            self._bot.senf_action("typing ")

        def on_timeout():
            del context["waiting"]
            self._script.goto(context, step["next"])

        context["waiting"] = True
        t = Timer(step["time"], on_timeout)
        t.start()

    def message_node_handler(self, runner, context, step, event, data):
        if event != "start":
            return

        message = step["text"]
        self._bot.send(context["chat_id"], format_text(message, context))
        self._script.goto(context, step["next"])

    def choice_node_handler(self, runner, context, step, event, value):
        text = format_text(step["text"], context)
        answers = step["answers"]
        if event == "start":
            message = self._bot.send_question(context["chat_id"], text, [answers])
            context["last_message_id"] = message["result"]["message_id"]
        elif event == "button":
            for answer in answers:
                if answer[1] == value:
                    self._bot.edit_message(context["chat_id"], context["last_message_id"], f"{text}\n\n-- {answer[0]}", None)
                    del context["last_message_id"]
                    self._script.goto(context, answer[1])
                    return

    def range_node_handler(self, runner, context, step, event, value):
        text = format_text(step["text"], context)
        if event == "start":
            message = self._bot.send_question(context["chat_id"], text, [step["values"]])
            context["last_message_id"] = message["result"]["message_id"]
        elif event == "button":
            result = int(value)
            context["variables"][step["variable"]] = result
            self._bot.edit_message(context["chat_id"], context["last_message_id"], f"{text}\n\n-- {result}", None)
            del context["last_message_id"]
            self._script.goto(context, step["next"])

    def input_node_handler(self, runner, context, step, event, value: str):
        text = format_text(step["text"], context)
        if event == "start":
            message = self._bot.send(context["chat_id"], text)
            context["last_message_id"] = message["result"]["message_id"]
        elif event == "message":
            result = None
            variable = step["variable"]
            var_type = self._script.get_variable_type(variable)
            if var_type == "string":
                result = value
            elif var_type == "number":
                result = float(value)
            elif var_type == "bool":
                result = bool(value)
            context["variables"][variable] = result
            del context["last_message_id"]
            self._script.goto(context, step["next"])

    def condition_node_handler(self, runner, context, step, event, value: str):
        if event != "start":
            return

        for cond in step["conditions"]:
            result = self._eval(cond[0])
            if result:
                self._script.goto(context, cond[1])
                return
        self._script.goto(context, step["default"])

    def calculation_node_handler(self, runner, context, step, event, value: str):
        if event != "start":
            return

        for expression in step["expressions"]:
            variable = expression[0]
            value = self._eval(expression[1])
            context["variables"][variable] = value

        self._script.goto(context, step["next"])

    def send_node_handler(self, runner, context, step, event, value: str):
        if event != "start":
            return

        self._script.goto(context, step["next"])

# end
