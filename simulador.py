import asyncio
import websockets
import json
import time
import requests

# Variáveis globais
saldo_inicial_sol = 1.0  # Começamos com 1 SOL
saldo_atual_sol = saldo_inicial_sol  # Saldo inicial de SOL
transacoes = []  # Para armazenar todas as transações realizadas
historico_compras = {}  # Armazena o preço de compra e quantidade de cada token
rpc_url = "https://api.mainnet-beta.solana.com"  # URL da API RPC da Solana

# Função para calcular a evolução geral da conta
def calcular_evolucao_geral():
    return ((saldo_atual_sol - saldo_inicial_sol) / saldo_inicial_sol) * 100

# Função para exibir a mensagem inicial
def mensagem_inicial():
    print(f"{time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())} ---  ---  ---  ---  --- {saldo_atual_sol:.6f} SOL")

# Função para obter a data real da transação usando a API RPC da Solana
def obter_data_real(signature):
    for tentativa in range(3):
        try:
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getTransaction",
                "params": [signature, "json"]
            }
            response = requests.post(rpc_url, json=payload)
            if response.status_code == 200:
                result = response.json().get("result")
                if result and "blockTime" in result:
                    data_real = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(result["blockTime"]))
                    return data_real
        except Exception as e:
            print(f"Erro ao buscar data real da transação: {e}")
    return "NOT AVAILABLE"

# Função para processar transações
def processar_transacao(data):
    global saldo_atual_sol

    # Obtendo os dados da transação
    tx_type = data.get('txType')
    mint = data.get('mint')
    symbol = data.get('symbol', 'UNKNOWN SYMBOL')
    signature = data.get('signature')
    token_amount = data.get('tokenAmount', 0)  # Define token_amount como 0 se não estiver presente
    market_cap_sol = data.get('marketCapSol')

    # Validação dos dados da transação (sem verificar token_amount)
    if not tx_type or not mint or market_cap_sol is None:
        log_erro(mint, symbol)
        return

    # Tenta obter a data real da transação
    data_real = obter_data_real(signature) if signature else "NOT AVAILABLE"

    # Ajuste na quantidade de tokens para o cálculo
    token_amount = token_amount * 0.01
    preco_token_sol = market_cap_sol / 1_000_000_000  # Preço do token em SOL

    # Processamento de compra
    if tx_type == 'buy':
        valor_compra = token_amount * preco_token_sol
        saldo_atual_sol -= valor_compra
        log_transacao('COMPRA', mint, symbol, token_amount, valor_compra, saldo_atual_sol, data_real)

        # Armazenamento no histórico de compras
        if mint in historico_compras:
            historico_compras[mint].append({'preco_compra': preco_token_sol, 'quantidade': token_amount})
        else:
            historico_compras[mint] = [{'preco_compra': preco_token_sol, 'quantidade': token_amount}]

    # Processamento de venda
    elif tx_type == 'sell':
        valor_venda = token_amount * preco_token_sol
        saldo_atual_sol += valor_venda
        log_transacao('VENDA', mint, symbol, token_amount, valor_venda, saldo_atual_sol, data_real)

        # Atualizando o histórico de compras para cálculo de lucro/perda
        quantidade_vender = token_amount
        while quantidade_vender > 0 and historico_compras.get(mint):
            compra = historico_compras[mint][0]
            if compra['quantidade'] <= quantidade_vender:
                quantidade_vender -= compra['quantidade']
                historico_compras[mint].pop(0)
            else:
                compra['quantidade'] -= quantidade_vender
                quantidade_vender = 0

# Função para logar transações no formato especificado
def log_transacao(tipo, mint, symbol, token_amount, valor, saldo_atual, data_real):
    print(f"{time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())} --- {data_real} --- {tipo} --- {mint} --- {symbol} --- {token_amount:.6f} --- {valor:.6f} SOL --- {saldo_atual:.6f} SOL")

# Função para logar falhas de processamento
def log_erro(mint, symbol):
    print(f"{time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())} --- FAILURE TO PROCESS THE MESSAGE --- {mint if mint else 'UNKNOWN TOKEN'} --- {symbol}")

# Função para subscrever ao websocket e monitorar as transações
async def subscribe():
    uri = "wss://pumpportal.fun/api/data"
    while True:  # Loop para reconexão automática
        try:
            async with websockets.connect(uri) as websocket:
                payload = {
                    "method": "subscribeAccountTrade",
                    "keys": ["suqh5sHtr8HyJ7q8scBimULPkPpA557prMG47xCHQfK"]  # array of accounts to watch
                }
                await websocket.send(json.dumps(payload))

                # Recebe e processa as mensagens
                async for message in websocket:
                    data = json.loads(message)
                    processar_transacao(data)
        except Exception as e:
            print(f"Erro de conexão: {e}. Tentando reconectar em 5 segundos...")
            await asyncio.sleep(5)

# Exibe a mensagem inicial
mensagem_inicial()

# Executa a função de subscrição
asyncio.get_event_loop().run_until_complete(subscribe())
