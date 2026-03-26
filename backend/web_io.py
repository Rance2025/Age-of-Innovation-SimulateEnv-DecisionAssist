"""
Web IO 模块 - 兼容层
为了保持与原有代码的兼容性，提供与旧版相同的接口
但内部使用新的后端API
"""
import os
import sys
import threading

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app import GamePanelAPI, Silence_IO
except ImportError:
    # 如果从backend目录导入失败，尝试相对导入
    from backend.app import GamePanelAPI, Silence_IO


class GamePanel:
    """
    游戏面板类 - 兼容旧版接口
    内部使用新的GamePanelAPI
    """

    def __init__(self, host='127.0.0.1', port=5001, player_count=3):
        """初始化对局面板"""
        # 获取images目录路径 - 现在位于 frontend/assets/images
        static_folder = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'frontend', 'assets', 'images'
        )

        # 创建API实例
        self.api = GamePanelAPI(host=host, port=port, player_count=player_count, static_folder=static_folder)
        self.player_count = player_count
        self.host = host
        self.port = port

        # 启动服务
        threading.Thread(target=self._run_server, daemon=True).start()

        # 复制queues引用以便兼容旧代码
        self.queues = self.api.queues
        self.player_states = self.api.player_states

        # 规划卡颜色映射
        self.planning_card_colors = {
            "development": "#ff4444",
            "military": "#4444ff",
            "trade": "#44ff44",
            "technology": "#ffff44",
            "diplomacy": "#ff44ff",
            "infrastructure": "#ffaa44",
            "expansion": "#44ffff"
        }

    def _run_server(self):
        """运行Flask服务器"""
        self.api.run(debug=False, use_reloader=False)

    # ===== 兼容旧版接口 =====
    def get_input(self, prompt="> "):
        """获取用户输入"""
        return self.api.get_input(prompt)

    def output(self, channel, message, color=None):
        """输出到指定信息框"""
        return self.api.output(channel, message, color)

    def update_player_state(self, player_id, updates):
        """更新玩家状态"""
        return self.api.update_player_state(player_id, updates)

    def update_global_status(self, message):
        """更新全局状态"""
        return self.api.update_global_status(message)

    def update_terrain(self, row, col, terrain_type):
        """更新地图地形"""
        return self.api.update_terrain(row, col, terrain_type)

    def update_building(self, hex_row, hex_col, building_color, building_id, mode='replace'):
        """在指定六边形上放置元素"""
        return self.api.update_building(hex_row, hex_col, building_color, building_id, mode)

    def set_round_scoring(self, round_num, round_scoring_id):
        """设置回合计分图片"""
        return self.api.set_round_scoring(round_num, round_scoring_id)

    def set_final_round_bonus(self, final_scoring_id):
        """设置第6回合的叠加奖励图片"""
        return self.api.set_final_round_bonus(final_scoring_id)

    def set_bonus_columns(self, round_bonus_ids):
        """全量更新右侧助推板块图片"""
        return self.api.set_bonus_columns(round_bonus_ids)

    def round_update(self, round):
        """回合更新"""
        return self.api.round_update(round)

    def get_round_bonus(self, setup_round_booster_ids, round_booster_id):
        """获取回合的助推图片编号"""
        return self.api.get_round_bonus(setup_round_booster_ids, round_booster_id)

    def return_round_bonus(self, setup_round_booster_ids, round_booster_id):
        """返还回合助推图片"""
        return self.api.return_round_bonus(setup_round_booster_ids, round_booster_id)

    def highlight_hex(self, hex_list):
        """高亮可选地块"""
        return self.api.highlight_hex(hex_list)


# Silence_IO 从app模块导入以保持兼容
__all__ = ['GamePanel', 'Silence_IO']


# 测试代码
if __name__ == "__main__":
    panel = GamePanel(player_count=3)

    import time

    p, q = 0, 0
    while True:
        p = (p + 2) % 9
        q = (q + 3) % 13
        panel.highlight_hex([(p, q), ((2 * p) % 9, (2 * q) % 13)])
        panel.update_player_state(1, {
            'money': 150,
            'ore': 75,
            'meeple': 3,
            'bank_book': 2,
            'law_book': 1,
            'engineering_book': 0,
            'medical_book': 1,
            'magics_1': 5,
            'magics_2': 3,
            'magics_3': 2,
            'city_amount': 4,
            'navigation_level': 2,
            'shovel_level': 1,
            'planning_card': '山脉',
            'faction': '帝国',
            'score': 30
        })
        panel.update_building(0, 0, 1, 2, 'replace')
        panel.set_round_scoring(3, 5)
        panel.set_final_round_bonus(2)
        panel.round_update(5)
        time.sleep(3)
