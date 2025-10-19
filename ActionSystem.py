from GameState import GameState
from DetailedAction import DetailedAction


class ActionSystem:
    """行动系统"""
    def __init__(self, game_state: GameState, player_id: int):
        self.game_state = game_state                                                    # 游戏状态
        self.player_id = player_id                                                      # 当前玩家ID
        self.player = game_state.players[player_id]                                     # 当前玩家
        self.all_detailed_actions = DetailedAction().all_detailed_actions               # 所有具体行动                             
        self.immediate_action_need_to_be_executed_list = []                             # 待执行立即行动列表
        self.all_effect_object_dict = self.game_state.effect_object.all_object_dict     # 效果板块索引  

        # 动作定义
        self.actions = {
            'select_planning_card': {
                'execute': self.select_planning_card_action,
                'check': self.check_select_planning_card_action
            },
            'select_faction':{
                'execute': self.select_faction_action,
                'check': self.check_select_faction_action                
            },
            'select_palace_tile':{
                'execute': self.select_palace_tile_action,
                'check': self.check_select_palace_tile_action                
            },
            'select_round_booster':{
                'execute': self.select_round_booster_action,
                'check': self.check_select_round_booster_action
            },
            'pass_this_round': {
                'execute': self.pass_this_round_action,
                'check': self.check_pass_this_round_action
            },
            'quick_magics':{
                'execute':self.quick_magics_action,
                'check':self.check_quick_magics_action
            },
            'pass':{
                'execute': self.pass_action,
                'check': self.check_pass_action
            },
            '''
            'improve_navigation_level':{
                'execute':self,
                'check':self
            },
            ''':None
        }

    # TODO 检查效果板块函数

    def get_available_actions(self) -> list:

        available_action_ids = []
        
        for id, data in self.all_detailed_actions.items():
            if self.actions[data['action']]['check'](data['args']):
                available_action_ids.append(id)
            
        return available_action_ids
    
    def execute_action(self, action_id) -> list:
        
        action_name = self.all_detailed_actions[action_id]['action']
        action_arg = self.all_detailed_actions[action_id]['args']

        # 执行主要行动（含快速行动）并返回立即行动列表
        immediate_action_list = self.actions[action_name]['execute'](action_arg)
        
        # 如有立即行动
        if immediate_action_list:
            # 则将其返回
            return immediate_action_list
        
        return []
    
    def is_next_action_exist(self) -> bool:
        
        if (
            # 当主行动未执行时
            self.player.main_action_is_done == False
            # 或玩家未选择跳过回合且有可选快速魔力行动时
            or (
                self.player.ispass == False
                and any(self.actions[self.all_detailed_actions[id]['action']]['check'](self.all_detailed_actions[id]['args']) for id in range(36,50))
            )
        ):
            
            return True
        return False

    # TODO 立即行动
    def execute_immediate_action(self, immediate_action_id):

        pass

    def reset_action_state(self):

        # 重置是否已执行主要行动标记
        self.player.main_action_is_done = False
        # 重置是否已选择跳过标记
        self.player.ispass = False

    def check_select_planning_card_action(self, args) -> bool:
        """检查选择规划卡动作是否合法"""

        selected_planning_card_id = self.game_state.setup.available_planning_cards[args]
    
        if (
            # 判断是否为可选回合
            self.game_state.round == 0 
            # 判断该玩家是否已选择过规划卡
            and self.player.planning_card_id == 0 
            # 判断主行动是否已执行
            and self.player.main_action_is_done == False
            # 判断该规划卡是否可被选择
            and self.all_effect_object_dict['planning_card'][selected_planning_card_id].check_get(self.player_id)
        ):

            return True
        return False
        
    def select_planning_card_action(self, args):

        # 标记已执行主行动
        self.player.main_action_is_done = True
        # 获取选择的规划卡id
        selected_planning_card_id = self.game_state.setup.available_planning_cards[args]
        # 向玩家添加已选择的规划卡id
        self.player.planning_card_id = selected_planning_card_id
        # 向已选择的规划卡列表中添加已选择的规划卡id
        self.all_effect_object_dict['planning_card'][selected_planning_card_id].owner_list.append(self.player_id)
        # 获取所选规划卡效果板块的立即执行效果
        immediate_effect = self.all_effect_object_dict['planning_card'][selected_planning_card_id](self.player_id).immediate_effect()
        # 执行立即执行效果
        self.game_state.adjust(self.player_id, immediate_effect)

    def check_select_faction_action(self, args) -> bool:

        selected_faction_id = self.game_state.setup.selected_factions[args]

        if (
            # 判断是否处于初始设置阶段
            self.game_state.round == 0 
            # 判断玩家是否已经选择过派系
            and self.player.faction_id == 0 
            # 判断主行动是否已执行
            and self.player.main_action_is_done == False
            # 检测行动参数是否合法
            and args <= self.game_state.num_players
            # 判断该派系是否未被选择
            and self.all_effect_object_dict['faction'][selected_faction_id].check_get(self.player_id)
        ):

            return True
        return False
    
    def select_faction_action(self, args):

        # 设置主行动已执行
        self.player.main_action_is_done = True
        # 获取玩家选择的派系id
        selected_faction_id = self.game_state.setup.selected_factions[args]
        # 设置玩家派系id
        self.player.faction_id = selected_faction_id
        # 添加派系已选择列表
        self.all_effect_object_dict['faction'][selected_faction_id].owner_list.append(self.player_id)
        # 获取所选派系的立即执行效果
        immediate_effect = self.all_effect_object_dict['faction'][selected_faction_id](self.player_id).immediate_effect()
        # 执行立即执行效果
        self.game_state.adjust(self.player_id, immediate_effect)

    def check_select_palace_tile_action(self, args) -> bool:

        selected_palace_tile_id = self.game_state.setup.available_palace_tiles[args]

        if (
            # 判断是否处于初始阶段
            self.game_state.round == 0 
            # 判断是否已选择过宫殿板块
            and self.player.palace_tile_id == 0 
            # 判断主行动是否已被执行
            and self.player.main_action_is_done == False
            # 判断行动参数是否合法
            and args <= self.game_state.num_players
            # 判断该宫殿板块是否未被选择
            and self.all_effect_object_dict['palace_tile'][selected_palace_tile_id].check_get(self.player_id)
        ):

            return True
        return False
    
    def select_palace_tile_action(self, args):

        # 设置主行动已执行
        self.player.main_action_is_done = True
        # 获取玩家选择的宫殿板块id
        selected_palace_tile_id = self.game_state.setup.available_palace_tiles[args]
        # 设置玩家宫殿板块
        self.player.palace_tile_id = selected_palace_tile_id
        # 添加到已选择的宫殿板块列表中
        self.all_effect_object_dict['palace_tile'][selected_palace_tile_id].owner_list.append(self.player_id)
        # 获取所选宫殿板块的立即执行效果
        immediate_effect = self.all_effect_object_dict['palace_tile'][selected_palace_tile_id](self.player_id).immediate_effect()
        # 执行立即执行效果
        self.game_state.adjust(self.player_id, immediate_effect)

    def check_select_round_booster_action(self, args) -> bool:

        selected_booster_id = self.game_state.setup.available_round_boosters[args]

        if (
            # 判断是否处于初始阶段
            self.game_state.round == 0
            # 判断玩家是否已选择回合助推板
            and len(self.player.booster_ids) == 0
            # 判断主行动是否已被执行
            and self.player.main_action_is_done == False
            # 判断该行动参数是否合法
            and args <= self.game_state.num_players + 2
            # 检车该回合助推板是否未被选择
            and self.all_effect_object_dict['round_booster'][selected_booster_id].check_get(self.player_id)
        ):

            return True
        return False        
    
    def select_round_booster_action(self, args):

        # 设置主行动已执行
        self.player.main_action_is_done = True
        # 获取玩家选择回合助推板id
        selected_booster_id = self.game_state.setup.available_round_boosters[args]      
        # 设置玩家回合助推板
        self.player.booster_ids.append(selected_booster_id)
        # 添加到已选择回合助推板列表中
        self.all_effect_object_dict['round_booster'][selected_booster_id].owner_list.append(self.player_id)
        # 获取所选派系的立即执行效果
        immediate_effect = self.all_effect_object_dict['round_booster'][selected_booster_id](self.player_id).immediate_effect()
        # 执行立即执行效果
        self.game_state.adjust(self.player_id, immediate_effect)

    def check_pass_this_round_action(self, args) -> bool:

        selected_booster_id = self.game_state.setup.available_round_boosters[args]

        if (
            # 判断是否处于正式轮次
            1 <= self.game_state.round <= 6 
            # 检查主行动是否未执行
            and self.player.main_action_is_done == False
            # 检查行动参数是否合法
            and args <= self.game_state.num_players + 2
            # 判断最后一轮特殊情况
            and (
                (args != -1 and self.game_state.round != 6 and self.all_effect_object_dict['round_booster'][selected_booster_id].check_get(self.player_id))
                or
                (args == -1 and self.game_state.round == 6)
                )
        ):

            return True
        return False

    def pass_this_round_action(self, args):

        # 设置主行动已执行
        self.player.main_action_is_done = True
        # 获取玩家选择的回合助推板id
        selected_booster_id = self.game_state.setup.available_round_boosters[args]
        # 获取玩家将交还的回合助推板id
        returned_booster_id = self.player.booster_ids[-1]
        # 设置玩家新一轮回合助推板
        self.player.booster_ids.append(selected_booster_id)
        # 向将选择的回合助推板的持有者列表中添加玩家id，即标记为已被持有
        self.all_effect_object_dict['round_booster'][selected_booster_id].owner_list.append(self.player_id)
        # 获取获得回合助推板时的立即效果
        immediate_effect = self.all_effect_object_dict['round_booster'][selected_booster_id].immediate_effect()
        # 执行立即效果
        self.game_state.adjust(self.player_id,immediate_effect)
        # 从将交还的回合助推板的持有者列表中移除玩家id，即标记为未被持有
        self.all_effect_object_dict['round_booster'][returned_booster_id].owner_list.remove(self.player_id)
        # TODO 获取略过回合时的效果

        # TODO 执行略过回合效果

        # 将该玩家id从当前回合玩家行动顺序中移除
        self.game_state.current_player_order.remove(self.player_id)
        # 将该玩家id加入当前回合跳过顺序列表
        self.game_state.pass_order.append(self.player_id)
        # 设置玩家已跳过
        self.player.ispass = True

    def check_quick_magics_action(self, args) -> bool:
        
        # 所有魔力行动列表
        self.all_quick_magics_actions_list = {
            1: {
                'check': [('magics',(3,5)),('book',('all','bank',1))],
                'effect': [('magics',('use',5)), ('book',('get','bank',1))]
            },    
            2: {
                'check': [('magics',(3,5)),('book',('all','law',1))], 
                'effect': [('magics',('use',5)), ('book',('get','law',1))]
            },
            3: {
                'check': [('magics',(3,5)),('book',('all','engineering',1))], 
                'effect': [('magics',('use',5)), ('book',('get','engineering',1))]
            },
            4: {
                'check': [('magics',(3,5)),('book',('all','medical',1))], 
                'effect': [('magics',('use',5)), ('book',('get','medical',1))]
            },
            5: {
                'check': [('magics',(3,5)),('meeple',('all',1))], 
                'effect': [('magics',('use',5)), ('meeple',('get',1))]
            },
            6: {
                'check': [('magics',(3,3))], 
                'effect': [('magics',('use',3)), ('ore',('get', 1))]
            }, 
            7: {
                'check': [('magics',(3,1))], 
                'effect': [('magics',('use',1)), ('money',('get', 1))]
            },                  
            8: {
                'check': [('magics',(2,2))], 
                'effect': [('magics',('boom',1))]
            },
            9: {
                'check': [('book',('self','bank',1))], 
                'effect': [('book',('use','bank',1)), ('money',('get',1))]
            },
            10: {
                'check': [('book',('self','law',1))], 
                'effect': [('book',('use','law',1)), ('money',('get',1))]
            },
            11: {
                'check': [('book',('self','engineering',1))], 
                'effect': [('book',('use','engineering',1)), ('money',('get',1))]
            },
            12: {
                'check': [('book',('self','medical',1))], 
                'effect': [('book',('use','medical',1)), ('money',('get',1))]
            },
            13: {
                'check': [('meeple',('self',1))], 
                'effect': [('meeple',('use',1)), ('ore',('get',1))]
            }, 
            14: {
                'check': [('ore',(1,))], 
                'effect': [('ore',('use',1)), ('money',('get',1))]
            }
        }

        if (
            # 确保不在初始阶段
            self.game_state.round != 0 
            # 确保玩家没有跳过
            and self.player.ispass == False
            # 检查该行动是否可执行
            and self.game_state.check(self.player_id, self.all_quick_magics_actions_list[args]['check'])
        ):

            return True
        return False
    
    def quick_magics_action(self, args):

        # 获取玩家选择的快速魔力行动的参数
        action_args = self.all_quick_magics_actions_list[args]
        # 执行调整该行动影响
        self.game_state.adjust(self.player_id, action_args['effect'])

    
    def check_pass_action(self, args) -> bool:

        if (
            # 判断主行动是否已完成
            self.player.main_action_is_done == True 
            # 判断玩家是否未跳过
            and self.player.ispass == False
        ):

            return True
        return False
    
    def pass_action(self, args):
        
        # 设置玩家选择跳过
        self.ispass = True

    def check_improve_navigation_level_action(self, args):

        if (
            # 判断不处于初始阶段
            self.game_state.round != 0
            # 判断主要行动是否未完成
            and self.player.main_action_is_done == False
            # 判断是否可执行该调整 
            and self.game_state.check(self.player_id, [('navigation',tuple())])
        ):
            
            return True
        return False

    def improve_navigation_level_action(self, args):

        # 设置主行动已执行
        self.player.main_action_is_done = True     
        # 执行提升航行等级动作
        immediate_action = self.game_state.adjust(self.player_id, [('navigation',tuple())])  

        return immediate_action

    


