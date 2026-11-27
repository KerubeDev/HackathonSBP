from decimal import Decimal

import pytest

from app.rankings import ActivityCatalogEntry, Bank, CreditRecord, RankingEngine


ACTIVITIES = [
    ActivityCatalogEntry("K.64.649.6492.64921", "CONSUMO", "Credito personal"),
    ActivityCatalogEntry("K.64.649.6492.64922", "CONSUMO", "Automovil"),
    ActivityCatalogEntry("K.64.649.6499.64991", "CONSUMO", "Tarjeta"),
    ActivityCatalogEntry("A.01", "AGROPECUARIO", "Agricultura"),
    ActivityCatalogEntry("C.10", "INDUSTRIA", "Alimentos"),
    ActivityCatalogEntry("F.41", "CONSTRUCCION", "Vivienda interino"),
    ActivityCatalogEntry("G.46", "COMERCIO", "Mayorista"),
    ActivityCatalogEntry("L.68", "HIPOTECARIO", "Vivienda propia"),
]
BANKS = [Bank("101", "Banco Uno"), Bank("102", "Banco Dos")]


def record(
    loan: str,
    *,
    bank: str = "101",
    balance: str = "10.00",
    destination: str = "L",
    activity: str = "K.64.649.6492.64921",
    facility: str = "01",
) -> CreditRecord:
    return CreditRecord(
        period="20260731",
        loan_number=loan,
        bank_code=bank,
        destination=destination,
        balance=Decimal(balance),
        activity_code=activity,
        facility_code=facility,
    )


def test_cascade_keeps_the_first_failure_only_and_retains_exclusion_evidence():
    result = RankingEngine(ACTIVITIES, BANKS).calculate(
        [
            record("duplicate"),
            record("duplicate", destination="E", balance="-1.00"),
            record("foreign", destination="E", balance="-1.00"),
            record("non-positive", balance="0.00", activity="unknown"),
            record("unknown", activity="unknown"),
            record("valid", balance="1.00"),
        ]
    )

    assert result.quality.as_dict() == {
        "rows_read": 6,
        "excluded_e1_duplicates": 1,
        "excluded_e2_foreign_destination": 1,
        "excluded_e3_non_positive_balance": 1,
        "excluded_e4_uncatalogued_activity": 1,
        "local_valid_rows": 2,
    }
    assert [(item.loan_number, item.reason) for item in result.exclusions] == [
        ("duplicate", "E1_DUPLICATE"),
        ("foreign", "E2_FOREIGN_DESTINATION"),
        ("non-positive", "E3_NON_POSITIVE_BALANCE"),
        ("unknown", "E4_UNCATALOGUED_ACTIVITY"),
    ]


def test_rankings_include_every_bank_and_macroactivity_with_exact_cent_totals():
    result = RankingEngine(ACTIVITIES, BANKS).calculate(
        [
            record("one", balance="10.01", activity="A.01"),
            record("two", balance="9.99", activity="A.01"),
            record("three", bank="102", balance="20.00", activity="A.01"),
        ]
    )

    agro = [row for row in result.rankings if row.macroactivity == "AGROPECUARIO"]
    assert [(row.bank_code, row.position, row.activity_balance, row.total_valid_portfolio, row.weight_pct) for row in agro] == [
        ("101", 1, Decimal("20.00"), Decimal("20.00"), Decimal("100.0000")),
        ("102", 2, Decimal("20.00"), Decimal("20.00"), Decimal("100.0000")),
    ]
    assert len(result.rankings) == 12  # six rankings by two banks
    assert result.reconciliation_errors == []


def test_ties_use_ascending_bank_code_and_weight_uses_full_portfolio_denominator():
    result = RankingEngine(ACTIVITIES, BANKS).calculate(
        [
            record("a", bank="101", balance="10.00", activity="A.01"),
            record("b", bank="101", balance="10.00", activity="C.10"),
            record("c", bank="102", balance="10.00", activity="A.01"),
        ]
    )

    agro = [row for row in result.rankings if row.macroactivity == "AGROPECUARIO"]
    assert [(row.bank_code, row.position, row.weight_pct) for row in agro] == [
        ("101", 1, Decimal("50.0000")),
        ("102", 2, Decimal("100.0000")),
    ]


def test_sb21_consumo_reclassifies_personal_credit_card_without_changing_total():
    result = RankingEngine(ACTIVITIES, BANKS).calculate(
        [
            record("card", balance="20.00", facility="07"),
            record("personal", balance="10.00", facility="01"),
        ]
    )

    assert {(row.subactivity, row.balance) for row in result.subactivities} == {
        ("Tarjeta", Decimal("20.00")),
        ("Credito personal", Decimal("10.00")),
    }
    consumo = next(row for row in result.rankings if row.macroactivity == "CONSUMO" and row.bank_code == "101")
    assert consumo.activity_balance == Decimal("30.00")
    assert consumo.total_valid_portfolio == Decimal("30.00")


def test_invalid_known_catalog_references_are_alerts_not_exclusions():
    result = RankingEngine(ACTIVITIES, BANKS, facility_codes={"01", "03", "07"}).calculate(
        [record("unknown-bank", bank="999"), record("unknown-facility", facility="99")]
    )

    assert result.quality.local_valid_rows == 2
    assert {alert.code for alert in result.alerts} == {"UNKNOWN_BANK", "UNKNOWN_FACILITY"}


def test_rejects_mixed_periods_and_non_cent_values():
    engine = RankingEngine(ACTIVITIES, BANKS)
    with pytest.raises(ValueError, match="one period"):
        engine.calculate([record("a"), CreditRecord(**{**record("b").__dict__, "period": "20260831"})])
    with pytest.raises(ValueError, match="two decimal"):
        engine.calculate([record("a", balance="1.001")])
