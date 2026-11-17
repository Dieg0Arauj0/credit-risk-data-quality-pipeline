import pandas as pd
import pytest
from pandera.errors import SchemaError

from src.schema_validator import CLEAN_SCHEMA, RAW_SCHEMA, resumir_ausencias


@pytest.fixture
def dados_validos():
    return pd.DataFrame({
        "Unnamed: 0": [1, 2, 3],
        "SeriousDlqin2yrs": [0, 1, 0],
        "RevolvingUtilizationOfUnsecuredLines": [0.15, 0.80, 0.30],
        "age": [35, 42, 29],
        "NumberOfTime30-59DaysPastDueNotWorse": [0, 1, 0],
        "DebtRatio": [0.25, 0.40, 0.32],
        "MonthlyIncome": [5_000.0, None, 4_200.0],
        "NumberOfOpenCreditLinesAndLoans": [3, 5, 2],
        "NumberOfTimes90DaysLate": [0, 1, 0],
        "NumberRealEstateLoansOrLines": [0, 1, 0],
        "NumberOfTime60-89DaysPastDueNotWorse": [0, 0, 0],
        "NumberOfDependents": [1.0, None, 2.0],
    })


# Renda e dependentes podem chegar ausentes no CSV.
# O Raw Gate preserva esses valores para a etapa de imputação.
def test_raw_gate_aceita_ausencias_em_renda_e_dependentes(dados_validos):
    dados_validados = RAW_SCHEMA.validate(dados_validos)

    pd.testing.assert_frame_equal(dados_validados, dados_validos)


# A classe de atraso grave deve ser 0 ou 1.
# O Raw Gate deve apontar o valor 2 como a causa da reprovação.
def test_raw_gate_rejeita_alvo_fora_do_dominio(dados_validos):
    dados = dados_validos.assign(SeriousDlqin2yrs=[0, 1, 2])

    with pytest.raises(SchemaError) as erro:
        RAW_SCHEMA.validate(dados)

    assert erro.value.failure_cases["failure_case"].tolist() == [2]


# A coluna-alvo é obrigatória na base de treino.
# A mensagem de erro deve identificar a coluna que faltou.
def test_raw_gate_rejeita_ausencia_da_coluna_alvo(dados_validos):
    dados = dados_validos.drop(columns="SeriousDlqin2yrs")

    with pytest.raises(SchemaError, match="SeriousDlqin2yrs"):
        RAW_SCHEMA.validate(dados)


# O lote simula mais ausências de renda e nenhuma ausência de dependentes.
# Conferimos a taxa de cada coluna e a direção da variação em pontos percentuais.
def test_relatorio_mostra_variacao_das_ausencias(dados_validos):
    lote = dados_validos.assign(
        MonthlyIncome=[None, None, 4_200.0],
        NumberOfDependents=[1.0, 0.0, 2.0],
    )

    validados = RAW_SCHEMA.validate(lote)
    resumo = resumir_ausencias(validados)

    assert resumo.loc["MonthlyIncome", "lote_pct"] == pytest.approx(66.67)
    assert resumo.loc["MonthlyIncome", "diferenca_pp"] == pytest.approx(46.85)
    assert resumo.loc["NumberOfDependents", "lote_pct"] == pytest.approx(0.0)
    assert resumo.loc["NumberOfDependents", "diferenca_pp"] == pytest.approx(-2.62)


@pytest.fixture
def dados_tratados(dados_validos):
    return dados_validos.drop(
        columns=["Unnamed: 0", "SeriousDlqin2yrs"]
    ).assign(
        MonthlyIncome=[5_000.0, 4_500.0, 4_200.0],
        NumberOfDependents=[1.0, 0.0, 2.0],
        tem_atraso_96_98=[0, 0, 0],
        is_income_missing=[0, 1, 0],
        is_dependents_missing=[0, 1, 0],
        is_income_zero=[0, 0, 0],
        TotalPastDue=[0, 2, 0],
        HasSevereDelinquencyHistory=[0, 1, 0],
    )


# A EDA sinalizou idades acima de 100 anos pela raridade.
# O Clean Gate deve aceitar e preservar uma idade válida de 109 anos.
def test_clean_gate_aceita_idade_acima_de_100(dados_tratados):
    dados = dados_tratados.assign(age=[35, 42, 109])

    validados = CLEAN_SCHEMA.validate(dados)

    assert validados.loc[2, "age"] == 109


# Cada cenário altera um único campo da amostra tratada.
# Assim, conferimos o valor rejeitado em cada regra: idade, atraso ou indicador.
@pytest.mark.parametrize(
    "coluna, valor_invalido",
    [
        ("age", 0),
        ("NumberOfTime30-59DaysPastDueNotWorse", 96),
        ("NumberOfTimes90DaysLate", 98),
        ("is_income_missing", 2),
    ],
)
def test_clean_gate_rejeita_valores_invalidos(dados_tratados, coluna, valor_invalido):
    dados = dados_tratados.copy()
    dados.loc[0, coluna] = valor_invalido

    with pytest.raises(SchemaError) as erro:
        CLEAN_SCHEMA.validate(dados)

    assert erro.value.failure_cases["failure_case"].tolist() == [valor_invalido]


# Após a imputação, renda ausente indica que a saída ficou incompleta.
# O erro deve identificar MonthlyIncome e registrar o valor nulo.
def test_clean_gate_rejeita_renda_ausente(dados_tratados):
    dados = dados_tratados.copy()
    dados.loc[0, "MonthlyIncome"] = None

    with pytest.raises(SchemaError, match="MonthlyIncome") as erro:
        CLEAN_SCHEMA.validate(dados)

    assert erro.value.failure_cases["failure_case"].isna().tolist() == [True]
