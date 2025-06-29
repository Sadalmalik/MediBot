from abc import ABC, abstractmethod

from ..TBot import TBot


class BaseHandler(ABC):
    def __init__(self):
        self.bot: TBot = None

    def set_bot(self, bot: TBot):
        self.bot = bot

    @abstractmethod
    def handle(self, message):
        pass



