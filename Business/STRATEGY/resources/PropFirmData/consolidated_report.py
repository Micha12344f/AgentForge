#!/usr/bin/env python3
"""
Hedge Edge - Consolidated Prop-Firm Hedge Model Report
=======================================================
Loads all data (CFD/Forex, Futures, Instant Funded), runs every Type A/B/C
model, and generates a single in-depth PDF report.
"""

import glob, json, math, os, re, textwrap, io
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
from fpdf import FPDF

# -- PATHS --------------------------------------------------------------------
DATA_DIR = Path(__file__).parent
OUTPUT_PDF = DATA_DIR / f"HedgeEdge_Consolidated_Report_{datetime.now():%Y%m%d_%H%M%S}.pdf"
CHART_DIR = DATA_DIR / "_charts"
CHART_DIR.mkdir(exist_ok=True)

# -- GLOBAL PARAMETERS --------------------------------------------------------
# CFD/Forex
FX_FUNDED_TARGET       = 0.08
FX_SPREAD_COST         = 0.0003
FX_RESIZES             = 20
FX_WITHDRAWAL_PCT      = 0.04
FX_CYCLES              = 6
FX_SURVIVAL            = 0.80
FX_HEDGE_DRAG          = 0.015
FX_SURPLUS_PCT         = 0.02

# Futures
FUT_FUNDED_TARGET      = 0.06
FUT_SPREAD_CONTRACT    = 5.00
FUT_CONSISTENCY        = 0.20
FUT_WITHDRAWAL_PCT     = 0.04
FUT_CYCLES             = 6
FUT_SURVIVAL           = 0.80
FUT_HEDGE_DRAG         = 0.015
FUT_SURPLUS_PCT        = 0.02

# Instant Funded
IF_PAYOUT_TARGET       = 0.05
IF_SPREAD              = 0.0003
IF_BASE_DAYS           = 5
IF_ASSUME_UNSPEC       = "static"
IF_LEVERAGE            = 100


# +==============================================================================+
# |  1.  HELPER FUNCTIONS                                                       |
# +==============================================================================+

# -- CFD helpers ---------------------------------------------------------------
def classify_drawdown(dd_type_str):
    if not dd_type_str or dd_type_str == "-":
        return "static"
    if "trailing" in str(dd_type_str).lower():
        return "trailing"
    return "static"


# -- Futures helpers -----------------------------------------------------------
def parse_dollar(val):
    if isinstance(val, (int, float)):
        return float(val)
    if not val or val == '-' or str(val).lower() == 'none':
        return 0.0
    cleaned = re.sub(r'[^\d.]', '', str(val).replace(',', ''))
    return float(cleaned) if cleaned else 0.0

def parse_pct(val):
    if isinstance(val, (int, float)):
        return float(val) if val > 1 else val * 100
    if not val or val == '-' or str(val).lower() == 'none':
        return 0.0
    cleaned = re.sub(r'[^\d.]', '', str(val))
    return float(cleaned) if cleaned else 0.0

def parse_consistency(val):
    if not val or val == '-' or str(val).lower() == 'none':
        return 0.0
    cleaned = re.sub(r'[^\d.]', '', str(val))
    if cleaned:
        pct = float(cleaned)
        return pct / 100.0 if pct > 1 else pct
    return 0.0

def classify_dd_type_fut(val):
    if not val:
        return "trailing"
    v = str(val).lower()
    if "trail" in v:
        return "trailing"
    if "static" in v or "balance" in v:
        return "static"
    return "trailing"

def normalise_futures(c):
    fee = parse_dollar(c.get('fee_assumed') or c.get('fee_original') or c.get('fee_discounted') or 0)
    activation = parse_dollar(c.get('activation_fee', 0))
    profit_target = parse_dollar(c.get('profit_target', 0))
    if profit_target == 0 and c.get('profit_targets'):
        targets = c['profit_targets']
        if isinstance(targets, list) and targets:
            profit_target = sum(parse_dollar(t) for t in targets)
    max_loss = parse_dollar(c.get('max_loss') or c.get('max_drawdown_pct', 0))
    account_size = parse_dollar(c.get('account_size', 0))
    split = parse_pct(c.get('profit_split_pct') or c.get('profit_split', 80)) / 100.0
    payout_cap = parse_dollar(c.get('max_payout_amount', 0))
    dd_type = classify_dd_type_fut(c.get('max_loss_type', ''))
    cr = c.get('consistency_rule', {})
    if isinstance(cr, dict):
        consistency_eval = parse_consistency(cr.get('eval', 'None'))
    else:
        consistency_eval = parse_consistency(c.get('consistency_rule_eval', 'None'))
    mc = c.get('max_contract_size', c.get('max_contracts_minis', 0))
    if isinstance(mc, dict):
        minis = int(mc.get('minis', 0) or 0)
    elif isinstance(mc, str):
        nums = re.findall(r'\d+', mc)
        minis = int(nums[0]) if nums else 0
    else:
        minis = int(mc) if mc else 0
    return {
        'firm': c.get('firm', 'Unknown'), 'account_size': account_size,
        'steps': int(c.get('steps', 1) if c.get('steps') else 1),
        'fee': fee, 'activation_fee': activation,
        'profit_target': profit_target, 'max_loss': max_loss,
        'dd_type': dd_type, 'profit_split': split,
        'max_contracts_minis': minis, 'payout_cap': payout_cap,
        'consistency_eval': consistency_eval,
    }


# -- Instant-funded helpers ----------------------------------------------------
def parse_number(val):
    if isinstance(val, (int, float)):
        return float(val)
    text = str(val or "").strip()
    if not text or text == '-' or text.lower() == 'none':
        return 0.0
    cleaned = re.sub(r'[^\d.]', '', text.replace(',', ''))
    return float(cleaned) if cleaned else 0.0

def pct_to_ratio(val):
    num = parse_number(val)
    return num / 100.0 if num > 1 else num

def classify_drawdown_if(val):
    text = str(val or "").strip().lower()
    if not text or text == '-':
        return "unspecified"
    if "trail" in text or "highest" in text:
        return "trailing"
    if "balance based" in text or "static" in text:
        return "static"
    return "unspecified"

def extract_consistency_ratio(challenge):
    keys = ["consistency_rule", "consistency_rule_pct", "consistency_threshold",
            "consistency_threshold_pct", "max_daily_profit_pct",
            "daily_consistency_pct", "profit_consistency_pct"]
    ratios = []
    for key in keys:
        value = challenge.get(key)
        if isinstance(value, dict):
            for nested in value.values():
                ratio = pct_to_ratio(nested)
                if ratio > 0:
                    ratios.append(ratio)
        else:
            ratio = pct_to_ratio(value)
            if ratio > 0:
                ratios.append(ratio)
    return min(ratios) if ratios else 0.0

def normalise_instant(row):
    return {
        "firm": row.get("firm", "Unknown"),
        "account_size": parse_number(row.get("account_size")),
        "fee": parse_number(row.get("fee_discounted") or row.get("fee_original") or row.get("fee_assumed")),
        "max_dd_ratio": pct_to_ratio(row.get("max_drawdown_pct")),
        "daily_dd_ratio": pct_to_ratio(row.get("daily_drawdown_pct")),
        "profit_split": pct_to_ratio(row.get("profit_split_pct") or 80),
        "dd_type": classify_drawdown_if(row.get("drawdown_type")),
        "payout_timing": row.get("payout_timing", ""),
        "consistency_ratio": extract_consistency_ratio(row),
    }


# +==============================================================================+
# |  2.  MODEL COMPUTE FUNCTIONS                                                |
# +==============================================================================+

# --------------------- CFD Type A ---------------------------------------------
def compute_fx_type_a(ch, funded_target=FX_FUNDED_TARGET,
                      spread=FX_SPREAD_COST, resizes=FX_RESIZES):
    S = ch.get("account_size", 0)
    fee = ch.get("fee_assumed") or ch.get("fee_original") or ch.get("fee_discounted") or 0
    targets = ch.get("profit_targets") or []
    steps = ch.get("steps") or len(targets) or 2
    dd_max = (ch.get("max_drawdown_pct") or 10.0) / 100.0
    split = (ch.get("profit_split_pct") or 80.0) / 100.0
    dd_cat = classify_drawdown(ch.get("drawdown_type", ""))
    if targets:
        pts = [t / 100.0 for t in targets]
    else:
        pts = [0.08 / steps] * steps
    L = fee
    for i in range(steps):
        pt = pts[i] if i < len(pts) else pts[-1]
        if dd_cat == "trailing":
            dm = pt / resizes
            for _ in range(resizes):
                hs = L / dd_max
                L += hs * dm + hs * spread * 2
        else:
            hs = L / dd_max if dd_max > 0 else 0
            L += hs * pt + hs * spread * 2
    total_cost = L
    payout = S * funded_target * split
    EV = payout - total_cost
    cap_hs = total_cost / dd_max if dd_max > 0 else 0
    capital = cap_hs / 100 + cap_hs * dd_max * 1.5
    return {
        "firm": ch.get("firm"), "account_size": S, "fee": round(fee, 2),
        "steps": steps, "dd_category": dd_cat,
        "max_drawdown_pct": round(dd_max * 100, 2),
        "profit_split_pct": round(split * 100, 1),
        "total_cost": round(total_cost, 2), "funded_payout": round(payout, 2),
        "EV": round(EV, 2),
        "breakeven_pct": round((total_cost / split / S) * 100, 2) if S > 0 and split > 0 else 0,
        "capital_required": round(capital, 2),
        "capital_efficiency": round(EV / capital, 4) if capital > 0 else 0,
    }


# --------------------- CFD Type A cost helper ---------------------------------
def _fx_cost(ch, funded_target=FX_FUNDED_TARGET, spread=FX_SPREAD_COST, resizes=FX_RESIZES):
    S = ch.get("account_size", 0)
    fee = ch.get("fee_assumed") or ch.get("fee_original") or ch.get("fee_discounted") or 0
    targets = ch.get("profit_targets") or []
    steps = ch.get("steps") or len(targets) or 2
    dd_max = (ch.get("max_drawdown_pct") or 10.0) / 100.0
    split = (ch.get("profit_split_pct") or 80.0) / 100.0
    dd_cat = classify_drawdown(ch.get("drawdown_type", ""))
    if targets:
        pts = [t / 100.0 for t in targets]
    else:
        pts = [0.08 / steps] * steps
    L = fee
    for i in range(steps):
        pt = pts[i] if i < len(pts) else pts[-1]
        if dd_cat == "trailing":
            dm = pt / resizes
            for _ in range(resizes):
                hs = L / dd_max
                L += hs * dm + hs * spread * 2
        else:
            hs = L / dd_max if dd_max > 0 else 0
            L += hs * pt + hs * spread * 2
    return {"firm": ch.get("firm"), "account_size": S, "fee": round(fee, 2),
            "steps": steps, "dd_category": dd_cat, "dd_max": dd_max,
            "split": split, "challenge_cost": round(L, 2)}


