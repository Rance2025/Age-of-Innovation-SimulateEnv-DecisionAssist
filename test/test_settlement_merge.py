import os
import sys
import unittest


sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.game.aoi_game.game_engine import GameEngine


def build_map_board_state():
    init_settings = {
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
    }
    return GameEngine(3, init_settings).game_state.map_board_state


class SettlementMergeTest(unittest.TestCase):
    def test_city_root_remains_root_when_merging_non_city_into_city(self):
        map_board_state = build_map_board_state()
        settlements_and_cities = {
            (0, 0): [(0, 0), True],
            (0, 2): [(0, 2), False],
        }

        merged_root, merged_is_city = map_board_state.merge_settlement_root(
            settlements_and_cities, (0, 0), (0, 2)
        )

        self.assertEqual(merged_root, (0, 0))
        self.assertTrue(merged_is_city)
        self.assertEqual(
            map_board_state.find_settlement_root(settlements_and_cities, (0, 2)),
            ((0, 0), True),
        )

    def test_city_root_remains_root_when_city_is_second_argument(self):
        map_board_state = build_map_board_state()
        settlements_and_cities = {
            (0, 0): [(0, 0), False],
            (0, 2): [(0, 2), True],
        }

        merged_root, merged_is_city = map_board_state.merge_settlement_root(
            settlements_and_cities, (0, 0), (0, 2)
        )

        self.assertEqual(merged_root, (0, 2))
        self.assertTrue(merged_is_city)
        self.assertEqual(
            map_board_state.find_settlement_root(settlements_and_cities, (0, 0)),
            ((0, 2), True),
        )


if __name__ == "__main__":
    unittest.main()
