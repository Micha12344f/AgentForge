#!/usr/bin/env python3
"""Helpers for applying review-adjusted EV metrics inside notebooks."""

from __future__ import annotations

from collections.abc import Sequence

import pandas as pd

from hedge_arbitrage_model import compute_review_adjustment


def build_review_adjusted_dataframe(
    results: Sequence[dict | None],
    challenges: Sequence[dict],
    raw_ev_col: str,
    revenue_cols: Sequence[str],
    capital_col: str = "capital_required",
    fee_col: str = "fee",
) -> pd.DataFrame:
    """Attach review fields and adjusted EV metrics to notebook result rows.

    The function assumes results were produced in the same order as challenges.
    Any `None` result rows are skipped, which keeps it compatible with notebooks
    that filter invalid offers after model evaluation.
    """
    enriched: list[dict] = []

    for result, challenge in zip(results, challenges):
        if result is None:
            continue

        row = dict(result)
        review = compute_review_adjustment(challenge)
        row.update(review)

        revenue_base = 0.0
        for col in revenue_cols:
            value = row.get(col)
            if value is not None:
                revenue_base += float(value)

        review_factor = float(review["review_factor"])
        review_penalty = revenue_base * (1.0 - review_factor)
        raw_ev = float(row.get(raw_ev_col, 0.0) or 0.0)

        row["review_revenue_base"] = round(revenue_base, 2)
        row["review_revenue_penalty"] = round(review_penalty, 2)
        row["EV_review_adj"] = round(raw_ev - review_penalty, 2)

        if len(revenue_cols) == 1:
            revenue_col = revenue_cols[0]
            row[f"{revenue_col}_review_adj"] = round(
                float(row.get(revenue_col, 0.0) or 0.0) * review_factor,
                2,
            )

        capital_value = row.get(capital_col)
        if capital_value not in (None, 0):
            capital_value = float(capital_value)
            row["capital_efficiency_review_adj"] = round(
                row["EV_review_adj"] / capital_value,
                4,
            )
        else:
            row["capital_efficiency_review_adj"] = 0.0

        fee_value = row.get(fee_col)
        if fee_value not in (None, 0):
            fee_value = float(fee_value)
            row["cost_efficiency_review_adj"] = round(
                row["EV_review_adj"] / fee_value,
                4,
            )
        else:
            row["cost_efficiency_review_adj"] = 0.0

        enriched.append(row)

    return pd.DataFrame(enriched)