import os
from flask import Flask, render_template, request, Response, send_file
import json
import queue
import threading

class GamePanel:
    def __init__(self, host='127.0.0.1', port=5000, player_count=3):
        """初始化对局面板"""
        if not 3 <= player_count <= 5:
            raise ValueError("玩家数量必须在3-5之间")
        
        # 4个核心数据结构
        self.queues = {
            'input': queue.Queue(),       # 用户输入
            'outputs': [queue.Queue() for _ in range(player_count + 1)],  # 0=可选行动, 1+=玩家
            'global_status': queue.Queue()  # 全局状态
        }
        
        self.player_count = player_count
        self.host = host
        self.port = port
        self.app = Flask(__name__, template_folder='templates')
        
        # 精准路由配置
        self.app.route('/')(self.render_panel)
        self.app.route('/input', methods=['POST'])(self.handle_input)
        self.app.route('/stream/<stream_type>')(self.stream_data)
        self.app.route('/images/<path:filename>')(self.serve_image)  # 添加图片服务
        
        # 启动服务
        threading.Thread(target=self._run_server, daemon=True).start()
        # print(f"✓ 面板运行中: http://{host}:{port} (玩家数: {player_count})")

        # 添加玩家状态存储
        self.player_states = [{
            'money': 0,
            'ore': 0,
            'meeple': 0,
            'bank_book': 0,
            'law_book': 0,
            'engineering_book': 0,
            'medical_book': 0,
            'magics_1': 0,
            'magics_2': 0,
            'magics_3': 0,
            'city_amount': 0,
            'navigation_level': 0,
            'shovel_level': 0,
            'planning_card': None,  # 字符串类型
            'faction': None,        # 字符串类型
            'score': 0
        } for _ in range(player_count)]

        # 规划卡颜色映射
        self.planning_card_colors = {
            "development": "#ff4444",      # 发展卡 - 红色
            "military": "#4444ff",        # 军事卡 - 蓝色
            "trade": "#44ff44",           # 贸易卡 - 绿色
            "technology": "#ffff44",       # 科技卡 - 黄色
            "diplomacy": "#ff44ff",       # 外交卡 - 紫色
            "infrastructure": "#ffaa44",  # 基建卡 - 橙色
            "expansion": "#44ffff"        # 扩张卡 - 青色
        }
    
    def _run_server(self):
        """运行Flask服务器"""
        import logging
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)
        self.app.run(host=self.host, port=self.port, debug=False, use_reloader=False)

    def render_panel(self):
        return render_template('game_panel.html', panel_count=self.player_count)

    def handle_input(self):
        """处理用户输入 - 允许空字符串"""
        cmd = request.form.get('command', '')  # 不移除空白，保留原始输入
        # 无条件放入队列，即使为空字符串
        self.queues['input'].put(cmd)
        return '', 204

    def stream_data(self, stream_type):
        """数据流处理"""
        def generate():
            # 确定队列
            q = None
            if stream_type == 'status':
                q = self.queues['global_status']
            elif stream_type == 'actions':
                q = self.queues['outputs'][0]
            elif stream_type.startswith('player'):
                try:
                    channel = int(stream_type[6:])
                    if 1 <= channel <= self.player_count:
                        q = self.queues['outputs'][channel]
                    else:
                        yield "data: {\"content\": \"无效通道\"}\n\n"
                        return
                except (IndexError, ValueError):
                    yield "data: {\"content\": \"无效通道格式\"}\n\n"
                    return
            else:
                yield "data: {\"content\": \"无效流类型\"}\n\n"
                return
            
            if q is None:
                yield "data: {\"content\": \"队列未找到\"}\n\n"
                return
                
            while True:
                try:
                    msg = q.get(timeout=0.5)
                    yield f"data: {json.dumps({'content': str(msg)})}\n\n"
                except queue.Empty:
                    yield ":heartbeat\n\n"
        
        return Response(
            generate(), 
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Content-Type': 'text/event-stream',
                'Access-Control-Allow-Origin': '*'
            }
        )
    
    def serve_image(self, filename):
        """提供图片文件服务"""
        try:
            # 检查文件是否存在
            image_path = os.path.join('images', filename)
            if not os.path.exists(image_path):
                return "Image not found", 404
            
            # 发送文件
            return send_file(image_path)
        except Exception as e:
            return str(e), 500
        
    # ===== 4个核心接口 =====
    def get_input(self, prompt="> "):
        """1. 获取用户输入"""
        #self.output(0, prompt)
        return self.queues['input'].get()
    
    def output(self, channel, message, color=None):
        """2. 输出到指定信息框 (0=可选行动, 1+=玩家)，支持自定义颜色"""
        if 0 <= channel <= self.player_count:
            # 发送包含颜色信息的数据
            data = {'type': 'log_info','content': str(message)}
            if color:
                data['color'] = color
            self.queues['outputs'][channel].put(json.dumps(data))

    def update_player_state(self, player_id, updates):
        """
        3. 更新玩家状态 - 支持部分字段更新
        player_id: 玩家ID (1-based)
        updates: 包含要更新字段的字典
        """
        if not 0 <= player_id < self.player_count:
            raise ValueError(f"玩家ID必须在1-{self.player_count}之间")

        # 更新状态数据
        state = self.player_states[player_id]
        for key, value in updates.items():
            if key in state:
                state[key] = value
        
        # 准备发送到前端的数据
        frontend_data = {
            'player_id': player_id+1,
            'updates': {}
        }
        
        # 处理前13个数值字段
        numeric_fields = [
            'money', 'ore', 'meeple', 'bank_book', 'law_book', 
            'engineering_book', 'medical_book', 'magics_1', 
            'magics_2', 'magics_3', 'city_amount', 
            'navigation_level', 'shovel_level'
        ]
        
        for field in numeric_fields:
            if field in updates:
                frontend_data['updates'][field] = state[field]
        
        # 处理标题栏特殊字段
        title_fields = ['planning_card', 'faction', 'score']
        for field in title_fields:
            if field in updates:
                frontend_data['updates'][field] = state[field]
        
        # 发送到前端
        self.queues['outputs'][player_id+1].put(json.dumps({
            'type': 'state_update',
            'data': frontend_data
        }))
        
        return True

    def update_global_status(self, message):
        """4. 更新全局状态 (对局状态)"""
        self.queues['global_status'].put(json.dumps({
            'type': 'global_state',
            'content': message
        }))

    def update_terrain(self, row, col, terrain_type):
        """
        5. 更新地图地形
        row: 行索引 (0-8)
        col: 列索引 (0-12)
        terrain_type: 地形类型 (0-7)
        """
        if not 0 <= row <= 8 or not 0 <= col <= 12:
            raise ValueError("行索引必须在0-8之间，列索引必须在0-12之间")
        
        if terrain_type not in range(8):
            raise ValueError("地形类型必须在0-7之间")
        
        # 准备发送到前端的数据
        terrain_data = {
            'type': 'terrain_update',
            'data': {
                'row': row,
                'col': col,
                'terrain_type': terrain_type
            }
        }
        
        # 发送到前端（通过可选行动通道）
        self.queues['global_status'].put(json.dumps(terrain_data))
    
    def update_building(self, hex_row, hex_col, building_color, building_id, mode='replace'):
        """
        在指定六边形上放置元素
        hex_row: 六边形行号 (0-8 对应 A-I)
        hex_col: 六边形列号 (0-12 对应 1-13)
        building_color: planning-card-id (中立为0)
        building_id: 建筑类型 (1-5: 车间,工会,宫殿,学校,大学)
        mode: 模式 - 'replace'（替换）或 'overlay'（叠加）
        """
        if not (0 <= hex_row <= 8 and 0 <= hex_col <= 12):
            raise ValueError("六边形坐标必须在有效范围内: 行(0-8), 列(0-12)")
        
        if building_color not in range(8):
            raise ValueError("x参数必须在有效范围内")
        
        if building_id not in range(1,9):
            raise ValueError("y参数必须在1-8之间")
        
        if mode not in ['replace', 'overlay']:
            raise ValueError("模式必须是 'replace' 或 'overlay'")
        
        # 准备发送到前端的数据
        element_data = {
            'type': 'element_placement',
            'data': {
                'hex_row': hex_row,
                'hex_col': hex_col,
                'x': building_color,
                'y': building_id,
                'mode': mode
            }
        }
        
        # 发送到前端（通过全局状态通道）
        self.queues['global_status'].put(json.dumps(element_data))
        return True
    
    def set_round_scoring(self, round_num, round_scoring_id):
        """
        设置回合计分图片
        round_num: 回合数 (1-6)
        x: 计分图片编号 (0-12)
        """
        if not 1 <= round_num <= 6:
            raise ValueError("回合数必须在1-6之间")
        
        if not 0 <= round_scoring_id <= 12:
            raise ValueError("计分图片编号必须在0-12之间")
        
        # 准备发送到前端的数据
        scoring_data = {
            'type': 'round_scoring',
            'data': {
                'round': round_num,
                'x': round_scoring_id
            }
        }
        
        # 发送到前端
        self.queues['global_status'].put(json.dumps(scoring_data))
        return True

    def set_final_round_bonus(self, final_scoring_id):
        """
        设置第6回合的叠加奖励图片
        x: 奖励图片编号 (13-16)
        """
        if not 1 <= final_scoring_id <= 4:
            raise ValueError("奖励图片编号必须在1-4之间")
        
        # 准备发送到前端的数据
        bonus_data = {
            'type': 'final_round_bonus',
            'data': {
                'x': final_scoring_id + 12
            }
        }
        
        # 发送到前端
        self.queues['global_status'].put(json.dumps(bonus_data))
        return True

    def set_bonus_columns(self, round_bonus_ids):
        """
        全量更新右侧助推板块图片
        x_list: 包含图片编号的列表 (1-20)
        """
        if not isinstance(round_bonus_ids, list):
            raise ValueError("参数必须是列表")
        
        for x in round_bonus_ids:
            if not 1 <= x <= 20:
                raise ValueError("助推板块图片编号必须在1-20之间")
        
        # 准备发送到前端的数据
        bonus_columns_data = {
            'type': 'bonus_columns',
            'data': {
                'x_list': round_bonus_ids
            }
        }
        
        # 发送到前端
        self.queues['global_status'].put(json.dumps(bonus_columns_data))
        return True
    
    def round_update(self, round):
        
        # 准备发送到前端的数据
        round_update_data = {
            'type': 'round_scoring_update',
            'data': {
                'round': round
            }
        }
        # 发送到前端
        self.queues['global_status'].put(json.dumps(round_update_data))
        return True
    
    def get_round_bonus(self, setup_round_booster_ids, round_booster_id):
        """
        获取回合的助推图片编号
        round_booster_id: 回合的助推图片编号 (1-10)
        """
        if not 1 <= round_booster_id <= 10:
            raise ValueError("回合的助推图片编号必须在1-10之间")
        
        # 准备发送到前端的数据
        get_booster_data = {
            'type': 'round_bonus_get',
            'data': {
                'round_booster_index': setup_round_booster_ids.index(round_booster_id),
            }
        }
        print(setup_round_booster_ids.index(round_booster_id))
        # 发送到前端
        self.queues['global_status'].put(json.dumps(get_booster_data))
        return True

    def return_round_bonus(self, setup_round_booster_ids, round_booster_id):
        """
        返还回合助推图片
        round_booster_id: 回合的助推图片编号 (1-10)
        """
        if not 1 <= round_booster_id <= 10:
            raise ValueError("回合的助推图片编号必须在1-10之间")
        
        # 准备发送到前端的数据
        get_booster_data = {
            'type': 'round_bonus_back',
            'data': {
                'round_booster_index': setup_round_booster_ids.index(round_booster_id),
            }
        }
        print(setup_round_booster_ids.index(round_booster_id))
        # 发送到前端
        self.queues['global_status'].put(json.dumps(get_booster_data))
        return True

