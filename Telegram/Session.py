import os
import datetime
import json


class SessionsManager:
    def __init__(self, **kwargs):
        self._sessions = {}
        self._memorytime = kwargs.get("memorytime", 60*10)
        self._folder = kwargs.get("folder", "sessions")
        if not os.path.exists(self._folder):
            os.makedirs(self._folder)

    def get_session(self, sid) -> dict:
        if sid in self._sessions:
            session = self._sessions[sid]
        else:
            file = os.path.join(self._folder, f"{sid}.json")
            if os.path.exists(file):
                with open(file, "r", encoding="utf8") as f:
                    data = json.load(f)
                session = {"data": data}
            else:
                session = {"data": {}}
            self._sessions[sid] = session
        session["time"] = datetime.datetime.now() + datetime.timedelta(seconds=self._memorytime)
        session["data"]["sid"] = sid
        return session["data"]

    def save_session(self, sid):
        if sid in self._sessions:
            session = self._sessions[sid]
            file = os.path.join(self._folder, f"{sid}.json")
            if os.path.exists(file):
                with open(file, "w", encoding="utf8") as f:
                    json.dump(session["data"], f, indent=2)

    def update(self):
        curr_time = datetime.datetime.now()
        items = list(self._sessions.items())
        for sid, session in items:
            if curr_time < session["time"]:
                continue
            file = os.path.join(self._folder, f"{sid}.json")
            if os.path.exists(file):
                with open(file, "w", encoding="utf8") as f:
                    json.dump(session["data"], f, indent=2)
            self._sessions[sid] = None
            del self._sessions[sid]

    def save_all(self, clear_cache=True):
        for sid, session in self._sessions.items():
            file = os.path.join(self._folder, f"{sid}.json")
            with open(file, "w", encoding="utf8") as f:
                json.dump(session["data"], f, indent=2)
        if clear_cache:
            self._sessions.clear()

# end of class
