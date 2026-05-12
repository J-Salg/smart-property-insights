"""
Price model inference.

Loads model + scaler (local or S3 via resolver)
and exposes a single predict() method for API use.

Trained on log1p(SalePrice) → outputs converted with expm1().
"""
import numpy as np
import joblib
import tensorflow as tf
from app.services.model_loader import resolve_artifact

_model = None
_scaler = None

FEATURES = [
    "overall_qual",
    "gr_liv_area",
    "year_built",
    "garage_cars",
    "total_bsmt_sf",
    "full_bath",
    "bedroom_abv_gr",
    "lot_area",
]


def _load() -> None:
    global _model, _scaler
    if _model is not None:
        return

    model_path = resolve_artifact("price_model.keras")
    scaler_path = resolve_artifact("price_scaler.joblib")

    _model = tf.keras.models.load_model(model_path)
    _scaler = joblib.load(scaler_path)


class PricePredictor:
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

        log_price = float(_model.predict(x_scaled, verbose=0)[0][0])
        price = float(np.expm1(log_price))

        return {
            "predicted_price": round(price, 2),
            "price_range_low": round(price * 0.90, 2),
            "price_range_high": round(price * 1.10, 2),
            "currency": "USD",
        }
