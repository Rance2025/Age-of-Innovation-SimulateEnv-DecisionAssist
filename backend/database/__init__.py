"""
数据库模块
管理游戏历史记录
"""

from .database import GameRepository, DatabaseManager, get_db_instance

__all__ = ['GameRepository', 'DatabaseManager', 'get_db_instance']
