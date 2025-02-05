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
        st.subheader("📊 Gráfico de Produtos Mais Vendidos por UF")

        # 1️⃣ - Calcular o total de vendas por produto (independente da UF)
        total_vendas_produtos = entrada.groupby("Aparelho")["SaleQt"].sum().reset_index()

        # 2️⃣ - Selecionar os Top 10 produtos mais vendidos (ordenados corretamente)
        top_10_produtos = (
            total_vendas_produtos
            .nlargest(10, "SaleQt")  # Pega os 10 maiores
            .sort_values("SaleQt", ascending=True)  # 🔥 Inverter a ordem para gráfico horizontal correto
            ["Aparelho"]
            .tolist()
        )

        # 3️⃣ - Filtrar apenas esses produtos no dataset original
        df_top = entrada[entrada["Aparelho"].isin(top_10_produtos)]

        # 4️⃣ - Criar tabela pivotada para organizar os dados corretamente
        df_pivot = df_top.pivot_table(index="Aparelho", columns="UF", values="SaleQt", aggfunc="sum").fillna(0)

        # 5️⃣ - Garantir que os produtos estejam ordenados corretamente no gráfico
        df_pivot = df_pivot.loc[top_10_produtos]

        # 6️⃣ - Ordenar as UFs da maior para a menor para que a maior fique na BASE das barras
        ufs_ordenadas = df_pivot.sum(axis=0).sort_values(ascending=False).index  # 🔥 UFs com mais vendas primeiro

        # 7️⃣ - Reorganizar a pivot_table para seguir essa ordem de UFs
        df_pivot = df_pivot[ufs_ordenadas]

        # 8️⃣ - Criar gráfico de barras empilhadas
        fig, ax = plt.subplots(figsize=(10, 6))
        df_pivot.plot(kind="barh", stacked=True, colormap="coolwarm", ax=ax)

        # 9️⃣ - Ajustar título e rótulos
        ax.set_title("Top 10 Produtos Mais Vendidos por UF", fontsize=14, color="black")
        ax.set_xlabel("Quantidade Vendida", fontsize=12, color="black")
        ax.set_ylabel("Aparelho", fontsize=12, color="black")

        # 🔟 - Ajustar a legenda dentro do gráfico
        plt.legend(title="UF", loc="lower right", fontsize=10, bbox_to_anchor=(1.0, 0.0))

        # 🔥 Ajustar layout para evitar cortes
        plt.tight_layout()

        # 🔥 Exibir o gráfico no Streamlit
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

except Exception as e:
    st.error(f"❌ Erro ao carregar os dados: {e}")
