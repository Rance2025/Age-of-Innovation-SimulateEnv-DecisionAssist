import threading
import queue
import json
from flask import Flask, render_template, request, Response

class GamePanel:
    def __init__(self, host='127.0.0.1', port=5000, player_count=3):
        """初始化对局面板"""
        if not 3 <= player_count <= 5:
            raise ValueError("玩家数量必须在3-5之间")
        
        # 4个核心数据结构
        self.queues = {
            'input': queue.Queue(),       # 用户输入
            'outputs': [queue.Queue() for _ in range(player_count + 1)],  # 0=可选行动, 1+=玩家
            'player_states': queue.Queue(), # 所有玩家状态
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
        self.queues['global_status'].put(message)

class Silence_IO:
    def get_input(self, prompt = '>'):
        pass
    def output(self, channel, message, color=None):
        pass
    def update_player_states(self, player_id, field, value):
        pass
    def update_global_status(self, message):
        pass
# 测试代码
if __name__ == "__main__":
    panel = GamePanel(player_count=5)
    
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
        'planning_card': 'development',  # 发展卡，显示红色圆圈
        'faction': '帝国',               # 派系名称
        'score': 30
    })
    time.sleep(5)


    