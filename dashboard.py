import requests
import json
import time
from datetime import datetime

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
        "params": [signature, {"maxSupportedTransactionVersion": 10, "commitment": "finalized"}]
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

# Função para verificar tipo de transação (compra/venda parcial ou total)
def check_transaction_type(public_key, signature):

    transaction_details = get_transaction_details(signature)

    if not transaction_details:
        return "Transação não encontrada."
    
    is_valid = transaction_details['meta'].get('err') is None

# Analisar pré e pós-saldos de tokens para determinar compra/venda e se é total/parcial
    pre_token_balances = transaction_details['meta'].get('preTokenBalances', [])
    post_token_balances = transaction_details['meta'].get('postTokenBalances', [])
    
    transaction_type = 'unknown'
    token_address = None
    
    for pre, post in zip(pre_token_balances, post_token_balances):
        pre_amount = int(pre['uiTokenAmount']['amount'])
        post_amount = int(post['uiTokenAmount']['amount'])
        
        # Obter o token address do campo 'mint'
        token_address = pre['mint']

        if pre_amount < post_amount:
            transaction_type = 'buy'
            if pre_amount == 0:
                transaction_type += ' new'
            else:
                transaction_type += ' partial'
                
        elif pre_amount > post_amount:
            transaction_type = 'sell'
            if post_amount == 0:
                transaction_type += ' total'
            else:
                transaction_type += ' partial'
    
    # Retornar tipo de transação, validade e token address
    return {
        'transaction_type': transaction_type,
        'is_valid': is_valid,
        'token_address': token_address
    }




# Função para monitorar a carteira em tempo real e imprimir o timestamp de detecção
def monitor_wallet_in_real_time(public_key, limit=10, interval=5):
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
                print(f"Timestamp de detecção: {detection_time}")

                # Adicionar a assinatura ao conjunto de vistas
                seen_signatures.add(signature)
                result = check_transaction_type(public_key, signature)
                print(result)
                
                new_transactions = True

        if not new_transactions:
            # Se nenhuma nova transação for detectada, imprimir a mensagem de ausência
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f"Não existem transações novas. {current_time}")

        time.sleep(interval)

# Uso do script
if __name__ == "__main__":
    public_key = "9RE2n7FcNDybFmc29MJ7ND33FqxVzqwcreWpqpDvzG6r"  # Substitua pela sua chave pública Solana
    monitor_wallet_in_real_time(public_key, limit=1, interval=2)
