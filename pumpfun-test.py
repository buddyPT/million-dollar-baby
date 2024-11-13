import asyncio
import websockets
import json
from datetime import datetime
import requests

MIN_BONDINGCURVE=30
MIN_MARKETCAP=30
MIN_TokensInBondingCurve=999999999

# URL do endpoint RPC da Solana (mainnet)
SOLANA_RPC_URL = "https://alien-necessary-tree.solana-mainnet.quiknode.pro/9ed51dec93c83360fe9dd1748f02ef3a4908e7ce"

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
        #if result:
            # Verificar se o timestamp está presente
        #    block_time = result.get("blockTime")
        #    if block_time:
                # Converter o timestamp de Unix epoch para um formato legível
        #        timestamp = datetime.fromtimestamp(block_time).strftime('%Y-%m-%d %H:%M:%S')
                #print(f"Timestamp da transação: {timestamp}")
        #    else:
                #print("Timestamp não encontrado para esta transação.")
        return result
    else:
        #print(f"Erro ao obter transação: {response.status_code}")
        return {}


def get_raydium_pool_liquidity(mint):
    url = "https://api.raydium.io/pairs"
    response = requests.get(url)
    if response.status_code == 200:
        pools = response.json()
        for pool in pools:
            if pool['base_mint'] == mint or pool['quote_mint'] == mint:
                return pool['liquidity']
                #print(f"Liquidez no pool Raydium: {pool['liquidity']}")
                #break
    else:
        return -1
        #print("Erro ao obter dados:", response.status_code)

def evaluate_token(token):
    if token.get('vSolInBondingCurve'):
        vSolInBondingCurve = float(token.get('vSolInBondingCurve'))
        marketCapSol = float(token.get('marketCapSol'))
        vTokensInBondingCurve = float(token.get('vTokensInBondingCurve'))
        

        if vSolInBondingCurve > MIN_BONDINGCURVE and marketCapSol > MIN_MARKETCAP and vTokensInBondingCurve > MIN_TokensInBondingCurve:
            txType = token.get('txType')
            if txType == 'create':
                mint = token.get('mint')
                liquidity=get_raydium_pool_liquidity(mint)
                print("liquidity: ", liquidity)
                if liquidity and liquidity > -1:
                #details=get_transaction_details(token.get('signature'))
                #if details:
                    
                    symbol = token.get('symbol')

                    current_time = datetime.now()
                    buy_value=(marketCapSol/100000000)
                    sell_value=buy_value*1.1
                    print(f"{current_time}: buy {symbol} at ", buy_value)
                    print(f"{current_time}: mint {mint}")
                    print(f"{current_time}: sell at ", sell_value)
                    print("signature: ", token.get('signature'))
                    get_raydium_pool_liquidity(mint)


async def subscribe():
    uri = "wss://pumpportal.fun/api/data"
    async with websockets.connect(uri) as websocket:

        # Subscribing to token creation events
        payload = {
            "method": "subscribeNewToken",
        }
        await websocket.send(json.dumps(payload))


        # Subscribing to trades made by accounts
        #payload = {
        #    "method": "subscribeAccountTrade",
        #    "keys": ["suqh5sHtr8HyJ7q8scBimULPkPpA557prMG47xCHQfK"]  # array of accounts to watch
        #}
        #await websocket.send(json.dumps(payload))


        
        async for message in websocket:
            #print( json.loads(message))
            evaluate_token(json.loads(message))
            

# Run the subscribe function
asyncio.get_event_loop().run_until_complete(subscribe())