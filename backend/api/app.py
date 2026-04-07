"""Flask 应用创建和服务器运行"""
import os
import signal
import sys

import yaml
from flask import Flask

from backend.logger import setup_logging, get_logger
from backend.api.middleware import setup_cors, setup_error_handlers
from backend.api.routes import routes_bp

logger = get_logger(__name__)

# 全局标志，用于通知线程停止
_shutdown_requested = False


def shutdown_handler(signum, frame):
    """信号处理函数 - 优雅关闭"""
    global _shutdown_requested
    logger.info(f"收到信号 {signum}，开始关闭...")
    _shutdown_requested = True
    # 清理游戏状态
    _cleanup_game_state()
    sys.exit(0)


def _cleanup_game_state():
    """清理游戏状态"""
    try:
        # 清理游戏控制器
        from backend.game.start_game import _game_controllers, remove_game_controller
        for game_id in list(_game_controllers.keys()):
            remove_game_controller(game_id)
        logger.info("游戏状态已清理")
    except Exception as e:
        logger.error(f"清理游戏状态失败: {e}")


def register_signal_handlers():
    """注册信号处理器"""
    signal.signal(signal.SIGINT, shutdown_handler)   # Ctrl+C
    signal.signal(signal.SIGTERM, shutdown_handler)  # kill 命令
    if hasattr(signal, 'SIGBREAK'):  # Windows
        signal.signal(signal.SIGBREAK, shutdown_handler)


def load_config():
    """加载配置文件"""
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.yaml')
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def create_app() -> Flask:
    """创建 Flask 应用"""
    setup_logging()
    config = load_config()

    # 获取静态文件夹路径
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    static_folder = os.path.join(base_dir, config['paths']['static_folder'])

    app = Flask(__name__, static_folder=static_folder)

    # 配置 CORS
    setup_cors(app, config)

    # 注册错误处理器
    setup_error_handlers(app)

    # 注册蓝图
    app.register_blueprint(routes_bp)

    logger.info(f"Flask app created")
    return app


def run_app(host=None, port=None, debug=None, use_reloader=None):
    """运行 Flask 应用"""
    # 注册信号处理器
    register_signal_handlers()

    app = create_app()
    config = load_config()

    host = host or config['server']['host']
    port = port or config['server']['port']
    debug = debug if debug is not None else config['server']['debug']
    use_reloader = use_reloader if use_reloader is not None else config['server']['use_reloader']

    logger.info(f"Starting server on http://{host}:{port}")
    logger.info("按 Ctrl+C 停止服务器")

    try:
        app.run(host=host, port=port, debug=debug, use_reloader=use_reloader)
    except KeyboardInterrupt:
        logger.info("服务器已停止")
        _cleanup_game_state()
        sys.exit(0)
