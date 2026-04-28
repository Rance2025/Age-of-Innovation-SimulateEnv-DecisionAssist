import os
import sys
import unittest


sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.game.aoi_game.game_engine import GameEngine


def build_engine():
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
    engine = GameEngine(3, init_settings)
    game_state = engine.game_state

    for player in game_state.players:
        player.controlled_map_ids = set()
        player.settlements_and_cities = {}
        player.chainscore = 0
        player.trackscore = 0
        player.resourcescore = 0
        player.boardscore = 20
        player.navigation_level = 0
        player.temp_navigation = False
        player.faction_id = 1
        player.palace_tile_id = 1
        player.is_got_palace = False
        player.tracks = {
            "bank": 0,
            "law": 0,
            "engineering": 0,
            "medical": 0,
        }
        player.magics = {1: 0, 2: 0, 3: 0}
        player.resources.update(
            {
                "money": 0,
                "ore": 0,
                "meeples": 0,
                "bank_book": 0,
                "law_book": 0,
                "engineering_book": 0,
                "medical_book": 0,
            }
        )

    for i in range(9):
        for j in range(13):
            game_state.map_board_state.map_grid[i][j][1] = -1
            game_state.map_board_state.map_grid[i][j][2] = 0
            game_state.map_board_state.map_grid[i][j][3] = 0
            game_state.map_board_state.map_grid[i][j][4] = False

    return game_state


def add_building(game_state, player_id, pos, root=None):
    i, j = pos
    game_state.map_board_state.map_grid[i][j][1] = player_id
    game_state.map_board_state.map_grid[i][j][2] = 1
    game_state.players[player_id].controlled_map_ids.add(pos)
    game_state.players[player_id].settlements_and_cities[pos] = [root or pos, False]


class LargestChainScoringTest(unittest.TestCase):
    def test_navigation_level_one_connects_chains_across_one_water_hex(self):
        game_state = build_engine()

        add_building(game_state, 0, (0, 0))
        add_building(game_state, 0, (0, 2))
        game_state.players[0].navigation_level = 1
        add_building(game_state, 1, (2, 0))
        add_building(game_state, 2, (2, 2))

        final_scores = game_state.calculate_players_total_score()

        self.assertEqual(final_scores[0]["chain"], 18)
        self.assertEqual(final_scores[1]["chain"], 9)
        self.assertEqual(final_scores[2]["chain"], 9)

    def test_single_root_chain_counts_toward_final_scoring(self):
        game_state = build_engine()

        add_building(game_state, 0, (0, 2), (0, 2))
        add_building(game_state, 0, (1, 3), (0, 2))
        add_building(game_state, 1, (4, 0))
        add_building(game_state, 2, (6, 0))

        final_scores = game_state.calculate_players_total_score()

        self.assertEqual(final_scores[0]["chain"], 18)
        self.assertEqual(final_scores[1]["chain"], 9)
        self.assertEqual(final_scores[2]["chain"], 9)


if __name__ == "__main__":
    unittest.main()
