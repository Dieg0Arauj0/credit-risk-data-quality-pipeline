from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st


st.set_page_config(page_title="Risco de crédito", layout="wide")
st.title("Avaliação dos modelos de risco de crédito")

pasta_resultados = Path(__file__).resolve().parent / "data" / "processed"
arquivos = ["metricas_modelos.csv", "cobertura_teste.csv", "curvas_roc.csv", "matrizes_confusao.csv", "efeito_teto_utilizacao.csv", "validacoes_pandera.csv"]

faltantes = [nome for nome in arquivos if not (pasta_resultados / nome).is_file()]
if faltantes:
    st.error(
        "Execute as células de exportação do notebook "
        f"02_limpeza_pre_modelagem.ipynb. Arquivos pendentes: {', '.join(faltantes)}."
    )
    st.stop()

metricas = pd.read_csv(pasta_resultados / "metricas_modelos.csv")
cobertura = pd.read_csv(pasta_resultados / "cobertura_teste.csv").set_index("recorte")
curvas = pd.read_csv(pasta_resultados / "curvas_roc.csv")

total = cobertura["registros"].sum()
comum = cobertura.loc["Na comparação direta", "registros"]
adicional = cobertura.loc["Fora da comparação direta", "registros"]

col_total, col_comum, col_adicional = st.columns(3)
col_total.metric("Registros no teste", f"{total:,}".replace(",", "."))
col_comum.metric("Comparação direta", f"{comum:,}".replace(",", "."))
col_adicional.metric("Registros adicionais tratados", f"{adicional:,}".replace(",", "."))

st.subheader("Comparação no teste comum")
modelo = st.selectbox("Algoritmo", ["Regressão logística", "Random Forest"])

metricas_modelo = metricas.loc[
    metricas["recorte"].eq("Teste comum") & metricas["modelo"].eq(modelo)
].set_index("abordagem")

tabela = metricas_modelo[["ROC-AUC", "KS"]].round(4)
tabela["Recall da classe 1 (%)"] = (
    metricas_modelo["recall_classe_1"] * 100
).round(2)
st.dataframe(tabela)

curvas_modelo = curvas.loc[curvas["modelo"].eq(modelo)]

fig = px.line(
    curvas_modelo,
    x="taxa_falsos_positivos",
    y="taxa_verdadeiros_positivos",
    color="abordagem",
    color_discrete_map={"Referência": "#64748b", "Pipeline tratado": "#0f766e"},
    labels={
        "taxa_falsos_positivos": "Taxa de falsos positivos",
        "taxa_verdadeiros_positivos": "Taxa de verdadeiros positivos",
        "abordagem": "Abordagem",
    },
    title="Curva ROC",
)
fig.add_shape(
    type="line", x0=0, y0=0, x1=1, y1=1,
    line={"color": "#94a3b8", "dash": "dash"},
)
fig.update_xaxes(range=[0, 1], tickformat=".0%")
fig.update_yaxes(range=[0, 1], tickformat=".0%")

st.plotly_chart(fig)

st.subheader("Matrizes de confusão")
st.caption("Limiar de 0,50 · Contagem e percentual dentro da classe real")

confusao = pd.read_csv(pasta_resultados / "matrizes_confusao.csv")
confusao_modelo = confusao.loc[confusao["modelo"].eq(modelo)]

abordagens = ["Referência", "Pipeline tratado"]
classes = ["Sem atraso grave", "Atraso grave"]

fig_matrizes = make_subplots(rows=1, cols=2, subplot_titles=abordagens)

