import pandas as pd
import pytest
from pandera.errors import SchemaError

from src.schema_validator import RAW_SCHEMA, resumir_ausencias


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


def test_raw_gate_aceita_ausencias_em_renda_e_dependentes(dados_validos):
    dados_validados = RAW_SCHEMA.validate(dados_validos)

    pd.testing.assert_frame_equal(dados_validados, dados_validos)


def test_raw_gate_rejeita_alvo_fora_do_dominio(dados_validos):
    dados = dados_validos.assign(SeriousDlqin2yrs=[0, 1, 2])

    with pytest.raises(SchemaError) as erro:
        RAW_SCHEMA.validate(dados)

    assert erro.value.failure_cases["failure_case"].tolist() == [2]


def test_raw_gate_rejeita_ausencia_da_coluna_alvo(dados_validos):
    dados = dados_validos.drop(columns="SeriousDlqin2yrs")

    with pytest.raises(SchemaError, match="SeriousDlqin2yrs"):
        RAW_SCHEMA.validate(dados)

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
