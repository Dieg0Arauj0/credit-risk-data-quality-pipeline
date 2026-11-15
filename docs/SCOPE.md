# Escopo do projeto

**Pipeline de Auditoria Exploratória, Qualidade de Dados e Pré-Modelagem para Risco de Crédito**  
Repositório previsto `credit-risk-data-quality-pipeline`  
Status **Planejamento inicial**

## Contexto e objetivo

Este projeto de portfólio aplica práticas de QA à preparação de dados para um estudo de risco de crédito. A base é o sistema sob teste. O trabalho começa pela investigação de anomalias, transforma os achados em contratos de dados e registra como cada tratamento afeta a qualidade da base e os resultados dos modelos de referência.

A pergunta do case é **como a limpeza e a engenharia de variáveis afetam a qualidade dos dados e a capacidade de identificar inadimplência grave?** Os modelos servem para medir o efeito da pré-modelagem. Os principais resultados são o diagnóstico visual, as decisões de tratamento justificadas e os testes de qualidade reproduzíveis.

## Base e objeto de análise

A referência do case é o CSV de treino da competição **Give Me Some Credit**, com cerca de 150 mil registros previstos. O alvo `SeriousDlqin2yrs` indica inadimplência de 90 dias ou mais no horizonte de dois anos. O insumo ficará em `data/raw/cs-training.csv`, com origem, versão ou data de obtenção e dimensões registradas no notebook.

A versão sintética de `src/setup_data.py` é uma opção para exercitar o fluxo quando o CSV original estiver indisponível. Se for usada, a execução e seus resultados devem identificar a origem sintética. As relações introduzidas pelo gerador fazem parte desse cenário de teste.

| Frente de investigação | Campos e hipóteses iniciais |
| --- | --- |
| Desbalanceamento | Medir a proporção de casos positivos em `SeriousDlqin2yrs`. O planejamento cita aproximadamente 6,7%. |
| Valores ausentes | Medir a ausência em `MonthlyIncome` e `NumberOfDependents`. O planejamento cita aproximadamente 19,8% e 2,6%, respectivamente. Investigar a associação entre ausência de renda e a distribuição de `DebtRatio`. |
| Validade e extremos | Inspecionar idade igual a zero, idades extremas, utilização muito alta de crédito rotativo e caudas longas nas distribuições de renda, linhas de crédito e financiamentos imobiliários. |
| Histórico de atraso | Medir a frequência e a ocorrência conjunta dos valores 96 e 98 nas três contagens de atraso. Comparar as distribuições e correlações com e sem esses registros para fundamentar o tratamento. |

## Fases e entregáveis

### 1. Diagnóstico exploratório e estatístico

- Inventariar colunas, tipos, valores ausentes, duplicidades e possíveis identificadores. Preservar uma referência à linha de origem quando necessário para auditar transformações.
- Usar tabelas, histogramas, boxplots, gráficos de valores ausentes e matrizes de correlação para investigar a base. Registrar mediana, dispersão, assimetria e intervalo interquartil onde ajudarem a explicar os padrões observados.
- Documentar cada achado relevante com a evidência, o impacto provável e a decisão pendente. Verificar a documentação da base para interpretar 96/98 e os valores extremos de `DebtRatio`. Registrar como hipótese qualquer explicação cuja origem permaneça indeterminada.

**Entregável:** `notebooks/01_eda_diagnostico.ipynb`, com diagnóstico visual e decisões justificadas para a etapa de limpeza.

### 2. Contratos e testes de qualidade

- Implementar o **Raw Gate** em Pandera para verificar esquema, colunas obrigatórias, tipos, domínio do alvo e tolerâncias de ausência na entrada.
- Implementar o **Clean Gate** para validar a saída da limpeza, incluindo ausência de nulos, idade mínima prevista de 18 anos, ausência de 96/98 nas contagens processadas e intervalos acordados para as demais variáveis.
- Cobrir casos válidos e violações no Pytest. Usar exemplos pequenos e versionados no CI para verificar tanto a aceitação de dados válidos quanto a rejeição de violações. Na execução com a base completa, validar também o resultado em `data/processed/`.

**Entregáveis:** `src/schema_validator.py`, `tests/test_data_quality.py` e workflow em `.github/workflows/` para executar a suíte a cada push.

