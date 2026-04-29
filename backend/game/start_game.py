"""
游戏启动入口

核心运行文件，参照 simulate.py 中的核心流程运行游戏，
使用 GameStateManager 将游戏状态同步到前端。
"""

import copy
import threading
import queue
import time
from datetime import datetime
from typing import Optional, Dict, Any, Callable, Tuple, List

from .aoi_game import GameEngine, ActionRequest
from .agents import create_action_agent
from .utils import GameStateManager


DEFAULT_TIMER_CONFIG = {
    'main_time': 5 * 60 * 1000,
    'byo_yomi_time': 20 * 1000,
    'grace_period': 300,
    'timeout_strategy': 'random_fast_action'
}

ACTION_SELECTION_MODE_PLAYER_CHOICE = 'player_choice'
ACTION_SELECTION_MODE_ACCEPTED = 'accepted'
ACTION_SELECTION_MODE_REJECTED = 'rejected'
ACTION_SELECTION_MODE_STRATEGY_EXECUTE = 'strategy_execute'
ACTION_SELECTION_MODE_AI_AGENT = 'ai_agent'
ACTION_SELECTION_MODE_TIMEOUT_AGENT = 'timeout_agent'


class GameStopped(Exception):
    """Raised when a running game is explicitly stopped."""


STOP_INPUT = {'__stop__': True}


