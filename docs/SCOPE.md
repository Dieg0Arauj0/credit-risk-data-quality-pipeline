# Escopo do projeto

**Pipeline de Auditoria Exploratória, Qualidade de Dados e Pré-Modelagem para Risco de Crédito**
Repositório `credit-risk-data-quality-pipeline`
**Status** · Diagnóstico, validação, preparação, avaliação e painel verificados localmente.

## Contexto e objetivo

Este projeto de portfólio aplica práticas de QA à preparação de dados para um estudo de risco de crédito. A base é o sistema sob teste. O estudo investiga anomalias, relaciona os achados às regras dos contratos de dados e mede como o conjunto de decisões de preparação afeta a identificação de atraso grave.

A pergunta central é **como a limpeza e a engenharia de variáveis afetam a qualidade dos dados e a capacidade de identificar atraso grave?** O estudo cobre análise e avaliação offline para portfólio. Aprovação operacional de crédito, integração com sistemas bancários e monitoramento em produção ficam fora do escopo.

## Base e objeto de análise

O estudo usa o CSV original de treino da competição [Give Me Some Credit](https://www.kaggle.com/c/GiveMeSomeCredit/data), com **150.000 registros e 12 colunas**. O insumo fica em `data/raw/cs-training.csv`. O alvo `SeriousDlqin2yrs` indica atraso de 90 dias ou mais no horizonte de dois anos e tem **6,68%** de casos positivos. A coluna `Unnamed: 0` permite rastrear a posição do registro no CSV. As dez variáveis do perfil de entrada excluem essa numeração e o alvo.

| Frente                           | Evidência observada                                                                                                                                                                                       | Decisão ou uso                                                                                                                              |
| -------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| Desbalanceamento                 | 6,68% dos registros tinham atraso grave.                                                                                                                                                                   | Acompanhar o recall da classe `1`, além de ROC-AUC e KS.                                                                                  |
| Renda e dependentes              | 29.731 rendas e 3.924 contagens de dependentes ausentes. Todos os casos sem dependentes também estavam sem renda.                                                                                         | Permitir as ausências na entrada, registrá-las em indicadores e exigir o preenchimento na saída.                                          |
| Renda e `DebtRatio`            | As medianas brutas de `DebtRatio` diferiram entre renda zero, ausente e diferente de zero.                                                                                                               | Preservar a distinção entre renda zero e ausente. Usar uma estimativa para as razões nesses casos.                                        |
| Idade e utilização de crédito | Um caso com idade zero, 13 acima de 100 anos e utilização máxima de 50.708 na unidade original da coluna.                                                                                               | Imputar a idade zero, manter as idades acima de 100 anos e limitar a utilização pelo P99 do treino.                                        |
| Histórico de atraso             | Em 269 registros, `96` ou `98` aparece nas três contagens ao mesmo tempo. As correlações de Pearson caem de 0,98–0,99 para 0,22–0,31 quando esses registros ficam fora do cálculo exploratório. | Marcar as contagens sinalizadas como ausentes, imputá-las e preservar um indicador. O significado original dos valores permanece em aberto. |
| Perfis repetidos                 | 37 perfis idênticos nas variáveis de entrada aparecem com as duas classes do alvo, somando 145 registros.                                                                                                | Agrupar entradas idênticas antes de dividir treino e teste.                                                                                 |

## Metodologia aplicada e entregáveis

### 1. Diagnóstico exploratório e estatístico

- Inventário de dimensões, tipos inferidos, domínio do alvo, valores ausentes e possíveis identificadores.
- Análise univariada e bivariada com contagens, percentuais, medianas, quantis, histogramas, boxplots e curvas de distribuição acumulada.
- Matriz de ausências com missingno e cruzamento das ausências de renda e dependentes no CSV completo.
- Correlação de Pearson para medir a sensibilidade aos casos com `96/98` e matriz geral de Spearman para investigar as associações entre as variáveis e o alvo.
- Verificação de linhas repetidas com e sem o alvo. As coincidências descrevem os valores disponíveis no CSV, e a identidade dos tomadores permanece indeterminada.

**Entregável** · [Notebook de diagnóstico exploratório](../notebooks/01_eda_diagnostico.ipynb), com evidências e justificativas.

### 2. Contratos de dados e testes automatizados

**Pandera** é o framework de validação dos DataFrames. O *Raw Gate* exige as 12 colunas do CSV, verifica os tipos e exige que o alvo seja preenchido e esteja no domínio `0/1`. Permite valores ausentes em renda e dependentes. A taxa por lote é comparada à referência da EDA, e a diferença em pontos percentuais serve para revisão.

O *Clean Gate* exige o preenchimento das 16 variáveis de entrada da modelagem. Valida idade mínima de 18 anos, contagens não negativas, ausência de `96/98` nas três contagens tratadas e domínio binário dos indicadores.

**Pytest** é o framework de testes automatizados. A suíte exercita os contratos e o relatório de ausências com DataFrames sintéticos pequenos. Fixtures distintas representam a entrada bruta e a saída tratada. Nos cenários de falha, parte-se de uma amostra válida e altera-se um campo por vez para verificar a rejeição esperada. A parametrização reaproveita a mesma checagem para mais de um valor inválido.

| Grupo de testes                    | Cobertura                                                                                                                                                         | Execução local |
| ---------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------: |
| Entrada e relatório de ausências | Aceitação de renda e dependentes ausentes, rejeição de alvo fora de `0/1` e da falta da coluna-alvo no lote, cálculo da variação das taxas de ausência. |      4 aprovados |
| Saída tratada                     | Aceitação de idade acima de 100 anos. Rejeição de idade zero, das contagens `96` e `98`, de indicador fora de `0/1` e de renda ainda ausente.           |      6 aprovados |

A validação com os **dados reais** é executada no notebook e exportada para o painel. O Raw Gate aprovou 150.000 registros. O Clean Gate aprovou 120.001 de treino e 29.999 de teste. Os três resultados registraram zero ocorrências. O workflow do **GitHub Actions** está configurado para instalar as dependências e rodar o Pytest a cada push, em Ubuntu com Python 3.11.

**Entregáveis** · [Esquemas e relatório de ausências](../src/schema_validator.py), [suíte Pytest](../tests/test_data_quality.py) e [workflow do GitHub Actions](../.github/workflows/data-quality.yml).

### 3. Limpeza e pré-modelagem

A divisão usa `StratifiedGroupKFold` com cinco partes e semente 42. A primeira parte é reservada para teste e as outras quatro formam o treino. A verificação encontrou **zero perfis compartilhados**, com **6,68%** de atrasos graves em cada conjunto após arredondamento. Os parâmetros de tratamento são calculados no treino e aplicados aos dois conjuntos.

| Variável ou grupo       | Tratamento aplicado                                                                                                                                                                                                                                                                 |
| ------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `age`                  | Marcamos a idade zero como ausente e preenchemos com a mediana de idade do treino.                                                                                                                                                                                                  |
| `MonthlyIncome`        | Usamos a mediana do grupo de faixa etária e créditos em aberto. A mediana global do treino serve de alternativa e, nesta execução, todas as 29.731 ausências receberam a mediana do grupo. Preservamos renda zero e registramos ausências originais em `is_income_missing`. |
| `NumberOfDependents`   | Preenchemos ausências com a mediana do treino e preservamos a informação de ausência original em `is_dependents_missing`.                                                                                                                                                     |
| `DebtRatio`            | Nos registros com renda original zero ou ausente, usamos como estimativa a mediana de `DebtRatio` no treino com renda positiva. `is_income_zero` e `is_income_missing` registram as duas situações.                                                                         |
| Utilização de crédito | Aplicamos winsorização unilateral com o teto do P99 do treino, aproximadamente `1,096866`.                                                                                                                                                                                      |
| Contagens de atraso      | Imputamos `96/98` com a mediana da respectiva contagem no treino e registramos as ocorrências em `tem_atraso_96_98`. Derivamos `TotalPastDue` e `HasSevereDelinquencyHistory` das contagens tratadas.                                                                      |
| Escalonamento            | Comparamos `StandardScaler` e `RobustScaler` no treino. As duas versões da regressão logística usam `RobustScaler`, ajustado no treino de cada versão. A Random Forest usa as variáveis sem escalonamento.                                                               |

**Entregável implementado** · [Notebook de limpeza, pré-modelagem e avaliação](../notebooks/02_limpeza_pre_modelagem.ipynb). As transformações são executadas nesse notebook. A extração dessas regras para `src/cleaner.py` permanece como evolução prevista no planejamento original. Uma estimativa de renda disponível depende de evidência adicional sobre as despesas que compõem `DebtRatio`.

### 4. Avaliação do impacto e apresentação

- Treinamos regressão logística e Random Forest em duas abordagens por algoritmo. A referência usa as dez variáveis brutas e os registros completos com `dropna()`. A versão tratada usa todo o treino e 16 variáveis.
- A comparação direta usa os mesmos **24.010 registros de teste** para as quatro combinações, com **ROC-AUC, KS e recall da classe 1**. Usamos **0,50** como limiar fixo para recall e matrizes de confusão.
- Avaliamos os dois modelos tratados separadamente nos **5.989 registros adicionais** com campos originalmente ausentes. Esse recorte complementa a cobertura de **80,04%** da referência no teste.
- O painel exibe cobertura, métricas, curvas ROC, matrizes de confusão, o antes e depois da utilização de crédito e os resultados dos contratos Pandera. O diagnóstico detalhado está no notebook exploratório.

Na comparação direta, a ROC-AUC da regressão logística passou de **0,6853 para 0,8384** e o recall de **3,54% para 18,38%**. Na Random Forest, a ROC-AUC ficou próxima de **0,839** nas duas versões, e o recall passou de **16,10% para 17,24%**. O experimento mede o efeito conjunto do tratamento, das variáveis derivadas e da inclusão de mais registros no treino.

**Entregáveis** · Avaliação no notebook de pré-modelagem, [painel Streamlit](../app.py) e [README](../README.md) com resultados e instruções de execução. O painel consome seis CSVs agregados gerados localmente em `data/processed/`.

## Organização e ferramentas

| Área                              | Estrutura ou ferramentas                                                                                               |
| ---------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| Documentação                     | `docs/SCOPE.md`, `README.md` , `TEST_PLAN.md`                                                                  |
| Dados                              | `data/raw/` para os insumos e `data/processed/` para as saídas agregadas. Os arquivos de dados ficam fora do Git. |
| Ambiente                           | Python 3.11, `.venv`, `requirements.txt` e Jupyter                                                                 |
| Diagnóstico visual                | Pandas, NumPy, missingno, Seaborn e Matplotlib                                                                         |
| Transformação e avaliação      | scikit-learn                                                                                                           |
| Qualidade e integração contínua | Pandera, Pytest e GitHub Actions                                                                                       |
| Painel interativo                  | Streamlit e Plotly                                                                                                     |

## Critérios de aceite e evidências

- [X] O README documenta a origem do CSV e os passos para executar os notebooks, os testes e o painel.
- [X] O notebook exploratório registra as evidências das principais anomalias e as relaciona às decisões de tratamento.
- [X] Os contratos são cobertos por testes automatizados. A suíte teve 10 testes aprovados localmente, e Raw Gate e Clean Gate aprovaram os conjuntos reais na execução documentada.
- [X] O notebook demonstra a separação por perfil e o ajuste de medianas, teto e escalonadores exclusivamente sobre dados de treino.
- [X] A avaliação registra ROC-AUC, KS, recall, limiar e cobertura. O painel e o README apresentam a comparação e os resultados observados.
- [X] O painel foi executado localmente com as saídas agregadas e exibiu as três aprovações dos contratos.
- [X] Confirmar na aba Actions a primeira execução remota do workflow após o push.
