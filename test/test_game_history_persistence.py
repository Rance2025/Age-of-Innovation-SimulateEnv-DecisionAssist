import os
import shutil
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch


sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database.database import GameRepository
from backend.game.start_game import GameController


class CaptureRepository:
    def __init__(self):
        self.records = []

    def create_game(self, data):
        self.records.append(data)
        return len(self.records)


def build_sample_history_payload():
    return {
        "schema_version": "1.0",
        "started_at": "2026-04-28T10:00:00+08:00",
        "ended_at": "2026-04-28T10:12:34+08:00",
        "end_status": "finished",
        "error_message": None,
        "num_players": 3,
        "game_mode": "standard",
        "path_length": 1,
        "requested_config": {
            "game_mode": "standard",
            "timer_mode": "standard",
            "timer_config": {
                "main_time": 2700000,
                "byo_yomi_time": 45000,
                "grace_period": 300,
                "timeout_strategy": "random_fast_action",
            },
            "init_settings": {
                "init_player_order": "random",
                "setup_tiles": {
                    "planning_cards": "random",
                    "factions": "random",
                    "palace_tiles": "random",
                    "round_boosters": "random",
                    "round_scoring": "random",
                    "final_scoring": "random",
                    "ability_tiles": "random",
                    "science_tiles": "random",
                    "book_actions": "random",
                },
            },
        },
        "resolved_config": {
            "timer": {
                "main_time": 2700000,
                "byo_yomi_time": 45000,
                "grace_period": 300,
                "timeout_strategy_name": "random_fast_action",
            },
            "setup": {
                "init_player_order": [2, 0, 1],
                "setup_tiles": {
                    "planning_cards": [1, 4, 7],
                    "factions": [3, 8, 12],
                    "palace_tiles": [2, 5, 9],
                    "round_boosters": [1, 2, 6, 7],
                    "round_scoring": [3, 5, 2, 1, 6, 4],
                    "final_scoring": 2,
                    "ability_tiles": [4, 7, 1, 9, 2, 6],
                    "science_tiles": [3, 8, 5, 1, 7, 2],
                    "book_actions": [2, 4, 1],
                },
            },
        },
        "players": [
            {"player_id": 0, "player_type": "human", "player_input_id": "player-1", "strategy_name": ""},
            {"player_id": 1, "player_type": "ai", "player_input_id": "", "strategy_name": "random_pure"},
            {"player_id": 2, "player_type": "human", "player_input_id": "player-3", "strategy_name": ""},
        ],
        "action_history": [
            {
                "player_id": 1,
                "action_type": "normal",
                "action_id": 11,
                "selection_mode": "ai_agent",
                "strategy_name": "random_pure",
                "duration_ms": 1234,
                "player_remaining_ms": 456000,
            }
        ],
        "final_player_remaining_ms": [523000, 0, 18000],
        "final_scores": {
            "0": {"total": 132, "board": 48, "chain": 22, "track": 41, "resource": 21},
            "1": {"total": 126, "board": 46, "chain": 19, "track": 39, "resource": 22},
            "2": {"total": 118, "board": 43, "chain": 18, "track": 35, "resource": 22},
        },
    }


class GameHistoryRepositoryTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            ".tmp-test-artifacts",
            "game-history-tests",
        )
        os.makedirs(self.temp_dir, exist_ok=True)
        self.db_path = os.path.join(self.temp_dir, "game_history_test.db")
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        GameRepository._instance = None
        self.config_patcher = patch(
            "backend.database.database.load_config",
            return_value={"paths": {"db_path": self.db_path}},
        )
        self.config_patcher.start()
        self.repo = GameRepository()

    def tearDown(self):
        self.config_patcher.stop()
        GameRepository._instance = None
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_repository_round_trip_preserves_new_history_payload(self):
        payload = build_sample_history_payload()

        game_id = self.repo.create_game(payload)
        game = self.repo.get_game(game_id)

        self.assertEqual(game["end_status"], "finished")
        self.assertEqual(game["game_mode"], "standard")
        self.assertEqual(game["requested_config"]["timer_mode"], "standard")
        self.assertEqual(game["requested_config"]["timer_config"]["main_time"], 2700000)
        self.assertEqual(game["resolved_config"]["timer"]["timeout_strategy_name"], "random_fast_action")
        self.assertEqual(game["players"][1]["player_id"], 1)
        self.assertEqual(game["players"][0]["player_input_id"], "player-1")
        self.assertEqual(game["players"][1]["strategy_name"], "random_pure")
        self.assertEqual(game["action_history"][0]["selection_mode"], "ai_agent")
        self.assertEqual(game["action_history"][0]["strategy_name"], "random_pure")
        self.assertEqual(game["final_player_remaining_ms"], [523000, 0, 18000])
        self.assertNotIn("setup_mode", game)
        self.assertNotIn("created_at", game)
        self.assertNotIn("player_results", game)


class GameControllerHistoryPersistenceTest(unittest.TestCase):
    def build_controller(self):
        controller = GameController(
            "test-game",
            3,
            {
                "main_time": 2700000,
                "byo_yomi_time": 45000,
                "grace_period": 300,
                "timeout_strategy": "random_fast_action",
            },
        )
        controller._history_repository = CaptureRepository()
        controller._history_saved = False
        controller._started_at_iso = "2026-04-28T10:00:00+08:00"
        controller._original_init_settings = build_sample_history_payload()["requested_config"]["init_settings"]
        controller._resolved_init_settings = build_sample_history_payload()["resolved_config"]["setup"]
        controller._requested_game_payload = {
            "num_players": 3,
            "game_mode": {"type": "standard"},
            "timer_config": {
                "main_time": 2700000,
                "byo_yomi_time": 45000,
                "grace_period": 300,
                "timeout_strategy": "random_fast_action",
            },
            "players": [
                {"type": "human", "args": "player-1"},
                {"type": "ai", "args": "random_pure"},
                {"type": "human", "args": "player-3"},
            ],
            "init_settings": build_sample_history_payload()["requested_config"]["init_settings"],
        }
        controller._player_remaining_times = [523000, 0, 18000]
        controller.final_scores = build_sample_history_payload()["final_scores"]
        controller.state_manager = SimpleNamespace(
            get_full_state=lambda: {
                "state": {
                    "action_history": build_sample_history_payload()["action_history"]
                }
            }
        )
        return controller

    def test_finished_history_save_uses_single_record_payload(self):
        controller = self.build_controller()

        controller._save_game_history("finished")

        self.assertEqual(len(controller._history_repository.records), 1)
        saved = controller._history_repository.records[0]
        self.assertEqual(saved["end_status"], "finished")
        self.assertEqual(saved["players"][0]["player_input_id"], "player-1")
        self.assertEqual(saved["action_history"][0]["selection_mode"], "ai_agent")
        self.assertEqual(saved["players"][1]["strategy_name"], "random_pure")

    def test_stop_saves_interrupted_history(self):
        controller = self.build_controller()
        controller.is_running = True

        controller.stop()

        self.assertEqual(len(controller._history_repository.records), 1)
        saved = controller._history_repository.records[0]
        self.assertEqual(saved["end_status"], "interrupted")

    def test_error_history_save_keeps_error_message(self):
        controller = self.build_controller()

        controller._save_game_history("error", error_message="boom")

        self.assertEqual(len(controller._history_repository.records), 1)
        saved = controller._history_repository.records[0]
        self.assertEqual(saved["end_status"], "error")
        self.assertEqual(saved["error_message"], "boom")


if __name__ == "__main__":
    unittest.main()
