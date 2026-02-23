from GameEngine import GameEngine
from web_io import GamePanel, Silence_IO
import time
from GameHistoryRecorder import save_game_history

def table(data):
    import numpy as np
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

if __name__ == "__main__":
    start_time = time.time()
    res = []
    # 初始化网页控制台
    num_players = 3
    io = GamePanel(port=5000, player_count=num_players) # 自动启动后台服务
    io.update_global_status("=== 大创造时代游戏开始 ===")
    # for i in range(1000):
    game_args_dict = {
        'num_players': num_players,
        'setup_mode': 'target',                          # input | random | target 
        'setup_tile_args' : (
            3,                                          # 排除的规划卡
            [2, 3, 5, 8],                               # 派系板块 (3+1=4个)
            [3, 9, 14,16],                              # 宫殿板块 (3+1=4个)
            [1, 3, 4, 7, 8, 10],                        # 回合助推板 (3+3=6个)
            [5, 3, 4, 8, 2, 6],                         # 轮次计分板块
            2,                                          # 最终计分板块
            [3, 7, 2, 6, 9, 10, 12, 1, 11, 5, 4, 8],    # 能力板块顺序
            [3, 5, 18, 7, 4, 2, 9, 11],                 # 科学板块 (2+2*3=8个)
            [2, 4, 6]                                   # 书本行动板块
        ),
        'setup_player_order_args': [2, 0, 1],
        'action_history': [],
        'simulation_path': [],
        'path_length': 0,
        'action_mode': 'input',                          # input | simulate | reproduce
        'web_io': io, # Silence_IO() | io,
        'need_estimate': False,
    }
    # time.sleep(1)
    game_engine = GameEngine(game_args_dict)
    result = game_engine.run_game()
    save_game_history(game_args_dict, result)
    print(result)
    # res.append(result)
    # if i % 250 == 0:
    #     print('-',end=' ',flush=True)

    # end_time = time.time() 
    # print(f'耗时{end_time - start_time:.10f}秒')

    # arr = np.array(list(map(lambda x: x[0],res)))
    # # 计算平均数和标准差
    # mean_value = np.mean(arr)  # 平均数
    # std_value = np.std(arr)     # 总体标准差
    
    # print(f'万局（三人）第一名分数均值:{mean_value}，标准差:{std_value}')

    # table(arr)

    # print(f'万局（三人）最大总分: {max(res,key=sum)}')
    # print(f'万局（三人）第一名最高分: {max(res,key=lambda x: x[0])}')
    # print(f'万局（三人）平均总分{sum(map(sum,res))/len(res)}')
    # print(f'万局（三人）第一名平局分{sum(map(lambda x: x[0],res))/len(res)}')
            
