from dotenv import dotenv_values

from telethon import TelegramClient, events, sync

config = dotenv_values(".env")

# Substitua pelos seus valores
api_id = config["APP_API_ID"]
api_hash = config["APP_API_HASH"]
user_id = int(config["TELEGRAM_CHANELID"])  # Substitua pelo ID do usuário que você deseja monitorar

# Inicialize o cliente
client = TelegramClient('telegram-reader', api_id, api_hash)

# Evento para nova mensagem
@client.on(events.NewMessage)
async def handle_new_message(event):
    # Conteúdo da mensagem
    # Verifica se a mensagem é do usuário especificado
    if event.sender_id == user_id:
        mensagem = event.message.message

        # Verifique o conteúdo da mensagem e responda com base nisso
        if "olá" in mensagem.lower():
            resposta = "Olá! Como posso ajudar?"
        elif "ajuda" in mensagem.lower():
            resposta = "Claro! Estou aqui para ajudar. O que você precisa?"
        else:
            resposta = "Desculpe, não entendi sua mensagem."
    

        # Envie a resposta de volta
        await event.reply(resposta)

# Execute o cliente e fique sempre à escuta de novas mensagens
with client:
    print("Bot está agora monitorando mensagens...")
    client.run_until_disconnected()
