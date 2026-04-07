"""日志配置"""
import logging
import sys


def setup_logging(level=logging.INFO):
    """设置日志"""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    logging.getLogger('werkzeug').setLevel(logging.ERROR)
    logging.getLogger('sqlalchemy').setLevel(logging.WARNING)


def get_logger(name):
    """获取日志记录器"""
    return logging.getLogger(name)
