"""
前端展示所需数据结构定义

此文件定义了从前端展示角度需要的简化数据模型，与后端游戏状态对应。
用于 GameStateManager 将游戏状态转换为前端可用的格式。
"""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Any
from enum import Enum


class ChangeType(Enum):
    """变更类型"""
    ADDED = "added"           # 新增
    MODIFIED = "modified"     # 修改
    REMOVED = "removed"       # 删除


@dataclass
class GameMeta:
    """游戏元信息"""
    round: int = 0                      # 当前回合数
    num_players: int = 3                # 玩家数量
    current_player_id: int = -1         # 当前行动玩家ID（0=玩家1, 1=玩家2, 2=玩家3）
    action_type: str = ""               # 当前行动类型 ("normal" / "immediate")
    is_game_over: bool = False          # 游戏是否结束
    setup_choice_is_completed: bool = False  # 初始板块选择阶段是否完成
    setup_build_is_completed: bool = False   # 初始建筑摆放阶段是否完成
    current_player_order: List[int] = field(default_factory=list)  # 当前回合未pass的玩家顺序
    pass_order: List[int] = field(default_factory=list)            # 本回合已pass的玩家顺序


@dataclass
class TimerState:
    """Timer state carried in full and incremental frontend payloads."""
    action_deadline: int = 0
    current_player_remaining: int = 0
    main_time_limit: int = 0
    byo_yomi_time_limit: int = 0
    all_players_remaining: List[int] = field(default_factory=list)


@dataclass
class Resources:
    """资源"""
    money: int = 0                      # 金钱
    ore: int = 0                        # 矿石
    bank_book: int = 0                  # 银行学书籍
    law_book: int = 0                   # 法学书籍
    engineering_book: int = 0           # 工程学书籍
    medical_book: int = 0               # 医学书籍
    meeples: int = 0                    # 可用米宝数量
    all_meeples: int = 7                # 米宝总数
    all_bridges: int = 3                # 桥梁总数


@dataclass
class Magics:
    """魔力"""
    zone1: int = 5                      # 魔力区域1（初始区）
    zone2: int = 7                      # 魔力区域2（缓冲/消耗区）
    zone3: int = 0                      # 魔力区域3（可用区）


@dataclass
class Buildings:
    """建筑"""
    workshop: int = 9                   # 车间剩余数量
    guild: int = 4                      # 工会剩余数量
    palace: int = 1                     # 宫殿剩余数量
    school: int = 3                     # 学校剩余数量
    university: int = 1                 # 大学剩余数量
    tower: int = 0                      # 中立塔楼拥有数量
    monument: int = 0                   # 中立纪念碑拥有数量
    annex: int = 0                      # 侧楼剩余数量
    neutral_workshop: int = 0           # 中立车间拥有数量
    neutral_guild: int = 0              # 中立工会拥有数量
    neutral_palace: int = 0             # 中立宫殿拥有数量
    neutral_school: int = 0             # 中立学校拥有数量
    neutral_university: int = 0         # 中立大学拥有数量


@dataclass
class Tracks:
    """科技轨"""
    bank: int = 0                       # 银行学轨进度
    law: int = 0                        # 法学轨进度
    engineering: int = 0                # 工程学轨进度
    medical: int = 0                    # 医学轨进度


@dataclass
class PlayerState:
    """玩家状态"""
    player_id: int = 0                  # 玩家ID（0/1/2）
    planning_card_id: int = 0           # 规划卡ID
    faction_id: int = 0                 # 派系ID
    palace_tile_id: int = 0             # 宫殿瓦片ID
    is_got_palace: bool = False         # 是否已解锁宫殿板块
    resources: Resources = field(default_factory=Resources)
    magics: Magics = field(default_factory=Magics)
    buildings: Buildings = field(default_factory=Buildings)
    tracks: Tracks = field(default_factory=Tracks)
    tracks_over_7_amount: int = 0       # 科技轨超过7的数量
    navigation_level: int = 0           # 航行等级
    shovel_level: int = 3               # 铲子等级
    temp_navigation: bool = False       # 临时航行标记
    controlled_map_ids: List[Tuple[int, int]] = field(default_factory=list)   # 控制的地图坐标列表
    adjacent_map_ids: List[Tuple[int, int]] = field(default_factory=list)     # 相邻地图坐标列表
    reachable_map_ids: List[Tuple[int, int]] = field(default_factory=list)    # 可达地图坐标列表
    citys_amount: int = 0               # 城市数量
    booster_ids: List[int] = field(default_factory=list)                      # 拥有的回合助推器ID列表
    ability_tile_ids: List[int] = field(default_factory=list)                 # 拥有的能力瓦片ID列表
    science_tile_ids: List[int] = field(default_factory=list)                 # 拥有的科技瓦片ID列表
    boardscore: int = 20                # 板面得分
    trackscore: int = 0                 # 科技轨得分
    chainscore: int = 0                 # 连锁得分
    resourcescore: int = 0              # 资源得分
    main_action_is_done: bool = False   # 主行动是否已完成
    ispass: bool = False                # 是否已跳过


