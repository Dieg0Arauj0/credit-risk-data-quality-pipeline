# Credit Risk Data Quality Pipeline

Projeto de portfólio que aplica práticas de QA à preparação de dados para um estudo de risco de crédito. A base de dados é o sistema sob teste.

**Status** · Análise exploratória, contratos de dados, pré-modelagem, avaliação e painel Streamlit executados localmente.

## O problema

Renda ausente, proporções extremas e contagens de atraso atípicas podem distorcer tanto a análise quanto os resultados de um modelo. Como as decisões de limpeza e engenharia de variáveis afetam a qualidade dos dados e a capacidade de identificar atraso grave?

O projeto usa os **150.000 registros** de treino da competição [Give Me Some Credit](https://www.kaggle.com/c/GiveMeSomeCredit/data). A variável-alvo, `SeriousDlqin2yrs`, indica se houve atraso de **90 dias ou mais** no horizonte de dois anos. A classe de atraso grave representa **6,68%** da base.

## Do diagnóstico à avaliação

| Etapa                                                               | O que foi implementado                                                                                                                                                                                                                                                                                               |
| ------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [Diagnóstico exploratório](notebooks/01_eda_diagnostico.ipynb)     | Investigação visual de valores ausentes, desbalanceamento, extremos, correlações e perfis repetidos. Os valores `96` e `98` ocorreram simultaneamente nas três contagens de atraso em 269 registros e influenciaram fortemente a correlação de Pearson.                                                   |
| [Contratos de dados](src/schema_validator.py)                        | O *Raw Gate* verifica as 12 colunas da entrada, seus tipos e o domínio do alvo. Um relatório compara as taxas de ausência com a base de referência. O *Clean Gate* verifica as 16 variáveis após o tratamento, incluindo preenchimento, idades, contagens de atraso e indicadores binários.               |
| [Limpeza e pré-modelagem](notebooks/02_limpeza_pre_modelagem.ipynb) | Imputação de renda por faixa etária e quantidade de créditos em aberto, tratamento de contagens atípicas e aplicação de um teto no P99 ao uso do limite. Estatísticas de imputação e teto são aprendidos apenas no treino. Perfis idênticos nas variáveis brutas ficam juntos na divisão treino/teste. |
| [Avaliação e painel](app.py)                                       | Comparação de regressão logística e Random Forest, cada uma com uma referência com `dropna()` e uma versão com dados tratados. O painel interativo apresenta cobertura, métricas, curvas ROC, matrizes de confusão, o efeito do teto na distribuição e os resultados dos contratos.                      |

O fio condutor é a rastreabilidade entre **achado da análise exploratória → decisão de tratamento → regra de qualidade → teste automatizado**.

## Principais resultados

A divisão, por perfis de entrada, resultou em **120.001 registros de treino** e **29.999 de teste**, com **zero perfis compartilhados** e **6,68%** de atrasos graves em cada conjunto após arredondamento.

A comparação direta usa os **mesmos 24.010 registros de teste** nas duas abordagens, ou **80,04%** do conjunto de teste. A referência treina com as linhas completas. A abordagem tratada usa todo o treino e inclui as variáveis derivadas. Na regressão logística, as duas abordagens usam `RobustScaler`, ajustado separadamente no respectivo treino.

| Modelo                | Abordagem        | ROC-AUC |     KS | Recall da classe de atraso grave |
| --------------------- | ---------------- | ------: | -----: | -------------------------------: |
| Regressão logística | Referência      |  0,6853 | 0,3035 |                            3,54% |
| Regressão logística | Pipeline tratado |  0,8384 | 0,5230 |                           18,38% |
| Random Forest         | Referência      |  0,8389 | 0,5366 |                           16,10% |
| Random Forest         | Pipeline tratado |  0,8388 | 0,5381 |                           17,24% |

Com limiar de **0,50**, a regressão logística tratada encontrou **306 casos graves**, ante **59** na referência. Os falsos alarmes passaram de **42 para 235**. Na Random Forest, a ROC-AUC ficou praticamente estável e o recall subiu **1,14 ponto percentual** no mesmo limiar. A comparação mede o efeito conjunto da preparação e do uso de mais registros no treino.

### Cobertura adicional

O pipeline tratado gerou previsões para **5.989 registros** com campos originalmente ausentes, que ficaram fora da comparação direta. Havia **340 casos reais de atraso grave** nesse grupo.

| Modelo tratado        | ROC-AUC |     KS | Recall a 0,50 | Casos graves detectados |
| --------------------- | ------: | -----: | ------------: | ----------------------: |
| Regressão logística |  0,8892 | 0,6454 |        17,35% |               59 de 340 |
| Random Forest         |  0,8869 | 0,6475 |        25,29% |               86 de 340 |

## Validação dos dados

| Contrato   | Conjunto       | Registros verificados | Resultado | Ocorrências reportadas |
| ---------- | -------------- | --------------------: | --------- | ----------------------: |
| Raw Gate   | Base original  |               150.000 | Aprovado  |                       0 |
| Clean Gate | Treino tratado |               120.001 | Aprovado  |                       0 |
| Clean Gate | Teste tratado  |                29.999 | Aprovado  |                       0 |

A [suíte Pytest](tests/test_data_quality.py) teve **10 testes aprovados localmente**. Ela usa amostras sintéticas para verificar entradas válidas e violações como alvo fora do domínio, coluna obrigatória ausente, renda ausente após tratamento e indicador fora de `0/1`. O [workflow do GitHub Actions](.github/workflows/data-quality.yml) está configurado para executar a suíte a cada push.

## Como reproduzir

1. Na raiz do repositório, crie o ambiente com **Python 3.11** e instale as dependências. No Windows, use o PowerShell:

   ```powershell
   py -3.11 -m venv .venv
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   ```
2. Baixe o `cs-training.csv` na [aba Data da competição](https://www.kaggle.com/c/GiveMeSomeCredit/data) e salve em `data/raw/cs-training.csv`. O `Data Dictionary.xls` pode ficar na mesma pasta para consulta.
3. Selecione o kernel da `.venv` nos notebooks. Execute o [diagnóstico exploratório](notebooks/01_eda_diagnostico.ipynb) para acompanhar as evidências. Execute o notebook de [pré-modelagem e avaliação](notebooks/02_limpeza_pre_modelagem.ipynb) até o fim para treinar os modelos e gerar os **seis CSVs agregados** em `data/processed/`.
4. Abra o painel:

   ```powershell
   .\.venv\Scripts\python.exe -m streamlit run app.py
   ```
5. Rode os testes em outro terminal:

   ```powershell
   .\.venv\Scripts\python.exe -m pytest tests/test_data_quality.py -q
   ```

O painel lê os CSVs gerados pelo notebook. O CSV original e as saídas geradas ficam fora do Git.

![1794886409435](image/README/1794886409435.png)

## Ferramentas

| Área                        | Ferramentas                                                     |
| ---------------------------- | --------------------------------------------------------------- |
| Análise e visualização    | Python, Jupyter, Pandas, NumPy, Matplotlib, Seaborn e missingno |
| Qualidade e automação      | Pandera, Pytest e GitHub Actions                                |
| Pré-modelagem e avaliação | scikit-learn                                                    |
| Painel interativo            | Streamlit e Plotly                                              |

O [escopo do projeto](docs/SCOPE.md) registra a proposta original, os entregáveis e os critérios de aceite do estudo offline.
