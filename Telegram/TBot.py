import os
import json
import requests

from .Session import SessionsManager


class TBot:
    def __init__(self, token, **kwarg):
        self._token = token
        self._running = False
        self._update = kwarg.get("update", 0)
        self._timeout = kwarg.get("polling", 300)
        self._working_directory = kwarg.get("working_directory", "bot_folder")

        if kwarg.get("use_sessions", False):
            self._session_manager = SessionsManager(folder=os.path.join(self._working_directory, "sessions"))

        self._handlers = []
        self._command_handler = None
        if kwarg.get("use_commands", False):
            from .Handlers.CommandsHandler import CommandsHandler
            self._command_handler = CommandsHandler()
            self._command_handler.set_bot(self)
            self._handlers.append(self._command_handler)
        if kwarg.get("use_urls", False):
            from .Handlers.URLSHandler import URLSHandler
            handler = URLSHandler()
            handler.set_bot(self)
            self._handlers.append(handler)
        if kwarg.get("use_images", False):
            from .Handlers.ImagesHandler import ImagesHandler
            handler = ImagesHandler()
            handler.set_bot(self)
            self._handlers.append(handler)

        self._message_handler = None
        self._callback_handler = None
        self._update_handler = None
        self._after_messages_handled = None
        self._after_update = None

    # setup ========================================================================== #

    def on_message(self, func):
        if self._message_handler is not None:
            raise Exception("Message handler already defined!")
        self._message_handler = func

    def on_callback(self, func):
        if self._callback_handler is not None:
            raise Exception("Update handler already defined!")
        self._callback_handler = func

    def on_update(self, func):
        if self._update_handler is not None:
            raise Exception("Update handler already defined!")
        self._update_handler = func

    def on_batch(self, func):
        if self._after_messages_handled is not None:
            raise Exception("After Messages handler already defined!")
        self._after_messages_handled = func

    def on_command(self, command):
        if self._command_handler is None:
            raise Exception("Command handling not initialized! Please create bot with use_commands=true")
        return lambda func: self._command_handler.add_command(command, func)

    # internal ======================================================================= #

    def _call(self, method, data=None):
        response = requests.post(f"https://api.telegram.org/bot{self._token}/{method}", data=data)
        return response.json()

    # public API ===================================================================== #

    def send(self, chat, text):
        return self._call('sendMessage', {
            'chat_id': chat,
            'text': text
        })

    def send_question(self, chat, text, buttons):
        payload = {
            'chat_id': chat,
            'text': text
        }
        if buttons is not None:
            payload["reply_markup"] = json.dumps({
                "inline_keyboard": [[{"text": btn, "callback_data": btn} for btn in line] for line in buttons]
            })

        return self._call('sendMessage', payload)

    def edit_message(self, chat, message_id, text, buttons=None):
        payload = {
            'chat_id': chat,
            'message_id': message_id,
            'text': text
        }
        if buttons is not None:
            payload["reply_markup"] = json.dumps({
                "inline_keyboard": [[{"text": btn, "callback_data": btn} for btn in line] for line in buttons]
            })
        return self._call('editMessageText', payload)

    def edit_buttons(self, chat, message_id, buttons=None):
        payload = {
            'chat_id': chat,
            'message_id': message_id
        }
        if buttons is not None:
            payload["reply_markup"] = json.dumps({
                "inline_keyboard": [[{"text": btn, "callback_data": btn} for btn in line] for line in buttons]
            })
        return self._call('editMessageReplyMarkup', payload)

    def send_raw(self, message):
        return self._call('sendMessage', message)

    def get_file(self, file_id):
        return self._call('getFile', {"file_id": file_id})

    def get_session(self, sid):
        if self._session_manager is None:
            return None
        return self._session_manager.get_session(sid)

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
                    idx = update["update_id"]
                    if self._update <= idx:
                        self._update = idx + 1
                    print(f"Get update:\n{json.dumps(update, indent=2)}\n")
                    if "message" in update and self._message_handler is not None:
                        message = update["message"]
                        frames.add((message['from']['id'], message['chat']['id']))
                        for handler in self._handlers:
                            handler.handle(message)
                        session = self.get_session(message["from"]["id"])
                        self._message_handler(message, session)
                    if "callback_query" in update and self._callback_handler is not None:
                        query = update["callback_query"]
                        session = self.get_session(query["from"]["id"])
                        self._callback_handler(query, session)
                    elif self._update_handler is not None:
                        self._update_handler(update)

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
