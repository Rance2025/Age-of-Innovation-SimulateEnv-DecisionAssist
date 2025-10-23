import random
import time
from typing import List,Callable,Union

class GameState:
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
            self.selected_book_actions = []         # [int] 顺序不重要
            
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
                'bridge':0,             # 桥
                'all_bridge': 3         # 所有桥
            }

            # 建筑系统
            self.buildings = {
                1: 9,  # 车间
                2: 4,  # 工会
                3: 1,  # 宫殿
                4: 3,  # 学校
                5: 1   # 大学
            }

            # 航行和铲子等级
            self.navigation_level = 0
            self.shovel_level = 3
            
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

            self.controlled_territory_ids = [] # 当前控制的领土ID列表
            self.adjacent_coords = []          # 相邻坐标列表（排除控制领土）
            self.reachable_coords = []         # 可抵达坐标列表（排除控制领土）
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

            self.income_effect_list: list[Callable[[int],None]] = []        # 收入阶段效果列表 
            self.pass_effect_list: list[Callable[[int],None]] = []          # 略过动作效果列表
            self.round_end_effect_list: list[Callable[[int],None]] = []     # 轮次结束效果列表
            

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
                f"桥梁: {self.resources['bridge']}"
            ])
            
            # 建筑状态
            buildings_str = ", ".join([
                f"车间: {self.buildings[1]}",
                f"工会: {self.buildings[2]}",
                f"宫殿: {self.buildings[3]}",
                f"学校: {self.buildings[4]}",
                f"大学: {self.buildings[5]}"
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
                f"控制领土: {self.controlled_territory_ids}",
                f"相邻坐标: {self.adjacent_coords}",
                f"可抵达坐标: {self.reachable_coords}"
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
                -1: 0,
                0: 0,
                1: 1,   # 车间 -> 1魔力
                8: 1,   # 侧楼 -> 1魔力
                2: 2,   # 工会 -> 2魔力
                4: 2,   # 学校 -> 2魔力
                6: 2,   # 塔楼 -> 2魔力
                3: 3,   # 宫殿 -> 3魔力
                5: 3,   # 大学 -> 3魔力
                7: 4    # 山脉 -> 4魔力
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
            
            # 建筑网格 (二维数组)
            self.building_grid = [[0]*13 for _ in range(9)]  # 每个元素是建筑类型ID
    
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
        self.num_players = num_players                                                    # 玩家数量
        self.setup = __class__.GameSetup(num_players)                                     # 游戏初始状态设置
        self.players = [__class__.PlayerState(i) for i in range(num_players)]             # 玩家状态
        self.map_board_state = __class__.MapBoardState()                                  # 地图状态
        self.display_board_state = __class__.DisplayBoardState(num_players)               # 展示板状态
        self.init_player_order = random.sample(list(range(num_players)),num_players)      # 初始玩家顺位
        self.current_player_order = self.init_player_order.copy()                         # 当前玩家顺位
        self.pass_order = list(reversed(self.current_player_order))                       # 本回合玩家结束顺序
        self.round = 0                                                                    # 当前回合 (0表示设置阶段)
        self.all_players_immediate_action_list: list[tuple[int,tuple]] = []               # 立即行动列表  
        self.all_players_setup_action_list: list[tuple[int,Callable[[int],None]]] = []    # 初始设置完毕后主要轮次开始前行动列表
        self.effect_object()
    
    def create_setup_action_order(self):

        def setup_build(player_id: int):
            self.adjust(player_id, [('building','setup')])

        setup_build_action_order: list[tuple[int,Callable[[int],None]]] = []

        if (
            any(self.players[idx].faction_id == 8 for idx in range(self.num_players))
            and any(self.players[idx].faction_id == 10 for idx in range(self.num_players))
        ):
            owner_faction_8_id = self.all_available_object_dict['faction'][8].owner_list[0]
            owner_faction_10_id = self.all_available_object_dict['faction'][10].owner_list[0]

            for player_idx in list(reversed(self.init_player_order)) + self.init_player_order:
                if player_idx == owner_faction_8_id:
                    continue
                setup_build_action_order.append((player_idx, setup_build))

            setup_build_action_order.append((owner_faction_10_id, setup_build))
            setup_build_action_order.append((owner_faction_8_id, setup_build))

        elif any(self.players[idx].faction_id == 8 for idx in range(self.num_players)):

            owner_faction_8_id = self.all_available_object_dict['faction'][8].owner_list[0]

            for player_idx in list(reversed(self.init_player_order)) + self.init_player_order:
                if player_idx == owner_faction_8_id:
                    continue
                setup_build_action_order.append((player_idx, setup_build))

            setup_build_action_order.append((owner_faction_8_id, setup_build))

        elif any(self.players[idx].faction_id == 10 for idx in range(self.num_players)):

            owner_faction_10_id = self.all_available_object_dict['faction'][10].owner_list[0]

            for player_idx in list(reversed(self.init_player_order)) + self.init_player_order:
                setup_build_action_order.append((player_idx, setup_build))

            setup_build_action_order.append((owner_faction_10_id, setup_build))

        self.all_players_setup_action_list= setup_build_action_order + self.all_players_setup_action_list

    def check(self, player_id: int, list_to_be_checked: list) -> bool:

        def check_money(player_id, num) -> bool:
            if self.players[player_id].resources['money'] >= num:
                return True
            else:
                return False
        
        def check_ore(player_id, num) -> bool:
            if self.players[player_id].resources['ore'] >= num:
                return True
            else:
                return False
        
        def check_book(player_id, where, typ, num) -> bool:
            
            match where, typ:
                case 'self', 'any':
                    if sum([self.players[player_id].resources[f'{x}_book'] for x in ['bank','law','engineering','medical']]) >= num:
                        return True
                case 'self':
                    if self.players[player_id].resources[f'{typ}_book'] >= num:
                        return True
                case 'all', 'any':
                    if sum([self.setup.current_global_books[f'{x}_book'] for x in ['bank','law','engineering','medical']]) >= num:
                        return True
                case 'all':
                    if self.setup.current_global_books[f'{typ}_book'] >= num:
                        return True
                case _:
                    raise ValueError(f'不存在【{where}】处的书')
                
            return False              
        
        def check_meeple(player_id, where, num) -> bool:

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
         
        def check_bridge(player_id, where, num) -> bool: # TODO 检查桥
            return True
        
        def check_building(*arg) -> bool: # TODO 检查建筑
            return True
        
        def check_magics(player_id, zone, num) -> bool:
            if self.players[player_id].magics[zone] >= num:
                return True
            else:
                return False
        
        def check_score(player_id, which, num) -> bool:
            match which:
                case 'board':
                    if self.players[player_id].boardscore >= num:
                        return True
                case 'track':
                    if self.players[player_id].trackscore >= num:
                        return True
                case 'chain':
                    if self.players[player_id].chainscore >= num:
                        return True
                case 'resource':
                    if self.players[player_id].resourcescore >= num:
                        return True
                case _:
                    raise ValueError(f'不存在【{which}】板块分数')
            return False
        
        def check_improve_navigation_level(player_id) -> bool:
            if (
                check_meeple(player_id, 'self', 1)
                and check_money(player_id, 4)
                and self.players[player_id].navigation_level < 3
            ):
                return True
            return False
        
        def check_improve_shovel_level(player_id) -> bool:
            if (
                check_meeple(player_id, 'self', 1)
                and check_ore(player_id, 1)
                and (
                    check_money(player_id, 5) 
                    or (
                        self.players[player_id].planning_card_id == 1 
                        and check_money(player_id, 1)
                    )
                )
                and self.players[player_id].shovel_level > 1
            ):
                return True
            return False
        
        def check_build_and_shovel(play_id, typ) -> bool:
            return True
        
        self.all_check_list = {
            'money': check_money,
            'ore': check_ore,
            'book': check_book,
            'meeple': check_meeple,
            'bridge': check_bridge,
            'building': check_building,
            'magics': check_magics,
            'score':check_score,
            'navigation': check_improve_navigation_level,
            'shovel': check_improve_shovel_level,
            'building': check_build_and_shovel
        }
        
        for check_item, *check_args in list_to_be_checked:
            if check_item not in self.all_check_list:
                raise ValueError(f'非法状态检查对象：{check_item}')
            else:
                if self.all_check_list[check_item](player_id,*check_args) == False:
                    return False
        return True

    def adjust(self, player_id: int, list_to_be_adjusted):

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
                    self.all_players_immediate_action_list.append((player_id, ('select_books', 'get', num)))
                case 'get':
                    act_num = min(self.setup.current_global_books[f'{typ}_book'], num)
                    self.setup.current_global_books[f'{typ}_book'] -= act_num
                    self.players[player_id].resources[f'{typ}_book'] += act_num
                case 'use', 'any':
                    self.all_players_immediate_action_list.append((player_id, ('select_books', 'use', num)))
                case 'use':
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
         
        def adjust_bridge(player_id: int, mode: str, where: str, num: int): # TODO 调整桥
            return []
        
        def adjust_building(*arg) -> list: # TODO 调整建筑
            return []

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
                self.all_players_immediate_action_list.append((player_id, ('select_tracks', 'get', num)))
        
        def improve_navigation_level(player_id: int):

            self.players[player_id].navigation_level += 1

            if self.players[player_id].planning_card_id == 3:
                match self.players[player_id].navigation_level:
                    case 1:
                        return []
                    case 2:
                        adjust_score(player_id, 'get', 'board', 3)
                    case 3:
                        adjust_book(player_id, 'get', 'any', 2)
            else:
                match self.players[player_id].navigation_level:
                    case 1:
                        adjust_score(player_id, 'get', 'board', 2)
                    case 2:
                        adjust_book(player_id, 'get', 'any', 2)
                    case 3:
                        adjust_score(player_id, 'get', 'board', 4)

            adjust_meeple(player_id, 'use', 1)
            adjust_money(player_id, 'use', 4)

        def improve_shovel_level(player_id: int):

            adjust_meeple(player_id, 'use', 1)
            adjust_ore(player_id, 'use', 1)
            adjust_money(player_id, 'use', 5 if self.players[player_id].planning_card_id != 1 else 1)
            self.players[player_id].shovel_level -= 1

            match self.players[player_id].shovel_level:
                case 2:
                    adjust_book(player_id, 'get', 'any', 2)
                case 1:
                    adjust_score(player_id, 'get', 'board', 6)
        
        def shovel(player_id: int):
            pass

        def build_and_upgrade(player_id: int, mode: str, args=1):
            match mode:
                case 'setup':
                    if self.players[player_id].faction_id == 8:
                        pass
                    elif self.players[player_id].faction_id == 10:
                        pass
                    else:
                        pass
            pass
        
        self.all_adjust_list = {
            'money': adjust_money,
            'ore': adjust_ore,
            'book': adjust_book,
            'meeple': adjust_meeple,
            'bridge': adjust_bridge,
            'building': adjust_building,
            'score': adjust_score,
            'magics': magic_rotation,
            'tracks': climb_track,
            'navigation': improve_navigation_level,
            'shovel': improve_shovel_level,
            'land': shovel,
            'building': build_and_upgrade
        }

        for adjust_item, *adjust_args in list_to_be_adjusted:
            if adjust_item not in self.all_adjust_list:
                raise ValueError(f'非法状态调整对象：{adjust_item}')
            else:
                self.all_adjust_list[adjust_item](player_id, *adjust_args)
 
    def effect_object(self): # TODO 效果板块

        def actual_object_store(typ, id):
            """实际对象仓库"""

            out_ref = self
            
            class EffectObject:
                """效果对象抽象基类"""
                max_owner = 1
                
                # 子类初始化时调用
                def __init_subclass__(cls, **kwargs):
                    super().__init_subclass__(**kwargs)
                    # 为子类创建独立属性
                    cls.owner_list = []
                    cls.imme_effect = []
                    cls.inco_effect = []
                    cls.stp_action = []
                
                # 检查是否可获取
                def check_get(self, player_id: int) -> bool:
                    if player_id in self.owner_list or len(self.owner_list) >= self.max_owner:
                        return False
                    if not out_ref.check(player_id, self.cost_check()):
                        return False
                    return True

                # 获取代价检查
                def cost_check(self) -> list:
                    return [] 
                
                # 立即执行方法
                def immediate_effect(self, executed_player_id):
                    out_ref.adjust(executed_player_id, self.imme_effect)
                # 初始设置行动方法
                def setup_action(self, executed_player_id):
                    out_ref.adjust(executed_player_id, self.stp_action)
                # 回合收入方法
                def income_effect(self, executed_player_id):
                    out_ref.adjust(executed_player_id, self.inco_effect)
                # 回合结束方法
                def round_end_effect(self, executed_player_id):
                    pass
                # 略过回合方法
                def pass_effect(self, executed_player_id):
                    pass
                
                # 获取效果触发器
                def get(self, got_player_id):
                    self.owner_list.append(got_player_id)
                    self.immediate_effect(got_player_id)
                    out_ref.players[got_player_id].income_effect_list.append(self.income_effect)
                    out_ref.players[got_player_id].pass_effect_list.append(self.pass_effect)
                    out_ref.all_players_setup_action_list.append((got_player_id,self.setup_action))
                    
                        
            class PlanningCard(EffectObject):
                max_owner = 1
                def immediate_effect(self, executed_player_id):
                    '''回合收入效果: 规划卡 (即个人板面) 建筑收入'''
                    buildings = out_ref.players[executed_player_id].buildings
                    self.inco_effect.extend([
                        ('ore', 'get', 10-buildings[1] if buildings[1]>=5 else 9-buildings[1]),
                        ('money', 'get', 2*(4-buildings[2])),
                        ('magics', 'get', 4-buildings[2] if buildings[2]>=2 else 2*(4-buildings[2])-2), 
                        ('meeple', 'get', 3-buildings[4] + 1-buildings[5]) 
                    ])
                    super().immediate_effect(executed_player_id)

                pass
            
            class Faction(EffectObject):
                max_owner = 1
                pass

            class PalaceTile(EffectObject):
                max_owner = 1
                pass

            class RoundBooster(EffectObject):
                max_owner = 1
                pass

            class AbilityTile(EffectObject):
                max_owner = 4
                pass

            class ScienceTile(EffectObject):
                max_owner = 1
                pass

            class RoundScoring(EffectObject):

                max_owner = out_ref.num_players

                def __init_subclass__(cls, **kwargs):
                    super().__init_subclass__(**kwargs)
                    cls.owner_list = list(range(out_ref.num_players))
                
            class FinalScoring(EffectObject):

                max_owner = out_ref.num_players

                def __init_subclass__(cls, **kwargs):
                    super().__init_subclass__(**kwargs)
                    cls.owner_list = list(range(out_ref.num_players))
                    
            class BookAction(EffectObject):
                max_owner = 1
                pass

            class PlainPlanningCard(PlanningCard):
                
                # 行动效果：减少升级铲子花费
                # 写在check_improve_shovel_level_action过程中了

                pass

            class SwampPlanningCard(PlanningCard):
                
                def immediate_effect(self, executed_player_id):
                    '''立即效果: 获取1米宝+2魔力'''
                    self.imme_effect.extend([
                        ('meeple','get',1), 
                        ('magics','get',2), 
                    ])
                    super().immediate_effect(executed_player_id)

            class LakePlanningCard(PlanningCard):

                def immediate_effect(self, executed_player_id):
                    '''立即效果: 免费提升1航行'''
                    self.imme_effect.extend([
                        ('navigation',)
                    ])
                    super().immediate_effect(executed_player_id)
                
            class ForestPlanningCard(PlanningCard):

                def immediate_effect(self, executed_player_id):              
                    '''立即效果: 获取1魔力+各轨道推1格'''
                    self.imme_effect.extend([              
                        ('magics','get',1), 
                        ('tracks','bank',1), 
                        ('tracks','law',1), 
                        ('tracks','engineering',1),
                        ('tracks','medical',1)
                    ])
                    super().immediate_effect(executed_player_id)
                
            class MountainPlanningCard(PlanningCard):
                
                def income_effect(self, executed_player_id):
                    '''收入阶段: 收入额外2块+第一个工会多收入1块'''
                    self.inco_effect.extend([
                        ('money', 'get', 2),
                        ('money', 'get', min(1, 4-out_ref.players[self.owner_list[0]].buildings[2]))
                    ])
                    super().income_effect(executed_player_id)
                    
                
            class WastelandPlanningCard(PlanningCard):

                def setup_action(self, executed_player_id):
                    '''初始设置阶段: 获取任意1书'''
                    self.stp_action.extend([ 
                        ('book','get','any',1), 
                    ])
                    super().setup_action(executed_player_id)

                def immediate_effect(self, executed_player_id):
                    '''立即效果: 获取1矿'''
                    self.imme_effect.extend([
                        ('ore','get',1)
                    ])
                    super().immediate_effect(executed_player_id)

                    # TODO 第二项发明少付1书

            class DesertPlanningCard(PlanningCard):

                def setup_action(self, executed_player_id):
                    '''初始设置阶段: 在游戏开始后（初始房子都摆好之后）立即一铲不可建房'''
                    self.stp_action.extend([
                        ('land',)
                    ])
                    super().setup_action(executed_player_id)
            
            class BlessedFaction(Faction):
                pass

            class FelinesFaction(Faction):
                pass

            class GoblinsFaction(Faction):
                pass

            class IllusionistsFaction(Faction):
                pass

            class InventorsFaction(Faction):
                pass

            class LizardsFaction(Faction):
                pass

            class MolesFaction(Faction):
                pass

            class MonksFaction(Faction):
                pass

            class NavigatorsFaction(Faction):
                pass

            class OmarFaction(Faction):
                pass

            class PhilosophersFaction(Faction):
                pass

            class PsychicsFaction(Faction):
                pass

            class PalaceTile1(PalaceTile):
                pass

            class PalaceTile2(PalaceTile):
                pass

            class PalaceTile3(PalaceTile):
                pass

            class PalaceTile4(PalaceTile):
                pass

            class PalaceTile5(PalaceTile):
                pass

            class PalaceTile6(PalaceTile):
                pass

            class PalaceTile7(PalaceTile):
                pass

            class PalaceTile8(PalaceTile):
                pass

            class PalaceTile9(PalaceTile):
                pass        

            class PalaceTile10(PalaceTile):
                pass

            class PalaceTile11(PalaceTile):
                pass

            class PalaceTile12(PalaceTile):
                pass

            class PalaceTile13(PalaceTile):
                pass

            class PalaceTile14(PalaceTile):
                pass

            class PalaceTile15(PalaceTile):
                pass

            class PalaceTile16(PalaceTile):
                pass

            class RoundBooster1(RoundBooster):
                pass

            class RoundBooster2(RoundBooster):
                pass

            class RoundBooster3(RoundBooster):
                pass

            class RoundBooster4(RoundBooster):
                pass

            class RoundBooster5(RoundBooster):
                pass

            class RoundBooster6(RoundBooster):
                pass

            class RoundBooster7(RoundBooster):
                pass

            class RoundBooster8(RoundBooster):
                pass

            class RoundBooster9(RoundBooster):
                pass

            class RoundBooster10(RoundBooster):
                pass
            
            class AbilityTile1(AbilityTile):
                pass

            class AbilityTile2(AbilityTile):
                pass

            class AbilityTile3(AbilityTile):
                pass
            
            class AbilityTile4(AbilityTile):
                pass

            class AbilityTile5(AbilityTile):
                pass

            class AbilityTile6(AbilityTile):
                pass

            class AbilityTile7(AbilityTile):
                pass

            class AbilityTile8(AbilityTile):
                pass

            class AbilityTile9(AbilityTile):
                pass

            class AbilityTile10(AbilityTile):
                pass

            class AbilityTile11(AbilityTile):
                pass

            class AbilityTile12(AbilityTile):
                pass

            class ScienceTile1(ScienceTile):
                pass
            
            class ScienceTile2(ScienceTile):
                pass

            class ScienceTile3(ScienceTile):
                pass

            class ScienceTile4(ScienceTile):
                pass

            class ScienceTile5(ScienceTile):
                pass

            class ScienceTile6(ScienceTile):
                pass

            class ScienceTile7(ScienceTile):
                pass

            class ScienceTile8(ScienceTile):
                pass

            class ScienceTile9(ScienceTile):
                pass

            class ScienceTile10(ScienceTile):
                pass

            class ScienceTile11(ScienceTile):
                pass

            class ScienceTile12(ScienceTile):
                pass

            class ScienceTile13(ScienceTile):
                pass

            class ScienceTile14(ScienceTile):
                pass

            class ScienceTile15(ScienceTile):
                pass
            
            class ScienceTile16(ScienceTile):
                pass

            class ScienceTile17(ScienceTile):
                pass

            class ScienceTile18(ScienceTile):
                pass

            class RoundScoring1(RoundScoring):
                pass
            
            class RoundScoring2(RoundScoring):
                pass

            class RoundScoring3(RoundScoring):
                pass

            class RoundScoring4(RoundScoring):
                pass

            class RoundScoring5(RoundScoring):
                pass

            class RoundScoring6(RoundScoring):
                pass

            class RoundScoring7(RoundScoring):
                pass

            class RoundScoring8(RoundScoring):
                pass

            class RoundScoring9(RoundScoring):
                pass

            class RoundScoring10(RoundScoring):
                pass

            class RoundScoring11(RoundScoring):
                pass

            class RoundScoring12(RoundScoring):
                pass

            class FinalScoring1(FinalScoring):
                pass
            
            class FinalScoring2(FinalScoring):
                pass

            class FinalScoring3(FinalScoring):
                pass

            class FinalScoring4(FinalScoring):
                pass

            class BookAction1(BookAction):
                pass
            
            class BookAction2(BookAction):
                pass

            class BookAction3(BookAction):
                pass

            class BookAction4(BookAction):
                pass

            class BookAction5(BookAction):
                pass

            class BookAction6(BookAction):
                pass

            all_object_dict = {
                'planning_card': {
                    1: PlainPlanningCard,
                    2: SwampPlanningCard,
                    3: LakePlanningCard,
                    4: ForestPlanningCard,
                    5: MountainPlanningCard,
                    6: WastelandPlanningCard,
                    7: DesertPlanningCard
                },
                'faction': {
                    1: BlessedFaction,
                    2: FelinesFaction,
                    3: GoblinsFaction,
                    4: IllusionistsFaction,
                    5: InventorsFaction,
                    6: LizardsFaction,
                    7: MolesFaction,
                    8: MonksFaction,
                    9: NavigatorsFaction,
                    10: OmarFaction,
                    11: PhilosophersFaction,
                    12: PsychicsFaction
                },
                'palace_tile': {
                    1: PalaceTile1,
                    2: PalaceTile2,
                    3: PalaceTile3,
                    4: PalaceTile4,
                    5: PalaceTile5,
                    6: PalaceTile6,
                    7: PalaceTile7,
                    8: PalaceTile8,
                    9: PalaceTile9,
                    10: PalaceTile10,
                    11: PalaceTile11,
                    12: PalaceTile12,
                    13: PalaceTile13,
                    14: PalaceTile14,
                    15: PalaceTile15,
                    16: PalaceTile16
                },
                'round_booster': {
                    1: RoundBooster1,
                    2: RoundBooster2,
                    3: RoundBooster3,
                    4: RoundBooster4,
                    5: RoundBooster5,
                    6: RoundBooster6,
                    7: RoundBooster7,
                    8: RoundBooster8,
                    9: RoundBooster9,
                    10: RoundBooster10,
                },
                'ability_tile': {
                    1: AbilityTile1,
                    2: AbilityTile2,
                    3: AbilityTile3,
                    4: AbilityTile4,
                    5: AbilityTile5,
                    6: AbilityTile6,
                    7: AbilityTile7,
                    8: AbilityTile8,
                    9: AbilityTile9,
                    10: AbilityTile10,
                    11: AbilityTile11,
                    12: AbilityTile12
                },
                'science_tile': {
                    1: ScienceTile1,
                    2: ScienceTile2,
                    3: ScienceTile3,
                    4: ScienceTile4,
                    5: ScienceTile5,
                    6: ScienceTile6,
                    7: ScienceTile7,
                    8: ScienceTile8,
                    9: ScienceTile9,
                    10: ScienceTile10,
                    11: ScienceTile11,
                    12: ScienceTile12,
                    13: ScienceTile13,
                    14: ScienceTile14,
                    15: ScienceTile15,
                    16: ScienceTile16,
                    17: ScienceTile17,
                    18: ScienceTile18,
                },
                'round_scoring': {
                    1: RoundScoring1,
                    2: RoundScoring2,
                    3: RoundScoring3,
                    4: RoundScoring4,
                    5: RoundScoring5,
                    6: RoundScoring6,
                    7: RoundScoring7,
                    8: RoundScoring8,
                    9: RoundScoring9,
                    10: RoundScoring10,
                    11: RoundScoring11,
                    12: RoundScoring12
                },
                'final_scoring': {
                    1: FinalScoring1,
                    2: FinalScoring2,
                    3: FinalScoring3,
                    4: FinalScoring4,
                },
                'book_action': {
                    1: BookAction1,
                    2: BookAction2,
                    3: BookAction3,
                    4: BookAction4,
                    5: BookAction5,
                    6: BookAction6,
                }
            }

            return all_object_dict[typ][id]()
        
        # 本局所有需实例化效果板块对象字典
        self.all_available_object_dict: dict[str, dict[int, type]] = {}

        all_typ_dict = {
            'planning_card': self.setup.selected_planning_cards,
            'faction': self.setup.selected_factions,
            'palace_tile': self.setup.selected_palace_tiles,
            'round_booster': self.setup.selected_round_boosters,
            'ability_tile': self.setup.ability_tiles_order,
            'science_tile': self.setup.science_tiles_order,
            'round_scoring': self.setup.round_scoring_order,
            'final_scoring': [self.setup.final_scoring],
            'book_action': self.setup.selected_book_actions
        }

        for typ_name, typ_available_id_list in all_typ_dict.items():

            self.all_available_object_dict[typ_name] = {
                id : actual_object_store(typ_name, id) 
                for id in typ_available_id_list
            }