# --------------------- CFD Type B ---------------------------------------------
def compute_fx_type_b(ch):
    base = _fx_cost(ch)
    S, split, dd = base["account_size"], base["split"], base["dd_max"]
    L = base["challenge_cost"]
    tw, td = 0.0, 0.0
    cum = 1.0
    for k in range(1, FX_CYCLES + 1):
        pa = cum
        w = S * FX_WITHDRAWAL_PCT * split * pa
        d = S * FX_HEDGE_DRAG * pa
        L += S * FX_HEDGE_DRAG
        tw += w; td += d
        cum *= FX_SURVIVAL
    ev_a = S * FX_FUNDED_TARGET * split - base["challenge_cost"]
    ev_b = tw - td
    hs = L / dd if dd > 0 else 0
    capital = hs / 100 + hs * dd * 1.5
    return {
        "firm": base["firm"], "account_size": S, "fee": base["fee"],
        "steps": base["steps"], "dd_category": base["dd_category"],
        "challenge_cost": base["challenge_cost"],
        "type_a_ev": round(ev_a, 2), "ev_b": round(ev_b, 2),
        "ev_advantage": round(ev_b - ev_a, 2),
        "total_withdrawals": round(tw, 2), "total_drag": round(td, 2),
        "capital_required": round(capital, 2),
        "capital_efficiency": round(ev_b / capital, 4) if capital > 0 else 0,
    }


# --------------------- CFD Type C ---------------------------------------------
def compute_fx_type_c(ch, surplus_pct=FX_SURPLUS_PCT):
    base = _fx_cost(ch)
    S, split, dd = base["account_size"], base["split"], base["dd_max"]
    L = base["challenge_cost"]
    P = S * surplus_pct
    tw, td, es = 0.0, 0.0, 0.0
    cum = 1.0
    for k in range(1, FX_CYCLES + 1):
        pa = cum
        w = S * FX_WITHDRAWAL_PCT * split * pa
        dm = (L + P) / L if L > 0 else 1.0
        d = S * FX_HEDGE_DRAG * dm * pa
        L += S * FX_HEDGE_DRAG * dm
        pf = pa * (1 - FX_SURVIVAL)
        es += P * pf
        tw += w; td += d
        cum *= FX_SURVIVAL
    ev_a = S * FX_FUNDED_TARGET * split - base["challenge_cost"]
    ev_c = tw + es - td
    hs = (L + P) / dd if dd > 0 else 0
    capital = hs / 100 + hs * dd * 1.5
    return {
        "firm": base["firm"], "account_size": S, "fee": base["fee"],
        "steps": base["steps"], "dd_category": base["dd_category"],
        "challenge_cost": base["challenge_cost"],
        "type_a_ev": round(ev_a, 2), "ev_c": round(ev_c, 2),
        "ev_advantage": round(ev_c - ev_a, 2),
        "total_withdrawals": round(tw, 2), "total_drag": round(td, 2),
        "expected_surplus": round(es, 2),
        "capital_required": round(capital, 2),
        "capital_efficiency": round(ev_c / capital, 4) if capital > 0 else 0,
    }


# --------------------- Futures Type A -----------------------------------------
def compute_fut_type_a(ch):
    S = ch['account_size']; fee = ch['fee']; act = ch['activation_fee']
    target = ch['profit_target']; DD = ch['max_loss']
    split = ch['profit_split']; dd_type = ch['dd_type']
    minis = ch['max_contracts_minis'] or 1; cap = ch['payout_cap']
    thr = ch['consistency_eval']; steps = ch['steps']
    if S <= 0 or DD <= 0 or target <= 0:
        return None
    N = max(math.ceil(1.0 / thr) if thr > 0 else 1, 10)
    L = fee
    for step in range(steps):
        st = target / steps; dm = st / N
        if dd_type == 'trailing':
            for _ in range(N):
                L += dm * L / DD + minis * FUT_SPREAD_CONTRACT * 2
        else:
            L += target * L / DD + minis * FUT_SPREAD_CONTRACT * 2 * N
    total_cost = L + act
    raw_payout = S * FUT_FUNDED_TARGET * split
    payout = min(raw_payout, cap) if cap > 0 else raw_payout
    EV = payout - total_cost
    capital = (minis or 1) * 1000 * 2
    return {
        'firm': ch['firm'], 'account_size': S, 'fee': round(fee, 2),
        'activation_fee': round(act, 2), 'steps': steps,
        'profit_target': round(target, 2), 'max_loss': round(DD, 2),
        'dd_type': dd_type, 'profit_split_pct': round(split * 100, 1),
        'payout_cap': round(cap, 2),
        'total_cost': round(total_cost, 2), 'funded_payout': round(payout, 2),
        'EV': round(EV, 2),
        'breakeven_pct': round((total_cost / split / S) * 100, 2) if S > 0 and split > 0 else 0,
        'capital_required': round(capital, 2),
        'capital_efficiency': round(EV / capital, 4) if capital > 0 else 0,
    }


# --------------------- Futures cost helper ------------------------------------
def _fut_cost(ch):
    S = ch['account_size']; fee = ch['fee']; act = ch['activation_fee']
    target = ch['profit_target']; DD = ch['max_loss']
    split = ch['profit_split']; dd_type = ch['dd_type']
    minis = ch['max_contracts_minis'] or 1; cap = ch['payout_cap']
    thr = ch['consistency_eval']; steps = ch['steps']
    if S <= 0 or DD <= 0 or target <= 0:
        return None
    N = max(math.ceil(1.0 / thr) if thr > 0 else 1, 10)
    L = fee
    for step in range(steps):
        st = target / steps; dm = st / N
        if dd_type == 'trailing':
            for _ in range(N):
                L += dm * L / DD + minis * FUT_SPREAD_CONTRACT * 2
        else:
            L += target * L / DD + minis * FUT_SPREAD_CONTRACT * 2 * N
    return {'firm': ch['firm'], 'account_size': S, 'fee': round(fee, 2),
            'activation_fee': round(act, 2), 'steps': steps,
            'dd_type': dd_type, 'dd_max': DD, 'split': split,
            'payout_cap': cap, 'minis': minis,
            'challenge_cost': round(L + act, 2)}


# --------------------- Futures Type B -----------------------------------------
def compute_fut_type_b(ch):
    base = _fut_cost(ch)
    if base is None:
        return None
    S, split, DD, cap = base['account_size'], base['split'], base['dd_max'], base['payout_cap']
    L = base['challenge_cost']
    tw, td = 0.0, 0.0; cum = 1.0
    for k in range(1, FUT_CYCLES + 1):
        pa = cum
        raw_w = S * FUT_WITHDRAWAL_PCT * split
        w = (min(raw_w, cap) if cap > 0 else raw_w) * pa
        d = S * FUT_HEDGE_DRAG * pa
        L += S * FUT_HEDGE_DRAG
        tw += w; td += d; cum *= FUT_SURVIVAL
    payout_a = S * FUT_FUNDED_TARGET * split
    if cap > 0: payout_a = min(payout_a, cap)
    ev_a = payout_a - base['challenge_cost']
    ev_b = tw - td
    hs = L / DD if DD > 0 else 0
    capital = hs / 100 + hs * DD * 1.5
    return {
        'firm': base['firm'], 'account_size': S, 'fee': base['fee'],
        'steps': base['steps'], 'dd_type': base['dd_type'],
        'payout_cap': round(cap, 2), 'challenge_cost': base['challenge_cost'],
        'type_a_ev': round(ev_a, 2), 'ev_b': round(ev_b, 2),
        'ev_advantage': round(ev_b - ev_a, 2),
        'total_withdrawals': round(tw, 2), 'total_drag': round(td, 2),
        'capital_required': round(capital, 2),
        'capital_efficiency': round(ev_b / capital, 4) if capital > 0 else 0,
    }


# --------------------- Futures Type C -----------------------------------------
def compute_fut_type_c(ch, surplus_pct=FUT_SURPLUS_PCT):
    base = _fut_cost(ch)
    if base is None:
        return None
    S, split, DD, cap = base['account_size'], base['split'], base['dd_max'], base['payout_cap']
    L = base['challenge_cost']; P = S * surplus_pct
    tw, td, es = 0.0, 0.0, 0.0; cum = 1.0
    for k in range(1, FUT_CYCLES + 1):
        pa = cum
        raw_w = S * FUT_WITHDRAWAL_PCT * split
        w = (min(raw_w, cap) if cap > 0 else raw_w) * pa
        dm = (L + P) / L if L > 0 else 1.0
        d = S * FUT_HEDGE_DRAG * dm * pa
        L += S * FUT_HEDGE_DRAG * dm
        pf = pa * (1 - FUT_SURVIVAL)
        es += P * pf
        tw += w; td += d; cum *= FUT_SURVIVAL
    payout_a = S * FUT_FUNDED_TARGET * split
    if cap > 0: payout_a = min(payout_a, cap)
    ev_a = payout_a - base['challenge_cost']
    ev_c = tw + es - td
    hs = (L + P) / DD if DD > 0 else 0
    capital = hs / 100 + hs * DD * 1.5
    return {
        'firm': base['firm'], 'account_size': S, 'fee': base['fee'],
        'steps': base['steps'], 'dd_type': base['dd_type'],
        'payout_cap': round(cap, 2), 'challenge_cost': base['challenge_cost'],
        'type_a_ev': round(ev_a, 2), 'ev_c': round(ev_c, 2),
        'ev_advantage': round(ev_c - ev_a, 2),
        'total_withdrawals': round(tw, 2), 'total_drag': round(td, 2),
        'expected_surplus': round(es, 2),
        'capital_required': round(capital, 2),
        'capital_efficiency': round(ev_c / capital, 4) if capital > 0 else 0,
    }


