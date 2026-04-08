# GameState 前端展示数据映射与SSE推送设计文档

## 1. 概述

本文档设计了一个后端 Python 类 `GameStateSyncManager`，用于：
1. 接收游戏引擎 yield 返回的 `ActionRequest` 并提取数据
2. 维护当前游戏状态的完整快照
3. 计算增量变化（与上一次状态对比）
4. 通过 SSE (Server-Sent Events) 推送增量更新给前端
5. 支持页面刷新时的全量更新

### 1.1 架构图

```
┌─────────────────┐     yield      ┌─────────────────────────┐
│   GameEngine    │ ─────────────> │  GameStateSyncManager   │
│   (游戏引擎)     │  ActionRequest │    (后端状态管理类)      │
└─────────────────┘                └─────────────────────────┘
                                              │
                    ┌─────────────────────────┼─────────────────────────┐
                    │                         │                         │
                    ▼                         ▼                         ▼
           ┌─────────────┐          ┌─────────────────┐        ┌─────────────┐
           │  计算增量    │          │   保存全量状态    │        │  SSE推送    │
           │  (diff)     │          │   (snapshot)    │        │  给前端      │
           └─────────────┘          └─────────────────┘        └─────────────┘
                    │                                                  │
                    └──────────────────────┬───────────────────────────┘
                                           ▼
                              ┌─────────────────────────┐
                              │      前端 (Vue)          │
                              │  - 增量更新: 合并diff    │
                              │  - 全量更新: 替换状态    │
                              └─────────────────────────┘
```

---

## 2. 数据模型定义

### 2.1 前端展示所需数据结构

```python
from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple, Optional, Any
from enum import Enum

class ChangeType(Enum):
    """变更类型"""
    ADDED = "added"           # 新增
    MODIFIED = "modified"     # 修改
    REMOVED = "removed"       # 删除

@dataclass
class GameMeta:
    """游戏元信息"""
    round: int = 0
    num_players: int = 3
    current_player_id: int = -1
    action_type: str = ""
    is_game_over: bool = False
    setup_choice_is_completed: bool = False
    setup_build_is_completed: bool = False

@dataclass
class Resources:
    """资源"""
    money: int = 0
    ore: int = 0
    bank_book: int = 0
    law_book: int = 0
    engineering_book: int = 0
    medical_book: int = 0
    meeples: int = 0
    all_meeples: int = 7
    all_bridges: int = 3

@dataclass
class Magics:
    """魔力"""
    zone1: int = 5
    zone2: int = 7
    zone3: int = 0

@dataclass
class Buildings:
    """建筑"""
    workshop: int = 9
    guild: int = 4
    palace: int = 1
    school: int = 3
    university: int = 1
    tower: int = 0
    monument: int = 0
    annex: int = 0

@dataclass
class Tracks:
    """科技轨"""
    bank: int = 0
    law: int = 0
    engineering: int = 0
    medical: int = 0

@dataclass
class PlayerState:
    """玩家状态"""
    player_id: int = 0
    planning_card_id: int = 0
    faction_id: int = 0
    palace_tile_id: int = 0
    is_got_palace: bool = False
    resources: Resources = field(default_factory=Resources)
    magics: Magics = field(default_factory=Magics)
    buildings: Buildings = field(default_factory=Buildings)
    tracks: Tracks = field(default_factory=Tracks)
    tracks_over_7_amount: int = 0
    navigation_level: int = 0
    shovel_level: int = 3
    temp_navigation: bool = False
    controlled_map_ids: List[Tuple[int, int]] = field(default_factory=list)
    adjacent_map_ids: List[Tuple[int, int]] = field(default_factory=list)
    reachable_map_ids: List[Tuple[int, int]] = field(default_factory=list)
    citys_amount: int = 0
    booster_ids: List[int] = field(default_factory=list)
    ability_tile_ids: List[int] = field(default_factory=list)
    science_tile_ids: List[int] = field(default_factory=list)
    boardscore: int = 20
    trackscore: int = 0
    chainscore: int = 0
    resourcescore: int = 0
    main_action_is_done: bool = False
    ispass: bool = False

@dataclass
class MapCell:
    """
    地图单元格 - 前端展示用简化模型
    
    从后端 map_grid[5] 提取：
    - [0]: terrain - 地形类型（决定地块颜色）
    - [1]: controller - 控制玩家ID（决定边框颜色，-1表示无）
    - [2]: building_id - 建筑类型（决定建筑图片，0表示无建筑）
    - [3]: annex_count - 侧楼数量（0或1，侧楼可与其他建筑共存）
    - [4]: is_neutral - 是否中立建筑（影响样式）
    
    前端展示所需最小信息：
    1. terrain: 地形颜色
    2. building: 主建筑（含类型、是否中立）
    3. has_annex: 是否有侧楼（侧楼可叠加）
    """
    # 地形类型 (0-7): 决定地块背景色
    # 0=水域, 1=平原(棕), 2=沼泽(黑), 3=湖泊(蓝), 4=森林(绿), 5=山脉(灰), 6=荒地(红), 7=沙漠(黄)
    terrain: int = 0
    
    # 控制者玩家ID (-1=无, 0=玩家1, 1=玩家2, 2=玩家3)
    controller: int = -1
    
    # 主建筑类型 (0=无, 1=车间, 2=工会, 3=宫殿, 4=学校, 5=大学, 6=塔楼, 7=山脉, 8=侧楼)
    # 注意：侧楼作为特殊建筑，通常以 annex 形式存在，但也可以作为主建筑
    building_id: int = 0
    
    # 是否中立建筑（影响建筑样式）
    is_neutral: bool = False
    
    # 是否有侧楼（侧楼可与其他建筑共存）
    has_annex: bool = False
    
    @property
    def is_empty(self) -> bool:
        """是否空地块（无建筑）"""
        return self.building_id == 0
    
    @property
    def is_controlled(self) -> bool:
        """是否被玩家控制"""
        return self.controller != -1
    
    @property
    def building_with_annex(self) -> Dict:
        """获取完整的建筑信息（用于前端渲染）"""
        return {
            'main_building': self.building_id,  # 主建筑图片ID
            'is_neutral': self.is_neutral,
            'has_annex': self.has_annex,  # 是否同时显示侧楼
            'controller': self.controller  # 用于建筑颜色/边框
        }

@dataclass
class MapState:
    """地图状态"""
    width: int = 13
    height: int = 9
    grid: List[List[MapCell]] = field(default_factory=list)
    bridges: Dict[str, int] = field(default_factory=dict)  # 桥梁连接状态

@dataclass
class ScienceTrackState:
    """科技轨展示状态"""
    is_crowned: bool = False
    meeples: List[bool] = field(default_factory=lambda: [False]*4)

@dataclass
class DisplayBoardState:
    """展示板状态"""
    science_tracks: Dict[str, ScienceTrackState] = field(default_factory=dict)

@dataclass
class GameSetup:
    """游戏设置"""
    selected_planning_cards: List[int] = field(default_factory=list)
    selected_factions: List[int] = field(default_factory=list)
    selected_palace_tiles: List[int] = field(default_factory=list)
    selected_round_boosters: List[int] = field(default_factory=list)
    round_scoring_order: List[int] = field(default_factory=list)
    final_scoring: int = 0
    ability_tiles_order: List[int] = field(default_factory=list)
    science_tiles_order: List[int] = field(default_factory=list)
    selected_book_actions: List[int] = field(default_factory=list)
    init_player_order: List[int] = field(default_factory=list)
    current_global_books: Dict[str, int] = field(default_factory=lambda: {
        'bank_book': 12, 'law_book': 12, 'engineering_book': 12, 'medical_book': 12
    })

@dataclass
class AvailableAction:
    """可选行动"""
    action_id: int = 0
    description: str = ""

@dataclass
class FinalScore:
    """最终得分"""
    total: int = 0
    board: int = 0
    chain: int = 0
    track: int = 0
    resource: int = 0

@dataclass
class FullGameState:
    """完整游戏状态（用于全量更新）"""
    meta: GameMeta = field(default_factory=GameMeta)
    setup: GameSetup = field(default_factory=GameSetup)
    players: List[PlayerState] = field(default_factory=list)
    map_state: MapState = field(default_factory=MapState)
    display_board: DisplayBoardState = field(default_factory=DisplayBoardState)
    available_actions: List[AvailableAction] = field(default_factory=list)
    final_scores: Optional[Dict[int, FinalScore]] = None

@dataclass
class StateDiff:
    """状态差异（用于增量更新）"""
    path: str           # 变更路径，如 "players.0.resources.money"
    old_value: Any      # 旧值
    new_value: Any      # 新值
    change_type: ChangeType
```

