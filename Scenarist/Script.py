import json
import time
from threading import Timer

import toml


class ScriptRunner:
    def __init__(self, scenario_path):
        with open(scenario_path, "r", encoding="utf8") as script_in:
            self._script = toml.load(script_in)
        print(f"Script:\n\n{json.dumps(self._script, indent=2)}\n\n")
        self._handlers = []

    def create_context(self):
        variables = {}
        if "variables" in self._script:
            variables = self._script["variables"]
        return {
            "step": None,
            "variables": variables.copy() if variables is not None else dict()
        }

    def get_step(self, step_id):
        if step_id in self._script["node"]:
            return self._script["node"][step_id]
        return None

    def goto_step(self, context, step_id):
        step = self.get_step(step_id)
        if step is None:
            step_id = None
        context["step"] = step_id
        if step_id is None:
            return
        self.run_event(context, "start", None)

    def add_handler(self, priority, events, handler):
        self._handlers.append((priority, events, handler))
        self._handlers = sorted(self._handlers, key=lambda entry: entry[0])

    def run_event(self, context, event, content):
        step = self.get_step(context["step"])
        if step is None:
            print("Context has no step! use goto on context!")
            return
        for (order, events, handler) in self._handlers:
            if event in events:
                handler(self, context, step, event, content)
        if event == "start":
            self._handle_next(context, step, event, content)
            self._handle_end(context, step, event, content)

    def _handle_next(self, context, step, event, content):
        if step is None:
            return
        if "next" not in step:
            return
        if "wait" in step:
            t = Timer(step["wait"], lambda: self.goto_step(context, step["next"]))
            t.start()
        else:
            self.goto_step(context, step["next"])

    def _handle_end(self, context, step, event, content):
        if step is None:
            return
        if "end" not in step:
            return
        if step["end"]:
            self.goto_step(context, None)


# test sample

def message_handler(runner: ScriptRunner, context, step, event, content):
    if step is None:
        return
    print(step["message"])


def question_handler(runner: ScriptRunner, context, step, event, content):
    if step is None:
        return
    if "buttons" not in step:
        return
    if event == "choice":
        for btn in step["buttons"]:
            if btn[0] == content:
                runner.goto_step(context, btn[1])
                return
    elif event == "start":
        for btn in step["buttons"]:
            print(f"  - {btn[0]} :: {btn[1]}")


def main():
    # c:no
    sr = ScriptRunner("../Script/bot_script_test.toml")
    sr.add_handler(10, ["start"], message_handler)
    sr.add_handler(20, ["start", "choice"], question_handler)
    dialogue = sr.create_context()
    sr.goto_step(dialogue, "start")
    while dialogue["step"] is not None:
        user_input = input()
        event = "message"
        if user_input.startswith("m:"):
            user_input = user_input[2:]
        elif user_input.startswith("c:"):
            user_input = user_input[2:]
            event = "choice"
        sr.run_event(dialogue, event, user_input)
    print("Цикл завершен!")
    sr.run_event(dialogue, "message", "test")


if __name__ == "__main__":
    main()
