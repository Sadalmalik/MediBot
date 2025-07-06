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
        os.makedirs(self._working_directory, exist_ok=True)

        if kwarg.get("use_sessions", False):
            self._session_manager = SessionsManager(folder=os.path.join(self._working_directory, "sessions"))
            self._global = self._session_manager.get_session("global")
            if "users" not in self._global:
                self._global["users"] = {}

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
            handler = ImagesHandler(folder=os.path.join(self._working_directory, "images"))
            handler.set_bot(self)
            self._handlers.append(handler)

        self._message_handler = None
        self._callback_handler = None
        self._update_handler = None
        self._after_messages_handled = None
        self._after_update = None

    @property
    def global_session(self):
        return self._global

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

    def send(self, chat_id, text):
        return self._call('sendMessage', {
            'chat_id': chat_id,
            'text': text
        })

    def senf_action(self, chat_id, action):
        return self._call('sendChatAction', {
            'chat_id': chat_id,
            'action': action
        })

    def send_question(self, chat_id, text, buttons):
        payload = {
            'chat_id': chat_id,
            'text': text
        }
        if buttons is not None:
            def prepare_button(button):
                if isinstance(button, str):
                    return {"text": button, "callback_data": button}
                elif isinstance(button, list):
                    return {"text": button[0], "callback_data": button[1]}
                elif isinstance(button, dict):
                    return button
                elif isinstance(button, int):
                    return {"text": str(button), "callback_data": button}
                else:
                    raise Exception(f"Unknown button format: {button}")
            keyboard = [[prepare_button(btn) for btn in line] for line in buttons]
            print(keyboard)
            payload["reply_markup"] = json.dumps({
                "inline_keyboard": keyboard
            })

        return self._call('sendMessage', payload)

    def edit_message(self, chat_id, message_id, text, buttons=None):
        payload = {
            'chat_id': chat_id,
            'message_id': message_id,
            'text': text
        }
        if buttons is not None:
            payload["reply_markup"] = json.dumps({
                "inline_keyboard": [[{"text": btn, "callback_data": btn} for btn in line] for line in buttons]
            })
        return self._call('editMessageText', payload)

    def edit_buttons(self, chat_id, message_id, buttons=None):
        payload = {
            'chat_id': chat_id,
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

    def save_session(self, sid):
        if self._session_manager is None:
            return
        self._session_manager.save_session(sid)

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
                    if "message" in update and self._message_handler is not None:
                        message = update["message"]
                        frames.add((message['from']['id'], message['chat']['id']))
                        for handler in self._handlers:
                            handler.handle(message)
                        user_id = message["from"]["id"]
                        if user_id not in self._global["users"]:
                            # Хз пока, какую глобальную дату о юзерах надо будет хранить кроме их айдишников
                            self._global["users"][user_id] = {}
                        session = self.get_session(user_id)
                        if "username" not in session:
                            session["username"] = message["from"]["username"]
                        self._message_handler(message, session)
                        self.save_session(user_id)
                    if "callback_query" in update and self._callback_handler is not None:
                        query = update["callback_query"]
                        user_id = query["from"]["id"]
                        if user_id not in self._global["users"]:
                            # Хз пока, какую глобальную дату о юзерах надо будет хранить кроме их айдишников
                            self._global["users"][user_id] = {}
                        session = self.get_session(user_id)
                        if "username" not in session:
                            session["username"] = query["from"]["username"]
                        self._callback_handler(query, session)
                        self.save_session(user_id)
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
