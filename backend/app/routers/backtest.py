"""
Backtesting endpoints.
  POST /backtest/run   – trigger a new backtest run
  GET  /backtest       – list all backtest results
  GET  /backtest/{id}  – single result with equity curve
"""
import asyncio
from datetime import date, datetime, timezone
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.models.db_models import BacktestResult
from app.models.schemas import BacktestResultOut

router = APIRouter(prefix="/backtest", tags=["Backtest"])


# ── Core backtesting logic ─────────────────────────────────────

def run_backtest_simulation(
    model_version: str,
    symbols: List[str],
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    transaction_cost_pct: float = 0.001,
    slippage_pct: float = 0.0005,
) -> Dict:
    """
    Signal-based backtest using historical Yahoo data.
    Returns detailed performance metrics.
    """
    from app.services.market_data import YahooFallbackProvider
    from engine.indicators import compute_all_indicators
    from engine.feature_engineering import build_feature_matrix, CLASS_MAP
    from engine.predictor import get_xgb_predictor

    provider = YahooFallbackProvider()
    predictor = get_xgb_predictor()

    if not predictor.is_ready:
        return {"error": "No trained model available. Run training first."}

    # Collect per-symbol results
    all_trades: List[Dict] = []
    per_stock: Dict[str, Dict] = {}
    equity = 100_000.0  # Starting capital INR
    equity_curve: List[Dict] = [{"date": "start", "equity": equity}]

    for sym in symbols[:20]:    # Limit to 20 symbols for speed
        try:
            raw = provider._sync_history(sym, "60d", "5m")
            if len(raw) < 100:
                continue
            df = pd.DataFrame(raw)
            df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
            df = df.set_index("timestamp")[["open", "high", "low", "close", "volume"]].astype(float)
            df = compute_all_indicators(df)

            # Walk-forward simulation
            sym_trades = []
            in_trade = None

            for i in range(60, len(df)):
                window = df.iloc[:i]
                signal, conf, _ = predictor.predict(window)
                close_price = float(df.iloc[i]["close"])

                if in_trade:
                    # Check exit
                    high = float(df.iloc[i]["high"])
                    low  = float(df.iloc[i]["low"])

                    hit_target = (in_trade["direction"] == "BUY"  and high >= in_trade["target"]) or \
                                 (in_trade["direction"] == "SELL" and low  <= in_trade["target"])
                    hit_sl     = (in_trade["direction"] == "BUY"  and low  <= in_trade["sl"]) or \
                                 (in_trade["direction"] == "SELL" and high >= in_trade["sl"])

                    if hit_target or hit_sl:
                        exit_price = in_trade["target"] if hit_target else in_trade["sl"]
                        pnl = (exit_price - in_trade["entry"]) if in_trade["direction"] == "BUY" \
                              else (in_trade["entry"] - exit_price)
                        # Deduct costs
                        cost = abs(pnl) * (transaction_cost_pct + slippage_pct)
                        net_pnl = pnl - cost

                        in_trade["exit_price"] = exit_price
                        in_trade["pnl"]        = net_pnl
                        in_trade["outcome"]    = "WIN" if net_pnl > 0 else "LOSS"
                        sym_trades.append(in_trade)
                        in_trade = None

                elif signal in ("BUY", "SELL") and conf >= 0.60:
                    from engine.risk_manager import calculate_risk_profile
                    rp = calculate_risk_profile(signal, close_price, atr=close_price * 0.01)
                    in_trade = {
                        "symbol": sym,
                        "direction": signal,
                        "entry": rp.entry_price,
                        "sl": rp.stop_loss,
                        "target": rp.target_price,
                        "entry_time": df.index[i].isoformat(),
                    }

            if sym_trades:
                total_pnl = sum(t["pnl"] for t in sym_trades)
                wins      = sum(1 for t in sym_trades if t["outcome"] == "WIN")
                equity   += total_pnl
                equity_curve.append({"date": sym, "equity": round(equity, 2)})
                per_stock[sym] = {
                    "trades": len(sym_trades),
                    "wins": wins,
                    "win_rate": round(wins / len(sym_trades), 4),
                    "total_pnl": round(total_pnl, 2),
                }
                all_trades.extend(sym_trades)
        except Exception as exc:
            per_stock[sym] = {"error": str(exc)}

    if not all_trades:
        return {"error": "No trades generated in backtest period"}

    # Aggregate metrics
    total_trades  = len(all_trades)
    winning_trades = sum(1 for t in all_trades if t.get("outcome") == "WIN")
    pnls = [t["pnl"] for t in all_trades]
    win_pnls  = [p for p in pnls if p > 0]
    loss_pnls = [p for p in pnls if p <= 0]

    total_return = (equity - 100_000) / 100_000 * 100

    # Sharpe (simplified using trade-level returns)
    pnl_arr = np.array(pnls)
    sharpe = float(pnl_arr.mean() / pnl_arr.std()) * np.sqrt(252) if pnl_arr.std() > 0 else 0.0

    # Max drawdown
    eq_values = [e["equity"] for e in equity_curve]
    running_max = np.maximum.accumulate(eq_values)
    drawdown = (np.array(eq_values) - running_max) / running_max
    max_dd = float(drawdown.min())

    return {
        "model_version": model_version,
        "total_trades": total_trades,
        "winning_trades": winning_trades,
        "losing_trades": total_trades - winning_trades,
        "win_rate": round(winning_trades / total_trades, 4) if total_trades > 0 else 0,
        "total_return": round(total_return, 4),
        "sharpe_ratio": round(sharpe, 4),
        "max_drawdown": round(max_dd, 4),
        "avg_profit": round(float(np.mean(win_pnls)), 2) if win_pnls else 0,
        "avg_loss":   round(float(np.mean(loss_pnls)), 2) if loss_pnls else 0,
        "equity_curve": equity_curve,
        "per_stock_stats": per_stock,
        "transaction_cost_pct": transaction_cost_pct,
        "slippage_pct": slippage_pct,
    }


