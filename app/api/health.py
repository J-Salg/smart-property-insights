from flask import Blueprint, jsonify
from app.services.price_predictor import PricePredictor
from app.services.energy_predictor import EnergyPredictor

health_bp = Blueprint("health", __name__)


@health_bp.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "models": {
            "price": PricePredictor.is_ready(),
            "energy": EnergyPredictor.is_ready(),
        },
    })
