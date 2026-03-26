import sys
import os

# 添加backend目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend'))

from GameEngine import GameEngine
from web_io import GamePanel, Silence_IO

def main(
    mode = 'full_human',                # 全局模式（full_human | random_simulate | one_ai_and_other_random_simulate)
    num_players = 3,                    # 玩家数（3 ~ 5)
    setup_mode = 'random',              # 初始设置模式（可选：random | target | input)

    # 以下为仅当 setup_mode 等于 target 时生效的参数

    setup_tile_args:tuple = tuple(),    # 初始效果板块指定
    setup_player_order_args:list = [],  # 初始玩家顺序指定
    
    # 以下为仅当 mode 等于 random_simulate 时生效的参数
    
    times = 1000,                       # 模拟次数
    simulation_path:list = [],          # 模拟路径指定
    expect_result = 'first_one',        # 期望结果
    need_chart = True,                  # 是否需要图表
):
    
    match mode:
        case 'full_human':
            # 初步排错
            match setup_mode:
                case 'random':
                    pass
                case 'target':
                    if not setup_tile_args:
                        raise Exception('全人类模式中采用指定初始模式下，效果板块参数为空')
                    if len(setup_tile_args) != 9:
                        raise Exception('全人类模式中采用指定初始模式下，效果板块参数长度填写不足')
                    if (
                        type(setup_tile_args[0]) != int
                        or any(type(setup_tile_args[i]) != list for i in range(1,9) if i != 5)
                        or type(setup_tile_args[5]) != int
                    ):
                        raise Exception('全人类模式中采用指定初始模式下，效果板块参数中一个或多个位置的元素类型不合法')
                    if not setup_player_order_args:
                        raise Exception('全人类模式中采用指定初始模式下，玩家初始顺序参数为空')
                    if len(setup_player_order_args) != num_players:
                        raise Exception('全人类模式中采用指定初始模式下，玩家初始顺序参数长度与玩家数不一致')
                    if len(set(setup_player_order_args)) != num_players:
                        raise Exception('全人类模式中采用指定初始模式下，玩家初始顺序参数中存在重复值')
                    if any(player_idx not in setup_player_order_args for player_idx in range(num_players)):
                        raise Exception('全人类模式中采用指定初始模式下，玩家初始顺序参数中存在非法值')
                case 'input':
                    pass
                case _:
                    raise Exception('在全人类模式中采用不合法的初始设置模式（合法模式仅有input、random和target)')
                
            # 初始化网页控制台
            io = GamePanel(port=5001, player_count=num_players) # 自动启动后台服务
            io.update_global_status("=== 大创造时代游戏开始 ===")
            game_args_dict = {
                'num_players': num_players,
                'setup_mode': setup_mode,                           # input | random | target 
                'setup_tile_args' : setup_tile_args,
                'setup_player_order_args': setup_player_order_args,
                'action_history': [],
                'simulation_path': [],
                'remaining_path_length': 0,
                'action_mode': ['human'] * num_players,             # human | random_simulate | reproduce
                'web_io': io,                                       # Silence_IO() | io,
                'need_estimate': False,
            }
            game_engine = GameEngine(game_args_dict)
            result = game_engine.run_game()

            from GameHistoryRecorder import save_game_history
            save_game_history(game_args_dict, result)
            print(result)
        
        case 'random_simulate':
            # 初步排错
            match setup_mode:
                case 'random':
                    pass
                case 'target':
                    if not setup_tile_args:
                        raise Exception('在完全随机模拟中采用指定初始模式下，效果板块参数为空')
                    if len(setup_tile_args) != 9:
                        raise Exception('在完全随机模拟中采用指定初始模式下，效果板块参数长度填写不足')
                    if (
                        type(setup_tile_args[0]) != int
                        or any(type(setup_tile_args[i]) != list for i in range(1,9) if i != 5)
                        or type(setup_tile_args[5]) != int
                    ):
                        raise Exception('在完全随机模拟中采用指定初始模式下，效果板块参数中一个或多个位置的元素类型不合法')
                    if not setup_player_order_args:
                        raise Exception('在完全随机模拟中采用指定初始模式下，玩家初始顺序参数为空')
                    if len(setup_player_order_args) != num_players:
                        raise Exception('在完全随机模拟中采用指定初始模式下，玩家初始顺序参数长度与玩家数不一致')
                    if len(set(setup_player_order_args)) != num_players:
                        raise Exception('在完全随机模拟中采用指定初始模式下，玩家初始顺序参数中存在重复值')
                    if any(player_idx not in setup_player_order_args for player_idx in range(num_players)):
                        raise Exception('在完全随机模拟中采用指定初始模式下，玩家初始顺序参数中存在非法值')
                case _:
                    raise Exception('在完全随机模拟中采用不合法的初始设置模式（合法模式仅有random和target)')
            
            import time
            import numpy as np
            from tqdm import tqdm

            result_list = []
            start_time = time.time()

            for _ in tqdm(range(times), desc="模拟进度"):
                game_args_dict = {
                    'num_players': num_players,
                    'setup_mode': setup_mode,                                   # input | random | target 
                    'setup_tile_args' : setup_tile_args,
                    'setup_player_order_args': setup_player_order_args,
                    'action_history': [],
                    'simulation_path': simulation_path,
                    'remaining_path_length': len(simulation_path),
                    'action_mode': ['random_simulate'] * num_players,           # human | random_simulate | reproduce
                    'web_io': Silence_IO(),
                    'need_estimate': False,
                }
                game_engine = GameEngine(game_args_dict)
                result = game_engine.run_game()
            
                result_list.append(result)

            end_time = time.time()
            time_spend = end_time - start_time
            print(f'耗时{time_spend:.2f}秒')

            match expect_result:
                case 'first_one':
                    def transform(result: dict):
                        return sorted(list(map(lambda x:x['total'], result.values())), reverse=True)[0]
                    analysed_result_list = list(map(transform, result_list))

            # 计算平均数和标准差
            mean_value = np.mean(analysed_result_list)  # 平均数
            std_value = np.std(analysed_result_list)     # 总体标准差
            
            print(f'{times}局（{num_players}人）第一名分数均值:{mean_value}，标准差:{std_value}')
            
            returned_data = {
                'all_result_list': result_list,
                'analysed_result_list': analysed_result_list,
                'time_spend': time_spend,
                'mean_value': mean_value,
                'std_value': std_value,
            }

            if need_chart == True:
                # 定义图表绘制函数
                def get_chart(data):
                    import matplotlib.pyplot as plt
                    from scipy import stats  # 用于正态分布曲线
                            
                    # 方法1: 使用系统自带的中文字体
                    plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS', 'DejaVu Sans']
                    plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

                    # 计算统计量
                    mean_value = np.mean(data)
                    median_value = np.median(data)
                    std_value = np.std(data)
                    min_value = np.min(data)
                    max_value = np.max(data)
                    percentile_25 = np.percentile(data, 25)
                    percentile_75 = np.percentile(data, 75)

                    # 创建图表
                    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

                    # 1. 直方图 + 密度曲线
                    ax1.hist(data, bins=40, edgecolor='black', alpha=0.7, density=True, color='skyblue')
                    ax1.axvline(mean_value, color='red', linewidth=2, label=f'均值: {mean_value:.2f}')
                    ax1.axvline(median_value, color='green', linewidth=2, label=f'中位数: {median_value:.2f}')
                    ax1.axvspan(percentile_25, percentile_75, alpha=0.2, color='yellow', label='25%-75%分位区间')

                    # 添加正态分布曲线参考
                    x = np.linspace(min_value, max_value, 1000)
                    pdf = stats.norm.pdf(x, mean_value, std_value)
                    ax1.plot(x, pdf, 'r-', lw=2, label='正态分布参考')

                    ax1.set_title('数据分布直方图', fontsize=14)
                    ax1.set_xlabel('数值', fontsize=12)
                    ax1.set_ylabel('密度', fontsize=12)
                    ax1.legend()
                    ax1.grid(True, alpha=0.3)

                    # 2. 箱线图
                    ax2.boxplot(data, vert=True, patch_artist=True)
                    ax2.set_title('数据箱线图', fontsize=14)
                    ax2.set_ylabel('数值', fontsize=12)
                    ax2.grid(True, alpha=0.3)

                    # 添加统计信息文本
                    stats_text = f"""
                    统计信息:
                    数量: {len(data):,}
                    均值: {mean_value:.2f}
                    中位数: {median_value:.2f}
                    标准差: {std_value:.2f}
                    最小值: {min_value:.2f}
                    最大值: {max_value:.2f}
                    25%分位数: {percentile_25:.2f}
                    75%分位数: {percentile_75:.2f}
                    """

                    fig.text(0.02, 0.5, stats_text, fontsize=10, 
                            verticalalignment='center', 
                            bbox=dict(boxstyle="round,pad=0.5", facecolor="lightgray"))

                    plt.tight_layout()
                    plt.show()
                    return plt
                
                chart = get_chart(analysed_result_list)
                returned_data['chart'] = chart
            
            return returned_data
        
        case 'one_ai_and_other_random_simulate':
            # 初步排错
            match setup_mode:
                case 'random':
                    pass
                case 'target':
                    if not setup_tile_args:
                        raise Exception('在完全随机模拟中采用指定初始模式下，效果板块参数为空')
                    if len(setup_tile_args) != 9:
                        raise Exception('在完全随机模拟中采用指定初始模式下，效果板块参数长度填写不足')
                    if (
                        type(setup_tile_args[0]) != int
                        or any(type(setup_tile_args[i]) != list for i in range(1,9) if i != 5)
                        or type(setup_tile_args[5]) != int
                    ):
                        raise Exception('在完全随机模拟中采用指定初始模式下，效果板块参数中一个或多个位置的元素类型不合法')
                    if not setup_player_order_args:
                        raise Exception('在完全随机模拟中采用指定初始模式下，玩家初始顺序参数为空')
                    if len(setup_player_order_args) != num_players:
                        raise Exception('在完全随机模拟中采用指定初始模式下，玩家初始顺序参数长度与玩家数不一致')
                    if len(set(setup_player_order_args)) != num_players:
                        raise Exception('在完全随机模拟中采用指定初始模式下，玩家初始顺序参数中存在重复值')
                    if any(player_idx not in setup_player_order_args for player_idx in range(num_players)):
                        raise Exception('在完全随机模拟中采用指定初始模式下，玩家初始顺序参数中存在非法值')
                case _:
                    raise Exception('在完全随机模拟中采用不合法的初始设置模式（合法模式仅有random和target)')
            
            # 初始化网页控制台
            io = GamePanel(port=5001, player_count=num_players) # 自动启动后台服务
            io.update_global_status("=== 大创造时代游戏开始 ===")
            game_args_dict = {
                'num_players': num_players,
                'setup_mode': setup_mode,                           # input | random | target 
                'setup_tile_args' : setup_tile_args,
                'setup_player_order_args': setup_player_order_args,
                'action_history': [],
                'simulation_path': [],
                'remaining_path_length': 0,
                'action_mode': ['ai_selection_per_step'] + ['random_simulate'] * (num_players-1),             # human | random_simulate | reproduce | ai_selection_per_step
                'web_io': io,                                       # Silence_IO() | io,
                'need_estimate': False,
            }
            game_engine = GameEngine(game_args_dict)
            result = game_engine.run_game()

            from GameHistoryRecorder import save_game_history
            save_game_history(game_args_dict, result)
            print(result)
        
        case _:
            raise ValueError('非法全局模式')

