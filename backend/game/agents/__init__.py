"""行动选择策略包。"""

from .base import BaseActionAgent
from .fast_action_random_agent import FastActionRandomAgent
from .random_agent import RandomAgent

ACTION_AGENT_FACTORIES = {
    "random_pure": RandomAgent,
    "random_fast_action": FastActionRandomAgent,
}


def create_action_agent(strategy_id: str) -> BaseActionAgent:
    """根据策略 ID 创建对应策略对象。"""
    normalized_strategy_id = strategy_id.strip() if isinstance(strategy_id, str) else ""
    agent_class = ACTION_AGENT_FACTORIES.get(normalized_strategy_id)
    if agent_class is None:
        raise ValueError(f"Unsupported strategy_id: {strategy_id}")
    return agent_class()


__all__ = [
    "BaseActionAgent",
    "RandomAgent",
    "FastActionRandomAgent",
    "ACTION_AGENT_FACTORIES",
    "create_action_agent",
]