---

## 3. 核心类设计：GameStateSyncManager

```python
# 建议文件位置: backend/game_state_sync_manager.py

import json
import copy
from typing import Dict, List, Optional, Any, Callable
from dataclasses import asdict, is_dataclass
from datetime import datetime

class GameStateSyncManager:
    """
    游戏状态同步管理器
    
    职责：
    1. 随游戏创建而创建，随游戏结束而销毁
    2. 接收 ActionRequest，提取并维护游戏状态
    3. 计算状态增量（diff）
    4. 通过 SSE 推送增量或全量更新
    5. 支持页面刷新时的全量同步
    """
    
    def __init__(self, game_id: str, sse_manager: 'SSEManager'):
        """
        初始化状态管理器
        
        Args:
            game_id: 游戏唯一标识
            sse_manager: SSE管理器，用于推送消息
        """
        self.game_id = game_id
        self.sse_manager = sse_manager
        
        # 当前完整状态快照
        self._current_state: Optional[FullGameState] = None
        
        # 上一次推送的状态（用于计算diff）
        self._last_pushed_state: Optional[FullGameState] = None
        
        # 状态版本号（每次更新递增）
        self._version: int = 0
        
        # 历史状态缓存（用于回放，可选）
        self._state_history: List[Dict] = []
        
        # 客户端连接状态 {client_id: last_ack_version}
        self._client_versions: Dict[str, int] = {}
        
    # ==================== 核心更新方法 ====================
    
    def update_from_action_request(self, request: 'ActionRequest') -> None:
        """
        从 ActionRequest 更新状态并推送
        
        这是主要入口方法，每次游戏引擎 yield 返回时调用
        """
        # 1. 提取新状态
        new_state = self._extract_state_from_request(request)
        
        # 2. 计算增量（使用优化的地图diff）
        diffs = self._calculate_optimized_diff(self._current_state, new_state)
        
        # 3. 更新当前状态
        self._current_state = new_state
        self._version += 1
        
        # 4. 保存历史（可选）
        self._save_to_history()
        
        # 5. 推送更新
        if diffs:
            self._push_incremental_update(diffs)
        
        # 6. 更新上一次推送状态
        self._last_pushed_state = copy.deepcopy(new_state)
    
    def _calculate_optimized_diff(self, old_state: Optional[FullGameState],
                                   new_state: FullGameState) -> List[StateDiff]:
        """
        计算优化后的增量
        
        对地图使用专门的单元格级diff算法，其他使用通用diff
        """
        diffs = []
        
        if not old_state:
            # 首次初始化，返回整个状态
            return [StateDiff('', None, asdict(new_state), ChangeType.ADDED)]
        
        # 1. 对比 meta
        diffs.extend(self._calculate_diff(
            asdict(old_state.meta), 
            asdict(new_state.meta)
        ))
        
        # 2. 对比 setup（通常只在初始化时变化）
        diffs.extend(self._calculate_diff(
            asdict(old_state.setup),
            asdict(new_state.setup)
        ))
        
        # 3. 对比 players
        diffs.extend(self._calculate_diff(
            asdict(old_state.players),
            asdict(new_state.players)
        ))
        
        # 4. 对比地图（使用优化的单元格级diff）
        map_diffs = self._calculate_map_diff(old_state.map_state, new_state.map_state)
        diffs.extend(map_diffs)
        
        # 5. 对比 display_board
        diffs.extend(self._calculate_diff(
            asdict(old_state.display_board),
            asdict(new_state.display_board)
        ))
        
        # 6. 对比 available_actions
        diffs.extend(self._calculate_diff(
            asdict(old_state.available_actions),
            asdict(new_state.available_actions)
        ))
        
        # 7. 对比 final_scores
        diffs.extend(self._calculate_diff(
            asdict(old_state.final_scores),
            asdict(new_state.final_scores)
        ))
        
        return diffs
    
    def _extract_state_from_request(self, request: 'ActionRequest') -> FullGameState:
        """从 ActionRequest 提取完整状态"""
        gs = request.game_state
        
        return FullGameState(
            meta=self._extract_meta(request, gs),
            setup=self._extract_setup(gs.setup) if gs else GameSetup(),
            players=self._extract_players(gs.players) if gs else [],
            map_state=self._extract_map_state(gs.map_board_state) if gs else MapState(),
            display_board=self._extract_display_board(gs.display_board_state) if gs else DisplayBoardState(),
            available_actions=self._extract_available_actions(request.available_actions),
            final_scores=self._extract_final_scores(request.final_scores) if request.is_game_over else None
        )
    
    # ==================== 状态提取子方法 ====================
    
    def _extract_meta(self, request: 'ActionRequest', gs: Optional['GameStateBase']) -> GameMeta:
        """提取元信息"""
        setup_choice_is_completed = bool(gs and getattr(gs, 'setup_choice_is_completed', False))
        return GameMeta(
            round=gs.round if gs else 0,
            num_players=gs.num_players if gs else 3,
            current_player_id=request.player_id,
            action_type=request.action_type,
            is_game_over=request.is_game_over,
            setup_choice_is_completed=setup_choice_is_completed,
            setup_build_is_completed=self._is_setup_build_completed(gs, setup_choice_is_completed)
        )
    
    def _extract_setup(self, setup: 'GameSetup') -> GameSetup:
        """提取游戏设置"""
        return GameSetup(
            selected_planning_cards=list(setup.selected_planning_cards),
            selected_factions=list(setup.selected_factions),
            selected_palace_tiles=list(setup.selected_palace_tiles),
            selected_round_boosters=list(setup.selected_round_boosters),
            round_scoring_order=list(setup.round_scoring_order),
            final_scoring=setup.final_scoring,
            ability_tiles_order=list(setup.ability_tiles_order),
            science_tiles_order=list(setup.science_tiles_order),
            selected_book_actions=list(setup.selected_book_actions),
            init_player_order=list(setup.init_player_order),
            current_global_books=dict(setup.current_global_books)
        )
    
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
                annex=p.buildings[8]
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
    
    def _calculate_map_diff(self, old_map: Optional[MapState], 
                           new_map: MapState) -> List[StateDiff]:
        """
        专门优化地图增量计算 - 只返回变更的单元格
        
        对比字段: terrain, controller, building_id, is_neutral, has_annex
        """
        diffs = []
        
        if not old_map or not old_map.grid:
            # 首次初始化，返回整个地图
            diffs.append(StateDiff('map_state', None, asdict(new_map), ChangeType.ADDED))
            return diffs
        
        # 对比每个单元格
        for row_idx in range(new_map.height):
            for col_idx in range(new_map.width):
                old_cell = old_map.grid[row_idx][col_idx] if row_idx < len(old_map.grid) else None
                new_cell = new_map.grid[row_idx][col_idx]
                
                cell_diffs = self._compare_map_cell(
                    f'map_state.grid[{row_idx}][{col_idx}]',
                    old_cell, new_cell
                )
                diffs.extend(cell_diffs)
        
        # 对比桥梁状态
        old_bridges = old_map.bridges if old_map else {}
        new_bridges = new_map.bridges
        
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
    
    def _compare_map_cell(self, path: str, old_cell: Optional[MapCell], 
                         new_cell: MapCell) -> List[StateDiff]:
        """
        对比单个地图单元格
        
        前端展示所需字段:
        - terrain: 地形颜色
        - controller: 控制者（边框颜色）
        - building_id: 主建筑图片
        - is_neutral: 是否中立建筑
        - has_annex: 是否有侧楼（可叠加显示）
        """
        diffs = []
        
        if not old_cell:
            # 新增单元格（理论上不会发生，因为地图固定）
            return [StateDiff(path, None, asdict(new_cell), ChangeType.ADDED)]
        
        # 对比每个展示字段
        display_fields = ['terrain', 'controller', 'building_id', 'is_neutral', 'has_annex']
        for field in display_fields:
            old_val = getattr(old_cell, field)
            new_val = getattr(new_cell, field)
            
            if old_val != new_val:
                diffs.append(StateDiff(
                    f'{path}.{field}',
                    old_val,
                    new_val,
                    ChangeType.MODIFIED
                ))
        
        return diffs
    
    def _extract_display_board(self, display: 'DisplayBoardState') -> DisplayBoardState:
        """提取展示板状态"""
        return DisplayBoardState(
            science_tracks={
                'bank': ScienceTrackState(
                    is_crowned=display.science_tracks['bank']['is_crowned'],
                    meeples=list(display.science_tracks['bank']['meeples'])
                ),
                'law': ScienceTrackState(
                    is_crowned=display.science_tracks['law']['is_crowned'],
                    meeples=list(display.science_tracks['law']['meeples'])
                ),
                'engineering': ScienceTrackState(
                    is_crowned=display.science_tracks['engineering']['is_crowned'],
                    meeples=list(display.science_tracks['engineering']['meeples'])
                ),
                'medical': ScienceTrackState(
                    is_crowned=display.science_tracks['medical']['is_crowned'],
                    meeples=list(display.science_tracks['medical']['meeples'])
                )
            }
        )
    
    def _extract_available_actions(self, actions: Dict[int, str]) -> List[AvailableAction]:
        """提取可选行动"""
        return [AvailableAction(action_id=k, description=v) for k, v in actions.items()]
    
    def _extract_final_scores(self, scores: Dict[int, Dict[str, int]]) -> Dict[int, FinalScore]:
        """提取最终得分"""
        return {
            k: FinalScore(
                total=v['total'],
                board=v['board'],
                chain=v['chain'],
                track=v['track'],
                resource=v['resource']
            )
            for k, v in scores.items()
        }
    
    # ==================== 增量计算核心算法 ====================
    
    def _calculate_diff(self, old_state: Optional[FullGameState], 
                        new_state: FullGameState) -> List[StateDiff]:
        """
        计算两个状态之间的差异
        
        返回变更列表，每个变更包含路径、旧值、新值和变更类型
        """
        diffs = []
        old_dict = asdict(old_state) if old_state else {}
        new_dict = asdict(new_state)
        
        self._deep_compare('', old_dict, new_dict, diffs)
        return diffs
    
    def _deep_compare(self, path: str, old: Any, new: Any, diffs: List[StateDiff]):
        """深度比较两个值"""
        if type(old) != type(new):
            diffs.append(StateDiff(path, old, new, ChangeType.MODIFIED))
            return
        
        if isinstance(new, dict):
            all_keys = set(old.keys() if old else []) | set(new.keys())
            for key in all_keys:
                new_path = f"{path}.{key}" if path else key
                old_val = old.get(key) if old else None
                new_val = new.get(key)
                
                if key not in (old or {}):
                    diffs.append(StateDiff(new_path, None, new_val, ChangeType.ADDED))
                elif key not in new:
                    diffs.append(StateDiff(new_path, old_val, None, ChangeType.REMOVED))
                else:
                    self._deep_compare(new_path, old_val, new_val, diffs)
        
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
                    self._deep_compare(new_path, old_val, new_val, diffs)
        
        elif old != new:
            diffs.append(StateDiff(path, old, new, ChangeType.MODIFIED))
    
    # ==================== SSE 推送方法 ====================
    
    def _push_incremental_update(self, diffs: List[StateDiff]):
        """推送增量更新"""
        message = {
            'type': 'incremental',
            'version': self._version,
            'timestamp': datetime.now().isoformat(),
            'game_id': self.game_id,
            'changes': [
                {
                    'path': d.path,
                    'new_value': d.new_value,
                    'change_type': d.change_type.value
                }
                for d in diffs
            ]
        }
        self.sse_manager.broadcast(self.game_id, message)
    
    def get_full_state(self) -> Optional[Dict]:
        """
        获取全量状态（用于HTTP GET请求响应）
        
        使用场景：
        - 页面刷新后，前端发起 GET /game/{id}/state 请求
        - 新用户中途加入观战
        
        Returns:
            完整状态字典，包含版本号信息
        """
        if not self._current_state:
            return None
        
        return {
            'version': self._version,
            'timestamp': datetime.now().isoformat(),
            'game_id': self.game_id,
            'state': asdict(self._current_state)
        }
    
    def get_full_state_for_client(self, client_version: Optional[int] = None) -> Dict:
        """
        获取全量状态（带版本校验）
        
        Args:
            client_version: 客户端当前版本号，如果落后太多则返回全量
            
        Returns:
            如果客户端版本与当前一致，返回 {'up_to_date': True}
            否则返回完整状态
        """
        if client_version == self._version:
            return {'up_to_date': True, 'version': self._version}
        
        return self.get_full_state() or {'error': 'Game not started'}
    
    # ==================== 客户端管理 ====================
    
    def register_client(self, client_id: str):
        """注册新客户端连接（仅建立SSE，不推送全量状态）"""
        self._client_versions[client_id] = 0  # 初始版本为0，表示需要全量更新
    
    def unregister_client(self, client_id: str):
        """注销客户端连接"""
        self._client_versions.pop(client_id, None)
    
    def handle_client_ack(self, client_id: str, version: int):
        """处理客户端确认收到指定版本"""
        self._client_versions[client_id] = version
    
    # ==================== 历史记录（可选） ====================
    
    def _save_to_history(self):
        """保存状态到历史"""
        self._state_history.append({
            'version': self._version,
            'timestamp': datetime.now().isoformat(),
            'state': asdict(self._current_state)
        })
    
    def get_state_at_version(self, version: int) -> Optional[FullGameState]:
        """获取指定版本的状态（用于回放）"""
        for record in self._state_history:
            if record['version'] == version:
                # 从字典重建对象
                return self._dict_to_state(record['state'])
        return None
    
    # ==================== 工具方法 ====================
    
    def get_current_state(self) -> Optional[FullGameState]:
        """获取当前完整状态"""
        return copy.deepcopy(self._current_state)
    
    def get_version(self) -> int:
        """获取当前版本号"""
        return self._version
    
    def _dict_to_state(self, data: Dict) -> FullGameState:
        """从字典重建状态对象（简化版，实际需要完整实现）"""
        # 这里需要实现从字典到dataclass的完整转换
        pass
```

