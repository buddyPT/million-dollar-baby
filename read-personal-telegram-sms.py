from dotenv import dotenv_values

import re
import requests
from telethon import TelegramClient, events, sync

config = dotenv_values(".env")

# Substitua pelos seus valores
api_id = config["APP_API_ID"]
api_hash = config["APP_API_HASH"]
user_signal_id = int(config["TELEGRAM_SIGNAL"])  # Substitua pelo ID do usuário que você deseja monitorar
user_operator_id = int(config["TELEGRAM_OPERATOR"])
wallet_address = config["TELEGRAM_WALLET"]

# Inicialize o cliente
client = TelegramClient('telegram-reader', api_id, api_hash)

# Função para obter o saldo da carteira usando a API do Solana
def get_wallet_balance(wallet_address):
    url = "https://api.mainnet-beta.solana.com"
    headers = {"Content-Type": "application/json"}
    data = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getBalance",
        "params": [wallet_address]
    }
    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 200:
        balance_data = response.json()
        # O saldo é retornado em lamports, portanto, dividimos por 1 bilhão para obter o valor em SOL
        return balance_data["result"]["value"] / 1_000_000_000
    else:
        print("Erro ao obter o saldo da carteira.")
        return None

# Função para calcular a quantidade a ser comprada
def calculate_purchase_amount(transaction_type, wallet_address):
    balance = get_wallet_balance(wallet_address)
    if balance is not None:
        if transaction_type == "New holder":
            return balance * 0.1  # 10% do saldo da carteira
        elif transaction_type == "Buy more":
            return balance * 0.05  # 5% do saldo da carteira
    return 0
# Função para extrair informações da mensagem
def extract_info(message):
    # Expressão regular para capturar o tipo de transação (conteúdo entre colchetes)
    type_pattern = r'\[(.*?)\]'
    # Expressão regular para capturar o endereço do token (alfanumérico com 40+ caracteres)
    token_address_pattern = r'[a-zA-Z0-9]{40,}'

    # Encontrar tipo de transação
    type_match = re.search(type_pattern, message)
    transaction_type = type_match.group(1) if type_match else 'TYPE_NOT_FOUND'

    # Encontrar endereço do token
    token_address_match = re.search(token_address_pattern, message)
    token_address = token_address_match.group(0) if token_address_match else 'TOKEN_NOT_FOUND'

    return transaction_type, token_address

# Evento para nova mensagem
@client.on(events.NewMessage)
async def handle_new_message(event):
    # Conteúdo da mensagem
    # Verifica se a mensagem é do usuário especificado
    if event.sender_id == user_signal_id:
        message = event.message.message
        # Verifique o conteúdo da mensagem e responda com base nisso
        #if "olá" in mensagem.lower():
        #    resposta = "Olá! Como posso ajudar?"
        #elif "ajuda" in mensagem.lower():
        #    resposta = "Claro! Estou aqui para ajudar. O que você precisa?"
        #else:
        #    resposta = "Desculpe, não entendi sua mensagem."
    

        # Envie a resposta de volta
        #await event.reply(resposta)
        transaction_type, token_address = extract_info(message)
        print(f'Tipo de Transação: {transaction_type}')
        print(f'Endereço do Token: {token_address}')

        command = ""
        # Envia o comando "/buy" caso seja do tipo "New holder"
        if token_address != 'TOKEN_NOT_FOUND':
            if transaction_type in ["New holder", "Buy more"]:
                quantidade = calculate_purchase_amount(transaction_type, wallet_address)
                if quantidade > 0:
                    command = f"/buy {token_address} {quantidade:.2f}"
            elif transaction_type == "Sell part":
                command = f"/sell {token_address} 50%"
            elif transaction_type == "Sell all":
                command = f"/sell {token_address} 100%"
            else:
                command = ""

        if command != "":
            await client.send_message(user_operator_id, command)  # Envia o comando como resposta
            print(f'Comando enviado: {command}')


# Execute o cliente e fique sempre à escuta de novas mensagens
with client:
    print("Bot está agora monitorando mensagens...")
    client.run_until_disconnected()
