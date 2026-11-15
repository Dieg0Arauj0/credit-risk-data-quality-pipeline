# Credit Risk Data Quality Pipeline

Projeto de portfólio que aplica práticas de QA à preparação de dados para um estudo de risco de crédito.

**Status** · Planejamento inicial, com escopo definido.

## O problema

Em uma base de crédito, renda ausente, proporções extremas e contagens de atraso atípicas podem distorcer tanto a análise quanto os resultados de um modelo. O projeto trata a **base de dados como sistema sob teste**. Como a limpeza e a engenharia de variáveis afetam a qualidade dos dados e a capacidade de identificar inadimplência grave?

A referência é a base de treino da competição **Give Me Some Credit**. O alvo, `SeriousDlqin2yrs`, indica inadimplência de 90 dias ou mais no horizonte de dois anos. O CSV de origem ficará em `data/raw/cs-training.csv`. Os arquivos de dados brutos e processados ficarão fora do Git.

## Etapas do projeto

| Etapa | O que o projeto prevê entregar |
| --- | --- |
| **Diagnóstico exploratório** | Notebook com gráficos e estatísticas sobre dados ausentes, valores extremos, desbalanceamento do alvo e padrões nas contagens de atraso. |
| **Contratos de dados** | Validações do esquema e da tolerância a nulos na entrada (*Raw Gate*) e das regras da base tratada na saída (*Clean Gate*). Testes com Pandera e Pytest no GitHub Actions. |
| **Limpeza e pré-modelagem** | Pipeline com imputação, tratamento de extremos e engenharia de variáveis. Os parâmetros de transformação serão ajustados apenas no conjunto de treino. |
| **Avaliação e apresentação** | Comparação de uma referência com `dropna()` e do pipeline tratado usando regressão logística e Random Forest. O painel Streamlit apresentará gráficos antes e depois, resultados dos contratos e métricas de avaliação. |

O fio condutor do case será a rastreabilidade entre **achado da análise exploratória → decisão de tratamento → regra de qualidade → teste automatizado**. A avaliação dos modelos usará os mesmos registros elegíveis para as duas abordagens e registrará quantos ficaram de fora da comparação. As métricas previstas são ROC-AUC, recall da classe inadimplente e KS.

## Ferramentas previstas

| Área | Ferramentas |
| --- | --- |
| Análise e visualização | Python 3.11+, Jupyter, Pandas, NumPy, SciPy, Seaborn, Matplotlib e Plotly |
| Qualidade e automação | Pandera, Pytest e GitHub Actions |
| Pré-modelagem e avaliação | scikit-learn |
| Painel interativo | Streamlit |

## Comece pelo escopo

O [escopo do projeto](docs/SCOPE.md) detalha os entregáveis, a estrutura prevista e os critérios de aceite. A primeira etapa de implementação será configurar o ambiente, registrar a procedência do CSV e criar `notebooks/01_eda_diagnostico.ipynb`.