---

## 4. HTTP API 路由设计

### 4.1 文件位置

```
backend/
├── api/
│   ├── __init__.py
│   ├── app.py              # FastAPI 应用主入口
│   ├── routes.py           # 通用路由（如健康检查）
│   └── game_routes.py      # 游戏相关路由（新增）
├── game_state_sync_manager.py  # GameStateSyncManager 类
├── sse_manager.py              # SSEManager 类
└── ...
```

### 4.2 游戏路由文件

```python
# 文件位置: backend/api/game_routes.py

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from typing import Dict, Optional
import uuid

# 导入管理器类
from ..game_state_sync_manager import GameStateSyncManager
from ..sse_manager import SSEManager

router = APIRouter(prefix="/game", tags=["game"])

# ========== 全局注册表 ==========
# 游戏状态管理器注册表 {game_id: GameStateSyncManager}
game_managers: Dict[str, GameStateSyncManager] = {}

# SSE 管理器（全局单例）
sse_manager = SSEManager()

# ========== 游戏生命周期管理 ==========

def create_game(game_id: str, game_engine) -> GameStateSyncManager:
    """
    创建新游戏
    
    在游戏启动时调用，由 backend/app.py 或 game_init.py 触发
    """
    if game_id in game_managers:
        raise ValueError(f"Game {game_id} already exists")
    
    manager = GameStateSyncManager(game_id, sse_manager)
    game_managers[game_id] = manager
    return manager

def get_game_manager(game_id: str) -> Optional[GameStateSyncManager]:
    """获取游戏管理器"""
    return game_managers.get(game_id)

def remove_game(game_id: str):
    """清理游戏资源"""
    if game_id in game_managers:
        del game_managers[game_id]

# ========== API 端点 ==========

@router.get("/{game_id}/state")
async def get_game_state(game_id: str, client_version: Optional[int] = None):
    """
    获取游戏全量状态
    
    使用场景：
    - 页面刷新后恢复状态
    - 新用户中途加入
    - SSE断线重连后校验版本
    
    Args:
        game_id: 游戏ID
        client_version: 客户端当前版本号（可选），用于校验是否需要更新
        
    Returns:
        完整游戏状态或提示已是最新
    """
    manager = get_game_manager(game_id)
    if not manager:
        raise HTTPException(status_code=404, detail="Game not found")
    
    return manager.get_full_state_for_client(client_version)

@router.get("/{game_id}/events")
async def game_events(game_id: str, request: Request):
    """
    SSE 实时事件流
    
    建立长连接，接收增量更新
    """
    manager = get_game_manager(game_id)
    if not manager:
        raise HTTPException(status_code=404, detail="Game not found")
    
    # 生成或获取客户端ID
    client_id = request.headers.get('X-Client-ID')
    if not client_id:
        client_id = str(uuid.uuid4())
    
    # 注册客户端
    manager.register_client(client_id)
    
    # 返回 SSE 流
    return StreamingResponse(
        sse_manager.connect(game_id, client_id),
        media_type="text/event-stream",
        headers={
            'X-Client-ID': client_id,
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
        }
    )

@router.post("/{game_id}/action")
async def submit_action(game_id: str, action: dict):
    """
    提交玩家行动
    
    前端选择行动后调用此接口
    
    请求体示例：
    {
        "player_id": 0,
        "action_id": 65,
        "action_type": "normal"
    }
    """
    manager = get_game_manager(game_id)
    if not manager:
        raise HTTPException(status_code=404, detail="Game not found")
    
    # 将行动传递给游戏引擎
    # 具体实现取决于你的游戏引擎架构
    # 例如：manager.game_engine.send(action)
    
    # 游戏引擎处理后会 yield 新的 ActionRequest
    # 由 GameStateSyncManager.update_from_action_request() 自动处理并推送更新
    
    return {"status": "action_received"}
```

