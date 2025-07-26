import json


def format_text(text, context):
    if "variables" in context:
        variables = context["variables"]
        for key in variables.keys():
            text = text.replace(f"{{{key}}}", str(variables[key]))
    return text


class ScriptableStateMachine:
    def __init__(self, script_file_path, no_script=None):
        with open(script_file_path, "r", encoding="utf8") as script_in:
            self._script = json.load(script_in)
            self._nodes = self._script["node"]
            self._technical = self._script.get("technical", None) or {}
        # print(f"Script:\n\n{json.dumps(self._script, indent=2)}\n\n")
        self._handlers = {}
        self._no_script = no_script

    def init_context(self, **kwargs):
        context = kwargs.get("context", None) or {}
        variables = context.get("variables", None) or {}
        if "variables" in self._script:
            for var, var_type in self._script["variables"].items():
                if var not in variables:
                    if var_type == "string":
                        variables[var] = ''
                    if var_type == "number":
                        variables[var] = 0
                    if var_type == "bool":
                        variables[var] = False
        context['variables'] = variables
        if "node" not in context:
            context['node'] = None
        return context

    def validate_variables_context(self, context):
        variables = context['variables']
        if "variables" in self._script:
            for var, var_type in self._script["variables"].items():
                if var not in variables:
                    if var_type == "string":
                        variables[var] = ''
                    if var_type == "number":
                        variables[var] = 0
                    if var_type == "bool":
                        variables[var] = False

    def get_variable_type(self, variable):
        return self._script["variables"][variable]

    def add_handler(self, node_type: str, events, handler):
        if node_type in self._handlers:
            raise Exception(f"There can be only one handler for node type! But you trying add another one for '{node_type}'")
        self._handlers[node_type] = (events, handler)

    def __getitem__(self, node_id):
        if node_id in self._nodes:
            return self._nodes[node_id]
        print(f"node not found: {node_id}")
        return None

    def is_command_allowed(self, command: str):
        return command in self._script["commands"]

    def _call_event(self, context, node, event, data):
        if node is None:
            if "on_no_script" in self._technical:
                node = self._technical["on_no_script"]
            else:
                print("Context has no step! use goto on context!")
                return
        if "type" not in node:
            raise Exception("Node must contain type!")
        node_type = node["type"]
        if node_type not in self._handlers:
            raise Exception(f"No handlers defined for '{node_type}'")
        events, handler = self._handlers[node_type]
        if event in events:
            # try:
                handler(self, context, node, event, data)
            # except Exception as e:
            #     print(f"Exception in handler: {node_type}\n{e}")

    def goto(self, context, node_id):
        node = self[node_id]
        if node is None:
            node_id = None
        context["node"] = node_id
        if node_id is None:
            return
        self.event(context, "start", None)

    def event(self, context, event, data):
        node_id = context["node"]
        if node_id is None:
            node_id = self._no_script
        node = self[node_id]
        self._call_event(context, node, event, data)

    def technical_event(self, context, node_id, event, data):
        node = self._technical[node_id]
        self._call_event(context, node, event, data)
