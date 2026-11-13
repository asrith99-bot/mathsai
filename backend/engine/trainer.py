"""
ML Model Training Pipeline.

Trains Random Forest and XGBoost classifiers on historical intraday data.
Uses chronological train/validation/test splitting to prevent data leakage.
Saves trained models to backend/ml_models/.
"""
import os
import json
import pickle
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from loguru import logger
from sklearn.ensemble import RandomForestClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import (
    accuracy_score, classification_report, f1_score,
    precision_score, recall_score
)
from sklearn.preprocessing import StandardScaler
import xgboost as xgb

from engine.indicators import compute_all_indicators
from engine.feature_engineering import (
    FEATURE_COLUMNS, build_feature_matrix, CLASS_MAP
)

MODEL_DIR = Path(__file__).parent.parent / "ml_models"
MODEL_DIR.mkdir(exist_ok=True)

# ── Split ratios ──────────────────────────────────────────────
TRAIN_RATIO = 0.70
VAL_RATIO   = 0.15
# test = remaining 15%

WATCHLIST = [
    "RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK",
    "SBIN", "BHARTIARTL", "ITC", "LT", "AXISBANK",
    "KOTAKBANK", "BAJFINANCE", "MARUTI", "SUNPHARMA", "TITAN",
    "TATAMOTORS", "NTPC", "POWERGRID", "ONGC", "TATASTEEL",
    "JSWSTEEL", "HINDALCO", "WIPRO", "HCLTECH", "TECHM",
    "ULTRACEMCO", "ASIANPAINT", "NESTLEIND", "TRENT", "BEL",
    "ADANIPORTS", "COALINDIA", "GRASIM", "EICHERMOT", "DRREDDY",
    "CIPLA", "DIVISLAB", "APOLLOHOSP", "INDUSINDBK", "BANKBARODA",
    "PNB", "CANBK", "DLF", "GODREJCP", "SBILIFE",
    "HDFCLIFE", "LTIM", "ZOMATO", "HINDUNILVR",
]

# Subset used for initial training to avoid Yahoo rate limits
TRAINING_SUBSET = [
    "RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK",
    "SBIN", "BHARTIARTL", "ITC", "LT", "AXISBANK",
    "KOTAKBANK", "BAJFINANCE", "MARUTI", "SUNPHARMA", "TITAN",
    "WIPRO", "HCLTECH", "TATAMOTORS", "NTPC", "ONGC",
]


def _fetch_training_data(symbol: str, period: str = "60d", interval: str = "5m") -> pd.DataFrame:
    """
    Fetch historical OHLCV data from Yahoo Finance for training.
    Compatible with yfinance >=1.0 multi-level column format.
    Retries up to 3 times with backoff on failure.
    """
    import time
    import yfinance as yf
    yf_sym = f"{symbol}.NS" if symbol != "M&M" else "M%26M.NS"

    for attempt in range(3):
        try:
            time.sleep(1 + attempt * 2)
            df = yf.download(
                yf_sym,
                period=period,
                interval=interval,
                progress=False,
                auto_adjust=True,
            )
            if df.empty:
                logger.warning(f"No training data for {symbol} (attempt {attempt+1})")
                continue

            # yfinance >=1.0 returns MultiIndex columns: (Price, Ticker)
            # Flatten to single level lowercase
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = [str(c[0]).lower() for c in df.columns]
            else:
                df.columns = [str(c).lower() for c in df.columns]

            # Rename 'adj close' → 'close' if present and 'close' missing
            if "adj close" in df.columns and "close" not in df.columns:
                df = df.rename(columns={"adj close": "close"})

            needed = ["open", "high", "low", "close", "volume"]
            missing = [c for c in needed if c not in df.columns]
            if missing:
                logger.warning(f"{symbol}: missing columns {missing}, skipping")
                continue

            df = df[needed].dropna()
            df.index = pd.to_datetime(df.index, utc=True)
            logger.info(f"{symbol}: {len(df)} rows fetched")
            return df

        except Exception as exc:
            logger.warning(f"Attempt {attempt+1} failed for {symbol}: {exc}")
            time.sleep(5)

    logger.error(f"All attempts failed for {symbol}")
    return pd.DataFrame()


def collect_all_training_data(symbols: List[str] = None) -> pd.DataFrame:
    """
    Collect and concatenate feature matrices from all symbols.
    Defaults to TRAINING_SUBSET to avoid Yahoo rate limits.
    """
    if symbols is None:
        symbols = TRAINING_SUBSET

    all_X: List[pd.DataFrame] = []
    all_y: List[pd.Series] = []

    for sym in symbols:
        logger.info(f"Fetching training data: {sym}")
        raw = _fetch_training_data(sym)
        if raw.empty:
            continue
        raw = compute_all_indicators(raw)
        try:
            X, y = build_feature_matrix(raw, lookahead=1)
            if len(X) < 50:
                logger.warning(f"{sym}: insufficient rows ({len(X)}), skipping")
                continue
            all_X.append(X)
            all_y.append(y)
        except Exception as exc:
            logger.error(f"Feature engineering failed for {sym}: {exc}")

    if not all_X:
        raise RuntimeError("No training data collected — check market data connectivity")

    X_all = pd.concat(all_X, ignore_index=True)
    y_all = pd.concat(all_y, ignore_index=True)
    logger.info(f"Total training samples: {len(X_all)}, class dist: {y_all.value_counts().to_dict()}")
    return X_all, y_all


