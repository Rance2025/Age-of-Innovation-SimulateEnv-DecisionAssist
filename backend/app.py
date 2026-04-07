"""
后端API服务 - 应用程序入口

这是重构后的新架构入口文件，提供简洁的接口来启动和管理游戏服务。

使用方式:
    1. 直接运行: python -m backend.app
    2. 导入使用: from backend.app import create_app, run_app
"""
import os
import sys

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 配置日志
from backend.logger import setup_logging, get_logger
setup_logging()
logger = get_logger(__name__)

# 新架构导入
from backend.api.app import create_app, run_app


def create_api(host='127.0.0.1', port=5001, player_count=3, static_folder=None):
    """
    创建新的API实例 - 向后兼容

    注意: 新架构中推荐使用 create_app()
    """
    logger.warning("create_api() is deprecated, use create_app() instead")
    return create_app()


if __name__ == "__main__":
    # 测试运行
    logger.info("=" * 60)
    logger.info("Age of Innovation - Game Server")
    logger.info("=" * 60)

    logger.info("Starting server...")
    run_app()
