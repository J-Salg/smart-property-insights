import os
from flask import Flask, send_from_directory
from app.extensions import db, migrate, cors


def create_app(config_name: str | None = None) -> Flask:
    app = Flask(__name__, static_folder="static")

    from app.config import config
    env = config_name or os.getenv("FLASK_ENV", "development")
    app.config.from_object(config[env])

    db.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}})

    from app.api.predict import predict_bp
    from app.api.health import health_bp
    app.register_blueprint(predict_bp, url_prefix="/api")
    app.register_blueprint(health_bp, url_prefix="/api")

    from app.models import prediction_log 

    @app.route("/")
    def index():
        return send_from_directory(app.static_folder, "index.html")

    return app
