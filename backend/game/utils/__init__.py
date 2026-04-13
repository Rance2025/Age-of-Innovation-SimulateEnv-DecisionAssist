"""
工具模块
包含前端状态类型定义、游戏状态管理器等
"""

from .frontend_state_types import (
    ChangeType, GameMeta, TimerState, Resources, Magics, Buildings, Tracks,
    PlayerState, MapCell, MapState, ScienceTrackState, DisplayBoardState,
    GameSetup, AvailableAction, ActionHistoryEntry, FinalScore, FullGameState, StateDiff
)
from .game_state_manager import GameStateManager

__all__ = [
    'ChangeType', 'GameMeta', 'TimerState', 'Resources', 'Magics', 'Buildings', 'Tracks',
    'PlayerState', 'MapCell', 'MapState', 'ScienceTrackState', 'DisplayBoardState',
    'GameSetup', 'AvailableAction', 'ActionHistoryEntry', 'FinalScore', 'FullGameState', 'StateDiff',
    'GameStateManager'
]
