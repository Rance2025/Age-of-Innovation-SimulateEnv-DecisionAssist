"""
游戏启动入口

核心运行文件，参照 simulate.py 中的核心流程运行游戏，
使用 GameStateManager 将游戏状态同步到前端。
"""

import threading
import queue
from typing import Optional, Dict, Any, Callable, Tuple

from .aoi_game import GameEngine, ActionRequest
from .agents import create_action_agent
from .utils import GameStateManager


class GameController:
    """
    游戏控制器 - 管理游戏生命周期和输入输出

    职责：
    1. 接收用户输入（来自前端或策略Agent）
    2. 管理游戏状态同步
    3. 协调游戏主循环
    4. 支持策略Agent接口（包括AI和非AI策略）
    """

    def __init__(self, game_id: str, num_players: int = 3):
        self.game_id = game_id
        self.num_players = num_players
        self.is_running = False
        self.current_request: Optional[ActionRequest] = None

        # 输入队列 - 用于接收前端的行动选择
        self._input_queue = queue.Queue()

        # 游戏线程
        self._game_thread: Optional[threading.Thread] = None

        # 状态管理器
        self.state_manager = GameStateManager()

        # 策略Agent注册表 {player_id: Agent}
        self._agents: Dict[int, Any] = {}

        # 游戏结果
        self.final_scores: Optional[Dict] = None

        # 消息推送回调函数
        self._message_callback: Optional[Callable[[Dict], None]] = None

    def set_message_callback(self, callback: Callable[[Dict], None]):
        """设置消息推送回调函数"""
        self._message_callback = callback
        # 同时设置给状态管理器
        self.state_manager.set_message_callback(callback)

    def register_agent(self, player_id: int, agent: Any) -> bool:
        """
        注册策略Agent

        Args:
            player_id: 玩家ID (0, 1, 2)
            agent: Agent对象，必须实现 get_action(request) -> int 方法

        Returns:
            是否注册成功
        """
        if 0 <= player_id < self.num_players:
            self._agents[player_id] = agent
            return True
        return False

    def unregister_agent(self, player_id: int) -> bool:
        """注销策略Agent"""
        if player_id in self._agents:
            del self._agents[player_id]
            return True
        return False

    def _validate_current_request_for_strategy(self, player_id: Optional[int] = None) -> ActionRequest:
        """校验当前是否存在可供策略计算的行动请求。"""
        if not self.is_running or self.current_request is None:
            raise ValueError("No active action request.")

        if self.current_request.is_game_over:
            raise ValueError("Game is already over.")

        if player_id is not None and player_id != self.current_request.player_id:
            raise ValueError("player_id does not match current action player.")

        if not self.current_request.available_actions:
            raise ValueError("No available actions for current request.")

        return self.current_request

    def recommend_strategy_action(
        self,
        strategy_id: str,
        player_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        基于当前 ActionRequest 计算指定策略的推荐行动。

        Returns:
            包含 action_id / description / player_id / selection_strategy 的推荐结果
        """
        request = self._validate_current_request_for_strategy(player_id)
        agent = create_action_agent(strategy_id)
        action_id = int(agent.get_action(request))

        if action_id not in request.available_actions:
            raise ValueError(f"Strategy returned invalid action_id: {action_id}")

        strategy_name = getattr(agent, 'strategy_name', None) or strategy_id
        return {
            'action_id': action_id,
            'description': request.available_actions.get(action_id, ''),
            'player_id': request.player_id,
            'selection_strategy': strategy_name
        }

    def execute_strategy_action(
        self,
        strategy_id: str,
        player_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        基于当前 ActionRequest 执行指定策略的单次行动。

        Returns:
            推荐结果，并保证该行动已提交到输入队列
        """
        recommendation = self.recommend_strategy_action(strategy_id, player_id)
        success = self.submit_action(
            recommendation['action_id'],
            recommendation['player_id'],
            selection_source='system',
            selection_strategy=recommendation['selection_strategy']
        )

        if not success:
            raise RuntimeError("Failed to submit strategy action.")

        return recommendation

    def submit_action(
        self,
        action_id: int,
        player_id: Optional[int] = None,
        selection_source: str = 'manual',
        selection_strategy: Optional[str] = None
    ) -> bool:
        """
        提交行动ID（供前端调用）

        Args:
            action_id: 选择的行动ID
            player_id: 玩家ID（可选，用于验证）
            selection_source: 选择来源（manual / system）
            selection_strategy: 选择策略标识

        Returns:
            是否成功提交
        """
        if not self.is_running or self.current_request is None:
            return False

        # 验证玩家ID
        if player_id is not None and player_id != self.current_request.player_id:
            return False

        # 验证行动ID是否有效
        if action_id not in self.current_request.available_actions:
            return False

        normalized_source = 'system' if selection_source == 'system' else 'manual'
        normalized_strategy = selection_strategy.strip() if isinstance(selection_strategy, str) else None

        # 将行动ID放入输入队列
        self._input_queue.put({
            'action_id': action_id,
            'selection_source': normalized_source,
            'selection_strategy': normalized_strategy
        })
        return True

    def _get_action_decision(self, request: ActionRequest) -> Tuple[int, Dict[str, Optional[str]]]:
        """
        获取行动决策信息

        逻辑：
        1. 检查当前玩家是否注册了Agent，如有则调用Agent返回action_id
        2. 如没有Agent，则等待从前端输入（无限等待，不设置超时）

        Args:
            request: 当前行动请求

        Returns:
            (行动ID, 选择元数据)
        """
        player_id = request.player_id

        # 1. 检查是否有Agent
        if player_id in self._agents:
            agent = self._agents[player_id]
            action_id = agent.get_action(request)
            strategy_name = getattr(agent, 'strategy_name', None) or getattr(agent, 'name', None) or agent.__class__.__name__
            return action_id, {
                'selection_source': 'system',
                'selection_strategy': strategy_name
            }

        # 2. 等待前端输入（无限等待）
        self._push_available_actions(request)
        payload = self._input_queue.get()

        if isinstance(payload, dict):
            action_id = int(payload.get('action_id'))
            selection_source = 'system' if payload.get('selection_source') == 'system' else 'manual'
            selection_strategy = payload.get('selection_strategy')
            normalized_strategy = selection_strategy.strip() if isinstance(selection_strategy, str) else None
            return action_id, {
                'selection_source': selection_source,
                'selection_strategy': normalized_strategy
            }

        return int(payload), {
            'selection_source': 'manual',
            'selection_strategy': None
        }

    def _record_action_selection_metadata(self, request: ActionRequest, metadata: Dict[str, Optional[str]]):
        """在后端登记下一条行动历史对应的选择来源元数据。"""
        game_state = getattr(request, 'game_state', None)
        raw_history = list(getattr(game_state, 'action_history', []) or [])
        next_raw_action_index = len(raw_history) + 1

        self.state_manager.record_action_selection_metadata(
            raw_action_index=next_raw_action_index,
            selection_source=metadata.get('selection_source', 'manual') or 'manual',
            selection_strategy=metadata.get('selection_strategy')
        )

    def _push_available_actions(self, request: ActionRequest):
        """推送可选行动到前端（通过回调函数）"""
        if not self._message_callback:
            return

        try:
            actions = [
                {'id': k, 'description': v}
                for k, v in request.available_actions.items()
            ]

            self._message_callback({
                'type': 'actions',
                'player_id': request.player_id,
                'data': {
                    'actions': actions,
                    'count': len(actions),
                    'current_player': request.player_id
                }
            })
        except Exception:
            pass

    def _game_loop(self, init_settings: Dict):
        """游戏主循环（在独立线程中运行）"""
        try:
            # 创建游戏引擎
            game = GameEngine(
                num_players=self.num_players,
                init_settings=init_settings
            ).run_game()

            # 获取初始请求
            request = next(game)
            self.current_request = request

            # 更新状态管理器（首次会推送全量状态）
            self.state_manager.update_from_action_request(request)

            # 游戏主循环
            while not request.is_game_over:
                # 获取行动ID（从Agent或前端）
                action_id, selection_metadata = self._get_action_decision(request)
                self._record_action_selection_metadata(request, selection_metadata)

                # 发送行动ID给游戏引擎
                request = game.send(action_id)
                self.current_request = request

                # 更新游戏状态管理器（计算增量并推送）
                self.state_manager.update_from_action_request(request)

            # 游戏结束
            self.final_scores = request.final_scores
            self._handle_game_end(request)

        except Exception:
            import traceback
            traceback.print_exc()
        finally:
            self.is_running = False
            self.current_request = None

    def _handle_game_end(self, request: ActionRequest):
        """处理游戏结束"""
        # 推送游戏结束消息到前端
        if not self._message_callback:
            return

        try:
            self._message_callback({
                'type': 'game_over',
                'data': {
                    'final_scores': request.final_scores
                }
            })
        except Exception:
            pass

    def start(self, init_settings: Optional[Dict] = None) -> bool:
        """
        启动游戏

        Args:
            init_settings: 初始化设置

        Returns:
            是否成功启动
        """
        if self.is_running:
            return False

        self.is_running = True

        # 默认初始化设置
        if init_settings is None:
            init_settings = get_default_init_settings()

        # 启动游戏线程
        self._game_thread = threading.Thread(
            target=self._game_loop,
            args=(init_settings,),
            daemon=True
        )
        self._game_thread.start()

        return True

    def stop(self):
        """停止游戏"""
        self.is_running = False
        # 清空输入队列，防止阻塞
        while not self._input_queue.empty():
            try:
                self._input_queue.get_nowait()
            except queue.Empty:
                break


# ========== 全局游戏控制器注册表 ==========

_game_controllers: Dict[str, GameController] = {}


def get_game_controller(game_id: str) -> Optional[GameController]:
    """获取游戏控制器"""
    return _game_controllers.get(game_id)


def create_game_controller(game_id: str, num_players: int = 3) -> GameController:
    """创建游戏控制器"""
    controller = GameController(game_id, num_players)
    _game_controllers[game_id] = controller
    return controller


def remove_game_controller(game_id: str):
    """移除游戏控制器"""
    if game_id in _game_controllers:
        _game_controllers[game_id].stop()
        del _game_controllers[game_id]


def get_default_init_settings() -> dict:
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
