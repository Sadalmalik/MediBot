from .BaseHandler import BaseHandler


class URLSHandler(BaseHandler):
    def handle(self, message):
        urls = []
        if "text" in message and "entities" in message:
            text = message["text"]
            for entity in message["entities"]:
                if entity["type"] != "url":
                    continue
                urls.append(text[entity["offset"]:entity["offset"] + entity["length"]])

        if "meta" not in message:
            message["meta"] = {}
        message["meta"]["urls"] = urls
