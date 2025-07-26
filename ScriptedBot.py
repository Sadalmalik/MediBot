import re
import requests
from threading import Timer

from Evaluator import ExpressionEvaluator
from Telegram import TBot
from Scripting import ScriptableStateMachine, format_text


# Эвенты для стейт-машины сценария:
# start - старт ноды
# button - пользователь нажал кнопку
# message - пользователь прислал сообщение


class ScriptedBot:
    def __init__(self, bot_token: str, working_directory: str, script_path: str):
        self._eval = ExpressionEvaluator()

        self._bot = TBot(bot_token, working_directory=working_directory, use_sessions=True)
        self._bot.on_message(self.handle_telegram_message)
        self._bot.on_callback(self.handle_telegram_callback)
        self._bot.on_poll(self.handle_telegram_poll)

        self._script = ScriptableStateMachine(script_path)
        self._script.add_handler("end", ["start"], self.end_node_handler)
        self._script.add_handler("wait", ["start"], self.wait_node_handler)
        self._script.add_handler("message", ["start"], self.message_node_handler)
        self._script.add_handler("choice", ["start", "button"], self.choice_node_handler)
        self._script.add_handler("selection", ["start", "poll"], self.selection_node_handler)
        self._script.add_handler("range", ["start", "button"], self.range_node_handler)
        self._script.add_handler("input", ["start", "message"], self.input_node_handler)
        self._script.add_handler("condition", ["start"], self.condition_node_handler)
        self._script.add_handler("calculate", ["start"], self.calculation_node_handler)
        self._script.add_handler("send_form", ["start"], self.send_form_node_handler)

    def run(self):
        self._bot.cleanup_updates()
        for sid in self._bot.global_session['sessions']:
            context = self._bot.get_session(sid)
            self._script.init_context(context=context)
            # self._script.technical_event(context, "on_reload", "start", None)

            # restart timers in case bot was reloaded during some timers
            if "node" in context and context["node"]:
                if "waiting" in context:
                    del context["waiting"]
                    self._script.event(context, "start", None)

            # clear polls
            polls = self._bot.get_all_polls_from_chat(context["chat"]["id"])
            for data in polls:
                self._bot.stop_poll(context["chat"]["id"], data['message_id'])

        self._bot.run()

    # ------------------------------------------------------------------------------
    # region: Telegram bindings ----------------------------------------------------
    # ------------------------------------------------------------------------------

    def handle_telegram_message(self, message, session):
        self._script.init_context(context=session)
        text = message["text"].strip()
        if text.startswith("/"):
            command = text[1:].split()[0]
            if self._script.is_command_allowed(command):
                self._script.goto(session, command)
            else:
                self._script.technical_event(session, "unknown_command", "start", None)
        else:
            self._script.event(session, "message", text)

    def handle_telegram_callback(self, callback, session):
        self._script.init_context(context=session)
        data = callback["data"]
        self._script.event(session, "button", data)

    def handle_telegram_poll(self, poll, session):
        if poll['is_closed']:
            return
        self._script.init_context(context=session)
        self._script.event(session, "poll", poll)

    # ------------------------------------------------------------------------------
    # region: script nodes ---------------------------------------------------------
    # ------------------------------------------------------------------------------

    def event_delay(self, context, step, event, inner_handler):
        if "waiting" in context and context["waiting"]:
            print(f"Node already in waiting state! Can't handle '{event}' event!")
            return

        if event == "start" and "wait" in step:
            time = step["wait"]

            if isinstance(time, list):
                time, action = time
                self._bot.send_action(context["chat"]["id"], action)

            def on_timeout():
                del context["waiting"]
                inner_handler()
                self._bot.save_session(context["sid"])

            context["waiting"] = True
            t = Timer(float(time), on_timeout)
            t.start()
        else:
            inner_handler()

    def end_node_handler(self, runner, context, step, event, data):
        self._script.goto(context, None)

    def wait_node_handler(self, runner, context, step, event, data):
        if "waiting" in context and context["waiting"]:
            print("Waiting node already in waiting state!")
            return

        if step.get('show_status', False):
            self._bot.send_action(context["chat"]["id"], "typing")

        def on_timeout():
            del context["waiting"]
            self._script.goto(context, step["next"])

        context["waiting"] = True
        t = Timer(step["time"], on_timeout)
        t.start()

    def message_node_handler(self, runner, context, step, event, data):
        def handler():
            message = step["text"]
            chat_id = context["chat"]["id"]
            if 'chat_id' in step:
                chat_id = context["chat"]["id"]
            self._bot.send(chat_id, format_text(message, context))
            if "next" in step:
                self._script.goto(context, step["next"])
            else:
                print(f"Node {context['node']} has no next node!")

        self.event_delay(context, step, event, handler)

    def choice_node_handler(self, runner, context, step, event, value):
        def handler():
            text = format_text(step["text"], context)
            answers = step["answers"]
            if event == "start":
                message = self._bot.send_question(context["chat"]["id"], text, [answers])
                context["last_message_id"] = message["result"]["message_id"]
            elif event == "button":
                for answer in answers:
                    if answer[1] == value:
                        self._bot.edit_message(
                            context["chat"]["id"],
                            context["last_message_id"],
                            # TODO: хардкод - плохо. Надо в будущем думать над системами локализации ботов
                            f"{text.rstrip()}\n\nВаш ответ: {answer[0]}", None)
                        del context["last_message_id"]
                        self._script.goto(context, answer[1])
                        return

        self.event_delay(context, step, event, handler)

    def range_node_handler(self, runner, context, step, event, value):
        def handler():
            text = format_text(step["text"], context)
            if event == "start":
                message = self._bot.send_question(context["chat"]["id"], text, [step["values"]])
                context["last_message_id"] = message["result"]["message_id"]
            elif event == "button":
                result = int(value)
                context["variables"][step["variable"]] = result
                self._bot.edit_message(
                    context["chat"]["id"],
                    context["last_message_id"],
                    f"{text.rstrip()}\n\nВаш ответ: {result}", None)
                del context["last_message_id"]
                self._script.goto(context, step["next"])

        self.event_delay(context, step, event, handler)

    def selection_node_handler(self, runner, context, step, event, poll):
        def handler():
            if event == "start":
                text = format_text(step["text"], context)
                options = [option[0] for option in step['options']]
                multiple = step.get('multiple', False)
                message = self._bot.send_poll(context["chat"]["id"], text, options, multiple)
                context["last_message_id"] = message["result"]["message_id"]
            elif event == "poll":
                for poll_option in poll['options']:
                    text = poll_option['text']
                    count = poll_option['voter_count']
                    for option in step['options']:
                        if option[0] == text and option[1]:
                            var = option[1]
                            context["variables"][var] += count
                self._bot.stop_poll(poll['chat']['id'], poll['message_id'])
                self._script.goto(context, step["next"])

        self.event_delay(context, step, event, handler)

    def input_node_handler(self, runner, context, step, event, value: str):
        def handler():
            text = format_text(step["text"], context)
            if event == "start":
                message = self._bot.send(context["chat"]["id"], text)
                context["last_message_id"] = message["result"]["message_id"]
            elif event == "message":
                try:
                    result = None
                    variable = step["variable"]
                    var_type = self._script.get_variable_type(variable)
                    if var_type == "string":
                        result = value
                    elif var_type == "number":
                        m = re.findall(f'[\\d-]+(?:\\.[\\d-]){0,1}', value)
                        result = float(m[0])
                    elif var_type == "bool":
                        result = False
                        if value is True or value == "true" or value == "да" or value == "да":
                            result = True
                    context["variables"][variable] = result
                    del context["last_message_id"]
                    self._script.goto(context, step["next"])
                except Exception:
                    self._script.technical_event(context, 'cant_parse', 'start', None)
                    message = self._bot.send(context["chat"]["id"], text)
                    context["last_message_id"] = message["result"]["message_id"]

        self.event_delay(context, step, event, handler)

    def condition_node_handler(self, runner, context, step, event, value: str):
        def handler():
            for cond in step["conditions"]:
                result = self._eval(cond[0], context['variables'])
                if result:
                    self._script.goto(context, cond[1])
                    return
            self._script.goto(context, step["default"])

        self.event_delay(context, step, event, handler)

    def calculation_node_handler(self, runner, context, step, event, value: str):
        def handler():
            for expression in step["expressions"]:
                variable = expression[0]
                val = self._eval(expression[1], context['variables'])
                context["variables"][variable] = val

            self._script.goto(context, step["next"])

        self.event_delay(context, step, event, handler)

    def send_form_node_handler(self, runner, context, step, event, value: str):
        def handler():
            data = {}
            username = context["chat"]["username"]
            for item in step['form']:
                field, variable = item
                if variable == "@username":
                    data[field] = username
                else:
                    data[field] = context["variables"][variable]
            response = requests.post(step['url'], data=data)
            if response.status_code == 200:
                print(f"Form submitted successfully: {username}")
            else:
                print(f"Failed to submit form: {username}. Status code: {response.status_code}")
            self._script.goto(context, step["next"])

        self.event_delay(context, step, event, handler)

# end
