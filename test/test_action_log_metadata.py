import os
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch


sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.game.start_game import GameController
from backend.game.utils.game_state_manager import GameStateManager


class DummyAgent:
    strategy_name = "random_pure"

    def get_action(self, request):
        return 7


class TimeoutAgent:
    strategy_name = "random_fast_action"

    def get_action(self, request):
        return 11


class ActionLogMetadataTest(unittest.TestCase):
    def test_game_state_manager_records_strategy_name_without_selection_source(self):
        manager = GameStateManager()

        manager.record_action_selection_metadata(
            raw_action_index=1,
            strategy_name="random_fast_action",
            selection_mode="strategy_execute",
        )

        entry = manager._build_action_history_action_entry(
            record=[0, "normal", 11],
            detailed_actions={11: {"description": "test action", "action": "test"}},
            stage_key="round-1",
            raw_action_index=1,
        )

        self.assertEqual(entry.selection_mode, "strategy_execute")
        self.assertEqual(entry.strategy_name, "random_fast_action")
        self.assertFalse(hasattr(entry, "selection_source"))

    def test_ai_agent_action_uses_ai_agent_mode(self):
        controller = GameController("test-game", 3)
        controller._agents[0] = DummyAgent()

        request = SimpleNamespace(
            player_id=0,
            available_actions={7: "do something"},
        )

        with patch("backend.game.start_game.time.sleep", return_value=None):
            action_id, metadata = controller._resolve_action_decision(request, 0)

        self.assertEqual(action_id, 7)
        self.assertEqual(metadata["selection_mode"], "ai_agent")
        self.assertEqual(metadata["strategy_name"], "random_pure")
        self.assertNotIn("selection_source", metadata)

    def test_timeout_action_uses_timeout_agent_mode(self):
        controller = GameController("test-game", 3)
        controller.current_request = SimpleNamespace(
            available_actions={11: "timeout action"},
        )
        controller._timeout_strategy = "random_fast_action"

        with patch("backend.game.start_game.create_action_agent", return_value=TimeoutAgent()):
            payload = controller._execute_timeout_action(0)

        self.assertEqual(payload["action_id"], 11)
        self.assertEqual(payload["selection_mode"], "timeout_agent")
        self.assertEqual(payload["strategy_name"], "random_fast_action")
        self.assertNotIn("selection_source", payload)


if __name__ == "__main__":
    unittest.main()
