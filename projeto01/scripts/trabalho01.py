# -*- coding: utf-8 -*-
"""
Created on Mon May  5 19:57:04 2025

@author: Bianca e Ana Julia
"""
#%% Importar bibliotecas
import pandas as pd
import matplotlib.pyplot as plt
import os
from scipy.stats import shapiro, kruskal
import pymannkendall as mk
import seaborn as sns

#%% Importar asquivos csv
caminho_pasta = r"C:\Users\BiaBN\OneDrive\Documentos\ENS5132\projeto01\inputs\SP"
arquivos_csv = os.listdir(caminho_pasta)
lista_dfs= []
for arquivo in arquivos_csv:
    df = pd.read_csv(os.path.join(caminho_pasta, arquivo),encoding='latin1')
    lista_dfs.append(df) 
    
df_final = pd.concat(lista_dfs, ignore_index=True)
df_final = df_final[df_final['Valor'] <= 10000]
#%% Reformatando dataframe
def formatar_df_iema (df):
    df['Data'] = pd.to_datetime(df['Data'])
    
    # Extraindo ano, mês e dia
    df['Ano'] = df['Data'].dt.year
    df['Mes'] = df['Data'].dt.month
    df['Dia'] = df['Data'].dt.day
    
    df = df.rename(columns={'Hora': 'Horario'})
    
    df['Horario'] = df['Horario'].str.replace('24:00', '00:00')
    df['Horario'] = df['Horario'].str.slice(0, 5)
    df['Horario'] = pd.to_datetime(df['Horario'], format='%H:%M', errors='coerce')
    df['Hora'] = df['Horario'].dt.hour
    df['Minuto'] = df['Horario'].dt.minute
    del df['Data'], df['Horario']
    df['Poluente'] = df['Poluente'].astype(str).str.replace('MP2.5', 'MP25', regex=False)
    return df
df_final= formatar_df_iema(df_final)
#%% Colocando datetime como index
df_final['datetime'] = pd.to_datetime(
    df_final[['Ano', 'Mes', 'Dia', 'Hora', 'Minuto']].rename(
        columns={'Ano': 'year', 'Mes': 'month', 'Dia': 'day', 'Hora': 'hour', 'Minuto': 'minute'}
    ))
df_final["dia_semana"] = df_final["datetime"].dt.dayofweek
df_final.set_index('datetime', inplace=True)

#%% Resultados estatisticos
# ---- Listas para armazenar os resultados ----
normalidade_resultados = []
mann_kendall_resultados = []
sazonalidade_semanal_resultados = []
sazonalidade_mensal_resultados = []

# ---- Loop por estação e poluente ----
for estacao in df_final["Estacao"].unique():
    for poluente in df_final["Poluente"].unique():
        subset = df_final[(df_final["Estacao"] == estacao) & (df_final["Poluente"] == poluente)].copy()
        valores = subset["Valor"].dropna()

        # Teste de normalidade (Shapiro-Wilk)
        if len(valores) >= 3:
            sample = valores.sample(min(len(valores), 5000), random_state=42)
            stat, p_shapiro = shapiro(sample)
            normalidade_resultados.append({
                "Estacao": estacao,
                "Poluente": poluente,
                "p_shapiro": p_shapiro
            })

        #Teste de tendência (Mann-Kendall)
        serie_mensal = subset.resample("ME")["Valor"].mean().dropna()
        if len(serie_mensal) >= 8:
            mk_result = mk.original_test(serie_mensal)
            mann_kendall_resultados.append({
                "Estacao": estacao,
                "Poluente": poluente,
                "trend": mk_result.trend,
                "p_value": mk_result.p,
                "slope": mk_result.slope
            })

        # Sazonalidade semanal (Kruskal-Wallis)
        grupos_semana = [g["Valor"].dropna() for _, g in subset.groupby("dia_semana")]
        grupos_semana_validos = [g for g in grupos_semana if len(g) > 1]
        if len(grupos_semana_validos) >= 2:
            stat, p_kruskal_sem = kruskal(*grupos_semana_validos)
            sazonalidade_semanal_resultados.append({
                "Estacao": estacao,
                "Poluente": poluente,
                "p_kruskal_semanal": p_kruskal_sem
            })
        
        # Sazonalidade mensal (Kruskal-Wallis)
        grupos_mes = [g["Valor"].dropna() for _, g in subset.groupby("Mes")]
        grupos_mes_validos = [g for g in grupos_mes if len(g) > 1]
        if len(grupos_mes_validos) >= 2:
            stat, p_kruskal_mes = kruskal(*grupos_mes_validos)
            sazonalidade_mensal_resultados.append({
                "Estacao": estacao,
                "Poluente": poluente,
                "p_kruskal_mensal": p_kruskal_mes
            })

#%%---- Resultados em DataFrames ----
df_normalidade = pd.DataFrame(normalidade_resultados)
df_mk = pd.DataFrame(mann_kendall_resultados)
df_sazonal_sem = pd.DataFrame(sazonalidade_semanal_resultados)
df_sazonal_mes = pd.DataFrame(sazonalidade_mensal_resultados)

#%% ---- Salvar os resultados ----
df_normalidade.to_csv(r'C:\Users\BiaBN\OneDrive\Documentos\ENS5132\projeto01\outputs\normalidade.csv', index=False)
df_mk.to_csv(r'C:\Users\BiaBN\OneDrive\Documentos\ENS5132\projeto01\outputs\tendencia_mk.csv', index=False)
df_sazonal_sem.to_csv(r'C:\Users\BiaBN\OneDrive\Documentos\ENS5132\projeto01\outputs\sazonal_sem.csv', index=False)
df_sazonal_mes.to_csv(r'C:\Users\BiaBN\OneDrive\Documentos\ENS5132\projeto01\outputs\sazonal_mes.csv', index=False)

