from GameState import GameStateBase
from DetailedAction import DetailedAction

class ActionSystem:
    """行动系统"""
    def __init__(self, game_state: GameStateBase, player_id: int):
        self.game_state = game_state                                                    # 游戏状态
        self.player_id = player_id                                                      # 当前玩家ID
        self.player = game_state.players[player_id]                                     # 当前玩家
        self.all_detailed_actions = DetailedAction().all_detailed_actions               # 所有具体行动         
        self.all_available_object_dict = self.game_state.all_available_object_dict      # 效果板块索引

        # 行动名称列表
        self.action_list = [
            'select_planning_card',
            'select_faction',
            'select_palace_tile',
            'select_round_booster',
            'setup_build',
            'pass_this_round',
            'quick_magics',
            'pass',
            'improve_navigation_level',
            'improve_shovel_level',
            'insert_meeple',
        ]

        # 立即行动名称列表
        self.immediate_action_list = [
            'select_book',
            'select_track',
            'select_position',
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

        # 执行行动（主要/快速/立即/初始）
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

    def action_dict(self, mode: str, name: str):

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
                # 所有可用行动id: 57-64
                available_action_ids_list = []
                for id in range(1,9):
                    # 检查该行动是否可执行
                    if self.game_state.check(self.player_id, check_quick_magics_actions_args_dict[id]):
                        action_id = id + 56
                        available_action_ids_list.append(action_id)
                return available_action_ids_list
            else:
                return []
        
        def quick_magics_action(args):
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

        def check_pass_action() -> list:

            if (
                # 判断主行动是否已完成
                self.player.main_action_is_done == True 
                # 判断玩家是否未跳过
                and self.player.ispass == False
            ):
                # 所有可用行动id: 65
                return [65]
            else:
                return []
        
        def pass_action(args):
            
            # 设置玩家选择跳过
            self.player.ispass = True

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

            self.game_state.adjust(self.player_id, [('track', args)])
        
        def check_select_position_action(mode) -> list:

            # 所有可用行动id: 84-164
            available_action_ids_list = []
            match mode:
                case 'anywhere': 
                    for action_id in range(84,165):
                        i,j = self.all_detailed_actions[action_id]['args']
                        match self.game_state.map_board_state.map_grid[i][j]:
                            case [self.player.planning_card_id, -1, 0, _, _]:
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
                # 所有可用行动id: 165
                available_action_ids_list = [165]
                
                match self.player.faction_id:
                    case 8:
                        self.player.main_action_is_done = True
                        return [65] # 僧侣建大学无车间，所以跳过
                    case _:
                        return available_action_ids_list 
            else:
                return []
            
        def setup_build_action(args):

            # 设置主行动已执行
            self.player.main_action_is_done = True
            # 建造
            self.game_state.adjust(self.player_id, [('building', *args)])

        check_action_dict: dict = {
            'select_planning_card': check_select_planning_card_action,
            'select_faction': check_select_faction_action,
            'select_palace_tile': check_select_palace_tile_action,
            'select_round_booster': check_select_round_booster_action,
            'setup_build': check_setup_build_action,
            'pass_this_round': check_pass_this_round_action,
            'quick_magics': check_quick_magics_action,
            'pass': check_pass_action,
            'improve_navigation_level': check_improve_navigation_level_action,
            'improve_shovel_level': check_improve_shovel_level_action,
            'insert_meeple': check_insert_meeple_action,
            'select_book': check_select_book_action,
            'select_track': check_select_track_action,
            'select_position': check_select_position_action,
        }
        execute_action_dict: dict = {
            'select_planning_card': select_planning_card_action,
            'select_faction': select_faction_action,
            'select_palace_tile': select_palace_tile_action,
            'select_round_booster': select_round_booster_action,
            'setup_build': setup_build_action,
            'pass_this_round': pass_this_round_action,
            'quick_magics': quick_magics_action,
            'pass': pass_action,
            'improve_navigation_level': improve_navigation_level_action,
            'improve_shovel_level': improve_shovel_level_action,
            'insert_meeple': insert_meeple_action,
            'select_book': select_book_action,
            'select_track': select_track_action,
            'select_position': select_position_action,
        }

        match mode:
            case 'check':
                return check_action_dict[name]
            case 'execute':
                return execute_action_dict[name]
            case _:
                raise ValueError('Invalid mode')
            
        