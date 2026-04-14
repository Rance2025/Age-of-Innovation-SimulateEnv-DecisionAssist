"""所有路由定义"""
import json
import os
import queue
import time
import yaml
import threading

from flask import Blueprint, request, jsonify, Response, send_file, send_from_directory

from backend.logger import get_logger

logger = get_logger(__name__)

# 全局消息队列（用于 SSE 推送）
_message_queue = queue.Queue()
_message_lock = threading.Lock()
_message_listeners: list = []


def register_message_listener(callback):
    """注册消息监听器（用于 SSE）"""
    with _message_lock:
        _message_listeners.append(callback)


def unregister_message_listener(callback):
    """注销消息监听器"""
    with _message_lock:
        if callback in _message_listeners:
            _message_listeners.remove(callback)


def put_message(message: dict):
    """推送消息到队列和所有监听器"""
    # 放入队列（供 SSE 拉取）
    _message_queue.put(json.dumps(message))

    # 推送给所有监听器（实时推送）
    with _message_lock:
        listeners = _message_listeners.copy()

    for listener in listeners:
        try:
            listener(message)
        except Exception:
            pass
routes_bp = Blueprint('routes', __name__)

# 服务器启动时间戳 - 用于检测后端是否重启
_server_start_time = time.time()

# 加载配置
def load_config():
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.yaml')
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def get_active_game_controller():
    """获取当前运行中的游戏控制器。"""
    from backend.game.start_game import _game_controllers

    for _, controller in _game_controllers.items():
        if controller.is_running:
            return controller

    return None


# ===== 静态路由 =====

@routes_bp.route('/')
def index():
    """首页"""
    config = load_config()
    return {
        'status': 'ok',
        'service': 'Game Panel API',
        'version': '3.0',
        'player_count': config['players']['default_count']
    }


@routes_bp.route('/config')
def get_config():
    """获取配置"""
    config = load_config()
    return jsonify({
        'player_count': config['players']['default_count'],
        'api_version': '3.0',
        'min_players': config['players']['min_count'],
        'max_players': config['players']['max_count']
    })


@routes_bp.route('/api/server/info', methods=['GET'])
def get_server_info():
    """获取服务器信息，包括启动时间戳"""
    return jsonify({
        'status': 'success',
        'start_time': _server_start_time,
        'timestamp': time.time()
    })


@routes_bp.route('/images/<path:filename>')
def serve_image(filename):
    """提供图片"""
    config = load_config()
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    image_path = os.path.join(base_dir, config['paths']['static_folder'], filename)
    if not os.path.exists(image_path):
        return "Image not found", 404
    return send_file(image_path)


@routes_bp.route('/assets/<path:filename>')
def serve_assets(filename):
    """提供静态资源"""
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    assets_dir = os.path.join(base_dir, 'frontend', 'assets')
    return send_from_directory(assets_dir, filename)


# ===== 游戏路由 =====

@routes_bp.route('/input', methods=['POST'])
def handle_input():
    """处理用户输入 - 转发到 GameController"""
    try:
        # 获取输入内容
        if request.is_json:
            data = request.get_json()
            action_id = data.get('action_id')
        else:
            # 兼容表单格式
            cmd = request.form.get('command', '')
            try:
                action_id = int(cmd)
            except ValueError:
                return jsonify({'error': 'Invalid action_id'}), 400

        if action_id is None:
            return jsonify({'error': 'action_id is required'}), 400

        # 获取当前活跃的游戏控制器
        controller = get_active_game_controller()
        if not controller:
            return jsonify({'error': 'No active game found'}), 404

        # 提交行动
        success = controller.submit_action(action_id)

        if success:
            return jsonify({'status': 'success', 'action_id': action_id})
        else:
            return jsonify({'error': 'Failed to submit action'}), 400

    except Exception as e:
        logger.error(f"处理输入失败: {str(e)}")
        return jsonify({'error': str(e)}), 500


