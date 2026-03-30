import os
from flask import Flask

from server.config import FACE_DIR
from server.routes import routes
from server.storage import cleanup_old_data
from server.vision import ensure_model_ready


def create_app() -> Flask:
    app = Flask(__name__)
    app.register_blueprint(routes)
    return app


if __name__ == "__main__":
    os.makedirs(FACE_DIR, exist_ok=True)
    cleanup_old_data()
    ensure_model_ready()
    app = create_app()
    app.run(host="127.0.0.1", port=5000, debug=True)
