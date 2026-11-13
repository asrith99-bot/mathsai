#!/usr/bin/env bash
# Backend startup script
set -e

echo "=== AI Stock Intelligence Backend ==="

# Check if model exists, train if not
if [ ! -f "ml_models/xgboost_latest.pkl" ]; then
  echo "No trained model found. Training now (this will take 5–15 minutes)…"
  python -m engine.trainer
  echo "Training complete."
fi

echo "Starting FastAPI server…"
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
