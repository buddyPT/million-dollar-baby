from dotenv import dotenv_values

import requests
import json
import time
from datetime import datetime
from telethon import TelegramClient, events, sync

config = dotenv_values(".env")

# Substitua pelos seus valores
api_id = config["APP_API_ID"]
api_hash = config["APP_API_HASH"]
user_operator_id = int(config["TELEGRAM_OPERATOR"])
wallet_address = config["TELEGRAM_WALLET"]

# Inicialize o cliente
client = TelegramClient('telegram-reader', api_id, api_hash)

# URL do endpoint RPC da Solana (mainnet)
SOLANA_RPC_URL = "https://alien-necessary-tree.solana-mainnet.quiknode.pro/9ed51dec93c83360fe9dd1748f02ef3a4908e7ce"


# Função para obter assinaturas de transações
def get_transaction_signatures(public_key, limit=10):
    params = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getSignaturesForAddress",
        "params": [public_key, {"limit": limit}]
    }
    response = requests.post(SOLANA_RPC_URL, json=params)
    if response.status_code == 200:
        return response.json().get("result", [])
    else:
        print(f"Erro na requisição: {response.status_code}")
        return []

# Função para obter detalhes de uma transação e incluir o timestamp
def get_transaction_details(signature):
    params = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getTransaction",
        "params": [signature, {"maxSupportedTransactionVersion": 10, "commitment": "confirmed"}]
    }
    response = requests.post(SOLANA_RPC_URL, json=params)
    if response.status_code == 200:
        result = response.json().get("result", {})
        if result:
            # Verificar se o timestamp está presente
            block_time = result.get("blockTime")
            if block_time:
                # Converter o timestamp de Unix epoch para um formato legível
                timestamp = datetime.fromtimestamp(block_time).strftime('%Y-%m-%d %H:%M:%S')
                print(f"Timestamp da transação: {timestamp}")
            else:
                print("Timestamp não encontrado para esta transação.")
        return result
    else:
        print(f"Erro ao obter transação: {response.status_code}")
        return {}


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


async def send_telegram_command(transaction_type, wallet_address, token_address):
    command = ""
    # Envia o comando "/buy" caso seja do tipo "New holder"
    if token_address != 'TOKEN_NOT_FOUND':
        if transaction_type in ["New holder", "Buy more"]:
            quantidade = calculate_purchase_amount(transaction_type, wallet_address)
            if quantidade > 0:
                command = f"/buy {token_address} {quantidade:.6f}"
        elif transaction_type == "Sell part":
            command = f"/sell {token_address} 50%"
        elif transaction_type == "Sell all":
            command = f"/sell {token_address} 100%"
        else:
            command = ""

    if command != "":
        await client.send_message(user_operator_id, command)  # Envia o comando como resposta
        print(f'Comando enviado: {command}')

# Função para o balance da carteira
def get_walltet_balance(public_key, balances):

    for balance in balances:
        owner = balance['owner']
        if owner == public_key:
            return int(balance['uiTokenAmount']['amount'])
        
    return 0


def check_transaction_type(public_key, signature):
    transaction_details = get_transaction_details(signature)

    if not transaction_details:
        return {
        'is_valid': False
        }

    # Verifica se a transação foi bem-sucedida
    is_valid = transaction_details['meta'].get('err') is None

    # Analisar pré e pós-saldos de tokens para determinar compra/venda e se é total/parcial
    pre_token_balances = transaction_details['meta'].get('preTokenBalances', [])
    post_token_balances = transaction_details['meta'].get('postTokenBalances', [])

    transaction_type = 'TOKEN_NOT_FOUND'
    token_address = pre_token_balances[0]['mint']

    pre_amount = get_walltet_balance(public_key, pre_token_balances)
    post_amount = get_walltet_balance(public_key, post_token_balances)
    
    # Determinar o tipo de transação
    if pre_amount < post_amount:
        if pre_amount == 0:
            transaction_type = 'New holder'  # Primeira compra (não havia saldo antes)
        else:
            transaction_type = 'Buy more'  # Compra adicional
            
    elif pre_amount > post_amount:
        if post_amount == 0:
            transaction_type = 'Sell all'  # Venda total (todo o saldo foi vendido)
        else:
            transaction_type = 'Sell part'  # Venda parcial

    # Retornar tipo de transação, validade e token address
    return {
        'transaction_type': transaction_type,
        'is_valid': is_valid,
        'token_address': token_address
    }



# Função para monitorar a carteira em tempo real e imprimir o timestamp de detecção
def monitor_wallet_in_real_time(public_key, limit=10, interval=3):
    seen_signatures = set()  # Conjunto para armazenar assinaturas já vistas
    while True:
        signatures = get_transaction_signatures(public_key, limit)
        new_transactions = False  # Flag para verificar se há novas transações

        for signature_info in signatures:
            signature = signature_info["signature"]
            if signature not in seen_signatures:
                # Capturar o timestamp do momento em que a transação é detectada
                detection_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                print(f"\nNova transação detectada: {signature}")
                

                # Adicionar a assinatura ao conjunto de vistas
                seen_signatures.add(signature)
                result = check_transaction_type(public_key, signature)
                print(f"Timestamp de detecção: {detection_time}")
                print(result)
                
                if result.is_valid:
                    new_transactions = True
                    
                    send_telegram_command(result.transaction_type, wallet_address, result.token_address)

        if not new_transactions:
            # Se nenhuma nova transação for detectada, imprimir a mensagem de ausência
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f"Não existem transações novas. {current_time}")

        time.sleep(interval)

# Uso do script
if __name__ == "__main__":
    #public_key = "9RE2n7FcNDybFmc29MJ7ND33FqxVzqwcreWpqpDvzG6r"  # Substitua pela sua chave pública Solana
    #public_key = "CXNguFpJ4TUyACqn75vYvqcTGLqDfBxNQ9SpvV9rBhXW"  # Substitua pela sua chave pública Solana
    #public_key = "suqh5sHtr8HyJ7q8scBimULPkPpA557prMG47xCHQfK"  # Substitua pela sua chave pública Solana
    public_key = "CRBYGyfcRSiwcpUr4qxbVeR7MDNb32mkhxxzFAN7iinS"  # Substitua pela sua chave pública Solana
    
    monitor_wallet_in_real_time(public_key, limit=10, interval=3)


    # Execute o cliente e fique sempre à escuta de novas mensagens
    with client:
        client.run_until_disconnected()
