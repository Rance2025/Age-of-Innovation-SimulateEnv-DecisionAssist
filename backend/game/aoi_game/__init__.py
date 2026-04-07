"""
Age of Innovation 游戏引擎
可作为库被其他项目调用
"""

from .game_engine import GameEngine
from .game_state import GameStateBase
from .utils import ActionRequest
from .utils import load_game_history, action_request, GameHistory, ActionRecord, PlayerResult

__all__ = [
    'GameEngine', 
    'GameStateBase', 
    'ActionRequest', 
    'load_game_history', 
    'action_request', 
    'GameHistory', 
    'ActionRecord', 
    'PlayerResult'  
]

__version__ = '0.1.0'
