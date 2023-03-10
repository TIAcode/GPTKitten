import sys
import openai
import argparse

openai.api_key = "FILL-IN-YOUR-KEY"

START_PROMPT = [
    {
        "role": "system",
        "content": "You are an AI assistant. Given to you is possibly data from user's terminal session and a request from user. Provide a best response to the user.",
    },
    {"role": "user", "content": "{data}"},
]


def get_last_line(data: str) -> str:
    return data.rstrip().rsplit("\n", maxsplit=1)[1]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    # parser.add_argument(
    #    "--win",
    #    "-w",
    #    type=int,
    #    help="Window ID to send the response to",
    # )
    args = parser.parse_args()
    if not sys.stdin.isatty():  # args.data:
        input_data = sys.stdin.read()
        sys.stdin.close()
        sys.stdin = open("/dev/tty")
        print("Input data: ...", get_last_line(input_data))
    else:
        print("No screen data?")
        input_data = ""

    running = True
    prompt = []
    for prompt_item in START_PROMPT:
        prompt_text = prompt_item["content"].format(data=input_data).lstrip("\n")
        if prompt_text.strip():
            filled_prompt = dict(prompt_item)
            filled_prompt["content"] = prompt_text
            prompt.append(filled_prompt)

    while running:
        user_prompt = input("Message: ")
        print("")
        if user_prompt.strip().lower() == "/quit":
            running = False
            continue
        prompt.append({"role": "user", "content": user_prompt})
        reply = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=prompt)
        print(reply["choices"][0]["message"]["content"])
        print("")
        prompt.append(
            {"role": "assistant", "content": reply["choices"][0]["message"]["content"]}
        )
