from flask import Flask, jsonify

from config import Config
from app.db import ensure_indexes, init_db
from app.utils.errors import register_error_handlers


def create_app(config_object=Config):
    app = Flask(__name__)
    app.config.from_object(config_object)

    init_db()
    ensure_indexes()

    from app.api.movies import movies_bp
    from app.api.uploads import uploads_bp
    app.register_blueprint(movies_bp)
    app.register_blueprint(uploads_bp)

    register_error_handlers(app)

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"}), 200

    return app