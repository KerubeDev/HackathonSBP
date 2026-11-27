"""Deterministic SBP ranking calculation boundary.

This module deliberately has no dependency on the AI agent or persistence layer:
official results are generated solely from source records and the frozen catalogs.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
from typing import Iterable


CENT = Decimal("0.01")
PERCENT = Decimal("0.0001")
PERSONAL_CREDIT = "K.64.649.6492.64921"
AUTOMOBILE = "K.64.649.6492.64922"
CREDIT_CARD = "K.64.649.6499.64991"


@dataclass(frozen=True)
class Bank:
    code: str
    name: str


@dataclass(frozen=True)
class ActivityCatalogEntry:
    code: str
    macroactivity: str
    subactivity: str


@dataclass(frozen=True)
class CreditRecord:
    period: str
    loan_number: str
    bank_code: str
    destination: str
    balance: Decimal
    activity_code: str
    facility_code: str

    def __post_init__(self) -> None:
        if not isinstance(self.balance, Decimal):
            raise TypeError("balance must be a Decimal")
        if self.balance.quantize(CENT) != self.balance:
            raise ValueError("balance must use at most two decimal places")


@dataclass(frozen=True)
class Exclusion:
    loan_number: str
    reason: str


@dataclass(frozen=True)
class QualityAlert:
    code: str
    loan_number: str
    message: str


@dataclass(frozen=True)
class QualityReport:
    rows_read: int
    excluded_e1_duplicates: int
    excluded_e2_foreign_destination: int
    excluded_e3_non_positive_balance: int
    excluded_e4_uncatalogued_activity: int
    local_valid_rows: int

    def as_dict(self) -> dict[str, int]:
        return self.__dict__.copy()


@dataclass(frozen=True)
class RankingRow:
    period: str
    macroactivity: str
    position: int
    bank_code: str
    bank_name: str
    activity_balance: Decimal
    total_valid_portfolio: Decimal
    weight_pct: Decimal
    valid_operations: int


@dataclass(frozen=True)
class SubactivityRow:
    period: str
    macroactivity: str
    subactivity: str
    bank_code: str
    balance: Decimal


@dataclass(frozen=True)
class RankingResult:
    period: str
    quality: QualityReport
    exclusions: list[Exclusion]
    alerts: list[QualityAlert]
    rankings: list[RankingRow]
    subactivities: list[SubactivityRow]
    reconciliation_errors: list[str]
    source_hash: str
    rule_version: str
    catalog_version: str


class RankingEngine:
    """Calculates one period using the exclusive E1–E4 cascade."""

    def __init__(
        self,
        activities: Iterable[ActivityCatalogEntry],
        banks: Iterable[Bank],
        *,
        facility_codes: set[str] | None = None,
        rule_version: str = "sbp-2026-v1",
        catalog_version: str = "frozen-v1",
    ) -> None:
        activity_list, bank_list = list(activities), list(banks)
        self.activities = {entry.code: entry for entry in activity_list}
        self.banks = {bank.code: bank for bank in bank_list}
        if len(self.activities) != len(activity_list) or len(self.banks) != len(bank_list):
            raise ValueError("catalog codes must be unique")
        self.macroactivities = sorted({entry.macroactivity for entry in activity_list})
        if len(self.macroactivities) != 6:
            raise ValueError("the SBP catalog must define exactly six macroactivities")
        self.facility_codes = facility_codes
        self.rule_version, self.catalog_version = rule_version, catalog_version

    def calculate(self, records: Iterable[CreditRecord]) -> RankingResult:
        rows = list(records)
        periods = {row.period for row in rows}
        if len(periods) > 1:
            raise ValueError("a calculation run must contain exactly one period")
        period = next(iter(periods), "")
        exclusions: list[Exclusion] = []
        alerts: list[QualityAlert] = []
        unique: list[CreditRecord] = []
        loans: set[str] = set()
        for row in rows:
            if row.loan_number in loans:
                exclusions.append(Exclusion(row.loan_number, "E1_DUPLICATE"))
            else:
                loans.add(row.loan_number)
                unique.append(row)

        local = [row for row in unique if row.destination == "L"]
        exclusions.extend(Exclusion(row.loan_number, "E2_FOREIGN_DESTINATION") for row in unique if row.destination != "L")
        positive = [row for row in local if row.balance > 0]
        exclusions.extend(Exclusion(row.loan_number, "E3_NON_POSITIVE_BALANCE") for row in local if row.balance <= 0)
        valid = [row for row in positive if row.activity_code in self.activities]
        exclusions.extend(Exclusion(row.loan_number, "E4_UNCATALOGUED_ACTIVITY") for row in positive if row.activity_code not in self.activities)

        subactivity_totals: dict[tuple[str, str, str], Decimal] = defaultdict(lambda: Decimal("0.00"))
        activity_totals: dict[tuple[str, str], Decimal] = defaultdict(lambda: Decimal("0.00"))
        operations: dict[tuple[str, str], int] = defaultdict(int)
        portfolio_totals: dict[str, Decimal] = defaultdict(lambda: Decimal("0.00"))
        for row in valid:
            entry = self.activities[row.activity_code]
            if row.bank_code not in self.banks:
                alerts.append(QualityAlert("UNKNOWN_BANK", row.loan_number, "Bank code is not in the supplied catalog."))
            if self.facility_codes is not None and row.facility_code not in self.facility_codes:
                alerts.append(QualityAlert("UNKNOWN_FACILITY", row.loan_number, "Facility code is not in the supplied catalog."))
            subactivity = self._subactivity(row, entry, alerts)
            key = (entry.macroactivity, row.bank_code)
            subactivity_totals[(entry.macroactivity, subactivity, row.bank_code)] += row.balance
            activity_totals[key] += row.balance
            operations[key] += 1
            portfolio_totals[row.bank_code] += row.balance

        rankings = self._rankings(period, activity_totals, portfolio_totals, operations)
        subactivities = [
            SubactivityRow(period, macro, sub, bank, balance.quantize(CENT))
            for (macro, sub, bank), balance in sorted(subactivity_totals.items())
        ]
        quality = QualityReport(
            len(rows),
            sum(item.reason == "E1_DUPLICATE" for item in exclusions),
            sum(item.reason == "E2_FOREIGN_DESTINATION" for item in exclusions),
            sum(item.reason == "E3_NON_POSITIVE_BALANCE" for item in exclusions),
            sum(item.reason == "E4_UNCATALOGUED_ACTIVITY" for item in exclusions),
            len(valid),
        )
        errors = self._reconcile(rankings, subactivities, portfolio_totals)
        return RankingResult(
            period, quality, exclusions, alerts, rankings, subactivities, errors,
            self._source_hash(rows), self.rule_version, self.catalog_version,
        )

    def _subactivity(self, row: CreditRecord, entry: ActivityCatalogEntry, alerts: list[QualityAlert]) -> str:
        if row.activity_code == PERSONAL_CREDIT and row.facility_code == "07":
            return "Tarjeta"
        if row.activity_code == AUTOMOBILE and row.facility_code != "03":
            alerts.append(QualityAlert("SB21_AUTOMOBILE_FACILITY_MISMATCH", row.loan_number, "Automobile activity must use facility 03."))
        if row.activity_code == CREDIT_CARD and row.facility_code != "07":
            alerts.append(QualityAlert("SB21_CREDIT_CARD_FACILITY_MISMATCH", row.loan_number, "Credit-card activity must use facility 07."))
        return entry.subactivity

    def _rankings(self, period, totals, portfolios, operations) -> list[RankingRow]:
        result: list[RankingRow] = []
        for macro in self.macroactivities:
            ordered = sorted(
                self.banks.values(),
                key=lambda bank: (-totals[(macro, bank.code)], bank.code),
            )
            for position, bank in enumerate(ordered, start=1):
                balance, total = totals[(macro, bank.code)], portfolios[bank.code]
                weight = Decimal("0.0000") if total == 0 else (balance * 100 / total).quantize(PERCENT, rounding=ROUND_HALF_UP)
                result.append(RankingRow(period, macro, position, bank.code, bank.name, balance.quantize(CENT), total.quantize(CENT), weight, operations[(macro, bank.code)]))
        return result

    def _reconcile(self, rankings, subactivities, portfolios) -> list[str]:
        errors: list[str] = []
        sub_totals: dict[tuple[str, str], Decimal] = defaultdict(lambda: Decimal("0.00"))
        for row in subactivities:
            sub_totals[(row.macroactivity, row.bank_code)] += row.balance
        per_bank: dict[str, Decimal] = defaultdict(lambda: Decimal("0.00"))
        for row in rankings:
            if sub_totals[(row.macroactivity, row.bank_code)] != row.activity_balance:
                errors.append(f"subactivity reconciliation failed for {row.macroactivity}/{row.bank_code}")
            per_bank[row.bank_code] += row.activity_balance
        for bank in self.banks.values():
            if per_bank[bank.code] != portfolios[bank.code]:
                errors.append(f"portfolio reconciliation failed for {bank.code}")
        return errors

    def _source_hash(self, rows: list[CreditRecord]) -> str:
        payload = "\n".join(
            "|".join((row.period, row.loan_number, row.bank_code, row.destination, str(row.balance), row.activity_code, row.facility_code))
            for row in rows
        )
        return sha256(payload.encode()).hexdigest()
