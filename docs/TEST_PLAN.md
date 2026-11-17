# Plano de testes

**Projeto** · [Credit Risk Data Quality Pipeline](../README.md)
**Escopo relacionado** · [Metodologia e critérios de aceite](SCOPE.md)
**Ambiente da execução registrada** · Python 3.11, PowerShell, Jupyter e Streamlit local

## Objetivo

Verificar a integridade dos dados na entrada e na saída do pipeline, a separação entre treino e teste e a correspondência entre os resultados dos notebooks e o painel. O plano cobre o fluxo offline do projeto de portfólio.

## Estratégia de testes

| Camada                               | Como verificamos                                                                                                                      | Evidência                                                               |
| ------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------ |
| Contratos e relatório de ausências | Pandera aplica o Raw Gate e o Clean Gate. O Pytest executa os cenários de aceitação e rejeição em amostras sintéticas pequenas. | Saída local do Pytest e registro do workflow de integração contínua. |
| Pré-modelagem e avaliação         | Executamos o notebook com o CSV original e conferimos as asserções, as contagens de auditoria e os resultados exportados.           | Células executadas, tabelas de auditoria e CSVs agregados.              |
| Painel Streamlit                     | Abrimos o painel local e conferimos os totais, os gráficos, o seletor e os estados de erro descritos neste plano.                    | Conferência visual e, quando necessário, captura da tela.              |

A suíte usa duas fixtures. `dados_validos` representa a entrada bruta, na qual renda e dependentes podem estar ausentes. `dados_tratados` representa a saída após a imputação e inclui os indicadores e as variáveis derivadas. Os cenários de rejeição partem de uma amostra válida e alteram um campo por vez. Cada combinação de `pytest.mark.parametrize` conta como um caso de teste.

## Matriz de rastreabilidade dos casos automatizados

Os identificadores abaixo referenciam as funções em [`tests/test_data_quality.py`](../tests/test_data_quality.py). As regras de entrada e saída estão em [`src/schema_validator.py`](../src/schema_validator.py).

| ID       | Achado ou regra de qualidade                                             | Entrada do teste                                                                             | Resultado esperado                                                                                                         | Função Pytest                                                                 |
| -------- | ------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| RAW-01   | Renda e dependentes podem chegar ausentes.                               | Amostra válida com valores nulos em `MonthlyIncome` e `NumberOfDependents`.             | Raw Gate aprova e preserva o DataFrame, incluindo os valores ausentes.                                                     | `test_raw_gate_aceita_ausencias_em_renda_e_dependentes`                       |
| RAW-02   | O alvo aceita apenas `0` e `1`.                                      | `SeriousDlqin2yrs` contém `2`.                                                          | Raw Gate rejeita e identifica o valor `2`.                                                                               | `test_raw_gate_rejeita_alvo_fora_do_dominio`                                  |
| RAW-03   | A coluna-alvo é obrigatória no CSV de treino.                          | Amostra sem a coluna `SeriousDlqin2yrs`.                                                   | Raw Gate rejeita e menciona a coluna na mensagem de erro.                                                                  | `test_raw_gate_rejeita_ausencia_da_coluna_alvo`                               |
| RAW-04   | A taxa de ausência por lote deve ser comparável à referência da EDA. | Lote de três linhas com duas rendas ausentes e todos os valores de dependentes preenchidos. | Renda apresenta 66,67% de ausência e +46,85 pontos percentuais. Dependentes apresentam 0,00% e −2,62 pontos percentuais. | `test_relatorio_mostra_variacao_das_ausencias`                                |
| CLEAN-01 | Idade acima de 100 anos foi sinalizada pela raridade e continua válida. | Registro tratado com `age = 109`.                                                          | Clean Gate aprova e preserva o valor `109`.                                                                              | `test_clean_gate_aceita_idade_acima_de_100`                                   |
| CLEAN-02 | A idade mínima após tratamento é 18 anos.                             | Registro tratado com `age = 0`.                                                            | Clean Gate rejeita e identifica o valor `0`.                                                                             | `test_clean_gate_rejeita_valores_invalidos` · caso `age = 0`               |
| CLEAN-03 | As contagens de atraso tratadas excluem `96` e `98`.                 | Valor `96` na contagem de atrasos de 30 a 59 dias.                                         | Clean Gate rejeita e identifica o valor `96`.                                                                            | `test_clean_gate_rejeita_valores_invalidos` · caso `96`                    |
| CLEAN-04 | As contagens de atraso tratadas excluem `96` e `98`.                 | Valor `98` na contagem de atrasos de 90 dias ou mais.                                      | Clean Gate rejeita e identifica o valor `98`.                                                                            | `test_clean_gate_rejeita_valores_invalidos` · caso `98`                    |
| CLEAN-05 | Indicadores binários só aceitam `0` ou `1`.                        | `is_income_missing = 2`.                                                                   | Clean Gate rejeita e identifica o valor `2`.                                                                             | `test_clean_gate_rejeita_valores_invalidos` · caso `is_income_missing = 2` |
| CLEAN-06 | A renda deve estar preenchida após a imputação.                       | Um valor nulo em `MonthlyIncome` na amostra tratada.                                       | Clean Gate rejeita, identifica a coluna e registra o valor ausente como evidência.                                        | `test_clean_gate_rejeita_renda_ausente`                                       |

