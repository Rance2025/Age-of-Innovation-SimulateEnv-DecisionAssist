"""完全随机策略。"""

from __future__ import annotations

from ..aoi_game import ActionRequest
from .base import BaseActionAgent


class RandomAgent(BaseActionAgent):
    """从当前所有合法行动中等概率随机选择。"""

    strategy_name = "random_pure"

    def get_action(self, request: ActionRequest) -> int:
        action_ids = self._get_available_action_ids(request)
        return self._rng.choice(action_ids)
