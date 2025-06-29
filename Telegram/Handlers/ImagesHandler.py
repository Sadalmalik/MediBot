import requests

from .BaseHandler import BaseHandler


class ImagesHandler(BaseHandler):
    def __init__(self):
        super().__init__()
        self._photo_handler = None
        self._photo_complete_handler = None

    def on_photo(self, func):
        if self._photo_handler is not None:
            raise Exception("Photo handler already defined!")
        self._photo_handler = func

    def on_photos_handled(self, func):
        if self._photo_complete_handler is not None:
            raise Exception("Photo complete handler already defined!")
        self._photo_complete_handler = func

    def handle(self, message):
        if "photo" not in message:
            return
        photos = self._download_all_photo(message)
        if len(photos) == 0:
            return
        if "meta" not in message:
            message["meta"] = {}
        message["meta"]["photos"] = photos
        if self._photo_handler:
            for file in photos:
                self._photo_handler(message, file)
        if self._photo_complete_handler:
            self._photo_complete_handler(message, photos)

    def _download_all_photo(self, message):
        files = {}
        for photo in message["photo"]:
            result = self.bot.get_file(photo["file_id"])
            if result["ok"]:
                file = result["result"]
                files[file["file_id"]] = file
        result = []
        for uid, file in files.items():
            file["local_path"] = self._download_file(file, message)
            result.append(file)
        return result

    def _download_file(self, file, message):
        if "file_path" not in file:
            return None
        r = requests.get(f"https://api.telegram.org/file/bot{self.bot._token}/{file["file_path"]}",
                         allow_redirects=True)
        fname = os.path.basename(file["file_path"])
        fpath = f"{self._download_path}/m{message["message_id"]}_{fname}"
        folder = os.path.dirname(fpath)
        if not os.path.exists(folder):
            os.makedirs(folder)
        with open(fpath, 'wb') as file:
            file.write(r.content)
        return fpath