# --------------------- Instant Funded -----------------------------------------
def compute_instant(ch):
    S = ch["account_size"]; fee = ch["fee"]
    dd_ratio = ch["max_dd_ratio"]; split = ch["profit_split"]
    cr = ch["consistency_ratio"]
    eff_dd = ch["dd_type"] if ch["dd_type"] != "unspecified" else IF_ASSUME_UNSPEC
    if S <= 0 or fee <= 0 or dd_ratio <= 0 or split <= 0:
        return None
    dd_dollars = S * dd_ratio
    gross = S * IF_PAYOUT_TARGET; payout = gross * split
    min_days = math.ceil(1.0 / cr) if cr > 0 else 1
    days = max(IF_BASE_DAYS, min_days)
    daily_profit = gross / days
    L = fee; peak = 0.0
    if eff_dd == "trailing":
        for _ in range(days):
            hn = L / dd_ratio; peak = max(peak, hn)
            L += daily_profit * L / dd_dollars + hn * IF_SPREAD * 2
    else:
        hn = L / dd_ratio; peak = hn
        for _ in range(days):
            L += hn * (daily_profit / S) + hn * IF_SPREAD * 2
    EV = payout - L
    capital = (peak / IF_LEVERAGE) * 1.5 if peak > 0 else 0
    return {
        "firm": ch["firm"], "account_size": S, "fee": round(fee, 2),
        "dd_type": ch["dd_type"], "effective_dd_type": eff_dd,
        "max_dd_pct": round(dd_ratio * 100, 2),
        "profit_split_pct": round(split * 100, 1),
        "trading_days": days, "payout_timing": ch["payout_timing"],
        "funded_payout": round(payout, 2), "total_cost": round(L, 2),
        "EV": round(EV, 2),
        "breakeven_pct": round((L / split / S) * 100, 2) if S > 0 and split > 0 else 0,
        "capital_required": round(capital, 2),
        "capital_efficiency": round(EV / capital, 4) if capital > 0 else 0,
    }


# +==============================================================================+
# |  3.  DATA LOADING                                                           |
# +==============================================================================+

def latest_json(pattern):
    files = glob.glob(str(DATA_DIR / pattern))
    return max(files, key=os.path.getmtime) if files else None

def load_fx():
    f = latest_json("propmatch_challenges_*.json")
    if not f: return []
    with open(f, encoding="utf-8") as fh:
        raw = json.load(fh)
    return raw.get("challenges", raw.get("results", []))

def load_futures():
    f = latest_json("propmatch_futures_*.json")
    if not f: return []
    with open(f, encoding="utf-8") as fh:
        raw = json.load(fh)
    return raw.get("challenges", raw.get("results", []))

def load_instant():
    """Load instant-funded from the FX challenges (steps_label == 'Instant')."""
    f = latest_json("propmatch_challenges_*.json")
    if not f: return []
    with open(f, encoding="utf-8") as fh:
        raw = json.load(fh)
    all_ch = raw.get("challenges", raw.get("results", []))
    return [r for r in all_ch if str(r.get("steps_label", "")).lower() == "instant"]


# +==============================================================================+
# |  4.  RUN ALL MODELS                                                         |
# +==============================================================================+

print("Loading data...", flush=True)
fx_raw = load_fx()
# Filter out instant-funded from FX for Types A/B/C (they're separate)
fx_challenges = [c for c in fx_raw if str(c.get("steps_label", "")).lower() != "instant"]
fut_raw = load_futures()
instant_raw = load_instant()

print(f"  FX challenges: {len(fx_challenges)}")
print(f"  Futures challenges: {len(fut_raw)}")
print(f"  Instant-funded offers: {len(instant_raw)}")

# -- CFD/FX models -------------------------------------------------------------
print("Running CFD/Forex models...", flush=True)
fx_a = [r for r in (compute_fx_type_a(c) for c in fx_challenges) if r and r["EV"] > -999999]
fx_b = [r for r in (compute_fx_type_b(c) for c in fx_challenges) if r]
fx_c = [r for r in (compute_fx_type_c(c) for c in fx_challenges) if r]
df_fx_a = pd.DataFrame(fx_a).sort_values("EV", ascending=False).reset_index(drop=True)
df_fx_b = pd.DataFrame(fx_b).sort_values("ev_b", ascending=False).reset_index(drop=True)
df_fx_c = pd.DataFrame(fx_c).sort_values("ev_c", ascending=False).reset_index(drop=True)

# -- Futures models ------------------------------------------------------------
print("Running Futures models...", flush=True)
fut_parsed = [normalise_futures(c) for c in fut_raw]
fut_a = [r for r in (compute_fut_type_a(c) for c in fut_parsed) if r]
fut_b = [r for r in (compute_fut_type_b(c) for c in fut_parsed) if r]
fut_c = [r for r in (compute_fut_type_c(c) for c in fut_parsed) if r]
df_fut_a = pd.DataFrame(fut_a).sort_values("EV", ascending=False).reset_index(drop=True) if fut_a else pd.DataFrame()
df_fut_b = pd.DataFrame(fut_b).sort_values("ev_b", ascending=False).reset_index(drop=True) if fut_b else pd.DataFrame()
df_fut_c = pd.DataFrame(fut_c).sort_values("ev_c", ascending=False).reset_index(drop=True) if fut_c else pd.DataFrame()

# -- Instant-funded model ------------------------------------------------------
print("Running Instant-Funded model...", flush=True)
inst_norm = [normalise_instant(r) for r in instant_raw]
inst_res = [r for r in (compute_instant(c) for c in inst_norm) if r]
df_inst = pd.DataFrame(inst_res).sort_values("EV", ascending=False).reset_index(drop=True) if inst_res else pd.DataFrame()


# +==============================================================================+
# |  5.  CHART GENERATION                                                       |
# +==============================================================================+

COLORS = {
    "fx_a": "#1f77b4", "fx_b": "#2ca02c", "fx_c": "#9467bd",
    "fut_a": "#ff7f0e", "fut_b": "#d62728", "fut_c": "#e377c2",
    "inst": "#17becf", "pos": "#2ecc71", "neg": "#e74c3c",
}

plt.rcParams.update({
    "figure.facecolor": "white", "axes.facecolor": "#f9f9f9",
    "font.size": 9, "axes.titlesize": 11, "axes.labelsize": 9,
    "xtick.labelsize": 7, "ytick.labelsize": 8,
})

def savefig(fig, name):
    path = CHART_DIR / f"{name}.png"
    fig.savefig(path, dpi=180, bbox_inches="tight", pad_inches=0.15)
    plt.close(fig)
    return str(path)


# Chart 1: Cross-asset EV comparison box plot
def chart_ev_boxplot():
    fig, ax = plt.subplots(figsize=(10, 5))
    data, labels, colors = [], [], []
    for lbl, df, col, ev_col in [
        ("FX Type A", df_fx_a, COLORS["fx_a"], "EV"),
        ("FX Type B", df_fx_b, COLORS["fx_b"], "ev_b"),
        ("FX Type C", df_fx_c, COLORS["fx_c"], "ev_c"),
        ("Fut Type A", df_fut_a, COLORS["fut_a"], "EV"),
        ("Fut Type B", df_fut_b, COLORS["fut_b"], "ev_b"),
        ("Fut Type C", df_fut_c, COLORS["fut_c"], "ev_c"),
        ("Instant", df_inst, COLORS["inst"], "EV"),
    ]:
        if not df.empty and ev_col in df.columns:
            data.append(df[ev_col].dropna().values)
            labels.append(lbl)
            colors.append(col)
    bp = ax.boxplot(data, patch_artist=True, showfliers=True, widths=0.6,
                    flierprops=dict(marker=".", markersize=3, alpha=0.4))
    for patch, c in zip(bp["boxes"], colors):
        patch.set_facecolor(c); patch.set_alpha(0.55)
    ax.set_xticklabels(labels, rotation=25, ha="right")
    ax.axhline(0, color="grey", ls="--", lw=0.8, alpha=0.6)
    ax.set_ylabel("Expected Value ($)")
    ax.set_title("EV Distribution - All Models & Asset Classes")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))
    fig.tight_layout()
    return savefig(fig, "01_ev_boxplot")


# Chart 2: Top 20 overall opportunities (bar chart)
def chart_top20_overall():
    rows = []
    for _, r in df_fx_a.head(10).iterrows():
        rows.append({"label": f"{r['firm']} ${r['account_size']/1000:.0f}k", "EV": r["EV"], "class": "FX-A"})
    for _, r in df_fx_b.head(10).iterrows():
        rows.append({"label": f"{r['firm']} ${r['account_size']/1000:.0f}k", "EV": r["ev_b"], "class": "FX-B"})
    for _, r in df_fx_c.head(10).iterrows():
        rows.append({"label": f"{r['firm']} ${r['account_size']/1000:.0f}k", "EV": r["ev_c"], "class": "FX-C"})
    if not df_fut_a.empty:
        for _, r in df_fut_a.head(10).iterrows():
            rows.append({"label": f"{r['firm']} ${r['account_size']/1000:.0f}k", "EV": r["EV"], "class": "Fut-A"})
    if not df_fut_b.empty:
        for _, r in df_fut_b.head(10).iterrows():
            rows.append({"label": f"{r['firm']} ${r['account_size']/1000:.0f}k", "EV": r["ev_b"], "class": "Fut-B"})
    if not df_fut_c.empty:
        for _, r in df_fut_c.head(10).iterrows():
            rows.append({"label": f"{r['firm']} ${r['account_size']/1000:.0f}k", "EV": r["ev_c"], "class": "Fut-C"})
    if not df_inst.empty:
        for _, r in df_inst.head(10).iterrows():
            rows.append({"label": f"{r['firm']} ${r['account_size']/1000:.0f}k", "EV": r["EV"], "class": "Instant"})
    df_all = pd.DataFrame(rows).sort_values("EV", ascending=False).head(25)
    cmap = {"FX-A": COLORS["fx_a"], "FX-B": COLORS["fx_b"], "FX-C": COLORS["fx_c"],
            "Fut-A": COLORS["fut_a"], "Fut-B": COLORS["fut_b"], "Fut-C": COLORS["fut_c"],
            "Instant": COLORS["inst"]}
    fig, ax = plt.subplots(figsize=(10, 7))
    bars = ax.barh(range(len(df_all)), df_all["EV"].values, color=[cmap.get(c, "#888") for c in df_all["class"]])
    ax.set_yticks(range(len(df_all)))
    ax.set_yticklabels(df_all["label"].values, fontsize=7)
    ax.invert_yaxis()
    ax.set_xlabel("Expected Value ($)")
    ax.set_title("Top 25 Opportunities Across All Models")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))
    # Legend
    from matplotlib.patches import Patch
    handles = [Patch(color=cmap[k], label=k) for k in cmap if any(df_all["class"] == k)]
    ax.legend(handles=handles, loc="lower right", fontsize=7)
    fig.tight_layout()
    return savefig(fig, "02_top25_overall")


