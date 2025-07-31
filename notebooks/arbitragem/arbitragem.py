import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from statsmodels.tsa.stattools import coint
import itertools



# Carregar dados
def carregar_dados(moeda1, moeda2):

    path_ativo_1 = f'../../data/fechamentos/{moeda1}USDT_5m_data.csv'
    path_ativo_2 = f'../../data/fechamentos/{moeda2}USDT_5m_data.csv'

    ativo1 = pd.read_csv(path_ativo_1, parse_dates=['timestamp'], index_col='timestamp')
    ativo2 = pd.read_csv(path_ativo_2, parse_dates=['timestamp'], index_col='timestamp')

    # Elimina NaNs restantes
    df = pd.DataFrame({
        'Ativo1': ativo1['close'],
        'Ativo2': ativo2['close']
    }).dropna()

    return df



# Teste de cointegração
def testar_cointegracao(series1, series2):
    _, pvalor, _ = coint(series1, series2)
    return pvalor

# Zscore
def calcular_zscore(spread, window=60):
    rolling_mean = spread.rolling(window=window).mean() #média da última janela
    rolling_std = spread.rolling(window=window).std() #desvio padrão da última janela

    # Substituir stds muito baixos por um mínimo
    epsilon = 1e-8
    rolling_std = rolling_std.replace(0, epsilon).fillna(epsilon)

    zscore = (spread - rolling_mean) / rolling_std  #zscore = (x- média_janela)/(desvio_padrao_janela)

    return rolling_mean, rolling_std, zscore #média da janela, desvio padrao, zscore

# Zscore
def calcular_media_ativos(ativo1, ativo2, window=60):
    ativo1_mean = ativo1.rolling(window=window).mean() #média da última janela
    ativo2_mean = ativo2.rolling(window=window).mean() #média da última janela

    ativo1_std = ativo1.rolling(window=window).std() #std da media movel
    ativo2_std = ativo2.rolling(window=window).std() #std da media movel


    return ativo1_mean, ativo2_mean, ativo1_std, ativo2_std  #média da janela, desvio padrao, zscore


#spread
def calcular_spread(serie1, serie2):
    serie1 = pd.to_numeric(serie1, errors='coerce')
    serie2 = pd.to_numeric(serie2, errors='coerce')
    spread = serie1 - serie2

    return spread

# Estratégia de sinalização
def gerar_sinais(df, zscore_compra_e_venda, zscore_encerrar_posicao, stop_loss, cooldown_stop_loss, janela):
    series1 = df['Ativo1']
    series2 = df['Ativo2']

    limite_superior =zscore_compra_e_venda
    limite_inferior = -zscore_compra_e_venda

    spread = calcular_spread(series1, series2)
    rolling_mean, rolling_std, zscore = calcular_zscore(spread, janela) #Zscore com janela movel
    media_movel_ativo1, media_movel_ativo2, ativo1_std, ativo2_std = calcular_media_ativos(series1, series2, janela) #media movel do ativo 1 e 2

    nomes_posicoes = ["neutro", "compra_1_vende_2", "vende_1_compra_2"]
    posicao = nomes_posicoes[0] #comprado_vendido, vendido_comprado, encerrar, Neutro

    
    sinais_compra_e_venda = []

    for i in range(len(df)):
        linha_df = df.iloc[i]
        if zscore.iloc[i] > limite_superior:
            posicao = nomes_posicoes[2] #entra vendido no ativo 1 e comprado no 2
        if zscore.iloc[i] < -limite_inferior:
            posicao = nomes_posicoes[1] #entra comprado no ativo 1 e vendido no 2
        if (-0.5 < zscore.iloc[i] < zscore_encerrar_posicao):
            posicao = nomes_posicoes[0] #posicao mantem neutra ou encerra posicao anterior
        ##if stoploss
        sinais_compra_e_venda.append(posicao)
    
    # Resultado final
    df_sinais = pd.DataFrame({
        'timestamp': df.index,
        'Ativo1': pd.to_numeric(series1, errors='coerce'),
        'Ativo2': pd.to_numeric(series2, errors='coerce'),
        'ativo1_mean': media_movel_ativo1,
        'ativo2_mean': media_movel_ativo2,
        'ativo1_std': ativo1_std, 
        'ativo2_std': ativo2_std,
        'spread': pd.to_numeric(spread, errors='coerce'),
        'rolling_mean': rolling_mean.values,
        'rolling_std': rolling_std.values,
        'zscore': zscore.values,
        'sinal': sinais_compra_e_venda
    }).dropna()
    
    df_sinais.to_excel('resultados/estrategia.xlsx', index=False)

    return df_sinais


