"""
游戏初始化模块

提供游戏启动和模拟的高级接口。
"""
import os
import sys
from typing import List, Dict, Any

from backend.logger import get_logger
from backend.web_io import WebIO, SilentIO

logger = get_logger(__name__)


def start_game(
    num_players: int,
    players: List[dict],
    game_mode: dict,
    init_settings: dict,
) -> Dict[str, Any]:
    """
    开始游戏函数

    Args:
        num_players: 玩家数量 (3 ~ 5)
        players: 玩家配置列表（已弃用，会被忽略）
        game_mode: 游戏模式配置
        init_settings: 初始设置配置

    Returns:
        游戏结果

    Note:
        当前版本忽略传入的 players 参数，默认使用全部 human 模式
    """
    logger.info("=" * 60)
    logger.info("大创造时代游戏开始")
    logger.info("=" * 60)

    # 修改：忽略传入的 players 参数，默认使用全部 human
    action_mode = ['human'] * num_players
    logger.info(f"玩家模式: {action_mode} (已忽略传入的 players 参数)")

    # 创建 WebIO
    io = WebIO(player_count=num_players)
    io.update_global_status("=== 大创造时代游戏开始 ===")

    # 构建 game_args_dict
    game_args_dict = {
        'num_players': num_players,
        'init_player_order': init_settings.get('player_order', {'type': 'random', 'args': []}),
        'setup_tiles': init_settings.get('setup_tiles', {}),
        'action_history': [],
        'simulation_path': [],
        'remaining_path_length': 0,
        'action_mode': action_mode,
        'web_io': io,
        'need_estimate': False,
    }

    # 启动游戏引擎
    from game.GameEngine import GameEngine
    game_engine = GameEngine(game_args_dict)
    result = game_engine.run_game()

    logger.info("=" * 60)
    logger.info("游戏结束")
    logger.info(f"结果: {result}")
    logger.info("=" * 60)

    return result


def simulate(
    num_players: int,
    players: List[dict],
    game_mode: dict,
    init_settings: dict,
    times: int = 1000,
    simulation_path: List = [],
    expect_result: str = 'first_one',
    need_chart: bool = True,
) -> Dict[str, Any]:
    """
    模拟游戏函数

    Args:
        num_players: 玩家数量 (3 ~ 5)
        players: 玩家配置列表
        game_mode: 游戏模式配置
        init_settings: 初始设置配置
        times: 模拟次数，默认 1000
        simulation_path: 模拟路径指定
        expect_result: 期望结果类型
        need_chart: 是否需要生成图表

    Returns:
        包含模拟结果统计信息
    """
    import time
    import numpy as np
    from tqdm import tqdm

    logger.info(f"开始模拟: {times} 局，{num_players} 人")

    # 构建 action_mode 列表
    action_mode = []
    for player in players:
        match player.get("type"):
            case "human":
                action_mode.append("human")
            case "random":
                action_mode.append("random_simulate")
            case "ai":
                action_mode.append("ai_selection_per_step")
            case _:
                action_mode.append("random_simulate")

    result_list = []
    start_time = time.time()

    from game.GameEngine import GameEngine

    for _ in tqdm(range(times), desc="模拟进度"):
        game_args_dict = {
            'num_players': num_players,
            'init_player_order': init_settings.get('player_order', {'type': 'random', 'args': []}),
            'setup_tiles': init_settings.get('setup_tiles', {}),
            'action_history': [],
            'simulation_path': simulation_path,
            'remaining_path_length': len(simulation_path),
            'action_mode': action_mode,
            'web_io': SilentIO(),
            'need_estimate': False,
        }
        game_engine = GameEngine(game_args_dict)
        result = game_engine.run_game()
        result_list.append(result)

    end_time = time.time()
    time_spend = end_time - start_time
    logger.info(f'模拟完成，耗时 {time_spend:.2f} 秒')

    # 结果分析
    match expect_result:
        case 'first_one':
            def transform(result: dict):
                return sorted(list(map(lambda x: x['total'], result.values())), reverse=True)[0]
            analysed_result_list = list(map(transform, result_list))
        case _:
            analysed_result_list = result_list

    mean_value = np.mean(analysed_result_list)
    std_value = np.std(analysed_result_list)

    logger.info(f'{times}局（{num_players}人）第一名分数均值:{mean_value}，标准差:{std_value}')

    returned_data = {
        'all_result_list': result_list,
        'analysed_result_list': analysed_result_list,
        'time_spend': time_spend,
        'mean_value': mean_value,
        'std_value': std_value,
    }

    if need_chart:
        chart = _generate_chart(analysed_result_list)
        returned_data['chart'] = chart

    return returned_data


def _generate_chart(data):
    """生成数据分布图表"""
    import matplotlib.pyplot as plt
    from scipy import stats
    import numpy as np

    plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False

    mean_value = np.mean(data)
    median_value = np.median(data)
    std_value = np.std(data)
    min_value = np.min(data)
    max_value = np.max(data)
    percentile_25 = np.percentile(data, 25)
    percentile_75 = np.percentile(data, 75)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

    ax1.hist(data, bins=40, edgecolor='black', alpha=0.7, density=True, color='skyblue')
    ax1.axvline(mean_value, color='red', linewidth=2, label=f'均值: {mean_value:.2f}')
    ax1.axvline(median_value, color='green', linewidth=2, label=f'中位数: {median_value:.2f}')
    ax1.axvspan(percentile_25, percentile_75, alpha=0.2, color='yellow', label='25%-75%分位区间')

    x = np.linspace(min_value, max_value, 1000)
    pdf = stats.norm.pdf(x, mean_value, std_value)
    ax1.plot(x, pdf, 'r-', lw=2, label='正态分布参考')

    ax1.set_title('数据分布直方图', fontsize=14)
    ax1.set_xlabel('数值', fontsize=12)
    ax1.set_ylabel('密度', fontsize=12)
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    ax2.boxplot(data, vert=True, patch_artist=True)
    ax2.set_title('数据箱线图', fontsize=14)
    ax2.set_ylabel('数值', fontsize=12)
    ax2.grid(True, alpha=0.3)

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


if __name__ == "__main__":
    simulate(
        num_players=3,
        players=[{"type": "random", "args": None}] * 3,
        game_mode={"type": "standard", "args": None},
        init_settings={
            "player_order": {"type": "random", "args": []},
            "setup_tiles": {
                "planning_cards": "random",
                "factions": "random",
                "palace_tiles": "random",
                "round_boosters": "random",
                "round_scoring": "random",
                "final_scoring": "random",
                "ability_tiles": "random",
                "science_tiles": "random",
                "book_actions": "random"
            }
        },
        times=100
    )
