"""Flask application factory (Phase 10)."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, jsonify
from flask_cors import CORS

from backend.config import DEFAULT_PAGE_SIZE
from backend.routes.activities import bp as activities_bp
from backend.routes.analytics import bp as analytics_bp
from backend.routes.review import bp as review_bp
from backend.routes.collection import bp as collection_bp
from backend.routes.query import bp as query_bp
from backend.routes.admin import bp as admin_bp
from backend.routes.auth import bp as auth_bp
from backend.routes.linkedin_public import bp as linkedin_bp
from backend.routes.linkedin_admin import bp as linkedin_admin_bp


def create_app(config=None):
    app = Flask(__name__)
    app.config.update(dict(
        JSON_SORT_KEYS=False,
        DEFAULT_PAGE_SIZE=DEFAULT_PAGE_SIZE,
    ))
    if config:
        app.config.update(config)

    CORS(app, resources={r"/api/*": {"origins": "*"}})

    app.register_blueprint(activities_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(review_bp)
    app.register_blueprint(collection_bp)
    app.register_blueprint(query_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(linkedin_bp)
    app.register_blueprint(linkedin_admin_bp)

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok"})

    @app.errorhandler(404)
    def not_found(_e):
        return jsonify({"error": "not found"}), 404

    @app.errorhandler(500)
    def server_error(e):
        app.logger.exception("unhandled error: %s", e)
        return jsonify({"error": "internal server error"}), 500

    @app.errorhandler(ValueError)
    def bad_value(e):
        return jsonify({"error": str(e)}), 400

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)