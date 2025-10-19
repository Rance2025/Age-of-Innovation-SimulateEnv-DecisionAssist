from GameEngine import GameEngine

# 测试游戏运行
if __name__ == "__main__":
    print("=== 大创造时代游戏开始 ===")
    num_players = 3
    game_engine = GameEngine(num_players)
    game_engine.run_game()
    game_engine.show_players_state()