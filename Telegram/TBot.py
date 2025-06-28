import os
import re
import requests
from abc import abstractmethod, ABC


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


def get_urls(message):
    urls = []
    if "text" in message and "entities" in message:
        text = message["text"]
        for entity in message["entities"]:
            if entity["type"] != "url":
                continue
            urls.append(text[entity["offset"]:entity["offset"] + entity["length"]])
    return urls


class MessageHandler(ABC):
    @abstractmethod
    def handle(self, message):
        pass


class TBot:
    def __init__(self, token, **kwarg):
        self._token = token
        self._running = False
        self._update = kwarg.get("update", 0)
        self._timeout = kwarg.get("polling", 300)
        self._download_path = kwarg.get("download_path", "downloads")
        self._command_handlers = {}
        self._undefined_command_handler = None
        self._message_handler = None
        self._photo_handler = None
        self._photo_complete_handler = None
        self._after_messages_handled = None
        self._after_update = None

    def _call(self, method, data=None):
        response = requests.post(f"https://api.telegram.org/bot{self._token}/{method}", data=data)
        return response.json()

    def _download_file(self, file, message):
        if "file_path" not in file:
            return None
        r = requests.get(f"https://api.telegram.org/file/bot{self._token}/{file["file_path"]}", allow_redirects=True)
        fname = os.path.basename(file["file_path"])
        fpath = f"{self._download_path}/m{message["message_id"]}_{fname}"
        folder = os.path.dirname(fpath)
        if not os.path.exists(folder):
            os.makedirs(folder)
        with open(fpath, 'wb') as file:
            file.write(r.content)
        return fpath

    def _download_all_photo(self, message):
        files = {}
        for photo in message["photo"]:
            result = self._call("getFile", {"file_id": photo["file_id"]})
            if result["ok"]:
                file = result["result"]
                files[file["file_id"]] = file
        result = []
        for uid, file in files.items():
            file["local_path"] = self._download_file(file, message)
            result.append(file)
        return result

    def _handle_photo(self, message):
        if "photo" not in message:
            return
        photos = self._download_all_photo(message)
        if len(photos) == 0:
            return
        if self._photo_handler:
            for file in photos:
                self._photo_handler(message, file)
        if self._photo_complete_handler:
            self._photo_complete_handler(message, photos)

    def _handle_commands(self, message):
        commands = _get_commands(message)
        if len(self._command_handlers) == 0:
            return
        for command in commands:
            if command["command"] in self._command_handlers:
                self._command_handlers[command["command"]](command=command, message=message)
            elif self._undefined_command_handler is not None:
                self._undefined_command_handler(command=command, message=message)
            else:
                print(f"Unknown command:\n{command}\n")
                self.send({
                    'chat_id': message["chat"]["id"],
                    'text': f"Unknown command: {command["command"]}"
                })

    def _handle_message(self, message):
        self._handle_photo(message)
        self._handle_commands(message)
        self._message_handler(message)

    def on_command(self, command):
        def decorator(func):
            self._command_handlers[command] = func

        return decorator

    def on_undefined_command(self, func):
        if self._undefined_command_handler is not None:
            raise Exception("Undefined command handler already defined!")
        self._undefined_command_handler = func

    def on_photo(self, func):
        if self._photo_handler is not None:
            raise Exception("Photo handler already defined!")
        self._photo_handler = func

    def on_photos_handled(self, func):
        if self._photo_complete_handler is not None:
            raise Exception("Photo complete handler already defined!")
        self._photo_complete_handler = func

    def on_message(self, func):
        if self._message_handler is not None:
            raise Exception("Message handler already defined!")
        self._message_handler = func

    def on_messages_handled(self, func):
        if self._after_messages_handled is not None:
            raise Exception("After Messages handler already defined!")
        self._after_messages_handled = func

    def on_update(self, func):
        if self._after_update is not None:
            raise Exception("Update handler already defined!")
        self._after_update = func

    def send(self, message):
        return self._call('sendMessage', message)

    def run(self):
        data = self._call("deleteWebhook")
        print(data)

        self._running = True
        while self._running:
            data = self._call("getUpdates", {
                "offset": self._update,
                "timeout": self._timeout
            })
            frames = set()
            if data["ok"] and data["result"] and len(data["result"]) > 0:
                for update in data["result"]:
                    message = update["message"]
                    idx = update["update_id"]
                    if self._update <= idx:
                        self._update = idx + 1
                    frames.add((message['from']['id'], message['chat']['id']))
                    self._handle_message(message)
            if self._after_messages_handled:
                for frame in frames:
                    self._after_messages_handled({
                        "from": frame[0],
                        "chat": frame[1]
                    })
            if self._after_update:
                self._after_update()

        print("Bot polling complete")

    def stop(self, skip_last_message=True):
        if self._running:
            self._running = False
            if skip_last_message:
                # Just sending last message ID so bot won't read stop message again
                self._call("getUpdates", {
                    "offset": self._update,
                    "timeout": 0
                })
        else:
            raise Exception("Can't stop bot - it's not running!")
