from GameState import GameStateBase

class AllEffectObject:

    class EffectObject:
        """效果对象抽象基类"""

        max_owner = 1
        additional_action_name = 'Effect_Object_Base'

        def __init__(self, game_state: GameStateBase) -> None:
            self.game_state = game_state
            self.owner_list = []
            self.immediate_effect = []
            self.income_effect = []
            self.round_end_effect = []
            self.pass_effect = []
            self.setup_effect = []
            self.additional_action_is_done = [False] * game_state.num_players
        
        # 检查是否可获取
        def check_get(self, player_id: int) -> bool:
            if player_id in self.owner_list or len(self.owner_list) >= self.max_owner:
                return False
            if not self.game_state.check(player_id, self.cost_check()):
                return False
            return True
        
        # 获取代价检查
        def cost_check(self, player_id = -1) -> list:
            return [] 
        
        # 立即执行方法
        def execute_immediate_effect(self, executed_player_id):
            self.game_state.adjust(executed_player_id, self.immediate_effect)
        # 回合收入方法
        def execute_income_effect(self, executed_player_id):
            self.game_state.adjust(executed_player_id, self.income_effect)
        # 回合结束方法
        def execute_round_end_effect(self, executed_player_id):
            # 重置每回合一次附加行动已执行标记
            self.additional_action_is_done = [False] * self.game_state.num_players
            # 执行回合结束效果
            self.game_state.adjust(executed_player_id, self.round_end_effect)
        # 略过回合方法
        def execute_pass_effect(self, executed_player_id):
            self.game_state.adjust(executed_player_id, self.pass_effect)
        # 初始设置方法
        def execute_setup_effect(self, executed_player_id):
            self.game_state.adjust(executed_player_id, self.setup_effect)
        # 额外行动方法
        def additional_action(self, mode, player_id, args = tuple()):
            pass
        
        # 当获取时
        def get(self, got_player_id):
            self.owner_list.append(got_player_id)
            self.execute_immediate_effect(got_player_id)
            self.game_state.players[got_player_id].income_effect_list.append(self.execute_income_effect)
            self.game_state.players[got_player_id].pass_effect_list.append(self.execute_pass_effect)
            self.game_state.players[got_player_id].round_end_effect_list.append(self.execute_round_end_effect)
            self.game_state.players[got_player_id].setup_effect_list.append(self.execute_setup_effect)  
            self.game_state.players[got_player_id].additional_actions_dict[self.additional_action_name] = self.additional_action

        # 当激活时
        def activate(self, executed_player_id):    
            pass
        def round_end(self):
            pass

    class PlanningCard(EffectObject):
        def execute_income_effect(self, executed_player_id):
            '''回合收入效果: 规划卡 (即个人板面) 建筑收入'''
            buildings = self.game_state.players[executed_player_id].buildings
            self.income_effect.extend([
                ('ore', 'get', 10-buildings[1] if buildings[1]>=5 else 9-buildings[1]),
                ('money', 'get', 2*(4-buildings[2])),
                ('magics', 'get', 4-buildings[2] if buildings[2]>=2 else 2*(4-buildings[2])-2), 
                ('meeple', 'get', 3-buildings[4] + 1-buildings[5]) 
            ])
            super().execute_income_effect(executed_player_id)

    class Faction(EffectObject):
        pass

    class PalaceTile(EffectObject):
        # 当获取时
        def get(self, got_player_id):
            self.owner_list.append(got_player_id)
        
        # 当激活时
        def activate(self, executed_player_id):
            self.execute_immediate_effect(executed_player_id)
            self.game_state.players[executed_player_id].income_effect_list.append(self.execute_income_effect)
            self.game_state.players[executed_player_id].pass_effect_list.append(self.execute_pass_effect)
            self.game_state.players[executed_player_id].round_end_effect_list.append(self.execute_round_end_effect)
            self.game_state.players[executed_player_id].setup_effect_list.append(self.execute_setup_effect) 

    class RoundBooster(EffectObject):
        
        # TODO 还回逻辑有大问题

        # 当回合结束时
        def round_end(self):
            if not self.owner_list:
                self.immediate_effect.extend([
                    ('money', 'get', 1),
                ])
            super().round_end()

        # 当获取时
        def get(self, got_player_id):
            super().get(got_player_id)
            # 清空回合结束产生的因未被获取的金钱加成
            self.immediate_effect.clear()

    class AbilityTile(EffectObject):
        
        max_owner = 4
        typ = 0
        num_book = 0

        def execute_immediate_effect(self, executed_player_id):
            self.immediate_effect.insert(0, ('book', 'get', self.typ, self.num_book))
            self.immediate_effect.insert(0, ('tracks', self.typ, 3 - self.num_book))
            super().execute_immediate_effect(executed_player_id)

    class ScienceTile(EffectObject):
        
        # 检查是否可获取
        def check_get(self, player_id: int) -> bool:
            if player_id in self.owner_list or len(self.owner_list) >= self.max_owner:
                return False
            if not self.game_state.check(player_id, self.cost_check(player_id)):
                return False
            return True
        
        need_typ_list = [0,0,0,0]

        # 获取代价检查
        def cost_check(self, player_id = -1) -> list:
            check_list = []
            check_list.append(('book', 'self', 'any', 5))
            for id, typ in enumerate(['bank', 'law', 'engineering', 'medical']):
                if self.need_typ_list[id] > 0:
                    check_list.append(('book', 'self', typ, self.need_typ_list[id]))
            if self.game_state.players[player_id].is_got_palace == False:
                check_list.append(('money', 5))
            return check_list

    class RoundScoring(EffectObject):
        pass
        
    class FinalScoring(EffectObject):
        pass
            
    class BookAction(EffectObject):
        
        # 当回合结束时
        def execute_round_end_effect(self, executed_player_id):
            # 清空控制者列表
            self.owner_list.clear()
            super().execute_round_end_effect(executed_player_id)

    
    class CityTile(EffectObject):

        max_owner = 3
        # 同一玩家可重复获取
        def check_get(self, player_id: int) -> bool:
            if len(self.owner_list) >= self.max_owner:
                return False
            return True
        
        def execute_immediate_effect(self, executed_player_id):
            self.game_state.players[executed_player_id].citys_amount += 1
            super().execute_immediate_effect(executed_player_id)

    class MagicsAction(EffectObject):
        
        # 当回合结束时
        def execute_round_end_effect(self, executed_player_id):
            # 清空控制者列表
            self.owner_list.clear()
            super().execute_round_end_effect(executed_player_id)

    class PlainPlanningCard(PlanningCard):
        '''行动效果：减少升级铲子花费'''
        # 写在check_improve_shovel_level_action过程中了
        pass

    class SwampPlanningCard(PlanningCard):
        
        def execute_immediate_effect(self, executed_player_id):
            '''立即效果: 获取1米宝+2魔力'''
            self.immediate_effect.extend([
                ('meeple','get',1), 
                ('magics','get',2), 
            ])
            super().execute_immediate_effect(executed_player_id)

    class LakePlanningCard(PlanningCard):

        def execute_immediate_effect(self, executed_player_id):
            '''立即效果: 免费提升1航行'''
            self.game_state.players[executed_player_id].navigation_level += 1
        
    class ForestPlanningCard(PlanningCard):

        def execute_immediate_effect(self, executed_player_id):              
            '''立即效果: 获取1魔力+各轨道推1格'''
            self.immediate_effect.extend([              
                ('magics','get',1), 
                ('tracks','bank',1), 
                ('tracks','law',1), 
                ('tracks','engineering',1),
                ('tracks','medical',1)
            ])
            super().execute_immediate_effect(executed_player_id)
        
    class MountainPlanningCard(PlanningCard):
        
        def execute_income_effect(self, executed_player_id):
            '''收入阶段: 收入额外2块+第一个工会多收入1块'''
            self.income_effect.extend([
                ('money', 'get', 2),
                ('money', 'get', min(1, 4-self.game_state.players[executed_player_id].buildings[2]))
            ])
            super().execute_income_effect(executed_player_id)
                
    class WastelandPlanningCard(PlanningCard):

        def execute_setup_effect(self, executed_player_id):
            '''初始设置阶段: 获取任意1书'''
            self.setup_effect.extend([ 
                ('book','get','any',1), 
            ])
            super().execute_setup_effect(executed_player_id)

        def execute_immediate_effect(self, executed_player_id):
            '''立即效果: 获取1矿'''
            self.immediate_effect.extend([
                ('ore','get',1)
            ])
            super().execute_immediate_effect(executed_player_id)

            # TODO 第二项发明少付1书

    class DesertPlanningCard(PlanningCard):

        def execute_setup_effect(self, executed_player_id):
            '''初始设置阶段: 在初始建筑摆放完毕后立即一铲不可建房'''
            # 立即选择位置
            self.game_state.invoke_immediate_aciton(executed_player_id, ('select_position', 'reachable', ('shovel', 1)))
            self.setup_effect.extend([
                ('land', 1)
            ])
            super().execute_setup_effect(executed_player_id)

    class BlessedFaction(Faction):

        def execute_immediate_effect(self, executed_player_id):
            '''立即效果: 各轨道推一格'''
            self.immediate_effect.extend([
                ('tracks','bank',1), 
                ('tracks','law',1), 
                ('tracks','engineering',1),
                ('tracks','medical',1)
            ])
            super().execute_immediate_effect(executed_player_id)
        # TODO 轮次计分板效果写到过程中

    class FelinesFaction(Faction):

        def execute_immediate_effect(self, executed_player_id):
            '''立即效果: 银行、医学轨道推一格'''
            self.immediate_effect.extend([
                ('tracks','bank',1), 
                ('tracks','medical',1)
            ])
            super().execute_immediate_effect(executed_player_id)
            
        '''行动效果: 当建城时, 任意轨道推一格执行3次 + 获取1书'''
        # TODO 猫人行动效果

    class GoblinsFaction(Faction):

        def execute_immediate_effect(self, executed_player_id):
            '''立即效果: 银行、工程轨道推一格 + 获取1矿'''
            self.immediate_effect.extend([
                ('tracks','bank',1), 
                ('tracks','engineering',1),
                ('ore','get',1)
            ])
            super().execute_immediate_effect(executed_player_id)

        '''行动效果: 每用一铲获得2块钱'''
        # TODO 哥布林行动效果

    class IllusionistsFaction(Faction):

        def execute_immediate_effect(self, executed_player_id):
            '''立即效果: 医学轨道推两格'''
            self.immediate_effect.extend([
                ('tracks','medical',2)
            ])
            super().execute_immediate_effect(executed_player_id)
        
        '''行动效果: 每次执行魔力行动时, 少花费一点魔力并获得板面分数 (1分, 5人局2分)'''
        # TODO 幻术师行动效果

    class InventorsFaction(Faction):

        # TODO 未知错误 未触发选择能力板块
        def execute_setup_effect(self, executed_player_id):
            '''初始设置阶段: 获取任一能力板块'''
            self.game_state.invoke_immediate_aciton(executed_player_id, ('select_ability_tile',))
            super().execute_setup_effect(executed_player_id)

    class LizardsFaction(Faction):

        def execute_setup_effect(self, executed_player_id):
            '''初始设置阶段: 任意轨道推一格执行两次'''
            self.setup_effect.extend([
                ('tracks','any',2)
            ])
            super().execute_setup_effect(executed_player_id)

        '''行动效果: 当建城时, 立即免费一铲 + 免费建造一个车间 (无需在刚刚铲的地块上)'''
        # TODO 蜥蜴人行动效果

    class MolesFaction(Faction):

        def execute_immediate_effect(self, executed_player_id):
            '''立即效果: 工程轨道推两格'''
            self.immediate_effect.extend([
                ('tracks','engineering',2)
            ])
            super().execute_immediate_effect(executed_player_id)
        
        '''行动效果: 当执行地形改造并/或建造车间时, 可支付1矿跨越一个地形执行 (终局计分视为可抵达,即使无剩余矿), 并获得4版面分数'''
        '''附加可用行动: 支付1矿, 建造1座桥梁, 连接两侧建筑, 视为相邻'''
        # TODO 鼹鼠行动效果和附加可用行动

    class MonksFaction(Faction):

        def execute_immediate_effect(self, executed_player_id):
            '''立即效果: 法律轨道推一格'''
            self.immediate_effect.extend([
                ('tracks','law',1)
            ])
            super().execute_immediate_effect(executed_player_id)

        '''初始设置阶段: 取消摆放两个工会，而是摆放一个大学作为初始建筑'''
        # 写成check_setup_building_action中了

    class NavigatorsFaction(Faction):

        def execute_immediate_effect(self, executed_player_id):
            '''立即效果: 法律轨道推三格'''
            self.immediate_effect.extend([
                ('tracks','law',3)
            ])
            super().execute_immediate_effect(executed_player_id)

        '''行动效果: 当工会建造在河边时, 获得2版面分数'''
        # TODO 航海家行动效果

    class OmarFaction(Faction):

        def execute_immediate_effect(self, executed_player_id):
            '''立即效果: 银行、工程轨道推一格 + 获取一中立塔楼'''
            self.immediate_effect.extend([
                ('tracks','bank',1), 
                ('tracks','engineering',1)
            ])
            self.game_state.players[executed_player_id].buildings[6] += 1
            super().execute_immediate_effect(executed_player_id)
            
        '''初始设置阶段: 可多摆放一个中立塔楼作为初始建筑'''
        # 写成check_setup_building_action中了

        def execute_income_effect(self, executed_player_id):
            '''回合收入阶段: 获得2魔力 + 2块钱'''
            self.income_effect.extend([
                ('magics','get',2),
                ('money','get',2)
            ])
            super().execute_income_effect(executed_player_id)

    class PhilosophersFaction(Faction):

        def execute_immediate_effect(self, executed_player_id):
            '''立即效果: 银行轨道推两格'''
            self.immediate_effect.extend([
                ('tracks','bank',2)
            ])
            super().execute_immediate_effect(executed_player_id)

        '''行动效果: 获取能力板块时, 多获得对应学科的书1本'''
        # TODO 哲学家行动效果

        additional_action_name = 'additional_action_philosophers_faction'
        
        def additional_action(self, mode, player_id, args=tuple()):
            '''每回合一次附加行动: 获取1书'''
            match mode:
                case 'check':
                    if (
                        # 判断不处于初始阶段
                        self.game_state.round != 0
                        # 判断主要行动是否未完成
                        and self.game_state.players[player_id].main_action_is_done == False
                        # 判断每回合一次附加行动是否未执行
                        and self.additional_action_is_done[player_id] ==  False
                    ):
                        return [289]
                    else:
                        return []
                    
                case 'execute':

                    # 设置主行动已执行
                    self.game_state.players[player_id].main_action_is_done = True
                    # 设置每回合一次附加行动已执行
                    self.additional_action_is_done[player_id] = True
                    # 获取奖励
                    self.game_state.adjust(player_id, [('book', 'get', 'any', 1)])

    class PsychicsFaction(Faction):

        def execute_immediate_effect(self, executed_player_id):
            '''立即效果: 银行、医学轨道推一格 + 获取1矿'''
            self.immediate_effect.extend([
                ('tracks','bank',1), 
                ('tracks','medical',1),
                ('ore','get',1)
            ])
            super().execute_immediate_effect(executed_player_id)

        additional_action_name = 'additional_action_psychics_faction'
        
        def additional_action(self, mode, player_id, args=tuple()):
            '''每回合一次附加行动: 转5点魔力, 并立即进行下一动'''
            match mode:
                case 'check':
                    if (
                        # 判断不处于初始阶段
                        self.game_state.round != 0
                        # 判断主要行动是否未完成
                        and self.game_state.players[player_id].main_action_is_done == False
                        # 判断每回合一次附加行动是否未执行
                        and self.additional_action_is_done[player_id] ==  False
                    ):
                        return [290]
                    else:
                        return []
                    
                case 'execute':

                    # 不设置主行动执行
                    # 设置每回合一次附加行动已执行
                    self.additional_action_is_done[player_id] = True
                    # 获取奖励
                    self.game_state.adjust(player_id, [('magics', 'get', 5)])

    class PalaceTile1(PalaceTile):
        
        def execute_income_effect(self, executed_player_id):
            '''收入效果: 获得5魔力'''
            self.income_effect.extend([
                ('magics','get', 5)
            ])
            super().execute_income_effect(executed_player_id)

        additional_action_name = 'additional_action_palace_tile_1'
        
        def additional_action(self, mode, player_id, args=tuple()):
            '''每回合一次附加行动: 获得2矿'''
            match mode:
                case 'check':
                    if (
                        # 判断不处于初始阶段
                        self.game_state.round != 0
                        # 判断主要行动是否未完成
                        and self.game_state.players[player_id].main_action_is_done == False
                        # 判断每回合一次附加行动是否未执行
                        and self.additional_action_is_done[player_id] ==  False
                    ):
                        return [291]
                    else:
                        return []
                    
                case 'execute':

                    # 设置主行动已执行
                    self.game_state.players[player_id].main_action_is_done = True
                    # 设置每回合一次附加行动已执行
                    self.additional_action_is_done[player_id] = True
                    # 获取奖励
                    self.game_state.adjust(player_id, [('ore', 'get', 2)])

    class PalaceTile2(PalaceTile):
        
        additional_action_name = 'additional_action_palace_tile_2'
        
        def additional_action(self, mode, player_id, args=tuple()):
            '''每回合一次附加行动: 立即2铲并可选建造'''
            match mode:
                case 'check':
                    if (
                        # 判断不处于初始阶段
                        self.game_state.round != 0
                        # 判断主要行动是否未完成
                        and self.game_state.players[player_id].main_action_is_done == False
                        # 判断每回合一次附加行动是否未执行
                        and self.additional_action_is_done[player_id] ==  False
                    ):
                        return [292]
                    else:
                        return []
                    
                case 'execute':

                    # 设置主行动已执行
                    self.game_state.players[player_id].main_action_is_done = True
                    # 设置每回合一次附加行动已执行
                    self.additional_action_is_done[player_id] = True
                    # 获取奖励
                    self.game_state.adjust(player_id, [('spade', 2)])

    class PalaceTile3(PalaceTile):
        
        def execute_income_effect(self, executed_player_id):
            '''收入效果: 获得2魔力'''
            self.income_effect.extend([
                ('magics','get', 2)
            ])
            super().execute_income_effect(executed_player_id)

        additional_action_name = 'additional_action_palace_tile_3'
        
        def additional_action(self, mode, player_id, args=tuple()):
            '''每回合一次附加行动: 将1个学院降级为工会，并获得3分1矿'''
            match mode:
                case 'check':
                    if (
                        # 判断不处于初始阶段
                        self.game_state.round != 0
                        # 判断主要行动是否未完成
                        and self.game_state.players[player_id].main_action_is_done == False
                        # 判断每回合一次附加行动是否未执行
                        and self.additional_action_is_done[player_id] ==  False
                        # 检查是否还有工会
                        and self.game_state.players[player_id].buildings[2] > 0
                        # 检查是否有学院已被建造
                        and self.game_state.players[player_id].buildings[4] < 3
                    ):
                        return [293]
                    else:
                        return []
                    
                case 'execute':

                    # 设置主行动已执行
                    self.game_state.players[player_id].main_action_is_done = True
                    # 设置每回合一次附加行动已执行
                    self.additional_action_is_done[player_id] = True
                    # 选择降级位置
                    self.game_state.invoke_immediate_aciton(player_id, ('select_position', 'controlled', (4, None)))
                    # 执行降级行动并获取奖励
                    self.game_state.adjust(player_id, [
                        ('building', 'degrade', 2, False), 
                        ('score', 'get', 'board', 3), 
                        ('ore', 'get', 1)
                    ])

    class PalaceTile4(PalaceTile):
        
        def execute_income_effect(self, executed_player_id):
            '''收入效果: 获得2魔力'''
            self.income_effect.extend([
                ('magics','get', 2)
            ])
            super().execute_income_effect(executed_player_id)

        additional_action_name = 'additional_action_palace_tile_4'
        
        def additional_action(self, mode, player_id, args=tuple()):
            '''每回合一次附加行动: 将1个车间升级为工会'''
            match mode:
                case 'check':
                    if (
                        # 判断不处于初始阶段
                        self.game_state.round != 0
                        # 判断主要行动是否未完成
                        and self.game_state.players[player_id].main_action_is_done == False
                        # 判断每回合一次附加行动是否未执行
                        and self.additional_action_is_done[player_id] ==  False
                        # 检查是否还有工会
                        and self.game_state.players[player_id].buildings[2] > 0
                        # 检查是否有车间已被建造
                        and self.game_state.players[player_id].buildings[4] < 9
                    ):
                        return [294]
                    else:
                        return []
                    
                case 'execute':

                    # 设置主行动已执行
                    self.game_state.players[player_id].main_action_is_done = True
                    # 设置每回合一次附加行动已执行
                    self.additional_action_is_done[player_id] = True
                    # 选择升级位置
                    self.game_state.invoke_immediate_aciton(player_id, ('select_position', 'controlled', (1, 'alone_or_neighbor')))
                    # 执行升级行动
                    self.game_state.adjust(player_id, [('building', 'upgrade_special', 2, False)])

    class PalaceTile5(PalaceTile):
        
        def execute_income_effect(self, executed_player_id):
            '''收入效果: 获得4魔力'''
            self.income_effect.extend([
                ('magics','get', 4)
            ])
            super().execute_income_effect(executed_player_id)

        def execute_immediate_effect(self, executed_player_id):
            '''立即效果: 获得1能力板块'''
            self.game_state.invoke_immediate_aciton(executed_player_id, ('select_ability_tile',))
            super().execute_immediate_effect(executed_player_id)

    class PalaceTile6(PalaceTile):
        
        def execute_income_effect(self, executed_player_id):
            '''收入效果: 获得2魔力 + 1书'''
            self.income_effect.extend([
                ('magics','get', 4),
                ('book', 'get', 'any', 1)
            ])
            super().execute_income_effect(executed_player_id)

        additional_action_name = 'additional_action_palace_tile_6'
        
        def additional_action(self, mode, player_id, args=tuple()):
            '''每回合一次附加行动: 获得2轨'''
            match mode:
                case 'check':
                    if (
                        # 判断不处于初始阶段
                        self.game_state.round != 0
                        # 判断主要行动是否未完成
                        and self.game_state.players[player_id].main_action_is_done == False
                        # 检测该玩家每回合一次的附加行动是否已执行
                        and self.additional_action_is_done[player_id] == False
                    ):
                        return [295]
                    else:
                        return []
                    
                case 'execute':

                    # 设置主行动已执行
                    self.game_state.players[player_id].main_action_is_done = True
                    # 设置每回合一次附加行动已执行
                    self.additional_action_is_done[player_id] = True
                    # 获取奖励
                    self.game_state.adjust(player_id, [('tracks', 'any', 2)])        

    class PalaceTile7(PalaceTile):
        
        def execute_income_effect(self, executed_player_id):
            '''收入效果: 获得4魔力'''
            self.income_effect.extend([
                ('magics', 'get', 4)
            ])
            super().execute_income_effect(executed_player_id)

        def execute_pass_effect(self, executed_player_id):
            '''略过效果: 每1学院获得1分'''
            building_nums = (
                self.game_state.players[executed_player_id].buildings[4] 
                + self.game_state.players[executed_player_id].buildings[12]
            )
            self.pass_effect.extend([
                ('score', 'get', 'board', 3 * building_nums)
            ])
            super().execute_pass_effect(executed_player_id)

    class PalaceTile8(PalaceTile):
        
        def execute_income_effect(self, executed_player_id):
            '''收入效果: 获得2块钱 + 1矿 + 2魔力'''
            self.income_effect.extend([
                ('money', 'get', 2),
                ('ore', 'get', 1),
                ('magics', 'get', 2)
            ])
            super().execute_income_effect(executed_player_id)
        
        # TODO 涉及建城效果

    class PalaceTile9(PalaceTile):

        def execute_income_effect(self, executed_player_id):
            '''收入效果: 获得1米宝'''
            self.income_effect.extend([
                ('meeple', 'get', 1)
            ])
            super().execute_income_effect(executed_player_id)

        # TODO 涉及选择位置行动     

    class PalaceTile10(PalaceTile):
        
        def execute_income_effect(self, executed_player_id):
            '''收入效果: 获得6块钱'''
            self.income_effect.extend([
                ('money', 'get', 6)
            ])
            super().execute_income_effect(executed_player_id)

        def execute_immediate_effect(self, executed_player_id):
            '''立即效果: 获得12转魔 + 2书'''
            self.immediate_effect.extend([
                ('magics', 'get', 12),
                ('book', 'get', 'any', 2)
            ])
            super().execute_immediate_effect(executed_player_id)

    class PalaceTile11(PalaceTile):
        
        def execute_income_effect(self, executed_player_id):
            '''收入效果: 获得1矿'''
            self.income_effect.extend([
                ('ore', 'get', 1)
            ])
            super().execute_income_effect(executed_player_id)

        def execute_immediate_effect(self, executed_player_id):
            '''立即效果: 获得1城片'''
            self.game_state.invoke_immediate_aciton(executed_player_id, ('select_city_tile',))
            super().execute_immediate_effect(executed_player_id)

    class PalaceTile12(PalaceTile):
        
        def execute_income_effect(self, executed_player_id):
            '''收入效果: 获得8转魔'''
            self.income_effect.extend([
                ('magics', 'get', 8)
            ])
            super().execute_income_effect(executed_player_id)
        
        # TODO 涉及建造的行动效果

    class PalaceTile13(PalaceTile):
        
        additional_action_name = 'additional_action_palace_tile_13'
        
        def additional_action(self, mode, player_id, args=tuple()):
            '''每回合一次附加行动: 获取3块钱 + 1书'''
            match mode:
                case 'check':
                    if (
                        # 判断不处于初始阶段
                        self.game_state.round != 0
                        # 判断主要行动是否未完成
                        and self.game_state.players[player_id].main_action_is_done == False
                        # 判断每回合一次附加行动是否未执行
                        and self.additional_action_is_done[player_id] ==  False
                    ):
                        return [296]
                    else:
                        return []
                    
                case 'execute':

                    # 设置主行动已执行
                    self.game_state.players[player_id].main_action_is_done = True
                    # 设置每回合一次附加行动已执行
                    self.additional_action_is_done[player_id] = True
                    # 获取奖励
                    self.game_state.adjust(player_id, [
                        ('money', 'get', 3),
                        ('book', 'get', 'any', 1)
                    ])
                    
        # TODO 涉及建造的行动效果

    class PalaceTile14(PalaceTile):
        
        def execute_income_effect(self, executed_player_id):
            '''收入效果: 获得6转魔'''
            self.income_effect.extend([
                ('magics', 'get', 6)
            ])
            super().execute_income_effect(executed_player_id)

        # TODO 涉及建城检查效果

        def execute_immediate_effect(self, executed_player_id):
            '''立即效果: 升2级航海'''
            self.immediate_effect.extend([
                ('navigation',),
                ('navigation',)
            ])
            super().execute_immediate_effect(executed_player_id)

    class PalaceTile15(PalaceTile):
        
        def execute_income_effect(self, executed_player_id):
            '''收入效果: 获得6转魔'''
            self.income_effect.extend([
                ('magics', 'get', 6)
            ])
            super().execute_income_effect(executed_player_id)

        def execute_immediate_effect(self, executed_player_id):
            '''立即效果: 获得立即2铲（可建造） + 2书 + 立即建造2桥'''
            self.immediate_effect.extend([
                ('spade', 2),
                ('book', 'get', 'any', 2)
            ])
            for i in range(2):
                if self.game_state.check(executed_player_id, [('bridge',)]):
                    self.game_state.adjust(executed_player_id, [('bridge',)])
                else:
                    break
            super().execute_immediate_effect(executed_player_id)

    class PalaceTile16(PalaceTile):
        
        def execute_income_effect(self, executed_player_id):
            '''收入效果: 获得2转魔 + 1书'''
            self.income_effect.extend([
                ('magics', 'get', 2),
                ('book', 'get', 'any', 1)
            ])
            super().execute_income_effect(executed_player_id)
        
        # TODO 涉及建造行动效果

    class RoundBooster1(RoundBooster):
        
        def execute_immediate_effect(self, executed_player_id):
            '''收入效果: 获得临时1航行'''
            self.game_state.players[executed_player_id].temp_navigation = True
            super().execute_immediate_effect(executed_player_id)
        
        # TODO 涉及建造行动效果
        # TODO 涉及略过效果

    class RoundBooster2(RoundBooster):
        
        def execute_income_effect(self, executed_player_id):
            '''收入效果: 获得1矿'''
            self.income_effect.extend([
                ('ore', 'get', 1),
            ])
            super().execute_income_effect(executed_player_id)

        def execute_pass_effect(self, executed_player_id):
            building_nums = (
                self.game_state.players[executed_player_id].buildings[3]
                + self.game_state.players[executed_player_id].buildings[5]
                + self.game_state.players[executed_player_id].buildings[11]
                + self.game_state.players[executed_player_id].buildings[13]
            )
            self.pass_effect.extend([
                ('score', 'get', building_nums)
            ])
            super().execute_pass_effect(executed_player_id)

    class RoundBooster3(RoundBooster):

        def execute_income_effect(self, executed_player_id):
            '''收入效果: 获取2矿'''
            self.income_effect.extend([
                ('ore', 'get', 2)
            ])
            super().execute_income_effect(executed_player_id)
        
        additional_action_name = 'additional_action_round_booster_3'
        
        def additional_action(self, mode, player_id, args=tuple()):
            '''每回合一次附加行动: 获取2轨'''
            match mode:
                case 'check':
                    if (
                        # 判断不处于初始阶段
                        self.game_state.round != 0
                        # 判断主要行动是否未完成
                        and self.game_state.players[player_id].main_action_is_done == False
                        # 判断每回合一次附加行动是否未执行
                        and self.additional_action_is_done[player_id] ==  False
                    ):
                        return [297]
                    else:
                        return []
                    
                case 'execute':

                    # 设置主行动已执行
                    self.game_state.players[player_id].main_action_is_done = True
                    # 设置每回合一次附加行动已执行
                    self.additional_action_is_done[player_id] = True
                    # 获取奖励
                    self.game_state.adjust(player_id, [
                        ('tracks', 'any', 2)
                    ])

    class RoundBooster4(RoundBooster):
        
        def execute_income_effect(self, executed_player_id):
            '''收入效果: 获得1米宝'''
            self.income_effect.extend([
                ('meeple', 'get', 1)
            ])
            super().execute_income_effect(executed_player_id)

        # TODO 爬轨行动效果

    class RoundBooster5(RoundBooster):
        
        additional_action_name = 'additional_action_round_booster_5'
        
        def additional_action(self, mode, player_id, args=tuple()):
            '''每回合一次附加行动: 获取1铲'''
            match mode:
                case 'check':
                    if (
                        # 判断不处于初始阶段
                        self.game_state.round != 0
                        # 判断主要行动是否未完成
                        and self.game_state.players[player_id].main_action_is_done == False
                        # 判断每回合一次附加行动是否未执行
                        and self.additional_action_is_done[player_id] ==  False
                    ):
                        return [298]
                    else:
                        return []
                    
                case 'execute':

                    # 设置主行动已执行
                    self.game_state.players[player_id].main_action_is_done = True
                    # 设置每回合一次附加行动已执行
                    self.additional_action_is_done[player_id] = True
                    # 获取奖励
                    self.game_state.adjust(player_id, [
                        ('spade', 1)
                    ])
        
        def execute_income_effect(self, executed_player_id):
            '''收入效果: 获得1书'''
            self.income_effect.extend([
                ('book', 'get', 'any', 1)
            ])
            super().execute_income_effect(executed_player_id)

    class RoundBooster6(RoundBooster):
        
        def execute_income_effect(self, executed_player_id):
            '''收入效果: 获得4块钱'''
            self.income_effect.extend([
                ('money', 'get', 4)
            ])
            super().execute_income_effect(executed_player_id)
        
        def execute_pass_effect(self, executed_player_id):
            '''略过效果: 每1学院获得1轨'''
            building_nums = (
                self.game_state.players[executed_player_id].buildings[4] 
                + self.game_state.players[executed_player_id].buildings[12]
            )
            self.pass_effect.extend([
                ('tracks', 'any', building_nums)
            ])
            super().execute_pass_effect(executed_player_id)

    class RoundBooster7(RoundBooster):
        
        def execute_income_effect(self, executed_player_id):
            '''收入效果: 获得3转魔'''
            self.income_effect.extend([
                ('magics', 'get', 3)
            ])
            super().execute_income_effect(executed_player_id)

        # TODO 涉及建筑建造行动效果

    class RoundBooster8(RoundBooster):

        additional_action_name = 'additional_action_round_booster_8'
        
        def additional_action(self, mode, player_id, args=tuple()):
            '''每回合一次附加行动: 立即建造1桥'''
            match mode:
                case 'check':
                    if (
                        # 判断不处于初始阶段
                        self.game_state.round != 0
                        # 判断主要行动是否未完成
                        and self.game_state.players[player_id].main_action_is_done == False
                        # 判断每回合一次附加行动是否未执行
                        and self.additional_action_is_done[player_id] ==  False
                        # 检测是否满足建桥条件
                        and self.game_state.check(player_id, [('bridge',)])
                    ):
                        return [299]
                    else:
                        return []
                    
                case 'execute':

                    # 设置主行动已执行
                    self.game_state.players[player_id].main_action_is_done = True
                    # 设置每回合一次附加行动已执行
                    self.additional_action_is_done[player_id] = True
                    # 建造桥梁
                    self.game_state.adjust(player_id, [('bridge',)])
        
        def execute_income_effect(self, executed_player_id):
            '''收入效果: 获得1书'''
            self.income_effect.extend([
                ('book', 'get', 'any', 1)
            ])
            super().execute_income_effect(executed_player_id)

    class RoundBooster9(RoundBooster):
        
        def execute_income_effect(self, executed_player_id):
            '''收入效果: 获得4转魔 + 2块钱'''
            self.income_effect.extend([
                ('magics', 'get', 4),
                ('money', 'get', 2)
            ])
            super().execute_income_effect(executed_player_id)

    class RoundBooster10(RoundBooster):
        
        def execute_income_effect(self, executed_player_id):
            '''收入效果: 获得6块钱'''
            self.income_effect.extend([
                ('money', 'get', 6)
            ])
            super().execute_income_effect(executed_player_id)

    class AbilityTile1(AbilityTile):
        
        def execute_income_effect(self, executed_player_id):
            '''收入效果: 获得1矿 + 1轨'''
            self.income_effect.extend([
                ('ore', 'get', 1),
                ('tracks', 'get', 'any', 1)
            ])
            super().execute_income_effect(executed_player_id)

    class AbilityTile2(AbilityTile):

        def execute_income_effect(self, executed_player_id):
            '''收入效果: 获得2分 + 2块钱'''
            self.income_effect.extend([
                ('score', 'get', 'board', 3),
                ('money', 'get', 2)
            ])
            super().execute_income_effect(executed_player_id)
        
    class AbilityTile3(AbilityTile):

        def execute_income_effect(self, executed_player_id):
            '''收入效果: 获得1书 + 1魔力'''
            self.income_effect.extend([
                ('book', 'get', 'any', 1),
                ('magics', 'get', 1)
            ])
            super().execute_income_effect(executed_player_id)
        
    class AbilityTile4(AbilityTile):
        
        def execute_immediate_effect(self, executed_player_id):
            '''立即效果: 获得1矿 + 5分 + 2块钱'''
            self.immediate_effect.extend([
                ('ore', 'get', 1),
                ('score', 'get', 'board', 5),
                ('money', 'get', 2)
            ])
            super().execute_immediate_effect(executed_player_id)

    class AbilityTile5(AbilityTile):
        
        def execute_immediate_effect(self, executed_player_id):
            '''立即效果: 立即2铲并可选建造'''
            self.immediate_effect.extend([
                ('spade', 2)
            ])
            super().execute_immediate_effect(executed_player_id)

    class AbilityTile6(AbilityTile):
        
        def execute_immediate_effect(self, executed_player_id):
            '''立即效果: 获得2个侧楼'''
            self.game_state.players[executed_player_id].buildings[8] += 2  
            super().execute_immediate_effect(executed_player_id)

        additional_action_name = 'additional_action_ability_tile_6'
        
        def additional_action(self, mode, player_id, args=tuple()):
            '''附加行动: 建造1个侧楼'''
            match mode:
                case 'check':
                    if (
                        # 判断不处于初始阶段
                        self.game_state.round != 0
                        # 判断主要行动是否未完成
                        and self.game_state.players[player_id].main_action_is_done == False
                        # 检查是否还有侧楼
                        and self.game_state.players[player_id].buildings[8] > 0
                        # 存在已控制坐标
                        and self.game_state.players[player_id].controlled_map_ids
                    ):
                        return [302]
                    else:
                        return []
                    
                case 'execute':

                    # 设置主行动已执行
                    self.game_state.players[player_id].main_action_is_done = True
                    # 选择建造位置
                    self.game_state.invoke_immediate_aciton(player_id, ('select_position', 'controlled', (8, None)))
                    # 执行建造行动
                    self.game_state.adjust(player_id, [('building', 'build_annex', 8, True)])

    class AbilityTile7(AbilityTile):
        
        additional_action_name = 'additional_action_ability_tile_7'
        
        def additional_action(self, mode, player_id, args=tuple()):
            '''每回合一次附加行动: 获得4魔力'''
            match mode:
                case 'check':
                    if (
                        # 判断不处于初始阶段
                        self.game_state.round != 0
                        # 判断主要行动是否未完成
                        and self.game_state.players[player_id].main_action_is_done == False
                        # 检测该玩家每回合一次的附加行动是否已执行
                        and self.additional_action_is_done[player_id] == False
                    ):
                        return [288]
                    else:
                        return []
                    
                case 'execute':

                    # 设置主行动已执行
                    self.game_state.players[player_id].main_action_is_done = True
                    # 设置每回合一次附加行动已执行
                    self.additional_action_is_done[player_id] = True
                    # 获取奖励
                    self.game_state.adjust(player_id, [('magics', 'get', 4)])

    class AbilityTile8(AbilityTile):
        
        # TODO 行动效果
        pass

    class AbilityTile9(AbilityTile):
        
        def execute_pass_effect(self, executed_player_id):
            '''略过效果: 每一个城片获得2分'''
            self.pass_effect.extend([
                ('score', 'get', 'board', 2 * self.game_state.players[executed_player_id].citys_amount)
            ])
            super().execute_pass_effect(executed_player_id)

    class AbilityTile10(AbilityTile):
        
        # TODO 行动效果
        pass

    class AbilityTile11(AbilityTile):

        def execute_immediate_effect(self, executed_player_id):
            '''立即效果: 建造一个中立的塔楼'''
            self.immediate_effect.extend([
                ('building', 'build_neutral', 6, True),
            ])
            super().execute_immediate_effect(executed_player_id)
        
        def execute_income_effect(self, executed_player_id):
            '''收入效果: 获得2魔力 + 2块钱'''
            self.income_effect.extend([
                ('magcis', 'get', 2),
                ('money', 'get', 2)
            ])
            super().execute_income_effect(executed_player_id)

    class AbilityTile12(AbilityTile):
        
        def execute_pass_effect(self, executed_player_id):
            '''略过效果: 获得四学科轨最低值的分数'''
            self.pass_effect.extend([
                ('score', 'get', 'board', min(self.game_state.players[executed_player_id].tracks.values()))
            ])
            super().execute_pass_effect(executed_player_id)

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
        
        def cost_check(self, player_id = -1) -> list:
            return [('book', 'self', 'any', 1)]
        
        def execute_immediate_effect(self, executed_player_id):
            self.immediate_effect.extend([
                ('book', 'use', 'any', 1),
                ('magics', 'get', 5),
            ])
            super().execute_immediate_effect(executed_player_id)

    class BookAction2(BookAction):
        
        def cost_check(self, player_id = -1) -> list:
            return [('book', 'self', 'any', 1)]
        
        def execute_immediate_effect(self, executed_player_id):
            self.immediate_effect.extend([
                ('book', 'use', 'any', 1),
                ('tracks', 'any', 2),
            ])
            super().execute_immediate_effect(executed_player_id)

    class BookAction3(BookAction):
        
        def cost_check(self, player_id = -1) -> list:
            return [('book', 'self', 'any', 2)]
        
        def execute_immediate_effect(self, executed_player_id):
            self.immediate_effect.extend([
                ('book', 'use', 'any', 2),
                ('money', 'get', 6),
            ])
            super().execute_immediate_effect(executed_player_id)

    class BookAction4(BookAction):
        
        def cost_check(self, player_id = -1) -> list:
            return [('book', 'self', 'any', 2)]
        
        def execute_immediate_effect(self, executed_player_id):
            self.immediate_effect.extend([
                ('book', 'use', 'any', 2),
            ])
            super().execute_immediate_effect(executed_player_id)
            if self.game_state.check(executed_player_id, [('building',1)]):
                self.game_state.invoke_immediate_aciton(executed_player_id, ('select_position', 'controlled', (1, 'alone_or_neighbor')))
                self.game_state.adjust(executed_player_id,[('building', 'upgrade_special', 2, False)])
            
    class BookAction5(BookAction):
        
        def cost_check(self, player_id = -1) -> list:
            return [('book', 'self', 'any', 2)]
        
        def execute_immediate_effect(self, executed_player_id):
            self.immediate_effect.extend([
                ('book', 'use', 'any', 2),
                ('score', 'get', 'board', 2 * (4 - self.game_state.players[executed_player_id].buildings[2] + self.game_state.players[executed_player_id].buildings[10])),
            ])
            super().execute_immediate_effect(executed_player_id)

    class BookAction6(BookAction):
        
        def cost_check(self, player_id = -1) -> list:
            return [('book', 'self', 'any', 3)]
        
        def execute_immediate_effect(self, executed_player_id):
            self.immediate_effect.extend([
                ('book', 'use', 'any', 3),
                ('spade',3),
            ])
            super().execute_immediate_effect(executed_player_id)
    
    class CityTileBook(CityTile):

        def execute_immediate_effect(self, executed_player_id):
            self.immediate_effect.extend([
                ('book', 'get', 'any', 2),
                ('score', 'get', 'board', 5),
            ])
            super().execute_immediate_effect(executed_player_id)

    class CityTileTrack(CityTile):

        def execute_immediate_effect(self, executed_player_id):
            self.immediate_effect.extend([
                ('tracks', 'bank', 1),
                ('tracks', 'law', 1),
                ('tracks', 'engineering', 1),
                ('tracks', 'medical', 1),
                ('score', 'get', 'board', 7),
            ])
            super().execute_immediate_effect(executed_player_id)
    
    class CityTileShovel(CityTile):

        def execute_immediate_effect(self, executed_player_id):
            self.immediate_effect.extend([
                ('spade', 2),
                ('score', 'get', 'board', 5),
            ])
            super().execute_immediate_effect(executed_player_id)
    
    class CityTileMagics(CityTile):

        def execute_immediate_effect(self, executed_player_id):
            self.immediate_effect.extend([
                ('magics', 'get', 8),
                ('score', 'get', 'board', 8),
            ])
            super().execute_immediate_effect(executed_player_id)
    
    class CityTileOre(CityTile):

        def execute_immediate_effect(self, executed_player_id):
            self.immediate_effect.extend([
                ('ore', 'get', 3),
                ('score', 'get', 'board', 4),
            ])
            super().execute_immediate_effect(executed_player_id)
    
    class CityTileMeeple(CityTile):

        def execute_immediate_effect(self, executed_player_id):
            self.immediate_effect.extend([
                ('meeple', 'get', 1),
                ('score', 'get', 'board', 8),
            ])
            super().execute_immediate_effect(executed_player_id)
    
    class CityTileMoney(CityTile):
        
        def execute_immediate_effect(self, executed_player_id):
            self.immediate_effect.extend([
                ('money', 'get', 6),
                ('score', 'get', 'board', 6),
            ])
            super().execute_immediate_effect(executed_player_id)

    class MagicsActionBridge(MagicsAction):
        
        def cost_check(self, player_id = -1) -> list:
            return [('magics',3,3)]
        
        def execute_immediate_effect(self, executed_player_id):
            self.immediate_effect.extend([
                ('magics', 'use', 3),
                ('bridge',)
            ])
            super().execute_immediate_effect(executed_player_id)

    class MagicsActionMeeple(MagicsAction):
        
        def cost_check(self, player_id = -1) -> list:
            return [('magics',3,3)]
        
        def execute_immediate_effect(self, executed_player_id):
            self.immediate_effect.extend([
                ('magics','use',3),
                ('meeple','get',1)
            ])
            super().execute_immediate_effect(executed_player_id)
        
    class MagicsActionOre(MagicsAction):
        
        def cost_check(self, player_id = -1) -> list:
            return [('magics',3,4)]
        
        def execute_immediate_effect(self, executed_player_id):
            self.immediate_effect.extend([
                ('magics','use',4),
                ('ore','get', 2)
            ])
            super().execute_immediate_effect(executed_player_id)

    class MagicsActionMoney(MagicsAction):
        
        def cost_check(self, player_id = -1) -> list:
            return [('magics',3,4)]
        
        def execute_immediate_effect(self, executed_player_id):
            self.immediate_effect.extend([
                ('magics','use',4),
                ('money','get',7)
            ])
            super().execute_immediate_effect(executed_player_id)

    class MagicsActionShovel1(MagicsAction):
        
        def cost_check(self, player_id = -1) -> list:
            return [('magics',3,4)]
        
        def execute_immediate_effect(self, executed_player_id):
            self.immediate_effect.extend([
                ('magics','use',4),
                ('spade',1)
            ])
            super().execute_immediate_effect(executed_player_id)

    class MagicsActionShovel2(MagicsAction):
        
        def cost_check(self, player_id = -1) -> list:
            return [('magics',3,6)]

        def execute_immediate_effect(self, executed_player_id):
            self.immediate_effect.extend([
                ('magics','use',6),
                ('spade',2)
            ])
            super().execute_immediate_effect(executed_player_id)

    def __init__(self, game_state: GameStateBase) -> None:
        self.game_state = game_state
        self.EffectObject(game_state)
        self.all_object_dict = {
            'planning_card': {
                1: self.PlainPlanningCard,
                2: self.SwampPlanningCard,
                3: self.LakePlanningCard,
                4: self.ForestPlanningCard,
                5: self.MountainPlanningCard,
                6: self.WastelandPlanningCard,
                7: self.DesertPlanningCard
            },
            'faction': {
                1: self.BlessedFaction,
                2: self.FelinesFaction,
                3: self.GoblinsFaction,
                4: self.IllusionistsFaction,
                5: self.InventorsFaction,
                6: self.LizardsFaction,
                7: self.MolesFaction,
                8: self.MonksFaction,
                9: self.NavigatorsFaction,
                10: self.OmarFaction,
                11: self.PhilosophersFaction,
                12: self.PsychicsFaction
            },
            'palace_tile': {
                1: self.PalaceTile1,
                2: self.PalaceTile2,
                3: self.PalaceTile3,
                4: self.PalaceTile4,
                5: self.PalaceTile5,
                6: self.PalaceTile6,
                7: self.PalaceTile7,
                8: self.PalaceTile8,
                9: self.PalaceTile9,
                10: self.PalaceTile10,
                11: self.PalaceTile11,
                12: self.PalaceTile12,
                13: self.PalaceTile13,
                14: self.PalaceTile14,
                15: self.PalaceTile15,
                16: self.PalaceTile16
            },
            'round_booster': {
                1: self.RoundBooster1,
                2: self.RoundBooster2,
                3: self.RoundBooster3,
                4: self.RoundBooster4,
                5: self.RoundBooster5,
                6: self.RoundBooster6,
                7: self.RoundBooster7,
                8: self.RoundBooster8,
                9: self.RoundBooster9,
                10: self.RoundBooster10,
            },
            'ability_tile': {
                1: self.AbilityTile1,
                2: self.AbilityTile2,
                3: self.AbilityTile3,
                4: self.AbilityTile4,
                5: self.AbilityTile5,
                6: self.AbilityTile6,
                7: self.AbilityTile7,
                8: self.AbilityTile8,
                9: self.AbilityTile9,
                10: self.AbilityTile10,
                11: self.AbilityTile11,
                12: self.AbilityTile12
            },
            'science_tile': {
                1: self.ScienceTile1,
                2: self.ScienceTile2,
                3: self.ScienceTile3,
                4: self.ScienceTile4,
                5: self.ScienceTile5,
                6: self.ScienceTile6,
                7: self.ScienceTile7,
                8: self.ScienceTile8,
                9: self.ScienceTile9,
                10: self.ScienceTile10,
                11: self.ScienceTile11,
                12: self.ScienceTile12,
                13: self.ScienceTile13,
                14: self.ScienceTile14,
                15: self.ScienceTile15,
                16: self.ScienceTile16,
                17: self.ScienceTile17,
                18: self.ScienceTile18,
            },
            'round_scoring': {
                1: self.RoundScoring1,
                2: self.RoundScoring2,
                3: self.RoundScoring3,
                4: self.RoundScoring4,
                5: self.RoundScoring5,
                6: self.RoundScoring6,
                7: self.RoundScoring7,
                8: self.RoundScoring8,
                9: self.RoundScoring9,
                10:self. RoundScoring10,
                11: self.RoundScoring11,
                12: self.RoundScoring12
            },
            'final_scoring': {
                1: self.FinalScoring1,
                2: self.FinalScoring2,
                3: self.FinalScoring3,
                4: self.FinalScoring4,
            },
            'book_action': {
                1: self.BookAction1,
                2: self.BookAction2,
                3: self.BookAction3,
                4: self.BookAction4,
                5: self.BookAction5,
                6: self.BookAction6,
            },
            'city_tile': {
                1: self.CityTileBook,
                2: self.CityTileTrack,
                3: self.CityTileShovel,
                4: self.CityTileMagics,
                5: self.CityTileOre,
                6: self.CityTileMeeple,
                7: self.CityTileMoney,
            },
            'magics_action': {
                1: self.MagicsActionBridge,
                2: self.MagicsActionMeeple,
                3: self.MagicsActionOre,
                4: self.MagicsActionMoney,
                5: self.MagicsActionShovel1,
                6: self.MagicsActionShovel2,
            },
        }

        # 初始化各能力板块的获取立即效果
        for order_id, ability_tile_id in enumerate(self.game_state.setup.ability_tiles_order):
            self.all_object_dict['ability_tile'][ability_tile_id].typ = ['bank', 'law', 'engineering', 'medical'][order_id // 3]
            self.all_object_dict['ability_tile'][ability_tile_id].num_book = order_id % 3

        for order_id, science_tile_id in enumerate(self.game_state.setup.science_tiles_order):
            self.all_object_dict['science_tile'][science_tile_id].need_typ_list = self.game_state.display_board_state.tech_ability_board_spend[order_id]
            
    def create_actual_object(self,typ: str, object_id: int): 
        return self.all_object_dict[typ][object_id](self.game_state)