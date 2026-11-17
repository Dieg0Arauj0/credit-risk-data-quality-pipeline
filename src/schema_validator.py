import pandas as pd
import pandera.pandas as pa

RAW_SCHEMA = pa.DataFrameSchema(
    {
        "Unnamed: 0": pa.Column(int),
        "SeriousDlqin2yrs": pa.Column(
            int,
            checks=pa.Check.isin([0, 1]),
            nullable=False,
            required=True,
        ),
        "RevolvingUtilizationOfUnsecuredLines": pa.Column(float),
        "age": pa.Column(int),
        "NumberOfTime30-59DaysPastDueNotWorse": pa.Column(int),
        "DebtRatio": pa.Column(float),
        "MonthlyIncome": pa.Column(float, nullable=True),
        "NumberOfOpenCreditLinesAndLoans": pa.Column(int),
        "NumberOfTimes90DaysLate": pa.Column(int),
        "NumberRealEstateLoansOrLines": pa.Column(int),
        "NumberOfTime60-89DaysPastDueNotWorse": pa.Column(int),
        "NumberOfDependents": pa.Column(float, nullable=True),
    },

    strict=False,
)

REFERENCIA_AUSENCIAS = pd.Series({
    "MonthlyIncome": 29_731 / 150_000 * 100,
    "NumberOfDependents": 3_924 / 150_000 * 100,
})


def resumir_ausencias(dados: pd.DataFrame) -> pd.DataFrame:
    taxas_lote = (
        dados[REFERENCIA_AUSENCIAS.index].isna().mean().mul(100)
    )

    resumo = pd.DataFrame({
        "lote_pct": taxas_lote,
        "referencia_pct": REFERENCIA_AUSENCIAS,
        "diferenca_pp": taxas_lote - REFERENCIA_AUSENCIAS,
    })

    return resumo.round(2).rename_axis("coluna")
