"""快速行动优化随机策略。"""

from __future__ import annotations

from ..aoi_game import ActionRequest
from .base import BaseActionAgent


class FastActionRandomAgent(BaseActionAgent):
    """
    当候选行动中包含快速行动时优先偏向它，否则退化为普通随机。

    默认规则：
    - 候选中包含 action_id=65 时，以 85% 概率直接选择 65
    - 若未命中 65，则只在其余候选中随机
    - 若候选只有 65，则直接返回 65
    """

    strategy_name = "random_fast_action"

    def __init__(
        self,
        fast_action_id: int = 65,
        fast_action_probability: float = 0.85,
        rng=None,
    ):
        super().__init__(rng=rng)

        if not 0 <= fast_action_probability <= 1:
            raise ValueError("fast_action_probability must be between 0 and 1.")

        self.fast_action_id = fast_action_id
        self.fast_action_probability = fast_action_probability

    def get_action(self, request: ActionRequest) -> int:
        action_ids = self._get_available_action_ids(request)

        if self.fast_action_id not in action_ids:
            return self._rng.choice(action_ids)

        if len(action_ids) == 1:
            return self.fast_action_id

        if self._rng.random() < self.fast_action_probability:
            return self.fast_action_id

        other_action_ids = [
            action_id
            for action_id in action_ids
            if action_id != self.fast_action_id
        ]
        return self._rng.choice(other_action_ids)
