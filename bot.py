from telegram.ext import Application, CommandHandler, MessageHandler, filters

from settings import BOT_PATH, BOT_TOKEN


def read() -> set:
    with open(BOT_PATH, "a+", encoding="UTF-8") as f:
        return set([int(i.strip()) for i in f.readlines()])


def write(chats):
    with open(BOT_PATH, "w", encoding="UTF-8") as f:
        for chat in chats:
            f.write(str(chat) + "\n")


async def add_user(update, context):
    chat = update.effective_chat.id
    chats = read()
    chats.add(chat)
    write(chats)
    await list_chat(update, context)


async def del_user(update, context):
    chat = update.effective_chat.id
    chats = read()
    if chats:
        chats.remove(chat)
        write(chats)
    await list_chat(update, context)


async def echo(update, context):
    "mirror message"
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text=update.message.text
    )


async def list_chat(update, context):
    "send list of users to chats"
    users = str(read())
    await context.bot.send_message(chat_id=update.effective_chat.id, text=users)


async def say(update, context):
    "send message to all chats"
    for chat in read():
        text = " ".join(context.args)
        await context.bot.send_message(chat_id=chat, text=text)


async def unknown(update, context):
    "handle unknown command"
    await context.bot.send_message(
        chat_id=update.effective_chat.id,  # chat_id = update.message.chat.id
        text="Unknown command. Try [start | stop | list | say]",
    )


if __name__ == "__main__":
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", add_user))
    app.add_handler(CommandHandler("stop", del_user))
    app.add_handler(CommandHandler("list", list_chat))
    app.add_handler(CommandHandler("say", say))
    app.add_handler(MessageHandler(filters.COMMAND, unknown))
    app.add_handler(MessageHandler(filters.TEXT, echo))

    app.run_polling()
