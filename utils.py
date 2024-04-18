import asyncio
import logging
import smtplib
from datetime import datetime as dt
from random import choices
from string import ascii_letters, digits
from time import time

from telegram import Bot
from werkzeug.security import generate_password_hash  # ,check_password_hash

from crud import crud
from settings import (
    BOT_ON,
    BOT_PATH,
    BOT_TOKEN,
    EMAIL_PSW,
    SENDER,
    SENDER_EMAIL,
    SMTP_SERVER,
)


def hpsw(psw):
    return generate_password_hash(psw)


def random_chars(length=12, extension=None):
    """Generate random chars sequence with given length and optional extension."""
    chars = "".join(choices(ascii_letters, k=length))
    if extension:
        chars += "." + extension.strip(".")
    return chars


def utc(t):
    "unix timestamp converter Y.m.d H:M"
    return dt.fromtimestamp(t).strftime("%Y.%m.%d %H:%M")


def valid_psw(psw):
    "password validator: ascii_letters+digits+_.!@#$&"
    symbols = "_.!@#$&"
    allowed = ascii_letters + digits + symbols
    return set(psw) < set(allowed), "a-zA-Z0-9" + symbols


def invalid_user(user_id) -> dict | None:
    user = crud.get_user(user_id)
    valid = (user, user.active, user.exp_date > time(), user.tokens > 0)
    if not all(valid):
        return {
            "user_id": user.id,
            "active": valid[1],
            "date": valid[2],
            "tokens": valid[3],
        }


def send_email(email, msg) -> dict:
    "-> success: {}; error: { 'aa@bb.c' : ( 550 ,'User unknown' ) }"
    message = (
        f"""Subject: Password {email}\r\nFrom: {SENDER}\r\nTo: {email}\r\n{msg}\n"""
    )
    with smtplib.SMTP(SMTP_SERVER) as server:
        server.login(SENDER_EMAIL, EMAIL_PSW)
        res = server.sendmail(SENDER_EMAIL, [email, SENDER_EMAIL], message)
        return res


def bot_send(msg: str):
    "The maximum length of a Telegram message is 4096 characters and it must be UTF-8 encoded."
    msg = msg[:4096].encode()

    async def send(chat, msg):
        await Bot(BOT_TOKEN).send_message(chat, msg)

    if BOT_ON:
        with open(BOT_PATH, "r", encoding="UTF-8") as f:
            chats = set([int(i.strip()) for i in f.readlines()])
        for chat in chats:
            # print(chat, msg)
            asyncio.run(send(chat, msg))


class TelegramHandler(logging.Handler):
    def emit(self, record):
        message = self.format(record)
        bot_send(message)


# def logger(name):
#     fmt = "\n%(levelname)s [%(asctime)s] %(pathname)s, line %(lineno)d\n%(message)s"
#     # %(module)s, %(funcName)s
#     datefmt = "%b%d %H:%M:%S"
#     logger = logging.getLogger(name)
#     logger.setLevel(LOGLEVEL)
#     formatter = logging.Formatter(fmt=fmt, datefmt=datefmt)

#     f_handler = logging.FileHandler(f"./log/{name}.log", encoding="utf-8")
#     t_handler = TelegramHandler(logging.WARNING)
#     s_handler = logging.StreamHandler()
#     f_handler.setFormatter(formatter)
#     t_handler.setFormatter(formatter)
#     logger.addHandler(f_handler)
#     logger.addHandler(t_handler)
#     logger.addHandler(s_handler)
#     return logger
