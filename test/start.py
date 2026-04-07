from aoi_game import GameEngine


def main():
    import random
    init_settings = {
        'init_player_order': 'random',
        'setup_tiles': {
            'planning_cards': 'random',
            'factions': 'random',
            'palace_tiles': 'random',
            'round_boosters': 'random',
            'round_scoring': 'random',
            'final_scoring': 'random',
            'ability_tiles': 'random',
            'science_tiles': 'random',
            'book_actions': 'random',
        }
    }

    # 创建游戏引擎并启动游戏
    game = GameEngine(num_players=3, init_settings=init_settings).run_game()

    # 获取初始请求
    request = next(game)

    # 游戏主循环
    while not request.is_game_over:
        print(f"\n【第{request.game_state.round}轮】玩家{request.player_id + 1}的回合")
        print(f"行动类型: {request.action_type}")
        print("可用行动:")
        for action_id, description in request.available_actions.items():
            print(f"  {action_id}: {description}")
        
        # 获取玩家输入并发送
        input_str = input("选择行动ID: ")
        if input_str:
            action_id = int(input_str)
        else:
            action_id = random.choice(list(request.available_actions.keys()))
            print(action_id,end='')
        request = game.send(action_id)

    # 游戏结束，显示最终得分
    print("\n=== 游戏结束 ===")
    for player_id, score in request.final_scores.items():
        print(f"玩家{player_id + 1}: {score}分")