for coluna, abordagem in enumerate(abordagens, start=1):
    dados = confusao_modelo.loc[confusao_modelo["abordagem"].eq(abordagem)]

    contagens = dados.pivot(
        index="classe_real", columns="classe_prevista", values="registros"
    ).reindex(index=[0, 1], columns=[0, 1])
    percentuais = dados.pivot(
        index="classe_real", columns="classe_prevista",
        values="percentual_na_classe_real",
    ).reindex(index=[0, 1], columns=[0, 1])

    anotacoes = [
        [
            f"{contagem:,}".replace(",", ".")
            + "<br>"
            + f"{percentual:.2f}%".replace(".", ",")
            for contagem, percentual in zip(linha_contagens, linha_percentuais)
        ]
        for linha_contagens, linha_percentuais in zip(
            contagens.to_numpy(), percentuais.to_numpy()
        )
    ]

    fig_matrizes.add_trace(
        go.Heatmap(
            x=classes,
            y=classes,
            z=percentuais.to_numpy(),
            text=anotacoes,
            texttemplate="%{text}",
            textfont={"color": "#0f172a"},
            hovertemplate="Real: %{y}<br>Prevista: %{x}<br>%{text}<extra></extra>",
            coloraxis="coloraxis",
            xgap=2,
            ygap=2,
        ),
        row=1,
        col=coluna,
    )

fig_matrizes.update_xaxes(title_text="Classe prevista")
fig_matrizes.update_yaxes(title_text="Classe real", autorange="reversed")
fig_matrizes.update_layout(
    height=380,
    coloraxis={
        "cmin": 0,
        "cmax": 100,
        "colorscale": [[0, "#f0fdfa"], [1, "#2dd4bf"]],
        "colorbar": {"title": "% da classe real"},
    },
)

st.plotly_chart(fig_matrizes)

st.subheader("Desempenho nos registros com campos ausentes")

adicionais = metricas.loc[metricas["recorte"].eq("Teste adicional")].copy()
registros = int(adicionais["registros"].iloc[0])
casos_graves = int(adicionais["casos_graves_reais"].iloc[0])

st.caption(
    f"{registros:,} registros · {casos_graves:,} casos reais de atraso grave"
    .replace(",", ".")
    + " · Limiar de 0,50"
)

adicionais["casos_detectados"] = (
    adicionais["recall_classe_1"] * adicionais["casos_graves_reais"]
).round().astype(int)

fig_adicional = px.bar(
    adicionais,
    x="recall_classe_1",
    y="modelo",
    orientation="h",
    text="casos_detectados",
    labels={"recall_classe_1": "Recall da classe 1", "modelo": "Modelo tratado"},
)
fig_adicional.update_traces(
    marker_color="#0f766e",
    texttemplate="%{x:.2%} · %{text} casos",
    textposition="outside",
)
fig_adicional.update_xaxes(range=[0, 1], tickformat=".0%")
fig_adicional.update_yaxes(autorange="reversed")
fig_adicional.update_layout(height=260)

st.plotly_chart(fig_adicional)
st.dataframe(adicionais.set_index("modelo")[["ROC-AUC", "KS"]].round(4))

st.subheader("Efeito do tratamento nos dados")
st.caption("Uso do limite de crédito no treino · Percentis 98 a 100")

utilizacao = pd.read_csv(pasta_resultados / "efeito_teto_utilizacao.csv")

fig_utilizacao = px.line(
    utilizacao,
    x="percentil",
    y="uso_do_limite",
    color="etapa",
    log_y=True,
    color_discrete_map={"Antes": "#64748b", "Depois": "#0f766e"},
    labels={
        "percentil": "Percentil no treino",
        "uso_do_limite": "Proporção do limite utilizado (escala log)",
        "etapa": "Etapa",
    },
)
fig_utilizacao.add_vline(
    x=99, line_dash="dash", line_color="#b45309", annotation_text="P99 do treino"
)

st.plotly_chart(fig_utilizacao)

st.subheader("Validação dos dados com Pandera")
st.caption("Raw Gate na entrada do pipeline · Clean Gate após o tratamento")

validacoes = pd.read_csv(pasta_resultados / "validacoes_pandera.csv")
st.dataframe(validacoes, hide_index=True)
