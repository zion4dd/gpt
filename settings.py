import os
import platform

import dotenv
from loguru import logger

if platform.system() == "Windows":
    dotenv.load_dotenv(override=True)

TOPIC = "<topic>"  # tag for topic in gpt mods

DEBUG = os.getenv("DEBUG") == "true"
SECRET = os.getenv("SECRET_KEY")
print('.env >>> DEBUG="%s"' % os.getenv("DEBUG"))

# openai
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
MODEL_4K = os.getenv("MODEL_4K")
MODEL_16K = os.getenv("MODEL_16K")

# admin
ADMIN = os.getenv("ADMIN")
HPSW = os.getenv("ADMIN_PSW")
TRIAL = int(os.getenv("TRIAL", 30000))  # trial tokens

# login validation
VALID_EMAIL = os.getenv("VALID_EMAIL") == "true"
VALID_PSW = os.getenv("VALID_PSW") == "true"

# email smtp
SMTP_SERVER = "smtp.beget.com"
SENDER_EMAIL = "iforgotpsw@project-gpt.su"
SENDER = f"project-gpt <{SENDER_EMAIL}>"
EMAIL_PSW = os.getenv("EMAIL_PSW")

# database
DB_DIR = "./dbstorage"
DB_PATH = os.getenv("DB_PATH_SQLITE")
# DB_PATH = os.getenv("DB_PATH_PG")
print("db >>>", DB_PATH[:8])

# log
LOG_DIR = "./log"
LOGLEVEL = int(os.getenv("LOGLEVEL", 30))

# bot
BOT_PATH = "./dbstorage/chats.txt"
BOT_ON = os.getenv("BOT_ON") == "true"
BOT_TOKEN = os.getenv("BOT_TOKEN")

# dalle_gen
IMG_EXT = "jpg"
IMG_MAX = 6
if platform.system() == "Windows":
    IMG_PATH = "d:\\code\\project_gpt\\imgs\\"
    IMG_URL = "http://localhost:5000/imgs/"
else:
    IMG_PATH = "/var/www/imgs/"
    IMG_URL = "https://project-gpt.su/imgs/"

# sentry
SENTRY = os.getenv("SENTRY")

# loggers
loggers = {
    "__main__": 30,
    "gpt": LOGLEVEL,
    "db": LOGLEVEL,
    "views.user": LOGLEVEL,
    "dalle": LOGLEVEL,
    "img_man": LOGLEVEL,
}


def add_logger(name, level):
    logger.add(
        f"./log/{name}.log",
        rotation="1 MB",
        retention=3,
        filter=lambda x: x["extra"].get("name") == name,
        diagnose=False,
        backtrace=False,
        level=level,
    )


for name, level in loggers.items():
    add_logger(name, level)