def simular_retorno_por_trade(df, capital_inicial=10000):
    series1 = df['Ativo1'] #cotação ativo 1
    series2 = df['Ativo2'] #cotação ativo 2
    sinais = df['sinal']   #sinal compra e venda
    capital = capital_inicial
    capital_series = [capital]
    posicao = None
    entrada_indice = None

    retornos_trade = [None] 
    

    for i in range(1, len(sinais)):
        ret = None  # retorno naquele ponto
        if posicao is None and sinais.iloc[i] != 'neutro':
            posicao = sinais.iloc[i]
            entrada_indice = i
        elif posicao is not None and sinais.iloc[i] == 'neutro':
            if posicao == 'compra_1_vende_2':
                ret = ((series1.iloc[i] - series1.iloc[entrada_indice]) / series1.iloc[entrada_indice]) - \
                      ((series2.iloc[i] - series2.iloc[entrada_indice]) / series2.iloc[entrada_indice])
            else:
                ret = ((series2.iloc[i] - series2.iloc[entrada_indice]) / series2.iloc[entrada_indice]) - \
                      ((series1.iloc[i] - series1.iloc[entrada_indice]) / series1.iloc[entrada_indice])

            capital *= (1 + ret)
            posicao = None
            entrada_indice = None

        capital_series.append(capital)
        retornos_trade.append(ret)

    retorno_pct = (capital / capital_inicial) - 1

    df_resultado = df.copy()

    #retornos
    df_resultado['capital'] = capital_series
    df_resultado['retorno_trade'] = retornos_trade


    return capital, retorno_pct, capital_series, df_resultado

def simular_estrategia(moeda1, moeda2, zscore_compra_e_venda, zscore_encerrar_posicao, 
                       stop_loss, cooldown_stop_loss, janela, capital_inicial=10000):
    
    # Carregar dados
    df = carregar_dados(moeda1, moeda2)

    # Testar cointegração
    p_valor = testar_cointegracao(df['Ativo1'], df['Ativo2'])
    if p_valor > 0.05:
        print(f"As séries {moeda1}-{moeda2} não são cointegradas (p-valor = {p_valor:.4f})")
        return None, None, None

    # Gerar sinais
    df_sinais = gerar_sinais(df, zscore_compra_e_venda, zscore_encerrar_posicao, stop_loss, cooldown_stop_loss, janela)

    # Simular retorno
    capital_final, retorno_pct, capital_series, df_resultado = simular_retorno_por_trade(df_sinais, capital_inicial)

    # Calcular retornos percentuais por trade
    retornos_trade = df_resultado['retorno_trade'].dropna()

    # Calcular métricas
    sharpe = calcular_sharpe(retornos_trade)
    retorno_risco = retorno_ajustado_ao_risco(retornos_trade)

    return retorno_pct, retorno_risco, sharpe

def retorno_ajustado_ao_risco(serie_retorno):
    serie_retorno = pd.Series(serie_retorno).dropna()
    if len(serie_retorno) == 0:
        return 0
    retorno_total = (1 + serie_retorno).prod() - 1
    risco = serie_retorno.std()
    if risco == 0:
        return 0
    return retorno_total / risco

def calcular_sharpe(serie_retorno, taxa_livre_risco=0.0):
    serie_retorno = pd.Series(serie_retorno).dropna()
    if len(serie_retorno) == 0:
        return 0
    media_excesso_retorno = serie_retorno.mean() - taxa_livre_risco
    desvio = serie_retorno.std()
    if desvio == 0:
        return 0
    sharpe = media_excesso_retorno / desvio
    return sharpe
    