import random
import time
from typing import Callable

class GameStateBase:
    """游戏状态类"""
    class GameSetup: # TODO 轮次计分的限制性规定判定
        """游戏初始设置类"""
        def __init__(self, num_players: int):
            self.num_players = num_players
            self.seedid = 7
            
            # 所有可用组件
            self.all_factions = list(range(1, 13))       # 共12派系
            self.all_planning_cards = list(range(1, 8))  # 共7规划卡
            self.all_round_scoring = list(range(1, 13))  # 共12轮次计分卡
            self.all_final_scoring = list(range(1, 5))   # 共4最终轮次计分卡
            self.all_book_actions = list(range(1, 7))    # 共6书本行动板块
            self.all_ability_tiles = list(range(1, 13))  # 共12能力板块
            self.all_science_tiles = list(range(1, 19))  # 共18科学板块
            self.all_palace_tiles = list(range(1, 17))   # 共16宫殿板块
            self.all_round_boosters = list(range(1, 11)) # 共10回合助推板
            
            # 初始化设置结果
            self.selected_planning_cards = []       # [int]
            self.selected_factions = []             # [int]
            self.selected_palace_tiles = []         # [int]
            self.selected_round_boosters = []       # [int]            
            self.round_scoring_order = []           # [int] 顺序重要
            self.final_scoring = 0                  # int
            self.ability_tiles_order = []           # [int] 顺序重要
            self.science_tiles_order = []           # [int] 顺序重要
            self.selected_book_actions = []         # [int] 
            
            # 当前全局书资源
            self.current_global_books = {
                'bank_book': 12,                   # 银行书总量上限
                'law_book': 12,                    # 法律书总量上限
                'engineering_book': 12,            # 工程书总量上限
                'medical_book': 12,                # 医学书总量上限
            }
            
            # 执行初始设置
            self.perform_initial_setup()
        
        def perform_initial_setup(self):
            """执行所有初始设置步骤"""
            self.seedid = int(time.strftime("%S%H%M", time.localtime()))
            random.seed(self.seedid)
            # print(f'seed:{self.seedid}')

            # 1. 选择6张规划卡
            self.selected_planning_cards =sorted(random.sample(self.all_planning_cards, 6))

            # 2. 选择人数+1的派系板块
            self.selected_factions = sorted(random.sample(self.all_factions, self.num_players + 1))
            
            # 3. 选取人数+1个宫殿板块作为可选项
            self.selected_palace_tiles = sorted(random.sample(self.all_palace_tiles, self.num_players + 1))
            
            # 4. 选取人数+3个回合助推板作为可选项
            self.selected_round_boosters = sorted(random.sample(self.all_round_boosters, self.num_players + 3))
            
            # 5. 选取6个轮次计分板块并随机排序
            self.round_scoring_order = random.sample(self.all_round_scoring, 6)
            random.shuffle(self.round_scoring_order)

            # 6. 随机选取1个最终计分板块
            self.final_scoring = random.choice(self.all_final_scoring)

            # 7. 对共12块能力板块随机排序
            self.ability_tiles_order = random.sample(self.all_ability_tiles, 12)
            random.shuffle(self.ability_tiles_order)
            
            # 8. 选取2+人数*2的科学板块并随机排序
            self.science_tiles_order = random.sample(self.all_science_tiles, self.num_players * 2 + 2)
            random.shuffle(self.science_tiles_order)
            
            # 9. 选取3个书本行动
            self.selected_book_actions = sorted(random.sample(self.all_book_actions, 3))            
      
        def __str__(self):
            """返回设置结果的字符串表示"""
            return (
                f"游戏初始设置 ({self.num_players}玩家):\n"
                f"随机种子: {self.seedid}\n"
                f"派系板块: {self.selected_factions}\n"
                f"可用规划卡: {self.selected_planning_cards}\n"
                f"轮次计分顺序: {self.round_scoring_order}\n"
                f"最终计分: {self.final_scoring}\n"
                f"书本行动: {self.selected_book_actions}\n"
                f"能力板块顺序: {self.ability_tiles_order}\n"
                f"科学板块顺序: {self.science_tiles_order}\n"
                f"可用宫殿板块: {self.selected_palace_tiles}\n"
                f"可用回合助推板: {self.selected_round_boosters}"
            )
    
    class PlayerState:
        """玩家状态类"""
        def __init__(self, player_id: int):
            self.player_id = player_id    # 玩家ID
            self.planning_card_id = 0     # 选择的规划卡ID
            self.faction_id = 0           # 选择的派系ID
            self.palace_tile_id = 0       # 选择的宫殿板块ID
            self.booster_ids = []         # 使用过的助推板ID
            
            # 资源系统
            self.resources = {
                'money': 15,            # 钱
                'ore': 3,               # 矿
                'bank_book': 0,         # 银行书
                'law_book': 0,          # 法律书
                'engineering_book': 0,  # 工程书
                'medical_book': 0,      # 医学书
                'meeples': 0,           # 米宝
                'all_meeples': 7,       # 所有米宝
                'all_bridges': 3         # 所有桥
            }

            # 建筑系统
            self.buildings = {
                1: 9,  # 车间
                2: 4,  # 工会
                3: 1,  # 宫殿
                4: 3,  # 学校
                5: 1,  # 大学
                6: 0,  # 中立塔楼
                7: 0,  # 中立纪念碑
                8: 0,  # 侧楼
                9: 0,  # 中立车间
                10: 0, # 中立工会
                11: 0, # 中立宫殿
                12: 0, # 中立学校
                13: 0, # 中立大学
            }

            # 航行和铲子等级
            self.navigation_level = 0
            self.shovel_level = 3
            self.temp_navigation = False
            
            # 科技轨系统
            self.tracks:dict[str,int] = {
                'bank': 0,         # 银行轨
                'law': 0,          # 法律轨
                'engineering': 0,  # 工程轨
                'medical': 0,      # 医学轨
            }
            
            # 魔力系统
            self.magics = {
                1: 5,  # 一区魔力
                2: 7,  # 二区魔力
                3: 0,  # 三区魔力
            }

            self.controlled_map_ids = set()    # 当前控制的领土ID列表
            self.adjacent_map_ids = set()      # 相邻坐标列表（排除控制领土）
            self.reachable_map_ids = set()     # 可抵达坐标列表（包含控制领土，不包含水域）
            self.settlements_and_cities = {}   # 当前聚落与城市字典

            # 创建各地形id需要几铲才能成为原生地的初始空字典，在选择规划卡后更新
            self.terrain_id_need_shovel_times = {i: -1 for i in range(1,8)}

            self.science_tile_ids = []         # 当前已获得科技板块ID列表
            self.ability_tile_ids = []         # 当前已获得能力板块ID列表
            self.all_effect_objects = []       # 所有效果板块列表
            
            self.is_got_palace = False     # 是否已解锁宫殿板块
            self.citys_amount = 0          # 当前城市数量
            self.tracks_over_7_amount = 0  # 当前科技轨超过7数量
                    
            self.boardscore = 20    # 当前板面分数
            self.trackscore = 0     # 当前科技轨分数
            self.chainscore = 0     # 当前大链分数
            self.resourcescore = 0  # 当前资源分数

            self.main_action_is_done = False # 主要行动是否完成
            self.ispass = False              # 是否已跳过
            self.choice_position = tuple()   # 玩家选择地图坐标记录

            self.income_effect_list: list[Callable[[int],None]] = []        # 收入阶段效果列表 
            self.pass_effect_list: list[Callable[[int],None]] = []          # 略过动作效果列表
            self.round_end_effect_list: list[Callable[[int],None]] = []     # 轮次结束效果列表
            self.setup_effect_list: list[Callable[[int],None]] = []         # 初始设置效果列表

        def __str__(self):
            """玩家状态的中文表示"""
            # 初始状态
            init_str = ", ".join([
                f"派系: {self.faction_id}",
                f"规划卡: {self.planning_card_id}",
                f"宫殿板: {self.palace_tile_id}", 
                f"助推板: {self.booster_ids}"        
            ])

            # 资源状态
            resources_str = ", ".join([
                f"金钱: {self.resources['money']}",
                f"矿石: {self.resources['ore']}",
                f"银行书: {self.resources['bank_book']}",
                f"法律书: {self.resources['law_book']}",
                f"工程书: {self.resources['engineering_book']}",
                f"医学书: {self.resources['medical_book']}",
                f"米宝: {self.resources['meeples']}",
                f"剩余米宝: {self.resources['all_meeples']}",
                f"剩余桥梁: {self.resources['all_bridges']}"
            ])
            
            # 建筑状态
            buildings_str = ", ".join([
                f"车间: {self.buildings[1]}",
                f"工会: {self.buildings[2]}",
                f"宫殿: {self.buildings[3]}",
                f"学校: {self.buildings[4]}",
                f"大学: {self.buildings[5]}",
                f"塔楼: {self.buildings[6]}",
                f"山脉: {self.buildings[7]}",
                f"侧楼: {self.buildings[8]}"
            ])
            
            # 科技轨状态
            tracks_str = ", ".join([
                f"银行轨: {self.tracks['bank']}级",
                f"法律轨: {self.tracks['law']}级",
                f"工程轨: {self.tracks['engineering']}级",
                f"医学轨: {self.tracks['medical']}级"
            ])
            
            # 魔力状态
            magics_str = ", ".join([
                f"一区魔力: {self.magics[1]}个",
                f"二区魔力: {self.magics[2]}个",
                f"三区魔力: {self.magics[3]}个"
            ])
            
            # 坐标状态
            coords_str = ", ".join([
                f"控制领土: {self.controlled_map_ids}",
                f"相邻坐标: {self.adjacent_map_ids}",
                f"可抵达坐标: {self.reachable_map_ids}"
            ])
            
            # 分数状态
            scores_str = ", ".join([
                f"板面分数: {self.boardscore}",
                f"科技轨分数: {self.trackscore}",
                f"大链分数: {self.chainscore}",
                f"资源分数: {self.resourcescore}"
            ])
            
            # 其他状态
            other_str = ", ".join([
                f"城市数量: {self.citys_amount}",
                f"科技轨超过7级: {self.tracks_over_7_amount}条",
                f"宫殿解锁: {'是' if self.is_got_palace else '否'}"
            ])
            
            return (
                f"玩家 {self.player_id + 1} 状态:\n"
                f"初始: {init_str}\n"
                f"资源: {resources_str}\n"
                f"建筑: {buildings_str}\n"
                f"科技: {tracks_str}\n"
                f"魔力: {magics_str}\n"
                f"坐标: {coords_str}\n"
                f"其他: {other_str}\n"
                f"分数: {scores_str}\n"
            )   

    class MapBoardState:
        """游戏地图状态"""
        def __init__(self):
            # 地图尺寸
            self.width = 13
            self.height = 9
            
            # 地形类型定义
            self.terrain_types = {
                0: "水域",
                1: "平原",
                2: "沼泽",
                3: "湖泊",
                4: "森林",
                5: "山脉",
                6: "荒地",
                7: "沙漠",
            }
            
            # 建筑类型定义
            self.building_types = {
                -1: "不可建造",
                0: "无",
                1: "车间",
                2: "工会",
                3: "宫殿",
                4: "学校",
                5: "大学",
                6: "塔楼",
                7: "山脉",
                8: "侧楼"
            }

            self.building_magic = {
                0: 0,
                1: 1,   # 车间 -> 1魔力
                8: 1,   # 侧楼 -> 1魔力
                2: 2,   # 工会 -> 2魔力
                4: 2,   # 学校 -> 2魔力
                6: 2,   # 塔楼 -> 2魔力
                3: 3,   # 宫殿 -> 3魔力
                5: 3,   # 大学 -> 3魔力
                7: 4,   # 山脉 -> 4魔力
            }
            
            # 地形网格 (二维数组)
            self.terrain_grid = [
                [4,0,3,2,1,6,5,0,3,2,1,7,0],
                [5,0,0,4,3,4,7,0,4,5,3,0,2],
                [6,3,2,0,5,1,2,0,0,6,0,0,6],
                [7,5,6,0,7,6,0,2,0,0,1,5,4],
                [1,4,1,7,0,0,0,4,5,3,6,7,1],
                [2,0,0,0,3,5,0,7,1,0,2,3,6],
                [3,0,1,2,0,4,1,0,0,0,0,0,0],
                [0,7,3,0,6,2,7,6,2,3,4,2,0],
                [4,5,6,0,7,5,1,3,4,5,6,7,1]
            ]  # 每个元素是地形类型ID
            
            # 汇总地图网格
            self.map_grid: list[list[list[int]]] = [
                [
                    [
                        self.terrain_grid[i][j],    # 地形
                        -1,                         # 控制玩家id
                        0,                          # 建筑id
                        0,                          # 侧楼数量
                        False,                      # 是否中立建筑
                    ] for j in range(13)
                ] for i in range(9)
            ]

            # 可建桥的地块坐标
            self.enable_bridge_pos_dict = {
                (0, 2) : ((1, 0), (2, 2)) ,
                (0, 8) : ((1, 6),) ,
                (0, 11) : ((1, 12),) ,
                (1, 0) : ((0, 2),) ,
                (1, 3) : ((2, 2),) ,
                (1, 6) : ((0, 8),) ,
                (1, 10) : ((2, 12), (3, 10)) ,
                (1, 12) : ((0, 11),) ,
                (2, 2) : ((0, 2), (1, 3)) ,
                (2, 4) : ((3, 2),) ,
                (2, 6) : ((3, 7),) ,
                (2, 9) : ((3, 7), (4, 9), (3, 10)) ,
                (2, 12) : ((1, 10),) ,
                (3, 2) : ((2, 4),) ,
                (3, 4) : ((4, 3), (5, 4)) ,
                (3, 5) : ((4, 7), (5, 5)) ,
                (3, 7) : ((2, 6), (2, 9)) ,
                (3, 10) : ((1, 10), (2, 9)) ,
                (4, 2) : ((6, 2),) ,
                (4, 3) : ((3, 4), (5, 4), (6, 3)) ,
                (4, 7) : ((3, 5), (5, 5)) ,
                (4, 9) : ((2, 9),) ,
                (5, 0) : ((6, 2),) ,
                (5, 4) : ((3, 4), (4, 3), (6, 3)) ,
                (5, 5) : ((3, 5), (4, 7)) ,
                (5, 7) : ((6, 6), (7, 7)) ,
                (5, 8) : ((7, 8),) ,
                (5, 10) : ((7, 10),) ,
                (5, 11) : ((7, 11),) ,
                (6, 0) : ((7, 1), (8, 0)) ,
                (6, 2) : ((4, 2), (5, 0)) ,
                (6, 3) : ((4, 3), (5, 4), (7, 4)) ,
                (6, 6) : ((5, 7),) ,
                (7, 1) : ((6, 0),) ,
                (7, 2) : ((8, 4),) ,
                (7, 4) : ((6, 3),) ,
                (7, 7) : ((5, 7),) ,
                (7, 8) : ((5, 8),) ,
                (7, 10) : ((5, 10),) ,
                (7, 11) : ((5, 11),) ,
                (8, 0) : ((6, 0),) ,
                (8, 4) : ((7, 2),) ,
            }

            # 该桥位是否已被建造
            self.bridges_is_conneted = {
                ((0, 2), (1, 0)): -1,
                ((0, 2), (2, 2)): -1,
                ((0, 8), (1, 6)): -1,
                ((0, 11), (1, 12)): -1,
                ((1, 3), (2, 2)): -1,
                ((1, 10), (2, 12)): -1,
                ((1, 10), (3, 10)): -1,
                ((2, 4), (3, 2)): -1,
                ((2, 6), (3, 7)): -1,
                ((2, 9), (3, 7)): -1,
                ((2, 9), (4, 9)): -1,
                ((2, 9), (3, 10)): -1,
                ((3, 4), (4, 3)): -1,
                ((3, 4), (5, 4)): -1,
                ((3, 5), (4, 7)): -1,
                ((3, 5), (5, 5)): -1,
                ((4, 2), (6, 2)): -1,
                ((4, 3), (5, 4)): -1,
                ((4, 3), (6, 3)): -1,
                ((4, 7), (5, 5)): -1,
                ((5, 0), (6, 2)): -1,
                ((5, 4), (6, 3)): -1,
                ((5, 7), (6, 6)): -1,
                ((5, 7), (7, 7)): -1,
                ((5, 8), (7, 8)): -1,
                ((5, 10), (7, 10)): -1,
                ((5, 11), (7, 11)): -1,
                ((6, 0), (7, 1)): -1,
                ((6, 0), (8, 0)): -1,
                ((6, 3), (7, 4)): -1,
                ((7, 2), (8, 4)): -1,
            }
    
    class DisplayBoardState:
        """展示板状态"""
        def __init__(self,num_players):
            # 科技展示板花费
            self.tech_ability_board_spend = {
                # 以打乱科技板块顺序号：其中指定花费 (银行书, 法律书, 工程书, 医学书)
                0: (2,0,0,0),
                1: (2,0,0,0),
                2: (0,2,0,0),
                3: (0,2,0,0),
                4: (0,0,2,0),
                5: (0,0,2,0),
                6: (0,0,0,2),
                7: (0,0,0,2),
                8: (2,2,0,0) if num_players == 4 else (2,0,0,0),
                9: (0,0,2,2) if num_players == 4 else (0,2,0,0),
                10: (0,0,2,0),
                11: (0,0,0,2)
            }
            
            # 科技展示板剩余数量
            self.tech_ability_board_remaining_amount = {i:1 for i in range(2 * num_players + 2)}
            
            # 能力展示板奖励
            self.ability_board_rewards = {
                #以打乱能力板块顺序号：奖励 (银行书, 法律书, 工程书, 医学书, 银行等级, 法律等级, 工程等级, 医学等级)
                0: (0,0,0,0,3,0,0,0),
                1: (1,0,0,0,2,0,0,0),
                2: (2,0,0,0,1,0,0,0),
                3: (0,0,0,0,0,3,0,0),
                4: (0,1,0,0,0,2,0,0),
                5: (0,2,0,0,0,1,0,0),
                6: (0,0,0,0,0,0,3,0),
                7: (0,0,1,0,0,0,2,0),
                8: (0,0,2,0,0,0,1,0),
                9: (0,0,0,0,0,0,0,3),
                10: (0,0,0,1,0,0,0,2),
                11: (0,0,0,2,0,0,0,1),
            }
            
            # 能力展示板剩余数量
            self.ability_board_remaining_amount = {i:4 for i in range(12)}
            
            # 科学展示板图（科技轨道）
            self.science_tracks = {
                'bank': {
                    'is_crowned': False,    # 是否被登顶
                    'meeples': [False] * 4  # 4个米宝位置
                },
                'law': {
                    'is_crowned': False,
                    'meeples': [False] * 4
                },
                'engineering': {
                    'is_crowned': False,
                    'meeples': [False] * 4
                },
                'medical': {
                    'is_crowned': False,
                    'meeples': [False] * 4
                }
            }     

    def __init__(self, num_players: int = 3):
        if num_players:
            self.num_players = num_players                                                    # 玩家数量
            self.setup = __class__.GameSetup(num_players)                                     # 游戏初始状态设置
            self.players = [__class__.PlayerState(i) for i in range(num_players)]             # 玩家状态
            self.map_board_state = __class__.MapBoardState()                                  # 地图状态
            self.display_board_state = __class__.DisplayBoardState(num_players)               # 展示板状态
            self.round = 0                                                                    # 当前回合 (0表示设置阶段)
            self.init_player_order = random.sample(list(range(num_players)),num_players)      # 初始玩家顺位
            self.current_player_order = self.init_player_order.copy()                         # 当前玩家顺位
            self.pass_order = list(reversed(self.current_player_order))                       # 本回合玩家结束顺序
            self.setup_choice_is_completed = False                                            # 初始选择是否完成
            self.check = self.init_check()                                                    # 初始化检查函数
            self.adjust = self.init_adjust()                                                  # 初始化调整函数

    def invoke_immediate_aciton(self, player_id: int, args: tuple):
        return
    
    def update_reachable_map_ids_set(self, player_id: int, update_pos: tuple = tuple()):
        """更新可抵达的坐标列表"""

        def update_reachable_map_ids(pos: tuple[int, int], navigation_distance: int = 1, visited: set = set()):
            if visited:
                visited = set()
            
            # 如果已经访问过这个位置，直接返回
            if pos in visited:
                return
    
            # 标记当前位置为已访问
            visited.add(pos)

            # 判断该地块是否是可建桥位两侧中的一测
            if pos in self.map_board_state.enable_bridge_pos_dict:
                # 如是，则遍历其对侧地块
                for corres_pos in self.map_board_state.enable_bridge_pos_dict[pos]:
                    (i,j),(p,q) = pos, corres_pos
                    # 判断对侧地块是否已被其他玩家占领
                    if self.map_board_state.map_grid[p][q][1] in (-1, player_id):
                        # 若未被其他玩家占领，则排序两侧地块坐标，生成桥键
                        if i > p or (i == p and q > j):
                            bridge_key = ((p,q),(i,j))
                        else:
                            bridge_key = ((i,j),(p,q))
                        # 根据桥键查询该桥位是否已被该玩家连接
                        if self.map_board_state.bridges_is_conneted[bridge_key] == player_id:
                            # 如已被连接，则将对侧地块加入可抵地块集合中
                            player.reachable_map_ids.add((p,q))

            i,j = pos
            direction = [(-1,i%2-1),(-1,i%2),(0,-1),(0,1),(1,i%2-1),(1,i%2)]

            for dx,dy in direction:
                new_i, new_j = i + dx, j + dy
                if (
                    # 在合法边界内
                    0 <= new_i <= 8 and 0 <= new_j <= 12
                    # 没有被其他玩家控制
                    and self.map_board_state.map_grid[new_i][new_j][1] == -1
                ):
                    if (
                        # 如果该地块不是水域
                        self.map_board_state.map_grid[new_i][new_j][0] != 0
                    ):
                        # 添加该地块到可抵达集合中
                        player.reachable_map_ids.add((new_i,new_j))
                    elif (
                        # 如果该玩家有航行能力
                        current_navigation_level >= navigation_distance
                    ):
                        # 递归查找可抵达地块
                        update_reachable_map_ids((new_i,new_j), navigation_distance+1, visited)

        player = self.players[player_id]
        current_navigation_level = player.navigation_level + 1 if player.temp_navigation else 0

        # 移除原可抵达地块坐标集合中已被控制的
        for pos in player.reachable_map_ids.copy():
            i,j = pos
            if self.map_board_state.map_grid[i][j][1] != -1:
                player.reachable_map_ids.remove(pos)

        # 如有指定更新的控制坐标，则以该坐标为原点进行查找
        if update_pos:
            update_reachable_map_ids(update_pos)
        else:
            # 如无，则遍历控制列表添加（如有新增）新的可抵达地块坐标进入集合
            for pos in player.controlled_map_ids:
                update_reachable_map_ids(pos)

    def absorb_magics_check(self, player_id: int, pos: tuple[int, int]):
        
        i,j = pos
        direction = [(-1,i%2-1),(-1,i%2),(0,-1),(0,1),(1,i%2-1),(1,i%2)]
        player_get_magics = {i:0 for i in range(self.num_players)}

        # 遍历相邻地块
        for dx,dy in direction:
            new_i, new_j = i + dx, j + dy
            if 0 <= new_i <= 8 and 0 <= new_j <= 12:
                # 若相邻建筑为其他派系控制，则加入计算其他派系获取魔力点数
                if self.map_board_state.map_grid[new_i][new_j][1] not in (-1, player_id): 
                    get_magics_player_id, building_id, num_side_building = self.map_board_state.map_grid[new_i][new_j][1:4]
                    # 计算该其他玩家该地块可吸取的魔力点数
                    get_magics_num = self.map_board_state.building_magic[building_id] + num_side_building
                    # 将该其他玩家该地块可吸取魔力点数加入该其他玩家本次可获取魔力点数之和中
                    player_get_magics[get_magics_player_id] += get_magics_num

        if self.round != 0: # 初始建筑摆放不触发吸魔行动
            for player_idx, get_magics_nums in player_get_magics.items():
                actual_num = min(
                    get_magics_nums,                                                                # 获取的魔力值
                    2 * self.players[player_idx].magics[1] + self.players[player_idx].magics[2],    # 当前最大可转动魔力点数
                    self.players[player_idx].boardscore - 1                                         # 最大可支付版面分数
                )
                if actual_num:
                    self.invoke_immediate_aciton(player_idx, ('gain_magics', actual_num))

    def city_establishment_check(self, player_id: int, mode: str, pos: tuple[int, int], bridge_key: tuple[tuple[int,int],tuple[int,int]] = tuple()):

        settlements_and_cities = self.players[player_id].settlements_and_cities
        if pos not in settlements_and_cities:
            settlements_and_cities[pos] = [pos, False]

        def find(pos: tuple[int,int]):
            # 路径压缩优化
            stack = []
            current = pos
            # 找到根节点
            while settlements_and_cities[current][0] != current:
                stack.append(current)
                current = settlements_and_cities[current][0]
            root = current
            root_is_city = settlements_and_cities[root][1]
            
            # 路径压缩：将所有节点直接指向根节点
            for node in stack:
                settlements_and_cities[node] = [root, root_is_city]
            return root, root_is_city
        
        def merge(pos_a: tuple[int,int], pos_b: tuple[int,int]):
            root_a, is_city_a = find(pos_a)
            root_b, is_city_b = find(pos_b)

            if root_a == root_b:
                return root_a, is_city_a  # 已经在同一聚落

            # 新聚落的城市状态
            new_is_city = is_city_a or is_city_b
            # 更新a的父节点信息，以b为新父节点
            settlements_and_cities[root_a] = [root_b, new_is_city]
            # 更新父节点b的城市状态
            settlements_and_cities[root_b] = [root_b, new_is_city]

            return root_b, new_is_city

        current_root, current_is_city = find(pos)

        match mode:
            # 新建一座桥的情况
            case 'bridge':
                for temp_pos in bridge_key:
                    if temp_pos == pos:
                        continue
                    i,j = temp_pos
                    # 若桥对侧地块已被己方控制
                    if self.map_board_state.map_grid[i][j][1] == player_id:
                        # 则合并两侧聚落
                        current_root, current_is_city = merge(pos, temp_pos)
                        break
                else:
                    # 即桥对侧不被己方控制，则直接跳出，无需进行后续建城检查，因该聚落魔力点数不会更新
                    return 
            # 更新一个建筑的情况
            case 'build':
                i,j = pos
                need_following_check = False
                # 判断桥对侧地块是否已连接（若存在）
                if pos in self.map_board_state.enable_bridge_pos_dict:
                    for corres_pos in self.map_board_state.enable_bridge_pos_dict[pos]:
                        p,q = corres_pos
                        # 若桥对侧地块被己方控制
                        if self.map_board_state.map_grid[p][q][1] == player_id:
                            # 获取桥键
                            if i > p or (i == p and j > q):
                                bridge_key = (corres_pos, pos)
                            else:
                                bridge_key = (pos, corres_pos)
                            # 判断该桥是否已被己方建造
                            if self.map_board_state.bridges_is_conneted[bridge_key] == player_id:
                                # 若已建造，则将两侧建筑合并为同一聚落
                                current_root, current_is_city = merge(corres_pos, pos)
                                need_following_check = True
                            
                direction = [(-1,i%2-1),(-1,i%2),(0,-1),(0,1),(1,i%2-1),(1,i%2)]
                # 遍历判断相邻地块
                for dx,dy in direction:
                    new_i, new_j = i + dx, j + dy
                    if 0 <= new_i <= 8 and 0 <= new_j <= 12:
                        # 若相邻建筑为己方
                        if self.map_board_state.map_grid[new_i][new_j][1] == player_id:
                            # 合并并更新当前聚落信息
                            current_root, current_is_city = merge((new_i, new_j), (i, j))
                            need_following_check = True
                # 若建立该新建筑后，不存在任何相邻地块（含桥对侧地块，如有）上有己方建筑
                # 则无需后续建城检查，直接跳出，因为该聚落魔力点数不会更新
                if need_following_check == False:
                    return 
            case 'upgrade':
                # 在升级一个建筑地块的情况下
                # 相邻地块（含有效桥对侧地块）必已经同属一个聚落，则无需更新聚落，直接进行建城检查
                pass

        # 使用合并后最新的根节点和城市状态
        if not current_is_city:  # 如果当前聚落还不是城市
            curent_settlement_magics_total = 0  # 当前聚落魔力点之和
            curent_settlement_building_nums = 0 # 当前聚落建筑数量

            # 统计当前聚落的所有建筑
            # 遍历所有控制地块，获取其上建筑所需聚落
            for building_pos in self.players[player_id].controlled_map_ids:
                building_root, _ = find(building_pos)
                # 若与当前聚落所属同一聚落
                if building_root == current_root:
                    cur_i, cur_j = building_pos
                    # 则获取该建筑对应魔力点
                    building_id, num_side_building = self.map_board_state.map_grid[cur_i][cur_j][2:4]
                    magics_num = self.map_board_state.building_magic[building_id] + num_side_building
                    # 累加计算该聚落魔力点总数
                    curent_settlement_magics_total += magics_num
                    
                    match building_id:
                        case 5: # 大学算作两个建筑
                            curent_settlement_building_nums += 2 + num_side_building
                        case 7: # 纪念碑算作三个建筑
                            curent_settlement_building_nums += 3 + num_side_building
                        case _:
                            curent_settlement_building_nums += 1 + num_side_building
            
            if (
                # 判断当前聚落魔力点数和是否大于等于7
                curent_settlement_magics_total >= 7
                # 判断当前聚落建筑数量是否大于等于4
                and curent_settlement_building_nums >= 4
            ):
                # 标记根节点为城市
                settlements_and_cities[current_root] = [current_root, True]
                self.players[player_id].citys_amount += 1
                self.invoke_immediate_aciton(player_id, ('select_city_tile',))
        
    def init_check(self):

        def check_money(player_id: int, num: int) -> bool:
            if self.players[player_id].resources['money'] >= num:
                return True
            else:
                return False
        
        def check_ore(player_id: int, num: int) -> bool:
            if self.players[player_id].resources['ore'] >= num:
                return True
            else:
                return False
        
        def check_book(player_id: int, where: str, typ: str, num: int) -> bool:
            
            match where, typ:
                case 'self', 'any':
                    if sum([self.players[player_id].resources[f'{x}_book'] for x in ['bank','law','engineering','medical']]) >= num:
                        return True
                case 'self', _:
                    if self.players[player_id].resources[f'{typ}_book'] >= num:
                        return True
                case 'all', 'any':
                    if sum([self.setup.current_global_books[f'{x}_book'] for x in ['bank','law','engineering','medical']]) >= num:
                        return True
                case 'all', _:
                    if self.setup.current_global_books[f'{typ}_book'] >= num:
                        return True
                case _:
                    raise ValueError(f'不存在【{where}】处的书')
                
            return False              
        
        def check_meeple(player_id: int, where: str, num: int) -> bool:

            match where:
                case 'self':
                    if self.players[player_id].resources['meeples'] >= num:
                        return True
                case 'all':
                    if self.players[player_id].resources['all_meeples'] >= num:
                        return True                    
                case _:
                    raise ValueError(f'不存在【{where}】处的米宝')
            return False
        
        def check_magics(player_id: int, zone: int, num: int) -> bool:
            if self.players[player_id].magics[zone] >= num:
                return True
            else:
                return False
        
        def check_score(player_id: int, num: int) -> bool:
            if self.players[player_id].boardscore >= num:
                return True
            else:
                return False
        
        def check_tracks(player_id: int, typ: str) -> bool:
            if (
                self.players[player_id].tracks[typ] == 7 
                and self.players[player_id].tracks_over_7_amount == self.players[player_id].citys_amount
            ) or (
                self.players[player_id].tracks[typ] == 11
                and self.display_board_state.science_tracks[typ]['is_crowned'] == True
            ):
                return False
            else:
                return True
        
        def check_build(player_id: int, building_id: int) -> bool:
            if self.players[player_id].buildings[building_id] >= 1:
                return True
            return False
        
        def check_bridge(player_id: int) -> bool:
            if self.players[player_id].resources['all_bridges'] >= 1:
                '''判断是否可建桥（有控制地块是可建桥地块，且其桥连接对侧地块未被其他玩家占领，且该桥位尚未被建造）'''
                # 获取以控制的可建桥位
                for pos in self.players[player_id].controlled_map_ids:
                    if pos in self.map_board_state.enable_bridge_pos_dict.keys():
                        for corresponding_pos in self.map_board_state.enable_bridge_pos_dict[pos]:
                            p,q = pos
                            i,j = corresponding_pos
                            # 判断对侧地块是否被其他玩家控制
                            if self.map_board_state.map_grid[i][j][1] in (-1, player_id):
                                # 如无，则排序可建桥位两侧坐标（小者在前）
                                if p > i or (p == i and q > j):
                                    bridge_key = ((i,j),(p,q))
                                else:
                                    bridge_key = ((p,q),(i,j))

                                if self.map_board_state.bridges_is_conneted[bridge_key] == -1:
                                    return True
                                    # 找到一个，确认该行动可被执行即跳出
                return False
            else:
                return False
            
        def check_shovel(player_id: int) -> bool:
            # 判断是否存在可铲地（至少一铲）
            for i,j in self.players[player_id].reachable_map_ids:
                terrain = self.map_board_state.map_grid[i][j][0]
                # 如有则跳出是否可铲判断
                if self.players[player_id].terrain_id_need_shovel_times[terrain] >= 1:
                    return True
            return False
                 
        all_check_list = {
            'money': check_money,
            'ore': check_ore,
            'book': check_book,
            'meeple': check_meeple,
            'magics': check_magics,
            'score': check_score,
            'tracks': check_tracks,
            'building': check_build,
            'bridge': check_bridge,
            'spade': check_shovel,
        }

        def check(player_id: int, list_to_be_checked: list) -> bool:
            for check_item, *check_args in list_to_be_checked:
                if check_item not in all_check_list:
                    raise ValueError(f'非法状态检查对象：{check_item}')
                else:
                    if all_check_list[check_item](player_id,*check_args) == False:
                        return False
            return True
        
        return check

    def init_adjust(self):

        def adjust_money(player_id: int, mode: str, num: int):
            mode_factor = 1 if mode == 'get' else -1
            self.players[player_id].resources['money'] += mode_factor * num
        
        def adjust_ore(player_id:int , mode: str, num:int):
            mode_factor = 1 if mode == 'get' else -1
            self.players[player_id].resources['ore'] += mode_factor * num
        
        def adjust_book(player_id:int , mode: str, typ: str, num: int):
            match mode, typ:
                case 'get', 'any':
                    act_num = min(sum(self.setup.current_global_books.values()), num)
                    for _ in range(act_num):
                        self.invoke_immediate_aciton(player_id, ('select_book', 'get'))
                case 'get', _:
                    act_num = min(self.setup.current_global_books[f'{typ}_book'], num)
                    self.setup.current_global_books[f'{typ}_book'] -= act_num
                    self.players[player_id].resources[f'{typ}_book'] += act_num
                case 'use', 'any':
                    for _ in range(num):
                        self.invoke_immediate_aciton(player_id, ('select_book', 'use'))
                case 'use', _:
                    if num <= self.players[player_id].resources[f'{typ}_book']:
                        self.players[player_id].resources[f'{typ}_book'] -= num
                        self.setup.current_global_books[f'{typ}_book'] += num
                    else:
                        raise ValueError(f'{player_id + 1}号玩家未拥有{typ}书{num}本')
        
        def adjust_meeple(player_id: int, mode: str, args):
            match mode:
                case 'get':
                    num = args
                    act_num = min(num, self.players[player_id].resources['all_meeples'])
                    self.players[player_id].resources['all_meeples'] -=  act_num
                    self.players[player_id].resources['meeples'] += act_num
                case 'use':
                    num = args
                    if num <= self.players[player_id].resources['meeples']:
                        self.players[player_id].resources['meeples'] -= num 
                        self.players[player_id].resources['all_meeples'] +=  num
                    else:
                        raise ValueError(f'{player_id + 1}号玩家未拥有{num}个米宝')
                case 'climb':
                    typ = args
                    self.players[player_id].resources['meeples'] -= 1
                    for i in range(4):
                        if self.display_board_state.science_tracks[typ]['meeples'][i] == False:
                            self.display_board_state.science_tracks[typ]['meeples'][i] = True
                            if i == 0:
                                climb_num = 3
                            else:
                                climb_num = 2
                            break
                    else:
                        climb_num = 1
                        self.players[player_id].resources['all_meeples'] +=  1
                    climb_track(player_id, typ, climb_num)

        def adjust_score(player_id: int, mode: str, which: str, num: int):
            mode_factor = 1 if mode == 'get' else -1
            match which:
                case 'board':
                    self.players[player_id].boardscore += mode_factor * num
                case 'track':
                    self.players[player_id].trackscore += mode_factor * num
                case 'chain':
                    self.players[player_id].chainscore += mode_factor * num
                case 'resource':
                    self.players[player_id].resourcescore += mode_factor * num
                case _:
                    raise ValueError(f'不存在【{which}】板块分数')
            return []
    
        def magic_rotation(player_id: int, mode:str, num:int):
            match mode:
                case 'get':
                    if self.players[player_id].magics[1] > 0:
                        rot_num = min(self.players[player_id].magics[1], num)
                        self.players[player_id].magics[1] -= rot_num
                        self.players[player_id].magics[2] += rot_num
                        num -= rot_num
                    if num != 0:
                        if self.players[player_id].magics[2] > 0:
                            rot_num = min(self.players[player_id].magics[2], num)
                            self.players[player_id].magics[2] -= rot_num
                            self.players[player_id].magics[3] += rot_num
                case 'use':
                    if self.players[player_id].magics[3] >= num:
                        self.players[player_id].magics[3] -= num
                    else:
                        raise ValueError(f'三区无{num}点可用魔力')
                case 'boom':
                    if self.players[player_id].magics[2] >= 2 * num:
                        self.players[player_id].magics[2] -= 2 * num
                        self.players[player_id].magics[3] += num
                    else:
                        raise ValueError(f'不可爆魔，因二区无{2 * num}点魔力')
                case 'else':
                    self.players[player_id].magics[3] += num
                    # 科技板块效果-宫殿

        def climb_track(player_id: int, typ: str, num: int):

            if typ != 'any':
                player = self.players[player_id]

                before_climb = self.players[player_id].tracks[typ]

                if player.tracks[typ] > 7: 
                    if self.display_board_state.science_tracks[typ]['is_crowned'] == True:
                        act_arrive_value = min(player.tracks[typ] + num, 11)
                    else:
                        act_arrive_value = min(player.tracks[typ] + num, 12)
                        if act_arrive_value == 12:
                            self.display_board_state.science_tracks[typ]['is_crowned'] = True
                    self.players[player_id].tracks[typ] = act_arrive_value
                else:
                    if player.tracks_over_7_amount >= player.citys_amount:
                        act_arrive_value = min(player.tracks[typ] + num, 7)
                    else:
                        act_arrive_value = player.tracks[typ] + num
                        if act_arrive_value > 7:
                            player.tracks_over_7_amount += 1
                    self.players[player_id].tracks[typ] = act_arrive_value
                
                after_climb = self.players[player_id].tracks[typ]

                if before_climb < 3 <= after_climb:
                    magic_rotation(player_id, 'get', 1)
                if before_climb < 5 <= after_climb:
                    magic_rotation(player_id, 'get', 2)
                if before_climb < 7 <= after_climb:
                    magic_rotation(player_id, 'get', 2)
                if before_climb < 7 <= after_climb:
                    effect = ()
                    match typ:
                        case 'bank':
                            effect = ('money', 'get', 3)
                        case 'law':
                            effect = ('magics', 'get', 6)
                        case 'engineer':
                            effect = ('ore', 'get', 1)
                        case 'medical':
                            effect = ('score', 'get', 'board', 3)

                    def display_board_tracks_9(player_idx):
                        self.adjust(player_idx, [effect])

                    self.players[player_id].income_effect_list.append(display_board_tracks_9)
                if before_climb < 12 <= after_climb:
                    magic_rotation(player_id, 'get', 3)
            else:
                for _ in range(num):
                    self.invoke_immediate_aciton(player_id, ('select_track',))

        def adjust_terrain(player_id: int, shovel_times: int):

            i,j = self.players[player_id].choice_position

            native_terrain_id = self.players[player_id].planning_card_id
            current_terrain_id = self.map_board_state.map_grid[i][j][0]

            factor = 1 if current_terrain_id >= native_terrain_id else -1
            if abs(current_terrain_id - native_terrain_id) > 3:
                new_terrain_id = (current_terrain_id + factor * shovel_times - 1) % 7 + 1 
            else:
                new_terrain_id = current_terrain_id - factor * shovel_times

            self.map_board_state.map_grid[i][j][0] = new_terrain_id

        def adjust_building(player_id: int, mode:str, to_build_id: int, is_neutral: bool):
                
            i,j = self.players[player_id].choice_position

            match self.map_board_state.map_grid[i][j]:
                # 该地形被其他玩家控制的情况
                case [_,controller, _, _, _] if controller != -1 and controller != player_id:  
                    raise ValueError(f'{chr(ord('A')+i)}{j+1}处已被其他玩家控制')
                
                # 该地形非该玩家原生地形的情况
                case [terrain, _, _, _, _] if terrain != self.players[player_id].planning_card_id:
                    raise ValueError(f'{chr(ord('A')+i)}{j+1}处目前不是你的原生地形')

                # 该地形已存在该玩家建筑的情况
                case [_, _, pre_building_id, pre_side_building_num, pre_is_neutral] if pre_building_id != 0:
                    match mode, pre_building_id, pre_is_neutral, pre_side_building_num, to_build_id, is_neutral:
                        case 'upgrade', pre_building_id, False, _, to_build_id, False if (pre_building_id, to_build_id) in [(1,2),(2,3),(2,4),(4,5)]:
                            # 根据待建建筑id，支付升级费用
                            match to_build_id:
                                # 升级为工会时
                                case 2:
                                    # 判读该地块相邻是否有邻居
                                    direction = [(-1,i%2-1),(-1,i%2),(0,-1),(0,1),(1,i%2-1),(1,i%2)]
                                    for dx, dy in direction:
                                        new_i, new_j = i+dx, j+dy
                                        if 0 <= new_i <= 8 and 0 <= new_j <= 12:
                                            controlled_id = self.map_board_state.map_grid[new_i][new_j][1]
                                            if controlled_id != -1 and controlled_id != player_id:
                                                # 支付有邻居的升级费用
                                                self.adjust(player_id, [('money', 'use', 3), ('ore', 'use', 2)])
                                                break
                                    else:
                                        # 支付无邻居的升级费用
                                        self.adjust(player_id, [('money', 'use', 6), ('ore', 'use', 2)])
                                # 升级为宫殿时
                                case 3:
                                    # 支付升级费用
                                    self.adjust(player_id, [('money', 'use', 6), ('ore', 'use', 4)])
                                    # 标记宫殿已经获得
                                    self.players[player_id].is_got_palace = True
                                    # 激活宫殿板块
                                    cur_player_palace_tile_id = self.players[player_id].palace_tile_id
                                    self.all_available_object_dict['palace_tile'][cur_player_palace_tile_id].activate(player_id)
                                # 升级为学院时
                                case 4:
                                    # 支付升级费用
                                    self.adjust(player_id, [('money', 'use', 5), ('ore', 'use', 3)])
                                    # 立即获取一个能力板块
                                    self.invoke_immediate_aciton(player_id, ('select_ability_tile',))
                                # 升级为大学时
                                case 5:
                                    # 支付升级费用
                                    self.adjust(player_id, [('money', 'use', 8), ('ore', 'use', 5)])
                                    # 立即获取一个能力板块
                                    self.invoke_immediate_aciton(player_id, ('select_ability_tile',))

                            # 调整玩家规划板上建筑数量
                            self.players[player_id].buildings[pre_building_id] += 1
                            self.players[player_id].buildings[to_build_id] -= 1
                        case 'build_annex', _, _, 0, 8, True:
                            pass
                        case 'degrade', 4, False, _, 2, False:
                            pass
                        case 'upgrade_special', 1, False, _, 2, False:
                            # 调整玩家规划板上建筑数量
                            self.players[player_id].buildings[pre_building_id] += 1
                            self.players[player_id].buildings[to_build_id] -= 1
                        case _:
                            raise ValueError(f'已存在建筑物的地形上进行非法操作')
                    
                    # 修改地块的建筑id和侧楼数量和建筑性质
                    self.map_board_state.map_grid[i][j][2:] = to_build_id, pre_side_building_num, is_neutral
                    # 定义检查模式为升级
                    check_mode = 'upgrade'
                # 该地形为该玩家原生地形且无建筑的情况
                case _:
                    match mode, to_build_id, is_neutral:
                        case 'build_normal', 1, False:
                            # 支付建造费用
                            self.adjust(player_id, [('money', 'use', 2), ('ore', 'use', 1)])
                        case 'build_setup', to_build_id, is_neutral if (to_build_id, is_neutral) in [(1,False), (5,False), (6,True)]:
                            pass
                        case 'build_neutral', 1|2|3|4|5|6|7, True:
                            pass
                        case 'build_special', 2, False:
                            pass
                        case 'build_special', 1, False: # 蜥蜴人板块行动效果
                            pass
                        case _:
                            raise ValueError(f'在无建筑物的地形上进行非法操作')
                        
                    # 修改地块控制玩家id和建筑id和建筑性质
                    self.map_board_state.map_grid[i][j][1:3] = player_id, to_build_id
                    self.map_board_state.map_grid[i][j][4] = is_neutral
                    # 调整玩家规划板上建筑数量
                    self.players[player_id].buildings[to_build_id] -= 1
                    # 更新控制地块与可抵地块
                    self.players[player_id].controlled_map_ids.add((i,j))
                    self.update_reachable_map_ids_set(player_id, (i,j))
                    # 定义检查模式为建造
                    check_mode = 'build'

            if mode != 'build_annex':
                # 执行吸取魔力立即行动（如有）
                self.absorb_magics_check(player_id, (i,j))
            # 更新聚落及检查城市建立
            self.city_establishment_check(player_id,check_mode,(i,j))

        def build_bridge(player_id: int):
            self.players[player_id].resources['all_bridges'] -= 1
            self.invoke_immediate_aciton(player_id, ('build_bridge',))
            return 
             
        def shovel(player_id: int, shovel_times: int):
            # 初始化第一铲地标记和位置
            first_shovel = True
            first_pos = tuple()
            # 当仍然存在剩余铲数时
            while shovel_times > 0:
                # 判断是否存在可铲地（至少一铲）
                for i,j in self.players[player_id].reachable_map_ids:
                    terrain = self.map_board_state.map_grid[i][j][0]
                    # 如有则跳出是否可铲判断
                    if self.players[player_id].terrain_id_need_shovel_times[terrain] >= 1:
                        break
                else:
                    # 未跳出，则代表无可铲地块，则跳出铲行动
                    break
                # 选择可铲位置
                self.invoke_immediate_aciton(player_id, ('select_position', 'reachable', ('shovel', 1)))
                # 记录一铲地坐标
                if first_shovel:
                    first_pos = self.players[player_id].choice_position
                    first_shovel = False
                # 获取当前铲坐标
                pos = self.players[player_id].choice_position
                i,j = pos
                # 获取当前铲地块地形
                terrain = self.map_board_state.map_grid[i][j][0]
                # 判断铲当前地块的实际用铲量（需铲次数 和 剩余铲数 的两者小值）
                act_current_shovel_times = min(self.players[player_id].terrain_id_need_shovel_times[terrain], shovel_times)
                # 将该地块铲 实际用铲量 下
                adjust_terrain(player_id, act_current_shovel_times)
                # 更新剩余铲数
                shovel_times -= act_current_shovel_times

            # 剩余铲数归零 或 不可铲 后
            i,j = first_pos
            first_pos_terrain = self.map_board_state.map_grid[i][j][0]
            first_pos_shovel_times = self.players[player_id].terrain_id_need_shovel_times[first_pos_terrain]
            if self.check(player_id, [
                ('money', 2), 
                ('ore', 1 + first_pos_shovel_times * self.players[player_id].shovel_level),
                ('building', 1)
            ]):
                self.players[player_id].choice_position = first_pos
                self.invoke_immediate_aciton(player_id,('build_workshop',))

        all_adjust_list = {
            'money': adjust_money,
            'ore': adjust_ore,
            'book': adjust_book,
            'meeple': adjust_meeple,
            'score': adjust_score,
            'magics': magic_rotation,
            'tracks': climb_track,
            'land': adjust_terrain,
            'building': adjust_building,
            'bridge': build_bridge,
            'spade': shovel
        }

        def adjust(player_id: int, list_to_be_adjusted):
            for adjust_item, *adjust_args in list_to_be_adjusted:
                if adjust_item not in all_adjust_list:
                    raise ValueError(f'非法状态调整对象：{adjust_item}')
                else:
                    all_adjust_list[adjust_item](player_id, *adjust_args)

        return adjust
    
    def effect_object(self): # 效果板块
        
        from EffectObject import AllEffectObject   
             
        # 本局所有需实例化效果板块对象字典
        self.all_available_object_dict: dict[str, dict[int, AllEffectObject.EffectObject]] = {}
        self.all_effect_objects = AllEffectObject(self)

        all_typ_dict = {
            'planning_card': self.setup.selected_planning_cards,
            'faction': self.setup.selected_factions,
            'palace_tile': self.setup.selected_palace_tiles,
            'round_booster': self.setup.selected_round_boosters,
            'ability_tile': self.setup.ability_tiles_order,
            'science_tile': self.setup.science_tiles_order,
            'round_scoring': self.setup.round_scoring_order,
            'final_scoring': [self.setup.final_scoring],
            'book_action': self.setup.selected_book_actions,
            'city_tile': range(1,8),
            'magics_action': range(1,7)
        }

        for typ_name, typ_available_id_list in all_typ_dict.items():

            self.all_available_object_dict[typ_name] = {
                id : self.all_effect_objects.create_actual_object(typ_name, id) 
                for id in typ_available_id_list
            }
        