class Silence_IO:
    def get_input(self, prompt = '>'):
        pass
    def output(self, channel, message, color=None):
        pass
    def update_player_states(self, player_id, field, value):
        pass
    def update_global_status(self, message):
        pass
    def update_terrain(self, row, col, terrain_type):
        pass
    def update_building(self, hex_row, hex_col, building_colour, building_id, mode='replace'):
        pass
    def set_round_scoring(self, round_num, round_scoring_id):
        pass
    def set_final_round_bonus(self, final_scoring_id):
        pass
    def set_bonus_columns(self, round_bonus_ids):
        pass
    def round_update(self, round):
        pass
    def get_round_bonus(self, setup_round_booster_ids, round_booster_id):
        pass
    def return_round_bonus(self, setup_round_booster_ids, round_booster_id):
        pass

# 测试代码
if __name__ == "__main__":
    panel = GamePanel(player_count=3)
    
    import time
    # time.sleep(3)  # 等待服务器启动
    
    # # 运行诊断测试
    # print("\n=== 运行诊断测试 ===")
    
    # # 测试1: 基本消息发送
    # print("1. 发送测试消息...")
    # panel.update_global_status("诊断测试: 全局状态")
    # panel.output(0, "诊断测试: 可选行动消息")
    # panel.output(1, "诊断测试: 玩家1消息")
    # panel.output(2, "诊断测试: 玩家2消息")
    # panel.output(3, "诊断测试: 玩家3消息")
    
    # time.sleep(2)
    
    # # 测试2: 检查队列状态
    # print("\n2. 检查队列状态...")
    # for i, q in enumerate(panel.queues['outputs']):
    #     print(f"  输出队列[{i}]: {q.qsize()} 条消息等待")
    # print(f"  全局状态队列: {panel.queues['global_status'].qsize()} 条消息等待")
    
    # # 测试3: 持续发送消息
    # print("\n3. 开始持续测试...")
    # counter = 0
    # try:
    #     while True:
    #         counter += 1
    #         panel.update_global_status(f"持续测试 #{counter} - 全局状态")
    #         panel.output(0, f"持续测试 #{counter} - 可选行动")
    #         for i in range(1, panel.player_count + 1):
    #             panel.output(i, f"持续测试 #{counter} - 玩家{i}")
            
    #         time.sleep(3)
            
    # except KeyboardInterrupt:
    #     print("\n=== 测试结束 ===")
    while True:
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
            'planning_card': '山脉',  # 发展卡，显示红色圆圈
            'faction': '帝国',               # 派系名称
            'score': 30
        })
        panel.update_building(0, 0, 1, 2, 'replace')
        panel.set_final_round_bonus(2)
        panel.round_update(5)
        time.sleep(3)


    