### 4.3 主应用注册路由

```python
# 文件位置: backend/api/app.py

from fastapi import FastAPI
from .game_routes import router as game_router

app = FastAPI(title="AOI Game API")

# 注册游戏路由
app.include_router(game_router)

# 其他路由...
```

---

## 5. 完整实现示例

本节通过一个**具体场景**详解从发现增量到推送到前端的全过程。

### 5.1 场景设定

**当前状态**：
- 玩家0在位置 (3, 5) 建造了一个工会（building_id=2）
- 玩家0消耗了 2金钱 + 1矿石
- 玩家0的板面分数增加了3分
- 当前玩家切换到玩家1

**变更内容**：
1. `players[0].resources.money`: 15 → 13
2. `players[0].resources.ore`: 5 → 4
3. `players[0].buildings.guild`: 4 → 3
4. `players[0].boardscore`: 20 → 23
5. `map_state.grid[3][5].building_id`: 0 → 2
6. `map_state.grid[3][5].controller`: -1 → 0
7. `meta.current_player_id`: 0 → 1

### 5.2 完整代码实现

```python
# 文件位置: backend/game_state_sync_manager.py

import json
import copy
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum

class ChangeType(Enum):
    """变更类型"""
    ADDED = "added"
    MODIFIED = "modified"
    REMOVED = "removed"

@dataclass
class StateDiff:
    """状态差异"""
    path: str
    old_value: Any
    new_value: Any
    change_type: ChangeType


class GameStateSyncManager:
    """游戏状态同步管理器 - 完整实现"""
    
    def __init__(self, game_id: str, sse_manager: 'SSEManager'):
        self.game_id = game_id
        self.sse_manager = sse_manager
        
        self._current_state: Optional[Dict] = None
        self._last_pushed_state: Optional[Dict] = None
        self._version: int = 0
        self._state_history: List[Dict] = []
        self._client_versions: Dict[str, int] = {}
    
    # ==================== 核心入口方法 ====================
    
    def update_from_action_request(self, request: 'ActionRequest') -> None:
        """
        主入口：从 ActionRequest 更新状态并推送增量
        
        调用时机：每次游戏引擎 yield 返回时
        """
        print(f"\n{'='*60}")
        print(f"[Step 1] 接收到 ActionRequest")
        print(f"         当前玩家: {request.player_id}, 行动类型: {request.action_type}")
        
        # Step 1: 提取新状态
        new_state = self._extract_state_from_request(request)
        print(f"[Step 2] 状态提取完成")
        
        # Step 2: 计算增量（关键步骤）
        diffs = self._calculate_optimized_diff(self._current_state, new_state)
        print(f"[Step 3] 增量计算完成，发现 {len(diffs)} 处变更:")
        for i, diff in enumerate(diffs, 1):
            print(f"         {i}. {diff.path}: {diff.old_value} -> {diff.new_value}")
        
        # Step 3: 更新当前状态
        self._current_state = new_state
        self._version += 1
        print(f"[Step 4] 状态更新完成，新版本号: {self._version}")
        
        # Step 4: 推送更新
        if diffs:
            self._push_incremental_update(diffs)
            print(f"[Step 5] 增量更新已推送到前端")
        else:
            print(f"[Step 5] 无变更，跳过推送")
        
        # Step 5: 保存历史
        self._save_to_history()
        
        # Step 6: 更新上一次推送状态
        self._last_pushed_state = copy.deepcopy(new_state)
        print(f"{'='*60}\n")
    
    # ==================== 状态提取 ====================
    
    def _extract_state_from_request(self, request: 'ActionRequest') -> Dict:
        """从 ActionRequest 提取完整状态为字典"""
        gs = request.game_state
        
        return {
            'meta': {
                'round': gs.round if gs else 0,
                'num_players': gs.num_players if gs else 3,
                'current_player_id': request.player_id,
                'action_type': request.action_type,
                'is_game_over': request.is_game_over
            },
            'players': self._extract_players(gs.players) if gs else [],
            'map_state': self._extract_map_state(gs.map_board_state) if gs else {},
            'available_actions': [
                {'action_id': k, 'description': v}
                for k, v in request.available_actions.items()
            ]
        }
    
    def _extract_players(self, players: List['PlayerState']) -> List[Dict]:
        """提取玩家状态"""
        return [
            {
                'player_id': p.player_id,
                'resources': {
                    'money': p.resources['money'],
                    'ore': p.resources['ore'],
                    'bank_book': p.resources['bank_book'],
                    'law_book': p.resources['law_book'],
                    'engineering_book': p.resources['engineering_book'],
                    'medical_book': p.resources['medical_book'],
                    'meeples': p.resources['meeples'],
                    'all_meeples': p.resources['all_meeples'],
                    'all_bridges': p.resources['all_bridges']
                },
                'buildings': {
                    'workshop': p.buildings[1],
                    'guild': p.buildings[2],
                    'palace': p.buildings[3],
                    'school': p.buildings[4],
                    'university': p.buildings[5],
                    'tower': p.buildings[6],
                    'monument': p.buildings[7],
                    'annex': p.buildings[8]
                },
                'boardscore': p.boardscore,
                'faction_id': p.faction_id,
                'planning_card_id': p.planning_card_id
            }
            for p in players
        ]
    
    def _extract_map_state(self, map_board: 'MapBoardState') -> Dict:
        """
        提取地图状态
        
        后端格式: [terrain, controller, building_id, annex_count, is_neutral]
        前端格式: {terrain, controller, building_id, is_neutral, has_annex}
        """
        return {
            'width': map_board.width,
            'height': map_board.height,
            'grid': [
                [
                    {
                        'terrain': cell[0],           # 地形类型
                        'controller': cell[1],        # 控制者
                        'building_id': cell[2],       # 主建筑
                        'is_neutral': cell[4],        # 是否中立
                        'has_annex': cell[3] > 0      # 是否有侧楼（annex_count > 0）
                    }
                    for cell in row
                ]
                for row in map_board.map_grid
            ],
            'bridges': {str(k): v for k, v in map_board.bridges_is_conneted.items()}
        }
    
    # ==================== 增量计算核心 ====================
    
    def _calculate_optimized_diff(self, old_state: Optional[Dict], 
                                   new_state: Dict) -> List[StateDiff]:
        """
        计算优化后的增量
        
        对地图使用专门的单元格级diff算法
        """
        diffs = []
        
        if not old_state:
            # 首次初始化
            return [StateDiff('', None, new_state, ChangeType.ADDED)]
        
        # 1. 对比 meta
        diffs.extend(self._calculate_object_diff('meta', old_state.get('meta', {}), 
                                                  new_state.get('meta', {})))
        
        # 2. 对比 players
        diffs.extend(self._calculate_players_diff(
            old_state.get('players', []),
            new_state.get('players', [])
        ))
        
        # 3. 对比地图（使用优化的单元格级diff）
        diffs.extend(self._calculate_map_diff(
            old_state.get('map_state', {}),
            new_state.get('map_state', {})
        ))
        
        # 4. 对比 available_actions
        diffs.extend(self._calculate_object_diff('available_actions',
                                                  old_state.get('available_actions', []),
                                                  new_state.get('available_actions', [])))
        
        return diffs
    
    def _calculate_object_diff(self, path: str, old: Any, new: Any) -> List[StateDiff]:
        """递归计算对象差异"""
        diffs = []
        
        if type(old) != type(new):
            diffs.append(StateDiff(path, old, new, ChangeType.MODIFIED))
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
        """计算玩家列表差异"""
        diffs = []
        
        for i, (old_p, new_p) in enumerate(zip(old_players, new_players)):
            player_diffs = self._calculate_object_diff(f'players[{i}]', old_p, new_p)
            diffs.extend(player_diffs)
        
        return diffs
    
    def _calculate_map_diff(self, old_map: Dict, new_map: Dict) -> List[StateDiff]:
        """
        专门优化地图增量计算 - 只返回变更的单元格
        
        前端展示字段: terrain, controller, building_id, is_neutral, has_annex
        注意：后端 annex_count 转换为前端 has_annex (bool)
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
    
    # ==================== SSE 推送 ====================
    
    def _push_incremental_update(self, diffs: List[StateDiff]):
        """推送增量更新到所有连接的客户端"""
        message = {
            'type': 'incremental',
            'version': self._version,
            'timestamp': datetime.now().isoformat(),
            'game_id': self.game_id,
            'changes': [
                {
                    'path': d.path,
                    'new_value': d.new_value,
                    'change_type': d.change_type.value
                }
                for d in diffs
            ]
        }
        
        # 使用 SSEManager 广播
        self.sse_manager.broadcast(self.game_id, message)
    
    def get_full_state_for_client(self, client_version: Optional[int] = None) -> Dict:
        """获取全量状态（HTTP GET响应）"""
        if client_version == self._version:
            return {'up_to_date': True, 'version': self._version}
        
        if not self._current_state:
            return {'error': 'Game not started'}
        
        return {
            'version': self._version,
            'timestamp': datetime.now().isoformat(),
            'game_id': self.game_id,
            'state': self._current_state
        }
    
    def register_client(self, client_id: str):
        """注册新客户端"""
        self._client_versions[client_id] = 0
    
    def _save_to_history(self):
        """保存状态到历史"""
        self._state_history.append({
            'version': self._version,
            'timestamp': datetime.now().isoformat(),
            'state': copy.deepcopy(self._current_state)
        })
```

