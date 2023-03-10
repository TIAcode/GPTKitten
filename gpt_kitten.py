from typing import List, Optional, Union, Dict
import openai
from kitty.boss import Boss
from kitty.window import CommandOutput

import argparse


openai.api_key = "FILL-IN-YOUR-KEY"


def main(args: List[str]) -> str:
    pass


from kittens.tui.handler import result_handler
from kittens.tui.loop import debug

completion_prompts = {
    "complete": """Complete this code or terminal line. Do not write anything else except the best completion.

Terminal data:  {data}

Answer: """,
    "debug": "Capture from kitty terminal:\n{data}\n. Provide a command suggestion how to handle the situation.\n",
}


chat_prompts = {
    "complete": [
        {
            "role": "system",
            "content": "You are an AI assistant. Provide a best completion to the data and commands that has been sent from user's terminal.",
        },
        {
            "role": "user",
            "name": "example_user",
            "content": """python
Python 3.10.9 (main, Dec 19 2022, 17:35:49) [GCC 12.2.0] on linux
Type "help", "copyright", "credits" or "license" for more information.
>>> import random
>>> numbers=[5,14,515,141,12,7,8]
>>> choice=""",
        },
        {
            "role": "assistant",
            "name": "example_assistant",
            "content": """random.choice(numbers)""",
        },
        {
            "role": "user",
            "name": "example_user",
            "content": """SQLite version 3.41.0 2023-02-21 18:09:37
Enter ".help" for usage hints.
sqlite> select * from employee limit 3;
1|John Smith|john.smith@example.com|1
2|Mary Johnson|mary.johnson@example.com|2
3|Peter Brown|peter.brown@example.com|2
sqlite> select * from position;
1|Manager|75000.0
2|Developer|60000.0
3|Designer|55000.0
sqlite> # Select employees and position information sorted by salary
sqlite> select """,
        },
        {
            "role": "assistant",
            "name": "example_assistant",
            "content": """e.*, p.* from employee e join position p on p.id = e.position_id order by p.salary DESC;""",
        },
        {
            "role": "user",
            "content": "Terminal content: {data}. Only provide the best completion - do not write anything else.",
        },
    ],
    "ask": [
        {
            "role": "system",
            "content": "You are an AI assistant. Following is text capture from user's terminal and a request for your response.",
        },
        {"role": "user", "content": "{data}\n\nUser request: {input}"},
    ],
}


def get_first_line(data: str) -> str:
    return data.lstrip("\n").split("\n", maxsplit=1)[0]


@result_handler(no_ui=True)
def handle_result(
    args: List[str], answer: str, target_window_id: int, boss: Boss
) -> None:

    window = boss.window_id_map.get(target_window_id)
    if window is None:
        debug("window not found")

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--extent",
        "-e",
        type=str,
        help="selection, lastcmd, screen, scrollback. Comma separated list, default is selection,lastcmd,screen. Will be tried in order until result returned",
        default="selection,lastcmd,screen",
    )
    parser.add_argument(
        "--model",
        "-m",
        type=str,
        default="gpt-3.5-turbo",  # "code-davinci-002",
        help="gpt-3.5-turbo (suggested and default!), code-davinci-002, text-davinci-003 etc.",
    )
    # parser.add_argument("--max-input-tokens", type=int, default=2048)
    # parser.add_argument("--max-completion-tokens", type=int, default=200)
    # parser.add_argument("--temp", type=float, default=0.0)
    # parser.add_argument("--topp", type=int, default=1)
    # parser.add_argument(
    #    "--dunst", action="store_true", help="Use dunst for notifications"
    # )
    # parser.add_argument("--multiline", "-l", type=bool, default=False)
    # parser.add_argument("--input", "-i", type=str, default=None)
    parser.add_argument(
        "--prompt",
        "-p",
        type=str,
        choices=set(completion_prompts.keys()).union(set(chat_prompts.keys())),
        default="complete",
    )
    args.remove("gpt_kitten.py")
    settings = parser.parse_args(args)
    is_chat = settings.model.startswith("gpt-3.5")
    for extent in settings.extent.split(","):
        extent = extent.lower()
        if extent == "selection" and window.has_selection():
            screen_data = window.text_for_selection()
            if screen_data and screen_data.strip():
                break
        elif extent == "screen":
            screen_data = window.as_text()
            if screen_data and screen_data.strip():
                break
        elif extent == "scrollback":
            screen_data = window.as_text(add_history=True)
            if screen_data:
                break
        elif extent == "lastcmd":
            screen_data = window.cmd_output(CommandOutput.last_non_empty)
            if screen_data and screen_data.strip():
                break
    # screen_data = screen_data.rstrip("\n")
    if is_chat:
        prompt = chat_prompts.get(settings.prompt)
        for prompt_item in prompt:
            prompt_item["content"] = prompt_item["content"].format(
                data=screen_data, input=""
            )
        chat_reply = openai.ChatCompletion.create(
            messages=prompt, model=settings.model, temperature=0, top_p=1
        )
        reply_first_line = get_first_line(
            chat_reply["choices"][0]["message"]["content"]
        )
        boss.call_remote_control(window, ("send_text", reply_first_line))
    else:
        prompt = completion_prompts.get(settings.prompt)
        prompt = prompt.format(data=screen_data)
        completion = openai.Completion.create(
            prompt=prompt,
            model=settings.model,
            temperature=0,
            top_p=1,
            max_tokens=100,
            n=1,
        )
        completion_first_line = get_first_line(completion["choices"][0]["text"])
        boss.call_remote_control(window, ("send_text", completion_first_line))
