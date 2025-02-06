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

    # Criar colunas para organizar o layout
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("📊 Top 10 Produtos Mais Vendidos")

        # Selecionar os 10 produtos mais vendidos
        total_vendas_produtos = entrada.groupby("Aparelho")["SaleQt"].sum().reset_index()
        top_10_produtos = total_vendas_produtos.nlargest(10, "SaleQt")["Aparelho"].tolist()

        # Filtrar apenas esses produtos no dataset
        df_top = entrada[entrada["Aparelho"].isin(top_10_produtos)]

        # Criar tabela pivotada para organizar os dados corretamente
        df_pivot = df_top.pivot_table(index="Aparelho", columns="UF", values="SaleQt", aggfunc="sum").fillna(0)

        # Garantir que os produtos estejam ordenados corretamente em ordem decrescente
        df_pivot = df_pivot.loc[top_10_produtos[::-1]]

        # Ordenar as UFs da maior para a menor para que a maior fique na BASE das barras
        ufs_ordenadas = df_pivot.sum(axis=0).sort_values(ascending=False).index

        # Reorganizar a pivot_table para seguir essa ordem de UFs
        df_pivot = df_pivot[ufs_ordenadas]

        # Criar gráfico de barras empilhadas
        fig, ax = plt.subplots(figsize=(10, 6))
        df_pivot.plot(kind="barh", stacked=True, colormap="coolwarm", ax=ax)

        ax.set_title("Top 10 Produtos Mais Vendidos por UF", fontsize=14, color="white")
        ax.set_xlabel("Quantidade Vendida", fontsize=12, color="white")
        ax.set_ylabel("Aparelho", fontsize=12, color="white")

        # Ajustar a legenda dentro do gráfico
        plt.legend(title="UF", loc="lower right", fontsize=10, bbox_to_anchor=(1.0, 0.0))

        # Ajustar layout para evitar cortes
        plt.tight_layout()

        # Exibir o gráfico no Streamlit
        st.pyplot(fig)

    with col2:
        st.subheader("📋 Tabela de Produtos por UF")
        produto_selecionado = st.selectbox(
            "Selecione um produto:",
            entrada["Aparelho"].unique()
        )

        df_produto = entrada[entrada['Aparelho'] == produto_selecionado]

        preco_medio_produto = df_produto['Price'].mean()
        custo_medio_produto = df_produto['Cost'].mean()

        st.write(f"💰 **Preço Médio:** R$ {preco_medio_produto:.2f}")
        st.write(f"📉 **Custo Médio:** R$ {custo_medio_produto:.2f}")

        tabela_completa = (
            df_produto.groupby('UF').agg(
                Price=("Price", "mean"),
                Cost=("Cost", "mean"),
                Qty=("SaleQt", "sum")
            )
        ).reset_index()

        tabela_completa['SMS%'] = 1 - (tabela_completa['Cost'] / tabela_completa['Price'])
        tabela_completa = tabela_completa.round(2)

        st.write(f"📊 Dados por UF para **{produto_selecionado}**")
        st.dataframe(tabela_completa, height=400)

    # Criar colunas para análise detalhada
    col3, col4 = st.columns([2, 1])

    with col3:
        st.subheader("🔍 Análise de Precificação Geral")
        uf_selecionada = st.selectbox("Escolha uma UF para análise:", sorted(entrada["UF"].unique()))

        df_uf = entrada[entrada["UF"] == uf_selecionada]

        tabela_otimizada = df_uf.groupby("Aparelho").agg(
            Price=("Price", "mean"),
            Cost=("Cost", "mean"),
            Qty=("SaleQt", "sum"),
            Faturamento_Total=("SaleAmt", "sum"),
            Custo_Total=("SaleCostAmt", "sum")
        ).reset_index()

        tabela_otimizada["Margem"] = 1 - (tabela_otimizada["Custo_Total"] / tabela_otimizada["Faturamento_Total"])

        # Modelo de regressão linear para precificação ótima
        tabela_otimizada["Price Optimal"] = np.nan
        tabela_otimizada["New Qty"] = np.nan
        tabela_otimizada["New Revenue"] = np.nan

        for i, row in tabela_otimizada.iterrows():
            data_produto = df_uf[df_uf["Aparelho"] == row["Aparelho"]]

            if len(data_produto) > 2:
                X = data_produto["Price"].values.reshape(-1, 1)
                y = data_produto["SaleQt"].values.reshape(-1, 1)

                model = LinearRegression()
                model.fit(X, y)

                intercept = model.intercept_[0]
                slope = model.coef_[0][0]

                price_optimal = -intercept / (2 * slope)
                new_qty = intercept + slope * price_optimal
                new_revenue = new_qty * price_optimal

                tabela_otimizada.at[i, "Price Optimal"] = round(price_optimal, 2)
                tabela_otimizada.at[i, "New Qty"] = round(new_qty, 0)
                tabela_otimizada.at[i, "New Revenue"] = round(new_revenue, 2)

        st.write(f"📊 Precificação Ótima e Margem para Produtos na UF **{uf_selecionada}**")
        st.dataframe(tabela_otimizada, height=400)

    with col4:
        st.subheader("📈 Margem por UF")

        df_radar = entrada.groupby("UF").agg(
            Faturamento_Total=("SaleAmt", "sum"),
            Custo_Total=("SaleCostAmt", "sum")
        ).reset_index()

        df_radar["Margem_Total"] = 1 - (df_radar["Custo_Total"] / df_radar["Faturamento_Total"])

        # Criando o gráfico de radar
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=df_radar["Margem_Total"],
            theta=df_radar["UF"],
            fill='toself',
            name='Margem por UF'
        ))

        fig.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 1])
            ),
            title="Margem por UF"
        )

        st.plotly_chart(fig)

        st.plotly_chart(fig, use_container_width=True)
except Exception as e:
      st.error(f"❌ Erro ao carregar os dados: {e}")
