import requests
import json
import time

# URL do endpoint RPC da Solana (mainnet)
SOLANA_RPC_URL = "https://api.mainnet-beta.solana.com"
TOKEN_PROGRAM_ID = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"  # Programa SPL de tokens

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
        "params": [signature, {"maxSupportedTransactionVersion": 10}]
    }
    response = requests.post(SOLANA_RPC_URL, json=params)
    if response.status_code == 200:
        return response.json().get("result", {})
    else:
        print(f"Erro ao obter transação: {response.status_code}")
        return {}

# Função para obter saldo da carteira para um token específico
def get_token_balance(public_key, token_mint):
    params = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getTokenAccountsByOwner",
        "params": [public_key, {"mint": token_mint}, {"encoding": "jsonParsed"}]
    }
    response = requests.post(SOLANA_RPC_URL, json=params)
    if response.status_code == 200:
        result = response.json().get("result", {})
        if result["value"]:
            return int(result["value"][0]["account"]["data"]["parsed"]["info"]["tokenAmount"]["amount"])
    return 0

# Função para verificar tipo de transação (compra/venda parcial ou total)
def check_transaction_type(public_key, signature):
    transaction = get_transaction_details(signature)
    
    if not transaction:
        return "Transação não encontrada."

    instructions = transaction["transaction"]["message"]["instructions"]
    
    for instr in instructions:
        if instr.get("programId") == TOKEN_PROGRAM_ID:  # Verificar se a instrução está relacionada a SPL tokens
            parsed = instr.get("parsed", {})
            if parsed.get("type") == "transfer":
                info = parsed.get("info", {})
                source = info.get("source")
                destination = info.get("destination")
                amount = int(info.get("amount", 0))
                token_mint = info.get("mint")  # Extraímos o token_mint diretamente da transação

                # Se o token_mint não estiver presente, ignoramos essa instrução
                if not token_mint:
                    continue

                # Verificar se a carteira está envolvida
                if source == public_key:
                    # Venda: checar saldo após a transação
                    post_token_balance = get_token_balance(public_key, token_mint)
                    if post_token_balance == 0:
                        return f"Venda total de {amount} tokens ({token_mint})."
                    else:
                        return f"Venda parcial de {amount} tokens ({token_mint})."
                elif destination == public_key:
                    # Compra: checar saldo após a transação
                    post_token_balance = get_token_balance(public_key, token_mint)
                    if post_token_balance == amount:
                        return f"Primeira compra de {amount} tokens ({token_mint})."
                    else:
                        return f"Compra adicional de {amount} tokens ({token_mint})."

    return "Nenhuma transferência detectada."

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
                result = check_transaction_type(public_key, signature)
                print(result)
        time.sleep(interval)

# Uso do script
if __name__ == "__main__":
    public_key = "9RE2n7FcNDybFmc29MJ7ND33FqxVzqwcreWpqpDvzG6r"  # Substitua pela sua chave pública Solana
    monitor_wallet_in_real_time(public_key, limit=5, interval=5)
