from GameState import GameStateBase
from DetailedAction import DetailedAction
from typing import Callable

class ActionSystem:
    """行动系统"""
    def __init__(self, game_state: GameStateBase, player_id: int):
        self.game_state = game_state                                                    # 游戏状态
        self.player_id = player_id                                                      # 当前玩家ID
        self.player = game_state.players[player_id]                                     # 当前玩家
        self.all_detailed_actions = DetailedAction().all_detailed_actions               # 所有具体行动         
        self.all_available_object_dict = self.game_state.all_available_object_dict      # 效果板块索引
        self.action_dict = self.create_action_dict()                                    # 创建所有行动字典

        # 创建各地形id需要几铲才能成为原生地的初始空字典，在选择规划卡后更新
        self.terrain_id_need_shovel_times = {i: -1 for i in range(1,8)}

        # 行动名称列表
        self.action_list = [
            'select_planning_card',             # 选择规划卡
            'select_faction',                   # 选择派系
            'select_palace_tile',               # 选择宫殿板块
            'select_round_booster',             # 选择初始回合助推板
            'setup_build',                      # 初始建筑摆放
            'pass_this_round',                  # 略过本回合
            'quick_magics',                     # 快速魔力行动
            'improve_navigation_level',         # 升级航海等级
            'improve_shovel_level',             # 升级铲子等级
            'insert_meeple',                    # 插米宝提轨道
            'shovel_and_build',                 # 改造地形或/并建造
            'upgrade_building',                 # 升级建筑
        ]

        # 立即行动名称列表
        self.immediate_action_list = [
            'select_book',                      # 选择哪个学科的书
            'select_track',                     # 选择哪个学科的轨道
            'select_position',                  # 选择地图上哪个坐标
            'gain_magics',                      # 选择是否吸取魔力
            'select_city_tile',                 # 选择哪种城市板块
            'select_ability_tile',              # 选择哪种能力板块
        ]

    def get_available_actions(self, mode, args) -> list:

        available_action_ids_list = []

        match mode:
            case 'normal':
                for name in self.action_list:
                    action_function = self.action_dict('check', name)
                    available_action_ids_list.extend(action_function())

            case 'immediate':
                name, *args = args
                action_function = self.action_dict('check', name)
                available_action_ids_list.extend(action_function(*args))
                        
        return available_action_ids_list
    
    def execute_action(self, action_id):

        action_name = self.all_detailed_actions[action_id]['action']
        action_arg = self.all_detailed_actions[action_id]['args']

        # 执行行动（常规（主要/快速）/立即）
        self.action_dict('execute', action_name)(action_arg)
           
    def is_next_action_exist(self) -> bool:
        
        if (
            # 当主行动未执行时
            self.player.main_action_is_done == False
            # 或玩家有可选快速魔力行动时
            or self.action_dict('check', 'quick_magics')()
        ):
            return True
        return False

    def reset_action_state(self):

        # 重置是否已执行主要行动标记
        self.player.main_action_is_done = False
        # 重置是否已选择跳过标记
        self.player.ispass = False

    def create_action_dict(self):

        def check_select_planning_card_action() -> list:
            """检查选择规划卡动作是否合法"""
        
            if (
                # 判断是否为可选回合
                self.game_state.round == 0 
                # 判断该玩家是否已选择过规划卡
                and self.player.planning_card_id == 0 
                # 判断主行动是否已执行
                and self.player.main_action_is_done == False
                # 判断该规划卡是否可被选择
            ):
                # 所有可用行动id: 1-7
                available_action_ids_list = []
                for id in self.game_state.setup.selected_planning_cards:
                    # 判断该规划卡是否可获取
                    if self.all_available_object_dict['planning_card'][id].check_get(self.player_id):
                        action_id = id
                        available_action_ids_list.append(action_id)
                return available_action_ids_list
            else:
                return []
                 
        def select_planning_card_action(args):

            # 标记已执行主行动
            self.player.main_action_is_done = True
            # 向玩家添加已选择的规划卡id
            self.player.planning_card_id = args
            # 获取所选规划卡效果板块
            self.all_available_object_dict['planning_card'][args].get(self.player_id)
            # 计算各地形id需要几铲才能成为原生地
            for i in range(4):
                self.terrain_id_need_shovel_times[((self.player.planning_card_id-1)-i)%7+1] = i
                self.terrain_id_need_shovel_times[((self.player.planning_card_id-1)+i)%7+1] = i  

        def check_select_faction_action() -> list:

            if (
                # 判断是否处于初始设置阶段
                self.game_state.round == 0 
                # 判断玩家是否已经选择过派系
                and self.player.faction_id == 0 
                # 判断主行动是否已执行
                and self.player.main_action_is_done == False
            ):
                # 所有可用行动id: 8-19
                available_action_ids_list = []
                for id in self.game_state.setup.selected_factions:
                    # 判断该派系是否可获取
                    if self.all_available_object_dict['faction'][id].check_get(self.player_id):
                        action_id = id + 7
                        available_action_ids_list.append(action_id)
                return available_action_ids_list
            else:
                return []
        
        def select_faction_action(args):

            # 设置主行动已执行
            self.player.main_action_is_done = True
            # 设置玩家派系id
            self.player.faction_id = args
            # 获取所选派系效果板块
            self.all_available_object_dict['faction'][args].get(self.player_id)

        def check_select_palace_tile_action() -> list:

            if (
                # 判断是否处于初始阶段
                self.game_state.round == 0 
                # 判断是否已选择过宫殿板块
                and self.player.palace_tile_id == 0 
                # 判断主行动是否已被执行
                and self.player.main_action_is_done == False
            ):
                # 所有可用行动id: 20-35
                available_action_ids_list = []
                for id in self.game_state.setup.selected_palace_tiles:
                    # 判断该宫殿板块是否可获取
                    if self.all_available_object_dict['palace_tile'][id].check_get(self.player_id):
                        action_id = id + 19
                        available_action_ids_list.append(action_id)
                return available_action_ids_list
            else:
                return []
        
        def select_palace_tile_action(args):

            # 设置主行动已执行
            self.player.main_action_is_done = True
            # 设置玩家宫殿板块
            self.player.palace_tile_id = args
            # TODO 获取与激活要区分
            # 获取所选宫殿效果板块
            self.all_available_object_dict['palace_tile'][args].get(self.player_id)

        def check_select_round_booster_action() -> list:

            if (
                # 判断是否处于初始阶段
                self.game_state.round == 0
                # 判断玩家是否已选择回合助推板
                and len(self.player.booster_ids) == 0
                # 判断主行动是否已被执行
                and self.player.main_action_is_done == False
            ):
                # 所有可用行动id: 36-45
                available_action_ids_list = []
                for id in self.game_state.setup.selected_round_boosters:
                    # 判断该回合助推板是否可获取
                    if self.all_available_object_dict['round_booster'][id].check_get(self.player_id):
                        action_id = id + 35
                        available_action_ids_list.append(action_id)
                return available_action_ids_list
            else:
                return []       
        
        def select_round_booster_action(args):

            # 设置主行动已执行
            self.player.main_action_is_done = True   
            # 设置玩家回合助推板
            self.player.booster_ids.append(args)
            # 获取所选回合助推效果板块
            self.all_available_object_dict['round_booster'][args].get(self.player_id)

        def check_pass_this_round_action() -> list:

            if (
                # 判断是否处于正式轮次
                1 <= self.game_state.round <= 6 
                # 检查主行动是否未执行
                and self.player.main_action_is_done == False
            ):
                # 判断最后一轮特殊情况     
                if self.game_state.round != 6:
                    # 所有可用行动id: 46-56
                    available_action_ids_list = []
                    for id in self.game_state.setup.selected_round_boosters:
                        # 判断该回合助推板是否可获取
                        if self.all_available_object_dict['round_booster'][id].check_get(self.player_id):
                            action_id = id + 45
                            available_action_ids_list.append(action_id)
                    return available_action_ids_list
                else:
                    return [56]
            else:
                return []

        def pass_this_round_action(args):

            # 设置主行动已执行
            self.player.main_action_is_done = True
            # 获取玩家将交还的回合助推板id
            returned_booster_id = self.player.booster_ids[-1]

            if args != 'final':
                # 设置玩家新一轮回合助推板
                self.player.booster_ids.append(args)
                # 获取所选回合助推效果板块
                self.all_available_object_dict['round_booster'][args].get(self.player_id)

            # 从将交还的回合助推板的持有者列表中移除玩家id，即标记为未被持有
            self.all_available_object_dict['round_booster'][returned_booster_id].owner_list.remove(self.player_id)

            # 执行该玩家所有略过动作效果
            for effect_function in self.player.pass_effect_list:
                effect_function(self.player_id)

            # 将该玩家id从当前回合玩家行动顺序中移除
            self.game_state.current_player_order.remove(self.player_id)
            # 将该玩家id加入当前回合跳过顺序列表
            self.game_state.pass_order.append(self.player_id)
            # 设置玩家已跳过
            self.player.ispass = True

        # 所有魔力行动列表
            all_quick_magics_actions_list = {
            1: {
                'check': [('magics',3,5),('book','all','any',1)],
                'effect': [('magics','use',5), ('book','get','any',1)]
            },
            2: {
                'check': [('magics',3,5),('meeple','all',1)], 
                'effect': [('magics','use',5), ('meeple','get',1)]
            },
            3: {
                'check': [('magics',3,3)], 
                'effect': [('magics','use',3), ('ore','get', 1)]
            }, 
            4: {
                'check': [('magics',3,1)], 
                'effect': [('magics','use',1), ('money','get', 1)]
            },                  
            5: {
                'check': [('magics',2,2)], 
                'effect': [('magics','boom',1)]
            },
            6: {
                'check': [('book','self','any',1)], 
                'effect': [('book','use','any',1), ('money','get',1)]
            },
            7: {
                'check': [('meeple','self',1)], 
                'effect': [('meeple','use',1), ('ore','get',1)]
            }, 
            8: {
                'check': [('ore',1,)], 
                'effect': [('ore','use',1), ('money','get',1)]
            }
        }

        def check_quick_magics_action() -> list:
            # 魔力行动检查参数字典
            check_quick_magics_actions_args_dict: dict[int,list[tuple]] = {
                1: [('magics',3,5),('book','all','any',1)],
                2: [('magics',3,5),('meeple','all',1)],
                3: [('magics',3,3)],
                4: [('magics',3,1)],                 
                5: [('magics',2,2)],
                6: [('book','self','any',1)],
                7: [('meeple','self',1)], 
                8: [('ore',1,)],
            }

            if (
                # 确保不在初始阶段
                self.game_state.round != 0 
                # 确保玩家没有跳过
                and self.player.ispass == False
            ):
                # 所有可用行动id: 57-65
                available_action_ids_list = []
                for id in range(1,9):
                    # 检查该行动是否可执行
                    if self.game_state.check(self.player_id, check_quick_magics_actions_args_dict[id]):
                        action_id = id + 56
                        available_action_ids_list.append(action_id)

                if (
                    # 判断主行动是否已完成
                    self.player.main_action_is_done == True 
                ):
                    # 如果已完成主行动，则允许跳过快速行动
                    available_action_ids_list.append(65)
                return available_action_ids_list
            else:
                return []
        
        def quick_magics_action(args):

            if args == 'pass':
                # 设置玩家选择跳过
                self.player.ispass = True
            else:
                # 魔力行动执行参数字典
                execute_quick_magics_actions_args_dict: dict[int,list[tuple]] = {
                    1: [('magics','use',5), ('book','get','any',1)],
                    2: [('magics','use',5), ('meeple','get',1)],
                    3: [('magics','use',3), ('ore','get', 1)], 
                    4: [('magics','use',1), ('money','get', 1)],                  
                    5: [('magics','boom',1)],
                    6: [('book','use','any',1), ('money','get',1)],
                    7: [('meeple','use',1), ('ore','get',1)],
                    8: [('ore','use',1), ('money','get',1)],
                }
                # 获取玩家选择的快速魔力行动的参数
                action_args = execute_quick_magics_actions_args_dict[args]
                # 执行调整该行动影响
                self.game_state.adjust(self.player_id, action_args)

        def check_improve_navigation_level_action() -> list:

            if (
                # 判断不处于初始阶段
                self.game_state.round != 0
                # 判断主要行动是否未完成
                and self.player.main_action_is_done == False
                # 判断是否可执行该调整
                and self.player.navigation_level < 3
                # 判断是否可支付该花费
                and self.game_state.check(
                    self.player_id, 
                    [
                        ('meeple', 'self', 1), 
                        ('money', 4)
                    ]
                )
            ):
                # 所有可用行动id: 66
                return [66]
            else:
                return []

        def improve_navigation_level_action(args):

            # 设置主行动已执行
            self.player.main_action_is_done = True     
            # 支付提升航行等级花费
            self.game_state.adjust(
                self.player_id, 
                [
                    ('meeple', 'use', 1),
                    ('money', 'use', 4)
                ]
            )  
            # 执行提升航行等级动作
            self.player.navigation_level += 1
            # 查询本次提升奖励
            reward = []
            if self.player.planning_card_id == 3:
                match self.player.navigation_level:
                    case 2:
                        reward.append(('score', 'get', 'board', 3))
                    case 3:
                        reward.append(('book', 'get', 'any', 2))
            else:
                match self.player.navigation_level:
                    case 1:
                        reward.append(('score', 'get', 'board', 2))
                    case 2:
                        reward.append(('book', 'get', 'any', 2))
                    case 3:
                        reward.append(('score', 'get', 'board', 4))
            # 获取本次提升奖励
            self.game_state.adjust(self.player_id, reward)
            # 更新可抵达坐标
            self.game_state.update_controlled_and_reachable_map_ids(self.player_id, 'all')

        def check_improve_shovel_level_action() -> list:
            
            if (
                # 判断不处于初始阶段
                self.game_state.round != 0
                # 判断主要行动是否未完成
                and self.player.main_action_is_done == False
                # 判断是否可执行该调整
                and self.player.shovel_level > 1
                # 判断是否可支付该花费
                and self.game_state.check(
                    self.player_id, 
                    [
                        ('meeple', 'self', 1), 
                        ('ore', 1),
                        ('money', 5 if self.player.planning_card_id != 1 else 1)
                    ]
                )
            ):
                # 所有可用行动id: 67
                return [67]
            else:
                return []
        
        def improve_shovel_level_action(args):

            # 设置主行动已执行
            self.player.main_action_is_done = True     
            # 支付提升铲子等级花费
            self.game_state.adjust(
                self.player_id, 
                [
                    ('meeple', 'use', 1),
                    ('ore', 'use', 1),
                    ('money', 'use', 5 if self.player.planning_card_id != 1 else 1)
                ]
            )
            # 执行提升铲子等级动作
            self.player.shovel_level -= 1
            # 查询本次提升奖励
            reward = []
            match self.player.shovel_level:
                case 2:
                    reward.append(('book', 'get', 'any', 2))
                case 1:
                    reward.append(('score', 'get', 'board', 6))
            # 获取本次提升奖励
            self.game_state.adjust(self.player_id, reward)

        def check_insert_meeple_action() -> list:

            if (
                # 判断不处于初始阶段
                self.game_state.round != 0
                # 判断主要行动是否未完成
                and self.player.main_action_is_done == False
                # 判断是否可支付该花费
                and self.game_state.check(self.player_id, [('meeple', 'self', 1)])
            ):
                # 所有可用行动id: 68-71
                available_action_ids_list = []

                for i, typ in enumerate(['bank', 'law', 'engineering', 'medical']):

                    if self.game_state.check(self.player_id, [('tracks', typ)]):
                        available_action_ids_list.append(68+i)

                return available_action_ids_list
            else:
                return []
        
        def insert_meeple_action(args):

            # 设置主行动已执行
            self.player.main_action_is_done = True
            # 支付该花费并获取奖励
            self.game_state.adjust(self.player_id, [('meeple', 'climb', args)])
        
        def check_select_book_action(mode) -> list:

            # 所有可用行动id: 72-79
            available_action_ids_list = []   

            match mode:
                case 'use':
                    for id, typ in enumerate(['bank', 'law', 'engineering', 'medical']):
                        if self.player.resources[f'{typ}_book'] > 0:
                            available_action_ids_list.append(72+id)

                    return available_action_ids_list

                case 'get':
                    for id, typ in enumerate(['bank', 'law', 'engineering', 'medical']):
                        if self.game_state.setup.current_global_books[f'{typ}_book'] > 0:
                            available_action_ids_list.append(76+id)

            raise ValueError(f'select_book不存在{mode}行动参数')
        
        def select_book_action(args):

            self.game_state.adjust(self.player_id, [('book', *args)])

        def check_select_track_action() -> list:
            
            # 所有可用行动id: 80-83
            available_action_ids_list = []

            for id, typ in enumerate(['bank', 'law', 'engineering', 'medical']):
                match self.player.tracks[typ]:
                    case 7:
                        if self.player.tracks_over_7_amount < self.player.citys_amount:
                            available_action_ids_list.append(80+id) 
                    case 11:
                        if self.game_state.display_board_state.science_tracks[typ]['is_crowned'] == False:
                            available_action_ids_list.append(80+id)
                    case 12:
                        pass
                    case x if 0 <= x < 7 or 8 <= x < 11:
                        available_action_ids_list.append(80+id)
                    case _:
                        raise ValueError(f'{typ}轨道异常')
                            
            return available_action_ids_list
        
        def select_track_action(args):

            self.game_state.adjust(self.player_id, [('tracks', args)])
        
        def check_select_position_action(mode, args = tuple()) -> list:

            # 所有可用行动id: 84-164
            available_action_ids_list = []

            # 坐标-行动id反查表
            pos_to_action_id = [
                [1,0,2,3,4,5,6,0,7,8,9,10,0],
                [11,0,0,12,13,14,15,0,16,17,18,0,19],
                [20,21,22,0,23,24,25,0,0,26,0,0,27],
                [28,29,30,0,31,32,0,33,0,0,34,35,36],
                [37,38,39,40,0,0,0,41,42,43,44,45,46],
                [47,0,0,0,48,49,0,50,51,0,52,53,54],
                [55,0,56,57,0,58,59,0,0,0,0,0,0],
                [0,60,61,0,62,63,64,65,66,67,68,69,0],
                [70,71,72,0,73,74,75,76,77,78,79,80,81]
                ]
            
            match mode:
                case 'anywhere': 
                    # 从全部地块中遍历
                    for action_id in range(84,165):
                        i,j = self.all_detailed_actions[action_id]['args']
                        match self.game_state.map_board_state.map_grid[i][j]:
                            case [terrain, -1, 0, _, _] if terrain in args:
                                available_action_ids_list.append(action_id)
                case 'reachable':
                    # 从玩家可抵地块集合中遍历
                    for i,j in self.player.reachable_map_ids:
                        match self.game_state.map_board_state.map_grid[i][j]:
                            case [terrain, -1, 0, _, _] if terrain in args:
                                action_id = 83 + pos_to_action_id[i][j]
                                available_action_ids_list.append(action_id)
                case 'controlled':
                    # 从玩家控制地块集合中遍历
                    to_upgrade_building_id, neighbor_or_not = args
                    # 判断是否是建侧楼的特殊情况
                    if to_upgrade_building_id != 8:
                        # 遍历控制列表
                        for i,j in self.player.controlled_map_ids:
                            match self.game_state.map_board_state.map_grid[i][j]:
                                # 当被遍历到的控制地块上的当前建筑对象为需升级建筑时
                                case [_, _, to_upgrade_building_id, _, _]:
                                    # 如果需升级建筑为车间
                                    if to_upgrade_building_id == 1:
                                        # 判断可否支持无邻居建造
                                        if neighbor_or_not == 'alone_or_neighbor':
                                            # 如果支持，则无条件遍历所有控制地块，将其上为车间的行动id加入可用列表
                                            action_id = 83 + pos_to_action_id[i][j]
                                            available_action_ids_list.append(action_id)
                                        
                                        elif neighbor_or_not == 'neighbor':
                                            # 如果不支持，则还需遍历当前控制地块的相邻地块
                                            direction = [(-1,i%2-1),(-1,i%2),(0,-1),(0,1),(1,i%2-1),(1,i%2)]
                                            for dx, dy in direction:
                                                new_i, new_j = i+dx, j+dy
                                                if 0 <= new_i <= 8 and 0 <= new_j <= 12:
                                                    # 获取相邻地块的控制者id
                                                    controlled_id = self.game_state.map_board_state.map_grid[new_i][new_j][1]
                                                    # 如果控制者为其他派系玩家
                                                    if controlled_id != -1 and controlled_id != self.player_id:
                                                        # 则将当前控制地块的行动id加入可用列表,并跳出后续相邻地块的遍历
                                                        action_id = 83 + pos_to_action_id[i][j]
                                                        available_action_ids_list.append(action_id)
                                                        break
                                    # 如果不是车间
                                    else:
                                        action_id = 83 + pos_to_action_id[i][j]
                                        available_action_ids_list.append(action_id)
                    # 如果需要建造的为侧楼
                    else:
                        for i,j in self.player.controlled_map_ids:
                            match self.game_state.map_board_state.map_grid[i][j]:
                                case [_, _, _, 0, _]:
                                    action_id = 83 + pos_to_action_id[i][j]
                                    available_action_ids_list.append(action_id)
                case _:
                    pass
            return available_action_ids_list

        def select_position_action(args):

            self.player.choice_position = args

        def check_setup_build_action() -> list:
            if (
                # 判断是否处于初始阶段
                self.game_state.round == 0
                # 判断初始轮抽是否已完成
                and self.game_state.setup_choice_is_completed == True
                # 判断主行动是否已被执行
                and self.player.main_action_is_done == False
            ):
                # 所有可用行动id: 165-167
                available_action_ids_list = [165]
                
                match self.player.faction_id:
                    case 8:
                        return [166]
                    case 10:
                        if self.player.buildings[1] >= 8 and self.player.buildings[6] > 0:
                            return [165, 167]
                        elif self.player.buildings[1] == 7:
                            return [167]
                        else:
                            return [165]
                    case _:
                        return available_action_ids_list 
            else:
                return []
            
        def setup_build_action(args):

            # 设置主行动已执行
            self.player.main_action_is_done = True
            # 立即选择位置
            self.game_state.invoke_immediate_aciton(self.player_id, ('select_position', 'anywhere', set([self.player.planning_card_id])))
            # 建造
            self.game_state.adjust(self.player_id, [('building', *args)])

        def check_shovel_and_build_action() -> list:

            if (
                # 判断是否处于正式阶段
                self.game_state.round != 0
                # 判断主行动是否已被执行
                and self.player.main_action_is_done == False
            ):
                # 所有可用行动id: 168-174
                available_action_ids_list = []
                # 遍历查找最大支持铲i下再建造车间的花销，得到i
                for i in range(4):
                    if not self.game_state.check(self.player_id, [('money',2), ('ore',1+i*self.player.shovel_level),('building',1)]):
                        max_shovel_times_for_build = i-1
                        break
                else:
                    max_shovel_times_for_build = 3
                # 遍历查找最大支持铲i下单不建造的花销，得到i
                for i in range(1,4):
                    if not self.game_state.check(self.player_id, [('ore', i*self.player.shovel_level)]):
                        max_shovel_times_for_only_shovel = i-1
                        break
                else:
                    max_shovel_times_for_only_shovel = 3

                # 创建可抵达范围内地形需要几铲才能成为原生地的集合
                reachable_terrain_need_shovel_times_typs = set()

                # 遍历可抵达范围坐标
                for i,j in self.player.reachable_map_ids.copy():
                    match self.game_state.map_board_state.map_grid[i][j]:
                        case [terrain, controller, _, _, _]:
                            # 如果该地块已被控制，则从可抵达范围列表中移除
                            if controller != -1:
                                self.player.reachable_map_ids.remove((i,j))
                            else:
                                # 否则将其需要几铲才能成为原生地加入集合
                                reachable_terrain_need_shovel_times_typs.add(self.terrain_id_need_shovel_times[terrain])
                                # 如果0-3铲四种情况已经凑齐，则跳出循环
                                if len(reachable_terrain_need_shovel_times_typs) == 4:
                                    break

                # 如果可抵地块中铲成原生地所需的最小次数 小于等于 最大可支持建造车间前铲的次数，则允许该行动：将一个地块铲成原生地（如需）并建造一个车间
                if min(reachable_terrain_need_shovel_times_typs) <= max_shovel_times_for_build:
                    available_action_ids_list.append(168+max_shovel_times_for_build)
                # 可抵地块中铲成原生地所需的最大次数 与 最大可支持不建造仅铲的次数 的两者小值 是最大可铲次数
                # 则允许行动：在一个可抵地块上铲 1~最大可铲次数 下但不建造（若最大可铲次数为0，则无可用行动：在一个可抵地块上铲x下但不建造）
                available_action_ids_list.extend(list(range(172,172+min(max(reachable_terrain_need_shovel_times_typs),max_shovel_times_for_only_shovel))))

                # 返回可用行动id列表
                return available_action_ids_list
            else:
                return []

        def shovel_and_build_action(args):
            
            # 设置主行动已执行
            self.player.main_action_is_done = True

            if len(args) > 1:
                # 获取铲子和建筑参数
                max_shovel_times, *build_args = args
                # 创建空可铲地形id集合
                available_terrain_ids = set()
                # 遍历各地形id所需铲次数字典
                for key, value in self.terrain_id_need_shovel_times.items():
                    # 如果需铲次数 小于等于 可铲次数，则将该地形id加入可铲地形id集合
                    if value <= max_shovel_times:
                        available_terrain_ids.add(key)
                # 立即选择位置
                self.game_state.invoke_immediate_aciton(self.player_id, ('select_position', 'reachable', available_terrain_ids))
                # 计算需执行铲次数为所选地块的地形id的需铲次数
                i,j = self.player.choice_position
                shovel_times = self.terrain_id_need_shovel_times[self.game_state.map_board_state.map_grid[i][j][0]]
                # 执行铲子行动（如有）和建造行动
                self.game_state.adjust(self.player_id, [('land', shovel_times), ('building', *build_args)])
            else:
                # 获取铲子和建筑参数
                shovel_times, *build_args = args
                # 创建空可铲地形id集合
                available_terrain_ids = set()
                # 遍历各地形id所需铲次数字典
                for key, value in self.terrain_id_need_shovel_times.items():
                    # 如果需铲次数 大于等于 可铲次数，则将该地形id加入可铲地形id集合
                    if value >= shovel_times:
                        available_terrain_ids.add(key)
                # 立即选择位置
                self.game_state.invoke_immediate_aciton(self.player_id, ('select_position', 'reachable', available_terrain_ids))
                # 执行铲子行动
                self.game_state.adjust(self.player_id, [('land', shovel_times)])

        def check_gain_magics_action(actual_num) -> list:
            
            # 所有可用行动id: 175-199
            available_action_ids_list = [174 + actual_num, 199] # 返回可实际吸取魔力点数 与 放弃吸取
            
            return available_action_ids_list

        def gain_magics_action(args):
            
            if args == 'give_up':
                pass
            else:
                self.game_state.adjust(self.player_id, [('magics', 'get', args)])

        def check_select_city_tile_action() -> list:
            
            # 所有可用行动id: 200-206
            available_action_ids_list = []
            for city_tile_id in range(1,8):

                if self.all_available_object_dict['city_tile'][city_tile_id].check_get(self.player_id):
                    available_action_ids_list.append(199 + city_tile_id)

            return available_action_ids_list
        
        def select_city_tile_action(args):
            
            # 获取该城片id
            city_tile_id = args
            # 获取该城片
            self.all_available_object_dict['city_tile'][city_tile_id].get(self.player_id)

        def check_select_ability_tile_action() -> list:
            
            # 所有可用行动id: 207-218
            available_action_ids_list = []

            for ability_tile_id in range(1,13):
                
                if self.all_available_object_dict['ability_tile'][ability_tile_id].check_get(self.player_id):
                    action_id = 206 + ability_tile_id
                    available_action_ids_list.append(action_id)

            return available_action_ids_list

        def select_ability_tile_action(args):

            # 获取该能力板块id
            ability_tile_id = args
            # 获取该能力板块
            self.all_available_object_dict['city_tile'][ability_tile_id].get(self.player_id)
            # 添加该能力板块id
            self.player.ability_tile_ids.append(ability_tile_id)

        def check_upgrade_building_action() -> list:
            if (
                # 判断是否处于正式阶段
                self.game_state.round != 0
                # 判断主行动是否已被执行
                and self.player.main_action_is_done == False
            ):
                # 所有可用行动id: 219-223
                available_action_ids_list = []
                
                # 如果玩家规划板上车间数量小于9，则意味着版图上存在车间
                if self.player.buildings[1] < 9: 
                    # 检查无邻居条件下是否能支付花费
                    if self.game_state.check(self.player_id, [('building', 2), ('ore', 2), ('money', 6)]):
                        available_action_ids_list.append(220)
                    # 若不能，则检查有邻居情况下是否能支付花费
                    elif self.game_state.check(self.player_id, [('building', 2), ('ore', 2), ('money', 3)]):
                        # 若能，则遍历控制坐标集合
                        for i,j in self.player.controlled_map_ids:
                            # 获取该控制地块上建筑id
                            post_upgrade_building_id = self.game_state.map_board_state.map_grid[new_i][new_j][2]
                            # 如果该建筑为车间
                            if post_upgrade_building_id == 1:
                                direction = [(-1,i%2-1),(-1,i%2),(0,-1),(0,1),(1,i%2-1),(1,i%2)]
                                # 则遍历其6个相邻地块
                                for dx, dy in direction:
                                    new_i, new_j = i+dx, j+dy
                                    if 0 <= new_i <= 8 and 0 <= new_j <= 12:
                                        # 获取该相邻地块的控制者
                                        controlled_id = self.game_state.map_board_state.map_grid[new_i][new_j][1]
                                        # 如果控制者不为空且不为玩家自身（即相邻地块中存在被其他派系控制的）
                                        if controlled_id != -1 and controlled_id != self.player_id:
                                            available_action_ids_list.append(219)
                                            break
                                # 如果已确认至少有一个控制地块上建筑为车间的相邻地块上存在其他派系，则跳出遍历
                                if 219 in available_action_ids_list:
                                    break

                if self.player.buildings[2] < 4:
                    if self.game_state.check(self.player_id, [('building', 3), ('ore', 4), ('money', 6)]):
                        available_action_ids_list.append(221)
                    if self.game_state.check(self.player_id, [('building', 4), ('ore', 3), ('money', 5)]):
                        available_action_ids_list.append(222)

                if self.player.buildings[4] < 3:
                    if self.game_state.check(self.player_id, [('building', 5), ('ore', 5), ('money', 8)]):
                        available_action_ids_list.append(223)

                return available_action_ids_list
            else:
                return []
        
        def upgrade_building_action(args):
            
            # 设置主行动已执行
            self.player.main_action_is_done = True
            # 获取选择坐标参数
            pos_arg, *build_arg = args
            # 选择升级位置
            self.game_state.invoke_immediate_aciton(self.player_id, ('select_position', 'controlled', pos_arg))
            # 执行升级行动
            self.game_state.adjust(self.player_id, [('building', *build_arg)])

        check_action_dict: dict[str, Callable] = {
            'select_planning_card': check_select_planning_card_action,
            'select_faction': check_select_faction_action,
            'select_palace_tile': check_select_palace_tile_action,
            'select_round_booster': check_select_round_booster_action,
            'setup_build': check_setup_build_action,
            'pass_this_round': check_pass_this_round_action,
            'quick_magics': check_quick_magics_action,
            'improve_navigation_level': check_improve_navigation_level_action,
            'improve_shovel_level': check_improve_shovel_level_action,
            'insert_meeple': check_insert_meeple_action,
            'select_book': check_select_book_action,
            'select_track': check_select_track_action,
            'select_position': check_select_position_action,
            'shovel_and_build': check_shovel_and_build_action,
            'gain_magics': check_gain_magics_action,
            'select_city_tile': check_select_city_tile_action,
            'select_ability_tile': check_select_ability_tile_action,
            'upgrade_building': check_upgrade_building_action,
        }
        execute_action_dict: dict[str, Callable] = {
            'select_planning_card': select_planning_card_action,
            'select_faction': select_faction_action,
            'select_palace_tile': select_palace_tile_action,
            'select_round_booster': select_round_booster_action,
            'setup_build': setup_build_action,
            'pass_this_round': pass_this_round_action,
            'quick_magics': quick_magics_action,
            'improve_navigation_level': improve_navigation_level_action,
            'improve_shovel_level': improve_shovel_level_action,
            'insert_meeple': insert_meeple_action,
            'select_book': select_book_action,
            'select_track': select_track_action,
            'select_position': select_position_action,
            'shovel_and_build': shovel_and_build_action,
            'gain_magics': gain_magics_action,
            'select_city_tile': select_city_tile_action,
            'select_ability_tile': select_ability_tile_action,
            'upgrade_building': upgrade_building_action,
        }

        def action_dict(mode: str, name: str) -> Callable:
            match mode:
                case 'check':
                    return check_action_dict[name]
                case 'execute':
                    return execute_action_dict[name]
                case _:
                    raise ValueError('Invalid mode')
        
        return action_dict  
            