### 3. Limpeza e pré-modelagem

- Separar treino e teste antes de estimar parâmetros de transformação. Ajustar no treino as medianas de imputação, os limites por percentil e os escalonadores. Aplicar os parâmetros aprendidos ao teste.
- Avaliar a imputação de `MonthlyIncome` por faixa etária e quantidade de linhas de crédito, preservar a informação original de ausência em `is_income_missing` e documentar a regra para grupos com poucos dados. Definir o tratamento de `NumberOfDependents` a partir do diagnóstico.
- Aplicar o tratamento acordado para idades e contagens de atraso. Avaliar a correção de `DebtRatio` em registros com renda imputada conforme a interpretação dos dados de origem. Avaliar o corte no percentil 99 para a utilização de crédito e comparar `RobustScaler` com `StandardScaler`.
- Construir as variáveis planejadas `TotalPastDue` e `HasSevereDelinquencyHistory` sobre o histórico tratado. Avaliar a viabilidade de `DisposableIncomeEstimate` conforme a interpretação de `DebtRatio` e a disponibilidade de insumos para o cálculo.

**Entregáveis:** `src/cleaner.py`, `notebooks/02_limpeza_pre_modelagem.ipynb` e dados processados gerados localmente.

### 4. Avaliação do impacto e apresentação

- Treinar regressão logística e Random Forest em duas condições por modelo. A referência usa uma preparação mínima com `dropna()` no treino. A segunda execução usa o pipeline tratado.
- Usar a mesma divisão inicial e comparar os modelos nos mesmos registros elegíveis para ambas as abordagens. Reportar a cobertura do conjunto de teste e quantos registros a abordagem com `dropna()` perde. Registrar **ROC-AUC**, **recall da classe inadimplente** com limiar definido antes de avaliar o teste e **KS**, conforme as métricas previstas no escopo original.
- Apresentar no Streamlit o diagnóstico bruto, os gráficos antes e depois, os resultados dos contratos e a comparação dos modelos. Registrar no README as instruções de reprodução, os resultados observados e as limitações da comparação.

**Entregáveis:** avaliação reproduzível no notebook de pré-modelagem, `app.py` com Streamlit e Plotly e `README.md` com instruções e evidências.

## Organização e ferramentas

| Área | Estrutura ou ferramentas |
| --- | --- |
| Documentação | `docs/SCOPE.md` e `README.md` |
| Dados | `data/raw/` para a entrada preservada e `data/processed/` para as saídas geradas. CSVs e Parquets ficam fora do Git. |
| Ambiente | Python 3.11+, ambiente virtual `.venv`, `requirements.txt` e Jupyter |
| Análise e visualização | Pandas, NumPy, SciPy, Seaborn, Matplotlib e Plotly |
| Transformação e avaliação | scikit-learn |
| Qualidade e apresentação | Pandera, Pytest, GitHub Actions e Streamlit |

O escopo cobre uma avaliação offline para portfólio. Uso operacional para aprovação de crédito, integração com sistemas bancários e monitoramento em produção ficam fora desta versão.

## Critérios de aceite

- [ ] O README permite reproduzir o fluxo, da obtenção do CSV à execução dos notebooks, dos testes e do painel.
- [ ] A procedência do CSV e as evidências das principais anomalias estão registradas. As decisões de tratamento indicam quais achados as sustentam.
- [ ] Os contratos de entrada e saída têm testes automatizados. A suíte roda no GitHub Actions e o contrato de saída passa sobre a base processada da execução documentada.
- [ ] A divisão treino/teste e o ajuste dos parâmetros exclusivamente no treino podem ser verificados no código ou notebook.
- [ ] O relatório mostra ROC-AUC, recall, KS e cobertura da avaliação. A conclusão descreve a variação observada, inclusive quando uma métrica piora ou permanece estável.
- [ ] Os gráficos têm títulos informativos, eixos legíveis e destaque para os padrões que sustentam as conclusões. O README e o painel documentam os resultados da comparação.

## Primeiro passo

Criar a estrutura do repositório e configurar o ambiente Python. Em seguida, obter e registrar a origem do CSV e iniciar `notebooks/01_eda_diagnostico.ipynb` pelo inventário de colunas, distribuição do alvo, valores ausentes e anomalias.
