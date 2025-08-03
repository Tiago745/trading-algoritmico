from binance.client import Client
import pandas as pd

# A chave da API não é necessária para pegar dados históricos
client = Client(api_key='', api_secret='')

# Função para pegar dados históricos de velas
def get_historical_klines(symbol, interval, start_str=None, end_str=None):
    return client.get_historical_klines(symbol, interval, start_str, end_str)

symbol = 'BTCUSDT'
interval = Client.KLINE_INTERVAL_12HOUR
start_str = '20 Jul, 2017'
end_str = '20 Jul, 2025'

klines = get_historical_klines(symbol, interval, start_str, end_str)

# Converte os dados para um DataFrame do Pandas
df = pd.DataFrame(klines, 
                    columns=['timestamp', 'open', 'high', 'low', 'close', 'volume',
                            'close_time', 'quote_asset_volume', 'number_of_trades',
                            'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume',
                            'ignore'
                            ] )

# Converte o timestamp para um formato legível
df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

# Salva o DataFrame em um arquivo CSV
df.to_csv(f'data/fechamentos/{symbol}_{interval}_data.csv', index=False)