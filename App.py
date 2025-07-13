import os
import json
import requests

from ScriptedBot import ScriptedBot
from private import config

from Scripting import toml
from Telegram import TBot


def main():
    bot = ScriptedBot(
        config.bot_token,
        working_directory=os.path.abspath("private/bot"),
        script_path="Script/release_bot.toml")
    bot.run()


def cleanup():
    bot = TBot(config.bot_token, use_sessions=True)
    bot.cleanup_updates()


# <div jsname="o6bZLc">
# <input type="hidden" name="entry.2049190339" value="">
# <input type="hidden" name="entry.1909510680" value="">
# <input type="hidden" name="entry.210876095" value="">
# <input type="hidden" name="entry.1883094476" value="">
# <input type="hidden" name="entry.1253864560" value="">
# <input type="hidden" name="entry.289557824" value="">
# <input type="hidden" name="entry.2127535516" value="">
# <input type="hidden" name="entry.1224265442" value="">
# <input type="hidden" name="entry.2059824086" value="">
# <input type="hidden" name="entry.267514677" value="">
# <input type="hidden" name="entry.1771178035" value="">
# <input type="hidden" name="entry.1945850213" value="">
# <input type="hidden" name="entry.2036286477" value="">
# </div>

# <div jsname="o6bZLc">
# <input type="hidden" name="entry.893737562" value="имя">
# <input type="hidden" name="entry.1849799186" value="2">
# <input type="hidden" name="entry.1947250325" value="3">
# <input type="hidden" name="entry.1729075448" value="3">
# <input type="hidden" name="entry.855973916" value="3">
# <input type="hidden" name="entry.414445729" value="3">
# <input type="hidden" name="dlut" value="1752419877012">
# </div>

def send_form():
    url = "https://docs.google.com/forms/u/0/d/e/1FAIpQLSeZ-WPyFGLOEZUZ92iM3SYWIJ9odi8p0bwNxO5R5dhjLLB9qQ/formResponse"
    data = {
        "entry.893737562": "kaleb_sadalmalik",
        "entry.1849799186": "1",
        "entry.1947250325": "2",
        "entry.1729075448": "3",
        "entry.855973916": "4",
        "entry.414445729": "5"
    }
    response = requests.post(url, data=data)
    print(response)
    if response.status_code == 200:
        print("Form submitted successfully!")
    else:
        print(f"Failed to submit form. Status code: {response.status_code}")


if __name__ == "__main__":
    # send_form()
    cleanup()
    main()
