import requests
import json
import time
from dotenv import dotenv_values

# URL do endpoint RPC da Solana (mainnet)
SOLANA_RPC_URL = "https://api.mainnet-beta.solana.com"

config = dotenv_values(".env")
wallet_address = config["TELEGRAM_WALLET"]

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

# Função para obter detalhes de uma transação
def get_transaction_details(signature):
    params = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getTransaction",
        "params": [signature,{"maxSupportedTransactionVersion" : 5}]
    }
    response = requests.post(SOLANA_RPC_URL, json=params)
    if response.status_code == 200:
        return response.json().get("result", {})
    else:
        print(f"Erro ao obter transação: {response.status_code}")
        return {}

# Função para monitorar a carteira em tempo real
def monitor_wallet_in_real_time(public_key, limit=10, interval=5):
    last_seen_signature = None
    while True:
        signatures = get_transaction_signatures(public_key, limit)
        for signature_info in signatures:
            signature = signature_info["signature"]
            if signature != last_seen_signature:
                last_seen_signature = signature
                print(f"\nNova transação detectada: {signature}")
                transaction = get_transaction_details(signature)
                if transaction:
                    print(json.dumps(transaction, indent=2))
                else:
                    print("Detalhes não encontrados para essa transação.")
        time.sleep(interval)

# Uso do script
if __name__ == "__main__":
    public_key = "9RE2n7FcNDybFmc29MJ7ND33FqxVzqwcreWpqpDvzG6r"  # Substitua pela sua chave pública Solana
    monitor_wallet_in_real_time(public_key, limit=1, interval=5)
