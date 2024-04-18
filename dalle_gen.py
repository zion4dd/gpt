import os

import openai
import requests
from loguru import logger

from crud import crud
from settings import IMG_EXT, IMG_MAX, IMG_PATH, MODEL_4K, OPENAI_KEY
from utils import invalid_user, random_chars

logger = logger.bind(name="dalle")

openai.api_key = OPENAI_KEY


def create_openai_prompt_for_dalle(user_id, content_id):
    "Generate Prompt for Dall-e with Chat-GPT"
    text = crud.get_content(user_id, content_id)["text"]
    prompt = f"""Use the Text between tags '##' to create a prompt for Dall-e 
to generate an illustration for the Text: ##{text}##"""
    response = openai.Completion.create(
        model=MODEL_4K, prompt=prompt, temperature=0.6, max_tokens=2048
    )
    # top_p=1, frequency_penalty=0, presence_penalty=0, stop=["word", "word2"]
    return response["choices"][0]["text"].strip()


def create_openai_image(content_id, prompt, number, size):
    size_x = f"{size}x{size}"
    response = openai.Image.create(prompt=prompt, n=number, size=size_x)
    for i in response["data"]:
        response = requests.get(i["url"])
        if response:
            filename = random_chars(extension=IMG_EXT)
            file_path = os.path.join(IMG_PATH, filename)
            with open(file_path, "wb") as file:
                file.write(response.content)
                crud.add_content_field(content_id, "img", filename)
                logger.info(f"img: {filename}")


def dalle_gen(user_id, content_id, iprompt_id):
    invalid = invalid_user(user_id)
    if invalid:
        return {"message": "fail", "user": invalid}

    event = user_id, content_id, iprompt_id
    logger.info(f"user_id, content_id, iprompt_id >> {event}")
    cfg = crud.get_iprompt(user_id, iprompt_id)
    # cfg: name, size, number, main, style, mod1..mod5
    number = cfg["number"]
    size = cfg["size"]
    main_mod = (
        cfg["main"]
        if cfg["main"]
        else create_openai_prompt_for_dalle(user_id, content_id)
    )
    logger.info(f"MAIN_MOD >> {main_mod}")

    mod_list = [main_mod] + [
        cfg[i] for i in ("style", "mod1", "mod2", "mod3", "mod4", "mod5")
    ]
    prompt = " | ".join([i for i in mod_list if i])
    logger.warning(f"PROMPT {event} >> {prompt}")

    number = min(int(number), IMG_MAX - crud.get_images_count(content_id))
    if number > 0:
        create_openai_image(content_id, prompt, number, size)


#     # res += "| realistic photographic "
#     res += "| hyper realistic eye level exterior photo "
#     # res += "| photography "
#     # res += "| kodachrome film "
#     res += "| highly detailed "
#     res += "| 8K "
#     # res += "| greyscale "