@routes_bp.route('/api/game/start', methods=['POST'])
def start_game():
    """启动游戏"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # 启动游戏线程
        import threading
        thread = threading.Thread(target=_run_game, args=(data,), daemon=True)
        thread.start()

        return jsonify({
            'status': 'success',
            'message': 'Game started successfully',
            'data': data
        }), 200

    except Exception as e:
        logger.error(f"启动游戏失败: {str(e)}")
        return jsonify({'error': str(e)}), 500


@routes_bp.route('/api/game/status', methods=['GET'])
def game_status():
    """获取游戏状态"""
    # 简化实现，实际应该查询游戏线程状态
    return jsonify({'running': False})


@routes_bp.route('/api/game/state', methods=['GET'])
def get_game_state():
    """获取完整游戏状态（供前端全量查询）"""
    try:
        from backend.game.start_game import get_game_controller, _game_controllers
        
        # 获取客户端版本号
        client_version = request.args.get('client_version', type=int)
        
        # 获取当前运行的游戏控制器
        if _game_controllers:
            # 取第一个运行中的游戏
            game_id = list(_game_controllers.keys())[0]
            controller = get_game_controller(game_id)
            
            if controller and controller.state_manager:
                state = controller.state_manager.get_full_state()
                
                if state:
                    # 如果提供了版本号且匹配，返回 up_to_date
                    if client_version is not None and state.get('version') == client_version:
                        return jsonify({
                            'up_to_date': True,
                            'version': client_version
                        })
                    
                    return jsonify({
                        'status': 'success',
                        **state
                    })
        
        
        # 没有运行中的游戏，返回空状态
        return jsonify({
            'status': 'error',
            'message': 'No running game'
        }), 404
        
    except Exception as e:
        logger.error(f"获取游戏状态失败: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@routes_bp.route('/api/game/action', methods=['POST'])
def submit_action():
    """
    提交玩家行动

    请求体：
    {
        "action_id": 65,
        "player_id": 0,  // 可选，用于验证
        "selection_source": "manual",  // 可选，manual / system
        "selection_strategy": "random"  // 可选
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        action_id = data.get('action_id')
        player_id = data.get('player_id')
        selection_source = data.get('selection_source', 'manual')
        selection_strategy = data.get('selection_strategy')

        if action_id is None:
            return jsonify({'error': 'action_id is required'}), 400

        # 获取当前活跃的游戏控制器
        controller = get_active_game_controller()
        if not controller:
            return jsonify({'error': 'No active game found'}), 404

        # 提交行动
        success = controller.submit_action(
            action_id,
            player_id,
            selection_source=selection_source,
            selection_strategy=selection_strategy
        )

        if success:
            return jsonify({
                'status': 'success',
                'message': 'Action submitted successfully',
                'action_id': action_id
            })
        else:
            return jsonify({
                'error': 'Failed to submit action',
                'message': 'Game not running or invalid action'
            }), 400

    except Exception as e:
        logger.error(f"提交行动失败: {str(e)}")
        return jsonify({'error': str(e)}), 500


@routes_bp.route('/api/game/strategy/recommend', methods=['POST'])
def recommend_strategy_action():
    """获取当前策略推荐的行动，不立即执行。"""
    try:
        data = request.get_json() or {}
        strategy_id = data.get('strategy_id')
        player_id = data.get('player_id')

        if not isinstance(strategy_id, str) or not strategy_id.strip():
            return jsonify({'error': 'strategy_id is required'}), 400

        controller = get_active_game_controller()
        if not controller:
            return jsonify({'error': 'No active game found'}), 404

        recommendation = controller.recommend_strategy_action(strategy_id, player_id)
        return jsonify({
            'status': 'success',
            **recommendation
        })
    except ValueError as error:
        return jsonify({'error': str(error)}), 400
    except Exception as error:
        logger.error(f"策略推荐失败: {str(error)}")
        return jsonify({'error': str(error)}), 500


@routes_bp.route('/api/game/strategy/execute', methods=['POST'])
def execute_strategy_action():
    """按指定策略立即执行当前推荐行动。"""
    try:
        data = request.get_json() or {}
        strategy_id = data.get('strategy_id')
        player_id = data.get('player_id')

        if not isinstance(strategy_id, str) or not strategy_id.strip():
            return jsonify({'error': 'strategy_id is required'}), 400

        controller = get_active_game_controller()
        if not controller:
            return jsonify({'error': 'No active game found'}), 404

        recommendation = controller.execute_strategy_action(strategy_id, player_id)
        return jsonify({
            'status': 'success',
            **recommendation
        })
    except ValueError as error:
        return jsonify({'error': str(error)}), 400
    except RuntimeError as error:
        return jsonify({'error': str(error)}), 400
    except Exception as error:
        logger.error(f"策略执行失败: {str(error)}")
        return jsonify({'error': str(error)}), 500


@routes_bp.route('/api/game/stop', methods=['POST'])
def stop_game():
    """停止当前运行的游戏"""
    try:
        from backend.game.start_game import _game_controllers, remove_game_controller

        # 找到正在运行的游戏控制器并停止
        stopped_games = []
        for game_id in list(_game_controllers.keys()):
            controller = _game_controllers[game_id]
            if controller.is_running:
                controller.stop()
                stopped_games.append(game_id)
            remove_game_controller(game_id)

        if stopped_games:
            return jsonify({
                'status': 'success',
                'message': f'Games stopped: {stopped_games}'
            })
        else:
            return jsonify({
                'status': 'success',
                'message': 'No running games found'
            })

    except Exception as e:
        logger.error(f"停止游戏失败: {str(e)}")
        return jsonify({'error': str(e)}), 500


def _run_game(game_data):
    """在后台运行游戏 - 使用 GameController"""
    import sys
    import time
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

    from backend.game.start_game import create_game_controller, get_default_init_settings, DEFAULT_TIMER_CONFIG
    from backend.logger import get_logger

    logger = get_logger(__name__)
    logger.info("=" * 60)
    logger.info("游戏线程启动 (使用 GameController)")
    logger.info("=" * 60)

    try:
        # 获取游戏参数
        game_id = game_data.get('game_id', f"game_{time.time()}")
        num_players = game_data.get('num_players', 3)
        init_settings = game_data.get('init_settings', get_default_init_settings())
        timer_config = game_data.get('timer_config', DEFAULT_TIMER_CONFIG.copy())

        # 创建游戏控制器（传入 timer_config）
        controller = create_game_controller(game_id, num_players, timer_config)
        controller.set_message_callback(put_message)

        # 启动游戏
        controller.start(init_settings)

        # 等待游戏结束
        while controller.is_running:
            time.sleep(0.1)

        logger.info(f"游戏结束，结果: {controller.final_scores}")

    except Exception as e:
        logger.error(f"游戏运行出错: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())


# ===== 历史记录路由 =====

@routes_bp.route('/api/games', methods=['GET'])
def list_games():
    """获取游戏列表"""
    try:
        from ..database import GameRepository
        repo = GameRepository()

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)

        filters = {}
        num_players = request.args.get('num_players', type=int)
        if num_players:
            filters['num_players'] = num_players

        result = repo.list_games(page=page, per_page=per_page, filters=filters if filters else None)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@routes_bp.route('/api/games', methods=['POST'])
def create_game():
    """创建游戏记录"""
    try:
        from ..database import GameRepository
        repo = GameRepository()

        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        game_id = repo.create_game(data)
        return jsonify({'id': game_id, 'message': 'Game created successfully'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@routes_bp.route('/api/games/<int:game_id>', methods=['GET'])
def get_game(game_id):
    """获取游戏详情"""
    try:
        from ..database import GameRepository
        repo = GameRepository()

        game = repo.get_game(game_id)
        if game:
            return jsonify(game)
        return jsonify({'error': 'Game not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@routes_bp.route('/api/games/<int:game_id>', methods=['DELETE'])
def delete_game(game_id):
    """删除游戏记录"""
    try:
        from ..database import GameRepository
        repo = GameRepository()

        success = repo.delete_game(game_id)
        if success:
            return jsonify({'message': 'Game deleted successfully'})
        return jsonify({'error': 'Game not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@routes_bp.route('/api/games/stats', methods=['GET'])
def get_game_stats():
    """获取游戏统计"""
    try:
        from ..database import GameRepository
        repo = GameRepository()

        stats = repo.get_statistics()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ===== SSE 流路由（简化版：统一端点）=====

def generate_stream():
    """生成 SSE 数据流 - 从统一队列获取所有消息"""
    while True:
        try:
            # 从统一输出队列获取消息
            msg = _message_queue.get(timeout=0.5)
            # 直接发送消息，已经是 JSON 格式
            yield f"data: {msg}\n\n"
        except queue.Empty:
            # 发送心跳保持连接
            yield ":heartbeat\n\n"


@routes_bp.route('/stream/game')
def stream_game():
    """统一游戏数据流 - 所有消息都通过这个端点发送

    消息格式：
    {
        "type": "player_state|global_status|terrain_update|building_update|round_scoring|...",
        "player_id": 0,
        "data": { ... }
    }
    """
    return Response(
        generate_stream(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Access-Control-Allow-Origin': '*',
            'X-Accel-Buffering': 'no'  # 禁用 Nginx 缓冲
        }
    )
