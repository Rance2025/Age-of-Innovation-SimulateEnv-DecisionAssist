from GameEngine import GameEngine
from web_io import GamePanel, Silence_IO
import time

if __name__ == "__main__":
    # res = []
    # for i in range(10000):
        num_players = 3
        # 初始化网页控制台
        io = GamePanel(port=5000, player_count=num_players) # 自动启动后台服务
        io.update_global_status("=== 大创造时代游戏开始 ===")
        game_args_dict = {
            'num_players': num_players,
            'setup_mode': 'target',                         # input | random | target 
            'setup_tile_args' : (
                3,                                          # 排除的规划卡
                [2, 3, 5, 8],                               # 派系板块 (3+1=4个)
                [3, 9, 14,16],                              # 宫殿板块 (3+1=4个)
                [1, 3, 4, 7, 8, 10],                        # 回合助推板 (3+3=6个)
                [5, 3, 4, 8, 2, 6],                         # 轮次计分板块
                2,                                          # 最终计分板块
                [3, 7, 2, 6, 9, 10, 12, 1, 11, 5, 4, 8],    # 能力板块顺序
                [3, 5, 18, 7, 4, 2, 9, 11],                 # 科学板块 (2+2*3=8个
                [2, 4, 6]                                   # 书本行动板块
            ),
            'setup_player_order_args': [2, 0, 1],
            'action_history': [],
            'action_mode': 'input',                          # input | simulate | reproduce
            'web_io': io, # Silence_IO(5),
            'need_estimate': False,
        }
        # time.sleep(1)
        game_engine = GameEngine(game_args_dict)
        result = game_engine.run_game()
        print(result)
        # res.append(result)
    #     if i % 250 == 0:
    #         print('-',end=' ',flush=True)
    # print(f'万局（三人）最大总分: {max(res,key=sum)}')
    # print(f'万局（三人）第一名最高分: {max(res,key=lambda x: x[0])}')
    # print(f'万局（三人）平均总分{sum(map(sum,res))/len(res)}')
    # print(f'万局（三人）第一名平局分{sum(map(lambda x: x[0],res))/len(res)}')
        