# Chart 3: EV by account size (per asset class)
def chart_ev_by_size():
    fig, axes = plt.subplots(1, 3, figsize=(14, 5), sharey=False)
    # FX
    if not df_fx_a.empty:
        grp = df_fx_a.groupby("account_size")["EV"].agg(["mean", "count"]).reset_index()
        axes[0].bar(grp["account_size"].astype(str), grp["mean"], color=COLORS["fx_a"], alpha=0.7)
        axes[0].set_title("CFD/Forex - Avg EV by Size")
        axes[0].tick_params(axis='x', rotation=45)
    # Futures
    if not df_fut_a.empty:
        grp = df_fut_a.groupby("account_size")["EV"].agg(["mean", "count"]).reset_index()
        axes[1].bar(grp["account_size"].astype(str), grp["mean"], color=COLORS["fut_a"], alpha=0.7)
        axes[1].set_title("Futures - Avg EV by Size")
        axes[1].tick_params(axis='x', rotation=45)
    # Instant
    if not df_inst.empty:
        grp = df_inst.groupby("account_size")["EV"].agg(["mean", "count"]).reset_index()
        axes[2].bar(grp["account_size"].astype(str), grp["mean"], color=COLORS["inst"], alpha=0.7)
        axes[2].set_title("Instant Funded - Avg EV by Size")
        axes[2].tick_params(axis='x', rotation=45)
    for ax in axes:
        ax.axhline(0, color="grey", ls="--", lw=0.7)
        ax.set_xlabel("Account Size ($)")
        ax.set_ylabel("Avg EV ($)")
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))
    fig.suptitle("Average EV by Account Size per Asset Class", fontsize=12, y=1.02)
    fig.tight_layout()
    return savefig(fig, "03_ev_by_size")


# Chart 4: Capital Efficiency scatter
def chart_capital_efficiency():
    fig, ax = plt.subplots(figsize=(10, 6))
    for lbl, df, col, ev_col in [
        ("FX-A", df_fx_a, COLORS["fx_a"], "EV"),
        ("Fut-A", df_fut_a, COLORS["fut_a"], "EV"),
        ("Instant", df_inst, COLORS["inst"], "EV"),
    ]:
        if not df.empty and ev_col in df.columns and "capital_required" in df.columns:
            pos = df[df[ev_col] > 0]
            ax.scatter(pos["capital_required"], pos[ev_col], alpha=0.5,
                       s=pos["account_size"] / 1000, label=lbl, color=col, edgecolors="white", linewidth=0.3)
    ax.set_xlabel("Capital Required ($)")
    ax.set_ylabel("Expected Value ($)")
    ax.set_title("Capital Efficiency - EV vs Capital (bubble = account size)")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))
    ax.legend(fontsize=8)
    fig.tight_layout()
    return savefig(fig, "04_capital_efficiency")


# Chart 5: Type A vs B vs C EV comparison (FX)
def chart_fx_abc():
    if df_fx_a.empty:
        return None
    merged = df_fx_a[["firm", "account_size", "EV"]].rename(columns={"EV": "EV_A"})
    if not df_fx_b.empty:
        merged = merged.merge(df_fx_b[["firm", "account_size", "ev_b"]].rename(columns={"ev_b": "EV_B"}),
                              on=["firm", "account_size"], how="left")
    if not df_fx_c.empty:
        merged = merged.merge(df_fx_c[["firm", "account_size", "ev_c"]].rename(columns={"ev_c": "EV_C"}),
                              on=["firm", "account_size"], how="left")
    top = merged.sort_values("EV_A", ascending=False).head(20)
    fig, ax = plt.subplots(figsize=(10, 7))
    y = np.arange(len(top))
    w = 0.25
    ax.barh(y - w, top["EV_A"], w, label="Type A", color=COLORS["fx_a"], alpha=0.8)
    if "EV_B" in top.columns:
        ax.barh(y, top["EV_B"], w, label="Type B", color=COLORS["fx_b"], alpha=0.8)
    if "EV_C" in top.columns:
        ax.barh(y + w, top["EV_C"], w, label="Type C", color=COLORS["fx_c"], alpha=0.8)
    ax.set_yticks(y)
    labels = [f"{r['firm']} ${r['account_size']/1000:.0f}k" for _, r in top.iterrows()]
    ax.set_yticklabels(labels, fontsize=7)
    ax.invert_yaxis()
    ax.set_xlabel("EV ($)")
    ax.set_title("CFD/Forex - Type A vs B vs C (Top 20)")
    ax.legend(fontsize=8)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))
    fig.tight_layout()
    return savefig(fig, "05_fx_abc_comparison")


# Chart 6: Futures Type A vs B vs C
def chart_fut_abc():
    if df_fut_a.empty:
        return None
    merged = df_fut_a[["firm", "account_size", "EV"]].rename(columns={"EV": "EV_A"})
    if not df_fut_b.empty:
        merged = merged.merge(df_fut_b[["firm", "account_size", "ev_b"]].rename(columns={"ev_b": "EV_B"}),
                              on=["firm", "account_size"], how="left")
    if not df_fut_c.empty:
        merged = merged.merge(df_fut_c[["firm", "account_size", "ev_c"]].rename(columns={"ev_c": "EV_C"}),
                              on=["firm", "account_size"], how="left")
    top = merged.sort_values("EV_A", ascending=False).head(20)
    fig, ax = plt.subplots(figsize=(10, 7))
    y = np.arange(len(top))
    w = 0.25
    ax.barh(y - w, top["EV_A"], w, label="Type A", color=COLORS["fut_a"], alpha=0.8)
    if "EV_B" in top.columns:
        ax.barh(y, top["EV_B"], w, label="Type B", color=COLORS["fut_b"], alpha=0.8)
    if "EV_C" in top.columns:
        ax.barh(y + w, top["EV_C"], w, label="Type C", color=COLORS["fut_c"], alpha=0.8)
    ax.set_yticks(y)
    labels = [f"{r['firm']} ${r['account_size']/1000:.0f}k" for _, r in top.iterrows()]
    ax.set_yticklabels(labels, fontsize=7)
    ax.invert_yaxis()
    ax.set_xlabel("EV ($)")
    ax.set_title("Futures - Type A vs B vs C (Top 20)")
    ax.legend(fontsize=8)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))
    fig.tight_layout()
    return savefig(fig, "06_fut_abc_comparison")


# Chart 7: Firm leaderboard heatmap
def chart_firm_heatmap():
    # Collect best EV per firm across all models
    firm_evs = {}
    for lbl, df, ev_col in [
        ("FX-A", df_fx_a, "EV"), ("FX-B", df_fx_b, "ev_b"), ("FX-C", df_fx_c, "ev_c"),
        ("Fut-A", df_fut_a, "EV"), ("Fut-B", df_fut_b, "ev_b"), ("Fut-C", df_fut_c, "ev_c"),
        ("Instant", df_inst, "EV"),
    ]:
        if not df.empty and ev_col in df.columns:
            best = df.groupby("firm")[ev_col].max()
            for firm, ev in best.items():
                if firm not in firm_evs:
                    firm_evs[firm] = {}
                firm_evs[firm][lbl] = ev
    if not firm_evs:
        return None
    hm_df = pd.DataFrame(firm_evs).T.fillna(0)
    # Sort by total EV
    hm_df["_total"] = hm_df.sum(axis=1)
    hm_df = hm_df.sort_values("_total", ascending=False).head(20).drop(columns=["_total"])
    fig, ax = plt.subplots(figsize=(10, 8))
    im = ax.imshow(hm_df.values, aspect="auto", cmap="RdYlGn")
    ax.set_xticks(range(len(hm_df.columns)))
    ax.set_xticklabels(hm_df.columns, rotation=30, ha="right", fontsize=8)
    ax.set_yticks(range(len(hm_df.index)))
    ax.set_yticklabels(hm_df.index, fontsize=8)
    for i in range(len(hm_df.index)):
        for j in range(len(hm_df.columns)):
            v = hm_df.values[i, j]
            ax.text(j, i, f"${v:,.0f}" if abs(v) >= 1 else "-",
                    ha="center", va="center", fontsize=6,
                    color="white" if v < hm_df.values.mean() else "black")
    fig.colorbar(im, ax=ax, label="Best EV ($)", shrink=0.7)
    ax.set_title("Firm Leaderboard - Best EV per Model (Top 20 Firms)")
    fig.tight_layout()
    return savefig(fig, "07_firm_heatmap")


# Chart 8: Positive EV rates
def chart_pos_ev_rates():
    rates = {}
    for lbl, df, ev_col in [
        ("FX Type A", df_fx_a, "EV"), ("FX Type B", df_fx_b, "ev_b"), ("FX Type C", df_fx_c, "ev_c"),
        ("Fut Type A", df_fut_a, "EV"), ("Fut Type B", df_fut_b, "ev_b"), ("Fut Type C", df_fut_c, "ev_c"),
        ("Instant", df_inst, "EV"),
    ]:
        if not df.empty and ev_col in df.columns:
            total = len(df)
            pos = (df[ev_col] > 0).sum()
            rates[lbl] = (pos / total * 100) if total > 0 else 0
    fig, ax = plt.subplots(figsize=(9, 5))
    labels = list(rates.keys())
    vals = list(rates.values())
    colors = [COLORS["fx_a"], COLORS["fx_b"], COLORS["fx_c"],
              COLORS["fut_a"], COLORS["fut_b"], COLORS["fut_c"],
              COLORS["inst"]][:len(labels)]
    ax.bar(labels, vals, color=colors, alpha=0.8, edgecolor="white")
    ax.set_ylabel("% of Challenges with Positive EV")
    ax.set_title("Positive EV Rate by Model")
    ax.set_ylim(0, 105)
    for i, v in enumerate(vals):
        ax.text(i, v + 1.5, f"{v:.1f}%", ha="center", fontsize=8, fontweight="bold")
    ax.tick_params(axis='x', rotation=25)
    fig.tight_layout()
    return savefig(fig, "08_pos_ev_rates")