### 5.3 运行示例输出

```
============================================================
[Step 1] 接收到 ActionRequest
         当前玩家: 1, 行动类型: normal
[Step 2] 状态提取完成
[Step 3] 增量计算完成，发现 8 处变更:
         1. players[0].resources.money: 15 -> 13
         2. players[0].resources.ore: 5 -> 4
         3. players[0].buildings.guild: 4 -> 3
         4. players[0].boardscore: 20 -> 23
         5. map_state.grid[3][5].building_id: 0 -> 2
         6. map_state.grid[3][5].controller: -1 -> 0
         7. map_state.grid[3][5].has_annex: false -> true  (建造了侧楼)
         8. meta.current_player_id: 0 -> 1
[Step 4] 状态更新完成，新版本号: 43
[Step 5] 增量更新已推送到前端
============================================================
```

### 5.4 推送到前端的 SSE 消息

```json
{
  "type": "incremental",
  "version": 43,
  "timestamp": "2024-01-15T10:30:15.123456",
  "game_id": "game_abc123",
  "changes": [
    {"path": "players[0].resources.money", "new_value": 13, "change_type": "modified"},
    {"path": "players[0].resources.ore", "new_value": 4, "change_type": "modified"},
    {"path": "players[0].buildings.guild", "new_value": 3, "change_type": "modified"},
    {"path": "players[0].boardscore", "new_value": 23, "change_type": "modified"},
    {"path": "map_state.grid[3][5].building_id", "new_value": 2, "change_type": "modified"},
    {"path": "map_state.grid[3][5].controller", "new_value": 0, "change_type": "modified"},
    {"path": "map_state.grid[3][5].has_annex", "new_value": true, "change_type": "modified"},
    {"path": "meta.current_player_id", "new_value": 1, "change_type": "modified"}
  ]
}
```

