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

def send_form():
    form_url = "YOUR_GOOGLE_FORM_SUBMISSION_URL"  # Found in the form's HTML action attribute
    data = {
        "entry.123456789": "Your Name",  # Replace with actual entry IDs
        "entry.987654321": "Your Answer",
        # Add more entries for each form field
    }
    response = requests.post(form_url, data=data)

    if response.status_code == 200:
        print("Form submitted successfully!")
    else:
        print(f"Failed to submit form. Status code: {response.status_code}")


if __name__ == "__main__":
    cleanup()
    main()
