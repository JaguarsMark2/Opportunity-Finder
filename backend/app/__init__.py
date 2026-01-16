import os
import sys

from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings


def create_app(test_config: bool = False) -> Flask:
    """Create and configure Flask application.

    Args:
        test_config: Whether to use test configuration

    Returns:
        Configured Flask application
    """
    app = Flask(__name__)

    # Load configuration
    app.config.from_object(settings)
    if test_config:
        app.config["TESTING"] = True

    # JWT Configuration
    app.config["JWT_SECRET_KEY"] = settings.SECRET_KEY
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = settings.JWT_ACCESS_TOKEN_EXPIRES
    app.config["JWT_REFRESH_TOKEN_EXPIRES"] = settings.JWT_REFRESH_TOKEN_EXPIRES
    app.config["JWT_TOKEN_LOCATION"] = ["headers"]
    app.config["JWT_HEADER_NAME"] = "Authorization"
    app.config["JWT_HEADER_TYPE"] = "Bearer"

    # Initialize extensions
    CORS(app, origins=[settings.FRONTEND_URL])
    jwt = JWTManager(app)
    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"],
    )
    limiter.init_app(app)

    # Register blueprints
    from app.api.admin import admin_bp
    from app.api.auth import auth_bp
    from app.api.opportunities import opportunities_bp
    from app.api.payments import payments_bp
    from app.api.scan import scan_bp
    from app.api.scoring import scoring_bp
    from app.api.user import user_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(scoring_bp)
    app.register_blueprint(opportunities_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(scan_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(payments_bp)

    # JWT error handlers
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({'error': 'Token has expired'}), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({'error': 'Invalid token'}), 401

    @jwt.unauthorized_loader
    def unauthorized_callback(error):
        return jsonify({'error': 'Missing authorization header'}), 401

    # Health check endpoint
    @app.route("/health")
    def health_check():
        return {"status": "healthy", "service": "opportunity-finder"}, 200

    return app