@router.post("/run", status_code=202)
async def trigger_backtest(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Trigger a background backtest run."""
    from collector.yahoo_fallback import WATCHLIST
    from engine.predictor import get_xgb_predictor

    predictor = get_xgb_predictor()
    model_version = predictor.version if predictor.is_ready else "unknown"

    async def _run():
        result = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: run_backtest_simulation(model_version, WATCHLIST)
        )
        if "error" not in result:
            async with db as session:
                bt = BacktestResult(
                    model_version=result["model_version"],
                    total_return=result.get("total_return"),
                    win_rate=result.get("win_rate"),
                    sharpe_ratio=result.get("sharpe_ratio"),
                    max_drawdown=result.get("max_drawdown"),
                    total_trades=result.get("total_trades"),
                    winning_trades=result.get("winning_trades"),
                    losing_trades=result.get("losing_trades"),
                    avg_profit=result.get("avg_profit"),
                    avg_loss=result.get("avg_loss"),
                    equity_curve=result.get("equity_curve"),
                    per_stock_stats=result.get("per_stock_stats"),
                    transaction_cost_pct=result.get("transaction_cost_pct"),
                    slippage_pct=result.get("slippage_pct"),
                )
                session.add(bt)
                await session.commit()

    background_tasks.add_task(_run)
    return {"message": "Backtest started", "model_version": model_version}


@router.get("", response_model=List[BacktestResultOut])
async def list_backtests(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(BacktestResult).order_by(desc(BacktestResult.run_at)).limit(20)
    )
    return result.scalars().all()


@router.get("/{backtest_id}", response_model=BacktestResultOut)
async def get_backtest(backtest_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(BacktestResult).where(BacktestResult.id == backtest_id)
    )
    bt = result.scalar_one_or_none()
    if not bt:
        raise HTTPException(status_code=404, detail="Backtest not found")
    return bt
