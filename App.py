import os
import json
import requests

from ScriptedBot import ScriptedBot
from private import config

from Telegram import TBot


def main():
    bot = ScriptedBot(
        config.bot_token,
        working_directory=os.path.abspath("private/bot"),
        script_path="Script/bot_script_test_2.toml")
    bot.run()
    # bot = TBot(config.bot_token, use_sessions=True)
    # # bot.send_poll("820216855", "вопрос", ["Ответ 1", "Ответ 2", "Ответ 3"], True)
    #
    # @bot.on_callback
    # def callback_handler(callback, session):
    #     print(f"callback:\n{json.dumps(callback, indent=2)}\n\nSession:\n{json.dumps(session, indent=2)}")
    #
    # @bot.on_poll
    # def poll_handler(poll, session):
    #     print(f"poll:\n{json.dumps(poll, indent=2)}")
    #     if not poll['is_closed'] and 'chat' in poll:
    #         bot.stop_poll(poll['chat']['id'], poll['message_id'])
    #
    # bot.run()


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
    main()