class GameController:
    """
    游戏控制器 - 管理游戏生命周期和输入输出

    职责：
    1. 接收用户输入（来自前端或策略Agent）
    2. 管理游戏状态同步
    3. 协调游戏主循环
    4. 支持策略Agent接口（包括AI和非AI策略）
    """

    def __init__(self, game_id: str, num_players: int = 3, timer_config: dict = None):
        self.game_id = game_id
        self.num_players = num_players
        self.is_running = False
        self.current_request: Optional[ActionRequest] = None
        self._stop_event = threading.Event()

        # 合并前端传入的 timer_config 与默认值，确保所有必要字段都存在
        self._timer_config = DEFAULT_TIMER_CONFIG.copy()
        if timer_config:
            self._timer_config.update(timer_config)
        self._main_time = self._timer_config['main_time']
        self._byo_yomi_time = self._timer_config['byo_yomi_time']
        self._grace_period = self._timer_config['grace_period']
        self._timeout_strategy = self._timer_config['timeout_strategy']

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

        # 保存原始和已解析的初始设置
        self._original_init_settings: Optional[Dict] = None
        self._resolved_init_settings: Optional[Dict] = None
        self._requested_game_payload: Optional[Dict[str, Any]] = None
        self._game_engine = None

        # 消息推送回调函数
        self._message_callback: Optional[Callable[[Dict], None]] = None

        # 计时器状态
        self._player_remaining_times: List[int] = []
        self._action_start_time: int = 0
        self._action_deadline: int = 0

        # 历史存档
        self._history_repository = None
        self._history_saved = False
        self._started_at_iso: Optional[str] = None

    def set_message_callback(self, callback: Optional[Callable[[Dict], None]]):
        """设置消息推送回调函数"""
        self._message_callback = callback
        # 同时设置给状态管理器
        self.state_manager.set_message_callback(callback)

    def set_requested_game_payload(self, game_payload: Optional[Dict[str, Any]]):
        """保存启动时的原始对局配置，供历史存档使用。"""
        self._requested_game_payload = copy.deepcopy(game_payload) if isinstance(game_payload, dict) else None

    def _get_history_repository(self):
        if self._history_repository is None:
            from backend.database import GameRepository
            self._history_repository = GameRepository()
        return self._history_repository

    def _extract_game_mode(self) -> str:
        game_mode = (self._requested_game_payload or {}).get('game_mode', {})
        if isinstance(game_mode, dict):
            mode_value = game_mode.get('type')
            if isinstance(mode_value, str) and mode_value.strip():
                return mode_value.strip()
        return 'custom'

    def _build_requested_config(self) -> Dict[str, Any]:
        requested_payload = self._requested_game_payload or {}
        init_settings = requested_payload.get('init_settings')
        if not isinstance(init_settings, dict):
            init_settings = self._original_init_settings or {}

        game_mode = self._extract_game_mode()
        raw_timer_config = requested_payload.get('timer_config')
        if not isinstance(raw_timer_config, dict):
            raw_timer_config = {}
        return {
            'game_mode': game_mode,
            'timer_mode': game_mode,
            'timer_config': copy.deepcopy(raw_timer_config),
            'init_settings': copy.deepcopy(init_settings),
        }

    def _build_resolved_config(self) -> Dict[str, Any]:
        return {
            'timer': {
                'main_time': self._main_time,
                'byo_yomi_time': self._byo_yomi_time,
                'grace_period': self._grace_period,
                'timeout_strategy_name': self._timeout_strategy,
            },
            'setup': copy.deepcopy(self._resolved_init_settings or {}),
        }

    def _build_player_history_entries(self) -> List[Dict[str, Any]]:
        players = []
        raw_players = (self._requested_game_payload or {}).get('players', [])
        for player_id in range(self.num_players):
            player = raw_players[player_id] if player_id < len(raw_players) else {}
            player_type = player.get('type', 'human') if isinstance(player, dict) else 'human'
            player_input_id = ''
            strategy_name = ''
            if isinstance(player, dict):
                raw_player_arg = player.get('args', '')
                normalized_player_arg = raw_player_arg.strip() if isinstance(raw_player_arg, str) else ''
                raw_player_input_id = player.get('player_input_id', '')
                normalized_player_input_id = raw_player_input_id.strip() if isinstance(raw_player_input_id, str) else ''
                raw_strategy_id = player.get('strategy_id', '')
                normalized_strategy_id = raw_strategy_id.strip() if isinstance(raw_strategy_id, str) else ''

                if player_type == 'ai':
                    strategy_name = normalized_strategy_id or normalized_player_arg
                    if strategy_name == 'random':
                        strategy_name = 'random_pure'
                else:
                    player_input_id = normalized_player_input_id or normalized_player_arg

            players.append({
                'player_id': player_id,
                'player_type': player_type,
                'player_input_id': player_input_id,
                'strategy_name': strategy_name,
            })
        return players

    def _extract_action_history_for_save(self) -> List[Dict[str, Any]]:
        full_state = self.state_manager.get_full_state() if self.state_manager else None
        state = full_state.get('state') if isinstance(full_state, dict) else None
        raw_history = state.get('action_history', []) if isinstance(state, dict) else []
        if not isinstance(raw_history, list):
            return []

        return [
            copy.deepcopy(entry)
            for entry in raw_history
            if isinstance(entry, dict) and entry.get('kind', 'action') == 'action'
        ]

    def _save_game_history(self, end_status: str, error_message: Optional[str] = None):
        """保存一局游戏的完整历史记录。"""
        if self._history_saved or not self._started_at_iso:
            return None

        ended_at_iso = datetime.now().astimezone().isoformat()
        action_history = self._extract_action_history_for_save()
        payload = {
            'schema_version': '1.0',
            'game_id': self.game_id,
            'started_at': self._started_at_iso,
            'ended_at': ended_at_iso,
            'end_status': end_status,
            'error_message': error_message,
            'num_players': self.num_players,
            'game_mode': self._extract_game_mode(),
            'path_length': len(action_history),
            'requested_config': self._build_requested_config(),
            'resolved_config': self._build_resolved_config(),
            'players': self._build_player_history_entries(),
            'action_history': action_history,
            'final_player_remaining_ms': self._player_remaining_times.copy(),
            'final_scores': copy.deepcopy(self.final_scores),
        }

        self._get_history_repository().create_game(payload)
        self._history_saved = True
        return payload

    def _clear_input_queue(self):
        while not self._input_queue.empty():
            try:
                self._input_queue.get_nowait()
            except queue.Empty:
                break

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
        if self._stop_event.is_set():
            raise ValueError("Game is stopping.")

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
            包含 action_id / description / player_id / strategy_name 的推荐结果
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
            'strategy_name': strategy_name
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
            strategy_name=recommendation['strategy_name'],
            selection_mode=ACTION_SELECTION_MODE_STRATEGY_EXECUTE
        )

        if not success:
            raise RuntimeError("Failed to submit strategy action.")

        return recommendation

    def submit_action(
        self,
        action_id: int,
        player_id: Optional[int] = None,
        strategy_name: Optional[str] = None,
        selection_mode: Optional[str] = None
    ) -> bool:
        """
        提交行动ID（供前端调用）

        Args:
            action_id: 选择的行动ID
            player_id: 玩家ID（可选，用于验证）
            strategy_name: 关联的策略名称
            selection_mode: 选择模式（player_choice / accepted / rejected / strategy_execute / ai_agent / timeout_agent）

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

        normalized_strategy = strategy_name.strip() if isinstance(strategy_name, str) else None
        normalized_mode = selection_mode.strip() if isinstance(selection_mode, str) else None

        # 将行动ID放入输入队列
        payload = {
            'action_id': action_id,
            'strategy_name': normalized_strategy
        }
        if normalized_mode:
            payload['selection_mode'] = normalized_mode
        self._input_queue.put(payload)
        return True

    def _get_action_decision(self, request: ActionRequest) -> Tuple[int, Dict[str, Optional[str]]]:
        """
        获取行动决策信息（带计时器）

        Args:
            request: 当前行动请求

        Returns:
            (行动ID, 选择元数据)
        """
        player_id = request.player_id

        if not self._player_remaining_times:
            self._player_remaining_times = [self._main_time] * self.num_players

        self._action_start_time = int(time.time() * 1000)
        remaining = self._player_remaining_times[player_id]
        self._action_deadline = (
            self._action_start_time + remaining
            if remaining > 0
            else self._action_start_time + self._byo_yomi_time
        )

        self._update_timer_in_state_manager(player_id)

        action_id, selection_metadata = self._resolve_action_decision(request, player_id)

        # 计算下一个 action_index（用于记录用时）
        game_state = getattr(request, 'game_state', None)
        raw_history = list(getattr(game_state, 'action_history', []) or [])
        next_action_index = len(raw_history) + 1

        self._update_player_time_after_action(player_id, next_action_index)
        self._push_timer_update_after_action()

        return action_id, selection_metadata

    def _resolve_action_decision(self, request: ActionRequest, player_id: int) -> Tuple[int, Dict[str, Optional[str]]]:
        """解析行动决策，不在此处处理计时扣减。"""
        if player_id in self._agents:
            agent = self._agents[player_id]
            start_time = time.time()
            action_id = agent.get_action(request)
            elapsed = time.time() - start_time
            
            # AI 玩家最小3秒延迟（非阻塞式：游戏线程独立运行）
            min_delay = 3.0
            if elapsed < min_delay:
                time.sleep(min_delay - elapsed)
            
            strategy_name = getattr(agent, 'strategy_name', None) or getattr(agent, 'name', None) or agent.__class__.__name__
            return action_id, {
                'selection_mode': ACTION_SELECTION_MODE_AI_AGENT,
                'strategy_name': strategy_name
            }

        self._push_available_actions(request)
        payload = self._wait_for_action_with_timeout(player_id)

        if isinstance(payload, dict) and payload.get('__stop__') is True:
            raise GameStopped()

        if isinstance(payload, dict):
            action_id = int(payload.get('action_id'))
            strategy_name = payload.get('strategy_name')
            selection_mode = payload.get('selection_mode')
            normalized_strategy = strategy_name.strip() if isinstance(strategy_name, str) else None
            normalized_mode = selection_mode.strip() if isinstance(selection_mode, str) else None
            metadata = {
                'strategy_name': normalized_strategy
            }
            if normalized_mode:
                metadata['selection_mode'] = normalized_mode
            return action_id, metadata

        return int(payload), {
            'selection_mode': ACTION_SELECTION_MODE_PLAYER_CHOICE,
            'strategy_name': None
        }

    def _wait_for_action_with_timeout(self, player_id: int) -> Any:
        """等待玩家行动，基本时长耗尽后切到读秒。"""
        if self._stop_event.is_set():
            return dict(STOP_INPUT)

        remaining = self._player_remaining_times[player_id]

        if remaining > 0:
            try:
                payload = self._input_queue.get(timeout=remaining / 1000.0)
                if isinstance(payload, dict) and payload.get('__stop__') is True:
                    return dict(STOP_INPUT)
                if self._stop_event.is_set():
                    return dict(STOP_INPUT)
                return payload
            except queue.Empty:
                if self._stop_event.is_set():
                    return dict(STOP_INPUT)
                now = int(time.time() * 1000)
                self._player_remaining_times[player_id] = 0
                self._action_deadline = now + self._byo_yomi_time
                self._push_timer_state_update()

        try:
            payload = self._input_queue.get(timeout=self._byo_yomi_time / 1000.0)
            if isinstance(payload, dict) and payload.get('__stop__') is True:
                return dict(STOP_INPUT)
            if self._stop_event.is_set():
                return dict(STOP_INPUT)
            return payload
        except queue.Empty:
            if self._stop_event.is_set():
                return dict(STOP_INPUT)
            return self._execute_timeout_action(player_id)

    def _execute_timeout_action(self, player_id: int) -> Dict[str, Optional[str]]:
        """执行读秒超时后的自动行动。"""
        if self.current_request is None:
            raise RuntimeError("No current action request for timeout action.")

        try:
            agent = create_action_agent(self._timeout_strategy)
            action_id = int(agent.get_action(self.current_request))
            return {
                'action_id': action_id,
                'selection_mode': ACTION_SELECTION_MODE_TIMEOUT_AGENT,
                'strategy_name': self._timeout_strategy
            }
        except Exception:
            available = list(self.current_request.available_actions.keys())
            if not available:
                raise RuntimeError("No available actions for timeout fallback.")
            return {
                'action_id': available[0],
                'selection_mode': ACTION_SELECTION_MODE_TIMEOUT_AGENT,
                'strategy_name': None
            }

    def _push_incremental_changes(self, changes: List[Dict[str, Any]]):
        if not self._message_callback or not changes:
            return

        try:
            self._message_callback({
                'type': 'incremental',
                'changes': changes
            })
        except Exception:
            pass

    def _push_timer_patch(self, timer_patch: Dict[str, Any], meta_patch: Optional[Dict[str, Any]] = None):
        changes = [
            {
                'path': f'timer_state.{field}',
                'new_value': value,
                'change_type': 'modified'
            }
            for field, value in timer_patch.items()
        ]

        if meta_patch:
            changes.extend([
                {
                    'path': f'meta.{field}',
                    'new_value': value,
                    'change_type': 'modified'
                }
                for field, value in meta_patch.items()
            ])

        self._push_incremental_changes(changes)

    def _update_timer_in_state_manager(self, player_id: int):
        timer_patch = {
            'action_deadline': self._action_deadline,
            'current_player_remaining': self._player_remaining_times[player_id],
            'all_players_remaining': self._player_remaining_times.copy(),
            'main_time_limit': self._main_time,
            'byo_yomi_time_limit': self._byo_yomi_time
        }

        self.state_manager.update_timer_state(**timer_patch)
        self._push_timer_patch(timer_patch, meta_patch={'current_player_id': player_id})

    def _push_timer_state_update(self):
        timer_patch = {
            'action_deadline': self._action_deadline,
            'current_player_remaining': 0,
            'all_players_remaining': self._player_remaining_times.copy()
        }

        self.state_manager.update_timer_state(**timer_patch)
        self._push_timer_patch(timer_patch)

    def _push_timer_update_after_action(self):
        self._push_timer_patch({
            'all_players_remaining': self._player_remaining_times.copy()
        })

    def _update_player_time_after_action(self, player_id: int, action_index: int = None):
        """行动完成后更新玩家剩余主时间。"""
        if not self._player_remaining_times or player_id < 0:
            return

        action_end_time = int(time.time() * 1000)
        time_spent = action_end_time - self._action_start_time
        remaining_before = self._player_remaining_times[player_id]

        if remaining_before == 0:
            deadline_with_grace = self._action_deadline + self._grace_period
            if action_end_time > deadline_with_grace:
                print(f"[Timer] Player {player_id + 1} exceeded deadline with grace period")
        else:
            new_remaining = max(0, remaining_before - time_spent)
            self._player_remaining_times[player_id] = new_remaining

            if new_remaining == 0 and remaining_before > 0:
                self._action_deadline = action_end_time + self._byo_yomi_time

        self.state_manager.update_timer_state(
            current_player_remaining=self._player_remaining_times[player_id],
            action_deadline=self._action_deadline,
            all_players_remaining=self._player_remaining_times.copy()
        )

        # 记录行动用时
        if action_index is not None and time_spent > 0:
            self.state_manager.record_action_duration(
                raw_action_index=action_index,
                duration_ms=time_spent
            )

    def _record_action_selection_metadata(self, request: ActionRequest, metadata: Dict[str, Optional[str]]):
        """在后端登记下一条行动历史对应的策略元数据。"""
        game_state = getattr(request, 'game_state', None)
        raw_history = list(getattr(game_state, 'action_history', []) or [])
        next_raw_action_index = len(raw_history) + 1

        self.state_manager.record_action_selection_metadata(
            raw_action_index=next_raw_action_index,
            strategy_name=metadata.get('strategy_name'),
            selection_mode=metadata.get('selection_mode')
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

            message = {
                'type': 'actions',
                'player_id': request.player_id,
                'is_ai_player': request.player_id in self._agents,
                'data': {
                    'actions': actions,
                    'count': len(actions),
                    'current_player': request.player_id
                }
            }
            # print(f"[DEBUG] 推送 actions 消息: {message}")
            self._message_callback(message)
        except Exception:
            pass

    def _game_loop(self, init_settings: Dict):
        """游戏主循环（在独立线程中运行）"""
        try:
            # 创建游戏引擎
            engine = GameEngine(
                num_players=self.num_players,
                init_settings=init_settings
            )
            self._game_engine = engine
            game = engine.run_game()

            # 获取初始请求
            request = next(game)
            self.current_request = request

            # 提取已解析的初始设置（从 game_state.setup）
            if hasattr(engine, 'game_state') and hasattr(engine.game_state, 'setup'):
                setup = engine.game_state.setup
                gs = engine.game_state

                # 玩家顺序：0-based 转 1-based
                init_player_order = [i + 1 for i in gs.init_player_order]

                # 规划卡：从6张反推被排除的1张
                all_planning_cards = list(range(1, 8))
                excluded = [c for c in all_planning_cards if c not in setup.selected_planning_cards]
                planning_cards = excluded[0] if excluded else 1

                self._resolved_init_settings = {
                    'init_player_order': init_player_order,
                    'setup_tiles': {
                        'planning_cards': planning_cards,
                        'factions': setup.selected_factions,
                        'palace_tiles': setup.selected_palace_tiles,
                        'round_boosters': setup.selected_round_boosters,
                        'round_scoring': setup.round_scoring_order,
                        'final_scoring': setup.final_scoring,
                        'ability_tiles': setup.ability_tiles_order,
                        'science_tiles': setup.science_tiles_order,
                        'book_actions': setup.selected_book_actions,
                    }
                }

            if not self._player_remaining_times:
                self._player_remaining_times = [self._main_time] * self.num_players

            self.state_manager.update_timer_state(
                all_players_remaining=self._player_remaining_times.copy(),
                main_time_limit=self._main_time,
                byo_yomi_time_limit=self._byo_yomi_time
            )

            # 更新状态管理器（首次会推送全量状态）
            self.state_manager.update_from_action_request(request)

            # 游戏主循环
            while not request.is_game_over and self.is_running and not self._stop_event.is_set():
                # AI 回合也需要推送 actions，让前端知道是 AI 在行动
                if request.player_id in self._agents:
                    self._push_available_actions(request)

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
            self._save_game_history('finished')
            self._handle_game_end(request)

        except GameStopped:
            self._save_game_history('interrupted')
        except Exception as error:
            import traceback
            traceback.print_exc()
            self._save_game_history('error', error_message=str(error))
        finally:
            self.is_running = False
            self.current_request = None
            self._game_engine = None

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
        self._stop_event.clear()
        self.final_scores = None
        self._clear_input_queue()
        self._player_remaining_times = []
        self._action_start_time = 0
        self._action_deadline = 0
        self._game_engine = None
        self._history_saved = False
        self._started_at_iso = datetime.now().astimezone().isoformat()

        # 默认初始化设置
        if init_settings is None:
            init_settings = get_default_init_settings()

        # 保存原始设置（用于重新初始）
        self._original_init_settings = init_settings.copy()
        self._resolved_init_settings = None

        # 启动游戏线程
        self._game_thread = threading.Thread(
            target=self._game_loop,
            args=(init_settings,),
            daemon=True
        )
        self._game_thread.start()

        return True

    def get_settings(self, mode: str = 'original') -> Optional[Dict]:
        """获取初始设置

        Args:
            mode: 'original' 返回前端传入的原始设置（含 'random'）
                  'resolved' 返回后端随机化后的实际值

        Returns:
            设置字典，或 None（如果尚未初始化）
        """
        if mode == 'original':
            return self._original_init_settings
        elif mode == 'resolved':
            return self._resolved_init_settings
        return None

    def stop(self):
        """停止游戏"""
        if not self._history_saved and self._started_at_iso:
            self._save_game_history('interrupted')

        self.is_running = False
        self._stop_event.set()
        self._clear_input_queue()
        self._input_queue.put(dict(STOP_INPUT))

        if (
            self._game_thread is not None
            and self._game_thread.is_alive()
            and threading.current_thread() is not self._game_thread
        ):
            self._game_thread.join(timeout=2.0)

        self._clear_input_queue()
        self.current_request = None
        self._game_thread = None
        self._game_engine = None


# ========== 全局游戏控制器注册表 ==========

_game_controllers: Dict[str, GameController] = {}


def get_game_controller(game_id: str) -> Optional[GameController]:
    """获取游戏控制器"""
    return _game_controllers.get(game_id)


def create_game_controller(game_id: str, num_players: int = 3, timer_config: dict = None) -> GameController:
    """创建游戏控制器"""
    controller = GameController(game_id, num_players, timer_config)
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
