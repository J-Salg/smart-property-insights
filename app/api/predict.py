from flask import Blueprint, request, jsonify
from app.services.price_predictor import PricePredictor
from app.services.energy_predictor import EnergyPredictor
from app.models.prediction_log import PredictionLog
from app.extensions import db

predict_bp = Blueprint("predict", __name__)


@predict_bp.route("/predict/price", methods=["POST"])
def predict_price():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    try:
        result = PricePredictor.predict(data)
    except FileNotFoundError:
        return jsonify({"error": "Price model unavailable — please try again shortly"}), 503
    except ValueError as e:
        return jsonify({"error": str(e)}), 422

    _log(prediction_type="price", inputs=data, outputs=result)
    return jsonify(result)


@predict_bp.route("/predict/energy", methods=["POST"])
def predict_energy():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    try:
        result = EnergyPredictor.predict(data)
    except FileNotFoundError:
        return jsonify({"error": "Energy model unavailable — please try again shortly"}), 503
    except ValueError as e:
        return jsonify({"error": str(e)}), 422

    _log(prediction_type="energy", inputs=data, outputs=result)
    return jsonify(result)


def _log(prediction_type: str, inputs: dict, outputs: dict) -> None:
    try:
        entry = PredictionLog(prediction_type=prediction_type, inputs=inputs, outputs=outputs)
        db.session.add(entry)
        db.session.commit()
    except Exception:
        db.session.rollback()
