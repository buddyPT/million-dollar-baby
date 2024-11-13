import asyncio
import websockets
import json
import time

# Variáveis globais
saldo_inicial_sol = 1.0  # Começamos com 1 SOL
saldo_atual_sol = saldo_inicial_sol  # Saldo inicial de SOL
transacoes = []  # Para armazenar todas as transações realizadas
historico_compras = {}  # Armazena o preço de compra e quantidade de cada token

# Função para calcular a evolução geral da conta
def calcular_evolucao_geral():
    return ((saldo_atual_sol - saldo_inicial_sol) / saldo_inicial_sol) * 100

# Função para processar transações
def processar_transacao(data):
    global saldo_atual_sol

    # Obtendo os dados da transação
    tx_type = data.get('txType')
    mint = data.get('mint')
    token_amount = data.get('tokenAmount', 0)  # Define token_amount como 0 se não estiver presente
    market_cap_sol = data.get('marketCapSol')

    # Validação dos dados da transação (sem verificar token_amount)
    if not tx_type or not mint or market_cap_sol is None:
        log_erro(mint)
        return

    # Ajuste na quantidade de tokens para o cálculo
    token_amount = token_amount * 0.01
    preco_token_sol = market_cap_sol / 1_000_000_000  # Preço do token em SOL

    # Processamento de compra
    if tx_type == 'buy':
        valor_compra = token_amount * preco_token_sol
        saldo_atual_sol -= valor_compra
        log_transacao('COMPRA', mint, token_amount, valor_compra, saldo_atual_sol)

        # Armazenamento no histórico de compras
        if mint in historico_compras:
            historico_compras[mint].append({'preco_compra': preco_token_sol, 'quantidade': token_amount})
        else:
            historico_compras[mint] = [{'preco_compra': preco_token_sol, 'quantidade': token_amount}]

    # Processamento de venda
    elif tx_type == 'sell':
        valor_venda = token_amount * preco_token_sol
        saldo_atual_sol += valor_venda
        log_transacao('VENDA', mint, token_amount, valor_venda, saldo_atual_sol)

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
def log_transacao(tipo, mint, token_amount, valor, saldo_atual):
    print(f"{time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())} --- {tipo} --- {mint} --- {token_amount:.6f} --- {valor:.6f} SOL --- {saldo_atual:.6f} SOL")

# Função para logar falhas de processamento
def log_erro(mint):
    print(f"{time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())} --- FAILURE TO PROCESS THE MESSAGE --- {mint if mint else 'UNKNOWN TOKEN'}")

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

# Executa a função de subscrição
asyncio.get_event_loop().run_until_complete(subscribe())
