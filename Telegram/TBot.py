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

        self.use_sessions = kwarg.get("use_sessions", False)
        if self.use_sessions:
            self._session_manager = SessionsManager(folder=os.path.join(self._working_directory, "sessions"))
            global_session = self._session_manager.get_session("global")
            if "sessions" not in global_session:
                global_session["sessions"] = []
            if "polls" not in global_session:
                global_session["polls"] = {}

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
        self._poll_handler = None
        self._update_handler = None
        self._after_update = None

    @property
    def global_session(self):
        return self._session_manager.get_session("global")

    def save_global_session(self):
        self._session_manager.save_session("global")

    # setup ========================================================================== #

    def on_message(self, func):
        if self._message_handler is not None:
            raise Exception("Message handler already defined!")
        self._message_handler = func

    def on_callback(self, func):
        if self._callback_handler is not None:
            raise Exception("Callback handler already defined!")
        self._callback_handler = func

    def on_poll(self, func):
        if self._poll_handler is not None:
            raise Exception("Poll handler already defined!")
        self._poll_handler = func

    def on_update(self, func):
        if self._update_handler is not None:
            raise Exception("Update handler already defined!")
        self._update_handler = func

    def on_command(self, command):
        if self._command_handler is None:
            raise Exception("Command handling not initialized! Please create bot with use_commands=true")
        return lambda func: self._command_handler.add_command(command, func)

    # sessions ======================================================================= #

    def get_session(self, sid):
        if self._session_manager is None:
            return None
        if sid not in self.global_session["sessions"]:
            # Хз пока, какую глобальную дату о юзерах надо будет хранить кроме их айдишников
            self.global_session["sessions"].append(sid)
            self.save_global_session()
        session = self._session_manager.get_session(sid)
        if 'chat' not in session:
            info = self.get_chat(sid)
            session['chat'] = info
        return session

    def save_session(self, sid):
        if self._session_manager is None:
            return
        self._session_manager.save_session(sid)

    # internal ======================================================================= #

    def _call(self, method, data=None):
        response = requests.post(f"https://api.telegram.org/bot{self._token}/{method}", data=data)
        return response.json()

    # public API ===================================================================== #

    def get_chat(self, chat_id):
        response = self._call('getChat', {'chat_id': chat_id})
        if response['ok']:
            return response['result']
        return None

    def send(self, chat_id, text):
        return self._call('sendMessage', {
            'chat_id': chat_id,
            'text': text
        })

    def send_action(self, chat_id, action):
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

    def send_poll(self, chat_id, question, options, multiple_answers=False):
        payload = {
            'chat_id': chat_id,
            'question': question,
            'options': json.dumps([{'text': option} for option in options]),
            'allows_multiple_answers': multiple_answers
        }
        response = self._call('sendPoll', payload)
        if response['ok']:
            result = response['result']
            if self.global_session:
                poll_id = result['poll']['id']
                self.global_session['polls'][poll_id] = {
                    'message_id': result['message_id'],
                    'chat': result['chat'],
                    'poll': result['poll']
                }
                self.save_global_session()
        return response

    def stop_poll(self, chat_id, message_id):
        payload = {
            'chat_id': chat_id,
            'message_id': message_id
        }
        response = self._call('stopPoll', payload)
        if response['ok']:
            poll = response['result']
            del self.global_session['polls'][poll['id']]
        return response

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

    def edit_buttons(self, chat_id, message_id, buttons):
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

    def get_all_polls_from_chat(self, chat_id):
        result = []
        for poll_id, data in self.global_session['polls'].items():
            if chat_id == data['chat']['id']:
                data['poll_id'] = poll_id
                result.append(data)
        return result

    def cleanup_updates(self):
        data = self._call("getUpdates", {
            "offset": self._update,
            "timeout": self._timeout
        })
        for update in data["result"]:
            idx = update["update_id"]
            if self._update <= idx:
                self._update = idx + 1
        self._call("getUpdates", {
            "offset": self._update,
            "timeout": self._timeout
        })

    def run(self):
        data = self._call("deleteWebhook")
        print(data)

        self._running = True
        while self._running:
            data = self._call("getUpdates", {
                "offset": self._update,
                "timeout": self._timeout
            })
            if data["ok"] and data["result"] and len(data["result"]) > 0:
                for update in data["result"]:
                    idx = update["update_id"]
                    if self._update <= idx:
                        self._update = idx + 1
                    # print(f"update:\n{json.dumps(update, indent=2)}")
                    if "message" in update and self._message_handler is not None:
                        message = update["message"]
                        for handler in self._handlers:
                            handler.handle(message)
                        user_id = message["from"]["id"]
                        session = self.get_session(user_id)
                        self._message_handler(message, session)
                        self.save_session(user_id)
                    if "callback_query" in update and self._callback_handler is not None:
                        query = update["callback_query"]
                        user_id = query["from"]["id"]
                        session = self.get_session(user_id)
                        self._callback_handler(query, session)
                        self.save_session(user_id)
                    if "poll" in update:
                        poll = update["poll"]
                        session = None
                        if poll['id'] in self.global_session['polls']:
                            data = self.global_session['polls'][poll['id']]
                            # restore and bind poll to chat
                            poll['message_id'] = data['message_id']
                            poll['chat'] = data['chat']
                            session = self.get_session(poll['chat']['id'])
                        self._poll_handler(poll, session)
                        if poll['id'] in self.global_session['polls']:
                            self.save_session(poll['chat']['id'])
                    elif self._update_handler is not None:
                        self._update_handler(update)
            if self._after_update:
                self._after_update(self.global_session)
            self.save_global_session()
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
