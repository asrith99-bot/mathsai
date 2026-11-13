"""
ML Model Inference Engine.

Loads trained models from ml_models/ and provides
real-time prediction on current OHLCV+indicator data.

Models are loaded once at startup and re-loaded after retraining.
"""
import json
import pickle
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from loguru import logger

from engine.feature_engineering import (
    FEATURE_COLUMNS, CLASS_MAP, REVERSE_CLASS_MAP,
    prepare_inference_features
)

MODEL_DIR = Path(__file__).parent.parent / "ml_models"


class ModelPredictor:
    """
    Wraps a trained model for real-time inference.
    Thread-safe for read access; call reload() to swap the model.
    """

    def __init__(self, model_type: str = "xgboost"):
        self.model_type   = model_type
        self._model       = None
        self._metadata    = {}
        self._version     = "unloaded"
        self.load()

    def load(self, version: str = "latest") -> bool:
        """Load model from disk. Returns True on success."""
        pkl_path  = MODEL_DIR / f"{self.model_type}_{version}.pkl"
        meta_path = MODEL_DIR / f"{self.model_type}_{version}_meta.json"

        if not pkl_path.exists():
            logger.warning(
                f"Model not found: {pkl_path}. "
                "Run trainer.py to train a model before serving predictions."
            )
            return False

        try:
            with open(pkl_path, "rb") as f:
                self._model = pickle.load(f)
            if meta_path.exists():
                with open(meta_path) as f:
                    self._metadata = json.load(f)
            self._version = self._metadata.get("version", version)
            logger.info(f"Loaded {self.model_type} model v{self._version}")
            return True
        except Exception as exc:
            logger.error(f"Failed to load model: {exc}")
            return False

    def reload(self) -> bool:
        """Reload the latest model from disk."""
        return self.load("latest")

    @property
    def is_ready(self) -> bool:
        return self._model is not None

    @property
    def version(self) -> str:
        return self._version

    @property
    def metadata(self) -> Dict:
        return self._metadata

    def predict(
        self,
        df: pd.DataFrame,
    ) -> Tuple[str, float, Dict[str, float]]:
        """
        Predict the signal for the latest candle in df.

        Returns:
            signal: 'BUY', 'SELL', or 'HOLD'
            confidence: probability of the predicted class (0–1)
            probabilities: dict of all class probabilities
        """
        if not self.is_ready:
            return "HOLD", 0.0, {"BUY": 0.0, "SELL": 0.0, "HOLD": 1.0}

        try:
            X = prepare_inference_features(df)
            if X.empty:
                return "HOLD", 0.0, {"BUY": 0.0, "SELL": 0.0, "HOLD": 1.0}

            # Use only the last row for inference
            X_last = X.iloc[[-1]]

            # Align columns with training features
            train_features = self._metadata.get("features", FEATURE_COLUMNS)
            for col in train_features:
                if col not in X_last.columns:
                    X_last[col] = 0.0
            X_last = X_last[train_features]

            # Predict
            if hasattr(self._model, "predict_proba"):
                proba = self._model.predict_proba(X_last)[0]
                # XGBoost and RF return proba for each class (0=SELL, 1=HOLD, 2=BUY)
                pred_class = int(np.argmax(proba))
                confidence = float(proba[pred_class])
                probabilities = {
                    CLASS_MAP[i]: float(proba[i])
                    for i in range(len(proba))
                }
            else:
                pred_class = int(self._model.predict(X_last)[0])
                confidence = 0.6
                probabilities = {
                    "SELL": 0.0, "HOLD": 0.0, "BUY": 0.0,
                    CLASS_MAP[pred_class]: confidence,
                }

            signal = CLASS_MAP[pred_class]
            return signal, confidence, probabilities

        except Exception as exc:
            logger.error(f"Prediction failed: {exc}")
            return "HOLD", 0.0, {"BUY": 0.0, "SELL": 0.0, "HOLD": 1.0}

    def predict_batch(
        self,
        symbol_dfs: Dict[str, pd.DataFrame],
    ) -> Dict[str, Tuple[str, float, Dict[str, float]]]:
        """Predict for multiple symbols in one call."""
        results = {}
        for symbol, df in symbol_dfs.items():
            results[symbol] = self.predict(df)
        return results


# ── Global predictor singletons ───────────────────────────────
_xgb_predictor: Optional[ModelPredictor] = None
_rf_predictor:  Optional[ModelPredictor] = None


def get_xgb_predictor() -> ModelPredictor:
    global _xgb_predictor
    if _xgb_predictor is None:
        _xgb_predictor = ModelPredictor("xgboost")
    return _xgb_predictor


def get_rf_predictor() -> ModelPredictor:
    global _rf_predictor
    if _rf_predictor is None:
        _rf_predictor = ModelPredictor("random_forest")
    return _rf_predictor


def reload_all_models() -> None:
    """Call after retraining to hot-swap all models."""
    if _xgb_predictor:
        _xgb_predictor.reload()
    if _rf_predictor:
        _rf_predictor.reload()
    logger.info("All models reloaded.")
