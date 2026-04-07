"""
测试 simulate 功能的脚本
与 game_log.json 做交叉检验
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.game import simulate, load_game_history, SimulationConfig

if __name__ == "__main__":
    
    times = 10000
    num_players = 3

    # 获取测试数据文件的绝对路径
    test_dir = os.path.dirname(os.path.abspath(__file__))
    game_history_path = os.path.join(test_dir, 'game_log_test.json')
    
    game_history = load_game_history(game_history_path)
    init_settings = game_history.init_settings
    simulation_path = game_history.action_history

    # 使用 SimulationConfig 配置模拟参数
    config = SimulationConfig(
        times=times,
        num_players=num_players,
        # init_settings=init_settings,
        # simulation_path=simulation_path,
        # seed_id=[1775058399499152]
    )

    data = simulate(config)

    print(f'耗时{data["time_spend"]:.2f}秒')
    print(f'{times}局（{num_players}人）第1名分数均值:{data["mean_value"]:.2f}，标准差:{data["std_value"]:.2f}')
    data['chart'].show()
