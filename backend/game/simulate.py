from .aoi_game import GameEngine
import time
import random
import numpy as np
from tqdm import tqdm
import logging
from .aoi_game import ActionRecord
from typing import List


class SimulationConfig:
    """模拟配置数据模型类"""
    
    def __init__(
        self,
        times: int = 1000,
        num_players: int = 3,
        need_chart: bool = True,
        expect_result: str = 'first_one',
        init_settings: dict = None,
        simulation_path: list[ActionRecord] = None,
        seed_id: List[int] = None
    ):
        self.times = times
        self.num_players = num_players
        self.need_chart = need_chart
        self.expect_result = expect_result
        self.init_settings = init_settings if init_settings is not None else self._default_init_settings()
        self.simulation_path = simulation_path if simulation_path is not None else []
        self.seed_id = seed_id if seed_id is not None else []
        
        # 执行初始化检查，如果检查失败则抛出异常
        if not self._initial_check():
            raise ValueError("模拟参数设置不合法")
    
    @staticmethod
    def _default_init_settings() -> dict:
        """返回默认初始化设置"""
        return {
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
    
    def _initial_check(self) -> bool:
        """
        检查初始化设置和模拟路径的一致性
        当init_settings中包含'random'值且simulation_path不为空时发出警告
        检查seed_id长度与times的关系并自动调整
        
        Returns:
            bool: 检查是否通过（目前总是返回True，除非有严重错误）
        """
        # 检查seed_id长度
        if self.seed_id:
            seed_len = len(self.seed_id)
            if seed_len > self.times:
                logging.warning(f"⚠️ [警告] seed_id 长度 ({seed_len}) 大于 times ({self.times})，多余的种子将被忽略")
            elif seed_len < self.times:
                logging.warning(f"⚠️ [警告] seed_id 长度 ({seed_len}) 小于 times ({self.times})，自动调整 times 为 {seed_len}")
                self.times = seed_len
        
        def contains_random(init_settings: dict) -> bool:
            """检查初始化设置中是否包含'random'设置"""
            # 检查顶层设置
            if init_settings.get('init_player_order') == 'random':
                return True
            
            # 检查setup_tiles中的设置
            setup_tiles = init_settings.get('setup_tiles', {})
            for value in setup_tiles.values():
                if value == 'random':
                    return True
            
            return False
        
        has_random = contains_random(self.init_settings)
        path_not_empty = bool(self.simulation_path)
        
        if has_random and path_not_empty:
            logging.warning("⚠️ [警告] simulation_path 参数已失效！\n"
                           "原因：init_settings 中包含 'random' 设置，\n"
                           "随机设置将覆盖指定的模拟路径。")
        
        return True

# 定义图表绘制函数
def _get_chart(data):
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
    return plt

# 主函数-随机模拟
def simulate(config: SimulationConfig = None) -> dict:
    """
    执行游戏模拟
    
    Args:
        config: SimulationConfig 配置对象，包含所有模拟参数
        
    Returns:
        dict: 包含模拟结果的字典
    """
    # 如果没有传入配置，使用默认配置（初始化时会自动执行检查）
    if config is None:
        config = SimulationConfig()

    # 初始化所有模拟结果存储列表
    results = []

    # 开始模拟游戏  
    start_time = time.time()

    for i in tqdm(range(config.times), desc="Simulating..."):
        # 设置随机种子
        if config.seed_id:
            current_seed = config.seed_id[i]
        else:
            current_seed = int(time.time() * 1000000) + i
        random.seed(current_seed)
        res: dict[str, int | dict[int, dict[str, int]]]
        res = {"seed": current_seed}
        
        # 创建游戏引擎并启动游戏
        game = GameEngine(num_players=config.num_players, init_settings=config.init_settings).run_game()

        # 获取初始请求
        request = next(game)

        # 设置模拟路径指针
        s_index = 0

        # 游戏主循环
        while not request.is_game_over:
            available = request.available_actions
            if s_index < len(config.simulation_path):
                action = config.simulation_path[s_index]
                s_index += 1
                assert action.player_id == request.player_id
                assert action.action_type == request.action_type
                assert action.action_id in available
                action_id = action.action_id
            else:
                action_id = 65 if (65 in available and random.random() <= 0.9) else random.choice(list(available.keys()))
            request = game.send(action_id)
    
        # 获取最终分数
        res["scores"] = request.final_scores
        # 存储本次模拟结果
        results.append(res)

    # 模拟结束，计算耗时
    end_time = time.time()
    time_spend = end_time - start_time

    # 根据expect_result参数，选择需要分析的结果
    match config.expect_result:
        case 'first_one':
            def transform(result: dict[str, int | dict[int, dict[str, int]]]):
                # result 结构: {"seed": xxx, "scores": {player_id: {'total': int, ...}}}
                scores = result['scores']
                return sorted([s['total'] for s in scores.values()], reverse=True)[0]
            analysed_result_list = list(map(transform, results))
        case _:
            analysed_result_list = []

    # 计算平均数和标准差
    mean_value = np.mean(analysed_result_list)  # 平均数
    std_value = np.std(analysed_result_list)     # 总体标准差

    # 准备返回数据
    returned_data = {
        'all_result_list': results,
        'analysed_result_list': analysed_result_list,
        'time_spend': time_spend,
        'mean_value': mean_value,
        'std_value': std_value,
    }

    # 如果需要图表，则生成并添加到返回数据中
    if config.need_chart:
        chart = _get_chart(analysed_result_list)
        returned_data['chart'] = chart
    
    # 返回结果
    return returned_data
