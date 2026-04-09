"""行动选择策略基类。"""

from __future__ import annotations

import random
from typing import Protocol

from ..aoi_game import ActionRequest


class RandomLike(Protocol):
    """最小随机接口，便于注入测试随机源。"""

    def choice(self, seq):
        ...

    def random(self) -> float:
        ...


class BaseActionAgent:
    """统一行动策略接口。"""

    strategy_name = "base"

    def __init__(self, rng: RandomLike | None = None):
        self._rng = rng or random

    def get_action(self, request: ActionRequest) -> int:
        """根据 ActionRequest 返回一个合法 action_id。"""
        raise NotImplementedError

    def _get_available_action_ids(self, request: ActionRequest) -> list[int]:
        if request is None:
            raise ValueError("ActionRequest cannot be None.")

        available_actions = getattr(request, "available_actions", None)
        if not isinstance(available_actions, dict) or not available_actions:
            raise ValueError("ActionRequest.available_actions is empty.")

        return list(available_actions.keys())
