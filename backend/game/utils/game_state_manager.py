"""
游戏状态管理器 (GameStateManager)

负责：
1. 接收 ActionRequest，提取并维护游戏状态
2. 计算状态增量（diff）
3. 提供状态访问接口（用于前端获取状态）
"""

import copy
import json
import os
import time
from typing import Dict, List, Optional, Any, Callable, TYPE_CHECKING
from dataclasses import asdict
from datetime import datetime

from .frontend_state_types import (
    GameMeta, TimerState, GameSetup, PlayerState, Resources, Magics, Buildings, Tracks,
    MapState, MapCell, DisplayBoardState, ScienceTrackState,
    AvailableAction, ActionHistoryEntry, FinalScore, FullGameState, StateDiff, ChangeType
)

if TYPE_CHECKING:
    from ..aoi_game import ActionRequest
    from ..aoi_game.game_state import GameStateBase

ACTION_LOG_STAGE_ORDER = (
    'setup-choice',
    'setup-build',
    'setup-effect',
    'round-1',
    'round-2',
    'round-3',
    'round-4',
    'round-5',
    'round-6'
)
ACTION_LOG_STAGE_INDEX = {
    stage_key: index
    for index, stage_key in enumerate(ACTION_LOG_STAGE_ORDER)
}
ACTION_LOG_STAGE_LABELS = {
    'setup-choice': '初始板块选择阶段',
    'setup-build': '初始建筑摆放阶段',
    'setup-effect': '初始效果结算阶段',
    'round-1': '第 1 回合开始',
    'round-2': '第 2 回合开始',
    'round-3': '第 3 回合开始',
    'round-4': '第 4 回合开始',
    'round-5': '第 5 回合开始',
    'round-6': '第 6 回合开始'
}


