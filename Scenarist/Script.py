from . import toml
import json


class ScriptRunner:
    def __init__(self, scenario_path):
        with open(scenario_path, "r", encoding="utf8") as script_in:
            self.script = toml.load(script_in)

    def create_context(self):
        variables: dict = self.script["variables"]
        return {
            "step": None,
            "variables": variables.copy()
        }

    def run_command(self, context, command):
        pass

    def run_event(self, context, event):
        pass