# Você pode salvar cada um em CSV também:
# df_mk.to_csv("tendencia_mk.csv", index=False)

#%% Fazendo gráficos
sns.set(style="whitegrid")
plt.rcParams["figure.figsize"] = (12, 6)

#%%     HISTOGRAMA
for estacao in df_final["Estacao"].unique():
    pasta_estacao = r'C:\Users\BiaBN\OneDrive\Documentos\ENS5132\projeto01\outputs\ ' + estacao
    os.makedirs(pasta_estacao, exist_ok=True)
    for poluente in df_final["Poluente"].unique():
        dados = df_final[(df_final["Estacao"] == estacao) & (df_final["Poluente"] == poluente)].copy()

        if len(dados) < 50:
            continue  # pula se poucos dados
   
        sns.histplot(data=dados, x="Valor", bins=30, kde=True)
        plt.title(f"Histograma - {poluente} ({estacao})")
        plt.xlabel("Valor")
        plt.ylabel("Frequência")
        plt.tight_layout()
        plt.savefig(f"{pasta_estacao}/histograma_{poluente}.png")
        plt.close()
        print(estacao)
 
        #%% SÉRIE TEMPORAL
for estacao in df_final["Estacao"].unique():
    for poluente in df_final["Poluente"].unique():
        dados = df_final[(df_final["Estacao"] == estacao) & (df_final["Poluente"] == poluente)].copy()

        if len(dados) < 50:
            continue  # pula se poucos dados
        serie_diaria = dados.resample("D")["Valor"].mean().dropna()
        serie_diaria.plot()
        plt.title(f"Série Temporal Diária - {poluente} ({estacao})")
        plt.ylabel("Valor médio diário")
        plt.xlabel("Data")
        plt.tight_layout()
        plt.savefig(f"{pasta_estacao}/serie_temporal_{poluente}.png")
        plt.close()

        #%% BOXPLOT por ANO
for estacao in df_final["Estacao"].unique():
    for poluente in df_final["Poluente"].unique():
        dados = df_final[(df_final["Estacao"] == estacao) & (df_final["Poluente"] == poluente)].copy()

        if len(dados) < 50:
            continue  # pula se poucos dados
        sns.boxplot(data=dados, x="Ano", y="Valor")
        plt.title(f"Boxplot por Ano - {poluente} ({estacao})")
        plt.tight_layout()
        plt.savefig(f"{pasta_estacao}/boxplot_ano_{poluente}.png")
        plt.close()
   

        #%% BOXPLOT por MÊS
for estacao in df_final["Estacao"].unique():
    for poluente in df_final["Poluente"].unique():
        dados = df_final[(df_final["Estacao"] == estacao) & (df_final["Poluente"] == poluente)].copy()

        if len(dados) < 50:
            continue  # pula se poucos dados
        sns.boxplot(data=dados, x="Mes", y="Valor")
        plt.title(f"Boxplot por Mês - {poluente} ({estacao})")
        plt.xlabel("Mês")
        plt.tight_layout()
        plt.savefig(f"{pasta_estacao}/boxplot_mes_{poluente}.png")
        plt.close()
        
        #%% BOXPLOT por DIA DA SEMANA
dias = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
dia_dict = dict(zip(range(7), dias))

for estacao in df_final["Estacao"].unique():
    pasta_estacao = f"graficos/{estacao.replace('/', '_')}"
    os.makedirs(pasta_estacao, exist_ok=True)

    for poluente in df_final["Poluente"].unique():
        # Filtra os dados da estação e poluente
        dados = df_final[(df_final["Estacao"] == estacao) & (df_final["Poluente"] == poluente)].copy()

        if len(dados) < 50:
            continue

        # Garante que o índice seja datetime
        dados.index = pd.to_datetime(dados.index)

        # Cria colunas de dia da semana
        dados["dia_semana"] = dados.index.dayofweek
        dados["dia_nome"] = dados["dia_semana"].map(dia_dict)

        # Verifica se a coluna foi criada
        if "dia_nome" not in dados.columns:
            print(f"[ERRO] dia_nome não criada para {estacao} - {poluente}")
            continue

        # Gera o gráfico
        sns.boxplot(data=dados, x="dia_nome", y="Valor", order=dias)
        plt.title(f"Boxplot por Dia da Semana - {poluente} ({estacao})")
        plt.xlabel("Dia da Semana")
        plt.tight_layout()
        plt.savefig(f"{pasta_estacao}/boxplot_dia_semana_{poluente}.png")
        plt.close()

        #%% BOXPLOT por HORA
for estacao in df_final["Estacao"].unique():
    for poluente in df_final["Poluente"].unique():
        dados = df_final[(df_final["Estacao"] == estacao) & (df_final["Poluente"] == poluente)].copy()

        if len(dados) < 50:
            continue  # pula se poucos dados
        sns.boxplot(data=dados, x="Hora", y="Valor")
        plt.title(f"Boxplot por Hora do Dia - {poluente} ({estacao})")
        plt.xlabel("Hora")
        plt.tight_layout()
        plt.savefig(f"{pasta_estacao}/boxplot_hora_{poluente}.png")
        plt.close()
    
#%%
print(dados.columns)