class GameStateManager:
    """
    游戏状态管理器
    
    职责：
    1. 接收 ActionRequest，提取并维护游戏状态
    2. 计算状态增量（diff）
    3. 提供状态访问接口（用于前端获取状态）
    """
    
    def __init__(self):
        """初始化状态管理器"""
        # 当前完整状态快照
        self._current_state: Optional[FullGameState] = None

        # 上一次推送的状态（用于计算diff）
        self._last_pushed_state: Optional[Dict] = None

        # 状态版本号（每次更新递增）
        self._version: int = 0

        # 最后更新时间
        self._last_update_time: Optional[str] = None

        # 消息推送回调函数
        self._message_callback: Optional[Callable[[Dict], None]] = None

        # 后端维护的结构化行动历史，避免前端再自行推断阶段分割线
        self._structured_action_history: List[ActionHistoryEntry] = []
        self._last_raw_action_count: int = 0
        self._last_action_log_stage_key: Optional[str] = None
        self._pending_action_selection_metadata: Dict[int, Dict[str, str]] = {}

        # 计时器状态
        self._timer_state = {
            'action_deadline': 0,
            'current_player_remaining': 0,
            'main_time_limit': 0,
            'byo_yomi_time_limit': 0,
            'all_players_remaining': []
        }
        
        # 行动展示分组数据（缓存）
        self._action_display_groups = None
        self._action_id_to_display_group = {}
        
        # 行动用时记录
        self._pending_action_durations: Dict[int, int] = {}

        # 城市板块匹配状态（跨快照）
        # 记录1：城市根节点建立日志 {player_id: [(pos_key, action_history_length), ...]}
        self._city_establishment_log: Dict[int, List[Tuple[str, int]]] = {}
        # 记录2：城市板块获取日志 {player_id: [(tile_id, action_history_length), ...]}
        self._city_tile_acquisition_log: Dict[int, List[Tuple[int, int]]] = {}
        # 记录3：匹配结果映射 {player_id: {pos_key: city_tile_id}}
        self._city_tile_assignments: Dict[int, Dict[str, int]] = {}

    def set_message_callback(self, callback: Callable[[Dict], None]):
        """设置消息推送回调函数"""
        self._message_callback = callback

    def _load_action_display_groups(self):
        """加载行动展示分组数据"""
        if self._action_display_groups is not None:
            return
        
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            json_path = os.path.join(current_dir, 'available_action_display_groups.json')
            
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self._action_display_groups = data.get('groups', [])
            
            # 构建 action_id 到显示组的映射
            for group in self._action_display_groups:
                group_label = group.get('group_label', '')
                items = group.get('items', {})
                for action_id_str, item in items.items():
                    action_id = int(action_id_str)
                    self._action_id_to_display_group[action_id] = {
                        'group_key': group.get('group_key', ''),
                        'group_label': group_label,
                        'minor_label': item.get('minor_label', ''),
                        'minor_detail': item.get('minor_detail', ''),
                        'source_action': item.get('source_action', '')
                    }
        except Exception as e:
            # 如果加载失败，使用空数据
            self._action_display_groups = []
            self._action_id_to_display_group = {}
    
    def _get_action_display_group(self, action_id: int) -> dict:
        """获取指定 action_id 的显示组信息"""
        if self._action_display_groups is None:
            self._load_action_display_groups()
        return self._action_id_to_display_group.get(action_id, {})

    def update_timer_state(self, **kwargs):
        """更新计时器状态（由 GameController 调用）"""
        self._timer_state.update(kwargs)
        if self._current_state is not None:
            self._current_state.timer_state = self._extract_timer_state()

    # ==================== 核心更新方法 ====================

    def update_from_action_request(self, request: 'ActionRequest') -> List[StateDiff]:
        """
        从 ActionRequest 更新状态并推送到前端

        这是主要入口方法，每次游戏引擎 yield 返回时调用

        Args:
            request: 游戏引擎 yield 返回的 ActionRequest

        Returns:
            状态差异列表（可用于推送到前端）
        """
        # Step 1: 提取新状态
        new_state = self._extract_state_from_request(request)

        # Step 2: 计算增量（关键步骤）
        diffs = self._calculate_optimized_diff(self._last_pushed_state, new_state)

        # Step 2.5: 跨快照匹配城市板块
        if self._last_pushed_state is not None:
            new_state_dict = self._state_to_dict(new_state)
            current_ah_length = len(new_state_dict.get('action_history', []))
            self._update_city_tile_matches(self._last_pushed_state, new_state_dict, current_ah_length)
            # 重新计算增量，因为匹配结果可能影响 city_tile_assignments
            diffs = self._calculate_optimized_diff(self._last_pushed_state, new_state)

        # Step 3: 更新当前状态
        self._current_state = new_state
        self._version += 1
        self._last_update_time = datetime.now().isoformat()

        # Step 4: 推送到前端
        self._push_to_frontend(diffs)

        # Step 5: 更新上一次推送状态
        self._last_pushed_state = self._state_to_dict(new_state)

        return diffs

    def set_message_callback(self, callback: Callable[[Dict], None]):
        """设置消息推送回调函数"""
        self._message_callback = callback

    def _push_to_frontend(self, diffs: List[StateDiff]):
        """推送状态更新到前端"""
        if not diffs:
            return

        if not self._message_callback:
            return

        try:
            # 检查是否是第一次推送（全量状态）
            if len(diffs) == 1 and diffs[0].path == '' and diffs[0].change_type == ChangeType.ADDED:
                # 第一次推送，发送全量状态
                message = {
                    'type': 'full',
                    'version': self._version,
                    'timestamp': self._last_update_time,
                    'state': diffs[0].new_value
                }
            else:
                # 增量更新消息
                message = {
                    'type': 'incremental',
                    'version': self._version,
                    'timestamp': self._last_update_time,
                    'changes': [
                        {
                            'path': d.path,
                            'new_value': d.new_value,
                            'change_type': d.change_type.value
                        }
                        for d in diffs
                    ]
                }

            self._message_callback(message)
        except Exception:
            # 推送失败不影响游戏运行
            pass
    
    def _state_to_dict(self, state: FullGameState) -> Dict:
        """将 FullGameState 转换为字典"""
        return asdict(state)
    
    # ==================== 状态提取方法 ====================
    
    def _extract_state_from_request(self, request: 'ActionRequest') -> FullGameState:
        """从 ActionRequest 提取完整状态"""
        gs = request.game_state
        
        return FullGameState(
            meta=self._extract_meta(request, gs),
            setup=self._extract_setup(gs) if gs else GameSetup(),
            players=self._extract_players(gs.players) if gs else [],
            map_state=self._extract_map_state(gs.map_board_state) if gs else MapState(),
            display_board=self._extract_display_board(gs.display_board_state, gs) if gs else DisplayBoardState(),
            available_actions=self._extract_available_actions(request.available_actions),
            action_history=self._extract_action_history(gs) if gs else [],
            final_scores=self._extract_final_scores(request.final_scores) if request.is_game_over else None,
            timer_state=self._extract_timer_state()
        )

    def _extract_meta(self, request: 'ActionRequest', gs: Optional['GameStateBase']) -> GameMeta:
        """提取元信息"""
        setup_choice_is_completed = bool(gs and getattr(gs, 'setup_choice_is_completed', False))
        setup_build_is_completed = bool(gs and getattr(gs, 'setup_build_is_completed', False))
        return GameMeta(
            round=gs.round if gs else 0,
            num_players=gs.num_players if gs else 3,
            current_player_id=request.player_id,
            action_type=request.action_type,
            is_game_over=request.is_game_over,
            setup_choice_is_completed=setup_choice_is_completed,
            setup_build_is_completed=setup_build_is_completed,
            current_player_order=list(getattr(gs, 'current_player_order', [])) if gs else [],
            pass_order=list(getattr(gs, 'pass_order', [])) if gs else []
        )

    def _extract_timer_state(self) -> TimerState:
        """提取计时器状态"""
        all_players_remaining = self._timer_state.get('all_players_remaining', [])
        if not all_players_remaining:
            num_players = getattr(self._current_state, 'meta', None)
            if num_players:
                num_players = getattr(num_players, 'num_players', 3)
            else:
                num_players = 3
            all_players_remaining = [0] * num_players

        return TimerState(
            action_deadline=self._timer_state.get('action_deadline', 0),
            current_player_remaining=self._timer_state.get('current_player_remaining', 0),
            main_time_limit=self._timer_state.get('main_time_limit', 0),
            byo_yomi_time_limit=self._timer_state.get('byo_yomi_time_limit', 0),
            all_players_remaining=all_players_remaining
        )

    def _get_action_log_stage_key(self, gs: 'GameStateBase') -> str:
        """根据当前游戏状态返回行动记录阶段键。"""
        round_value = getattr(gs, 'round', 0)
        try:
            normalized_round = int(round_value)
        except (TypeError, ValueError):
            normalized_round = 0

        if 1 <= normalized_round <= 6:
            return f'round-{normalized_round}'

        if getattr(gs, 'setup_build_is_completed', False):
            return 'setup-effect'

        if getattr(gs, 'setup_choice_is_completed', False):
            return 'setup-build'

        return 'setup-choice'

    def _get_action_log_stage_transition_path(self, from_stage_key: Optional[str], to_stage_key: str) -> List[str]:
        """返回阶段切换过程中需要补入历史记录的阶段路径。"""
        if from_stage_key is None or from_stage_key not in ACTION_LOG_STAGE_INDEX:
            return [to_stage_key]

        if to_stage_key not in ACTION_LOG_STAGE_INDEX:
            return []

        from_index = ACTION_LOG_STAGE_INDEX[from_stage_key]
        to_index = ACTION_LOG_STAGE_INDEX[to_stage_key]
        if to_index <= from_index:
            return [to_stage_key]

        return list(ACTION_LOG_STAGE_ORDER[from_index + 1:to_index + 1])

    def _reset_action_history_tracking(self):
        """重置后端结构化行动历史缓存。"""
        self._structured_action_history = []
        self._last_raw_action_count = 0
        self._last_action_log_stage_key = None
        self._pending_action_selection_metadata = {}

    def record_action_selection_metadata(
        self,
        raw_action_index: int,
        selection_source: str = 'manual',
        selection_strategy: Optional[str] = None,
        selection_mode: Optional[str] = None
    ):
        """登记下一条底层行动记录对应的选择来源元数据。"""
        if not isinstance(raw_action_index, int) or raw_action_index <= 0:
            return

        normalized_source = 'system' if selection_source == 'system' else 'manual'
        normalized_strategy = selection_strategy.strip() if isinstance(selection_strategy, str) else ''
        normalized_mode = selection_mode.strip() if isinstance(selection_mode, str) else ''

        self._pending_action_selection_metadata[raw_action_index] = {
            'selection_source': normalized_source,
            'selection_strategy': normalized_strategy,
            'selection_mode': normalized_mode
        }

    def record_action_duration(
        self,
        raw_action_index: int,
        duration_ms: int
    ):
        """登记下一条底层行动记录对应的用时（毫秒）。"""
        if not isinstance(raw_action_index, int) or raw_action_index <= 0:
            return
        if not isinstance(duration_ms, int) or duration_ms < 0:
            return
        self._pending_action_durations[raw_action_index] = duration_ms

    def _append_action_history_divider(self, stage_key: str):
        """在结构化行动历史中追加阶段分割线。"""
        if stage_key not in ACTION_LOG_STAGE_LABELS:
            return

        last_entry = self._structured_action_history[-1] if self._structured_action_history else None
        if (
            last_entry is not None
            and last_entry.kind == 'divider'
            and last_entry.stage_key == stage_key
        ):
            return

        self._structured_action_history.append(ActionHistoryEntry(
            kind='divider',
            stage_key=stage_key,
            player_id=-1,
            action_type='divider',
            action_id=None,
            description=ACTION_LOG_STAGE_LABELS[stage_key]
        ))

    def _build_action_history_action_entry(
        self,
        record: Any,
        detailed_actions: Dict[Any, Any],
        stage_key: str,
        raw_action_index: int
    ) -> Optional[ActionHistoryEntry]:
        """将底层 action_history 记录转换为前端可直接消费的结构化记录。"""
        if not isinstance(record, (list, tuple)) or len(record) < 3:
            return None

        player_id, action_type, action_id = record[:3]
        action_detail = detailed_actions.get(action_id, {}) if isinstance(detailed_actions, dict) else {}
        description = action_detail.get('description', f'action {action_id}')
        action_key = action_detail.get('action', '')
        selection_metadata = self._pending_action_selection_metadata.pop(raw_action_index, None) or {}
        
        # 从 display groups 获取分类信息
        display_group = self._get_action_display_group(action_id)
        category = display_group.get('group_label', action_key) if display_group else action_key
        subcategory = display_group.get('minor_label', '') if display_group else ''
        detail = display_group.get('minor_detail', '') if display_group else ''
        
        # 获取玩家剩余时间
        all_players_remaining = self._timer_state.get('all_players_remaining', [])
        player_remaining = all_players_remaining[player_id] if 0 <= player_id < len(all_players_remaining) else 0
        
        # 获取行动用时
        duration_ms = self._pending_action_durations.pop(raw_action_index, 0)

        return ActionHistoryEntry(
            kind='action',
            stage_key=stage_key,
            player_id=player_id,
            action_type=action_type,
            action_id=action_id,
            description=description,
            selection_source=selection_metadata.get('selection_source', 'manual'),
            selection_strategy=selection_metadata.get('selection_strategy', ''),
            selection_mode=selection_metadata.get('selection_mode', ''),
            action_category=category,
            action_subcategory=subcategory,
            action_detail=detail,
            duration_ms=duration_ms,
            player_remaining_ms=player_remaining
        )
    
    def _extract_setup(self, gs: 'GameStateBase') -> GameSetup:
        """提取游戏设置"""
        setup = gs.setup
        return GameSetup(
            selected_planning_cards=list(setup.selected_planning_cards),
            selected_factions=list(setup.selected_factions),
            selected_palace_tiles=list(setup.selected_palace_tiles),
            selected_round_boosters=list(setup.selected_round_boosters),
            round_booster_coin_counts=self._extract_round_booster_coin_counts(gs, setup.selected_round_boosters),
            round_scoring_order=list(setup.round_scoring_order),
            final_scoring=setup.final_scoring,
            ability_tiles_order=list(setup.ability_tiles_order),
            science_tiles_order=list(setup.science_tiles_order),
            selected_book_actions=list(setup.selected_book_actions),
            init_player_order=list(setup.init_player_order),
            current_global_books=dict(setup.current_global_books)
        )

    def _extract_round_booster_coin_counts(
        self,
        gs: 'GameStateBase',
        booster_ids: List[int]
    ) -> Dict[int, int]:
        """提取每张回合助推板正面累计的 ('money', 'get', 1) 次数。"""
        all_available_object_dict = getattr(gs, 'all_available_object_dict', {}) or {}
        round_boosters = all_available_object_dict.get('round_booster', {}) if isinstance(all_available_object_dict, dict) else {}

        return {
            booster_id: self._count_round_booster_single_coin_effect(round_boosters.get(booster_id))
            for booster_id in booster_ids
        }

    def _count_round_booster_single_coin_effect(self, booster: Any) -> int:
        """只统计 immediate_effect 中精确匹配 ('money', 'get', 1) 的元组个数。"""
        immediate_effects = getattr(booster, 'immediate_effect', []) if booster is not None else []
        return sum(1 for effect in immediate_effects if effect == ('money', 'get', 1))
    
    def _extract_players(self, players: List['PlayerState']) -> List[PlayerState]:
        """提取玩家状态列表"""
        return [self._extract_single_player(p) for p in players]
    
    def _extract_single_player(self, p: 'PlayerState') -> PlayerState:
        """提取单个玩家状态"""
        return PlayerState(
            player_id=p.player_id,
            planning_card_id=p.planning_card_id,
            faction_id=p.faction_id,
            palace_tile_id=p.palace_tile_id,
            is_got_palace=p.is_got_palace,
            resources=Resources(
                money=p.resources['money'],
                ore=p.resources['ore'],
                bank_book=p.resources['bank_book'],
                law_book=p.resources['law_book'],
                engineering_book=p.resources['engineering_book'],
                medical_book=p.resources['medical_book'],
                meeples=p.resources['meeples'],
                all_meeples=p.resources['all_meeples'],
                all_bridges=p.resources['all_bridges']
            ),
            magics=Magics(
                zone1=p.magics[1],
                zone2=p.magics[2],
                zone3=p.magics[3]
            ),
            buildings=Buildings(
                workshop=p.buildings[1],
                guild=p.buildings[2],
                palace=p.buildings[3],
                school=p.buildings[4],
                university=p.buildings[5],
                tower=p.buildings[6],
                monument=p.buildings[7],
                annex=p.buildings[8],
                neutral_workshop=p.buildings[9],
                neutral_guild=p.buildings[10],
                neutral_palace=p.buildings[11],
                neutral_school=p.buildings[12],
                neutral_university=p.buildings[13]
            ),
            tracks=Tracks(
                bank=p.tracks['bank'],
                law=p.tracks['law'],
                engineering=p.tracks['engineering'],
                medical=p.tracks['medical']
            ),
            tracks_over_7_amount=p.tracks_over_7_amount,
            navigation_level=p.navigation_level,
            shovel_level=p.shovel_level,
            temp_navigation=p.temp_navigation,
            controlled_map_ids=list(p.controlled_map_ids),
            adjacent_map_ids=list(p.adjacent_map_ids),
            reachable_map_ids=list(p.reachable_map_ids),
            citys_amount=p.citys_amount,
            settlements_and_cities={
                f"{k[0]},{k[1]}": [f"{v[0][0]},{v[0][1]}", v[1]]
                for k, v in p.settlements_and_cities.items()
            },
            city_tile_assignments=self._city_tile_assignments.get(p.player_id, {}),
            booster_ids=list(p.booster_ids),
            ability_tile_ids=list(p.ability_tile_ids),
            science_tile_ids=list(p.science_tile_ids),
            boardscore=p.boardscore,
            trackscore=p.trackscore,
            chainscore=p.chainscore,
            resourcescore=p.resourcescore,
            main_action_is_done=p.main_action_is_done,
            ispass=p.ispass
        )
    
    def _extract_map_state(self, map_board: 'MapBoardState') -> MapState:
        """
        提取地图状态
        
        后端 map_grid 格式: [terrain, controller, building_id, annex_count, is_neutral]
        前端 MapCell 格式: {terrain, controller, building_id, is_neutral, has_annex}
        """
        grid = []
        for row_idx, row in enumerate(map_board.map_grid):
            grid_row = []
            for col_idx, cell in enumerate(row):
                # cell[0]=地形, cell[1]=控制者, cell[2]=建筑ID, cell[3]=侧楼数量, cell[4]=是否中立
                grid_row.append(MapCell(
                    terrain=cell[0],
                    controller=cell[1],
                    building_id=cell[2],
                    is_neutral=cell[4],
                    has_annex=cell[3] > 0  # annex_count > 0 表示有侧楼
                ))
            grid.append(grid_row)
        
        return MapState(
            width=map_board.width,
            height=map_board.height,
            grid=grid,
            bridges={str(k): v for k, v in map_board.bridges_is_conneted.items()}
        )
    
    def _extract_display_board(self, display: 'DisplayBoardState', gs: 'GameStateBase') -> DisplayBoardState:
        """提取展示板状态"""
        science_tracks = {}
        for track_name in ['bank', 'law', 'engineering', 'medical']:
            if hasattr(display, 'science_tracks') and track_name in display.science_tracks:
                track_data = display.science_tracks[track_name]
                science_tracks[track_name] = ScienceTrackState(
                    is_crowned=track_data.get('is_crowned', False),
                    meeples=list(track_data.get('meeples', [-1]*4))
                )
            else:
                science_tracks[track_name] = ScienceTrackState()

        return DisplayBoardState(
            science_tracks=science_tracks,
            ability_tile_owners=self._extract_tile_owner_map(gs, 'ability_tile', gs.setup.ability_tiles_order),
            science_tile_owners=self._extract_tile_owner_map(gs, 'science_tile', gs.setup.science_tiles_order),
            city_tile_owners=self._extract_tile_owner_map(gs, 'city_tile', list(range(1, 8)))
        )

    def _extract_tile_owner_map(
        self,
        gs: 'GameStateBase',
        tile_type: str,
        ordered_tile_ids: List[int]
    ) -> Dict[int, List[int]]:
        """提取能力/高科板块的 owner_list，供前端按顺序展示持有者标记。"""
        all_available_object_dict = getattr(gs, 'all_available_object_dict', {}) or {}
        tile_objects = all_available_object_dict.get(tile_type, {}) if isinstance(all_available_object_dict, dict) else {}

        owner_map: Dict[int, List[int]] = {}
        for tile_id in ordered_tile_ids:
            tile = tile_objects.get(tile_id) if isinstance(tile_objects, dict) else None
            owner_list = getattr(tile, 'owner_list', []) if tile is not None else []
            owner_map[tile_id] = [
                int(player_id)
                for player_id in owner_list
                if isinstance(player_id, int)
            ]

        return owner_map
    
    def _extract_available_actions(self, actions: Dict[int, str]) -> List[AvailableAction]:
        """提取可选行动"""
        return [AvailableAction(action_id=k, description=v) for k, v in actions.items()]

    def _extract_action_history(self, gs: 'GameStateBase') -> List[ActionHistoryEntry]:
        """提取结构化行动记录，并在后端直接维护阶段分割线。"""
        raw_history = list(getattr(gs, 'action_history', []) or [])
        detailed_actions = getattr(gs, 'all_detailed_actions', {}) or {}
        current_stage_key = self._get_action_log_stage_key(gs)
        raw_action_count = len(raw_history)

        if raw_action_count < self._last_raw_action_count:
            self._reset_action_history_tracking()

        if not self._structured_action_history:
            self._append_action_history_divider(current_stage_key)

        previous_stage_key = self._last_action_log_stage_key or current_stage_key
        new_records = raw_history[self._last_raw_action_count:]
        for offset, record in enumerate(new_records, start=1):
            action_entry = self._build_action_history_action_entry(
                record,
                detailed_actions,
                previous_stage_key,
                self._last_raw_action_count + offset
            )
            if action_entry is not None:
                self._structured_action_history.append(action_entry)

        transition_path = []
        if current_stage_key != previous_stage_key:
            transition_path = self._get_action_log_stage_transition_path(previous_stage_key, current_stage_key)

        for stage_key in transition_path:
            self._append_action_history_divider(stage_key)

        self._last_raw_action_count = raw_action_count
        self._last_action_log_stage_key = current_stage_key
        return copy.deepcopy(self._structured_action_history)
    
    def _extract_final_scores(self, scores: Dict[int, Dict[str, int]]) -> Dict[int, FinalScore]:
        """提取最终得分"""
        return {
            k: FinalScore(
                total=v.get('total', 0),
                board=v.get('board', 0),
                chain=v.get('chain', 0),
                track=v.get('track', 0),
                resource=v.get('resource', 0)
            )
            for k, v in scores.items()
        }
    
    # ==================== 增量计算核心算法 ====================
    
    def _calculate_optimized_diff(self, old_state: Optional[Dict], 
                                   new_state: FullGameState) -> List[StateDiff]:
        """
        计算优化后的增量
        
        对地图使用专门的单元格级diff算法，其他使用通用diff
        """
        diffs = []
        
        if old_state is None:
            # 首次初始化，返回整个状态
            return [StateDiff('', None, asdict(new_state), ChangeType.ADDED)]
        
        new_dict = asdict(new_state)
        
        # 1. 对比 meta
        old_meta = old_state.get('meta', {})
        new_meta = new_dict.get('meta', {})
        
        # 对 current_player_order 和 pass_order 使用整体替换（而非逐元素 diff）
        # 因为列表顺序和长度变化需要一次性更新，避免前端逐元素应用导致状态不一致
        for list_key in ('current_player_order', 'pass_order'):
            old_list = old_meta.get(list_key)
            new_list = new_meta.get(list_key)
            if old_list != new_list:
                diffs.append(StateDiff(
                    f'meta.{list_key}',
                    old_list,
                    new_list,
                    ChangeType.MODIFIED
                ))
        
        # 过滤掉已特殊处理的列表字段，对比 meta 的其他字段
        filtered_old_meta = {k: v for k, v in old_meta.items() if k not in ('current_player_order', 'pass_order')}
        filtered_new_meta = {k: v for k, v in new_meta.items() if k not in ('current_player_order', 'pass_order')}
        
        diffs.extend(self._calculate_object_diff(
            'meta', 
            filtered_old_meta, 
            filtered_new_meta
        ))
        
        # 2. 对比 setup（通常只在初始化时变化）
        diffs.extend(self._calculate_object_diff(
            'setup',
            old_state.get('setup', {}),
            new_dict.get('setup', {})
        ))
        
        # 3. 对比 players
        diffs.extend(self._calculate_players_diff(
            old_state.get('players', []),
            new_dict.get('players', [])
        ))
        
        # 4. 对比地图（使用优化的单元格级diff）
        diffs.extend(self._calculate_map_diff(
            old_state.get('map_state', {}),
            new_dict.get('map_state', {})
        ))
        
        # 5. 对比 display_board
        diffs.extend(self._calculate_display_board_diff(
            old_state.get('display_board', {}),
            new_dict.get('display_board', {})
        ))
        
        # 6. available_actions：每次完整推送，不计算增量
        # 直接替换整个列表
        old_actions = old_state.get('available_actions', [])
        new_actions = new_dict.get('available_actions', [])
        if old_actions != new_actions:
            diffs.append(StateDiff(
                'available_actions',
                old_actions,
                new_actions,
                ChangeType.MODIFIED
            ))

        old_action_history = old_state.get('action_history', [])
        new_action_history = new_dict.get('action_history', [])
        if old_action_history != new_action_history:
            diffs.append(StateDiff(
                'action_history',
                old_action_history,
                new_action_history,
                ChangeType.MODIFIED
            ))

        # 7. 对比 final_scores
        diffs.extend(self._calculate_object_diff(
            'final_scores',
            old_state.get('final_scores'),
            new_dict.get('final_scores')
        ))

        # 8. 对比 timer_state
        diffs.extend(self._calculate_object_diff(
            'timer_state',
            old_state.get('timer_state'),
            new_dict.get('timer_state')
        ))
        
        return diffs

    def _calculate_display_board_diff(self, old_display: Dict, new_display: Dict) -> List[StateDiff]:
        """展示板差异计算，对 owner_list 派生字段按整表替换，便于前端应用。"""
        if not isinstance(old_display, dict) or not isinstance(new_display, dict):
            return self._calculate_object_diff('display_board', old_display, new_display)

        diffs = self._calculate_object_diff(
            'display_board.science_tracks',
            old_display.get('science_tracks', {}),
            new_display.get('science_tracks', {})
        )

        for key in ('ability_tile_owners', 'science_tile_owners'):
            old_value = old_display.get(key, {})
            new_value = new_display.get(key, {})
            if old_value == new_value:
                continue

            diffs.append(StateDiff(
                f'display_board.{key}',
                old_value,
                new_value,
                ChangeType.MODIFIED
            ))

        return diffs
    
    def _calculate_object_diff(self, path: str, old: Any, new: Any) -> List[StateDiff]:
        """递归计算对象差异"""
        diffs = []
        
        # 类型不同，整体替换
        if type(old) != type(new):
            if old is None and new is not None:
                diffs.append(StateDiff(path, old, new, ChangeType.ADDED))
            elif old is not None and new is None:
                diffs.append(StateDiff(path, old, new, ChangeType.REMOVED))
            else:
                diffs.append(StateDiff(path, old, new, ChangeType.MODIFIED))
            return diffs
        
        if new is None:
            return diffs
        
        if isinstance(new, dict):
            all_keys = set(old.keys() if old else []) | set(new.keys())
            for key in all_keys:
                new_path = f"{path}.{key}"
                old_val = old.get(key) if old else None
                new_val = new.get(key)
                
                if key not in (old or {}):
                    diffs.append(StateDiff(new_path, None, new_val, ChangeType.ADDED))
                elif key not in new:
                    diffs.append(StateDiff(new_path, old_val, None, ChangeType.REMOVED))
                else:
                    diffs.extend(self._calculate_object_diff(new_path, old_val, new_val))
        
        elif isinstance(new, list):
            max_len = max(len(old) if old else 0, len(new))
            for i in range(max_len):
                new_path = f"{path}[{i}]"
                old_val = old[i] if old and i < len(old) else None
                new_val = new[i] if i < len(new) else None
                
                if old_val is None and new_val is not None:
                    diffs.append(StateDiff(new_path, None, new_val, ChangeType.ADDED))
                elif old_val is not None and new_val is None:
                    diffs.append(StateDiff(new_path, old_val, None, ChangeType.REMOVED))
                elif old_val != new_val:
                    diffs.extend(self._calculate_object_diff(new_path, old_val, new_val))
        
        elif old != new:
            diffs.append(StateDiff(path, old, new, ChangeType.MODIFIED))
        
        return diffs
    
    def _calculate_players_diff(self, old_players: List[Dict], 
                                 new_players: List[Dict]) -> List[StateDiff]:
        """
        计算玩家列表差异
            
        对于 set 类型字段（controlled_map_ids, reachable_map_ids）使用专门的增量计算
        """
        diffs = []
    
        for i, (old_p, new_p) in enumerate(zip(old_players, new_players)):
            player_path = f'players[{i}]'
                
            # 需要作为 set 增量更新的字段
            set_fields = {'controlled_map_ids', 'reachable_map_ids'}
                
            for key in set(old_p.keys()) | set(new_p.keys()):
                old_val = old_p.get(key)
                new_val = new_p.get(key)
                    
                if key in set_fields:
                    # 对 set 类型字段使用增量计算
                    set_diffs = self._calculate_set_diff(
                        f'{player_path}.{key}',
                        old_val if old_val else [],
                        new_val if new_val else []
                    )
                    diffs.extend(set_diffs)
                else:
                    # 其他字段使用普通增量计算
                    diffs.extend(self._calculate_object_diff(
                        f'{player_path}.{key}', old_val, new_val
                    ))
    
        return diffs
        
    def _calculate_set_diff(self, path: str, old_list: List, new_list: List) -> List[StateDiff]:
        """
        计算 set 类型字段的增量差异
            
        将列表视为集合，计算新增和删除的元素
        返回格式：
        - path.added: 新增的元素列表
        - path.removed: 删除的元素列表
            
        Args:
            path: 字段路径
            old_list: 旧值列表
            new_list: 新值列表
                
        Returns:
            StateDiff 列表，包含 added 和/或 removed 的差异
        """
        diffs = []
            
        # 转换为 tuple 以便存入 set（因为 list 不可哈希）
        def to_hashable(item):
            if isinstance(item, list):
                return tuple(item)
            return item
            
        def to_serializable(item):
            """转换为可序列化的格式"""
            if isinstance(item, tuple):
                return list(item)
            return item
            
            
        old_set = set(to_hashable(x) for x in old_list) if old_list else set()
        new_set = set(to_hashable(x) for x in new_list) if new_list else set()
            
        added = new_set - old_set
        removed = old_set - new_set
            
        # 如果有新增元素
        if added:
            diffs.append(StateDiff(
                f'{path}.added',
                None,
                [to_serializable(x) for x in added],
                ChangeType.ADDED
            ))
            
        # 如果有删除元素
        if removed:
            diffs.append(StateDiff(
                f'{path}.removed',
                [to_serializable(x) for x in removed],
                None,
                ChangeType.REMOVED
            ))
            
        return diffs
    
    def _calculate_map_diff(self, old_map: Dict, new_map: Dict) -> List[StateDiff]:
        """
        专门优化地图增量计算 - 只返回变更的单元格
        
        前端展示字段: terrain, controller, building_id, is_neutral, has_annex
        """
        diffs = []
        
        if not old_map or not old_map.get('grid'):
            # 首次初始化，返回整个地图
            return [StateDiff('map_state', None, new_map, ChangeType.ADDED)]
        
        old_grid = old_map.get('grid', [])
        new_grid = new_map.get('grid', [])
        
        # 遍历每个单元格
        height = new_map.get('height', 9)
        width = new_map.get('width', 13)
        
        for row_idx in range(height):
            for col_idx in range(width):
                old_cell = old_grid[row_idx][col_idx] if row_idx < len(old_grid) and col_idx < len(old_grid[row_idx]) else {}
                new_cell = new_grid[row_idx][col_idx]
                
                # 对比单元格的每个展示字段
                cell_path = f'map_state.grid[{row_idx}][{col_idx}]'
                display_fields = ['terrain', 'controller', 'building_id', 'is_neutral', 'has_annex']
                
                for field in display_fields:
                    old_val = old_cell.get(field)
                    new_val = new_cell.get(field)
                    
                    if old_val != new_val:
                        diffs.append(StateDiff(
                            f'{cell_path}.{field}',
                            old_val,
                            new_val,
                            ChangeType.MODIFIED
                        ))
        
        # 对比桥梁
        old_bridges = old_map.get('bridges', {})
        new_bridges = new_map.get('bridges', {})
        
        all_bridge_keys = set(old_bridges.keys()) | set(new_bridges.keys())
        for key in all_bridge_keys:
            old_val = old_bridges.get(key)
            new_val = new_bridges.get(key)
            
            if old_val != new_val:
                diffs.append(StateDiff(
                    f'map_state.bridges["{key}"]',
                    old_val,
                    new_val,
                    ChangeType.MODIFIED if old_val is not None and new_val is not None 
                    else (ChangeType.ADDED if new_val is not None else ChangeType.REMOVED)
                ))
        
        return diffs

    def _update_city_tile_matches(self, old_state: Dict, new_state: Dict, current_ah_length: int):
        """
        跨快照匹配 settlements_and_cities 新增城市与 city_tile 新增 owner。
        使用 action_history 长度作为"时间戳"，只有同一玩家内前后连续两动（ah_length 差值为1）才能匹配。
        
        三条记录：
        1. _city_establishment_log: {player_id: [(pos_key, action_history_length), ...]}
        2. _city_tile_acquisition_log: {player_id: [(tile_id, action_history_length), ...]}
        3. _city_tile_assignments: {player_id: {pos_key: city_tile_id}}
        """
        new_players = new_state.get('players', [])
        old_players = old_state.get('players', [])

        # Step 1: 检测 settlements_and_cities 新增的城市根节点
        for player_idx, player_data in enumerate(new_players):
            player_id = player_data.get('player_id', player_idx)
            old_sac = old_players[player_idx].get('settlements_and_cities', {}) if player_idx < len(old_players) else {}
            new_sac = player_data.get('settlements_and_cities', {})

            for pos_key, value in new_sac.items():
                is_new_establishment = False
                if pos_key not in old_sac:
                    # 新增条目，检查是否是根节点且 is_city=True
                    root_key, is_city = value[0], value[1]
                    if root_key == pos_key and is_city:
                        is_new_establishment = True
                elif old_sac.get(pos_key) != value:
                    # 已有条目变更，检查是否变为城市
                    old_root, old_is_city = old_sac[pos_key][0], old_sac[pos_key][1]
                    new_root, new_is_city = value[0], value[1]
                    if not old_is_city and new_is_city and new_root == pos_key:
                        is_new_establishment = True
                
                if is_new_establishment:
                    self._city_establishment_log.setdefault(player_id, []).append(
                        (pos_key, current_ah_length)
                    )

        # Step 2: 检测 city_tile_owners 新增的 owner
        old_owners = old_state.get('display_board', {}).get('city_tile_owners', {})
        new_owners = new_state.get('display_board', {}).get('city_tile_owners', {})

        for tile_id_str, new_owner_list in new_owners.items():
            tile_id = int(tile_id_str)
            old_owner_list = old_owners.get(tile_id_str, [])
            added_players = [p for p in new_owner_list if p not in old_owner_list]

            for player_id in added_players:
                self._city_tile_acquisition_log.setdefault(player_id, []).append(
                    (tile_id, current_ah_length)
                )

        # Step 3: 匹配检查
        # 遍历所有玩家的城市根节点记录，查找 ah_length+1 的城市板块获取记录
        all_player_ids = set(self._city_establishment_log.keys()) | set(self._city_tile_acquisition_log.keys())
        for player_id in all_player_ids:
            establishment_log = self._city_establishment_log.get(player_id, [])
            acquisition_log = self._city_tile_acquisition_log.get(player_id, [])
            
            for est_pos_key, est_ah_length in establishment_log:
                # 查找同一玩家中 ah_length 恰好为 est_ah_length + 1 的板块获取记录
                for acq_tile_id, acq_ah_length in acquisition_log:
                    if acq_ah_length == est_ah_length + 1:
                        # 匹配成功，加入 assignments
                        self._city_tile_assignments.setdefault(player_id, {})[est_pos_key] = acq_tile_id
                        break

        # Step 4: 处理根节点路径压缩导致的匹配迁移
        # 遍历所有已匹配的记录，检查根节点是否发生变化
        for player_id, assignments in list(self._city_tile_assignments.items()):
            player_data = None
            for p in new_players:
                if p.get('player_id') == player_id:
                    player_data = p
                    break

            sac = player_data.get('settlements_and_cities', {}) if player_data else {}
            new_assignments = {}
            for pos_key, tile_id in assignments.items():
                if pos_key in sac:
                    root_key = sac[pos_key][0]
                    if sac.get(root_key, [None, False])[1]:
                        # 根节点仍是城市，更新到当前根节点
                        new_assignments[root_key] = tile_id
                    else:
                        # 根节点不再是城市（异常情况），保留原记录
                        new_assignments[pos_key] = tile_id
                else:
                    # 该坐标不在 settlements_and_cities 中，保留原记录
                    new_assignments[pos_key] = tile_id
            self._city_tile_assignments[player_id] = new_assignments
    
    # ==================== 状态访问接口 ====================
    
    def get_full_state(self) -> Optional[Dict]:
        """
        获取全量状态
        
        Returns:
            完整状态字典，包含版本号信息
        """
        if not self._current_state:
            return None

        state = asdict(self._current_state)
        state['timer_state'] = asdict(self._extract_timer_state())

        return {
            'version': self._version,
            'timestamp': self._last_update_time,
            'state': state
        }
    
    def get_incremental_update(self) -> Optional[Dict]:
        """
        获取增量更新数据
        
        Returns:
            增量更新数据，包含变更列表
        """
        if not self._current_state or not self._last_pushed_state:
            return None
        
        diffs = self._calculate_optimized_diff(
            self._last_pushed_state, 
            self._current_state
        )
        
        if not diffs:
            return None
        
        return {
            'version': self._version,
            'timestamp': self._last_update_time,
            'changes': [
                {
                    'path': d.path,
                    'new_value': d.new_value,
                    'change_type': d.change_type.value
                }
                for d in diffs
            ]
        }
    
    def get_current_state(self) -> Optional[FullGameState]:
        """获取当前完整状态对象"""
        return copy.deepcopy(self._current_state)
    
    def get_version(self) -> int:
        """获取当前版本号"""
        return self._version
    
    def get_last_update_time(self) -> Optional[str]:
        """获取最后更新时间"""
        return self._last_update_time
    
    @property
    def is_initialized(self) -> bool:
        """是否已初始化（是否已接收过状态）"""
        return self._current_state is not None