@dataclass
class MapCell:
    """
    地图单元格 - 前端展示用简化模型
    
    从后端 map_grid[row][col] 提取：
    - [0]: terrain - 地形类型（决定地块颜色）
    - [1]: controller - 控制玩家ID（决定边框颜色，-1表示无）
    - [2]: building_id - 建筑类型（决定建筑图片，0表示无建筑）
    - [3]: annex_count - 侧楼数量（0或1，侧楼可与其他建筑共存）
    - [4]: is_neutral - 是否中立建筑（影响样式）
    
    前端展示所需最小信息：
    1. terrain: 地形颜色
    2. building_id: 主建筑（含类型、是否中立）
    3. has_annex: 是否有侧楼（侧楼可叠加）
    """
    # 地形类型 (0-7): 决定地块背景色
    # 0=水域, 1=平原(棕), 2=沼泽(黑), 3=湖泊(蓝), 4=森林(绿), 5=山脉(灰), 6=荒地(红), 7=沙漠(黄)
    terrain: int = 0
    
    # 控制者玩家ID (-1=无, 0=玩家1, 1=玩家2, 2=玩家3)
    controller: int = -1
    
    # 主建筑类型 (0=无, 1=车间, 2=工会, 3=宫殿, 4=学校, 5=大学, 6=塔楼, 7=山脉, 8=侧楼)
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
            'main_building': self.building_id,
            'is_neutral': self.is_neutral,
            'has_annex': self.has_annex,
            'controller': self.controller
        }


@dataclass
class MapState:
    """地图状态"""
    width: int = 13                                     # 地图宽度
    height: int = 9                                     # 地图高度
    grid: List[List[MapCell]] = field(default_factory=list)  # 二维网格，9行13列
    bridges: Dict[str, int] = field(default_factory=dict)    # 桥梁连接状态


@dataclass
class ScienceTrackState:
    """科技轨展示状态"""
    is_crowned: bool = False                            # 是否有加冕标记
    meeples: List[int] = field(default_factory=lambda: [-1]*4)      # 米宝位置标记，-1表示空，0~n-1为玩家id


@dataclass
class DisplayBoardState:
    """展示板状态"""
    science_tracks: Dict[str, ScienceTrackState] = field(default_factory=dict)  # 四条科技轨状态
    ability_tile_owners: Dict[int, List[int]] = field(default_factory=dict)     # 能力板块拥有者列表（按 owner_list 顺序）
    science_tile_owners: Dict[int, List[int]] = field(default_factory=dict)     # 高科板块拥有者列表（按 owner_list 顺序）


@dataclass
class GameSetup:
    """游戏设置"""
    selected_planning_cards: List[int] = field(default_factory=list)     # 选中的规划卡
    selected_factions: List[int] = field(default_factory=list)           # 选中的派系
    selected_palace_tiles: List[int] = field(default_factory=list)       # 选中的宫殿瓦片
    selected_round_boosters: List[int] = field(default_factory=list)     # 选中的回合助推器
    round_booster_coin_counts: Dict[int, int] = field(default_factory=dict)  # 每张回合助推板正面累计的 1 金币数量
    round_scoring_order: List[int] = field(default_factory=list)         # 轮次计分顺序
    final_scoring: int = 0                                               # 最终计分ID
    ability_tiles_order: List[int] = field(default_factory=list)         # 能力瓦片顺序
    science_tiles_order: List[int] = field(default_factory=list)         # 科技瓦片顺序
    selected_book_actions: List[int] = field(default_factory=list)       # 选中的书本行动
    init_player_order: List[int] = field(default_factory=list)           # 初始玩家顺序
    current_global_books: Dict[str, int] = field(default_factory=lambda: {
        'bank_book': 12, 'law_book': 12, 'engineering_book': 12, 'medical_book': 12
    })


@dataclass
class AvailableAction:
    """可选行动"""
    action_id: int = 0                  # 行动唯一标识
    description: str = ""               # 行动描述文本


@dataclass
class ActionHistoryEntry:
    """结构化行动记录"""
    kind: str = "action"                # 记录类型（action / divider）
    stage_key: str = ""                 # 所属阶段键
    player_id: int = -1                 # 后端玩家ID（0开始）
    action_type: str = ""               # 行动类型（normal / immediate）
    action_id: Optional[int] = None     # 行动ID；阶段分割线为空
    description: str = ""               # 行动描述文本
    selection_source: str = "manual"    # 选择来源（manual / system）
    selection_strategy: str = ""        # 选择策略标识


@dataclass
class FinalScore:
    """最终得分"""
    total: int = 0                      # 总分
    board: int = 0                      # 板面得分
    chain: int = 0                      # 连锁得分
    track: int = 0                      # 科技轨得分
    resource: int = 0                   # 资源得分


@dataclass
class FullGameState:
    """完整游戏状态（用于全量更新）"""
    meta: GameMeta = field(default_factory=GameMeta)
    setup: GameSetup = field(default_factory=GameSetup)
    players: List[PlayerState] = field(default_factory=list)
    map_state: MapState = field(default_factory=MapState)
    display_board: DisplayBoardState = field(default_factory=DisplayBoardState)
    available_actions: List[AvailableAction] = field(default_factory=list)
    action_history: List[ActionHistoryEntry] = field(default_factory=list)
    final_scores: Optional[Dict[int, FinalScore]] = None
    timer_state: TimerState = field(default_factory=TimerState)


@dataclass
class StateDiff:
    """状态差异（用于增量更新）"""
    path: str                           # 变更路径，如 "players[0].resources.money"
    old_value: Any                      # 旧值
    new_value: Any                      # 新值
    change_type: ChangeType             # 变更类型
