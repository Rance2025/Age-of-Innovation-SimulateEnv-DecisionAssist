"""
后端API服务 - Flask应用
提供SSE数据流服务和静态文件服务
"""
import os
import sys
import json
import queue
import threading
import logging
from flask import Flask, render_template, request, Response, send_file, send_from_directory, jsonify
from flask_cors import CORS

# 添加父目录到路径以导入其他模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入数据库模块
from backend.database import get_db_instance


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class GamePanelAPI:
    """游戏面板API服务"""

    def __init__(self, host='127.0.0.1', port=5001, player_count=3, static_folder=None):
        """初始化API服务"""
        if not 3 <= player_count <= 5:
            raise ValueError("玩家数量必须在3-5之间")

        self.player_count = player_count
        self.host = host
        self.port = port

        # 静态文件目录 - 指向 frontend/assets/images
        if static_folder is None:
            static_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'frontend', 'assets', 'images')
        self.static_folder = static_folder

        # 创建Flask应用
        self.app = Flask(__name__, static_folder=static_folder)

        # 启用CORS
        CORS(self.app, resources={
            r"/*": {
                "origins": "*",
                "methods": ["GET", "POST", "OPTIONS"],
                "allow_headers": ["Content-Type"]
            }
        })

        # 4个核心数据结构
        self.queues = {
            'input': queue.Queue(),
            'outputs': [queue.Queue() for _ in range(player_count + 1)],
            'global_status': queue.Queue()
        }

        # 玩家状态存储
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
            'planning_card': None,
            'faction': None,
            'score': 0
        } for _ in range(player_count)]

        # 注册路由
        self._register_routes()

    def _register_routes(self):
        """注册Flask路由"""
        self.app.route('/')(self.index)
        self.app.route('/input', methods=['POST'])(self.handle_input)
        self.app.route('/stream/<stream_type>')(self.stream_data)
        self.app.route('/images/<path:filename>')(self.serve_image)
        self.app.route('/config')(self.get_config)

        # 历史对局API
        self.app.route('/api/games', methods=['GET'])(self.list_games)
        self.app.route('/api/games', methods=['POST'])(self.create_game)
        self.app.route('/api/games/<int:game_id>', methods=['GET'])(self.get_game)
        self.app.route('/api/games/<int:game_id>', methods=['DELETE'])(self.delete_game)
        self.app.route('/api/games/stats', methods=['GET'])(self.get_game_stats)

        # 游戏启动API
        self.app.route('/api/game/start', methods=['POST'])(self.start_game)

    def index(self):
        """首页"""
        return {
            'status': 'ok',
            'service': 'Game Panel API',
            'version': '2.0',
            'player_count': self.player_count
        }

    def get_config(self):
        """获取配置信息"""
        return {
            'player_count': self.player_count,
            'api_version': '2.0'
        }

    def handle_input(self):
        """处理用户输入"""
        cmd = request.form.get('command', '')
        self.queues['input'].put(cmd)
        return '', 204

    # ===== 历史对局API =====
    def list_games(self):
        """获取游戏列表"""
        try:
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 10, type=int)
            sort_by = request.args.get('sort_by', 'timestamp')
            sort_order = request.args.get('sort_order', 'desc')

            # 筛选参数
            filters = {}
            num_players = request.args.get('num_players', type=int)
            if num_players:
                filters['num_players'] = num_players
            setup_mode = request.args.get('setup_mode')
            if setup_mode:
                filters['setup_mode'] = setup_mode

            db = get_db_instance()
            result = db.list_games(
                page=page,
                per_page=per_page,
                sort_by=sort_by,
                sort_order=sort_order,
                filters=filters if filters else None
            )
            return jsonify(result)
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    def create_game(self):
        """创建游戏记录"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No data provided'}), 400

            db = get_db_instance()
            game_id = db.create_game(data)
            return jsonify({'id': game_id, 'message': 'Game created successfully'}), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    def get_game(self, game_id):
        """获取单个游戏详情"""
        try:
            db = get_db_instance()
            game = db.get_game(game_id)
            if game:
                return jsonify(game)
            return jsonify({'error': 'Game not found'}), 404
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    def delete_game(self, game_id):
        """删除游戏记录"""
        try:
            db = get_db_instance()
            success = db.delete_game(game_id)
            if success:
                return jsonify({'message': 'Game deleted successfully'})
            return jsonify({'error': 'Game not found'}), 404
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    def get_game_stats(self):
        """获取游戏统计"""
        try:
            db = get_db_instance()
            stats = db.get_statistics()
            return jsonify(stats)
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    def start_game(self):
        """接收游戏启动设置并打印"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No data provided'}), 400

            # 对数据进行排序处理（除了顺序重要的字段）
            data = self._sort_data_except_order_sensitive(data)

            # 使用 Flask logger 输出日志
            self.app.logger.info("="*60)
            self.app.logger.info("收到游戏启动请求")
            self.app.logger.info("="*60)
            # 格式化输出，数组保持在一行
            formatted_json = json.dumps(data, indent=2, ensure_ascii=False)
            # 将多行数组压缩为一行（只匹配JSON数组：[数字, 数字, ...] 或 ["字符串", ...]）
            import re
            def compact_array(match):
                content = match.group(0).replace('\n', '').replace('  ', ' ')
                # 去除多余空格
                while '  ' in content:
                    content = content.replace('  ', ' ')
                return content
            # 只匹配包含数字、字符串、空格、逗号的JSON数组（以[开头，]结尾）
            formatted_json = re.sub(r'\[[\s\d,\[\]"\']{10,}?\]', compact_array, formatted_json, flags=re.DOTALL)
            # 将 players 数组中的每个对象压缩到一行
            def compact_player(match):
                content = match.group(0).replace('\n', '').replace('  ', ' ')
                while '  ' in content:
                    content = content.replace('  ', ' ')
                return content
            formatted_json = re.sub(r'\{\s*"type":\s*"[^"]+",\s*"args":\s*"[^"]+"\s*\}', compact_player, formatted_json, flags=re.DOTALL)
            for line in formatted_json.split('\n'):
                if line.strip():  # 跳过空行
                    self.app.logger.info(line)
            self.app.logger.info("="*60)

            return jsonify({
                'status': 'success',
                'message': 'Game settings received',
                'data': data
            }), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    def _sort_data_except_order_sensitive(self, data):
        """对数据进行排序，但保留顺序敏感字段的原始顺序"""
        if not isinstance(data, dict):
            return data

        # 顺序敏感的字段（不排序）
        order_sensitive_fields = {'round_scoring', 'ability_tiles', 'science_tiles'}

        # 处理 init_settings.setup_tiles 中的列表
        if 'init_settings' in data and isinstance(data['init_settings'], dict):
            init_settings = data['init_settings']
            if 'setup_tiles' in init_settings and isinstance(init_settings['setup_tiles'], dict):
                setup_tiles = init_settings['setup_tiles']
                for key, value in setup_tiles.items():
                    if isinstance(value, list) and key not in order_sensitive_fields:
                        setup_tiles[key] = sorted(value)

        return data

    def stream_data(self, stream_type):
        """数据流处理"""
        def generate():
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
            image_path = os.path.join(self.static_folder, filename)
            if not os.path.exists(image_path):
                return "Image not found", 404
            return send_file(image_path)
        except Exception as e:
            return str(e), 500

    def run(self, debug=False, use_reloader=False):
        """运行服务器"""
        import logging
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)
        self.app.run(host=self.host, port=self.port, debug=debug, use_reloader=use_reloader)

    # ===== 核心接口 =====
    def get_input(self, prompt="> "):
        """获取用户输入"""
        return self.queues['input'].get()

    def output(self, channel, message, color=None):
        """输出到指定信息框"""
        if 0 <= channel <= self.player_count:
            data = {'type': 'log_info', 'content': str(message)}
            if color:
                data['color'] = color
            self.queues['outputs'][channel].put(json.dumps(data))

    def update_player_state(self, player_id, updates):
        """更新玩家状态"""
        if not 0 <= player_id < self.player_count:
            raise ValueError(f"玩家ID必须在1-{self.player_count}之间")

        state = self.player_states[player_id]
        for key, value in updates.items():
            if key in state:
                state[key] = value

        frontend_data = {
            'player_id': player_id + 1,
            'updates': {}
        }

        numeric_fields = [
            'money', 'ore', 'meeple', 'bank_book', 'law_book',
            'engineering_book', 'medical_book', 'magics_1',
            'magics_2', 'magics_3', 'city_amount',
            'navigation_level', 'shovel_level'
        ]

        for field in numeric_fields:
            if field in updates:
                frontend_data['updates'][field] = state[field]

        title_fields = ['planning_card', 'faction', 'score']
        for field in title_fields:
            if field in updates:
                frontend_data['updates'][field] = state[field]

        self.queues['outputs'][player_id + 1].put(json.dumps({
            'type': 'state_update',
            'data': frontend_data
        }))

        return True

    def update_global_status(self, message):
        """更新全局状态"""
        self.queues['global_status'].put(json.dumps({
            'type': 'global_state',
            'content': message
        }))

    def update_terrain(self, row, col, terrain_type):
        """更新地图地形"""
        if not 0 <= row <= 8 or not 0 <= col <= 12:
            raise ValueError("行索引必须在0-8之间，列索引必须在0-12之间")

        if terrain_type not in range(8):
            raise ValueError("地形类型必须在0-7之间")

        terrain_data = {
            'type': 'terrain_update',
            'data': {
                'row': row,
                'col': col,
                'terrain_type': terrain_type
            }
        }

        self.queues['global_status'].put(json.dumps(terrain_data))

    def update_building(self, hex_row, hex_col, building_color, building_id, mode='replace'):
        """在指定六边形上放置元素"""
        if not (0 <= hex_row <= 8 and 0 <= hex_col <= 12):
            raise ValueError("六边形坐标必须在有效范围内: 行(0-8), 列(0-12)")

        if building_color not in range(8):
            raise ValueError("x参数必须在有效范围内")

        if building_id not in range(1, 9):
            raise ValueError("y参数必须在1-8之间")

        if mode not in ['replace', 'overlay']:
            raise ValueError("模式必须是 'replace' 或 'overlay'")

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

        self.queues['global_status'].put(json.dumps(element_data))
        return True

    def set_round_scoring(self, round_num, round_scoring_id):
        """设置回合计分图片"""
        if not 1 <= round_num <= 6:
            raise ValueError("回合数必须在1-6之间")

        if not 0 <= round_scoring_id <= 12:
            raise ValueError("计分图片编号必须在0-12之间")

        scoring_data = {
            'type': 'round_scoring',
            'data': {
                'round': round_num,
                'x': round_scoring_id
            }
        }

        self.queues['global_status'].put(json.dumps(scoring_data))
        return True

    def set_final_round_bonus(self, final_scoring_id):
        """设置第6回合的叠加奖励图片"""
        if not 1 <= final_scoring_id <= 4:
            raise ValueError("奖励图片编号必须在1-4之间")

        bonus_data = {
            'type': 'final_round_bonus',
            'data': {
                'x': final_scoring_id + 12
            }
        }

        self.queues['global_status'].put(json.dumps(bonus_data))
        return True

    def set_bonus_columns(self, round_bonus_ids):
        """全量更新右侧助推板块图片"""
        if not isinstance(round_bonus_ids, list):
            raise ValueError("参数必须是列表")

        for x in round_bonus_ids:
            if not 1 <= x <= 20:
                raise ValueError("助推板块图片编号必须在1-20之间")

        bonus_columns_data = {
            'type': 'bonus_columns',
            'data': {
                'x_list': round_bonus_ids
            }
        }

        self.queues['global_status'].put(json.dumps(bonus_columns_data))
        return True

    def round_update(self, round):
        """回合更新"""
        round_update_data = {
            'type': 'round_scoring_update',
            'data': {
                'round': round
            }
        }
        self.queues['global_status'].put(json.dumps(round_update_data))
        return True

    def get_round_bonus(self, setup_round_booster_ids, round_booster_id):
        """获取回合的助推图片编号"""
        if not 1 <= round_booster_id <= 10:
            raise ValueError("回合的助推图片编号必须在1-10之间")

        get_booster_data = {
            'type': 'round_bonus_get',
            'data': {
                'round_booster_index': setup_round_booster_ids.index(round_booster_id),
            }
        }

        self.queues['global_status'].put(json.dumps(get_booster_data))
        return True

    def return_round_bonus(self, setup_round_booster_ids, round_booster_id):
        """返还回合助推图片"""
        if not 1 <= round_booster_id <= 10:
            raise ValueError("回合的助推图片编号必须在1-10之间")

        get_booster_data = {
            'type': 'round_bonus_back',
            'data': {
                'round_booster_index': setup_round_booster_ids.index(round_booster_id),
            }
        }

        self.queues['global_status'].put(json.dumps(get_booster_data))
        return True

    def highlight_hex(self, hex_list):
        """高亮可选地块"""
        hex_list_data = {
            'type': 'highlight_hex',
            'data': {
                'hex_list': hex_list,
            }
        }

        self.queues['global_status'].put(json.dumps(hex_list_data))
        return True


class Silence_IO:
    """静默IO类（用于模拟模式）"""
    def get_input(self, prompt='>'):
        pass
    def output(self, channel, message, color=None):
        pass
    def update_player_state(self, player_id, updates):
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
    def highlight_hex(self, hex_list):
        pass


# 全局API实例
_api_instance = None


def get_api_instance(host='127.0.0.1', port=5001, player_count=3, static_folder=None):
    """获取或创建API实例（单例模式）"""
    global _api_instance
    if _api_instance is None:
        _api_instance = GamePanelAPI(host, port, player_count, static_folder)
    return _api_instance


def create_api(host='127.0.0.1', port=5001, player_count=3, static_folder=None):
    """创建新的API实例"""
    return GamePanelAPI(host, port, player_count, static_folder)


if __name__ == "__main__":
    # 测试运行
    api = GamePanelAPI(player_count=3)
    print(f"API服务启动在 http://127.0.0.1:5001")
    api.run()
