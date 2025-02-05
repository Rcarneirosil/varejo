import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
from sklearn.linear_model import LinearRegression

# Expandir a tela para largura total
st.set_page_config(layout="wide")

# Configuração do fundo escuro
plt.rcParams["figure.facecolor"] = "#0E1117"
plt.rcParams["axes.facecolor"] = "#0E1117"
plt.rcParams["axes.edgecolor"] = "white"
plt.rcParams["axes.labelcolor"] = "white"
plt.rcParams["xtick.color"] = "white"
plt.rcParams["ytick.color"] = "white"
plt.rcParams["text.color"] = "white"
plt.rcParams["legend.edgecolor"] = "white"
plt.rcParams["grid.color"] = "#444444"
plt.rcParams["savefig.facecolor"] = "#0E1117"

# Título do aplicativo
st.title("📊 Análise de Vendas")

# URL do arquivo CSV no GitHub
csv_url = "https://raw.githubusercontent.com/Rcarneirosil/varejo/main/entrada.csv"

# Tentar carregar o arquivo CSV diretamente do GitHub
try:
    entrada = pd.read_csv(csv_url, sep=",", encoding="utf-8")
    entrada.columns = entrada.columns.str.strip()
    st.success("✅ Dados carregados com sucesso!")

    # Criar a terceira coluna para exibir a análise de preços ótimos + margem
    col3, _ = st.columns([2, 1])

    with col3:
        st.subheader("🔍 Análise Completa por UF")
        uf_selecionada = st.selectbox("Escolha uma UF para análise:", sorted(entrada["UF"].unique()))

        df_uf = entrada[entrada["UF"] == uf_selecionada]

        # Criar tabela base (Agrupamento correto com margem e faturamento total calculados da tabela original)
        tabela_otimizada = df_uf.groupby("Aparelho").agg(
            Price=("Price", "mean"),
            Cost=("Cost", "mean"),
            Qty=("SaleQt", "sum"),
            Faturamento_Total=("SaleAmt", "sum"),  # Faturamento total por aparelho
            Custo_Total=("SaleCostAmt", "sum")  # Custo total para margem correta
        ).reset_index()

        # Calcular a margem correta com base na tabela `entrada`
        tabela_otimizada["Margem"] = 1 - (tabela_otimizada["Custo_Total"] / tabela_otimizada["Faturamento_Total"])

        # Adicionar colunas vazias para cálculos de otimização
        tabela_otimizada["Price Optimal"] = np.nan
        tabela_otimizada["New Qty"] = np.nan
        tabela_otimizada["New Revenue"] = np.nan
        tabela_otimizada["Elasticity"] = np.nan

        for i, row in tabela_otimizada.iterrows():
            data_produto = df_uf[df_uf["Aparelho"] == row["Aparelho"]]

            if len(data_produto) > 2:
                X = data_produto["Price"].values.reshape(-1, 1)
                y = data_produto["SaleQt"].values.reshape(-1, 1)

                model = LinearRegression()
                model.fit(X, y)

                intercept = model.intercept_[0]
                slope = model.coef_[0][0]

                mean_price = data_produto["Price"].mean()
                mean_quantity = data_produto["SaleQt"].mean()
                elasticity = (slope * mean_price) / mean_quantity
                price_optimal = -intercept / (2 * slope)

                new_qty = intercept + slope * price_optimal
                new_revenue = new_qty * price_optimal

                tabela_otimizada.at[i, "Price Optimal"] = round(price_optimal, 2)
                tabela_otimizada.at[i, "New Qty"] = round(new_qty, 0)
                tabela_otimizada.at[i, "New Revenue"] = round(new_revenue, 2)
                tabela_otimizada.at[i, "Elasticity"] = round(elasticity, 2)

        # Exibir a tabela atualizada com os cálculos corrigidos
        st.write(f"📊 Análise de Precificação Ótima, Margem e Faturamento para Produtos na UF **{uf_selecionada}**")
        st.dataframe(tabela_otimizada, height=400)

except Exception as e:
    st.error(f"❌ Erro ao carregar os dados: {e}")
