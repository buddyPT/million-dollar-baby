import websocket
import json
import time
from datetime import datetime

SOLANA_WS_URL = "wss://api.mainnet-beta.solana.com"
wallet_address = "9RE2n7FcNDybFmc29MJ7ND33FqxVzqwcreWpqpDvzG6r"

def on_message(ws, message):
    data = json.loads(message)
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"{current_time}: Nova transação detectada: \n\n")
    print(data)

def on_error(ws, error):
    print("Erro:", error)

def on_close(ws, close_status_code, close_msg):
    print("Conexão WebSocket encerrada:", close_msg)
    print("Tentando reconectar...")
    time.sleep(5)  # Aguardar alguns segundos antes de tentar reconectar
    connect_websocket()  # Tentar reconectar

def on_open(ws):
    print("Conexão WebSocket estabelecida")
    
    subscription_message = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "logsSubscribe",
        "params": [
            {
                "mentions": [wallet_address]
            },
            {
                "encoding": "jsonParsed"
            }
        ]
    }
    ws.send(json.dumps(subscription_message))

def connect_websocket():
    ws = websocket.WebSocketApp(SOLANA_WS_URL,
                                on_open=on_open,
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)
    ws.run_forever()  # Envia um ping a cada 30 segundos

# Iniciar a primeira conexão WebSocket
connect_websocket()
