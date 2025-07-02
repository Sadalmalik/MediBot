import json
from threading import Timer

from Scripting import toml


class ScriptableStateMachine:
    def __init__(self, script_file_path):
        with open(script_file_path, "r", encoding="utf8") as script_in:
            self._script = toml.load(script_in)
            self._nodes = self._script["node"]
        print(f"Script:\n\n{json.dumps(self._script, indent=2)}\n\n")
        self._handlers = []

    def create_context(self):
        variables = {}
        if "variables" in self._script:
            variables = self._script["variables"]
        return {
            "node": None,
            "variables": variables.copy() if variables is not None else dict()
        }

    def add_handler(self, priority, events, handler):
        self._handlers.append((priority, events, handler))
        self._handlers = sorted(self._handlers, key=lambda entry: entry[0])

    def __getitem__(self, node_id):
        if node_id in self._nodes:
            return self._nodes[node_id]
        return None

    def goto(self, context, node_id):
        step = self[node_id]
        if step is None:
            node_id = None
        context["node"] = node_id
        if node_id is None:
            return
        self.event(context, "start", None)

    def event(self, context, event, value):
        step = self[context["node"]]
        if step is None:
            print("Context has no step! use goto on context!")
            return
        for (order, events, handler) in self._handlers:
            if event in events:
                handler(self, context, step, event, value)
        if event == "start":
            self._handle_next(context, step, event, value)
            self._handle_end(context, step, event, value)

    def _handle_next(self, context, step, event, value):
        if step is None:
            return
        if "next" not in step:
            return
        if "wait" in step:
            t = Timer(step["wait"], lambda: self.goto(context, step["next"]))
            t.start()
        else:
            self.goto(context, step["next"])

    def _handle_end(self, context, step, event, value):
        if step is None:
            return
        if "end" not in step:
            return
        if step["end"]:
            self.goto(context, None)

