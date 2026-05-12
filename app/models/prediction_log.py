from datetime import datetime
from app.extensions import db


class PredictionLog(db.Model):
    __tablename__ = "prediction_logs"

    id = db.Column(db.Integer, primary_key=True)
    prediction_type = db.Column(db.String(20), nullable=False)  
    inputs = db.Column(db.JSON, nullable=False)
    outputs = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "prediction_type": self.prediction_type,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "created_at": self.created_at.isoformat(),
        }
