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
            data = {'content': str(message)}
            if color:
                data['color'] = color
            self.queues['outputs'][channel].put(json.dumps(data))

    def update_player_state(self, player_id, field, value):
        """更新单个玩家状态字段"""
        if 1 <= player_id <= self.player_count:
            # 这里需要存储玩家状态，然后通过新的SSE流发送
            # 简化实现：直接更新DOM（实际需要更复杂的实现）
            pass

    def update_global_status(self, message):
        """4. 更新全局状态 (对局状态)"""
        self.queues['global_status'].put(message)

class Silence_IO:
    def get_input(self, prompt = '>'):
        pass
    def output(self, channel, message, color=None):
        pass
    def update_player_states(self, states, color=None):
        pass
    def update_global_status(self, message):
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
        panel.output(0, "这是红色消息", color="red")
        time.sleep(3)


    