"""
Age of Innovation TableTopGame AI
一个用于《Age of Innovation》桌游的模拟和分析工具
"""

from .aoi_game import GameEngine, GameStateBase, ActionRequest, load_game_history, GameHistory, ActionRecord, PlayerResult
from .simulate import simulate, SimulationConfig
from .utils import GameStateManager

__all__ = ['GameEngine', 'GameStateBase', 'ActionRequest', 'load_game_history', 'GameHistory', 'ActionRecord', 'PlayerResult', 'simulate', 'SimulationConfig', 'GameStateManager']

__version__ = '0.1.0'
