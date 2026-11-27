"""Deterministic SBP ranking engine.

The engine deliberately uses only the supplied catalogs and Decimal arithmetic.
It is independent of the agent/LLM path so official results cannot be produced
or changed by a model.
"""
from __future__ import annotations

import csv
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Iterable

MONEY = Decimal("0.01")
PERCENT = Decimal("0.0001")
RANKINGS = ("HIPOTECARIO", "CONSTRUCCION", "INDUSTRIA", "AGROPECUARIO", "COMERCIO", "CONSUMO")
REQUIRED_COLUMNS = 61


def _d(value: str) -> Decimal:
    return Decimal((value or "0").strip())


def _q(value: Decimal, quantum: Decimal) -> Decimal:
    return value.quantize(quantum, rounding=ROUND_HALF_UP)


def read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def validate_at03(rows: list[dict[str, str]], expected_period: str | None = None) -> list[str]:
    """Return validation errors without mutating input rows."""
    errors: list[str] = []
    if not rows:
        return ["AT03 file is empty"]
    columns = list(rows[0])
    if len(columns) != REQUIRED_COLUMNS:
        errors.append(f"AT03 requires {REQUIRED_COLUMNS} columns, got {len(columns)}")
    for column in ("Fecha", "Codigo_Banco", "Numero_Prestamo", "Tipo_Actividad", "Destino", "Saldo"):
        if column not in columns:
            errors.append(f"missing required column: {column}")
    periods = {row.get("Fecha", "") for row in rows}
    if expected_period and periods != {expected_period}:
        errors.append(f"expected period {expected_period}, got {sorted(periods)}")
    for index, row in enumerate(rows, 2):
        try:
            _d(row.get("Saldo", ""))
        except Exception:
            errors.append(f"row {index}: Saldo is not decimal")
    return errors


def calculate_rankings(
    rows: Iterable[dict[str, str]],
    activities: Iterable[dict[str, str]],
    banks: Iterable[dict[str, str]],
    facilities: Iterable[dict[str, str]] = (),
) -> dict:
    """Calculate quality evidence, rankings, and subactivity totals."""
    rows = list(rows)
    activity_by_code = {r["Codigo_CINU"]: r for r in activities}
    bank_by_code = {r["Codigo_Banco"]: r for r in banks}
    facility_by_code = {r["Codigo_Facilidad"]: r for r in facilities if r.get("Codigo_Facilidad")}
    period = rows[0].get("Fecha", "") if rows else ""
    seen: set[str] = set()
    valid: list[dict[str, str]] = []
    exclusions = {key: 0 for key in ("E1", "E2", "E3", "E4")}
    excluded_rows: list[dict[str, str]] = []
    for row_number, row in enumerate(rows, 1):
        loan = row.get("Numero_Prestamo", "")
        reason = None
        if loan in seen:
            reason = "E1"
        else:
            seen.add(loan)
            if row.get("Destino") != "L":
                reason = "E2"
            elif _d(row.get("Saldo", "0")) <= 0:
                reason = "E3"
            elif row.get("Tipo_Actividad") not in activity_by_code:
                reason = "E4"
        if reason:
            exclusions[reason] += 1
            excluded_rows.append({"row": row_number, "loan": loan, "reason": reason})
        else:
            valid.append(row)

    portfolio: defaultdict[str, Decimal] = defaultdict(Decimal)
    activity_totals: defaultdict[tuple[str, str], Decimal] = defaultdict(Decimal)
    subactivity_totals: defaultdict[tuple[str, str, str], Decimal] = defaultdict(Decimal)
    operations: defaultdict[tuple[str, str], int] = defaultdict(int)
    for row in valid:
        bank = row["Codigo_Banco"]
        amount = _d(row["Saldo"])
        portfolio[bank] += amount
        catalog = activity_by_code[row["Tipo_Actividad"]]
        macro = catalog["Macroactividad_Reto"]
        sub = catalog["Subactividad_Reto"]
        # SB21 rule: personal credit with facility 07 becomes Tarjeta.
        if row["Tipo_Actividad"].endswith("64921") and row.get("Facilidad_Crediticia") == "07":
            sub = "Tarjeta"
        activity_totals[(macro, bank)] += amount
        subactivity_totals[(macro, bank, sub)] += amount
        operations[(macro, bank)] += 1

    result_rows: list[dict] = []
    for macro in RANKINGS:
        ordered = sorted(bank_by_code, key=lambda code: (-activity_totals[(macro, code)], code))
        for position, bank in enumerate(ordered, 1):
            total = portfolio[bank]
            balance = activity_totals[(macro, bank)]
            result_rows.append({
                "Fecha": period, "Ranking": macro, "Posicion": position,
                "Codigo_Banco": bank, "Banco": bank_by_code[bank].get("Nombre_Ficticio", bank),
                "Saldo_Actividad": str(_q(balance, MONEY)),
                "Total_Cartera_Local_Valida": str(_q(total, MONEY)),
                "Ponderacion_Pct": str(_q((balance / total * 100) if total else Decimal("0"), PERCENT)),
                "Operaciones_Validas": operations[(macro, bank)],
            })
    sub_rows = [
        {"Fecha": period, "Ranking": macro, "Subactividad": sub, "Codigo_Banco": bank,
         "Saldo": str(_q(value, MONEY))}
        for (macro, bank, sub), value in sorted(subactivity_totals.items())
    ]
    valid_count = len(valid)
    quality = {
        "period": period, "rows_read": len(rows), "E1": exclusions["E1"],
        "E2": exclusions["E2"], "E3": exclusions["E3"], "E4": exclusions["E4"],
        "valid_universe": valid_count, "reconciles": len(rows) == sum(exclusions.values()) + valid_count,
        "excluded_rows": excluded_rows,
    }
    return {"period": period, "quality": quality, "rankings": result_rows, "subactivities": sub_rows}