# Chart 9: EV histogram overlay
def chart_ev_histograms():
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.5))
    # FX
    if not df_fx_a.empty:
        axes[0].hist(df_fx_a["EV"], bins=30, alpha=0.6, color=COLORS["fx_a"], label="Type A")
    if not df_fx_b.empty:
        axes[0].hist(df_fx_b["ev_b"], bins=30, alpha=0.6, color=COLORS["fx_b"], label="Type B")
    if not df_fx_c.empty:
        axes[0].hist(df_fx_c["ev_c"], bins=30, alpha=0.6, color=COLORS["fx_c"], label="Type C")
    axes[0].set_title("CFD/Forex EV Distribution")
    axes[0].legend(fontsize=7)
    axes[0].axvline(0, color="red", ls="--", lw=0.8)
    # Futures
    if not df_fut_a.empty:
        axes[1].hist(df_fut_a["EV"], bins=20, alpha=0.6, color=COLORS["fut_a"], label="Type A")
    if not df_fut_b.empty:
        axes[1].hist(df_fut_b["ev_b"], bins=20, alpha=0.6, color=COLORS["fut_b"], label="Type B")
    if not df_fut_c.empty:
        axes[1].hist(df_fut_c["ev_c"], bins=20, alpha=0.6, color=COLORS["fut_c"], label="Type C")
    axes[1].set_title("Futures EV Distribution")
    axes[1].legend(fontsize=7)
    axes[1].axvline(0, color="red", ls="--", lw=0.8)
    # Instant
    if not df_inst.empty:
        axes[2].hist(df_inst["EV"], bins=20, alpha=0.6, color=COLORS["inst"])
    axes[2].set_title("Instant Funded EV Distribution")
    axes[2].axvline(0, color="red", ls="--", lw=0.8)
    for ax in axes:
        ax.set_xlabel("EV ($)"); ax.set_ylabel("Count")
    fig.suptitle("EV Distributions Across All Models", fontsize=12, y=1.01)
    fig.tight_layout()
    return savefig(fig, "09_ev_histograms")


# Chart 10: Fee vs EV scatter
def chart_fee_vs_ev():
    fig, ax = plt.subplots(figsize=(10, 6))
    for lbl, df, col, ev_col in [
        ("FX", df_fx_a, COLORS["fx_a"], "EV"),
        ("Futures", df_fut_a, COLORS["fut_a"], "EV"),
        ("Instant", df_inst, COLORS["inst"], "EV"),
    ]:
        if not df.empty and ev_col in df.columns and "fee" in df.columns:
            ax.scatter(df["fee"], df[ev_col], alpha=0.45, s=30, label=lbl, color=col)
    ax.axhline(0, color="grey", ls="--", lw=0.7)
    ax.set_xlabel("Challenge Fee ($)")
    ax.set_ylabel("EV ($)")
    ax.set_title("Fee vs Expected Value - Type A Models")
    ax.legend(fontsize=8)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))
    fig.tight_layout()
    return savefig(fig, "10_fee_vs_ev")


# Chart 11: Drawdown type comparison
def chart_dd_type():
    fig, axes = plt.subplots(1, 2, figsize=(11, 5))
    if not df_fx_a.empty and "dd_category" in df_fx_a.columns:
        grp = df_fx_a.groupby("dd_category")["EV"].agg(["mean", "median", "count"])
        grp.plot(kind="bar", y=["mean", "median"], ax=axes[0], color=[COLORS["fx_a"], COLORS["fx_b"]])
        axes[0].set_title("FX: EV by Drawdown Type")
        axes[0].set_ylabel("EV ($)")
        for i, (idx, row) in enumerate(grp.iterrows()):
            axes[0].text(i, row["mean"] + 5, f"n={int(row['count'])}", ha="center", fontsize=7)
    if not df_fut_a.empty and "dd_type" in df_fut_a.columns:
        grp = df_fut_a.groupby("dd_type")["EV"].agg(["mean", "median", "count"])
        grp.plot(kind="bar", y=["mean", "median"], ax=axes[1], color=[COLORS["fut_a"], COLORS["fut_b"]])
        axes[1].set_title("Futures: EV by Drawdown Type")
        axes[1].set_ylabel("EV ($)")
        for i, (idx, row) in enumerate(grp.iterrows()):
            axes[1].text(i, row["mean"] + 5, f"n={int(row['count'])}", ha="center", fontsize=7)
    for ax in axes:
        ax.tick_params(axis='x', rotation=0)
    fig.suptitle("Impact of Drawdown Type on EV", fontsize=12, y=1.01)
    fig.tight_layout()
    return savefig(fig, "11_dd_type_comparison")


# Chart 12: Profit split analysis
def chart_profit_split():
    fig, ax = plt.subplots(figsize=(9, 5))
    for lbl, df, col, ev_col, split_col in [
        ("FX", df_fx_a, COLORS["fx_a"], "EV", "profit_split_pct"),
        ("Futures", df_fut_a, COLORS["fut_a"], "EV", "profit_split_pct"),
        ("Instant", df_inst, COLORS["inst"], "EV", "profit_split_pct"),
    ]:
        if not df.empty and ev_col in df.columns and split_col in df.columns:
            ax.scatter(df[split_col], df[ev_col], alpha=0.4, s=25, label=lbl, color=col)
    ax.set_xlabel("Profit Split (%)")
    ax.set_ylabel("EV ($)")
    ax.set_title("Profit Split vs EV")
    ax.legend(fontsize=8)
    ax.axhline(0, color="grey", ls="--", lw=0.7)
    fig.tight_layout()
    return savefig(fig, "12_profit_split")


print("Generating charts...", flush=True)
chart_paths = []
for fn in [chart_ev_boxplot, chart_top20_overall, chart_ev_by_size,
           chart_capital_efficiency, chart_fx_abc, chart_fut_abc,
           chart_firm_heatmap, chart_pos_ev_rates, chart_ev_histograms,
           chart_fee_vs_ev, chart_dd_type, chart_profit_split]:
    result = fn()
    if result:
        chart_paths.append(result)
        print(f"  [ok] {Path(result).stem}")


# +==============================================================================+
# |  6.  PDF REPORT GENERATION                                                  |
# +==============================================================================+

class HedgePDF(FPDF):
    def __init__(self):
        super().__init__(orientation="P", unit="mm", format="letter")
        self.set_auto_page_break(auto=True, margin=20)
        self.set_margins(15, 15, 15)

    def header(self):
        if self.page_no() > 1:
            self.set_font("Helvetica", "I", 7)
            self.set_text_color(120, 120, 120)
            self.cell(0, 5, "Hedge Edge - Consolidated Prop-Firm Analysis", align="L")
            self.cell(0, 5, f"Page {self.page_no()}", align="R", new_x="LMARGIN", new_y="NEXT")
            self.line(15, self.get_y(), 197, self.get_y())
            self.ln(3)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(150, 150, 150)
        self.cell(0, 5, f"Generated {datetime.now():%Y-%m-%d %H:%M} | Hedge Edge Proprietary", align="C")

    def section_title(self, title, level=1):
        if level == 1:
            self.set_font("Helvetica", "B", 16)
            self.set_text_color(30, 60, 120)
        elif level == 2:
            self.set_font("Helvetica", "B", 13)
            self.set_text_color(40, 80, 140)
        else:
            self.set_font("Helvetica", "B", 11)
            self.set_text_color(60, 60, 60)
        self.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT")
        if level <= 2:
            self.set_draw_color(30, 60, 120)
            self.set_line_width(0.5 if level == 1 else 0.3)
            self.line(15, self.get_y(), 197, self.get_y())
        self.ln(4)

    def body_text(self, text):
        self.set_font("Helvetica", "", 9)
        self.set_text_color(30, 30, 30)
        self.multi_cell(0, 4.5, text)
        self.ln(2)

    def add_chart(self, path, w=180):
        if self.get_y() + 90 > 260:
            self.add_page()
        self.image(path, x=(self.w - w) / 2, w=w)
        self.ln(5)

    def add_table(self, df, columns, col_widths=None, title=None, max_rows=20):
        if df.empty:
            return
        if title:
            self.section_title(title, level=3)
        top = df.head(max_rows)
        n_cols = len(columns)
        if col_widths is None:
            avail = self.w - 30
            col_widths = [avail / n_cols] * n_cols
        # Check if table fits on page
        needed = 6 + len(top) * 5 + 5
        if self.get_y() + needed > 260:
            self.add_page()
        # Header
        self.set_font("Helvetica", "B", 7)
        self.set_fill_color(30, 60, 120)
        self.set_text_color(255, 255, 255)
        for i, col in enumerate(columns):
            display = col.replace("_", " ").title()[:15]
            self.cell(col_widths[i], 6, display, border=1, fill=True, align="C")
        self.ln()
        # Rows
        self.set_font("Helvetica", "", 7)
        self.set_text_color(30, 30, 30)
        for row_idx, (_, row) in enumerate(top.iterrows()):
            if row_idx % 2 == 0:
                self.set_fill_color(240, 244, 255)
            else:
                self.set_fill_color(255, 255, 255)
            for i, col in enumerate(columns):
                val = row.get(col, "")
                if isinstance(val, float):
                    if abs(val) >= 100:
                        text = f"${val:,.0f}"
                    elif abs(val) >= 1:
                        text = f"{val:.2f}"
                    else:
                        text = f"{val:.4f}"
                else:
                    text = str(val)[:18]
                self.cell(col_widths[i], 5, text, border=1, fill=True, align="C")
            self.ln()
        self.ln(3)

    def stat_card(self, label, value, unit=""):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(30, 60, 120)
        self.cell(45, 6, label + ":", align="R")
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(0, 0, 0)
        self.cell(50, 6, f"  {value}{unit}", align="L", new_x="LMARGIN", new_y="NEXT")


print("Building PDF...", flush=True)
pdf = HedgePDF()

# -- COVER PAGE ----------------------------------------------------------------
pdf.add_page()
pdf.ln(50)
pdf.set_font("Helvetica", "B", 28)
pdf.set_text_color(30, 60, 120)
pdf.cell(0, 15, "Hedge Edge", align="C", new_x="LMARGIN", new_y="NEXT")
pdf.set_font("Helvetica", "", 16)
pdf.set_text_color(80, 80, 80)
pdf.cell(0, 10, "Consolidated Prop-Firm Hedge Model Report", align="C", new_x="LMARGIN", new_y="NEXT")
pdf.ln(10)
pdf.set_draw_color(30, 60, 120)
pdf.set_line_width(1)
pdf.line(60, pdf.get_y(), 152, pdf.get_y())
pdf.ln(10)
pdf.set_font("Helvetica", "", 11)
pdf.set_text_color(60, 60, 60)
pdf.cell(0, 8, f"Generated: {datetime.now():%B %d, %Y at %H:%M}", align="C", new_x="LMARGIN", new_y="NEXT")
pdf.cell(0, 8, f"Data Sources: PropFirmMatch.com", align="C", new_x="LMARGIN", new_y="NEXT")
pdf.ln(5)
# Stats summary
pdf.set_font("Helvetica", "", 10)
lines = [
    f"CFD/Forex Challenges Analyzed: {len(fx_challenges)}",
    f"Futures Challenges Analyzed: {len(fut_raw)}",
    f"Instant-Funded Offers Analyzed: {len(instant_raw)}",
    f"Total Models Run: 7 (3 FX + 3 Futures + 1 Instant)",
    f"Total Opportunities Scored: {len(fx_a) + len(fx_b) + len(fx_c) + len(fut_a) + len(fut_b) + len(fut_c) + len(inst_res)}",
]
for line in lines:
    pdf.cell(0, 7, line, align="C", new_x="LMARGIN", new_y="NEXT")

