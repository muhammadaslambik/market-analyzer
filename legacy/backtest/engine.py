"""Minimal vectorized backtest for the confluence score.

Position rule: score >= entry -> long, score <= -entry -> short, else flat
(squared off when the score returns inside the neutral band).
Costs are charged on every position change. This is a research tool, not a
tick-accurate simulator."""

from __future__ import annotations

import numpy as np
import pandas as pd

from app.core.signals.confluence import score_series


def run_backtest(df: pd.DataFrame, indicators: dict, fee_bps: float = 10,
                 slippage_bps: float = 5, entry: float = 20, neutral: float = 10) -> dict:
    score = score_series(df, indicators)
    pos = pd.Series(0.0, index=df.index)
    state = 0.0
    for i, s in enumerate(score):
        if s >= entry:
            state = 1.0
        elif s <= -entry:
            state = -1.0
        elif abs(s) < neutral:
            state = 0.0
        pos.iloc[i] = state
    ret = df["close"].pct_change().fillna(0)
    cost = (pos.diff().abs().fillna(0)) * (fee_bps + slippage_bps) / 1e4
    strat = pos.shift(1).fillna(0) * ret - cost
    equity = (1 + strat).cumprod()

    trades = []
    cur_pos, entry_eq = 0.0, 1.0
    for i in range(len(df)):
        p = pos.iloc[i]
        if p != cur_pos:
            if cur_pos != 0:
                trades.append((equity.iloc[i] / entry_eq - 1) * cur_pos)
            if p != 0:
                entry_eq = equity.iloc[i]
            cur_pos = p
    if cur_pos != 0:
        trades.append((equity.iloc[-1] / entry_eq - 1) * cur_pos)

    trades = np.array(trades)
    wins = trades[trades > 0]
    losses = trades[trades <= 0]
    gross_profit = wins.sum() if len(wins) else 0.0
    gross_loss = abs(losses.sum()) if len(losses) else 0.0
    running_max = equity.cummax()
    max_dd = float(((equity - running_max) / running_max).min())
    bh = float(df["close"].iloc[-1] / df["close"].iloc[0] - 1)

    return {
        "bars": len(df),
        "trades": int(len(trades)),
        "win_rate": round(float((trades > 0).mean()) if len(trades) else 0.0, 4),
        "profit_factor": round(gross_profit / gross_loss, 3) if gross_loss > 0 else None,
        "total_return": round(float(equity.iloc[-1] - 1), 4),
        "buy_hold_return": round(bh, 4),
        "max_drawdown": round(max_dd, 4),
        "avg_score": round(float(score.mean()), 1),
    }
