from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..game_state import GameStateBase


@dataclass(frozen=True)
class ActionRequest:
    """
    行动请求 - 由 GameEngine 的生成器产出
    
    包含当前需要做出决策的玩家信息、可选行动列表以及完整的游戏状态，
    供前端展示或外部 AI 分析决策使用。
    
    当 is_game_over=True 时，表示游戏结束，player_id/action_type/available_actions 为 None，
    final_scores 包含最终得分，game_state 包含终局状态。
    """
    
    # ========== 下一步行动信息 ==========
    player_id: int = -1                     # 当前需要行动的玩家ID，None 表示游戏结束
    action_type: str = ''                   # 行动类型，None 表示游戏结束
    available_actions: dict[int, str] = field(default_factory=dict)  # 可选行动 {action_id: description}
    
    # ========== 游戏结束信息 ==========
    is_game_over: bool = False              # 游戏是否结束
    final_scores: dict[int, dict[str, int]] = field(default_factory=dict)  # 最终得分 {player_id: {score_type: score}}
    
    # ========== 当前游戏状态 ==========
    game_state: 'GameStateBase' = None      # 完整的游戏状态对象（终局时也返回）