def calculate_from_files(at03: str | Path, activity_catalog: str | Path, banks: str | Path,
                         facilities: str | Path | None = None) -> dict:
    return calculate_rankings(read_csv(at03), read_csv(activity_catalog), read_csv(banks),
                              read_csv(facilities) if facilities else ())


def calculate_many_from_files(at03_files: Iterable[str | Path], activity_catalog: str | Path,
                              banks: str | Path, facilities: str | Path | None = None) -> dict:
    """Process every supplied cut independently, then combine the evidence.

    A loan repeated in different files is valid: deduplication happens inside
    calculate_rankings, which is the required per-period cascade.
    """
    results = [
        calculate_from_files(path, activity_catalog, banks, facilities)
        for path in at03_files
    ]
    if not results:
        return {"periods": [], "rankings": [], "subactivities": [], "quality": []}
    return {
        "periods": [result["period"] for result in results],
        "period": results[-1]["period"],
        "rankings": [row for result in results for row in result["rankings"]],
        "subactivities": [row for result in results for row in result["subactivities"]],
        "quality": [result["quality"] for result in results],
    }


def compare_rankings(previous: dict, current: dict, position_threshold: int = 2) -> list[dict]:
    """Compare consecutive deterministic results without involving an LLM."""
    before = {(r["Ranking"], r["Codigo_Banco"]): r for r in previous["rankings"]}
    after = {(r["Ranking"], r["Codigo_Banco"]): r for r in current["rankings"]}
    movements = []
    for key, new in after.items():
        old = before.get(key)
        if not old:
            continue
        position_delta = int(old["Posicion"]) - int(new["Posicion"])
        old_balance = _d(old["Saldo_Actividad"])
        new_balance = _d(new["Saldo_Actividad"])
        balance_delta = new_balance - old_balance
        balance_pct = (balance_delta / old_balance * 100) if old_balance else Decimal("0")
        significant = abs(position_delta) >= position_threshold or position_delta == 11
        movements.append({
            "Ranking": new["Ranking"], "Codigo_Banco": new["Codigo_Banco"], "Banco": new["Banco"],
            "previous_period": previous["period"], "current_period": current["period"],
            "Cambio_Posicion": position_delta, "Var_Saldo": str(_q(balance_delta, MONEY)),
            "Var_Saldo_Pct": str(_q(balance_pct, PERCENT)), "significant": significant,
            "reason": "position threshold" if abs(position_delta) >= position_threshold else
                      ("leader change" if position_delta == 11 else None),
        })
    return movements
