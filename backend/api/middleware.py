"""中间件 - CORS 和错误处理"""
from flask_cors import CORS
from flask import jsonify

from backend.logger import get_logger

logger = get_logger(__name__)


def setup_cors(app, config):
    """配置 CORS"""
    CORS(app, resources={
        r"/*": {
            "origins": config['cors']['origins'],
            "methods": config['cors']['methods'],
            "allow_headers": config['cors']['headers']
        }
    })


def setup_error_handlers(app):
    """设置错误处理器"""

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({'error': 'Bad request', 'message': str(error)}), 400

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not found', 'message': str(error)}), 404

    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal server error: {str(error)}")
        return jsonify({'error': 'Internal server error', 'message': str(error)}), 500

    @app.errorhandler(Exception)
    def handle_exception(error):
        logger.error(f"Unhandled exception: {str(error)}")
        return jsonify({'error': 'Internal server error', 'message': str(error)}), 500
