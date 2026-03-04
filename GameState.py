import random
import time
from typing import Callable
from web_io import GamePanel, Silence_IO
from collections import defaultdict, deque
from DetailedAction import DetailedAction

class GameStateBase:
    """游戏状态类"""
    class GameSetup:
        """游戏初始设置类"""
        def __init__(self, num_players: int, mode: tuple, io: GamePanel|Silence_IO):
            self.num_players = num_players
            self.mode = mode
            self.seedid = 7
            self.io = io
            
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
            
            # 执行随机初始设置
            match mode[0]:
                case 'random':
                    self.perform_random_initial_setup()
                case 'target':
                    self.perform_target_initial_setup(mode[1])
                case 'input':
                    self.perform_input_initial_setup()
                case _:
                    raise ValueError('Invalid mode')
        
        def perform_random_initial_setup(self):
            """执行随机初始设置步骤"""
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
            self.io.set_bonus_columns(self.selected_round_boosters)
            
            # 5. 选取6个轮次计分板块并随机排序
            self.round_scoring_order = random.sample(self.all_round_scoring, 6)
            while not self.round_scoring_order_is_legal(self.round_scoring_order):
                self.round_scoring_order = random.sample(self.all_round_scoring, 6)
                random.shuffle(self.round_scoring_order)
            for i in range(6):
                self.io.set_round_scoring(i+1,self.round_scoring_order[i])

            # 6. 随机选取1个最终计分板块
            self.final_scoring = random.choice(self.all_final_scoring)
            self.io.set_final_round_bonus(self.final_scoring)

            # 7. 对共12块能力板块随机排序
            self.ability_tiles_order = random.sample(self.all_ability_tiles, 12)
            random.shuffle(self.ability_tiles_order)
            
            # 8. 选取2+人数*2的科学板块并随机排序
            self.science_tiles_order = random.sample(self.all_science_tiles, self.num_players * 2 + 2)
            random.shuffle(self.science_tiles_order)
            
            # 9. 选取3个书本行动
            self.selected_book_actions = sorted(random.sample(self.all_book_actions, 3))            
      
        def perform_target_initial_setup(self, args):
            """执行指定初始设置步骤"""
            def validate_setup_args(args, num_players):
                """
                验证通过args元组传入的设置参数是否合法
                
                Args:
                    args: 包含9个元素的元组，对应9个设置步骤
                    num_players: 玩家数量
                
                Returns:
                    bool: 参数是否合法
                    str: 错误信息（如果合法则为空字符串）
                """
                
                # 检查args是否为9个元素的元组
                if not isinstance(args, tuple) or len(args) != 9:
                    return False, "参数必须是一个包含9个元素的元组"
                
                try:
                    # 1. 检查被排除的规划卡
                    excluded_planning_card = args[0]
                    if not isinstance(excluded_planning_card, int) or excluded_planning_card < 1 or excluded_planning_card > 7:
                        return False, "被排除的规划卡必须是1-7之间的整数"
                    
                    # 2. 检查派系板块
                    selected_factions = args[1]
                    if (not isinstance(selected_factions, (list, tuple)) or 
                        len(set(selected_factions)) != num_players + 1 or 
                        min(selected_factions) < 1 or max(selected_factions) > 12):
                        return False, f"派系板块必须是包含{num_players+1}个不重复的1-12之间整数的列表"
                    
                    # 3. 检查宫殿板块
                    selected_palace_tiles = args[2]
                    if (not isinstance(selected_palace_tiles, (list, tuple)) or 
                        len(set(selected_palace_tiles)) != num_players + 1 or 
                        min(selected_palace_tiles) < 1 or max(selected_palace_tiles) > 16):
                        return False, f"宫殿板块必须是包含{num_players+1}个不重复的1-16之间整数的列表"
                    
                    # 4. 检查回合助推板
                    selected_round_boosters = args[3]
                    if (not isinstance(selected_round_boosters, (list, tuple)) or 
                        len(set(selected_round_boosters)) != num_players + 3 or 
                        min(selected_round_boosters) < 1 or max(selected_round_boosters) > 10):
                        return False, f"回合助推板必须是包含{num_players+3}个不重复的1-10之间整数的列表"
                    
                    # 5. 检查轮次计分板块
                    round_scoring_order = args[4]
                    if (not isinstance(round_scoring_order, (list, tuple)) or 
                        len(set(round_scoring_order)) != 6 or 
                        min(round_scoring_order) < 1 or max(round_scoring_order) > 12):
                        return False, "轮次计分板块必须是包含6个不重复的1-12之间整数的列表"
                    
                    if self.round_scoring_order_is_legal(round_scoring_order) == False:
                        return False, "轮次计分板不符合同学科前五回合内不能出现三次的限制性规定或8号板位于第五第六回合"
                    
                    # 6. 检查最终计分板块
                    final_scoring = args[5]
                    if not isinstance(final_scoring, int) or final_scoring < 1 or final_scoring > 4:
                        return False, "最终计分板块必须是1-4之间的整数"
                    
                    # 7. 检查能力板块顺序
                    ability_tiles_order = args[6]
                    if (not isinstance(ability_tiles_order, (list, tuple)) or 
                        len(set(ability_tiles_order)) != 12 or 
                        min(ability_tiles_order) < 1 or max(ability_tiles_order) > 12):
                        return False, "能力板块顺序必须是包含12个不重复的1-12之间整数的列表"
                    
                    # 8. 检查科学板块
                    science_count = 2 + num_players * 2
                    science_tiles_order = args[7]
                    if (not isinstance(science_tiles_order, (list, tuple)) or 
                        len(set(science_tiles_order)) != science_count or 
                        min(science_tiles_order) < 1 or max(science_tiles_order) > 18):
                        return False, f"科学板块必须是包含{science_count}个不重复的1-18之间整数的列表"
                    
                    # 9. 检查书本行动板块
                    selected_book_actions = args[8]
                    if (not isinstance(selected_book_actions, (list, tuple)) or 
                        len(set(selected_book_actions)) != 3 or 
                        min(selected_book_actions) < 1 or max(selected_book_actions) > 6):
                        return False, "书本行动板块必须是包含3个不重复的1-6之间整数的列表"
                    
                    return True, ""
                    
                except (IndexError, TypeError, ValueError) as e:
                    return False, f"参数格式错误: {str(e)}"
            
            res = validate_setup_args(args, self.num_players)
            if not res[0]:
                print(res[1])
                return
            
            # 1. 选择被排除的那张规划卡
            self.selected_planning_cards = self.all_planning_cards.copy()
            self.selected_planning_cards.remove(args[0])

            # 2. 选择人数+1的派系板块
            self.selected_factions = args[1]
            
            # 3. 选取人数+1个宫殿板块作为可选项
            self.selected_palace_tiles = args[2]
            
            # 4. 选取人数+3个回合助推板作为可选项
            self.selected_round_boosters = args[3]
            self.io.set_bonus_columns(self.selected_round_boosters)
            
            # 5. 选取6个轮次计分板块并随机排序
            self.round_scoring_order = args[4]
            for i in range(6):
                self.io.set_round_scoring(i+1,self.round_scoring_order[i])

            # 6. 随机选取1个最终计分板块
            self.final_scoring = args[5]
            self.io.set_final_round_bonus(self.final_scoring)

            # 7. 对共12块能力板块随机排序
            self.ability_tiles_order = args[6]
            
            # 8. 选取2+人数*2的科学板块并随机排序
            self.science_tiles_order = args[7]
            
            # 9. 选取3个书本行动
            self.selected_book_actions = args[8]

        def perform_input_initial_setup(self):
            """执行所有初始设置步骤"""

            # 1. 选择被排除的那张规划卡
            excluded_planning_card = int(self.io.get_input("请输入要排除的规划卡编号(1-7):"))
            if excluded_planning_card not in self.all_planning_cards:
                raise ValueError("无效的规划卡编号")
            self.selected_planning_cards = self.all_planning_cards.copy()
            self.selected_planning_cards.remove(excluded_planning_card)

            # 2. 选择人数+1的派系板块
            faction_input = self.io.get_input(f"请输入{self.num_players+1}个派系板块编号(1-12)，用空格分割:")
            inp = list(map(int, faction_input.split()))
            if len(set(inp)) != self.num_players + 1 or min(inp) < 1 or max(inp) > 12:
                raise ValueError('无效的派系板块')
            self.selected_factions = sorted(inp)

            # 3. 选取人数+1个宫殿板块作为可选项
            palace_input = self.io.get_input(f"请输入{self.num_players+1}个宫殿板块编号(1-16)，用空格分割:")
            inp = list(map(int, palace_input.split()))
            if len(set(inp)) != self.num_players + 1 or min(inp) < 1 or max(inp) > 16:
                raise ValueError('无效的宫殿板块')
            self.selected_palace_tiles = sorted(inp)

            # 4. 选取人数+3个回合助推板作为可选项
            booster_input = self.io.get_input(f"请输入{self.num_players+3}个回合助推板编号(1-10)，用空格分割:")
            inp = list(map(int, booster_input.split()))
            if len(set(inp)) != self.num_players + 3 or min(inp) < 1 or max(inp) > 10:
                raise ValueError('无效的回合助推板')
            self.selected_round_boosters = sorted(inp)
            self.io.set_bonus_columns(self.selected_round_boosters)

            # 5. 按第1-6轮顺序输入6个轮次计分板块
            scoring_input = self.io.get_input("请按顺序输入6个轮次计分板块编号(1-12)，用空格分割:")
            inp = list(map(int, scoring_input.split()))
            if len(set(inp)) != 6 or min(inp) < 1 or max(inp) > 12 or self.round_scoring_order_is_legal(inp):
                raise ValueError('无效的轮次计分板块')
            self.round_scoring_order = inp
            for i in range(6):
                self.io.set_round_scoring(i+1,self.round_scoring_order[i])

            # 6. 随机选取1个最终计分板块
            final_input = self.io.get_input("请输入1个最终计分板块编号(1-4):")
            inp = int(final_input)
            if inp not in self.all_final_scoring:
                raise ValueError('无效的最终计分板块')
            self.final_scoring = inp
            self.io.set_final_round_bonus(self.final_scoring)

            # 7. 对共12块能力板块随机排序
            ability_input = self.io.get_input("请按顺序输入12个能力板块编号(1-12)，用空格分割:")
            inp = list(map(int, ability_input.split()))
            if len(set(inp)) != 12 or min(inp) < 1 or max(inp) > 12:
                raise ValueError('无效的能力板块')
            self.ability_tiles_order = inp

            # 8. 选取2+人数*2的科学板块并随机排序
            science_count = 2 + self.num_players * 2
            science_input = self.io.get_input(f"请按顺序输入{science_count}个科学板块编号(1-18)，用空格分割:")
            inp = list(map(int, science_input.split()))
            if len(set(inp)) != science_count or min(inp) < 1 or max(inp) > 18:
                raise ValueError('无效的科学板块')
            self.science_tiles_order = inp

            # 9. 选取3个书本行动
            book_input = self.io.get_input("请输入3个书本行动板块编号(1-6)，用空格分割:")
            inp = list(map(int, book_input.split()))
            if len(set(inp)) != 3 or min(inp) < 1 or max(inp) > 6:
                raise ValueError('无效的书本行动板块')
            self.selected_book_actions = sorted(inp)  

        def round_scoring_order_is_legal(self, round_scoring_order) -> bool:
            """返回轮次计分顺序是否合法"""
            if 8 in round_scoring_order and round_scoring_order.index(8) >= 4:  # 8号轮次计分板块不能位于第5和第6轮次
                return False
            # 检查任意同轨道三板块不能在前五轮中同时出现
            if any(all(i in round_scoring_order[:5] for i in same_track_tile_ids) for same_track_tile_ids in [[2,5,7],[1,3,12],[8,10,11],[4,6,9]]):
                return False
            return True

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
            self.ability_tile_ids = []    # 获取的能力板块ID
            self.science_tile_ids = []    # 获取的科学板块ID
            
            # 资源系统
            self.resources = {
                'money': 0,            # 钱
                'ore': 0,               # 矿
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
            self.citys_amount = 0          # 当前城市数量（城片数量）
            self.tracks_over_7_amount = 0  # 当前科技轨超过7数量
                    
            self.boardscore = 20    # 当前板面分数
            self.trackscore = 0     # 当前科技轨分数
            self.chainscore = 0     # 当前大链分数
            self.resourcescore = 0  # 当前资源分数

            self.main_action_is_done = False # 主要行动是否完成
            self.ispass = False              # 是否已跳过
            self.choice_position = tuple()   # 玩家选择地图坐标记录
            self.choice_track = ''           # 玩家选择轨道类型记录

            self.income_effect_list: list[Callable[[int],None]] = []        # 收入阶段效果列表 
            self.pass_effect_list: list[Callable[[int],None]] = []          # 略过动作效果列表
            self.setup_effect_list: list[Callable[[int],None]] = []         # 初始设置效果列表
            self.additional_actions_dict: dict[str,Callable] = {}           # 额外行动列表

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
                f"聚落与城市: {self.settlements_and_cities}"
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
                f"城市（城片）数量: {self.citys_amount}",
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
                1: "平原（棕）",
                2: "沼泽（黑）",
                3: "湖泊（蓝）",
                4: "森林（绿）",
                5: "山脉（灰）",
                6: "荒地（红）",
                7: "沙漠（黄）",
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

        def find_settlement_root(self, settlements_and_cities, pos: tuple[int,int]):
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
        
        def merge_settlement_root(self, settlements_and_cities, pos_a: tuple[int,int], pos_b: tuple[int,int]):
            root_a, is_city_a = self.find_settlement_root(settlements_and_cities, pos_a)
            root_b, is_city_b = self.find_settlement_root(settlements_and_cities, pos_b)

            if root_a == root_b:
                return root_a, is_city_a  # 已经在同一聚落

            # 新聚落的城市状态
            new_is_city = is_city_a or is_city_b
            # 更新a的父节点信息，以b为新父节点
            settlements_and_cities[root_a] = [root_b, new_is_city]
            # 更新父节点b的城市状态
            settlements_and_cities[root_b] = [root_b, new_is_city]

            return root_b, new_is_city
        
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

    def __init__(self, game_args: dict, num_players: int = 3):
        if num_players:
            self.num_players = num_players                                                                          # 玩家数量
            self.game_args = game_args                                                                              # 本局游戏参数
            self.io: GamePanel|Silence_IO = game_args['web_io']                                                     # 网页IO接口     
            self.setup = __class__.GameSetup(num_players, (game_args['setup_mode'],game_args['setup_tile_args']), self.io)   # 游戏初始状态设置
            self.players:list[__class__.PlayerState] = [__class__.PlayerState(i) for i in range(num_players)]       # 玩家状态
            self.map_board_state = __class__.MapBoardState()                                                        # 地图状态
            self.display_board_state = __class__.DisplayBoardState(num_players)                                     # 展示板状态
            self.round = 0                                                                                          # 当前回合 (0表示设置阶段)
            match game_args['setup_mode']:                                                                          # 初始玩家顺位
                case 'random':
                    self.init_player_order = random.sample(list(range(num_players)),num_players)
                case 'input':
                    self.init_player_order = [int(i)-1 for i in self.io.get_input(f"请输入初始玩家顺位（1-{num_players}）: ").split()]
                    assert (
                        len(self.init_player_order) == num_players 
                        and min(self.init_player_order) > 0 
                        and max(self.init_player_order) <= num_players
                    )
                case 'target':
                    self.init_player_order = game_args['setup_player_order_args']
            self.current_player_order = self.init_player_order.copy()                                               # 当前玩家顺位
            self.pass_order = list(reversed(self.current_player_order))                                             # 本回合玩家结束顺序
            self.setup_choice_is_completed = False                                                                  # 初始选择是否完成
            self.check = self.init_check()                                                                          # 初始化检查函数
            self.adjust = self.init_adjust()                                                                        # 初始化调整函数
            self.all_detailed_actions = DetailedAction().all_detailed_actions                                       # 所有具体行动

    def invoke_immediate_aciton(self, player_id: int, args: tuple):
        return
    
    def update_reachable_map_ids_set(self, player_id: int, update_pos: tuple = tuple(), mode: str = 'normal'):
        """更新可抵达的坐标列表"""

        player = self.players[player_id]

        # 移除原可抵达地块坐标集合中已被控制的
        for player_idx in range(self.num_players):
            player.reachable_map_ids -= self.players[player_idx].controlled_map_ids

        if mode == 'exclude_controlled':
            return 

        def update_reachable_map_ids_rely_on_only_one_controlled_pos(pos: tuple[int, int], current_navigation_level: int) -> set:
            cur_pos_reachable_map_ids = set()
            navigation_reachable_map_ids_dict = {
                1:[], # 一航水域
                2:[], # 二航水域
                3:[], # 三航水域
                4:[], # 四航水域
            }
            
            # 先判定直接相邻的地块中的可抵地块
            i,j = pos
            direction = [(-1,i%2-1),(-1,i%2),(0,-1),(0,1),(1,i%2-1),(1,i%2)]
            for dx,dy in direction:
                new_i, new_j = i + dx, j + dy
                if (
                    # 在合法边界内
                    0 <= new_i <= 8 and 0 <= new_j <= 12
                    # 没有被任何玩家控制
                    and self.map_board_state.map_grid[new_i][new_j][1] == -1
                ):
                    # 如果是非水域地块，则直接加入当前地块的可抵地块集合中
                    if self.map_board_state.map_grid[new_i][new_j][0] != 0 :
                        cur_pos_reachable_map_ids.add((new_i,new_j))
                    # 如果该地块是水域，则需根据航行等级进一步判定
                    elif current_navigation_level >= 1:
                        navigation_reachable_map_ids_dict[1].append((new_i,new_j))
            
            # 进一步进行航行判定，检索所有可航抵水域地块
            if current_navigation_level >= 2:
                # 遍历所有可航行距离
                for navigation_distance in range(2,current_navigation_level+1):
                    # 如果无上一航行距离可抵的水域，则意味着所有航行可抵水域均已找到，直接跳出循环
                    if not navigation_reachable_map_ids_dict[navigation_distance-1]:
                        break
                    # 若有，则遍历上一距离可航抵水域的所有直接相邻地块
                    for i,j in navigation_reachable_map_ids_dict[navigation_distance-1]:
                        direction = [(-1,i%2-1),(-1,i%2),(0,-1),(0,1),(1,i%2-1),(1,i%2)]
                        for dx,dy in direction:
                            new_i, new_j = i + dx, j + dy
                            if (
                                # 在合法边界内
                                0 <= new_i <= 8 and 0 <= new_j <= 12
                                # 是水域地块
                                and self.map_board_state.map_grid[new_i][new_j][0] == 0
                                # 并且该地块不属于任何更近距离的可航抵水域
                                and all((new_i,new_j) not in navigation_reachable_map_ids_dict[t] for t in range(navigation_distance-1,0,-1))
                            ):
                                # 则将其加入当前航行距离的可航抵水域
                                navigation_reachable_map_ids_dict[navigation_distance].append((new_i,new_j))

            # 依据可航抵水域，判定可抵地块
            if current_navigation_level >= 1: 
                # 获取所有可航抵水域列表
                all_available_navigation_reachable_water_map_ids = [
                    (i,j) for t in range(1,5) for i,j in navigation_reachable_map_ids_dict[t] 
                ]
                # 则遍历所有可航抵水域的直接相邻地块
                for i,j in all_available_navigation_reachable_water_map_ids:
                    direction = [(-1,i%2-1),(-1,i%2),(0,-1),(0,1),(1,i%2-1),(1,i%2)]
                    for dx,dy in direction:
                        new_i, new_j = i + dx, j + dy
                        if (
                            # 在合法边界内
                            0 <= new_i <= 8 and 0 <= new_j <= 12
                            # 非水域地块
                            and self.map_board_state.map_grid[new_i][new_j][0] != 0
                            # 没有被任何玩家控制
                            and self.map_board_state.map_grid[new_i][new_j][1] == -1
                        ):
                            # 则将其加入当前检测地块的可抵地块集合中
                            cur_pos_reachable_map_ids.add((new_i,new_j))
                
            # 依据相邻桥梁连接，判定可抵地块
            # 判断该地块是否是可建桥位两侧中的一测
            if pos in self.map_board_state.enable_bridge_pos_dict:
                # 如是，则遍历其对侧地块
                for corres_pos in self.map_board_state.enable_bridge_pos_dict[pos]:
                    (i,j),(p,q) = pos, corres_pos
                    # 判断对侧地块是否已被任一玩家占领
                    if self.map_board_state.map_grid[p][q][1] in (-1, player_id):
                        # 若未被任一玩家占领，则排序两侧地块坐标，生成桥键
                        if i > p or (i == p and q > j):
                            bridge_key = ((p,q),(i,j))
                        else:
                            bridge_key = ((i,j),(p,q))
                        # 根据桥键查询该桥位是否已被该玩家连接
                        if self.map_board_state.bridges_is_conneted[bridge_key] == player_id:
                            # 如已被连接，则将对侧地块加入当前检测地块的可抵地块集合中
                            cur_pos_reachable_map_ids.add((p,q))

            return cur_pos_reachable_map_ids
        
        def update_reachable_map_ids_rely_on_all_controlled_pos(current_navigation_level: int) -> set:
            all_reachable_map_ids = set()
            navigation_reachable_map_ids_dict = {
                1:[], # 一航水域
                2:[], # 二航水域
                3:[], # 三航水域
                4:[], # 四航水域
            }
            
            # 先遍历所有控制地块，判定直接相邻的地块中的可抵地块
            for i,j in player.controlled_map_ids:
                direction = [(-1,i%2-1),(-1,i%2),(0,-1),(0,1),(1,i%2-1),(1,i%2)]
                for dx,dy in direction:
                    new_i, new_j = i + dx, j + dy
                    if (
                        # 在合法边界内
                        0 <= new_i <= 8 and 0 <= new_j <= 12
                        # 没有被任何玩家控制
                        and self.map_board_state.map_grid[new_i][new_j][1] == -1
                    ):
                        # 如果是非水域地块，则直接加入当前地块的可抵地块集合中
                        if self.map_board_state.map_grid[new_i][new_j][0] != 0 :
                            all_reachable_map_ids.add((new_i,new_j))
                        # 如果该地块是水域，则需根据航行等级进一步判定
                        elif current_navigation_level >= 1:
                            navigation_reachable_map_ids_dict[1].append((new_i,new_j))
            
            # 进一步进行航行判定，检索所有可航抵水域地块
            if current_navigation_level >= 2:
                # 遍历所有可航行距离
                for navigation_distance in range(2,current_navigation_level+1):
                    # 如果无上一航行距离可抵的水域，则意味着所有航行可抵水域均已找到，直接跳出循环
                    if not navigation_reachable_map_ids_dict[navigation_distance-1]:
                        break
                    # 若有，则遍历上一距离可航抵水域的所有直接相邻地块
                    for i,j in navigation_reachable_map_ids_dict[navigation_distance-1]:
                        direction = [(-1,i%2-1),(-1,i%2),(0,-1),(0,1),(1,i%2-1),(1,i%2)]
                        for dx,dy in direction:
                            new_i, new_j = i + dx, j + dy
                            if (
                                # 在合法边界内
                                0 <= new_i <= 8 and 0 <= new_j <= 12
                                # 是水域地块
                                and self.map_board_state.map_grid[new_i][new_j][0] == 0
                                # 并且该地块不属于任何更近距离的可航抵水域
                                and all((new_i,new_j) not in navigation_reachable_map_ids_dict[t] for t in range(navigation_distance-1,0,-1))
                            ):
                                # 则将其加入当前航行距离的可航抵水域
                                navigation_reachable_map_ids_dict[navigation_distance].append((new_i,new_j))

            # 依据可航抵水域，判定可抵地块
            if current_navigation_level >= 1: 
                # 获取所有可航抵水域列表
                all_available_navigation_reachable_water_map_ids = [
                    (i,j) for t in range(1,5) for i,j in navigation_reachable_map_ids_dict[t] 
                ]
                # 则遍历所有可航抵水域的直接相邻地块
                for i,j in all_available_navigation_reachable_water_map_ids:
                    direction = [(-1,i%2-1),(-1,i%2),(0,-1),(0,1),(1,i%2-1),(1,i%2)]
                    for dx,dy in direction:
                        new_i, new_j = i + dx, j + dy
                        if (
                            # 在合法边界内
                            0 <= new_i <= 8 and 0 <= new_j <= 12
                            # 非水域地块
                            and self.map_board_state.map_grid[new_i][new_j][0] != 0
                            # 没有被任何玩家控制
                            and self.map_board_state.map_grid[new_i][new_j][1] == -1
                        ):
                            # 则将其加入当前检测地块的可抵地块集合中
                            all_reachable_map_ids.add((new_i,new_j))
                
            # 依据相邻桥梁连接，判定可抵地块
            # 判断该地块是否是可建桥位两侧中的一测
            for pos in player.controlled_map_ids:
                if pos in self.map_board_state.enable_bridge_pos_dict:
                    # 如是，则遍历其对侧地块
                    for corres_pos in self.map_board_state.enable_bridge_pos_dict[pos]:
                        (i,j),(p,q) = pos, corres_pos
                        # 判断对侧地块是否已被任一玩家占领
                        if self.map_board_state.map_grid[p][q][1] in (-1, player_id):
                            # 若未被任一玩家占领，则排序两侧地块坐标，生成桥键
                            if i > p or (i == p and q > j):
                                bridge_key = ((p,q),(i,j))
                            else:
                                bridge_key = ((i,j),(p,q))
                            # 根据桥键查询该桥位是否已被该玩家连接
                            if self.map_board_state.bridges_is_conneted[bridge_key] == player_id:
                                # 如已被连接，则将对侧地块加入当前检测地块的可抵地块集合中
                                all_reachable_map_ids.add((p,q))

            return all_reachable_map_ids
        
        # 获取当前玩家最大可航行距离
        current_navigation_level = player.navigation_level + 1 if player.temp_navigation else player.navigation_level

        # 如有指定更新的控制坐标，则以该坐标为原点进行查找
        if update_pos:
            player.reachable_map_ids |= update_reachable_map_ids_rely_on_only_one_controlled_pos(update_pos, current_navigation_level)
        else:
            # 如无，则更新整个可抵地块集合
            player.reachable_map_ids = update_reachable_map_ids_rely_on_all_controlled_pos(current_navigation_level)

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
                    self.players[player_idx].boardscore + 1                                         # 最大可支付版面分数
                )
                if actual_num:
                    if self.invoke_immediate_aciton(player_idx, ('gain_magics', actual_num)): return 

    def city_establishment_check(self, player_id: int, mode: str, pos: tuple[int, int], bridge_key: tuple[tuple[int,int],tuple[int,int]] = tuple()):

        settlements_and_cities = self.players[player_id].settlements_and_cities
        if pos not in settlements_and_cities:
            settlements_and_cities[pos] = [pos, False]

        current_root, current_is_city = self.map_board_state.find_settlement_root(settlements_and_cities, pos)

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
                        current_root, current_is_city = self.map_board_state.merge_settlement_root(settlements_and_cities, pos, temp_pos)
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
                                current_root, current_is_city = self.map_board_state.merge_settlement_root(settlements_and_cities, corres_pos, pos)
                                need_following_check = True
                            
                direction = [(-1,i%2-1),(-1,i%2),(0,-1),(0,1),(1,i%2-1),(1,i%2)]
                # 遍历判断相邻地块
                for dx,dy in direction:
                    new_i, new_j = i + dx, j + dy
                    if 0 <= new_i <= 8 and 0 <= new_j <= 12:
                        # 若相邻建筑为己方
                        if self.map_board_state.map_grid[new_i][new_j][1] == player_id:
                            # 合并并更新当前聚落信息
                            current_root, current_is_city = self.map_board_state.merge_settlement_root(settlements_and_cities, (new_i, new_j), (i, j))
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
            # 遍历所有控制地块，获取其上建筑形成聚落的最少所需要的建筑数
            city_min_needed_building_nums = 4
            for building_pos in self.players[player_id].controlled_map_ids:
                building_root, _ = self.map_board_state.find_settlement_root(settlements_and_cities, building_pos)
                # 若与当前聚落所属同一聚落
                if building_root == current_root:
                    cur_i, cur_j = building_pos
                    # 则获取该建筑对应魔力点
                    building_id, num_side_building = self.map_board_state.map_grid[cur_i][cur_j][2:4]
                    magics_num = self.map_board_state.building_magic[building_id] + num_side_building
                    # 累加计算该聚落魔力点总数
                    curent_settlement_magics_total += magics_num
                    # 累加计算该聚落建筑总数
                    curent_settlement_building_nums += 1 + num_side_building
                    # 计算建城最低所需建筑数
                    match building_id:
                        case 5: # 聚落中有大学允许最低3个建筑建城
                            if city_min_needed_building_nums > 3:
                                city_min_needed_building_nums = 3 
                        case 7: # 聚落中有纪念碑允许最低2个建筑建城
                            if city_min_needed_building_nums > 2:
                                city_min_needed_building_nums = 2 
            
            
            # 判断建城所需最少的总魔力点数
            city_min_needed_magics_nums = 7
            # 如果玩家拥有宫殿板块8并以激活，则建城所需最少的总魔力点数变为6
            if self.players[player_id].palace_tile_id == 8 and self.players[player_id].is_got_palace == True:
                city_min_needed_magics_nums = 6

            # 判断当前聚落是否满足建城条件
            if (
                # 判断当前聚落魔力点数和是否大于等于最低建城所需总魔力点数
                curent_settlement_magics_total >= city_min_needed_magics_nums
                # 判断当前聚落建筑数量是否大于等于最低建城所需建筑数
                and curent_settlement_building_nums >= city_min_needed_building_nums
            ): 
                # 标记根节点为城市
                settlements_and_cities[current_root] = [current_root, True]
                # 触发立即行动，选取城片（保证一定存在可选城片）
                for city_tile_id in range(1,8):
                    if self.all_available_object_dict['city_tile'][city_tile_id].check_get(player_id):                 
                        if self.invoke_immediate_aciton(player_id, ('select_city_tile',)): return
                        break
        
    def calculate_players_total_score(self):

        def find_reachable_pos_set_rely_on_chain_root(chains_root: tuple) -> set:
            need_check_controlled_pos_set = chains_controlled[chains_root]
            all_reachable_map_ids = set()
            navigation_reachable_map_ids_dict = {
                1:[], # 一航水域
                2:[], # 二航水域
                3:[], # 三航水域
                4:[], # 四航水域
            }
            
            # 先遍历所有控制地块，判定相邻的地块中的可抵相连地块(含跨越地块)
            for i,j in need_check_controlled_pos_set:
                direction = [(-1,i%2-1),(-1,i%2),(0,-1),(0,1),(1,i%2-1),(1,i%2)]
                # 如果持有鼹鼠派系或者宫殿板块9，则扩展跨越1格地块至方向中
                if player.faction_id == 7 or player.palace_tile_id == 9:
                    direction.extend([(-2,-1),(-2,0),(-2,1),(-1,i%2-2),(-1,i%2+1),(0,-2),(0,2),(1,i%2-2),(1,i%2+1),(2,-1),(2,0),(2,1)])
                # 如果持有宫殿板块9，则扩展跨越2格地块至方向中
                if player.palace_tile_id == 9:
                    direction.extend([(-3,i%2-2),(-3,i%2-1),(-3,i%2),(-3,i%2+1),(-2,-2),(-2,1),(-1,i%2-3),(-1,i%2+2),(0,-3),(0,3),(1,i%2-3),(1,i%2+2),(2,-2),(2,1),(3,i%2-2),(3,i%2-1),(3,i%2),(3,i%2+1)])
                for dx,dy in direction:
                    new_i, new_j = i + dx, j + dy
                    if (
                        # 在合法边界内
                        0 <= new_i <= 8 and 0 <= new_j <= 12
                        # 被该玩家自身控制
                        and self.map_board_state.map_grid[new_i][new_j][1] == player_id
                    ):
                        # 如果是非水域地块，则直接加入当前地块的可抵地块集合中
                        if self.map_board_state.map_grid[new_i][new_j][0] != 0 :
                            all_reachable_map_ids.add((new_i,new_j))
                        # 如果该地块是水域，则需根据航行等级进一步判定
                        elif player.navigation_level >= 1:
                            navigation_reachable_map_ids_dict[1].append((new_i,new_j))
            
            # 进一步进行航行判定，检索所有可航抵水域地块
            if player.navigation_level >= 2:
                # 遍历所有可航行距离
                for navigation_distance in range(2,player.navigation_level+1):
                    # 如果无上一航行距离可抵的水域，则意味着所有航行可抵水域均已找到，直接跳出循环
                    if not navigation_reachable_map_ids_dict[navigation_distance-1]:
                        break
                    # 若有，则遍历上一距离可航抵水域的所有直接相邻地块
                    for i,j in navigation_reachable_map_ids_dict[navigation_distance-1]:
                        direction = [(-1,i%2-1),(-1,i%2),(0,-1),(0,1),(1,i%2-1),(1,i%2)]
                        for dx,dy in direction:
                            new_i, new_j = i + dx, j + dy
                            if (
                                # 在合法边界内
                                0 <= new_i <= 8 and 0 <= new_j <= 12
                                # 是水域地块
                                and self.map_board_state.map_grid[new_i][new_j][0] == 0
                                # 并且该地块不属于任何更近距离的可航抵水域
                                and all((new_i,new_j) not in navigation_reachable_map_ids_dict[t] for t in range(navigation_distance-1,0,-1))
                            ):
                                # 则将其加入当前航行距离的可航抵水域
                                navigation_reachable_map_ids_dict[navigation_distance].append((new_i,new_j))

            # 依据可航抵水域，判定可抵地块
            if player.navigation_level >= 1: 
                # 获取所有可航抵水域列表
                all_available_navigation_reachable_water_map_ids = [
                    (i,j) for t in range(1,5) for i,j in navigation_reachable_map_ids_dict[t] 
                ]
                # 则遍历所有可航抵水域的直接相邻地块
                for i,j in all_available_navigation_reachable_water_map_ids:
                    direction = [(-1,i%2-1),(-1,i%2),(0,-1),(0,1),(1,i%2-1),(1,i%2)]
                    for dx,dy in direction:
                        new_i, new_j = i + dx, j + dy
                        if (
                            # 在合法边界内
                            0 <= new_i <= 8 and 0 <= new_j <= 12
                            # 非水域地块
                            and self.map_board_state.map_grid[new_i][new_j][0] != 0
                            # 被该玩家自身控制
                            and self.map_board_state.map_grid[new_i][new_j][1] == player_id
                        ):
                            # 则将其加入当前检测地块的可抵地块集合中
                            all_reachable_map_ids.add((new_i,new_j))

            return all_reachable_map_ids
        
        # 计算各玩家大链分数
        all_players_largest_chain_num = {i:0 for i in range(self.num_players)}

        for player_id in range(self.num_players):

            player = self.players[player_id]
            chains_controlled:dict[tuple,set[tuple]] = {}
            chains_reachable:dict[tuple,set[tuple]] = {}

            # 建立根坐标与控制坐标对应字典
            for controlled_pos in player.settlements_and_cities.keys():
                root, _ = self.map_board_state.find_settlement_root(player.settlements_and_cities,controlled_pos)
                if root not in chains_controlled:
                    chains_controlled[root] = set()
                chains_controlled[root].add(controlled_pos)

            # 建立根坐标与可抵控制坐标对应字典
            for root in chains_controlled.keys():
                chains_reachable[root] = find_reachable_pos_set_rely_on_chain_root(root)
            
            # 生成所有根坐标对列表
            root_list = list(chains_controlled.keys())
            all_root_pair = []
            for i in range(len(root_list)-1):
                for j in range(i+1,len(root_list)):
                    all_root_pair.append(
                        (root_list[i],root_list[j])
                    )
            
            # 生成所有互联的根坐标对列表
            chained_root_pairs_list = []
            for r1, r2 in all_root_pair:
                if chains_controlled[r1] & chains_reachable[r2]:
                    chained_root_pairs_list.append((r1,r2))

            # 生成所有互联的根坐标集群列表
            chained_root_clusters_list = []
            for a, b in chained_root_pairs_list:
                merged = False
                for comp in chained_root_clusters_list:
                    if a in comp or b in comp:
                        comp.add(a)
                        comp.add(b)
                        merged = True
                        break
                if not merged:
                    chained_root_clusters_list.append({a, b})
            while True:
                changed = False
                for i in range(len(chained_root_clusters_list)):
                    for j in range(i+1, len(chained_root_clusters_list)):
                        if chained_root_clusters_list[i] & chained_root_clusters_list[j]:  # 如果有交集
                            chained_root_clusters_list[i] |= chained_root_clusters_list[j]  # 合并
                            chained_root_clusters_list.pop(j)
                            changed = True
                            break
                    if changed:
                        break
                if not changed:
                    break

            # 遍历每一个互联的根坐标集群，寻找最大的控制坐标链（大链）
            largest_chained_controlled_pos_num = 0
            for cluster in chained_root_clusters_list:
                current_root_pos_num = 0
                for controlled_root in cluster:
                    current_root_pos_num += len(chains_controlled[controlled_root])
                if current_root_pos_num > largest_chained_controlled_pos_num:
                    largest_chained_controlled_pos_num = current_root_pos_num
            all_players_largest_chain_num[player_id] = largest_chained_controlled_pos_num

        sorted_largest_chain_players = sorted(all_players_largest_chain_num.items(), key=lambda x:x[1], reverse=True)
        chain_score = [18,12,6]
        order_id = 1
        while order_id <= 3:
            for tie_place in range(order_id+1,self.num_players+1):
                if sorted_largest_chain_players[order_id-1][1] > sorted_largest_chain_players[tie_place-1][1]:
                    break
            else:
                tie_place = self.num_players + 1
            get_score_num = sum(chain_score[order_id-1: tie_place-1]) // (tie_place - order_id)
            for rank in range(order_id, tie_place):
                self.players[sorted_largest_chain_players[rank-1][0]].chainscore = get_score_num
            order_id = tie_place

        # 计算各玩家科技轨分数
        track_score = [8,4,2]
        for typ in ['bank', 'law', 'engineering', 'medical']:
            tracks_all_players = []
            for player_id in range(self.num_players):
                tracks_all_players.append((player_id, self.players[player_id].tracks[typ]))
            tracks_all_players.sort(key=lambda x:x[1], reverse=True)
            order_id = 1
            while order_id <= 3:
                for tie_place in range(order_id+1,self.num_players+1):
                    if tracks_all_players[order_id-1][1] > tracks_all_players[tie_place-1][1]:
                        break
                else:
                    tie_place = self.num_players + 1
                get_score_num = sum(track_score[order_id-1: tie_place-1]) // (tie_place - order_id)
                for rank in range(order_id, tie_place):
                    self.players[tracks_all_players[rank-1][0]].trackscore += get_score_num
                order_id = tie_place

        # 计算各玩家资源分数
        for player_id in range(self.num_players):
            self.players[player_id].resourcescore = sum(
                [
                    sum(
                        self.players[player_id].resources[x]
                        for x in [
                            'money', 'ore', 'meeples',
                            'bank_book', 'law_book', 'engineering_book', 'medical_book',
                        ]
                    ),
                    self.players[player_id].magics[3],
                    self.players[player_id].magics[2]//2,
                ]
            ) // 5
            
        return {
            player_idx: {
                'total': sum([
                    self.players[player_idx].boardscore,
                    self.players[player_idx].chainscore,
                    self.players[player_idx].trackscore,
                    self.players[player_idx].resourcescore
                ]),
                'board': self.players[player_idx].boardscore,
                'chain': self.players[player_idx].chainscore,
                'track': self.players[player_idx].trackscore,
                'resource': self.players[player_idx].resourcescore,
            }
            for player_idx in range(self.num_players)
        }
        
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
                terrain, controller = self.map_board_state.map_grid[i][j][:2]
                # 如有则跳出是否可铲判断
                if (
                    controller == -1
                    and self.players[player_id].terrain_id_need_shovel_times[terrain] >= 1
                ):
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
            self.io.update_player_state(player_id, {'money': self.players[player_id].resources['money']})
        
        def adjust_ore(player_id:int , mode: str, num:int):
            mode_factor = 1 if mode == 'get' else -1
            self.players[player_id].resources['ore'] += mode_factor * num
            self.io.update_player_state(player_id, {'ore': self.players[player_id].resources['ore']})
        
        def adjust_book(player_id:int , mode: str, typ: str, num: int):
            match mode, typ:
                case 'get', 'any':
                    act_num = min(sum(self.setup.current_global_books.values()), num)
                    for time in range(act_num):
                        # print(f'请选择您想获取的第{time + 1}本书的类型')
                        if self.invoke_immediate_aciton(player_id, ('select_book', 'get')): return 
                case 'get', _:
                    act_num = min(self.setup.current_global_books[f'{typ}_book'], num)
                    self.setup.current_global_books[f'{typ}_book'] -= act_num
                    self.players[player_id].resources[f'{typ}_book'] += act_num
                case 'use', 'any':
                    for time in range(num):
                        # print(f'请选择您想使用的第{time + 1}本书的类型')
                        if self.invoke_immediate_aciton(player_id, ('select_book', 'use')): return 
                case 'use', _:
                    if num <= self.players[player_id].resources[f'{typ}_book']:
                        self.players[player_id].resources[f'{typ}_book'] -= num
                        self.setup.current_global_books[f'{typ}_book'] += num
                    else:
                        raise ValueError(f'{player_id + 1}号玩家未拥有{typ}书{num}本')
            self.io.update_player_state(player_id, {f'{x}_book': self.players[player_id].resources[f'{x}_book'] for x in ['bank', 'law', 'engineering', 'medical']})

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
                    # 插入米宝行动效果触发
                    self.action_effect(player_id=player_id, insert_meeple=True)
            self.io.update_player_state(player_id, {'meeple': self.players[player_id].resources['meeples']})
                
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
            self.io.update_player_state(player_id, {'score': self.players[player_id].boardscore})
    
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
                        self.players[player_id].magics[1] += num
                    else:
                        raise ValueError(f'三区无{num}点可用魔力')
                case 'boom':    
                    if self.players[player_id].magics[2] >= 2 * num:
                        self.players[player_id].magics[2] -= 2 * num
                        self.players[player_id].magics[3] += num
                    else:
                        raise ValueError(f'不可爆魔，因二区无{2 * num}点魔力')
                case 'science_tile_18':
                    self.players[player_id].magics[3] += num
                    # 科技板块效果-宫殿
            self.io.update_player_state(player_id, {f'magics_{x}': self.players[player_id].magics[x] for x in range(1, 4)})

        def climb_track(player_id: int, typ: str, num: int, split: bool = True):

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
                actual_num = after_climb - before_climb

                if before_climb < 3 <= after_climb:
                    magic_rotation(player_id, 'get', 1)
                if before_climb < 5 <= after_climb:
                    magic_rotation(player_id, 'get', 2)
                if before_climb < 7 <= after_climb:
                    magic_rotation(player_id, 'get', 2)
                if before_climb < 9 <= after_climb:
                    match typ:
                        case 'bank':
                            def display_board_bank_tracks_9(player_idx):
                                self.adjust(player_idx, [('money', 'get', 3)])
                                # print(f'银行轨道等级9 -> 3块钱')
                            self.players[player_id].income_effect_list.append(display_board_bank_tracks_9)
                        case 'law':
                            def display_board_law_tracks_9(player_idx):
                                self.adjust(player_idx, [('magics', 'get', 6)])
                                # print(f'法律轨道等级9 -> 6转魔')
                            self.players[player_id].income_effect_list.append(display_board_law_tracks_9)
                        case 'engineering':
                            def display_board_engineering_tracks_9(player_idx):
                                self.adjust(player_idx, [('ore', 'get', 1)])
                                # print(f'工程轨道等级9 -> 1矿')
                            self.players[player_id].income_effect_list.append(display_board_engineering_tracks_9)
                        case 'medical':
                            def display_board_medical_tracks_9(player_idx):
                                self.adjust(player_idx, [('score', 'get', 'board', 3)])
                                # print(f'医疗轨道等级9 -> 3分')
                            self.players[player_id].income_effect_list.append(display_board_medical_tracks_9)
                        case _:
                            raise ValueError(f'不存在{typ}轨道效果')
                if before_climb < 12 <= after_climb:
                    magic_rotation(player_id, 'get', 3)
            else:
                if split:
                    actual_num = 0
                    # 循环调起选择轨道立即行动n次，每次推进1轨
                    for _ in range(num):
                        # 遍历检查是否有可推进轨道
                        for temp_typ in ['bank', 'law', 'engineering', 'medical']:
                            if self.check(player_id, [('tracks', temp_typ)]):
                                actual_num += 1
                                # 如有，则跳出循环，调起立即行动
                                break
                        else:
                            # 如无，则跳出循环，取消后续立即行动调起
                            break
                        if self.invoke_immediate_aciton(player_id, ('select_track',)): return
                else:
                    actual_num = 0
                    for temp_typ in ['bank', 'law', 'engineering', 'medical']:
                        if self.check(player_id, [('tracks', temp_typ)]):
                            actual_num = 1
                            # 如有，则跳出循环，调起立即行动
                            break
                    else:
                        return
                    if self.invoke_immediate_aciton(player_id, ('select_track',)): return
                    selected_track_typ = self.players[player_id].choice_track
                    climb_track(player_id, selected_track_typ, num-1)

            # 爬轨行动效果
            self.action_effect(player_id=player_id, climb_track_nums=actual_num)

        def adjust_terrain(player_id: int, shovel_times: int):

            i,j = self.players[player_id].choice_position

            native_terrain_id = self.players[player_id].planning_card_id
            current_terrain_id = self.map_board_state.map_grid[i][j][0]

            if shovel_times > self.players[player_id].terrain_id_need_shovel_times[current_terrain_id]:
                raise ValueError(f'地形铲次数超过可铲次数')

            factor = 1 if current_terrain_id >= native_terrain_id else -1
            if abs(current_terrain_id - native_terrain_id) > 3:
                new_terrain_id = (current_terrain_id + factor * shovel_times - 1) % 7 + 1 
            else:
                new_terrain_id = current_terrain_id - factor * shovel_times

            self.map_board_state.map_grid[i][j][0] = new_terrain_id
            # 铲子行动效果
            self.action_effect(player_id=player_id, shovel_times=shovel_times)

            self.io.update_terrain(i,j,self.map_board_state.map_grid[i][j][0])

        def adjust_building(player_id: int, mode:str, to_build_id: int, is_neutral: bool):

            def panel_update(pos):
                # 更新面板
                i,j = pos
                side_building_num = self.map_board_state.map_grid[i][j][3]
                match side_building_num, to_build_id:
                    case 0, y if y != 8:
                        self.io.update_building(i, j, 0 if is_neutral else self.players[player_id].planning_card_id, to_build_id, 'replace')
                    case 1, 8:
                        self.io.update_building(i, j, 0, 8, 'overlay')
                    case 1, y if y != 8:
                        self.io.update_building(i, j, 0 if is_neutral else self.players[player_id].planning_card_id, to_build_id, 'replace')
                        self.io.update_building(i, j, 0, 8, 'overlay')
                    case _:
                        raise ValueError('面板更新建筑模式不存在')
            
            match mode:
                case (
                    'build_normal'|'build_neutral'|
                    'build_setup'|'build_after_shovel'|
                    'build_special_faction_tile_6'|
                    'build_special_palace_tile_16'|
                    'build_after_tunneling'|
                    'build_after_flight'
                ):
                    if mode == 'build_setup':
                        # 立即选择位置
                        if self.invoke_immediate_aciton(
                            player_id, 
                            ('select_position', 'anywhere', set([self.players[player_id].planning_card_id]))
                        ): return 
                        # 获取选择的位置
                        i,j = self.players[player_id].choice_position

                    elif mode == 'build_after_shovel':
                        # 获取之前第一铲地位置
                        i,j = self.players[player_id].choice_position
                        # 支付建造工会费用
                        self.adjust(player_id, [('money', 'use', 2), ('ore', 'use', 1)])

                    elif mode == 'build_special_faction_tile_6': # 蜥蜴人派系板块行动效果
                        max_shovel_times = (
                            self.players[player_id].resources['ore']
                            // self.players[player_id].shovel_level
                        )
                        # 判断是否存在可建地
                        for p,q in self.players[player_id].reachable_map_ids:
                            terrain, controller = self.map_board_state.map_grid[p][q][:2]
                            # 如有则选择可建地并跳出判断
                            if (
                                self.players[player_id].terrain_id_need_shovel_times[terrain] <= max_shovel_times
                                and controller == -1    
                            ):
                                if self.invoke_immediate_aciton(
                                    player_id, 
                                    ('select_position', 'reachable', ('build', max_shovel_times))
                                ): return 
                                i,j = self.players[player_id].choice_position
                                cur_terrain = self.map_board_state.map_grid[i][j][0]
                                need_shovel_times = self.players[player_id].terrain_id_need_shovel_times[cur_terrain]
                                # 支付铲地费用
                                self.adjust(
                                    player_id, 
                                    [
                                        ('ore', 'use', need_shovel_times * self.players[player_id].shovel_level),
                                        ('land', need_shovel_times),
                                    ],
                                )
                                break
                        else:
                            return
                    
                    elif mode == 'build_special_palace_tile_16': # 宫殿板块16的立即行动效果
                        # 遍历查找是否存在可建原生地
                        for p,q in [(x,y) for x in range(9) for y in range(13)]:
                            terrain, controller = self.map_board_state.map_grid[p][q][:2]
                            # 如果存在无控制者的原生地，则调起选择地块位置行动后跳出，若无则返回
                            if (
                                terrain == self.players[player_id].planning_card_id 
                                and controller == -1
                            ):
                                if self.invoke_immediate_aciton(
                                    player_id, 
                                    ('select_position', 'anywhere', set([self.players[player_id].planning_card_id]))
                                ): return 
                                break
                        else:
                            return
                                    
                        # 获取选择的位置
                        i,j = self.players[player_id].choice_position

                    else: # build_normal | build_neutral | build_after_flight | build_after_tunneling
                        
                        # 最大可铲次数 = 玩家拥有矿数 // 铲子等级
                        if mode == 'build_normal' or mode == 'build_after_flight' or mode == 'build_after_tunneling':
                            max_shovel_times = (
                                (self.players[player_id].resources['ore'] - 1)
                                // self.players[player_id].shovel_level
                            )
                        elif mode == 'build_neutral':
                            max_shovel_times = (
                                self.players[player_id].resources['ore']
                                // self.players[player_id].shovel_level
                            )

                        # 根据模式确定检查范围
                        if mode == 'build_normal' or mode == 'build_neutral':
                            need_check_range = self.players[player_id].reachable_map_ids
                        
                        elif mode == 'build_after_tunneling': # 对于鼹鼠派系的特殊支持
                            
                            # 创建跨一地块范围坐标集合（未排除已被控制与水域地块）
                            available_map_ids = set()
                            
                            # 向集合中添加跨越1地块的坐标
                            for i,j in self.players[player_id].controlled_map_ids:
                                two_direction = [(-2,-1),(-2,0),(-2,1),(-1,i%2-2),(-1,i%2+1),(0,-2),(0,2),(1,i%2-2),(1,i%2+1),(2,-1),(2,0),(2,1)]
                                available_map_ids |= {(i+dx,j+dy) for dx,dy in two_direction if 0 <= i+dx <= 8 and 0 <= j+dy <= 12}
                                    
                            # 从集合中排除与现有建筑直接相邻的坐标
                            for i,j in self.players[player_id].controlled_map_ids:
                                one_direction = [(-1,i%2-1),(-1,i%2),(0,-1),(0,1),(1,i%2-1),(1,i%2)]
                                available_map_ids -= {(i+dx,j+dy) for dx,dy in one_direction if 0 <= i+dx <= 8 and 0 <= j+dy <= 12}

                            need_check_range = list(available_map_ids)

                        elif mode == 'build_after_flight':  # 对于宫殿板块14的特殊支持

                            # 创建跨一地块范围坐标集合（未排除已被控制与水域地块）
                            available_map_ids = set()
                            
                            # 向集合中添加跨越1地块的坐标
                            for i,j in self.players[player_id].controlled_map_ids:
                                two_direction = [(-2,-1),(-2,0),(-2,1),(-1,i%2-2),(-1,i%2+1),(0,-2),(0,2),(1,i%2-2),(1,i%2+1),(2,-1),(2,0),(2,1)]
                                available_map_ids |= {(i+dx,j+dy) for dx,dy in two_direction if 0 <= i+dx <= 8 and 0 <= j+dy <= 12}

                            # 向集合中添加跨越2地块的坐标
                            for i,j in self.players[player_id].controlled_map_ids:
                                three_direction = [(-3,i%2-2),(-3,i%2-1),(-3,i%2),(-3,i%2+1),(-2,-2),(-2,1),(-1,i%2-3),(-1,i%2+2),(0,-3),(0,3),(1,i%2-3),(1,i%2+2),(2,-2),(2,1),(3,i%2-2),(3,i%2-1),(3,i%2),(3,i%2+1)]
                                available_map_ids |= {(i+dx,j+dy) for dx,dy in three_direction if 0 <= i+dx <= 8 and 0 <= j+dy <= 12}
                                    
                            # 从集合中排除与现有建筑直接相邻的坐标
                            for i,j in self.players[player_id].controlled_map_ids:
                                one_direction = [(-1,i%2-1),(-1,i%2),(0,-1),(0,1),(1,i%2-1),(1,i%2)]
                                available_map_ids -= {(i+dx,j+dy) for dx,dy in one_direction if 0 <= i+dx <= 8 and 0 <= j+dy <= 12}

                            need_check_range = list(available_map_ids)

                        # 判断在需检查范围内是否存在可建地
                        for p,q in need_check_range:
                            terrain, controller = self.map_board_state.map_grid[p][q][:2]
                            if (
                                terrain != 0
                                and self.players[player_id].terrain_id_need_shovel_times[terrain] <= max_shovel_times
                                and controller == -1    
                            ):
                                if mode == 'build_normal' or mode == 'build_neutral':
                                    if self.invoke_immediate_aciton(
                                        player_id, 
                                        ('select_position', 'reachable', ('build', max_shovel_times))
                                    ): return
                                elif mode == 'build_after_flight':
                                    if self.invoke_immediate_aciton(
                                        player_id, 
                                        ('select_position', 'non_adjacent', (3, 'build', max_shovel_times))
                                    ): return
                                elif mode == 'build_after_tunneling':
                                    if self.invoke_immediate_aciton(
                                        player_id, 
                                        ('select_position', 'non_adjacent', (2, 'build', max_shovel_times))
                                    ): return 

                                i,j = self.players[player_id].choice_position
                                cur_terrain = self.map_board_state.map_grid[i][j][0]
                                need_shovel_times = self.players[player_id].terrain_id_need_shovel_times[cur_terrain]
                                # 支付铲地费用
                                self.adjust(
                                    player_id, 
                                    [
                                        ('ore', 'use', need_shovel_times * self.players[player_id].shovel_level),
                                        ('land', need_shovel_times),
                                    ],
                                )
                                if mode == 'build_normal' or mode == 'build_after_flight' or mode == 'build_after_tunneling':
                                    # 支付建造工会费用
                                    self.adjust(player_id, [('money', 'use', 2), ('ore', 'use', 1)])
                                break
                        else:
                            if mode == 'build_normal' or mode == 'build_after_flight' or mode == 'build_after_tunneling':
                                raise ValueError(f'无可建地')
                            elif mode == 'build_neutral':
                                # print(f'中立建造无可建地')
                                return 

                    # 检查该地块是否符合条件
                    match self.map_board_state.map_grid[i][j]:
                        # 该地形被其他玩家控制的情况
                        case [_,controller, _, _, _] if controller != -1 and controller != player_id:  
                            raise ValueError(f'{chr(ord('A')+i)}{j+1}处已被其他玩家控制')
                        # 该地形非该玩家原生地形的情况
                        case [terrain, _, _, _, _] if terrain != self.players[player_id].planning_card_id:
                            raise ValueError(f'{chr(ord('A')+i)}{j+1}处目前不是你的原生地形')
                        # 该地形已存在该玩家建筑的情况
                        case [_, _, pre_building_id, pre_side_building_num, pre_is_neutral] if pre_building_id != 0:    
                            raise ValueError(f'{chr(ord('A')+i)}{j+1}处已存在建筑')          
                    # 修改地块控制玩家id和建筑id和建筑性质
                    self.map_board_state.map_grid[i][j][1:3] = player_id, to_build_id
                    self.map_board_state.map_grid[i][j][4] = is_neutral
                    panel_update((i,j))
                    # 调整玩家规划板上建筑数量
                    if mode == 'build_setup':
                        if to_build_id == 6:
                            self.players[player_id].buildings[to_build_id] += 1
                        else:
                            self.players[player_id].buildings[to_build_id] -= 1
                    elif mode == 'build_neutral':
                        cor_dict = {
                            1: 9,
                            2: 10,
                            3: 11,
                            4: 12,
                            5: 13,
                            6: 6,
                            7: 7,
                        }
                        if to_build_id == 3:
                            self.players[player_id].is_got_palace = True
                        cor_to_build_id = cor_dict[to_build_id]
                        self.players[player_id].buildings[cor_to_build_id] += 1
                    else:
                        self.players[player_id].buildings[to_build_id] -= 1
                    # 更新控制地块与可抵地块
                    self.players[player_id].controlled_map_ids.add((i,j))
                    self.update_reachable_map_ids_set(player_id, (i,j))
                    # 定义检查模式为建造
                    check_mode = 'build'

                case 'upgrade'|'build_annex'|'degrade'|'upgrade_special':
                    i,j = self.players[player_id].choice_position
                    match self.map_board_state.map_grid[i][j]:
                        # 该地形被其他玩家控制的情况或未被控制的情况
                        case [_,controller, _, _, _] if controller != -1 and controller != player_id:  
                            raise ValueError(f'{chr(ord('A')+i)}{j+1}处已被其他玩家控制或未被控制')
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
                                            self.map_board_state.map_grid[i][j][2:] = to_build_id, pre_side_building_num, is_neutral
                                            panel_update((i,j))
                                            # 支付升级费用 并 立即获取一个能力板块
                                            self.adjust(player_id, [
                                                ('money', 'use', 5),
                                                ('ore', 'use', 3),
                                                ('ability_tile',)
                                            ])
                                        # 升级为大学时
                                        case 5:
                                            self.map_board_state.map_grid[i][j][2:] = to_build_id, pre_side_building_num, is_neutral
                                            panel_update((i,j))
                                            # 支付升级费用 并 立即获取一个能力板块
                                            self.adjust(player_id, [
                                                ('money', 'use', 8), 
                                                ('ore', 'use', 5),
                                                ('ability_tile',)
                                            ])
                                case 'build_annex', _, _, 0, 8, True:
                                    pass
                                case 'degrade', 4, False, _, 2, False:
                                    pass
                                case 'upgrade_special', 1, False, _, 2, False: # 宫殿板块4和书行动4 免费升级将1车间升级成工会
                                    pass
                                case _:
                                    raise ValueError(f'已存在建筑物的地形上进行非法操作')
                            
                            # 修改地块的建筑id和侧楼数量和建筑性质 与 玩家规划板上建筑数量
                            if to_build_id != 8:
                                self.map_board_state.map_grid[i][j][2:] = to_build_id, pre_side_building_num, is_neutral
                                self.players[player_id].buildings[pre_building_id] += 1
                            else:
                                self.map_board_state.map_grid[i][j][2:] = pre_building_id, 1, pre_is_neutral
                            if not (mode == 'upgrade' and to_build_id in [4,5]):
                                panel_update((i,j))
                            self.players[player_id].buildings[to_build_id] -= 1
                            # 定义检查模式为升级
                            check_mode = 'upgrade'
                        case _:
                            raise ValueError(f'未进入建筑升级模式')
                
                case _:
                    raise ValueError(f'不存在{mode}建筑效果')
            
            # 触发行动效果（初始阶段的建造不触发）
            if mode != 'build_setup':
                is_edge = False
                is_riverside = False
                if to_build_id == 1:
                    i,j = self.players[player_id].choice_position
                    # 判断是否处于地图边缘
                    if i == 0 or i == 8 or j == 0 or j == 12:
                        is_edge =True
                    # 判断是否处于河边
                    direction = [(-1,i%2-1),(-1,i%2),(0,-1),(0,1),(1,i%2-1),(1,i%2)]
                    for dx,dy in direction:
                        new_i, new_j = i + dx, j + dy
                        if (
                            # 在合法边界内
                            0 <= new_i <= 8 and 0 <= new_j <= 12
                            # 是水域地形
                            and self.map_board_state.map_grid[new_i][new_j][0] == 0
                        ):
                            is_riverside = True
                            break
                # 建筑行动效果触发
                self.action_effect(player_id=player_id, building_id=to_build_id, is_edge=is_edge, is_riverside=is_riverside)

            # 初始建造和建造侧楼不会触发吸取魔力立即行动
            if not (mode == 'build_annex' or mode == 'build_setup'):
                # 执行吸取魔力立即行动（如有）
                self.absorb_magics_check(player_id, (i,j))
            
            # 更新聚落及检查城市建立
            self.city_establishment_check(player_id,check_mode,(i,j))

        def build_bridge(player_id: int):
            # 调起建桥立即行动（保证一定可建）
            if self.check(player_id, [('bridge',)]):
                self.players[player_id].resources['all_bridges'] -= 1
                if self.invoke_immediate_aciton(player_id, ('build_bridge',)): return

        def shovel(player_id: int, shovel_times: int, can_build_after_shovel: bool = True):
            # 初始化第一铲地标记和位置
            first_shovel = True
            first_pos = tuple()
            # 当仍然存在剩余铲数时
            while shovel_times > 0:
                # 如果玩家持有鼹鼠派系或者宫殿板块9，则第一铲地需要判断是否使用其特殊行动，实现跨越1至2地块
                need_check_range = self.players[player_id].reachable_map_ids
                choice = 'normal'
                if (
                    # 仅第一铲地时可以使用飞行或隧道
                    first_shovel == True
                    # 仅当可以铲后建造时，才可使用飞行或隧道
                    and can_build_after_shovel == True
                    and (
                        # 满足使用隧道的条件
                        (
                            self.players[player_id].faction_id == 7
                            and self.players[player_id].resources['ore'] >= 1
                        )
                        # 或满足使用飞行的条件 
                        or (
                            self.players[player_id].palace_tile_id == 9
                            and self.players[player_id].is_got_palace == True
                            and self.players[player_id].resources['meeples'] >= 1
                        )
                    )
                ):
                    if self.invoke_immediate_aciton(player_id, ('select_tunneling_or_flight_in_spade',)): return 
                    
                    match self.game_args['action_history'][-1]:
                        case (player_id, 'immediate', 346):
                            pass
                        
                        case (player_id, 'immediate', 347):
                            # 创建跨一地块范围坐标集合（未排除已被控制与水域地块）
                            available_map_ids = set()

                            # 向集合中添加跨越1地块的坐标
                            for i,j in self.players[player_id].controlled_map_ids:
                                two_direction = [(-2,-1),(-2,0),(-2,1),(-1,i%2-2),(-1,i%2+1),(0,-2),(0,2),(1,i%2-2),(1,i%2+1),(2,-1),(2,0),(2,1)]
                                available_map_ids |= {(i+dx,j+dy) for dx,dy in two_direction if 0 <= i+dx <= 8 and 0 <= j+dy <= 12}
                                    
                            # 从集合中排除与现有建筑直接相邻的坐标
                            for i,j in self.players[player_id].controlled_map_ids:
                                one_direction = [(-1,i%2-1),(-1,i%2),(0,-1),(0,1),(1,i%2-1),(1,i%2)]
                                available_map_ids -= {(i+dx,j+dy) for dx,dy in one_direction if 0 <= i+dx <= 8 and 0 <= j+dy <= 12}

                            need_check_range = list(available_map_ids)
                            choice = 'tunneling'

                        case (player_id, 'immediate', 348):
                            # 创建跨一地块范围坐标集合（未排除已被控制与水域地块）
                            available_map_ids = set()

                            # 向集合中添加跨越1地块的坐标
                            for i,j in self.players[player_id].controlled_map_ids:
                                two_direction = [(-2,-1),(-2,0),(-2,1),(-1,i%2-2),(-1,i%2+1),(0,-2),(0,2),(1,i%2-2),(1,i%2+1),(2,-1),(2,0),(2,1)]
                                available_map_ids |= {(i+dx,j+dy) for dx,dy in two_direction if 0 <= i+dx <= 8 and 0 <= j+dy <= 12}

                            # 向集合中添加跨越2地块的坐标
                            for i,j in self.players[player_id].controlled_map_ids:
                                three_direction = [(-3,i%2-2),(-3,i%2-1),(-3,i%2),(-3,i%2+1),(-2,-2),(-2,1),(-1,i%2-3),(-1,i%2+2),(0,-3),(0,3),(1,i%2-3),(1,i%2+2),(2,-2),(2,1),(3,i%2-2),(3,i%2-1),(3,i%2),(3,i%2+1)]
                                available_map_ids |= {(i+dx,j+dy) for dx,dy in three_direction if 0 <= i+dx <= 8 and 0 <= j+dy <= 12}
                                    
                            # 从集合中排除与现有建筑直接相邻的坐标
                            for i,j in self.players[player_id].controlled_map_ids:
                                one_direction = [(-1,i%2-1),(-1,i%2),(0,-1),(0,1),(1,i%2-1),(1,i%2)]
                                available_map_ids -= {(i+dx,j+dy) for dx,dy in one_direction if 0 <= i+dx <= 8 and 0 <= j+dy <= 12}

                            need_check_range = list(available_map_ids)
                            choice = 'flight'

                        case _:
                            raise ValueError('选择隧道或飞行失败')

                # 判断是否存在可铲地（至少一铲）
                for i,j in need_check_range:
                    terrain, controller = self.map_board_state.map_grid[i][j][:2]
                    # 如有则跳出是否可铲判断
                    if (
                        controller == -1
                        and terrain != 0
                        and self.players[player_id].terrain_id_need_shovel_times[terrain] >= 1
                    ):
                        break
                else:
                    # 未跳出，则代表无可铲地块，则跳出铲行动
                    break

                if choice == 'normal':
                    # 选择可铲位置（保证一定存在可铲地）
                    if self.invoke_immediate_aciton(player_id, ('select_position', 'reachable', ('shovel', 1))): return 
                elif choice == 'tunneling':
                    # 选择可铲位置（保证一定存在可铲地）
                    if self.invoke_immediate_aciton(player_id, ('select_position','non_adjacent',(2,'shovel',1))): return
                elif choice == 'flight':
                    # 选择可铲位置（保证一定存在可铲地）
                    if self.invoke_immediate_aciton(player_id, ('select_position','non_adjacent',(3,'shovel',1))): return
                
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
            # 如果存在一铲地（即至少铲了一下之后），并且该次铲子允许铲后建造
            if first_pos and can_build_after_shovel:
                i,j = first_pos
                first_pos_terrain = self.map_board_state.map_grid[i][j][0]
                first_pos_shovel_times = self.players[player_id].terrain_id_need_shovel_times[first_pos_terrain]
                # 调起铲后建造立即行动（保证一定存在可建资源）
                if self.check(player_id, [
                    ('money', 2), 
                    ('ore', 1 + first_pos_shovel_times * self.players[player_id].shovel_level),
                    ('building', 1)
                ]):
                    self.players[player_id].choice_position = first_pos
                    if self.invoke_immediate_aciton(player_id,('build_workshop',)): return 

        def improve_navigation(player_id: int):
            # 判断是否可升级
            if self.players[player_id].navigation_level < 3:
                # 执行提升航行等级动作
                self.players[player_id].navigation_level += 1
                # 查询本次提升奖励
                reward = []
                if self.players[player_id].planning_card_id == 3:
                    match self.players[player_id].navigation_level:
                        case 2:
                            reward.append(('score', 'get', 'board', 3))
                        case 3:
                            reward.append(('book', 'get', 'any', 2))
                else:
                    match self.players[player_id].navigation_level:
                        case 1:
                            reward.append(('score', 'get', 'board', 2))
                        case 2:
                            reward.append(('book', 'get', 'any', 2))
                        case 3:
                            reward.append(('score', 'get', 'board', 4))
                # 获取本次提升奖励
                self.adjust(player_id, reward)
                # 升级航行行动效果触发
                self.action_effect(player_id=player_id, improve_navigation_or_shovel=True)

                # 更新数据面板
                self.io.update_player_state(player_id, {'navigation_level': self.players[player_id].navigation_level})

                # 更新可抵地块
                self.update_reachable_map_ids_set(player_id)

        def improve_shovel(player_id: int):
            # 判断是否可升级
            if self.players[player_id].shovel_level > 1:
                # 执行提升铲子等级动作
                self.players[player_id].shovel_level -= 1
                # 查询本次提升奖励
                reward = []
                match self.players[player_id].shovel_level:
                    case 2:
                        reward.append(('book', 'get', 'any', 2))
                    case 1:
                        reward.append(('score', 'get', 'board', 6))
                # 获取本次提升奖励
                self.adjust(player_id, reward)
                # 升级铲子行动效果触发
                self.action_effect(player_id=player_id, improve_navigation_or_shovel=True)
        
            self.io.update_player_state(player_id, {'shovel_level': self.players[player_id].shovel_level})

        def get_ability_tile(player_id: int):
            for ability_tile_id in range(1,13):
                if self.all_available_object_dict['ability_tile'][ability_tile_id].check_get(player_id):
                    if self.invoke_immediate_aciton(player_id, ('select_ability_tile',)): return 
                    break

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
            'spade': shovel,
            'navigation': improve_navigation,
            'shovel': improve_shovel,
            'ability_tile': get_ability_tile
        }

        def adjust(player_id: int, list_to_be_adjusted) -> tuple[str, str]:
            reward_str_list = []
            spend_str_list = []
            for adjust_item, *adjust_args in list_to_be_adjusted:
                if adjust_item not in all_adjust_list:
                    raise ValueError(f'非法状态调整对象：{adjust_item}')
                else:
                    all_adjust_list[adjust_item](player_id, *adjust_args)
                    match adjust_item, adjust_args:
                        case 'money', ('get', num):
                            if num > 0:
                                reward_str_list.append(f'{num}块钱')
                        case 'money', ('use', num):
                            if num > 0:
                                spend_str_list.append(f'{num}块钱') 
                        case 'ore', ('get', num):
                            if num > 0:
                                reward_str_list.append(f'{num}矿')
                        case 'ore', ('use', num):
                            if num > 0:
                                spend_str_list.append(f'{num}矿')
                        case 'book', ('get', typ, num):
                            if num > 0:
                                match typ:
                                    case 'any':
                                        reward_str_list.append(f'{num}任意书')
                                    case 'bank':
                                        reward_str_list.append(f'{num}银行书')
                                    case 'law':
                                        reward_str_list.append(f'{num}法律书')
                                    case 'engineering':
                                        reward_str_list.append(f'{num}工程书')
                                    case 'medical':
                                        reward_str_list.append(f'{num}医疗书')
                        case 'book', ('use', typ, num):
                            if num > 0:
                                match typ:
                                    case 'any':
                                        spend_str_list.append(f'{num}任意书')
                                    case 'bank':
                                        spend_str_list.append(f'{num}银行书')
                                    case 'law':
                                        spend_str_list.append(f'{num}法律书')
                                    case 'engineering':
                                        spend_str_list.append(f'{num}工程书')
                                    case 'medical':
                                        spend_str_list.append(f'{num}医疗书')
                        case 'meeple', ('get', num):
                            if num > 0:
                                reward_str_list.append(f'{num}米宝')
                        case 'meeple', ('use', num):
                            if num > 0:
                                spend_str_list.append(f'{num}米宝')
                        case 'score', ('get', 'board', num):
                            if num > 0:
                                reward_str_list.append(f'{num}分')
                        case 'score', ('use', 'baord', num):
                            if num > 0:
                                spend_str_list.append(f'{num}分')
                        case 'magics', ('get', num):
                            if num > 0:
                                reward_str_list.append(f'{num}转魔')
                        case 'magics', ('use', num):
                            if num > 0:
                                spend_str_list.append(f'{num}转魔')
                        case 'tracks', (typ, num):
                            if num > 0:
                                match typ:
                                    case 'any':
                                        reward_str_list.append(f'推{num}任意轨')
                                    case 'bank':
                                        reward_str_list.append(f'推{num}银行轨')
                                    case 'law':
                                        reward_str_list.append(f'推{num}法律轨')
                                    case 'engineering':
                                        reward_str_list.append(f'推{num}工程轨')
                                    case 'medical':
                                        reward_str_list.append(f'推{num}医疗轨')
                        case 'spade', (num, _):
                            if num > 0:
                                reward_str_list.append(f'{num}铲')
                        case 'navigation', _:
                            reward_str_list.append('升1航行')
                        case 'shovel', _:
                            reward_str_list.append('升1铲子')
                        case 'ability_tile', _:
                            reward_str_list.append('1能力板块')
            if spend_str_list:
                spend_str = ' + '.join(spend_str_list)
            else:
                spend_str = ''
            if reward_str_list:
                reward_str = ' + '.join(reward_str_list)
            else:
                reward_str = ''
            return spend_str, reward_str
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
        
    def action_effect(  # 行动效果触发
        self, player_id: int, 
        building_id = 0, is_edge = False, is_riverside = False,
        shovel_times = 0,
        insert_meeple = False,
        climb_track_nums = 0,
        get_city_tile = False,
        improve_navigation_or_shovel = False,
        get_science_tile = False,
        get_ability_tile_typ = '',
    ):  
        
        reward = []

        # 轮次计分板行动效果（所有玩家共用）
        match (
            self.setup.round_scoring_order[self.round - 1],
            building_id, shovel_times, climb_track_nums,
            get_city_tile,improve_navigation_or_shovel,
            get_science_tile,
        ):
            case 1, 1, *_:
                reward.append(('score', 'get', 'board', 2))
            case 2, 1, *_:
                reward.append(('score', 'get', 'board', 2))
            case 3, 2, *_:
                reward.append(('score', 'get', 'board', 3))
            case 4, 2, *_:
                reward.append(('score', 'get', 'board', 3))
            case 5, 4, *_:
                reward.append(('score', 'get', 'board', 4))
            case 6, 3|5, *_:
                reward.append(('score', 'get', 'board', 5))
            case 7, 3|5, *_:
                reward.append(('score', 'get', 'board', 5))
            case 8, _, times, *_:
                reward.append(('score', 'get', 'board', 2 * times))
            case 9, _, _, times, *_:
                reward.append(('score', 'get', 'board', times))
            case 10, _, _, _, True, *_:
                reward.append(('score', 'get', 'board', 5))
            case 11, _, _, _, _, True, *_:
                reward.append(('score', 'get', 'board', 3))
            case 12, _, _, _, _, _, True:
                reward.append(('score', 'get', 'board', 5))
        
        # 最终轮次计分板块行动效果
        if self.round == 6:
            match self.setup.final_scoring, building_id, is_edge:
                case 1, 1, _:
                    reward.append(('score', 'get', 'board', 2))
                case 2, 4, _:
                    reward.append(('score', 'get', 'board', 4))
                case 3, 1, True:
                    reward.append(('score', 'get', 'board', 3))
                case 4, 2, _:
                    reward.append(('score', 'get', 'board', 3))
        
        # 能力板块行动效果
        if insert_meeple and 8 in self.players[player_id].ability_tile_ids:
            reward.append(('score', 'get', 'board', 2))
        if building_id == 1 and is_edge and 10 in self.players[player_id].ability_tile_ids:
            reward.append(('score', 'get', 'board', 3))

        # 回合助推板行动效果
        if building_id == 1 and is_edge and self.players[player_id].booster_ids[-1] == 1:
            reward.append(('score', 'get', 'board', 2))
        elif insert_meeple and self.players[player_id].booster_ids[-1] == 4:
            reward.append(('score', 'get', 'board', 2))
        elif building_id == 2 and self.players[player_id].booster_ids[-1] == 7:
            reward.append(('score', 'get', 'board', 3))

        # 宫殿板块行动效果
        if self.players[player_id].buildings[3] == 0: # 等价于宫殿板块已激活
            if building_id == 1 and self.players[player_id].palace_tile_id == 12:
                reward.append(('score', 'get', 'board', 2))
            elif building_id == 2 and self.players[player_id].palace_tile_id == 13:
                reward.append(('score', 'get', 'board', 3))
        
        # 派系板块行动效果
        if get_city_tile and self.players[player_id].faction_id == 2:
            reward.extend([('tracks', 'any', 3), ('book', 'get', 'any', 1)])
        elif shovel_times and self.players[player_id].faction_id == 3:
            reward.append(('money', 'get', 2* shovel_times))
        elif get_city_tile and self.players[player_id].faction_id == 6:
            if self.check(player_id, [('spade',)]):
                reward.append(('spade', 1, False))
            if self.check(player_id, [('building', 1)]):
                reward.append(('building','build_special_faction_tile_6', 1, False))
        elif building_id == 1 and is_riverside and self.players[player_id].faction_id == 9:
            reward.append(('score', 'get', 'board', 2))
        elif get_ability_tile_typ and self.players[player_id].faction_id == 11:
            reward.append(('book', 'get', get_ability_tile_typ, 1))

        # ============== 获取奖励 ==============
        self.adjust(player_id=player_id, list_to_be_adjusted=reward)