if __name__ == "__main__":

    # TODO web_io的线程数需减少，单通道即可
    # TODO 网页页面的回合助推板持有者标记和额外金币的可视化显示
    # TODO 下一步评估agent的建立（通过构建指数，指标：当期收益 & 远期收益（总未来收益-当期收益） & 一位率 etc.)

    setup_tile_args = (
        2,                                          # 排除的规划卡
        [1, 4, 7, 9],                               # 派系板块 (num_players + 1 = 4个)
        [3, 9, 14,16],                              # 宫殿板块 (num_players + 1 = 4个)
        [1, 3, 4, 7, 8, 10],                        # 回合助推板 (num_players + 3 = 6个)
        [5, 3, 4, 8, 2, 6],                         # 轮次计分板块
        2,                                          # 最终计分板块
        [3, 7, 2, 6, 9, 10, 12, 1, 11, 5, 4, 8],    # 能力板块顺序
        [3, 5, 18, 7, 4, 2, 9, 11],                 # 科学板块 (2 + 2 * num_players = 8个)
        [2, 4, 6]                                   # 书本行动板块
    )

    # main(mode = 'full_human', num_players = 3, setup_mode = 'target', setup_tile_args = setup_tile_args, setup_player_order_args = [2,0,1])
    # main(mode = 'random_simulate')
    main(mode = 'one_ai_and_other_random_simulate', num_players = 3, setup_mode = 'random')
