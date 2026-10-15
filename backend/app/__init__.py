import os
from pathlib import Path
from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
from .config import Config
from .database import init_db
from .routes import auth_bp, api_bp

def create_app():
    root_dir = Path(__file__).resolve().parent.parent.parent

    app = Flask(
        __name__,
        static_folder=str(root_dir),
        static_url_path=""
    )
    app.config.from_object(Config)

    # Enable CORS for frontend integration
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Register API blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(api_bp)

    # Serve index.html at root
    @app.route("/")
    def index():
        return send_from_directory(str(root_dir), "index.html")

    # Serve any other static files
    @app.route("/<path:path>")
    def static_proxy(path):
        target = root_dir / path
        if target.exists() and target.is_file():
            return send_from_directory(str(root_dir), path)
        return send_from_directory(str(root_dir), "index.html")

    # Global 404 handler for API routes
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Resource not found", "code": "NOT_FOUND"}), 404

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"error": "Internal server error occurred", "code": "SERVER_ERROR"}), 500

    # Initialize tables
    with app.app_context():
        init_db()

    return app
