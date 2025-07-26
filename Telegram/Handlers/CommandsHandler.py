import re

from .BaseHandler import BaseHandler


def _get_commands(message):
    commands = []
    if "text" in message and "entities" in message:
        text = message["text"]
        for entity in message["entities"]:
            if entity["type"] == "bot_command":
                args = re.split("/|[\r\n]+", text[entity["offset"] + entity["length"]:])[0].split(' ')
                args = [arg for arg in args if arg]
                command = {
                    "command": text[entity["offset"]:entity["offset"] + entity["length"]],
                    "args": args,
                    "entity": entity
                }
                commands.append(command)
    return commands


class CommandsHandler(BaseHandler):
    def __init__(self):
        super().__init__()
        self._command_handlers = {}
        self._undefined_command_handler = None

    def add_command(self, command, handler):
        self._command_handlers[command] = handler

    def on_command(self, command):
        def decorator(func):
            self._command_handlers[command] = func
        return decorator

    def on_undefined_command(self, func):
        if self._undefined_command_handler is not None:
            raise Exception("Undefined command handler already defined!")
        self._undefined_command_handler = func

    def handle(self, message: dict):
        commands = _get_commands(message)
        if "meta" not in message:
            message["meta"] = {}
        message["meta"]["commands"] = commands

        if len(self._command_handlers) == 0:
            return
        for command in commands:
            if command["command"] in self._command_handlers:
                self._command_handlers[command["command"]](command=command, message=message)
            elif self._undefined_command_handler is not None:
                self._undefined_command_handler(command=command, message=message)
            else:
                print(f"Unknown command:\n{command}\n")
                if self.bot is not None:
                    self.bot.send(message["chat"]["id"], command["command"])
