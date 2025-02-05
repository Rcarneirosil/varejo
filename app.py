import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
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
st.title("📊 Análise de Vendas de Produtos com Precificação Ótima")

# Carregar o arquivo CSV
uploaded_file = st.file_uploader("Carregue o arquivo 'entrada.csv'", type="csv")

if uploaded_file is not None:
    entrada = pd.read_csv(uploaded_file)

    #%% Seleção de Estado (UF)
    st.header("🔍 Selecione um Estado para Análise")
    uf_selecionada = st.selectbox("Escolha uma UF:", sorted(entrada["UF"].unique()))

    # Filtrar os dados apenas para a UF selecionada
    df_uf = entrada[entrada["UF"] == uf_selecionada]

    #%% Criar colunas para exibir gráfico e tabela de preços ótimos
    col1, col2 = st.columns([2, 1])  # Ajustando os tamanhos para melhor visualização

    with col1:
        st.subheader(f"📊 Vendas por Produto na UF {uf_selecionada}")
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.barplot(data=df_uf, x="Aparelho", y="SaleQt", palette="coolwarm", ax=ax)
        ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha="right", fontsize=10)
        ax.set_title(f"Vendas por Produto - {uf_selecionada}", fontsize=14, color="white")
        ax.set_xlabel("Produto", fontsize=12, color="white")
        ax.set_ylabel("Quantidade Vendida", fontsize=12, color="white")
        plt.tight_layout()
        st.pyplot(fig)

    with col2:
        st.subheader(f"📋 Resumo de Produtos na UF {uf_selecionada}")
        st.write(f"🔹 Total de Produtos: {df_uf['Aparelho'].nunique()}")
        st.write(f"📦 Total de Vendas: {df_uf['SaleQt'].sum()} unidades")

    #%% Cálculo do Preço Ótimo e Elasticidade-Preço da Demanda para todos os produtos
    st.header(f"📊 Precificação Ótima e Elasticidade - {uf_selecionada}")

    # Criar tabela base com os produtos da UF
    tabela_otimizada = df_uf.groupby("Aparelho").agg(
        Price=("Price", "mean"),
        Cost=("Cost", "mean"),
        Qty=("SaleQt", "sum")
    ).reset_index()

    # Adicionar colunas vazias para cálculos
    tabela_otimizada["Price Optimal"] = np.nan
    tabela_otimizada["New Qty"] = np.nan
    tabela_otimizada["New Revenue"] = np.nan
    tabela_otimizada["Elasticity"] = np.nan

    # Aplicar modelo de regressão para cada produto
    for i, row in tabela_otimizada.iterrows():
        data_produto = df_uf[df_uf["Aparelho"] == row["Aparelho"]]

        if len(data_produto) > 2:  # Pelo menos 2 pontos para regressão
            X = data_produto["Price"].values.reshape(-1, 1)
            y = data_produto["SaleQt"].values.reshape(-1, 1)

            model = LinearRegression()
            model.fit(X, y)

            intercept = model.intercept_[0]
            slope = model.coef_[0][0]

            # Elasticidade e preço ótimo
            mean_price = data_produto["Price"].mean()
            mean_quantity = data_produto["SaleQt"].mean()
            elasticity = (slope * mean_price) / mean_quantity
            price_optimal = -intercept / (2 * slope)

            # Estimar nova quantidade e receita com o preço ótimo
            new_qty = intercept + slope * price_optimal
            new_revenue = new_qty * price_optimal

            # Adicionar ao DataFrame
            tabela_otimizada.at[i, "Price Optimal"] = round(price_optimal, 2)
            tabela_otimizada.at[i, "New Qty"] = round(new_qty, 0)
            tabela_otimizada.at[i, "New Revenue"] = round(new_revenue, 2)
            tabela_otimizada.at[i, "Elasticity"] = round(elasticity, 2)

    # Exibir a tabela com os preços ótimos
    st.dataframe(tabela_otimizada, height=400)

else:
    st.warning("🚨 Por favor, carregue o arquivo 'entrada.csv' para continuar.")
