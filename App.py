import os

from ScriptedBot import ScriptedBot
from private import config


def main():
    bot = ScriptedBot(
        config.bot_token,
        working_directory=os.path.abspath("private/bot"),
        script_path="Script/bot_script_test_2.toml",
        force_admins=config.admins)
    bot.run()


if __name__ == "__main__":
    main()