---

## 6. SSE 管理器设计

```python
# 建议文件位置: backend/sse_manager.py

import asyncio
from typing import Dict, Set, AsyncGenerator
from fastapi import Request
from fastapi.responses import StreamingResponse
import json

class SSEManager:
    """
    SSE (Server-Sent Events) 管理器
    
    管理客户端连接，支持按游戏房间广播消息
    """
    
    def __init__(self):
        # {game_id: {client_id: queue}}
        self._connections: Dict[str, Dict[str, asyncio.Queue]] = {}
        
    async def connect(self, game_id: str, client_id: str) -> AsyncGenerator[str, None]:
        """
        建立 SSE 连接
        
        使用示例（FastAPI路由）：
        ```python
        @router.get("/game/{game_id}/events")
        async def game_events(request: Request, game_id: str):
            client_id = request.headers.get('X-Client-ID', str(uuid.uuid4()))
            return StreamingResponse(
                sse_manager.connect(game_id, client_id),
                media_type="text/event-stream"
            )
        ```
        """
        queue = asyncio.Queue()
        
        if game_id not in self._connections:
            self._connections[game_id] = {}
        self._connections[game_id][client_id] = queue
        
        try:
            # 发送初始连接成功消息
            yield self._format_sse({
                'type': 'connected',
                'client_id': client_id,
                'game_id': game_id
            })
            
            # 持续监听消息队列
            while True:
                message = await queue.get()
                if message is None:  # 断开信号
                    break
                yield self._format_sse(message)
                
        finally:
            # 清理连接
            await self.disconnect(game_id, client_id)
    
    async def disconnect(self, game_id: str, client_id: str):
        """断开连接"""
        if game_id in self._connections:
            self._connections[game_id].pop(client_id, None)
            if not self._connections[game_id]:
                del self._connections[game_id]
    
    def broadcast(self, game_id: str, message: dict):
        """广播消息给指定游戏的所有客户端"""
        if game_id not in self._connections:
            return
        
        for queue in self._connections[game_id].values():
            try:
                queue.put_nowait(message)
            except asyncio.QueueFull:
                pass
    
    def send_to_client(self, client_id: str, message: dict):
        """发送消息给指定客户端"""
        for game_connections in self._connections.values():
            if client_id in game_connections:
                try:
                    game_connections[client_id].put_nowait(message)
                except asyncio.QueueFull:
                    pass
                break
    
    def _format_sse(self, data: dict) -> str:
        """格式化 SSE 消息"""
        return f"data: {json.dumps(data)}\n\n"
```

---

## 5. 前端状态管理（配合后端SSE）

