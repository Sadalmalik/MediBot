from Scripting import ScriptableStateMachine


def message_handler(runner: ScriptableStateMachine, context, step, event, value):
    if step is None:
        return
    if event == "start":
        print(step["message"])
        if "buttons" in step:
            for btn in step["buttons"]:
                print(f"  - {btn[0]} :: {btn[1]}")
    elif event == "choice":
        if "buttons" in step:
            for btn in step["buttons"]:
                if btn[0] == value:
                    runner.goto(context, btn[1])
                    return


def main():
    # c:no
    sr = ScriptableStateMachine("Script/bot_script_test.toml")
    sr.add_handler(10, ["start", "choice"], message_handler)
    dialogue = sr.create_context()
    sr.goto(dialogue, "start")
    while dialogue["node"] is not None:
        user_input = input()
        event = "message"
        if user_input.startswith("m:"):
            user_input = user_input[2:]
        elif user_input.startswith("c:"):
            user_input = user_input[2:]
            event = "choice"
        sr.event(dialogue, event, user_input)
    print("Цикл завершен!")
    sr.event(dialogue, "message", "test")


if __name__ == "__main__":
    main()