# -- TABLE OF CONTENTS --------------------------------------------------------
pdf.add_page()
pdf.section_title("Table of Contents", level=1)
toc = [
    "1. Executive Summary",
    "2. Cross-Asset Overview",
    "    2.1. EV Distribution (All Models)",
    "    2.2. Top 25 Overall Opportunities",
    "    2.3. Positive EV Rates",
    "    2.4. Firm Leaderboard Heatmap",
    "3. CFD/Forex Deep Dive",
    "    3.1. Type A - Challenge Insurance",
    "    3.2. Type B - Funded Recovery",
    "    3.3. Type C - Funded Surplus",
    "    3.4. A vs B vs C Comparison",
    "4. Futures Deep Dive",
    "    4.1. Type A - Challenge Insurance",
    "    4.2. Type B - Funded Recovery",
    "    4.3. Type C - Funded Surplus",
    "    4.4. A vs B vs C Comparison",
    "5. Instant-Funded Deep Dive",
    "6. Statistical Analysis",
    "    6.1. EV by Account Size",
    "    6.2. Fee vs EV Relationship",
    "    6.3. Drawdown Type Impact",
    "    6.4. Profit Split Analysis",
    "    6.5. Capital Efficiency",
    "7. Key Findings & Recommendations",
    "Appendix A: Methodology",
    "Appendix B: Parameter Summary",
]
pdf.set_font("Helvetica", "", 10)
for item in toc:
    pdf.cell(0, 6, item, new_x="LMARGIN", new_y="NEXT")

# -- 1. EXECUTIVE SUMMARY -----------------------------------------------------
pdf.add_page()
pdf.section_title("1. Executive Summary", level=1)

# Calculate summary stats
def safe_stat(df, col, func="mean"):
    if df.empty or col not in df.columns: return 0
    s = df[col].dropna()
    if func == "mean": return s.mean()
    if func == "median": return s.median()
    if func == "max": return s.max()
    if func == "count_pos": return (s > 0).sum()
    return 0

total_opps = len(fx_a) + len(fx_b) + len(fx_c) + len(fut_a) + len(fut_b) + len(fut_c) + len(inst_res)
total_pos = (
    safe_stat(df_fx_a, "EV", "count_pos") + safe_stat(df_fx_b, "ev_b", "count_pos") +
    safe_stat(df_fx_c, "ev_c", "count_pos") + safe_stat(df_fut_a, "EV", "count_pos") +
    safe_stat(df_fut_b, "ev_b", "count_pos") + safe_stat(df_fut_c, "ev_c", "count_pos") +
    safe_stat(df_inst, "EV", "count_pos")
)

pdf.body_text(
    "This report consolidates the complete Hedge Edge prop-firm analysis across three asset classes "
    "(CFD/Forex, Futures, Instant-Funded) and seven hedge model variants (Type A/B/C for FX and Futures, "
    "plus Instant-Funded first-payout model). Each model applies a deterministic hedging strategy to "
    "evaluate the expected value (EV) of participating in prop-firm challenges."
)

pdf.ln(2)
pdf.stat_card("Total Opportunities Scored", f"{total_opps:,}")
pdf.stat_card("Positive EV Opportunities", f"{int(total_pos):,}")
pdf.stat_card("Positive EV Rate", f"{total_pos/total_opps*100:.1f}", "%")
pdf.stat_card("Best FX EV (Type A)", f"${safe_stat(df_fx_a, 'EV', 'max'):,.2f}")
pdf.stat_card("Best FX EV (Type B)", f"${safe_stat(df_fx_b, 'ev_b', 'max'):,.2f}")
pdf.stat_card("Best FX EV (Type C)", f"${safe_stat(df_fx_c, 'ev_c', 'max'):,.2f}")
pdf.stat_card("Best Futures EV (Type A)", f"${safe_stat(df_fut_a, 'EV', 'max'):,.2f}")
pdf.stat_card("Best Futures EV (Type B)", f"${safe_stat(df_fut_b, 'ev_b', 'max'):,.2f}")
pdf.stat_card("Best Futures EV (Type C)", f"${safe_stat(df_fut_c, 'ev_c', 'max'):,.2f}")
pdf.stat_card("Best Instant EV", f"${safe_stat(df_inst, 'EV', 'max'):,.2f}")
pdf.ln(5)

pdf.body_text(
    "Key Insight: Funded-continuation models (Type B/C) consistently outperform challenge-only "
    "(Type A) models because the hedge recovers historical cost stacks upon funded-account failure. "
    "Type C adds a surplus buffer that generates additional recovery on failure, at the cost of "
    "proportionally higher hedge drag. Optimal model depends on risk tolerance and capital availability."
)

# -- 2. CROSS-ASSET OVERVIEW --------------------------------------------------
pdf.add_page()
pdf.section_title("2. Cross-Asset Overview", level=1)

pdf.section_title("2.1 EV Distribution - All Models", level=2)
pdf.body_text(
    "The box plot below shows the EV distribution across all seven model variants. "
    "This reveals the spread, central tendency, and outlier characteristics of each model. "
    "Models with higher medians and tighter distributions offer more consistent profitability."
)
if os.path.exists(str(CHART_DIR / "01_ev_boxplot.png")):
    pdf.add_chart(str(CHART_DIR / "01_ev_boxplot.png"))

pdf.add_page()
pdf.section_title("2.2 Top 25 Overall Opportunities", level=2)
pdf.body_text(
    "The following chart ranks the top 25 individual challenge opportunities across all "
    "models and asset classes by EV. Color coding indicates the model type."
)
if os.path.exists(str(CHART_DIR / "02_top25_overall.png")):
    pdf.add_chart(str(CHART_DIR / "02_top25_overall.png"))

# Top 25 table
all_ranked = []
for lbl, df, ev_col in [
    ("FX-A", df_fx_a, "EV"), ("FX-B", df_fx_b, "ev_b"), ("FX-C", df_fx_c, "ev_c"),
    ("Fut-A", df_fut_a, "EV"), ("Fut-B", df_fut_b, "ev_b"), ("Fut-C", df_fut_c, "ev_c"),
    ("Instant", df_inst, "EV"),
]:
    if not df.empty and ev_col in df.columns:
        for _, r in df.head(5).iterrows():
            all_ranked.append({"Model": lbl, "Firm": r.get("firm", "?"),
                               "Size": r.get("account_size", 0), "EV": r[ev_col],
                               "Fee": r.get("fee", 0)})
df_ranked = pd.DataFrame(all_ranked).sort_values("EV", ascending=False).head(25)
pdf.add_table(df_ranked, ["Model", "Firm", "Size", "Fee", "EV"],
              col_widths=[18, 35, 25, 25, 25], title="Top 25 Scored Opportunities", max_rows=25)

pdf.add_page()
pdf.section_title("2.3 Positive EV Rates by Model", level=2)
pdf.body_text(
    "Not every challenge has positive expected value under the hedge model. "
    "The chart below shows what percentage of challenges in each model produce positive EV, "
    "indicating the selectivity required."
)
if os.path.exists(str(CHART_DIR / "08_pos_ev_rates.png")):
    pdf.add_chart(str(CHART_DIR / "08_pos_ev_rates.png"))

pdf.section_title("2.4 Firm Leaderboard Heatmap", level=2)
pdf.body_text(
    "This heatmap shows the best EV achieved by each firm across all seven models. "
    "Green indicates strong positive EV; red indicates negative or zero. "
    "Firms that appear green across multiple columns offer diversified profitability."
)
if os.path.exists(str(CHART_DIR / "07_firm_heatmap.png")):
    pdf.add_chart(str(CHART_DIR / "07_firm_heatmap.png"))

# -- 3. CFD/FOREX DEEP DIVE ---------------------------------------------------
pdf.add_page()
pdf.section_title("3. CFD/Forex Deep Dive", level=1)
pdf.body_text(
    f"The CFD/Forex dataset contains {len(fx_challenges)} challenges from PropFirmMatch. "
    "These are traditional FX prop-firm challenges where profit targets and drawdowns are expressed "
    "as percentages of account size. The hedge uses leveraged FX positions with a 3-pip spread model."
)

pdf.section_title("3.1 Type A - Challenge Insurance", level=2)
pdf.body_text(
    "Type A is a challenge-only hedge. The trader opens a hedge position that grows in proportion "
    "to the challenge cost (insured base). If the challenge fails, the hedge profits, recovering the fee. "
    "EV = funded_payout - total_cost. Parameters: 8% funded target, 3-pip spread, 20 daily resizes for trailing."
)
fx_a_cols = ["firm", "account_size", "fee", "dd_category", "total_cost", "funded_payout", "EV", "capital_efficiency"]
fx_a_widths = [28, 20, 18, 18, 22, 22, 22, 22]
pdf.add_table(df_fx_a, fx_a_cols, fx_a_widths, "Top 20 - FX Type A Rankings")

# Summary stats
if not df_fx_a.empty:
    pdf.body_text(
        f"FX Type A Summary: {len(df_fx_a)} challenges scored | "
        f"Positive EV: {(df_fx_a['EV'] > 0).sum()} ({(df_fx_a['EV'] > 0).mean()*100:.1f}%) | "
        f"Mean EV: ${df_fx_a['EV'].mean():,.2f} | Median EV: ${df_fx_a['EV'].median():,.2f} | "
        f"Max EV: ${df_fx_a['EV'].max():,.2f} | Std Dev: ${df_fx_a['EV'].std():,.2f}"
    )

pdf.add_page()
pdf.section_title("3.2 Type B - Funded Recovery", level=2)
pdf.body_text(
    "Type B extends the hedge into the funded phase. After passing the challenge, the hedge continues "
    "to run during funded trading. If the funded account fails, the hedge recovers the accumulated cost stack. "
    "Meanwhile, each cycle the trader withdraws profits. EV_B = total_withdrawals - total_drag. "
    "Parameters: 4% withdrawal/cycle, 6 cycles, 80% survival rate, 1.5% hedge drag."
)
fx_b_cols = ["firm", "account_size", "fee", "type_a_ev", "ev_b", "ev_advantage", "capital_efficiency"]
fx_b_widths = [28, 22, 18, 22, 22, 22, 22]
pdf.add_table(df_fx_b, fx_b_cols, fx_b_widths, "Top 20 - FX Type B Rankings")

