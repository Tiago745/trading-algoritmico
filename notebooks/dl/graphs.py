import pandas as pd
import matplotlib.pyplot as plt

# Cria um gráfico de volatilidade das trades
symbols = ['BTCUSDT','ETHUSDT','XRPUSDT', 'BCHUSDT', 'LTCUSDT', 'EOSUSDT', 'BNBUSDT', 'XLMUSDT', 'TRXUSDT', 'ADAUSDT', 'XTZUSDT', 'SOLUSDT']

# Parâmetros para o cálculo da volatilidade anualizada
days_in_year = 365
hours_in_day = 24
annualization_factor = (days_in_year * hours_in_day)**0.5

# Janela de 30 dias em horas para o rolling
window_30_days = 30 * hours_in_day

# Condição para executar a geração de gráficos
conf = True

if conf:
    for symbol in symbols:
        trades = pd.read_csv(f'figures/ml/trades_{symbol}.csv')
        
        trades['Timestamp'] = pd.to_datetime(trades['Timestamp'])
        trades.set_index('Timestamp', inplace=True)
        
        # --- Cálculo da volatilidade da estratégia (em cima de Saldo_norm) ---
        trades['retornos_percentuais'] = trades['Saldo_norm'].pct_change()
        trades['volatilidade_anualizada_percentual'] = trades['retornos_percentuais'].rolling(window=window_30_days).std() * annualization_factor * 100

        # --- Cálculo da volatilidade da moeda (em cima de Valor_norm) ---
        trades['retornos_moeda'] = trades['Valor_norm'].pct_change()
        trades['volatilidade_anualizada_moeda'] = trades['retornos_moeda'].rolling(window=window_30_days).std() * annualization_factor * 100

        # Cria o gráfico
        plt.figure(figsize=(14, 7))
        
        # Plota a volatilidade da estratégia em vermelho
        plt.plot(trades.index, trades['volatilidade_anualizada_percentual'], label=f'Volatilidade da Estratégia (30 dias)', color='red')
        
        # Plota a volatilidade da moeda em azul para comparação
        plt.plot(trades.index, trades['volatilidade_anualizada_moeda'], label=f'Volatilidade da Moeda (30 dias)', color='blue', linestyle='--')
        
        plt.title(f'Comparação de Volatilidade - {symbol}')
        plt.xlabel('Data')
        plt.ylabel('Volatilidade Anualizada (%)')
        plt.legend()
        plt.grid(True)
        
        # Salva a imagem
        plt.savefig(f'figures/ml/comparacao_volatilidade_{symbol}.png', dpi=300, bbox_inches='tight')
        
        # Exibe o gráfico e fecha a figura
        plt.show()
        plt.close()