```typescript
// 建议文件位置: frontend/src/stores/gameState.ts

import { ref, reactive, watch } from 'vue'
import { defineStore } from 'pinia'

// ============ 类型定义（与后端对应） ============

interface GameMeta {
  round: number
  num_players: number
  current_player_id: number
  action_type: string
  is_game_over: boolean
  setup_choice_is_completed: boolean
  setup_build_is_completed: boolean
}

interface Resources {
  money: number
  ore: number
  bank_book: number
  law_book: number
  engineering_book: number
  medical_book: number
  meeples: number
  all_meeples: number
  all_bridges: number
}

interface PlayerState {
  player_id: number
  planning_card_id: number
  faction_id: number
  resources: Resources
  // ... 其他字段
}

interface MapCell {
  /**
   * 地图单元格 - 前端展示用
   * 
   * 从后端提取的字段：
   * - terrain: 地形类型（决定地块背景色）
   * - controller: 控制者ID（决定边框颜色）
   * - building_id: 主建筑类型（决定建筑图片）
   * - is_neutral: 是否中立建筑
   * - has_annex: 是否有侧楼（侧楼可与其他建筑共存）
   */
  
  // 地形类型 (0-7): 0=水域, 1=平原(棕), 2=沼泽(黑), 3=湖泊(蓝), 4=森林(绿), 5=山脉(灰), 6=荒地(红), 7=沙漠(黄)
  terrain: number
  
  // 控制者玩家ID (-1=无, 0=玩家1, 1=玩家2, 2=玩家3)
  controller: number
  
  // 主建筑类型 (0=无, 1=车间, 2=工会, 3=宫殿, 4=学校, 5=大学, 6=塔楼, 7=山脉, 8=侧楼)
  building_id: number
  
  // 是否中立建筑（影响建筑样式）
  is_neutral: boolean
  
  // 是否有侧楼（侧楼可与其他建筑共存，叠加显示）
  has_annex: boolean
}

interface MapState {
  width: number
  height: number
  grid: MapCell[][]
  bridges: Record<string, number>  // 桥梁连接状态
}

interface FullGameState {
  meta: GameMeta
  setup: any  // 游戏设置
  players: PlayerState[]
  map_state: MapState
  display_board: any
  available_actions: any[]
  final_scores?: any
}

interface StateChange {
  path: string
  new_value: any
  change_type: 'added' | 'modified' | 'removed'
}

interface SSEMessage {
  type: 'connected' | 'full' | 'incremental'
  version: number
  timestamp: string
  game_id: string
  state?: FullGameState
  changes?: StateChange[]
}

// ============ Pinia Store ============

export const useGameStateStore = defineStore('gameState', () => {
  // ========== 状态 ==========
  const state = reactive<FullGameState>({
    meta: {
      round: 0,
      num_players: 3,
      current_player_id: -1,
      action_type: '',
      is_game_over: false,
      setup_choice_is_completed: false,
      setup_build_is_completed: false
    },
    players: [],
    // ... 其他初始状态
  })
  
  const version = ref(0)
  const isConnected = ref(false)
  const clientId = ref('')
  const gameId = ref('')
  
  let eventSource: EventSource | null = null
  
  // ========== 核心方法 ==========
  
  /**
   * 初始化游戏连接
   * 流程：1. GET全量状态 -> 2. 建立SSE连接 -> 3. 接收增量更新
   */
  async function init(gameIdParam: string) {
    gameId.value = gameIdParam
    
    // 步骤1：获取全量状态
    await fetchFullState()
    
    // 步骤2：建立SSE连接（接收后续增量更新）
    connectSSE()
  }
  
  /**
   * 获取全量状态（HTTP GET）
   * 用于页面刷新后恢复状态
   */
  async function fetchFullState() {
    try {
      const response = await fetch(`/api/game/${gameId.value}/state?client_version=${version.value}`)
      const data = await response.json()
      
      if (data.up_to_date) {
        console.log('State is up to date')
        return
      }
      
      if (data.error) {
        throw new Error(data.error)
      }
      
      // 应用全量状态
      if (data.state) {
        Object.assign(state, data.state)
        version.value = data.version
        console.log('Full state loaded, version:', version.value)
      }
    } catch (error) {
      console.error('Failed to fetch full state:', error)
      throw error
    }
  }
  
  /**
   * 建立 SSE 连接（仅用于增量更新）
   */
  function connectSSE() {
    const url = `/api/game/${gameId.value}/events`
    
    // 如果有clientId，传递给后端保持会话
    const headers: Record<string, string> = {}
    if (clientId.value) {
      headers['X-Client-ID'] = clientId.value
    }
    
    eventSource = new EventSource(url, { headers })
    
    eventSource.onopen = () => {
      isConnected.value = true
      console.log('SSE connected')
    }
    
    eventSource.onmessage = (event) => {
      const message: SSEMessage = JSON.parse(event.data)
      handleSSEMessage(message)
    }
    
    eventSource.onerror = async (error) => {
      console.error('SSE error:', error)
      isConnected.value = false
      
      // SSE断开时，尝试重新获取全量状态并重建连接
      await handleReconnection()
    }
  }
  
  /**
   * 处理 SSE 消息（仅增量更新）
   */
  function handleSSEMessage(message: SSEMessage) {
    switch (message.type) {
      case 'connected':
        // 保存后端分配的clientId
        clientId.value = message.client_id || clientId.value
        break
        
      case 'incremental':
        // 增量更新：应用每个变更
        if (message.changes) {
          applyChanges(message.changes)
          version.value = message.version
        }
        break
        
      // 注意：不再处理 'full' 类型的SSE消息
      // 全量更新改为通过HTTP GET获取
    }
  }
  
  /**
   * 处理重连
   */
  async function handleReconnection() {
    console.log('Attempting to reconnect...')
    
    // 1. 重新获取全量状态
    await fetchFullState()
    
    // 2. 重建SSE连接
    connectSSE()
  }
  
  /**
   * 应用增量变更到状态
   */
  function applyChanges(changes: StateChange[]) {
    for (const change of changes) {
      applySingleChange(state, change.path, change.new_value, change.change_type)
    }
  }
  
  /**
   * 应用单个变更
   * 
   * 路径示例：
   * - "meta.round"
   * - "players[0].resources.money"
   * - "map_state.grid[3][5].building_id"
   */
  function applySingleChange(obj: any, path: string, value: any, type: string) {
    const keys = path.split(/\.|\[|\]/).filter(k => k !== '')
    let current = obj
    
    for (let i = 0; i < keys.length - 1; i++) {
      const key = keys[i]
      const nextKey = keys[i + 1]
      
      // 如果下一级是数字索引，确保当前是数组
      if (/^\d+$/.test(nextKey) && !Array.isArray(current[key])) {
        current[key] = []
      }
      // 如果下一级是字符串，确保当前是对象
      else if (!/^\d+$/.test(nextKey) && typeof current[key] !== 'object') {
        current[key] = {}
      }
      
      current = current[key]
    }
    
    const lastKey = keys[keys.length - 1]
    
    switch (type) {
      case 'added':
      case 'modified':
        current[lastKey] = value
        break
      case 'removed':
        if (Array.isArray(current)) {
          current.splice(parseInt(lastKey), 1)
        } else {
          delete current[lastKey]
        }
        break
    }
  }
  
  /**
   * 断开连接
   */
  function disconnect() {
    eventSource?.close()
    eventSource = null
    isConnected.value = false
  }
  
  // ========== Getter ==========
  
  const currentPlayer = computed(() => {
    return state.players.find(p => p.player_id === state.meta.current_player_id)
  })
  
  const getPlayer = (playerId: number) => {
    return state.players.find(p => p.player_id === playerId)
  }
  
  return {
    state,
    version,
    isConnected,
    clientId,
    connect,
    disconnect,
    currentPlayer,
    getPlayer
  }
})
```

---

## 6. 完整交互流程

### 6.1 正常游戏流程（增量更新）