def chronological_split(
    X: pd.DataFrame,
    y: pd.Series,
) -> Tuple:
    """
    Chronological split: train | validation | test.
    No shuffling — avoids temporal data leakage.
    """
    n = len(X)
    train_end = int(n * TRAIN_RATIO)
    val_end   = int(n * (TRAIN_RATIO + VAL_RATIO))

    X_train, y_train = X.iloc[:train_end], y.iloc[:train_end]
    X_val,   y_val   = X.iloc[train_end:val_end], y.iloc[train_end:val_end]
    X_test,  y_test  = X.iloc[val_end:], y.iloc[val_end:]

    logger.info(f"Split → Train: {len(X_train)}, Val: {len(X_val)}, Test: {len(X_test)}")
    return X_train, y_train, X_val, y_val, X_test, y_test


def evaluate_model(model, X: pd.DataFrame, y: pd.Series, label: str) -> Dict:
    preds = model.predict(X)
    acc   = float(accuracy_score(y, preds))
    f1    = float(f1_score(y, preds, average="weighted", zero_division=0))
    report = classification_report(
        y, preds,
        target_names=["SELL", "HOLD", "BUY"],
        zero_division=0,
        output_dict=True,
    )
    logger.info(f"{label} → Accuracy: {acc:.4f}, F1: {f1:.4f}")
    return {"accuracy": acc, "f1": f1, "report": report}


def train_xgboost(X_train, y_train, X_val, y_val) -> xgb.XGBClassifier:
    model = xgb.XGBClassifier(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        use_label_encoder=False,
        eval_metric="mlogloss",
        early_stopping_rounds=20,
        random_state=42,
        n_jobs=-1,
        num_class=3,
        objective="multi:softprob",
    )
    model.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        verbose=False,
    )
    return model


def train_random_forest(X_train, y_train) -> RandomForestClassifier:
    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=10,
        min_samples_leaf=5,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)
    return model


def save_model(model, model_name: str, version: str, metadata: Dict) -> str:
    """Pickle model to ml_models/ and save metadata JSON."""
    model_path = MODEL_DIR / f"{model_name}_{version}.pkl"
    meta_path  = MODEL_DIR / f"{model_name}_{version}_meta.json"

    with open(model_path, "wb") as f:
        pickle.dump(model, f)

    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2, default=str)

    logger.info(f"Saved model: {model_path}")
    return str(model_path)


def run_training_pipeline(
    model_type: str = "xgboost",
    symbols: List[str] = None,
) -> Dict:
    """
    Full training pipeline entry point.
    Returns metadata dict with paths and metrics.
    """
    version = datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M")
    logger.info(f"=== Starting training: {model_type} v{version} ===")

    X, y = collect_all_training_data(symbols)
    X_train, y_train, X_val, y_val, X_test, y_test = chronological_split(X, y)

    if model_type == "xgboost":
        model = train_xgboost(X_train, y_train, X_val, y_val)
    elif model_type == "random_forest":
        model = train_random_forest(X_train, y_train)
    else:
        raise ValueError(f"Unknown model type: {model_type}")

    val_metrics  = evaluate_model(model, X_val,  y_val,  "Validation")
    test_metrics = evaluate_model(model, X_test, y_test, "Test")

    # Feature importance
    if hasattr(model, "feature_importances_"):
        importances = dict(zip(
            X_train.columns.tolist(),
            model.feature_importances_.tolist(),
        ))
    else:
        importances = {}

    # Prediction distribution on test set
    pred_test = model.predict(X_test)
    dist = {CLASS_MAP[k]: int((pred_test == k).sum()) for k in [0, 1, 2]}

    metadata = {
        "model_name": model_type,
        "version": version,
        "trained_at": datetime.now(tz=timezone.utc).isoformat(),
        "features": X_train.columns.tolist(),
        "feature_importances": importances,
        "training_samples": len(X_train),
        "val_accuracy": val_metrics["accuracy"],
        "val_f1": val_metrics["f1"],
        "test_accuracy": test_metrics["accuracy"],
        "test_f1": test_metrics["f1"],
        "prediction_distribution": dist,
        "val_report": val_metrics["report"],
        "test_report": test_metrics["report"],
    }

    file_path = save_model(model, model_type, version, metadata)
    metadata["file_path"] = file_path

    # Also save as 'latest'
    latest_path = MODEL_DIR / f"{model_type}_latest.pkl"
    with open(latest_path, "wb") as f:
        pickle.dump(model, f)
    with open(MODEL_DIR / f"{model_type}_latest_meta.json", "w") as f:
        json.dump(metadata, f, indent=2, default=str)

    logger.info(f"=== Training complete: test_accuracy={test_metrics['accuracy']:.4f} ===")
    return metadata


if __name__ == "__main__":
    # Run as script: python -m engine.trainer
    result = run_training_pipeline(model_type="xgboost")
    print(json.dumps(result, indent=2, default=str))
