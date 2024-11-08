from dotenv import dotenv_values

from telethon import TelegramClient, events, sync

config = dotenv_values(".env")

# Substitua pelos seus valores
api_id = config["APP_API_ID"]
api_hash = config["APP_API_HASH"]
phone_number = config["PHONE_NUMBER"]

print(phone_number)

# Inicialize o cliente
client = TelegramClient('telegram-reader', api_id, api_hash)

async def main():
    await client.start()

    # Obtém as últimas 10 mensagens de um chat específico
    async for message in client.iter_messages('@GMGN_alert_bot', limit=10):
        print(message.sender_id, message.text)

# Executa o cliente
with client:
    client.loop.run_until_complete(main())