```
┌──────────┐                    ┌──────────────┐                    ┌──────────┐
│  GameEngine │  1. yield        │ GameStateSync │  2. 计算diff       │  前端    │
│           │  ActionRequest   │   Manager     │  3. SSE推送        │          │
│           │ ───────────────> │               │ ─────────────────> │          │
│           │                  │               │  {type:            │          │
│           │  4. 等待用户输入   │               │   "incremental",   │          │
│           │ <─────────────── │               │   changes: [...]}  │          │
│           │                  │               │                    │  4. 应用  │
│           │  5. send(action) │               │                    │  增量变更  │
│           │ ───────────────> │               │                    │          │
└──────────┘                  └──────────────┘                    └──────────┘
```

### 6.2 页面刷新重载（全量更新）

```
┌──────────┐     1. 页面刷新后     ┌──────────┐     2. GET请求      ┌──────────────┐
│   前端    │  建立SSE连接         │   前端    │  /game/{id}/state │ GameStateSync │
│ (重载后)  │ ──────────────────> │           │ ─────────────────> │   Manager    │
│           │                     │           │                   │              │
│           │  3. 接收全量状态      │           │ <──────────────── │              │
│           │ <────────────────── │           │   {state: {...}}  │              │
│           │                     │           │                   │              │
│           │  4. SSE增量更新      │           │  5. 后续yield     │              │
│           │ <─────────────────> │           │ <───────────────> │              │
│           │  恢复实时同步         │           │  增量推送          │              │
└──────────┘                     └──────────┘                   └──────────────┘
```

---

## 7. 消息格式规范

### 7.1 SSE 增量更新消息

```json
{
  "type": "incremental",
  "version": 42,
  "timestamp": "2024-01-15T10:30:00Z",
  "game_id": "game_12345",
  "changes": [
    {
      "path": "meta.current_player_id",
      "new_value": 1,
      "change_type": "modified"
    },
    {
      "path": "players[0].resources.money",
      "new_value": 15,
      "change_type": "modified"
    },
    {
      "path": "players[0].ability_tile_ids[2]",
      "new_value": 5,
      "change_type": "added"
    },
    {
      "path": "map_state.grid[3][5].building_id",
      "new_value": 2,
      "change_type": "modified"
    },
    {
      "path": "map_state.grid[3][5].controller",
      "new_value": 0,
      "change_type": "modified"
    },
    {
      "path": "map_state.grid[3][5].has_annex",
      "new_value": true,
      "change_type": "modified"
    },
    {
      "path": "map_state.bridges[\"((0,2),(1,0))\"]",
      "new_value": 0,
      "change_type": "modified"
    }
  ]
}
```

### 7.2 SSE 连接成功消息

```json
{
  "type": "connected",
  "client_id": "client_abc123",
  "game_id": "game_12345"
}
```

### 7.3 HTTP GET 全量状态响应

**正常响应（状态有更新）：**
```json
{
  "version": 42,
  "timestamp": "2024-01-15T10:30:00Z",
  "game_id": "game_12345",
  "state": {
    "meta": { ... },
    "setup": { ... },
    "players": [ ... ],
    "map_state": { 
      "width": 13,
      "height": 9,
      "grid": [
        [
          {
            "terrain": 4,
            "controller": -1,
            "building_id": 0,
            "is_neutral": false,
            "has_annex": false
          },
          ...
        ],
        ...
      ],
      "bridges": { ... }
    },
    "display_board": { ... },
    "available_actions": [ ... ]
  }
}
```

**已是最新（版本一致）：**
```json
{
  "up_to_date": true,
  "version": 42
}
```

**错误响应：**
```json
{
  "error": "Game not started"
}
```

---

## 8. 架构总结

### 8.1 数据流总结

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              正常游戏流程                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  GameEngine ──yield──> GameStateSyncManager ──SSE增量──> 前端                │
│       ↑                                                    │                │
│       │                                                    ↓                │
│       │                                              用户选择行动            │
│       │                                                    │                │
│       └────────────────send(action)────────────────<── POST /action          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                              页面刷新流程                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. 页面加载                                                                │
│  2. GET /game/{id}/state ──> 获取全量状态                                    │
│  3. 渲染界面                                                                 │
│  4. 建立 SSE 连接                                                           │
│  5. 接收后续增量更新                                                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 8.2 关键设计决策

| 决策 | 说明 |
|------|------|
| **增量更新粒度** | 地图到单元格级别，其他到字段级别 |
| **全量更新方式** | HTTP GET 请求，非 SSE 推送 |
| **版本号机制** | 每次状态更新递增，用于校验同步状态 |
| **重连策略** | SSE断开时自动重新GET全量状态并重建连接 |
| **available_actions** | 每次完整推送，不计算增量（直接替换整个列表） |
| **set类型字段** | `controlled_map_ids`、`reachable_map_ids` 作为集合增量更新，计算 added/removed |

### 8.3 特殊字段增量策略

#### 8.3.1 available_actions（完整替换）

可选行动列表每次都完整推送，不计算增量差异。

```json
{
  "path": "available_actions",
  "old_value": [...],
  "new_value": [{"action_id": 1, "description": "建造车间"}, ...],
  "change_type": "modified"
}
```

#### 8.3.2 set 类型字段增量更新

`controlled_map_ids` 和 `reachable_map_ids` 作为集合进行增量计算，只发送变化的部分：

```json
{
  "changes": [
    {
      "path": "players[0].controlled_map_ids.added",
      "new_value": [[1, 2], [3, 4]],
      "change_type": "added"
    },
    {
      "path": "players[0].controlled_map_ids.removed",
      "old_value": [[5, 6]],
      "change_type": "removed"
    }
  ]
}
```

前端处理逻辑：
```javascript
// 处理 set 增量更新
if (path.endsWith('.added')) {
  const basePath = path.replace('.added', '');
  const currentSet = new Set(getByPath(state, basePath).map(p => JSON.stringify(p)));
  new_value.forEach(item => currentSet.add(JSON.stringify(item)));
  setByPath(state, basePath, Array.from(currentSet).map(s => JSON.parse(s)));
}
else if (path.endsWith('.removed')) {
  const basePath = path.replace('.removed', '');
  const currentSet = new Set(getByPath(state, basePath).map(p => JSON.stringify(p)));
  new_value.forEach(item => currentSet.delete(JSON.stringify(item)));
  setByPath(state, basePath, Array.from(currentSet).map(s => JSON.parse(s)));
}
```

### 8.4 注意事项与优化建议

1. **性能优化**：
   - 地图使用专门的 `_calculate_map_diff()` 方法，只对比变更的单元格
   - 每个单元格变更单独一条 diff，路径格式：`map_state.grid[row][col].field`

2. **可靠性**：
   - 前端维护版本号，SSE断开后重新GET时携带版本号
   - 后端返回 `up_to_date: true` 避免不必要的数据传输
   - 可以实现心跳机制检测连接健康（可选）

3. **安全性**：
   - SSE 连接需要验证用户身份
   - 本游戏无私有数据，所有玩家看到相同信息

4. **扩展性**：
   - 预留 `_save_to_history()` 方法支持回放功能
   - 支持观战模式（只读连接，同样使用 GET + SSE 流程）