if not df_fx_b.empty:
    pdf.body_text(
        f"FX Type B Summary: {len(df_fx_b)} challenges scored | "
        f"Positive EV: {(df_fx_b['ev_b'] > 0).sum()} ({(df_fx_b['ev_b'] > 0).mean()*100:.1f}%) | "
        f"Mean EV: ${df_fx_b['ev_b'].mean():,.2f} | Median EV: ${df_fx_b['ev_b'].median():,.2f} | "
        f"Mean Advantage vs A: ${df_fx_b['ev_advantage'].mean():,.2f}"
    )

pdf.add_page()
pdf.section_title("3.3 Type C - Funded Surplus", level=2)
pdf.body_text(
    "Type C adds a surplus buffer (2% of account size) that the hedge also covers. On funded-account "
    "failure, the hedge recovers the cost stack PLUS the surplus. This increases drag proportionally "
    "but provides additional income on failure. EV_C = withdrawals + expected_surplus - drag."
)
fx_c_cols = ["firm", "account_size", "fee", "type_a_ev", "ev_c", "ev_advantage", "expected_surplus", "capital_efficiency"]
fx_c_widths = [25, 18, 16, 20, 20, 20, 20, 20]
pdf.add_table(df_fx_c, fx_c_cols, fx_c_widths, "Top 20 - FX Type C Rankings")

if not df_fx_c.empty:
    pdf.body_text(
        f"FX Type C Summary: {len(df_fx_c)} challenges scored | "
        f"Positive EV: {(df_fx_c['ev_c'] > 0).sum()} ({(df_fx_c['ev_c'] > 0).mean()*100:.1f}%) | "
        f"Mean EV: ${df_fx_c['ev_c'].mean():,.2f} | "
        f"Mean Surplus Recovery: ${df_fx_c['expected_surplus'].mean():,.2f}"
    )

pdf.section_title("3.4 CFD/Forex - A vs B vs C Comparison", level=2)
pdf.body_text(
    "The grouped bar chart below compares the EV of all three model types for the top 20 FX challenges. "
    "Type B consistently outperforms Type A as funded withdrawals exceed hedge drag. "
    "Type C provides marginal improvement over B via surplus recovery."
)
if os.path.exists(str(CHART_DIR / "05_fx_abc_comparison.png")):
    pdf.add_chart(str(CHART_DIR / "05_fx_abc_comparison.png"))

# -- 4. FUTURES DEEP DIVE -----------------------------------------------------
pdf.add_page()
pdf.section_title("4. Futures Deep Dive", level=1)
pdf.body_text(
    f"The Futures dataset contains {len(fut_raw)} challenges across account sizes from $25K to $300K. "
    "Futures challenges differ from FX: profit targets and drawdowns are in dollar amounts, spread is "
    "fixed per contract ($5/RT), and payout caps are common. Consistency rules often apply."
)

pdf.section_title("4.1 Type A - Futures Challenge Insurance", level=2)
pdf.body_text(
    "The futures Type A model accounts for per-contract spread costs, trailing/static drawdown mechanics, "
    "consistency-rule-driven trading days, and payout caps. Parameters: 6% funded target, $5/contract spread."
)
if not df_fut_a.empty:
    fut_a_cols = ["firm", "account_size", "fee", "dd_type", "payout_cap", "total_cost", "EV", "capital_efficiency"]
    fut_a_widths = [25, 20, 16, 18, 18, 20, 20, 20]
    pdf.add_table(df_fut_a, fut_a_cols, fut_a_widths, "Top 20 - Futures Type A Rankings")
    pdf.body_text(
        f"Futures Type A Summary: {len(df_fut_a)} challenges scored | "
        f"Positive EV: {(df_fut_a['EV'] > 0).sum()} ({(df_fut_a['EV'] > 0).mean()*100:.1f}%) | "
        f"Mean EV: ${df_fut_a['EV'].mean():,.2f} | Max EV: ${df_fut_a['EV'].max():,.2f}"
    )

pdf.add_page()
pdf.section_title("4.2 Type B - Futures Recovery", level=2)
pdf.body_text(
    "Futures Type B extends the hedge into the funded phase with the same recovery mechanics as FX Type B, "
    "but respects payout caps on withdrawals."
)
if not df_fut_b.empty:
    fut_b_cols = ["firm", "account_size", "fee", "payout_cap", "type_a_ev", "ev_b", "ev_advantage"]
    fut_b_widths = [28, 22, 18, 20, 22, 22, 22]
    pdf.add_table(df_fut_b, fut_b_cols, fut_b_widths, "Top 20 - Futures Type B Rankings")
    pdf.body_text(
        f"Futures Type B Summary: {len(df_fut_b)} scored | "
        f"Positive EV: {(df_fut_b['ev_b'] > 0).sum()} ({(df_fut_b['ev_b'] > 0).mean()*100:.1f}%) | "
        f"Mean EV: ${df_fut_b['ev_b'].mean():,.2f}"
    )

pdf.section_title("4.3 Type C - Futures Surplus", level=2)
if not df_fut_c.empty:
    fut_c_cols = ["firm", "account_size", "fee", "type_a_ev", "ev_c", "ev_advantage", "expected_surplus"]
    fut_c_widths = [28, 22, 18, 22, 22, 22, 22]
    pdf.add_table(df_fut_c, fut_c_cols, fut_c_widths, "Top 20 - Futures Type C Rankings")
    pdf.body_text(
        f"Futures Type C Summary: {len(df_fut_c)} scored | "
        f"Positive EV: {(df_fut_c['ev_c'] > 0).sum()} ({(df_fut_c['ev_c'] > 0).mean()*100:.1f}%) | "
        f"Mean EV: ${df_fut_c['ev_c'].mean():,.2f}"
    )

pdf.add_page()
pdf.section_title("4.4 Futures - A vs B vs C Comparison", level=2)
if os.path.exists(str(CHART_DIR / "06_fut_abc_comparison.png")):
    pdf.add_chart(str(CHART_DIR / "06_fut_abc_comparison.png"))

# -- 5. INSTANT-FUNDED DEEP DIVE ----------------------------------------------
pdf.add_page()
pdf.section_title("5. Instant-Funded Deep Dive", level=1)
pdf.body_text(
    f"The Instant-Funded dataset contains {len(instant_raw)} offers filtered from FX challenges "
    "(steps_label = 'Instant'). These skip the evaluation phase entirely - traders begin funded "
    "immediately. The model targets a 5% first payout with a consistency-driven minimum trading period. "
    "Parameters: 5% payout target, 3-pip spread, 5-day base period, 100x leverage."
)
if not df_inst.empty:
    inst_cols = ["firm", "account_size", "fee", "effective_dd_type", "max_dd_pct",
                 "profit_split_pct", "trading_days", "funded_payout", "total_cost", "EV", "capital_efficiency"]
    inst_widths = [22, 16, 14, 16, 14, 14, 12, 18, 16, 16, 18]
    pdf.add_table(df_inst, inst_cols, inst_widths, "Top 20 - Instant-Funded Rankings")
    pdf.body_text(
        f"Instant-Funded Summary: {len(df_inst)} offers scored | "
        f"Positive EV: {(df_inst['EV'] > 0).sum()} ({(df_inst['EV'] > 0).mean()*100:.1f}%) | "
        f"Mean EV: ${df_inst['EV'].mean():,.2f} | Max EV: ${df_inst['EV'].max():,.2f} | "
        f"Avg Capital Required: ${df_inst['capital_required'].mean():,.2f}"
    )

    # EV by DD type
    pdf.ln(3)
    pdf.section_title("Instant-Funded: EV by Drawdown Type", level=3)
    dd_grp = df_inst.groupby("effective_dd_type")["EV"].agg(["mean", "median", "count", "std"]).round(2)
    dd_grp = dd_grp.reset_index()
    dd_grp.columns = ["DD Type", "Mean EV", "Median EV", "Count", "Std Dev"]
    pdf.add_table(dd_grp, list(dd_grp.columns), [30, 30, 30, 25, 30], max_rows=10)

# -- 6. STATISTICAL ANALYSIS --------------------------------------------------
pdf.add_page()
pdf.section_title("6. Statistical Analysis", level=1)

pdf.section_title("6.1 EV by Account Size", level=2)
pdf.body_text(
    "Larger account sizes generally yield higher absolute EV due to larger funded payouts, "
    "but fees also scale. The chart below shows average EV by account size for each asset class."
)
if os.path.exists(str(CHART_DIR / "03_ev_by_size.png")):
    pdf.add_chart(str(CHART_DIR / "03_ev_by_size.png"))

# Detailed size breakdown tables
for lbl, df, ev_col in [("CFD/Forex", df_fx_a, "EV"), ("Futures", df_fut_a, "EV"), ("Instant", df_inst, "EV")]:
    if not df.empty and ev_col in df.columns:
        grp = df.groupby("account_size").agg(
            Count=(ev_col, "count"), Mean_EV=(ev_col, "mean"),
            Median_EV=(ev_col, "median"), Max_EV=(ev_col, "max"),
            Pos_Rate=(ev_col, lambda x: (x > 0).mean() * 100)
        ).round(2).reset_index()
        grp.columns = ["Size", "Count", "Mean EV", "Median EV", "Max EV", "Pos %"]
        pdf.add_table(grp, list(grp.columns), [25, 18, 25, 25, 25, 18],
                      title=f"{lbl} - EV by Account Size", max_rows=15)

pdf.add_page()
pdf.section_title("6.2 Fee vs EV Relationship", level=2)
pdf.body_text(
    "The scatter plot below reveals how challenge fees relate to expected value. "
    "Challenges with low fees relative to their EV represent the best cost-efficiency."
)
if os.path.exists(str(CHART_DIR / "10_fee_vs_ev.png")):
    pdf.add_chart(str(CHART_DIR / "10_fee_vs_ev.png"))

# Correlation analysis
pdf.section_title("Fee-EV Correlations", level=3)
for lbl, df, ev_col in [("FX Type A", df_fx_a, "EV"), ("Futures Type A", df_fut_a, "EV"), ("Instant", df_inst, "EV")]:
    if not df.empty and ev_col in df.columns and "fee" in df.columns:
        corr = df[["fee", ev_col]].corr().iloc[0, 1]
        pdf.body_text(f"{lbl}: Fee-EV correlation = {corr:.4f}")

