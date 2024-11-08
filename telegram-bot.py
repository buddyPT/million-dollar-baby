from dotenv import dotenv_values

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

config = dotenv_values(".env")

TOKEN = config["TELEGRAM_BOT_TOKEN"]

CANAL_ID = config["TELEGRAM_BOT_TOKEN"]

#async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#    await update.message.reply_text("Olá! Esdfdasda asdsa dsad.")

#async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#    await update.message.reply_text("Cona de sabão")

#app = ApplicationBuilder().token(TOKEN).build()

#app.add_handler(CommandHandler("start", start))
#app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

#app.run_polling()


async def canal_listener(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message.text
    print(f"Mensagem recebida do canal: {message}")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(MessageHandler(filters.Chat(CANAL_ID), canal_listener))
app.run_polling()