O vínculo entre **RAW-01** e **CLEAN-06** documenta a mudança da regra ao longo do pipeline. A ausência de renda é aceita na entrada e deve estar resolvida na saída.

## Verificações com a base original

Use [`02_limpeza_pre_modelagem.ipynb`](../notebooks/02_limpeza_pre_modelagem.ipynb). Os números abaixo correspondem à execução registrada para o CSV original e à divisão com semente 42.

| ID    | O que conferir                                                                  | Resultado esperado e evidência                                                                                                                                                                                                                        |
| ----- | ------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| NB-01 | Validar o CSV de treino pelo Raw Gate.                                          | 150.000 registros e 12 colunas, com zero ocorrências reportadas.                                                                                                                                                                                      |
| NB-02 | Dividir por perfil antes do tratamento e conferir a composição dos conjuntos. | 120.001 registros no treino e 29.999 no teste, com zero perfis compartilhados. Cada conjunto tem 6,68% de atraso grave após arredondamento.                                                                                                           |
| NB-03 | Auditar a imputação de idade, renda, dependentes e contagens de atraso.       | Um caso de idade zero tratado, 29.731 rendas e 3.924 contagens de dependentes preenchidas. As 807 ocorrências de `96/98` ficam resolvidas e as três contagens de atraso terminam sem ausências.                                                   |
| NB-04 | Conferir a origem dos parâmetros e a aplicação do teto.                      | As medianas, o P99 e os escalonadores são ajustados no treino. O mesmo teto do P99 é aplicado ao treino e ao teste, com máximo tratado de aproximadamente 1,096866.                                                                                 |
| NB-05 | Validar os dois conjuntos após o tratamento.                                   | Clean Gate aprova as 16 variáveis nos 120.001 registros de treino e nos 29.999 de teste, com zero ocorrências reportadas.                                                                                                                            |
| NB-06 | Verificar a elegibilidade e a ordem dos registros avaliados.                    | As duas abordagens usam os mesmos índices e rótulos, na mesma ordem, nos 24.010 registros comparáveis. Os 5.989 adicionais são avaliados separadamente pelos modelos tratados.                                                                     |
| NB-07 | Conferir os CSVs consumidos pelo painel.                                        | Seis arquivos agregados em `data/processed/`. A exportação contém seis linhas de métricas, duas de cobertura, quatro curvas ROC, 16 células de matrizes de confusão, 402 pontos do gráfico de utilização e três resultados de validação. |

As métricas registradas documentam o comportamento dos modelos nesse experimento. A checagem compara o painel com as saídas do notebook, incluindo o recorte avaliado e o limiar de 0,50 para recall e matrizes de confusão.

## Roteiro de verificação do painel

Use [`app.py`](../app.py) com os CSVs exportados pelo notebook.

| ID    | Passo manual                                                                     | Resultado esperado                                                                                                                                                        |
| ----- | -------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| UI-01 | Abrir o painel com as exportações disponíveis.                                | Exibe 29.999 registros no teste, 24.010 na comparação direta e 5.989 adicionais tratados.                                                                               |
| UI-02 | Alternar entre regressão logística e Random Forest no seletor.                 | Tabela do teste comum, curva ROC e as duas matrizes mudam para o algoritmo escolhido. O gráfico do teste adicional continua exibindo os dois modelos tratados.           |
| UI-03 | Conferir a matriz tratada da regressão logística e o teste adicional.          | A célula de verdadeiros positivos mostra 306 casos e 18,38%. No recorte adicional, são exibidos 59 casos detectados pela regressão logística e 86 pela Random Forest. |
| UI-04 | Conferir o gráfico de tratamento e a tabela Pandera.                            | O gráfico mostra a linha de referência do P99 e o teto após tratamento. A tabela exibe três aprovações com zero ocorrências reportadas.                            |
| UI-05 | Em uma cópia local do projeto, abrir o aplicativo com um CSV agregado pendente. | O painel identifica o arquivo pendente e orienta a executar as células de exportação do notebook.                                                                      |

## Execução e evidências

Na raiz do projeto, com as dependências instaladas na `.venv`, execute:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_data_quality.py -q
```

Para reproduzir as verificações com dados reais, coloque `cs-training.csv` em `data/raw/` e execute o notebook de pré-modelagem a partir de um kernel limpo. Em seguida, abra o painel:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

| Evidência                   | Estado registrado                                                                                                                                                                                                                      |
| ---------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Suíte automatizada local    | 10 casos aprovados na execução registrada.                                                                                                                                                                                           |
| Contratos com os dados reais | Raw Gate e Clean Gate aprovados no notebook e exibidos no painel, com zero ocorrências reportadas.                                                                                                                                    |
| Painel local                 | UI-02 aprovado: o seletor atualizou a tabela do teste comum, a curva ROC e as matrizes de confusão. UI-05 aprovado: na porta 8502, o painel identificou `curvas_roc.csv` ausente e orientou a executar as células de exportação. |
| Integração contínua       | [Workflow](../.github/workflows/data-quality.yml) Qualidade de dados #1, commit 373a52a. A etapa Executar os testes registrou 10 passed em 0,66 s                                                                                      |

Para registrar uma nova rodada, anote o commit, a versão do Python, o ambiente de execução, os casos verificados e o resultado. Em caso de falha, guarde a mensagem do Pytest, a tabela de ocorrências ou a captura do painel para facilitar a reprodução.
