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
    
    tx_type = data.get('txType')
    if not tx_type:
        print("Erro: 'txType' não encontrado na mensagem.")
        return

    mint = data.get('mint')
    token_amount = data.get('tokenAmount')
    market_cap_sol = data.get('marketCapSol')
    
    if not all([mint, token_amount, market_cap_sol]):
        print("Erro: Dados da transação incompletos.")
        return

    # Calculando o preço do token (em SOL)
    preco_token_sol = market_cap_sol / 1_000_000_000  # Preço do token

    # Registra a compra ou venda
    if tx_type == 'buy':
        valor_compra = token_amount * preco_token_sol
        saldo_atual_sol -= valor_compra  # Deduz o valor da compra do saldo de SOL
        transacoes.append({
            'tipo': 'compra',
            'mint': mint,
            'quantidade': token_amount,
            'preco_token': preco_token_sol,
            'valor_compra': valor_compra,
            'saldo_restante': saldo_atual_sol,
            'timestamp': time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
        })
        
        # Salva o preço e quantidade da compra no histórico
        if mint in historico_compras:
            historico_compras[mint].append({'preco_compra': preco_token_sol, 'quantidade': token_amount})
        else:
            historico_compras[mint] = [{'preco_compra': preco_token_sol, 'quantidade': token_amount}]
        
        log_transacao('Compra', token_amount, preco_token_sol, valor_compra, saldo_atual_sol)
        
    elif tx_type == 'sell':
        valor_venda = token_amount * preco_token_sol
        saldo_atual_sol += valor_venda  # Acrescenta o valor da venda ao saldo de SOL
        
        # Calcula o lucro/perda com base na quantidade proporcional vendida
        lucro_perda = 0
        quantidade_vender = token_amount
        while quantidade_vender > 0 and historico_compras.get(mint):
            compra = historico_compras[mint][0]
            if compra['quantidade'] <= quantidade_vender:
                # Vende toda essa quantidade e calcula o lucro/perda
                lucro_perda += (preco_token_sol - compra['preco_compra']) * compra['quantidade']
                quantidade_vender -= compra['quantidade']
                historico_compras[mint].pop(0)  # Remove esta entrada do histórico
            else:
                # Vende uma parte da quantidade
                lucro_perda += (preco_token_sol - compra['preco_compra']) * quantidade_vender
                compra['quantidade'] -= quantidade_vender
                quantidade_vender = 0

        percentual_lucro_perda = (lucro_perda / valor_venda) * 100 if valor_venda != 0 else 0

        # Atualiza a transação
        transacoes.append({
            'tipo': 'venda',
            'mint': mint,
            'quantidade': token_amount,
            'preco_token': preco_token_sol,
            'valor_venda': valor_venda,
            'lucro_perda': lucro_perda,
            'percentual_lucro_perda': percentual_lucro_perda,
            'saldo_restante': saldo_atual_sol,
            'timestamp': time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
        })
        log_transacao('Venda', token_amount, preco_token_sol, valor_venda, saldo_atual_sol, lucro_perda, percentual_lucro_perda)

    # Mostrar evolução geral da conta
    evolucao_geral = calcular_evolucao_geral()
    print(f"Evolução geral da conta: {evolucao_geral:.2f}%")

# Função para logar transações
def log_transacao(tipo, token_amount, preco_token_sol, valor, saldo_atual, lucro_perda=0, percentual_lucro_perda=0):
    if tipo == 'Compra':
        print(f"{tipo} registrada: {token_amount} tokens a {preco_token_sol} SOL cada, saldo restante: {saldo_atual} SOL")
    elif tipo == 'Venda':
        print(f"{tipo} registrada: {token_amount} tokens a {preco_token_sol} SOL cada, lucro/perda: {lucro_perda} SOL, saldo restante: {saldo_atual} SOL")
        print(f"Percentual de lucro/perda: {percentual_lucro_perda:.2f}%")

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
