import json
from threading import Timer

from Scripting import toml


def format_text(text, context):
    if "variables" in context:
        variables = context["variables"]
        for key in variables.keys():
            text = text.replace(f"{{{key}}}", variables[key])
    return text


class ScriptableStateMachine:
    def __init__(self, script_file_path):
        with open(script_file_path, "r", encoding="utf8") as script_in:
            self._script = toml.load(script_in)
            self._nodes = self._script["node"]
            self._technical = self._script["technical"]
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

    def _call_event(self, context, node, event, data):
        if node is None:
            if "on_no_script" in self._technical:
                node = self._technical["on_no_script"]
            else:
                print("Context has no step! use goto on context!")
                return
        for (order, events, handler) in self._handlers:
            if event in events:
                handler(self, context, node, event, data)
        if event == "start":
            self._handle_next(context, node, event, data)
            self._handle_end(context, node, event, data)

    def goto(self, context, node_id):
        step = self[node_id]
        if step is None:
            node_id = None
        context["node"] = node_id
        if node_id is None:
            return
        self.event(context, "start", None)

    def event(self, context, event, data):
        node = self[context["node"]]
        self._call_event(context, node, event, data)

    def technical_event(self, context, node_id, event, data):
        node = self._technical[node_id]
        self._call_event(context, node, event, data)

    def _handle_next(self, context, step, event, data):
        if step is None:
            return
        if "next" not in step:
            return
        if "wait" in step:
            t = Timer(step["wait"], lambda: self.goto(context, step["next"]))
            t.start()
        else:
            self.goto(context, step["next"])

    def _handle_end(self, context, step, event, data):
        if step is None:
            return
        if "end" not in step:
            return
        if step["end"]:
            self.goto(context, None)

