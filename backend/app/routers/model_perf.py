"""
Model performance endpoints.
  GET  /model/versions    – all model versions
  GET  /model/active      – currently active model
  POST /model/train       – trigger background retraining
  POST /model/reload      – hot-reload latest model without retraining
"""
import asyncio
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.models.db_models import ModelVersion
from app.models.schemas import ModelVersionOut
from engine.predictor import get_xgb_predictor, reload_all_models

router = APIRouter(prefix="/model", tags=["Model Performance"])


@router.get("/versions")
async def list_model_versions(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ModelVersion).order_by(desc(ModelVersion.trained_at))
    )
    return result.scalars().all()


@router.get("/active")
async def get_active_model():
    predictor = get_xgb_predictor()
    return {
        "model_name": "xgboost",
        "version": predictor.version,
        "is_ready": predictor.is_ready,
        "metadata": predictor.metadata,
    }


@router.post("/train", status_code=202)
async def trigger_training(
    background_tasks: BackgroundTasks,
    model_type: str = "xgboost",
    db: AsyncSession = Depends(get_db),
):
    """Triggers model retraining in background. Returns immediately."""
    async def _train_and_save():
        from engine.trainer import run_training_pipeline
        from app.models.db_models import ModelVersion as MVModel

        try:
            meta = await asyncio.get_event_loop().run_in_executor(
                None, lambda: run_training_pipeline(model_type)
            )
            # Save version record to DB
            async with db as session:
                mv = MVModel(
                    model_name=meta["model_name"],
                    version=meta["version"],
                    features=meta.get("features"),
                    feature_importances=meta.get("feature_importances"),
                    val_accuracy=meta.get("val_accuracy"),
                    val_f1=meta.get("val_f1"),
                    test_accuracy=meta.get("test_accuracy"),
                    test_f1=meta.get("test_f1"),
                    prediction_distribution=meta.get("prediction_distribution"),
                    training_samples=meta.get("training_samples"),
                    file_path=meta.get("file_path"),
                    is_active=True,
                )
                session.add(mv)
                await session.commit()
            # Reload
            reload_all_models()
        except Exception as exc:
            import traceback
            print(f"Training failed: {exc}\n{traceback.format_exc()}")

    background_tasks.add_task(_train_and_save)
    return {"message": f"Training {model_type} started in background"}


@router.post("/reload")
async def reload_model():
    """Hot-reload the latest model files from disk."""
    reload_all_models()
    predictor = get_xgb_predictor()
    return {
        "message": "Models reloaded",
        "version": predictor.version,
        "is_ready": predictor.is_ready,
    }
