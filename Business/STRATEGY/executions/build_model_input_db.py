#!/usr/bin/env python3
"""Build a lean SQLite database for hedge-model ingestion."""

import json
import sqlite3
from pathlib import Path

from normalize_challenges import INPUT_JSON, normalize_challenge

BASE = Path(__file__).resolve().parent.parent / "resources" / "PropFirmData"
OUTPUT_DB = BASE / "propmatch_model_input.db"
RAW_DB = BASE / "propmatch_challenges.db"

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS model_challenges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_file TEXT NOT NULL,
    source_index INTEGER NOT NULL,
    source_scraped_at TEXT,

    firm TEXT NOT NULL,
    firm_slug TEXT,
    program_name TEXT,
    asset_class TEXT,
    currency TEXT,
    country TEXT,
    rating REAL,
    reviews INTEGER,

    model_family TEXT NOT NULL,
    hedgeable INTEGER,
    hedgeability_reason TEXT,
    eligible_for_core_model INTEGER,
    quarantine_reason TEXT,

    account_size INTEGER NOT NULL,
    steps INTEGER,
    steps_label TEXT,

    fee_assumed REAL,
    fee_original REAL,
    fee_discounted REAL,
    activation_fee REAL,
    reset_fee REAL,
    refundable_fee INTEGER,

    profit_target_phase1 REAL,
    profit_target_phase2 REAL,
    profit_target_phase3 REAL,
    profit_targets_json TEXT,
    profit_split_pct REAL,

    daily_drawdown_pct REAL,
    max_drawdown_pct REAL,
    drawdown_type TEXT,
    max_loss_type TEXT,
    daily_drawdown_reset_type TEXT,
    drawdown_class TEXT,
    drawdown_anchor TEXT,

    payout_days INTEGER,
    payout_timing TEXT,
    min_trading_days INTEGER,
    payout_class TEXT,
    survival_model_class TEXT,

    leverage TEXT,
    leverage_eval TEXT,
    leverage_funded TEXT,

    news_trading INTEGER,
    copy_trading INTEGER,
    eas_allowed INTEGER,
    weekend_holding INTEGER,
    overnight_holding INTEGER,

    canonical_platforms TEXT,
    fee_refund_class TEXT,
    expected_refund_value REAL,
    expected_reset_cost REAL,
    effective_entry_cost REAL,
    requires_time_friction_model INTEGER,
    requires_trailing_engine INTEGER,
    panel_scraped INTEGER,
    panel_error TEXT
);
"""

INSERT_SQL = """
INSERT INTO model_challenges (
    source_file, source_index, source_scraped_at,
    firm, firm_slug, program_name, asset_class, currency, country, rating, reviews,
    model_family, hedgeable, hedgeability_reason, eligible_for_core_model, quarantine_reason,
    account_size, steps, steps_label,
    fee_assumed, fee_original, fee_discounted, activation_fee, reset_fee, refundable_fee,
    profit_target_phase1, profit_target_phase2, profit_target_phase3, profit_targets_json, profit_split_pct,
    daily_drawdown_pct, max_drawdown_pct, drawdown_type, max_loss_type, daily_drawdown_reset_type, drawdown_class, drawdown_anchor,
    payout_days, payout_timing, min_trading_days, payout_class, survival_model_class,
    leverage, leverage_eval, leverage_funded,
    news_trading, copy_trading, eas_allowed, weekend_holding, overnight_holding,
    canonical_platforms, fee_refund_class, expected_refund_value, expected_reset_cost, effective_entry_cost,
    requires_time_friction_model, requires_trailing_engine, panel_scraped, panel_error
) VALUES (
    :source_file, :source_index, :source_scraped_at,
    :firm, :firm_slug, :program_name, :asset_class, :currency, :country, :rating, :reviews,
    :model_family, :hedgeable, :hedgeability_reason, :eligible_for_core_model, :quarantine_reason,
    :account_size, :steps, :steps_label,
    :fee_assumed, :fee_original, :fee_discounted, :activation_fee, :reset_fee, :refundable_fee,
    :profit_target_phase1, :profit_target_phase2, :profit_target_phase3, :profit_targets_json, :profit_split_pct,
    :daily_drawdown_pct, :max_drawdown_pct, :drawdown_type, :max_loss_type, :daily_drawdown_reset_type, :drawdown_class, :drawdown_anchor,
    :payout_days, :payout_timing, :min_trading_days, :payout_class, :survival_model_class,
    :leverage, :leverage_eval, :leverage_funded,
    :news_trading, :copy_trading, :eas_allowed, :weekend_holding, :overnight_holding,
    :canonical_platforms, :fee_refund_class, :expected_refund_value, :expected_reset_cost, :effective_entry_cost,
    :requires_time_friction_model, :requires_trailing_engine, :panel_scraped, :panel_error
);
"""


def classify_model_family(row: dict) -> str:
    if row.get("asset_class") == "futures":
        return "futures"
    if row.get("steps_label") == "Instant":
        return "instant_funded"
    return "fx_challenge"



def assess_hedgeability(row: dict) -> tuple[int, str]:
    model_family = classify_model_family(row)
    drawdown_type = row.get("drawdown_type") or ""

    # Intraday trailing is NOT hedgeable — the trailing happens tick-by-tick
    # within the trading day, so you can't hold an offsetting position safely.
    dd_class = classify_drawdown_class(row)
    if dd_class == "intraday_trailing":
        return 0, "intraday_trailing_not_hedgeable"

    if model_family == "instant_funded":
        if not drawdown_type:
            return 0, "instant_unknown_drawdown_type"
        return 1, "instant_hedgeable"

    if row.get("max_drawdown_pct") is None:
        return 0, "missing_max_drawdown"
    if row.get("profit_split_pct") is None:
        return 0, "missing_profit_split"
    if row.get("fee_assumed") is None:
        return 0, "missing_fee"

    return 1, "core_fields_present"



def choose_leverage(row: dict) -> str:
    return row.get("leverage_funded") or row.get("leverage_eval") or "1:100"


def classify_drawdown_class(row: dict) -> str:
    raw = " ".join(
        str(x).strip().lower()
        for x in (row.get("drawdown_type"), row.get("max_loss_type"))
        if x
    )
    if not raw:
        return "unknown"
    if "intraday" in raw:
        return "intraday_trailing"
    if "trailing" in raw:
        return "trailing"
    if "eod" in raw or "end of day" in raw:
        return "eod_balance"
    if "balance based" in raw or "balance/equity" in raw or "static" in raw:
        return "static"
    if row.get("max_drawdown_pct") == 100:
        return "no_dd_limit"
    return "unknown"


def classify_drawdown_anchor(row: dict) -> str:
    raw = " ".join(
        str(x).strip().lower()
        for x in (row.get("drawdown_type"), row.get("max_loss_type"), row.get("daily_drawdown_reset_type"))
        if x
    )
    if not raw:
        return "unknown"
    if "intraday" in raw:
        return "intraday_peak"
    if "highest at eod" in raw or "eod" in raw or "end of day" in raw:
        return "highest_eod"
    if "equity" in raw:
        return "equity"
    if "balance" in raw or "static" in raw:
        return "balance"
    return "unknown"


def classify_payout_class(row: dict) -> str:
    model_family = classify_model_family(row)
    if model_family == "futures":
        return "futures"
    if model_family == "instant_funded":
        return "instant_funded"
    return "funded_continuation"


def classify_fee_refund_class(row: dict) -> str:
    refundable_fee = row.get("refundable_fee")
    if refundable_fee == 1:
        return "refundable_on_pass"
    if refundable_fee == 0:
        return "non_refundable"
    return "unclear"


def classify_survival_model_class(row: dict, drawdown_class: str) -> str:
    model_family = classify_model_family(row)
    if model_family == "futures":
        return "futures_trailing"
    if model_family == "instant_funded":
        if drawdown_class in {"trailing", "intraday_trailing"}:
            return "instant_trailing"
        return "instant_static"
    if drawdown_class in {"trailing", "intraday_trailing"}:
        return "challenge_trailing"
    return "challenge_static"


def compute_expected_refund_value(row: dict) -> float:
    fee_assumed = row.get("fee_assumed") or 0.0
    return float(fee_assumed) if row.get("refundable_fee") == 1 else 0.0


def compute_expected_reset_cost(row: dict) -> float:
    return 0.0


def compute_effective_entry_cost(row: dict, expected_refund_value: float, expected_reset_cost: float) -> float:
    fee_assumed = row.get("fee_assumed") or 0.0
    activation_fee = row.get("activation_fee") or 0.0
    return round(float(fee_assumed) + float(activation_fee) + float(expected_reset_cost) - float(expected_refund_value), 2)


def requires_time_friction_model(row: dict) -> int:
    return 1 if (row.get("min_trading_days") or 0) > 0 else 0


def requires_trailing_engine(drawdown_class: str) -> int:
    return 1 if drawdown_class in {"trailing", "intraday_trailing"} else 0


def determine_core_eligibility(row: dict, hedgeable: int, hedgeability_reason: str) -> tuple[int, str | None]:
    if hedgeable != 1:
        return 0, hedgeability_reason
    if hedgeability_reason in {"instant_unknown_drawdown_type", "missing_max_drawdown", "missing_profit_split", "missing_fee", "intraday_trailing_not_hedgeable"}:
        return 0, hedgeability_reason
    return 1, None



def load_source_rows() -> tuple[str, list[dict]]:
    if INPUT_JSON is not None and INPUT_JSON.exists():
        with open(INPUT_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)
        raw_rows = data["challenges"]
        normalized_rows = [normalize_challenge(row) for row in raw_rows]
        return INPUT_JSON.name, normalized_rows

    if RAW_DB.exists():
        conn = sqlite3.connect(str(RAW_DB))
        conn.row_factory = sqlite3.Row
        rows = [dict(row) for row in conn.execute("SELECT * FROM challenges ORDER BY id")]
        conn.close()
        return RAW_DB.name, rows

    raise FileNotFoundError(
        f"No propmatch_challenges_*.json or {RAW_DB.name} found in {BASE}"
    )



def build_model_row(normalized_row: dict, source_index: int, source_file: str) -> dict:
    model_family = classify_model_family(normalized_row)
    hedgeable, hedgeability_reason = assess_hedgeability(normalized_row)
    drawdown_class = classify_drawdown_class(normalized_row)
    drawdown_anchor = classify_drawdown_anchor(normalized_row)
    payout_class = classify_payout_class(normalized_row)
    fee_refund_class = classify_fee_refund_class(normalized_row)
    survival_model_class = classify_survival_model_class(normalized_row, drawdown_class)
    expected_refund_value = compute_expected_refund_value(normalized_row)
    expected_reset_cost = compute_expected_reset_cost(normalized_row)
    effective_entry_cost = compute_effective_entry_cost(normalized_row, expected_refund_value, expected_reset_cost)
    core_eligible, quarantine_reason = determine_core_eligibility(
        normalized_row, hedgeable, hedgeability_reason
    )

    return {
        "source_file": source_file,
        "source_index": source_index,
        "source_scraped_at": normalized_row.get("scraped_at"),

        "firm": normalized_row.get("firm"),
        "firm_slug": normalized_row.get("firm_slug"),
        "program_name": normalized_row.get("program_name"),
        "asset_class": normalized_row.get("asset_class"),
        "currency": normalized_row.get("currency"),
        "country": normalized_row.get("country"),
        "rating": normalized_row.get("rating"),
        "reviews": normalized_row.get("reviews"),

        "model_family": model_family,
        "hedgeable": hedgeable,
        "hedgeability_reason": hedgeability_reason,
        "eligible_for_core_model": core_eligible,
        "quarantine_reason": quarantine_reason,

        "account_size": normalized_row.get("account_size"),
        "steps": normalized_row.get("steps"),
        "steps_label": normalized_row.get("steps_label"),

        "fee_assumed": normalized_row.get("fee_assumed"),
        "fee_original": normalized_row.get("fee_original"),
        "fee_discounted": normalized_row.get("fee_discounted"),
        "activation_fee": normalized_row.get("activation_fee"),
        "reset_fee": normalized_row.get("reset_fee"),
        "refundable_fee": normalized_row.get("refundable_fee"),

        "profit_target_phase1": normalized_row.get("profit_target_phase1"),
        "profit_target_phase2": normalized_row.get("profit_target_phase2"),
        "profit_target_phase3": normalized_row.get("profit_target_phase3"),
        "profit_targets_json": normalized_row.get("profit_targets_json"),
        "profit_split_pct": normalized_row.get("profit_split_pct"),

        "daily_drawdown_pct": normalized_row.get("daily_drawdown_pct"),
        "max_drawdown_pct": normalized_row.get("max_drawdown_pct"),
        "drawdown_type": normalized_row.get("drawdown_type"),
        "max_loss_type": normalized_row.get("max_loss_type"),
        "daily_drawdown_reset_type": normalized_row.get("daily_drawdown_reset_type"),
        "drawdown_class": drawdown_class,
        "drawdown_anchor": drawdown_anchor,

        "payout_days": normalized_row.get("payout_days"),
        "payout_timing": normalized_row.get("payout_timing_clean"),
        "min_trading_days": normalized_row.get("min_trading_days"),
        "payout_class": payout_class,
        "survival_model_class": survival_model_class,

        "leverage": choose_leverage(normalized_row),
        "leverage_eval": normalized_row.get("leverage_eval"),
        "leverage_funded": normalized_row.get("leverage_funded"),

        "news_trading": normalized_row.get("news_trading"),
        "copy_trading": normalized_row.get("copy_trading"),
        "eas_allowed": normalized_row.get("eas_allowed"),
        "weekend_holding": normalized_row.get("weekend_holding"),
        "overnight_holding": normalized_row.get("overnight_holding"),

        "canonical_platforms": normalized_row.get("canonical_platforms"),
        "fee_refund_class": fee_refund_class,
        "expected_refund_value": expected_refund_value,
        "expected_reset_cost": expected_reset_cost,
        "effective_entry_cost": effective_entry_cost,
        "requires_time_friction_model": requires_time_friction_model(normalized_row),
        "requires_trailing_engine": requires_trailing_engine(drawdown_class),
        "panel_scraped": normalized_row.get("panel_scraped"),
        "panel_error": normalized_row.get("panel_error"),
    }



def main() -> None:
    source_file, normalized_rows = load_source_rows()
    model_rows = [
        build_model_row(normalized_row, index, source_file)
        for index, normalized_row in enumerate(normalized_rows, start=1)
    ]

    if OUTPUT_DB.exists():
        OUTPUT_DB.unlink()

    conn = sqlite3.connect(str(OUTPUT_DB))
    cur = conn.cursor()
    cur.execute(CREATE_TABLE_SQL)
    cur.executemany(INSERT_SQL, model_rows)

    cur.execute(
        """
        CREATE VIEW IF NOT EXISTS v_fx_model AS
        SELECT *
        FROM model_challenges
        WHERE model_family = 'fx_challenge' AND hedgeable = 1
        ORDER BY account_size, fee_assumed;
        """
    )
    cur.execute(
        """
        CREATE VIEW IF NOT EXISTS v_instant_model AS
        SELECT *
        FROM model_challenges
        WHERE model_family = 'instant_funded'
        ORDER BY hedgeable DESC, account_size, fee_assumed;
        """
    )
    cur.execute(
        """
        CREATE VIEW IF NOT EXISTS v_instant_model_eligible AS
        SELECT *
        FROM model_challenges
        WHERE model_family = 'instant_funded' AND hedgeable = 1
        ORDER BY account_size, fee_assumed;
        """
    )
    cur.execute(
        """
        CREATE VIEW IF NOT EXISTS v_model_inputs AS
        SELECT
            id,
            source_file,
            source_index,
            source_scraped_at,
            firm,
            firm_slug,
            rating,
            reviews,
            model_family,
            payout_class,
            survival_model_class,
            account_size,
            program_name,
            steps,
            steps_label,
            profit_target_phase1,
            profit_target_phase2,
            profit_target_phase3,
            profit_targets_json AS profit_targets,
            fee_assumed,
            fee_original,
            fee_discounted,
            activation_fee,
            reset_fee,
            refundable_fee,
            fee_refund_class,
            expected_refund_value,
            expected_reset_cost,
            effective_entry_cost,
            leverage,
            leverage_eval,
            leverage_funded,
            max_drawdown_pct,
            daily_drawdown_pct,
            drawdown_type,
            max_loss_type,
            daily_drawdown_reset_type,
            drawdown_class,
            drawdown_anchor,
            profit_split_pct,
            payout_days,
            payout_timing,
            min_trading_days,
            requires_time_friction_model,
            requires_trailing_engine,
            canonical_platforms,
            news_trading,
            copy_trading,
            eas_allowed,
            weekend_holding,
            overnight_holding,
            currency,
            country,
            hedgeable,
            hedgeability_reason,
            eligible_for_core_model,
            quarantine_reason,
            panel_scraped,
            panel_error
        FROM model_challenges
        WHERE eligible_for_core_model = 1
        ORDER BY model_family, firm, account_size;
        """
    )
    cur.execute(
        """
        CREATE VIEW IF NOT EXISTS v_model_required_fields AS
        SELECT *
        FROM v_model_inputs;
        """
    )
    cur.execute(
        """
        CREATE VIEW IF NOT EXISTS v_model_eligible AS
        SELECT *
        FROM v_model_inputs;
        """
    )
    cur.execute(
        """
        CREATE VIEW IF NOT EXISTS v_quarantined AS
        SELECT
            id,
            firm,
            model_family,
            account_size,
            program_name,
            drawdown_type,
            max_loss_type,
            drawdown_class,
            hedgeability_reason,
            quarantine_reason,
            fee_assumed,
            activation_fee,
            reset_fee,
            refundable_fee,
            max_drawdown_pct,
            profit_split_pct,
            min_trading_days,
            panel_scraped,
            panel_error
        FROM model_challenges
        WHERE eligible_for_core_model = 0
        ORDER BY quarantine_reason, firm, account_size;
        """
    )
    conn.commit()

    total_rows = cur.execute("SELECT COUNT(*) FROM model_challenges").fetchone()[0]
    hedgeable_rows = cur.execute("SELECT COUNT(*) FROM model_challenges WHERE hedgeable = 1").fetchone()[0]
    eligible_rows = cur.execute("SELECT COUNT(*) FROM v_model_inputs").fetchone()[0]
    quarantined_rows = cur.execute("SELECT COUNT(*) FROM v_quarantined").fetchone()[0]
    fx_rows = cur.execute("SELECT COUNT(*) FROM v_fx_model").fetchone()[0]
    instant_rows = cur.execute("SELECT COUNT(*) FROM v_instant_model").fetchone()[0]

    print(f"Created {OUTPUT_DB.name}")
    print(f"Source: {source_file}")
    print(f"Rows: {total_rows}")
    print(f"Hedgeable rows: {hedgeable_rows}")
    print(f"Eligible (strict): {eligible_rows}")
    print(f"Quarantined: {quarantined_rows}")
    print(f"FX challenge rows: {fx_rows}")
    print(f"Instant rows: {instant_rows}")
    print("\nHedgeability breakdown:")
    for reason, count in cur.execute(
        "SELECT hedgeability_reason, COUNT(*) FROM model_challenges GROUP BY hedgeability_reason ORDER BY COUNT(*) DESC"
    ):
        print(f"  {count:>4}  {reason}")

    conn.close()


if __name__ == "__main__":
    main()
