"""
游戏历史记录模块
包含数据模型、加载器和记录器
"""

import json
import os
from dataclasses import dataclass, field
from typing import List, Dict


# ========== 数据模型 ==========

@dataclass
class ActionRecord:
    """
    行动记录数据模型
    表示一个玩家的单次行动 [player_id, action_type, action_id]
    """
    player_id: int      # 玩家ID (0, 1, 2)
    action_type: str    # 行动类型 ("normal", "immediate" 等)
    action_id: int      # 行动ID

    @classmethod
    def from_list(cls, data: list) -> "ActionRecord":
        """从列表创建 ActionRecord 对象"""
        return cls(
            player_id=data[0],
            action_type=data[1],
            action_id=data[2]
        )

    def to_list(self) -> list:
        """转换为列表格式"""
        return [self.player_id, self.action_type, self.action_id]


@dataclass
class PlayerResult:
    """
    玩家结果数据模型
    包含玩家的各项得分
    """
    total: int      # 总分
    board: int      # 版图得分
    chain: int      # 连锁得分
    track: int      # 轨道得分
    resource: int   # 资源得分

    @classmethod
    def from_dict(cls, data: dict) -> "PlayerResult":
        """从字典创建 PlayerResult 对象"""
        return cls(
            total=data["total"],
            board=data["board"],
            chain=data["chain"],
            track=data["track"],
            resource=data["resource"]
        )

    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "total": self.total,
            "board": self.board,
            "chain": self.chain,
            "track": self.track,
            "resource": self.resource
        }


@dataclass
class GameHistory:
    """
    游戏历史记录数据模型
    与 game_log.json 结构完全一致
    """
    timestamp: str                          # ISO 格式时间戳
    num_players: int                        # 玩家数量
    init_settings: dict                     # 初始化设置，包含 init_player_order 和 setup_tiles
    action_history: List[ActionRecord] = field(default_factory=list)  # 行动历史
    result: Dict[str, PlayerResult] = field(default_factory=dict)  # 最终结果，键为玩家ID字符串

    @classmethod
    def from_dict(cls, data: dict) -> "GameHistory":
        """从字典创建 GameHistory 对象"""
        # 解析 action_history 字段
        action_history_data = data.get("action_history", [])
        action_history = [ActionRecord.from_list(item) for item in action_history_data]

        # 解析 result 字段
        result_data = data.get("result", {})
        result = {}
        for player_id, player_result in result_data.items():
            result[player_id] = PlayerResult.from_dict(player_result)

        return cls(
            timestamp=data["timestamp"],
            num_players=data["num_players"],
            init_settings=data["init_settings"],
            action_history=action_history,
            result=result
        )

    def to_dict(self) -> dict:
        """转换为字典格式（与 JSON 结构一致）"""
        return {
            "timestamp": self.timestamp,
            "num_players": self.num_players,
            "init_settings": self.init_settings,
            "action_history": [item.to_list() for item in self.action_history],
            "result": {k: v.to_dict() for k, v in self.result.items()}
        }


# ========== 加载器 ==========

def load_game_history(filepath: str) -> GameHistory:
    """
    从 JSON 文件加载游戏历史记录

    Args:
        filepath: JSON 文件绝对路径

    Returns:
        GameHistory 对象
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return GameHistory.from_dict(data)


# ========== 记录器 (预留) ==========

# TODO: 实现游戏历史记录器
# class GameHistoryRecorder:
#     pass
