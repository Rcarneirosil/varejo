import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# 1️⃣ - Calcular o total de vendas por produto (independente da UF)
total_vendas_produtos = entrada.groupby("Aparelho")["SaleQt"].sum().reset_index()

# 2️⃣ - Selecionar os Top 10 produtos mais vendidos
top_10_produtos = total_vendas_produtos.nlargest(10, "SaleQt")["Aparelho"]

# 3️⃣ - Filtrar apenas esses produtos no dataset original
df_top = entrada[entrada["Aparelho"].isin(top_10_produtos)]

# 4️⃣ - Criar tabela pivotada para organizar os dados corretamente
df_pivot = df_top.pivot_table(index="Aparelho", columns="UF", values="SaleQt", aggfunc="sum").fillna(0)

# 5️⃣ - Ordenar os produtos pelo total de vendas no dataset filtrado
df_pivot = df_pivot.loc[top_10_produtos]

# 6️⃣ - Converter para o formato adequado para o gráfico empilhado
df_top_agg = df_pivot.reset_index().melt(id_vars=["Aparelho"], var_name="UF", value_name="SaleQt")

# 7️⃣ - Criar o gráfico de barras empilhadas
fig, ax = plt.subplots(figsize=(10, 6))
sns.barplot(
    data=df_top_agg,
    x="SaleQt",
    y="Aparelho",
    hue="UF",  # 🔥 Empilhado por UF
    palette="coolwarm",
    estimator=sum,
    ci=None,
    dodge=False,  # 🔥 Faz as barras ficarem empilhadas
    ax=ax,
)

# 🔟 - Ajustar título e rótulos
ax.set_title("Top 10 Produtos Mais Vendidos por UF", fontsize=14, color="black")
ax.set_xlabel("Quantidade Vendida", fontsize=12, color="black")
ax.set_ylabel("Aparelho", fontsize=12, color="black")
plt.legend(title="UF", loc="upper right", fontsize=10)
plt.tight_layout()

# 🔥 Exibir o gráfico
plt.show()
