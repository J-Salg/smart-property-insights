"""
Energy model inference.

Loads model + scaler (local or S3 via resolver)
and exposes a single predict() method for API use.
"""
import numpy as np
import joblib
import tensorflow as tf
from app.services.model_loader import resolve_artifact

_model = None
_scaler = None

FEATURES = [
    "relative_compactness",
    "surface_area",
    "wall_area",
    "roof_area",
    "overall_height",
    "orientation",
    "glazing_area",
    "glazing_area_dist",
]


def _load() -> None:
    global _model, _scaler
    if _model is not None:
        return

    model_path = resolve_artifact("energy_model.keras")
    scaler_path = resolve_artifact("energy_scaler.joblib")

    _model = tf.keras.models.load_model(model_path)
    _scaler = joblib.load(scaler_path)


class EnergyPredictor:
    @staticmethod
    def is_ready() -> bool:
        return _model is not None

    @staticmethod
    def predict(data: dict) -> dict:
        _load()

        missing = [f for f in FEATURES if f not in data]
        if missing:
            raise ValueError(f"Missing required fields: {missing}")

        x = np.array([[float(data[f]) for f in FEATURES]], dtype=np.float32)
        x_scaled = _scaler.transform(x)

        pred = _model.predict(x_scaled, verbose=0)[0]
        heating = round(float(pred[0]), 2)
        cooling = round(float(pred[1]), 2)

        return {
            "heating_load_kwh_m2": heating,
            "cooling_load_kwh_m2": cooling,
            "total_load_kwh_m2": round(heating + cooling, 2),
        }
