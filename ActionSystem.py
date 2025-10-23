from GameState import GameState
from DetailedAction import DetailedAction

class ActionSystem:
    """行动系统"""
    def __init__(self, game_state: GameState, player_id: int):
        self.game_state = game_state                                                    # 游戏状态
        self.player_id = player_id                                                      # 当前玩家ID
        self.player = game_state.players[player_id]                                     # 当前玩家
        self.all_detailed_actions = DetailedAction().all_detailed_actions               # 所有具体行动         
        self.all_available_object_dict = self.game_state.all_available_object_dict      # 效果板块索引
        
        # 动作列表
        self.actions = {
            'check': {
                'select_planning_card': self.check_select_planning_card_action,
                'select_faction': self.check_select_faction_action,
                'select_palace_tile': self.check_select_palace_tile_action,
                'select_round_booster': self.check_select_round_booster_action,
                'pass_this_round': self.check_pass_this_round_action,
                'quick_magics': self.check_quick_magics_action,
                'pass': self.check_pass_action,
                'improve_navigation_level': self.check_improve_navigation_level_action,
                'improve_shovel_level': self.check_improve_shovel_level_action
            },
            'execute' : {
                'select_planning_card': self.select_planning_card_action,
                'select_faction': self.select_faction_action,
                'select_palace_tile': self.select_palace_tile_action,
                'select_round_booster': self.select_round_booster_action,
                'pass_this_round': self.pass_this_round_action,
                'quick_magics': self.quick_magics_action,
                'pass': self.pass_action,
                'improve_navigation_level': self.improve_navigation_level_action,
                'improve_shovel_level': self.improve_shovel_level_action
            }
        }

    def get_available_actions(self) -> list:

        available_action_ids_list = []

        for action_function in self.actions['check'].values():
            available_action_ids_list.extend(action_function())
            
        return available_action_ids_list
    
    def execute_action(self, action_id):
        
        action_name = self.all_detailed_actions[action_id]['action']
        action_arg = self.all_detailed_actions[action_id]['args']

        # 执行主要行动（含快速行动）并返回立即行动列表
        self.actions['execute'][action_name](action_arg)
        
    
    def is_next_action_exist(self) -> bool:
        
        if (
            # 当主行动未执行时
            self.player.main_action_is_done == False
            # 或玩家有可选快速魔力行动时
            or self.actions['check']['quick_magics']()
        ):
            return True
        return False

    # 返回可用立即行动id列表
    def get_available_immediate_actions(self, data) -> list:

        # 计算组合数C(n,3)
        def comb3(n):
            if n < 3:
                return 0
            return n * (n-1) * (n-2) // 6

        def encode(a, b, c, num):
            # 计算a部分的偏移量: ∑_{i=0}^{a-1} C(num-i+2, 2)
            total_a = comb3(num+3) - comb3(num-a+3)
            # 计算b部分的偏移量: ∑_{j=0}^{b-1} (num-a-j+1)
            total_b = (num - a + 1) * b - b*(b-1)//2
            return total_a + total_b + c
        
        def select_books(mode: str, num: int) -> list:

            available_immediate_action_ids = []
            
            match mode:
                case 'use':

                    ava_bank = self.player.resources['bank_book']
                    ava_law = self.player.resources['law_book']
                    ava_engineering = self.player.resources['engineering_book']
                    ava_medical = self.player.resources['medical_book']

                    start_id = sum(comb3(i) for i in range(3,num+3))

                    for i in range(min(num,ava_bank)+1):
                        for j in range(min(num-i,ava_law)+1):
                            for k in range(min(num-i-j,ava_engineering)+1):
                                for l in range(min(num-i-j-k,ava_medical)+1):
                                    if i+j+k+l == num:
                                        # 所有可用立即行动id: 10000-11819
                                        action_id = 10000 + start_id + encode(i,j,k,num)
                                        available_immediate_action_ids.append(action_id)
                    if available_immediate_action_ids:
                        return available_immediate_action_ids
                    else:
                        raise ValueError(f'不存在有效书本组合，即拥有书本数量不足')

                case 'get':

                    act_num = min(num, sum(list(self.game_state.setup.current_global_books.values())))

                    ava_bank = self.game_state.setup.current_global_books['bank_book']
                    ava_law = self.game_state.setup.current_global_books['law_book']
                    ava_engineering = self.game_state.setup.current_global_books['engineering_book']
                    ava_medical = self.game_state.setup.current_global_books['medical_book']

                    start_id = sum(comb3(i) for i in range(3,act_num+3))

                    for i in range(min(act_num,ava_bank)+1):
                        for j in range(min(act_num-i,ava_law)+1):
                            for k in range(min(act_num-i-j,ava_engineering)+1):
                                for l in range(min(act_num-i-j-k,ava_medical)+1):
                                    if i+j+k+l == num:
                                        # 所有可用立即行动id: 11820-13639
                                        action_id = 10000 + start_id + encode(i,j,k,num)
                                        available_immediate_action_ids.append(action_id)
                    
                    return available_immediate_action_ids

            raise ValueError(f'select_books不存在{mode}行动参数')
        
        def select_tracks(num: int) -> list:

            def ava_max_track_amount(typ) -> list[int]:
                match self.player.tracks[typ], self.game_state.display_board_state.science_tracks[typ]['is_crowned']:
                    case x,y if x > 7 and y == True:
                        return [11]
                    case x,y if x > 7 and y == False:
                        return [12]
                    case x,y if x <= 7 and y == True:
                        return [7,11]
                    case x,y if x <= 7 and y== False:
                        return [7,12]
                return []
            
            available_immediate_action_ids = []

            for max_bank in ava_max_track_amount('bank'):
                for max_law in ava_max_track_amount('law'):
                    for max_engineering in ava_max_track_amount('engineering'):
                        for max_medical in ava_max_track_amount('medical'):

                            if sum(x>7 for x in [max_bank,max_law,max_engineering,max_medical]) > self.player.citys_amount:
                                continue

                            ava_bank = max_bank-self.player.tracks['bank']
                            ava_law = int(max_law - self.player.tracks['law'])
                            ava_engineering = int(max_engineering - self.player.tracks['engineering'])
                            ava_medical = int(max_medical - self.player.tracks['medical'])

                            act_num = min(
                                num, 
                                sum([
                                    ava_bank, 
                                    ava_law, 
                                    ava_engineering, 
                                    ava_medical
                                ])
                            )

                            start_id = sum(comb3(i) for i in range(3,act_num+3))

                            for i in range(min(act_num,ava_bank)+1):
                                for j in range(min(act_num-i,ava_law)+1):
                                    for k in range(min(act_num-i-j,ava_engineering)+1):
                                        for l in range(min(act_num-i-j-k,ava_medical)+1):
                                            if i+j+k+l == act_num:
                                                # 所有可用立即行动id: 13640-15459
                                                action_id = 13640 + start_id + encode(i,j,k,num)
                                                available_immediate_action_ids.append(action_id)
            return available_immediate_action_ids
        
        self.check_immediate_action_dict = {
            'select_books': select_books,
            'select_tracks': select_tracks
        }

        name, *args = data
        return self.check_immediate_action_dict[name](*args)

    def execute_immediate_actions(self, immediate_action_id):

        def select_books(mode: str, nums: tuple):

            bank_num, law_num, engineering_num, medical_num = nums

            self.game_state.adjust(
                self.player_id,
                [
                    ('book',mode,'bank',bank_num),
                    ('book',mode,'law',law_num),
                    ('book',mode,'engineering',engineering_num),
                    ('book',mode,'medical',medical_num),
                ]
            )

        def select_tracks(bank_num: int, law_num: int, engineering_num: int, medical_num: int):

            self.game_state.adjust( 
                self.player_id,
                [
                    ('tracks','bank',bank_num),
                    ('tracks','law',law_num),
                    ('tracks','engineering',engineering_num),
                    ('tracks','medical',medical_num),
                ]
            )

        self.execute_immediate_action_dict = {
            'select_books': select_books,
            'select_tracks': select_tracks            
        }
        immediate_action_name = self.all_detailed_actions[immediate_action_id]['action']
        immediate_action_args = self.all_detailed_actions[immediate_action_id]['args']

        self.execute_immediate_action_dict[immediate_action_name](*immediate_action_args)

    def reset_action_state(self):

        # 重置是否已执行主要行动标记
        self.player.main_action_is_done = False
        # 重置是否已选择跳过标记
        self.player.ispass = False

    # TODO 初始设置行动
    def execute_setup_action(self):

        pass

    def check_select_planning_card_action(self) -> list:
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
        
    def select_planning_card_action(self, args):

        # 标记已执行主行动
        self.player.main_action_is_done = True
        # 向玩家添加已选择的规划卡id
        self.player.planning_card_id = args
        # 获取所选规划卡效果板块
        self.all_available_object_dict['planning_card'][args].get(self.player_id)

    def check_select_faction_action(self) -> list:

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
    
    def select_faction_action(self, args):

        # 设置主行动已执行
        self.player.main_action_is_done = True
        # 设置玩家派系id
        self.player.faction_id = args
        # 获取所选派系效果板块
        self.all_available_object_dict['faction'][args].get(self.player_id)


    def check_select_palace_tile_action(self) -> list:

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
    
    def select_palace_tile_action(self, args):

        # 设置主行动已执行
        self.player.main_action_is_done = True
        # 设置玩家宫殿板块
        self.player.palace_tile_id = args
        # 获取所选宫殿效果板块
        self.all_available_object_dict['palace_tile'][args].get(self.player_id)

    def check_select_round_booster_action(self) -> list:

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
    
    def select_round_booster_action(self, args):

        # 设置主行动已执行
        self.player.main_action_is_done = True   
        # 设置玩家回合助推板
        self.player.booster_ids.append(args)
        # 获取所选回合助推效果板块
        self.all_available_object_dict['round_booster'][args].get(self.player_id)

    def check_pass_this_round_action(self) -> list:

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

    def pass_this_round_action(self, args):

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
        # 将该玩家id从当前回合玩家行动顺序中移除
        self.game_state.current_player_order.remove(self.player_id)
        # 将该玩家id加入当前回合跳过顺序列表
        self.game_state.pass_order.append(self.player_id)
        # 设置玩家已跳过
        self.player.ispass = True


    def check_quick_magics_action(self) -> list:
        
        # 所有魔力行动列表
        self.all_quick_magics_actions_list = {
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
                if self.game_state.check(self.player_id, self.all_quick_magics_actions_list[id]['check']):
                    action_id = id + 56
                    available_action_ids_list.append(action_id)
            return available_action_ids_list
        else:
            return []
    
    def quick_magics_action(self, args):

        # 获取玩家选择的快速魔力行动的参数
        action_args = self.all_quick_magics_actions_list[args]
        # 执行调整该行动影响
        self.game_state.adjust(self.player_id, action_args['effect'])

    def check_pass_action(self) -> list:

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
    
    def pass_action(self, args):
        
        # 设置玩家选择跳过
        self.player.ispass = True

    def check_improve_navigation_level_action(self) -> list:

        if (
            # 判断不处于初始阶段
            self.game_state.round != 0
            # 判断主要行动是否未完成
            and self.player.main_action_is_done == False
            # 判断是否可执行该调整 
            and self.game_state.check(self.player_id, [('navigation',)])
        ):
            # 所有可用行动id: 66
            return [66]
        else:
            return []

    def improve_navigation_level_action(self, args):

        # 设置主行动已执行
        self.player.main_action_is_done = True     
        # 执行提升航行等级动作
        self.game_state.adjust(self.player_id, [('navigation',)])  

    def check_improve_shovel_level_action(self) -> list:
        
        if (
            # 判断不处于初始阶段
            self.game_state.round != 0
            # 判断主要行动是否未完成
            and self.player.main_action_is_done == False
            # 判断是否可执行该调整 
            and self.game_state.check(self.player_id, [('shovel',)])
        ):
            # 所有可用行动id: 67
            return [67]
        else:
            return []
    
    def improve_shovel_level_action(self, args):

        # 设置主行动已执行
        self.player.main_action_is_done = True     
        # 执行提升铲子等级动作
        self.game_state.adjust(self.player_id, [('shovel',)])  


if __name__ == '__main__':
    ac = ActionSystem(GameState(3), 1)
    print()
    res = ac.get_available_immediate_actions(('select_books','get',1))
    print(res)