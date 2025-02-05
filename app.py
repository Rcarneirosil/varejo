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
st.title("📊 Análise de Vendas")

# URL do arquivo CSV no GitHub (corrigida para o formato correto)
csv_url = "https://raw.githubusercontent.com/Rcarneirosil/varejo/main/entrada.csv"

# Tentar carregar o arquivo CSV diretamente do GitHub
try:
    entrada = pd.read_csv(csv_url, sep=",", encoding="utf-8")
    entrada.columns = entrada.columns.str.strip()
    st.success("✅ Dados carregados com sucesso!")

    # Criar colunas para organizar o layout
    col1, col2 = st.columns([2, 1])  # Mantendo layout original

    with col1:
        st.subheader("📊 Gráfico de Produtos Mais Vendidos")
        top_produtos = entrada.groupby("Aparelho")["SaleQt"].sum().sort_values(ascending=True)  # Inverter para gráfico horizontal
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.barplot(y=top_produtos.tail(10).index, x=top_produtos.tail(10).values, palette="coolwarm", ax=ax)  # Gráfico de barras horizontais
        ax.set_yticklabels(ax.get_yticklabels(), fontsize=10)
        ax.set_title("Top 10 Produtos Mais Vendidos", fontsize=14, color="white")
        ax.set_xlabel("Quantidade Vendida", fontsize=12, color="white")
        ax.set_ylabel("Aparelho", fontsize=12, color="white")
        plt.tight_layout()
        st.pyplot(fig)

    with col2:
        st.subheader("📋 Tabela de Produtos por UF")
        produto_selecionado = st.selectbox(
            "Selecione um produto:",
            entrada["Aparelho"].unique()
        )

        df_produto = entrada[entrada['Aparelho'] == produto_selecionado]

        vendas_por_uf = df_produto.groupby("UF")["SaleQt"].sum().reset_index()

        preco_medio_produto = df_produto['Price'].mean()
        custo_medio_produto = df_produto['Cost'].mean()

        st.write(f"💰 **Preço Médio:** R$ {preco_medio_produto:.2f}")
        st.write(f"📉 **Custo Médio:** R$ {custo_medio_produto:.2f}")

        preco_medio_por_uf = df_produto.groupby('UF')['Price'].mean().reset_index()
        custo_medio_por_uf = df_produto.groupby('UF')['Cost'].mean().reset_index()
        qtd_por_uf = df_produto.groupby('UF')['SaleQt'].sum().reset_index()

        tabela_completa = (
            preco_medio_por_uf
            .merge(custo_medio_por_uf, on='UF', suffixes=('_Preço', '_Custo'))
            .merge(qtd_por_uf, on='UF')
        )

        tabela_completa = tabela_completa.rename(columns={'SaleQt': 'Qty'})
        tabela_completa['SMS%'] = 1 - (tabela_completa['Cost'] / tabela_completa['Price'])
        tabela_completa = tabela_completa.round(2)

        st.write(f"📊 Dados por UF para **{produto_selecionado}**")
        st.dataframe(tabela_completa, height=400)

    # Criar colunas para a análise por UF
    col3, col4 = st.columns([1.5, 1.5])  # Ajuste para melhor distribuição do layout

    with col3:
        st.subheader("🔍 Análise Completa por UF")
        uf_selecionada = st.selectbox("Escolha uma UF para análise:", sorted(entrada["UF"].unique()))

        # Filtrar dados da UF selecionada
        df_uf = entrada[entrada["UF"] == uf_selecionada]

        # Criar tabela base (Agrupamento correto)
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

        # Aplicar modelo de regressão para cada produto **usando df_uf, sem agrupamento**
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

        # Exibir a tabela na col3
        st.write(f"📊 Análise de Precificação Ótima para Produtos na UF **{uf_selecionada}**")
        st.dataframe(tabela_otimizada, height=400)

    with col4:
        st.subheader("📈 Análise de Margem e Mix na UF")
        df_margem = df_uf.copy()
        df_margem["Margem"] = (df_margem["Price"] - df_margem["Cost"]) / df_margem["Price"]
        
        # Agrupar dados por aparelho e calcular margem média
        margem_mix = df_margem.groupby("Aparelho").agg(
            Margem=("Margem", "mean"),
            Qtde=("SaleQt", "sum")
        ).reset_index()

        # Criar gráfico de margem por aparelho
        fig, ax = plt.subplots(figsize=(8, 5))
        sns.barplot(y=margem_mix["Aparelho"], x=margem_mix["Margem"], palette="viridis", ax=ax)
        ax.set_title(f"Margem Média por Produto - {uf_selecionada}", fontsize=14, color="white")
        ax.set_xlabel("Margem (%)", fontsize=12, color="white")
        ax.set_ylabel("Produto", fontsize=12, color="white")
        plt.tight_layout()
        st.pyplot(fig)

        # Exibir tabela de mix e margem
        margem_mix = margem_mix.round(2)
        st.write(f"📊 Margem e Mix de Produtos na UF **{uf_selecionada}**")
        st.dataframe(margem_mix, height=400)

except Exception as e:
    st.error(f"❌ Erro ao carregar os dados: {e}")
