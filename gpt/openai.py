import asyncio

import openai
import tiktoken
from loguru import logger

from crud import crud
from settings import MODEL_4K, MODEL_16K, OPENAI_KEY

logger = logger.bind(name="gpt")
openai.api_key = OPENAI_KEY


def count_token(s: str) -> int:
    # encoding = tiktoken.encoding_for_model(model)
    encoding = tiktoken.get_encoding("cl100k_base")  # big base
    return len(encoding.encode(s))


def create_openai_completion(user_id, prompt, tokens, lvl=0) -> str:
    """
    send prompt to openai. return openai response. max lvl of recursion is 3\n
    $0.0020 / 1K tokens\n
    gpt-3.5-turbo-1106" is the flagship model of this family, supports a 16K context window and is optimized for dialog.\n
    gpt-3.5-turbo-instruct" is an Instruct model and only supports a 4K context window.\n
    https://openai.com/pricing\n
    """

    max_lvl = 3
    if lvl > max_lvl:  # max level of recursion
        raise Exception(
            f"Generation interrupt. Finish reason: max lvl of recursion is {max_lvl}"
        )

    model = MODEL_4K
    max_tokens = 4096
    response_tokens = max_tokens - count_token(prompt)
    if response_tokens < 500:
        model = MODEL_16K
        max_tokens = 16384

    tokens = min(response_tokens, tokens)
    # raise Exception("Stop before openai.Completion.create")
    response = openai.Completion.create(
        model=model,
        prompt=prompt,
        temperature=0.6,
        max_tokens=tokens,  # default: 2048
        # top_p=1,
        # frequency_penalty=0,
        # presence_penalty=0,
        # stop=["word", "word2"],
    )
    finish_reason = response["choices"][0]["finish_reason"]
    text = response["choices"][0]["text"].strip().replace('"', "'")
    total_tokens = response["usage"]["total_tokens"]
    crud.edit_user(user_id, {"tokens": -total_tokens})
    logger.info(f"TOTAL_TOKENS: {total_tokens}")
    if finish_reason == "stop":
        return text

    if text:
        prompt_continue = (
            text[len(text) // 2 :] + "...\n\ncontinue where you left off"
        )  # "keep going" | "go on" | "continue where you left off"
        text_continue = create_openai_completion(
            user_id, prompt_continue, tokens, lvl=lvl + 1
        )
        return text + " " + text_continue

    raise Exception(f"Generation interrupt. Finish reason: {finish_reason}")


async def create_openai_completion_async(user_id, template, tokens):
    return await asyncio.to_thread(create_openai_completion, user_id, template, tokens)