pdf.add_page()
pdf.section_title("6.3 Drawdown Type Impact", level=2)
pdf.body_text(
    "Trailing drawdowns create compounding hedge costs (the insured base grows exponentially), "
    "while static drawdowns keep costs linear. The chart below quantifies this impact."
)
if os.path.exists(str(CHART_DIR / "11_dd_type_comparison.png")):
    pdf.add_chart(str(CHART_DIR / "11_dd_type_comparison.png"))

pdf.section_title("6.4 Profit Split Analysis", level=2)
pdf.body_text(
    "Higher profit splits directly increase funded payouts without affecting hedge costs. "
    "A 90% split vs 80% split adds 12.5% more to the funded payout."
)
if os.path.exists(str(CHART_DIR / "12_profit_split.png")):
    pdf.add_chart(str(CHART_DIR / "12_profit_split.png"))

pdf.add_page()
pdf.section_title("6.5 Capital Efficiency", level=2)
pdf.body_text(
    "Capital efficiency measures how much EV is generated per dollar of required trading capital. "
    "High capital efficiency means better returns on the hedging capital deployed."
)
if os.path.exists(str(CHART_DIR / "04_capital_efficiency.png")):
    pdf.add_chart(str(CHART_DIR / "04_capital_efficiency.png"))

# Top 10 by capital efficiency
for lbl, df, ev_col, ce_col in [
    ("FX Type A", df_fx_a, "EV", "capital_efficiency"),
    ("Futures Type A", df_fut_a, "EV", "capital_efficiency"),
    ("Instant", df_inst, "EV", "capital_efficiency"),
]:
    if not df.empty and ev_col in df.columns and ce_col in df.columns:
        top_ce = df[df[ev_col] > 0].sort_values(ce_col, ascending=False).head(10)
        if not top_ce.empty:
            pdf.add_table(top_ce, ["firm", "account_size", "fee", ev_col, "capital_required", ce_col],
                          [28, 22, 18, 22, 25, 25],
                          title=f"Top 10 Capital-Efficient - {lbl}")

# -- 6.6 EV HISTOGRAMS --------------------------------------------------------
pdf.add_page()
pdf.section_title("6.6 EV Distribution Histograms", level=2)
pdf.body_text(
    "Overlaid histograms for each asset class reveal the shape of EV distributions. "
    "Right-skewed distributions indicate a few high-EV outliers pulling the mean above the median."
)
if os.path.exists(str(CHART_DIR / "09_ev_histograms.png")):
    pdf.add_chart(str(CHART_DIR / "09_ev_histograms.png"))

# Descriptive statistics table
stats_rows = []
for lbl, df, ev_col in [
    ("FX Type A", df_fx_a, "EV"), ("FX Type B", df_fx_b, "ev_b"), ("FX Type C", df_fx_c, "ev_c"),
    ("Fut Type A", df_fut_a, "EV"), ("Fut Type B", df_fut_b, "ev_b"), ("Fut Type C", df_fut_c, "ev_c"),
    ("Instant", df_inst, "EV"),
]:
    if not df.empty and ev_col in df.columns:
        s = df[ev_col].dropna()
        stats_rows.append({
            "Model": lbl, "N": len(s), "Mean": round(s.mean(), 2), "Median": round(s.median(), 2),
            "Std": round(s.std(), 2), "Min": round(s.min(), 2), "Max": round(s.max(), 2),
            "Skew": round(s.skew(), 3),
        })
df_stats = pd.DataFrame(stats_rows)
pdf.add_table(df_stats, list(df_stats.columns),
              [22, 12, 22, 22, 22, 22, 22, 18],
              title="Descriptive Statistics - EV Across All Models")


# -- 7. KEY FINDINGS & RECOMMENDATIONS ----------------------------------------
pdf.add_page()
pdf.section_title("7. Key Findings & Recommendations", level=1)

findings = [
    ("1. Type B/C Consistently Outperform Type A",
     "Across both FX and Futures, funded-continuation models (B and C) produce higher EV "
     "than challenge-only models. The funded phase generates recurring withdrawals that accumulate "
     "expected value over multiple cycles, while hedge drag is a smaller cost per cycle."),
    ("2. Static Drawdowns Are More Profitable Than Trailing",
     "Challenges with static (balance-based) drawdowns produce significantly higher EV because "
     "the hedge cost remains linear. Trailing drawdowns create compounding costs that erode margins."),
    ("3. Larger Accounts != Better Capital Efficiency",
     "While larger account sizes produce higher absolute EV, smaller accounts often have better "
     "capital efficiency (EV per dollar of required capital). The sweet spot varies by firm."),
    ("4. Payout Caps Severely Limit Futures EV",
     "Many futures firms cap payouts at $1,000-$3,000 per withdrawal. This caps the funded payout "
     "and extends the break-even timeline. Uncapped or high-cap firms dominate the futures rankings."),
    ("5. Profit Split Is the Strongest EV Driver",
     "A 10 percentage-point increase in profit split (e.g., 80% -> 90%) directly translates to "
     "~12.5% more funded payout with zero additional hedge cost. Firms offering 90%+ splits dominate."),
    ("6. Instant-Funded Offers Are Capital-Light",
     "Instant-funded models require significantly less capital than challenge-based models because "
     "there is no multi-phase evaluation to hedge through. They offer quick, low-risk opportunities."),
    ("7. Fee-to-EV Ratio Matters More Than Absolute EV",
     "A $200 fee challenge with $100 EV (50% return) is often better than a $1,000 fee challenge "
     "with $300 EV (30% return). Cost efficiency and capital efficiency should inform selection."),
]

for title, body in findings:
    pdf.section_title(title, level=3)
    pdf.body_text(body)

# Recommendations
pdf.add_page()
pdf.section_title("Recommendations", level=2)
recs = [
    "Prioritize Type B model for challenges where capital allows continued funded-phase hedging.",
    "Target firms with static drawdowns and >=90% profit splits for maximum EV.",
    "For Futures, avoid heavily capped firms ($1K payouts) unless fees are very low.",
    "Deploy initial capital into Instant-Funded offers for quick, low-risk EV generation.",
    "Diversify across 3-5 top-ranked firms per model to reduce single-firm counterparty risk.",
    "Re-run this analysis monthly as firms frequently update their challenge terms.",
    "Consider Type C surplus only when comfortable with the additional capital requirements.",
    f"Focus on firms with >$100 EV in Type A as entry-level opportunities ({(df_fx_a['EV'] > 100).sum() if not df_fx_a.empty else 0} FX + {(df_fut_a['EV'] > 100).sum() if not df_fut_a.empty else 0} Futures available).",
]
for i, rec in enumerate(recs, 1):
    pdf.body_text(f"{i}. {rec}")


# -- APPENDIX A: METHODOLOGY --------------------------------------------------
pdf.add_page()
pdf.section_title("Appendix A: Methodology", level=1)
pdf.body_text(
    "All models use a deterministic hedging framework. The hedge is a position that profits "
    "when the funded/challenge account moves against the trader (drawdown direction). "
    "The hedge is sized so that account drawdown = hedge profit, creating a zero-net-loss "
    "insurance mechanism."
)
pdf.section_title("Type A - Challenge Insurance", level=3)
pdf.body_text(
    "The insured base starts at the challenge fee. For each evaluation phase, the hedge loses "
    "as the account profits toward the target. For trailing drawdowns, the hedge is resized daily "
    "(compounding). For static, costs are linear. Total cost = (fee) x compounding factor. "
    "EV = funded_payout - total_cost."
)
pdf.section_title("Type B - Funded Recovery", level=3)
pdf.body_text(
    "Extends Type A into the funded phase. The funded account hedge is sized to recover the "
    "full accumulated cost stack if the account fails. Per-cycle: the trader withdraws a small "
    "profit (4% of account x split), while the hedge incurs drag (1.5% of account). "
    "Survival probability compounds at 80% per cycle over 6 cycles. EV_B = Sum(withdrawals) - Sum(drag)."
)
pdf.section_title("Type C - Funded Surplus", level=3)
pdf.body_text(
    "Extends Type B with an additional surplus buffer (default 2% of account). The hedge covers "
    "L + P (stack + surplus), so on failure it recovers both. Drag scales proportionally by "
    "(L+P)/L. EV_C = Sum(withdrawals) + Sum(expected_surplus) - Sum(drag)."
)
pdf.section_title("Instant-Funded", level=3)
pdf.body_text(
    "Single-phase model targeting a 5% first payout. Trading days are driven by consistency rules. "
    "Hedge cost depends on drawdown type (static vs trailing). Capital requirement based on "
    "peak hedge notional divided by leverage with 50% buffer."
)


# -- APPENDIX B: PARAMETER SUMMARY --------------------------------------------
pdf.add_page()
pdf.section_title("Appendix B: Parameter Summary", level=1)

params = [
    ("CFD/Forex Parameters", [
        ("Funded Target", "8%"), ("Spread Cost", "3 pips (0.03%)"),
        ("Resizes per Phase (Trailing)", "20"), ("Withdrawal per Cycle", "4%"),
        ("Funded Cycles", "6"), ("Survival Rate", "80%"),
        ("Hedge Drag per Cycle", "1.5%"), ("Surplus Target (Type C)", "2%"),
    ]),
    ("Futures Parameters", [
        ("Funded Target", "6%"), ("Spread per Contract", "$5 round-trip"),
        ("Default Consistency Threshold", "20%"), ("Withdrawal per Cycle", "4%"),
        ("Funded Cycles", "6"), ("Survival Rate", "80%"),
        ("Hedge Drag per Cycle", "1.5%"), ("Surplus Target (Type C)", "2%"),
    ]),
    ("Instant-Funded Parameters", [
        ("First Payout Target", "5%"), ("Spread Cost", "3 pips (0.03%)"),
        ("Base Trading Days", "5"), ("Default Leverage", "100x"),
        ("Unspecified DD Treatment", "Static"),
    ]),
]

for section, items in params:
    pdf.section_title(section, level=3)
    pdf.set_font("Helvetica", "", 9)
    for param, val in items:
        pdf.cell(60, 5, f"  {param}:", align="R")
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(50, 5, f"  {val}", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 9)
    pdf.ln(3)


# -- SAVE PDF ------------------------------------------------------------------
print(f"\nSaving PDF to: {OUTPUT_PDF}", flush=True)
pdf.output(str(OUTPUT_PDF))
print(f"[ok] PDF saved successfully ({OUTPUT_PDF.stat().st_size / 1024:.0f} KB)")
print(f"  Charts generated: {len(chart_paths)}")
print("Done!")
