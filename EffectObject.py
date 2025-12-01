from GameState import GameStateBase

class AllEffectObject:

    class EffectObject:
        """效果对象抽象基类"""

        max_owner = 1
        additional_action_name = 'Effect_Object_Base'
        name_dict = {}
        id = 0

        def __init__(self, game_state: GameStateBase) -> None:
            self.game_state = game_state
            self.owner_list = []
            self.immediate_effect = []
            self.income_effect = []
            self.pass_effect = []
            self.setup_effect = []
            self.additional_action_is_done = [False] * game_state.num_players
            self.round_end_effect_args: tuple[str, int, str, int] = tuple()
        
        # 检查是否可获取
        def check_get(self, player_id: int) -> bool:
            if player_id in self.owner_list or len(self.owner_list) >= self.max_owner:
                return False
            if not self.game_state.check(player_id, self.cost(player_id)[0]):
                return False
            return True
        
        # 获取花费
        def cost(self, player_id) -> tuple[list, list]:
            return [], [] # 花费检查，花费执行
        
        # 立即执行方法
        def execute_immediate_effect(self, executed_player_id:int):
            # 执行立即效果
            spend_str, reward_str = self.game_state.adjust(executed_player_id, self.immediate_effect)
            self._print_effect('immediate', executed_player_id, spend_str, reward_str)
            # 清空本版块立即效果列表（以防多玩家获取同一板块时，后获得者重复执行效果）
            self.immediate_effect.clear()
        # 回合收入方法
        def execute_income_effect(self, executed_player_id:int):
            # 执行收入效果
            spend_str, reward_str = self.game_state.adjust(executed_player_id, self.income_effect)
            self._print_effect('income',executed_player_id, spend_str, reward_str)
            # 清空本版块收入效果列表（以防多玩家获取同一板块时，后获得者重复执行效果）
            self.income_effect.clear()
        # 略过回合方法
        def execute_pass_effect(self, executed_player_id:int):
            # 执行略过回合效果
            spend_str, reward_str = self.game_state.adjust(executed_player_id, self.pass_effect)
            self._print_effect('pass',executed_player_id, spend_str, reward_str)
            # 清空本版块略过回合效果列表（以防多玩家获取同一板块时，后获得者重复执行效果）
            self.pass_effect.clear()
        # 初始设置方法
        def execute_setup_effect(self, executed_player_id:int):
            # 执行初始设置效果
            spend_str, reward_str = self.game_state.adjust(executed_player_id, self.setup_effect)
            self._print_effect('setup',executed_player_id, spend_str, reward_str)
            # 清空初始设置效果
            self.setup_effect.clear()
        # 额外行动方法
        def additional_action(self, mode, player_id:int, args = tuple()):
            pass
        
        # 当获取时
        def get(self, got_player_id):
            # 记录该板块的拥有者
            self.owner_list.append(got_player_id)
            # 支付该板块费用
            self.game_state.adjust(got_player_id, self.cost(got_player_id)[1])
            # 执行立即效果
            self.execute_immediate_effect(got_player_id)
            # 添加收入效果
            self.game_state.players[got_player_id].income_effect_list.append(self.execute_income_effect)
            # 添加略过效果
            self.game_state.players[got_player_id].pass_effect_list.append(self.execute_pass_effect)
            # 添加初始设置效果
            self.game_state.players[got_player_id].setup_effect_list.append(self.execute_setup_effect)
            # 添加额外行动 
            self.game_state.players[got_player_id].additional_actions_dict[self.additional_action_name] = self.additional_action

        # 当激活时
        def activate(self, executed_player_id):    
            pass
        # 当回合结束时
        def round_end(self):
            # 重置每回合一次附加行动已执行标记
            self.additional_action_is_done = [False] * self.game_state.num_players
        # 当交还时
        def back(self, executed_player_id):
            pass

        def _print_effect(self, mode, executed_player_id, spend_str, reward_str):
            color_dict = {
                'immediate': 'orange',
                'setup': 'orange',
                'income': 'pink',
                'pass': 'purple',
            }
            if spend_str and reward_str:
                print_str = f"{self.name_dict[self.id]}({spend_str}) -> {reward_str}"
                self.game_state.io.output(executed_player_id+1,print_str,color=color_dict[mode])
            elif reward_str:
                print_str = f"{self.name_dict[self.id]} -> {reward_str}"
                self.game_state.io.output(executed_player_id+1,print_str,color=color_dict[mode])
            elif spend_str:
                print_str = f"{self.name_dict[self.id]}({spend_str})"
                self.game_state.io.output(executed_player_id+1,print_str,color=color_dict[mode])

    class PlanningCard(EffectObject):

        name_dict = {
            1: "平原（棕）规划卡",
            2: "沼泽（黑）规划卡",
            3: "湖泊（蓝）规划卡",
            4: "森林（绿）规划卡",
            5: "山脉（灰）规划卡",
            6: "荒地（红）规划卡",
            7: "沙漠（黄）规划卡",
        } 
        
        id = 0

        def get(self, got_player_id):
            super().get(got_player_id)
            self.game_state.io.update_player_state(got_player_id, {'planning_card': self.name_dict[self.id][:2]})

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

        def execute_immediate_effect(self, executed_player_id: int):
            self.immediate_effect.extend([
                ('money', 'get', 15),
                ('ore', 'get', 3),
            ])
            super().execute_immediate_effect(executed_player_id)

    class Faction(EffectObject):
        
        name_dict = {
            1: '神佑者',
            2: '猫人',
            3: '哥布林',
            4: '幻术师',
            5: '发明家',
            6: '蜥蜴人',
            7: '鼹鼠',
            8: '僧侣',
            9: '航海家',
            10: '奥马尔',
            11: '哲学家',
            12: '通灵师',
        }

        id = 0
        
        def get(self, got_player_id):
            super().get(got_player_id)
            self.game_state.io.update_player_state(got_player_id, {'faction': self.name_dict[self.id]})

    class PalaceTile(EffectObject):

        name_dict = {i: f"宫殿板块{i}" for i in range(1,17)}

        # 当获取时
        def get(self, got_player_id):
            self.owner_list.append(got_player_id)
        
        # 当激活时
        def activate(self, executed_player_id):
            # 执行立即效果
            self.execute_immediate_effect(executed_player_id)
            # 添加收入效果
            self.game_state.players[executed_player_id].income_effect_list.append(self.execute_income_effect)
            # 添加略过效果
            self.game_state.players[executed_player_id].pass_effect_list.append(self.execute_pass_effect)
            # 添加初始设置效果
            self.game_state.players[executed_player_id].setup_effect_list.append(self.execute_setup_effect) 
            # 添加额外行动 
            self.game_state.players[executed_player_id].additional_actions_dict[self.additional_action_name] = self.additional_action

    class RoundBooster(EffectObject):

        name_dict = {i: f"回合助推板{i}" for i in range(1,11)}
        id = 0

        # 当回合结束时
        def round_end(self):
            if not self.owner_list:
                # print(f"回合助推板{self.id} -> 获取时额外获得1块钱")
                self.immediate_effect.extend([
                    ('money', 'get', 1),
                ])
            super().round_end()

        # 当获取时
        def get(self, got_player_id):
            super().get(got_player_id)
            # 设置玩家新一轮回合助推板
            self.game_state.players[got_player_id].booster_ids.append(self.id)

        # 当交还时
        def back(self, executed_player_id):
            # 从将交还的回合助推板的持有者列表中移除玩家id，即标记为未被持有
            self.owner_list.remove(executed_player_id)
            # 执行该玩家所有略过动作效果
            for effect_function in self.game_state.players[executed_player_id].pass_effect_list.copy():
                effect_function(executed_player_id)
            # 使用函数引用和实例标识来移除
            self._remove_effect_functions(executed_player_id)
            # 移除该玩家属于回合助推板的额外行动
            if self.additional_action_name in self.game_state.players[executed_player_id].additional_actions_dict:
                self.game_state.players[executed_player_id].additional_actions_dict.pop(self.additional_action_name)
            # 将该玩家id从当前回合玩家行动顺序中移除
            self.game_state.current_player_order.remove(executed_player_id)
            # 将该玩家id加入当前回合跳过顺序列表
            self.game_state.pass_order.append(executed_player_id)

        def _remove_effect_functions(self, player_id):
            """安全移除所有属于本回合助推板的收入、略过、回合结束效果函数"""
            player = self.game_state.players[player_id]
            
            # 定义要移除的方法名
            method_names = [
                'execute_pass_effect',
                'execute_income_effect', 
                'execute_setup_effect',
            ]
            
            # 从所有效果列表中移除
            effect_lists = [
                player.pass_effect_list,
                player.income_effect_list,
                player.setup_effect_list,
            ]
            
            for method_name, effect_list in zip(method_names, effect_lists):
                # 查找并移除属于当前实例的方法
                for func in effect_list.copy():
                    if (hasattr(func, '__self__') and   # 是绑定方法
                        func.__self__ is self and       # 属于当前实例
                        func.__name__ == method_name):  # 方法名匹配
                        effect_list.remove(func)
                        # print(f"已移除 {method_name}")

    class AbilityTile(EffectObject):
        
        name_dict = {i: f"能力板块{i}" for i in range(1,13)}
        id = 0
        max_owner = 4

        def get(self, got_player_id):
            # 添加该能力板块id至玩家列表
            self.game_state.players[got_player_id].ability_tile_ids.append(self.id)
            # 计算该能力板块奖励
            order_id = self.game_state.setup.ability_tiles_order.index(self.id)
            typ = ['bank', 'law', 'engineering', 'medical'][order_id // 3]
            num_book = order_id % 3
            reward = [
                ('book', 'get', typ, num_book),
                ('tracks', typ, 3 - num_book)
            ]
            # 获取该能力板块奖励
            self.game_state.adjust(got_player_id, reward)
            # 获取能力板块行动效果
            self.game_state.action_effect(player_id=got_player_id, get_ability_tile_typ=typ)
            super().get(got_player_id)
            

    class ScienceTile(EffectObject):

        name_dict = {i: f"高科板块{i}" for i in range(1,19)}
        id = 0

        # 检查是否可获取
        def check_get(self, player_id: int) -> bool:
            # 若通用获取检查失败，则不可获取
            if super().check_get(player_id) == False: 
                return False
            # 若该玩家已拥有三个高科板块，则不可获取
            if len(self.game_state.players[player_id].science_tile_ids) >= 3:
                return False
            return True

        # 花费获取
        def cost(self, player_id):
            # 初始化花费检查列表
            check_list = []
            adjust_list = []
            # 默认需要5本书，每已拥有一高科额外需要一本
            additional_book = len(self.game_state.players[player_id].science_tile_ids)
            if (
                # 特判: 沼泽规划卡玩家获取第二个高科板块时少花额外一书效果
                self.game_state.players[player_id].planning_card_id == 6
                and additional_book == 1
            ):
                additional_book = 0
            check_list.append(('book', 'self', 'any', 5 + additional_book))
            # 获取需支付花费的书中指定类型书的类型和数量
            order_id = self.game_state.setup.science_tiles_order.index(self.id)
            need_typ_list = self.game_state.display_board_state.tech_ability_board_spend[order_id]
            for i, typ in enumerate(['bank', 'law', 'engineering', 'medical']):
                if need_typ_list[i] > 0:
                    check_list.append(('book', 'self', typ, need_typ_list[i]))
                    adjust_list.append(('book', 'use', typ, need_typ_list[i]))
            adjust_list.append(('book', 'use', 'any', 5 + additional_book - sum(need_typ_list)))
            # 检查是否已建造宫殿，若无则需额外支付5块钱
            if self.game_state.players[player_id].is_got_palace == False:
                check_list.append(('money', 5))
                adjust_list.append(('money', 'use', 5))
            # 返回花费检查和执行列表
            return check_list,adjust_list
        
        def get(self, got_player_id):
            super().get(got_player_id)
            # 添加该高科板块id至玩家列表
            self.game_state.players[got_player_id].science_tile_ids.append(self.id)
            # 获取高科板块行动效果触发
            self.game_state.action_effect(player_id=got_player_id, get_science_tile=True)

    class RoundScoring(EffectObject):
        
        name_dict = {i: f"回合计分板块{i}" for i in range(1,13)}
        id = 0

        def round_end(self):
            '''回合结束效果: 执行本回合的回合计分板块的科学奖励效果'''
            round = self.game_state.round
            if (
                # 第6回合的回合计分板块的科学奖励部分被最终得分板块覆盖
                round != 6
                # 当前回合等于其在初始设置回合计分板块中的序号时该板块才生效
                and self.id == self.game_state.setup.round_scoring_order[round - 1]
                # round == self.game_state.setup.round_scoring_order.index(self.id) + 1
            ):
                # 按下一轮次顺序进行回合结束科学奖励结算
                for player_idx in self.game_state.pass_order:
                    # 获取该板块科学奖励参数
                    reward_item, reward_num, track_typ, track_num = self.round_end_effect_args
                    # 特判派系板块是神佑者的玩家，判定时轨道数量被视为+3
                    if self.game_state.players[player_idx].faction_id == 1:
                        additional_num = 3
                    else:
                        additional_num = 0
                    # 计算奖励获取数
                    get_num = (self.game_state.players[player_idx].tracks[track_typ] + additional_num) // track_num * reward_num
                    # 生成奖励获取列表
                    match reward_item:
                        case 'book':
                            round_end_effect = [(reward_item, 'get', 'any', get_num)]
                        case 'spade':
                            round_end_effect = [('spade', get_num, False)]
                        case _:
                            round_end_effect = [(reward_item, 'get', get_num)]
                    # 获取奖励
                    self.game_state.adjust(player_idx, round_end_effect)
            return super().round_end()
        
        '''其左侧行动效果均已写入action_effect方法中'''
        # 回合计分板块的行动效果
        
    class FinalScoring(EffectObject):
        
        name_dict = {i: f"最终计分板块{i}" for i in range(1,5)}
        '''其行动效果均已写入action_effect方法中'''
            
    class BookAction(EffectObject):

        name_dict = {i: f"书行动板块{i}" for i in range(1,7)}

        # 当回合结束时
        def round_end(self):
            # 清空控制者列表
            self.owner_list.clear()
            super().round_end()

    class CityTile(EffectObject):

        name_dict = {i: f"城片板块{i}" for i in range(1,8)}
        max_owner = 3
        # 同一玩家可重复获取
        def check_get(self, player_id: int) -> bool:
            if len(self.owner_list) >= self.max_owner:
                return False
            return True
        
        def get(self, got_player_id):
            super().get(got_player_id)
            self.game_state.action_effect(player_id=got_player_id, get_city_tile=True)
            self.game_state.io.update_player_state(got_player_id, {'city_amount': self.game_state.players[got_player_id].citys_amount})
        
        def execute_immediate_effect(self, executed_player_id):
            self.game_state.players[executed_player_id].citys_amount += 1
            super().execute_immediate_effect(executed_player_id)

    class MagicsAction(EffectObject):
        
        name_dict = {i: f"魔力行动板块{i}" for i in range(1,7)}
        # 当回合结束时

        def round_end(self):
            # 清空控制者列表
            self.owner_list.clear()
            super().round_end()

    class PlainPlanningCard(PlanningCard):

        id = 1

        '''行动效果：减少升级铲子花费'''
        # 写在check_improve_shovel_level_action过程中了
        pass

    class SwampPlanningCard(PlanningCard):

        id = 2
        
        def execute_immediate_effect(self, executed_player_id):
            '''立即效果: 获取1米宝+2魔力'''
            self.immediate_effect.extend([
                ('meeple','get',1), 
                ('magics','get',2), 
            ])
            super().execute_immediate_effect(executed_player_id)

    class LakePlanningCard(PlanningCard):

        id = 3

        def execute_immediate_effect(self, executed_player_id):
            '''立即效果: 免费提升1航行'''
            self.immediate_effect.extend([
                ('navigation',),
            ])
            super().execute_immediate_effect(executed_player_id)
        
    class ForestPlanningCard(PlanningCard):

        id = 4

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

        id = 5
        
        def execute_income_effect(self, executed_player_id):
            '''收入阶段: 收入额外2块+第一个工会多收入1块'''
            self.income_effect.extend([
                ('money', 'get', 2),
                ('money', 'get', min(1, 4-self.game_state.players[executed_player_id].buildings[2]))
            ])
            super().execute_income_effect(executed_player_id)
                
    class WastelandPlanningCard(PlanningCard):

        id = 6

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

            '''行动效果：第二项发明少付1书'''
            # 已写进获取高科板块的检查获取花费中

    class DesertPlanningCard(PlanningCard):

        id = 7

        def execute_setup_effect(self, executed_player_id):
            '''初始设置阶段: 在初始建筑摆放完毕后立即一铲不可建房'''
            self.setup_effect.extend([
                ('spade', 1, False)
            ])
            super().execute_setup_effect(executed_player_id)

    class BlessedFaction(Faction):

        id = 1

        def execute_immediate_effect(self, executed_player_id):
            '''立即效果: 各轨道推一格'''
            self.immediate_effect.extend([
                ('tracks','bank',1), 
                ('tracks','law',1), 
                ('tracks','engineering',1),
                ('tracks','medical',1)
            ])
            super().execute_immediate_effect(executed_player_id)
        '''行动效果: 结算轮次计分板块的科学奖励效果时，轨道被视为额外+3'''
        # 轮次计分板效果已写到行动效果方法中

    class FelinesFaction(Faction):

        id = 2

        def execute_immediate_effect(self, executed_player_id):
            '''立即效果: 银行、医学轨道推一格'''
            self.immediate_effect.extend([
                ('tracks','bank',1), 
                ('tracks','medical',1)
            ])
            super().execute_immediate_effect(executed_player_id)
            
        '''行动效果: 当建城时, 任意轨道推一格执行3次 + 获取1书'''
        # 猫人行动效果已写入action_effect中

    class GoblinsFaction(Faction):

        id = 3

        def execute_immediate_effect(self, executed_player_id):
            '''立即效果: 银行、工程轨道推一格 + 获取1矿'''
            self.immediate_effect.extend([
                ('tracks','bank',1), 
                ('tracks','engineering',1),
                ('ore','get',1)
            ])
            super().execute_immediate_effect(executed_player_id)

        '''行动效果: 每用一铲获得2块钱'''
        # 哥布林行动效果已写入action_effect中

    class IllusionistsFaction(Faction):

        id = 4

        def execute_immediate_effect(self, executed_player_id):
            '''立即效果: 医学轨道推两格'''
            self.immediate_effect.extend([
                ('tracks','medical',2)
            ])
            super().execute_immediate_effect(executed_player_id)
        
        '''行动效果: 每次执行魔力行动时, 少花费一点魔力并获得板面分数 (1分, 5人局2分)'''
        # TODO 幻术师行动效果

    class InventorsFaction(Faction):

        id = 5

        def execute_setup_effect(self, executed_player_id):
            '''初始设置阶段: 获取任一能力板块'''
            self.setup_effect.extend([
                ('ability_tile',)
            ])
            super().execute_setup_effect(executed_player_id)

    class LizardsFaction(Faction):

        id = 6

        def execute_setup_effect(self, executed_player_id):
            '''初始设置阶段: 任意轨道推一格执行两次'''
            self.setup_effect.extend([
                ('tracks','any',2)
            ])
            super().execute_setup_effect(executed_player_id)

        '''行动效果: 当建城时, 立即免费一铲 + 免费建造一个车间 (无需在刚刚铲的地块上)'''
        # TODO 蜥蜴人行动效果

    class MolesFaction(Faction):

        id = 7

        def execute_immediate_effect(self, executed_player_id):
            '''立即效果: 工程轨道推两格'''
            self.immediate_effect.extend([
                ('tracks','engineering',2)
            ])
            super().execute_immediate_effect(executed_player_id)
        
        '''行动效果: 当执行地形改造并/或建造车间时, 可支付1矿跨越一个地形执行 (终局计分视为可抵达,即使无剩余矿), 并获得4版面分数'''
        # TODO 鼹鼠行动效果
        
        '''附加可用行动: 支付1矿, 建造1座桥梁, 连接两侧建筑, 视为相邻'''
        # TODO 附加可用行动

    class MonksFaction(Faction):

        id = 8

        def execute_immediate_effect(self, executed_player_id):
            '''立即效果: 法律轨道推一格'''
            self.immediate_effect.extend([
                ('tracks','law',1)
            ])
            super().execute_immediate_effect(executed_player_id)

        '''初始设置阶段: 取消摆放两个工会，而是摆放一个大学作为初始建筑'''
        # 写成check_setup_building_action中了

    class NavigatorsFaction(Faction):

        id = 9

        def execute_immediate_effect(self, executed_player_id):
            '''立即效果: 法律轨道推三格'''
            self.immediate_effect.extend([
                ('tracks','law',3)
            ])
            super().execute_immediate_effect(executed_player_id)

        '''行动效果: 当工会建造在河边时, 获得2版面分数'''
        # 航海家行动效果已写入action_effect中

    class OmarFaction(Faction):

        id = 10

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

        id = 11

        def execute_immediate_effect(self, executed_player_id):
            '''立即效果: 银行轨道推两格'''
            self.immediate_effect.extend([
                ('tracks','bank',2)
            ])
            super().execute_immediate_effect(executed_player_id)

        '''行动效果: 获取能力板块时, 多获得对应学科的书1本'''
        # 哲学家行动效果已写入action_effect中

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
                        return [288]
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

        id = 12

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
                        return [289]
                    else:
                        return []
                    
                case 'execute':

                    # 不设置主行动执行
                    # 设置每回合一次附加行动已执行
                    self.additional_action_is_done[player_id] = True
                    # 获取奖励
                    self.game_state.adjust(player_id, [('magics', 'get', 5)])

    class PalaceTile1(PalaceTile):

        id = 1
        
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
                        return [290]
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
        
        id = 2
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
                        return [291]
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
        
        id = 3
        
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
                        return [292]
                    else:
                        return []
                    
                case 'execute':

                    # 设置主行动已执行
                    self.game_state.players[player_id].main_action_is_done = True
                    # 设置每回合一次附加行动已执行
                    self.additional_action_is_done[player_id] = True
                    # 选择降级位置
                    if self.game_state.invoke_immediate_aciton(player_id, ('select_position', 'controlled', (4, None))): return 
                    # 执行降级行动并获取奖励
                    self.game_state.adjust(player_id, [
                        ('building', 'degrade', 2, False), 
                        ('score', 'get', 'board', 3), 
                        ('ore', 'get', 1)
                    ])

    class PalaceTile4(PalaceTile):

        id = 4
        
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
                        and self.game_state.players[player_id].buildings[1] < 9
                    ):
                        return [293]
                    else:
                        return []
                    
                case 'execute':

                    # 设置主行动已执行
                    self.game_state.players[player_id].main_action_is_done = True
                    # 设置每回合一次附加行动已执行
                    self.additional_action_is_done[player_id] = True
                    # 选择升级位置
                    if self.game_state.invoke_immediate_aciton(player_id, ('select_position', 'controlled', (1, 'alone_or_neighbor'))): return 
                    # 执行升级行动
                    self.game_state.adjust(player_id, [('building', 'upgrade_special', 2, False)])

    class PalaceTile5(PalaceTile):

        id = 5
        
        def execute_income_effect(self, executed_player_id):
            '''收入效果: 获得4魔力'''
            self.income_effect.extend([
                ('magics','get', 4)
            ])
            super().execute_income_effect(executed_player_id)

        def execute_immediate_effect(self, executed_player_id):
            '''立即效果: 获得1能力板块'''
            self.immediate_effect.extend([
                ('ability_tile',)
            ])
            super().execute_immediate_effect(executed_player_id)

    class PalaceTile6(PalaceTile):

        id = 6
        
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
                        return [294]
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

        id = 7
        
        def execute_income_effect(self, executed_player_id):
            '''收入效果: 获得4魔力'''
            self.income_effect.extend([
                ('magics', 'get', 4)
            ])
            super().execute_income_effect(executed_player_id)

        def execute_pass_effect(self, executed_player_id):
            '''略过效果: 每1学院获得1分'''
            building_nums = (
                (3 - self.game_state.players[executed_player_id].buildings[4])
                + self.game_state.players[executed_player_id].buildings[12]
            )
            self.pass_effect.extend([
                ('score', 'get', 'board', 3 * building_nums)
            ])
            super().execute_pass_effect(executed_player_id)

    class PalaceTile8(PalaceTile):

        id = 8
        
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

        id = 9

        def execute_income_effect(self, executed_player_id):
            '''收入效果: 获得1米宝'''
            self.income_effect.extend([
                ('meeple', 'get', 1)
            ])
            super().execute_income_effect(executed_player_id)

        # TODO 涉及选择位置行动     

    class PalaceTile10(PalaceTile):

        id = 10
        
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

        id = 11
        
        def execute_income_effect(self, executed_player_id):
            '''收入效果: 获得1矿'''
            self.income_effect.extend([
                ('ore', 'get', 1)
            ])
            super().execute_income_effect(executed_player_id)

        def execute_immediate_effect(self, executed_player_id):
            '''立即效果: 获得1城片'''
            self.immediate_effect.extend([
                ('ability_tile',)
            ])
            super().execute_immediate_effect(executed_player_id)

    class PalaceTile12(PalaceTile):

        id = 12
        
        def execute_income_effect(self, executed_player_id):
            '''收入效果: 获得8转魔'''
            self.income_effect.extend([
                ('magics', 'get', 8)
            ])
            super().execute_income_effect(executed_player_id)
        
        '''行动效果: 每建造1车间获得2分'''
        # 建造行动效果已写入action_effect中

    class PalaceTile13(PalaceTile):

        id = 13
        
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
                        return [295]
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
                    
        '''行动效果: 每建造1工会获得3分'''
        # 建造行动效果已写入action_effect中

    class PalaceTile14(PalaceTile):

        id = 14
        
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

        id = 15
        
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

        id = 16
        
        def execute_income_effect(self, executed_player_id):
            '''收入效果: 获得2转魔 + 1书'''
            self.income_effect.extend([
                ('magics', 'get', 2),
                ('book', 'get', 'any', 1)
            ])
            super().execute_income_effect(executed_player_id)
        
        # TODO 特殊建造立即行动

    class RoundBooster1(RoundBooster):

        id = 1
        
        def execute_immediate_effect(self, executed_player_id):
            '''收入效果: 获得临时1航行'''
            self.game_state.players[executed_player_id].temp_navigation = True
            super().execute_immediate_effect(executed_player_id)
        
        def execute_pass_effect(self, executed_player_id):
            '''略过效果: 取消临时1航行'''
            self.game_state.players[executed_player_id].temp_navigation = False
            super().execute_pass_effect(executed_player_id)

        '''行动效果: 每建造1个位于河边的车间获得2分'''
        # 建筑建造行动效果已写入action_effect方法中

    class RoundBooster2(RoundBooster):

        id = 2
        
        def execute_income_effect(self, executed_player_id):
            '''收入效果: 获得1矿'''
            self.income_effect.extend([
                ('ore', 'get', 1),
            ])
            super().execute_income_effect(executed_player_id)

        def execute_pass_effect(self, executed_player_id):
            '''略过效果: 每一宫殿或大学获得4分'''
            building_nums = (
                (1 - self.game_state.players[executed_player_id].buildings[3])
                + (1 - self.game_state.players[executed_player_id].buildings[5])
                + self.game_state.players[executed_player_id].buildings[11]
                + self.game_state.players[executed_player_id].buildings[13]
            )
            self.pass_effect.extend([
                ('score', 'get', 'board', 4 * building_nums)
            ])
            super().execute_pass_effect(executed_player_id)

    class RoundBooster3(RoundBooster):

        id = 3

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
                        ('tracks', 'any', 2)
                    ])

    class RoundBooster4(RoundBooster):

        id = 4
        
        def execute_income_effect(self, executed_player_id):
            '''收入效果: 获得1米宝'''
            self.income_effect.extend([
                ('meeple', 'get', 1)
            ])
            super().execute_income_effect(executed_player_id)

        '''行动效果: 每插入1个米宝获得2分'''
        # 插入米宝行动效果已写入action_effect方法中

    class RoundBooster5(RoundBooster):

        id = 5
        
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
                        ('spade', 1)
                    ])
        
        def execute_income_effect(self, executed_player_id):
            '''收入效果: 获得1书'''
            self.income_effect.extend([
                ('book', 'get', 'any', 1)
            ])
            super().execute_income_effect(executed_player_id)

    class RoundBooster6(RoundBooster):

        id = 6
        
        def execute_income_effect(self, executed_player_id):
            '''收入效果: 获得4块钱'''
            self.income_effect.extend([
                ('money', 'get', 4)
            ])
            super().execute_income_effect(executed_player_id)
        
        def execute_pass_effect(self, executed_player_id):
            '''略过效果: 每1学院获得1轨'''
            building_nums = (
                (3 - self.game_state.players[executed_player_id].buildings[4])
                + self.game_state.players[executed_player_id].buildings[12]
            )
            self.pass_effect.extend([
                ('tracks', 'any', building_nums)
            ])
            super().execute_pass_effect(executed_player_id)

    class RoundBooster7(RoundBooster):

        id = 7
        
        def execute_income_effect(self, executed_player_id):
            '''收入效果: 获得3转魔'''
            self.income_effect.extend([
                ('magics', 'get', 3)
            ])
            super().execute_income_effect(executed_player_id)

        '''行动效果: 每建造1个工会获得3分'''
        # 建筑建造行动效果已写入action_effect方法中

    class RoundBooster8(RoundBooster):

        id = 8

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
                        return [298
                        ]
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

        id = 9
        
        def execute_income_effect(self, executed_player_id):
            '''收入效果: 获得4转魔 + 2块钱'''
            self.income_effect.extend([
                ('magics', 'get', 4),
                ('money', 'get', 2)
            ])
            super().execute_income_effect(executed_player_id)

    class RoundBooster10(RoundBooster):

        id = 10
        
        def execute_income_effect(self, executed_player_id):
            '''收入效果: 获得6块钱'''
            self.income_effect.extend([
                ('money', 'get', 6)
            ])
            super().execute_income_effect(executed_player_id)

    class AbilityTile1(AbilityTile):

        id = 1
        
        def execute_income_effect(self, executed_player_id):
            '''收入效果: 获得1矿 + 1轨'''
            self.income_effect.extend([
                ('ore', 'get', 1),
                ('tracks', 'any', 1)
            ])
            super().execute_income_effect(executed_player_id)

    class AbilityTile2(AbilityTile):

        id = 2

        def execute_income_effect(self, executed_player_id):
            '''收入效果: 获得2分 + 2块钱'''
            self.income_effect.extend([
                ('score', 'get', 'board', 3),
                ('money', 'get', 2)
            ])
            super().execute_income_effect(executed_player_id)
        
    class AbilityTile3(AbilityTile):
        
        id = 3

        def execute_income_effect(self, executed_player_id):
            '''收入效果: 获得1书 + 1魔力'''
            self.income_effect.extend([
                ('book', 'get', 'any', 1),
                ('magics', 'get', 1)
            ])
            super().execute_income_effect(executed_player_id)
        
    class AbilityTile4(AbilityTile):

        id = 4
        
        def execute_immediate_effect(self, executed_player_id):
            '''立即效果: 获得1矿 + 5分 + 2块钱'''
            self.immediate_effect.extend([
                ('ore', 'get', 1),
                ('score', 'get', 'board', 5),
                ('money', 'get', 2)
            ])
            super().execute_immediate_effect(executed_player_id)

    class AbilityTile5(AbilityTile):

        id = 5
        
        def execute_immediate_effect(self, executed_player_id):
            '''立即效果: 立即2铲并可选建造'''
            self.immediate_effect.extend([
                ('spade', 2)
            ])
            super().execute_immediate_effect(executed_player_id)

    class AbilityTile6(AbilityTile):

        id = 6
        
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
                        # 存在未建造侧楼的已控制坐标
                        and any(
                            self.game_state.map_board_state.map_grid[i][j][3] == 0
                            for i,j in self.game_state.players[player_id].controlled_map_ids
                        )
                    ):
                        return [301]
                    else:
                        return []
                    
                case 'execute':

                    # 设置主行动已执行
                    self.game_state.players[player_id].main_action_is_done = True
                    # 选择建造位置
                    if self.game_state.invoke_immediate_aciton(player_id, ('select_position', 'controlled', (8, None))): return 
                    # 执行建造行动
                    self.game_state.adjust(player_id, [('building', 'build_annex', 8, True)])

    class AbilityTile7(AbilityTile):

        id = 7
        
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
                        return [287]
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

        id = 8
        
        '''行动效果: 每插入1米宝获得2分'''
        #  行动效果已写入action_effect方法中
        pass

    class AbilityTile9(AbilityTile):

        id = 9
        
        def execute_pass_effect(self, executed_player_id):
            '''略过效果: 每一个城片获得2分'''
            self.pass_effect.extend([
                ('score', 'get', 'board', 2 * self.game_state.players[executed_player_id].citys_amount)
            ])
            super().execute_pass_effect(executed_player_id)

    class AbilityTile10(AbilityTile):

        id = 10
        
        '''行动效果: 每建造1处于边地的车间获得3分'''
        #  行动效果已写入action_effect方法中
        pass

    class AbilityTile11(AbilityTile):

        id = 11

        def execute_immediate_effect(self, executed_player_id):
            '''立即效果: 建造1个中立的塔楼'''
            self.immediate_effect.extend([
                ('building', 'build_neutral', 6, True)
            ])
            super().execute_immediate_effect(executed_player_id)
        
        def execute_income_effect(self, executed_player_id):
            '''收入效果: 获得2魔力 + 2块钱'''
            self.income_effect.extend([
                ('magics', 'get', 2),
                ('money', 'get', 2)
            ])
            super().execute_income_effect(executed_player_id)

    class AbilityTile12(AbilityTile):

        id = 12
        
        def execute_pass_effect(self, executed_player_id):
            '''略过效果: 获得四学科轨最低值的分数'''
            self.pass_effect.extend([
                ('score', 'get', 'board', min(self.game_state.players[executed_player_id].tracks.values()))
            ])
            super().execute_pass_effect(executed_player_id)

    class ScienceTile1(ScienceTile):
        
        id = 1
        additional_action_name = 'additional_action_science_tile_1'
        
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
                        return [299]
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
        
        def execute_immediate_effect(self, executed_player_id):
            self.immediate_effect.extend([
                ('book', 'get', 'any', 1),
                ('tracks', 'bank', 1),
                ('tracks', 'law', 1),
                ('tracks', 'engineering', 1),
                ('tracks', 'medical', 1),
            ])
            super().execute_immediate_effect(executed_player_id)

    class ScienceTile2(ScienceTile):

        id = 2

        def execute_pass_effect(self, executed_player_id):
            '''略过效果: 每已建1工会获得2分'''
            # 获取无论是否中立的工会建筑数量
            building_nums = (
                (4 - self.game_state.players[executed_player_id].buildings[2])
                + self.game_state.players[executed_player_id].buildings[10]
            )
            # 略过回合时，每已建一工会获取2分
            self.pass_effect.extend([
                ('score', 'get', 'board', 2 * building_nums)
            ])
            super().execute_pass_effect(executed_player_id)

    class ScienceTile3(ScienceTile):

        id = 3
        additional_action_name = 'additional_action_science_tile_3'
        
        def additional_action(self, mode, player_id, args=tuple()):
            '''每回合一次附加行动: 获取1米宝 + 3分'''
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
                        return [300]
                    else:
                        return []
                    
                case 'execute':

                    # 设置主行动已执行
                    self.game_state.players[player_id].main_action_is_done = True
                    # 设置每回合一次附加行动已执行
                    self.additional_action_is_done[player_id] = True
                    # 获取奖励
                    self.game_state.adjust(player_id, [
                        ('meeple', 'get', 1),
                        ('score', 'get', 'board', 3)
                    ])

    class ScienceTile4(ScienceTile):

        id = 4

        def execute_immediate_effect(self, executed_player_id):
            '''立即效果: 每有1不同形状建筑推1轨 + 获取10分'''
            num = (
                1 if (
                    self.game_state.players[executed_player_id].buildings[1] != 9
                    or self.game_state.players[executed_player_id].buildings[9] != 0
                )
                else 0
                + 1 if (
                    self.game_state.players[executed_player_id].buildings[2] != 4
                    or self.game_state.players[executed_player_id].buildings[10] != 0
                )
                else 0
                + 1 if (
                    self.game_state.players[executed_player_id].buildings[3] != 1
                    or self.game_state.players[executed_player_id].buildings[11] != 0
                )
                else 0
                + 1 if (
                    self.game_state.players[executed_player_id].buildings[4] != 3
                    or self.game_state.players[executed_player_id].buildings[12] != 0
                )
                else 0
                + 1 if (
                    self.game_state.players[executed_player_id].buildings[5] != 1
                    or self.game_state.players[executed_player_id].buildings[13] != 0
                )
                else 0
                + 1 if (
                    self.game_state.players[executed_player_id].buildings[6] != 0
                ) else 0
                + 1 if (
                    self.game_state.players[executed_player_id].buildings[7] != 0
                ) else 0
            )
            self.immediate_effect.extend([
                ('score', 'get', 'board', 10),
                ('tracks', 'any', num),
            ])
            super().execute_immediate_effect(executed_player_id)

    class ScienceTile5(ScienceTile):

        id = 5
        
        def execute_immediate_effect(self, executed_player_id):
            '''立即效果: 以建7-8个建筑获取8分，9-10个获取12分，11个以上获取18分'''
            building_num = (
                (9 - self.game_state.players[executed_player_id].buildings[1])
                + (4 - self.game_state.players[executed_player_id].buildings[2])
                + (1 - self.game_state.players[executed_player_id].buildings[3])
                + (3 - self.game_state.players[executed_player_id].buildings[4])
                + (1 - self.game_state.players[executed_player_id].buildings[5])
                + self.game_state.players[executed_player_id].buildings[6]
                + self.game_state.players[executed_player_id].buildings[7]
            )
            match building_num:
                case i if i <= 6:
                    score_num = 0
                case 7|8:
                    score_num = 8
                case 9|10:
                    score_num = 12
                case i if i >= 11:
                    score_num = 18

            self.immediate_effect.extend([
                ('score', 'get', 'board', score_num),
            ])
            super().execute_immediate_effect(executed_player_id)

    class ScienceTile6(ScienceTile):
        
        id = 6
        
        def execute_immediate_effect(self, executed_player_id):
            '''立即效果: 每已建1个学院获取5分数'''
            building_num = (
                3 - self.game_state.players[executed_player_id].buildings[4]
                + self.game_state.players[executed_player_id].buildings[12]
            )
            self.immediate_effect.extend([
                ('score', 'get', 'board', 5 * building_num),
            ])
            super().execute_immediate_effect(executed_player_id)

    class ScienceTile7(ScienceTile):
        
        id = 7
        
        def execute_immediate_effect(self, executed_player_id):
            '''立即效果: 已有4个聚落获得8分，5个12分，6个以上18分'''
            settlement_num = (
                len(set(map(
                    lambda x: x[0],
                    self.game_state.players[executed_player_id].settlements_and_cities.values()
                )))
            )
            match settlement_num:
                case i if i <= 3:
                    score_num = 0
                case 4:
                    score_num = 8
                case 5:
                    score_num = 12
                case i if i >= 6:
                    score_num = 18

            self.immediate_effect.extend([
                ('score', 'get', 'board', score_num),
            ])
            super().execute_immediate_effect(executed_player_id)

    class ScienceTile8(ScienceTile):
        
        id = 8
        
        def execute_immediate_effect(self, executed_player_id):
            '''立即效果: 每有1城片获取5分'''
            city_num = self.game_state.players[executed_player_id].citys_amount
            self.immediate_effect.extend([
                ('score', 'get', 'board', 5 * city_num),
            ])
            super().execute_immediate_effect(executed_player_id)

    class ScienceTile9(ScienceTile):
        
        id = 9
        
        def execute_immediate_effect(self, executed_player_id: int):
            '''立即效果: 获得等同最高2轨等级之和的分数'''
            score_num = sum(sorted(list(
                self.game_state.players[executed_player_id].tracks.values()
            ), reverse = True)[:2])
            self.immediate_effect.extend([
                ('score', 'get', 'board', score_num),
            ])
            super().execute_immediate_effect(executed_player_id)

    class ScienceTile10(ScienceTile):
        
        id = 10

        def execute_immediate_effect(self, executed_player_id: int):
            '''立即效果: 每已建1个车间获取2分'''
            building_num = (
                9 - self.game_state.players[executed_player_id].buildings[1]
                + self.game_state.players[executed_player_id].buildings[9]
            )
            self.immediate_effect.extend([
                ('score', 'get', 'board', 2 * building_num),
            ])
            super().execute_immediate_effect(executed_player_id)

    class ScienceTile11(ScienceTile):

        id = 11
        
        def execute_immediate_effect(self, executed_player_id: int):
            '''立即效果: 获取1米宝 + 提升1航行 + 提升1铲子'''
            self.immediate_effect.extend([
                ('meeple', 'get', 1),
                ('navigation',),
                ('shovel',),
            ])
            super().execute_immediate_effect(executed_player_id)

    class ScienceTile12(ScienceTile):
        
        id = 12
        
        def execute_immediate_effect(self, executed_player_id: int):
            '''立即效果: 已建1桥获取8分，2桥12分，3桥18分'''
            match self.game_state.players[executed_player_id].resources['all_bridges']:
                case 0:
                    score_num = 18
                case 1:
                    score_num = 12
                case 2:
                    score_num = 8
                case 3:
                    score_num = 0
            self.immediate_effect.extend([
                ('score', 'get', 'board', score_num),
            ])
            super().execute_immediate_effect(executed_player_id)

    class ScienceTile13(ScienceTile):
        
        id = 13
        
        def execute_immediate_effect(self, executed_player_id: int):
            '''立即效果: 建造1个中立的车间'''
            self.immediate_effect.extend([
                ('building', 'build_neutral', 1, True),
            ])
            super().execute_immediate_effect(executed_player_id)

        def execute_income_effect(self, executed_player_id: int):
            '''收入效果: 获取3矿'''
            self.income_effect.extend([
                ('ore', 'get', 3),
            ])
            super().execute_income_effect(executed_player_id)

    class ScienceTile14(ScienceTile):
        
        id = 14
        
        def execute_immediate_effect(self, executed_player_id: int):
            '''立即效果: 建造1个中立的工会'''
            self.immediate_effect.extend([
                ('building', 'build_neutral', 2, True),
            ])
            super().execute_immediate_effect(executed_player_id)
        
        def execute_income_effect(self, executed_player_id: int):
            '''收入效果: 获取5块'''
            self.income_effect.extend([
                ('money', 'get', 5),
            ])
            super().execute_income_effect(executed_player_id)

    class ScienceTile15(ScienceTile):
        
        id = 15
        
        def execute_immediate_effect(self, executed_player_id: int):
            '''立即效果: 建造1个中立的学院 + 获取1能力板块'''
            self.immediate_effect.extend([
                ('building', 'build_neutral', 4, True),
                ('ability_tile',)
            ])
            super().execute_immediate_effect(executed_player_id)

    class ScienceTile16(ScienceTile):
        
        id = 16
        
        def execute_immediate_effect(self, executed_player_id: int):
            '''立即效果: 建造1个中立的大学'''
            self.immediate_effect.extend([
                ('building', 'build_neutral', 5, True),
            ])
            super().execute_immediate_effect(executed_player_id)

        def execute_income_effect(self, executed_player_id: int):
            '''收入效果: 获取2分'''
            self.income_effect.extend([
                ('score', 'get', 'board', 2),
            ])
            super().execute_income_effect(executed_player_id)

    class ScienceTile17(ScienceTile):
        
        id = 17

        def execute_immediate_effect(self, executed_player_id: int):
            '''立即效果: 建造1个中立的宫殿， 并向3区添加2魔力'''
            self.immediate_effect.extend([
                ('building', 'build_neutral', 3, True),
                ('magics', 'science_tile_18', 2)
            ])
            super().execute_immediate_effect(executed_player_id)

        def execute_income_effect(self, executed_player_id: int):
            '''收入效果: 获取4转魔'''
            self.income_effect.extend([
                ('magics', 'get', 4),
            ])
            super().execute_income_effect(executed_player_id)

    class ScienceTile18(ScienceTile):
        
        id = 18
        
        def execute_immediate_effect(self, executed_player_id: int):
            '''立即效果: 建造1个中立的纪念碑 + 获得7分'''
            self.immediate_effect.extend([
                ('building', 'build_neutral', 7, True),
                ('score', 'get', 'board', 7)
            ])
            super().execute_immediate_effect(executed_player_id)

    class RoundScoring1(RoundScoring):

        id = 1
        
        def round_end(self):
            '''回合结束效果: 每有3法律轨，获得1米宝'''
            self.round_end_effect_args = ('meeple', 1, 'law', 3)
            return super().round_end()

    class RoundScoring2(RoundScoring):
        
        id = 2
        
        def round_end(self):
            '''回合结束效果: 每有3银行轨，获得4转魔'''
            self.round_end_effect_args = ('magics', 4, 'bank', 3)
            return super().round_end()

    class RoundScoring3(RoundScoring):
        
        id = 3
        
        def round_end(self):
            '''回合结束效果: 每有2法律轨，获得1书'''
            self.round_end_effect_args = ('book', 1, 'law', 3)
            return super().round_end()

    class RoundScoring4(RoundScoring):
        
        id = 4
        
        def round_end(self):
            '''回合结束效果: 每有4医疗轨，获得1铲'''
            self.round_end_effect_args = ('spade', 1, 'medical', 4)
            return super().round_end()

    class RoundScoring5(RoundScoring):
        
        id = 5
        
        def round_end(self):
            '''回合结束效果: 每有1银行轨，获得1块'''
            self.round_end_effect_args = ('money', 1, 'bank', 1)
            return super().round_end()

    class RoundScoring6(RoundScoring):
        
        id = 6
        
        def round_end(self):
            '''回合结束效果: 每有2医疗轨，获得1矿'''
            self.round_end_effect_args = ('ore', 1, 'medical', 2)
            return super().round_end()

    class RoundScoring7(RoundScoring):
        
        id = 7
        
        def round_end(self):
            '''回合结束效果: 每有2银行轨，获得1矿'''
            self.round_end_effect_args = ('ore', 1, 'bank', 2)
            return super().round_end()

    class RoundScoring8(RoundScoring):
        
        id = 8
        
        def round_end(self):
            '''回合结束效果: 每有1工程轨，获得1块'''
            self.round_end_effect_args = ('money', 1, 'engineering', 1)
            return super().round_end()

    class RoundScoring9(RoundScoring):
        
        id = 9
        
        def round_end(self):
            '''回合结束效果: 每有3医疗轨，获得1书'''
            self.round_end_effect_args = ('book', 1, 'medical', 3)
            return super().round_end()

    class RoundScoring10(RoundScoring):
        
        id = 10
        
        def round_end(self):
            '''回合结束效果: 每有4工程轨，获得1铲'''
            self.round_end_effect_args = ('spade', 1, 'engineering', 4)
            return super().round_end()

    class RoundScoring11(RoundScoring):
        
        id = 11
        
        def round_end(self):
            '''回合结束效果: 每有3工程轨，获得1米宝'''
            self.round_end_effect_args = ('meeple', 1, 'engineering', 3)
            return super().round_end()

    class RoundScoring12(RoundScoring):
        
        id = 12
        
        def round_end(self):
            '''回合结束效果: 每有2法律轨，获得3转魔'''
            self.round_end_effect_args = ('magics', 3, 'law', 2)
            return super().round_end()

    class FinalScoring1(FinalScoring):

        id = 1

        pass

    class FinalScoring2(FinalScoring):

        id = 2

        pass

    class FinalScoring3(FinalScoring):

        id = 3

        pass

    class FinalScoring4(FinalScoring):

        id = 4

        pass

    class BookAction1(BookAction):

        id = 1
        
        def cost(self, player_id):
            return [('book', 'self', 'any', 1)], [('book', 'use', 'any', 1)]
        
        def execute_immediate_effect(self, executed_player_id):
            self.immediate_effect.extend([
                ('magics', 'get', 5),
            ])
            super().execute_immediate_effect(executed_player_id)

    class BookAction2(BookAction):

        id = 2
        
        def cost(self, player_id):
            return [('book', 'self', 'any', 1)], [('book', 'use', 'any', 1)]
        
        def execute_immediate_effect(self, executed_player_id):
            self.immediate_effect.extend([
                ('tracks', 'any', 2),
            ])
            super().execute_immediate_effect(executed_player_id)

    class BookAction3(BookAction):

        id = 3
        
        def cost(self, player_id):
            return [('book', 'self', 'any', 2)], [('book', 'use', 'any', 2)]
        
        def execute_immediate_effect(self, executed_player_id):
            self.immediate_effect.extend([
                ('money', 'get', 6),
            ])
            super().execute_immediate_effect(executed_player_id)

    class BookAction4(BookAction):

        id = 4
        
        def cost(self, player_id):
            return [('book', 'self', 'any', 2)], [('book', 'use', 'any', 2)]
        
        def execute_immediate_effect(self, executed_player_id):
            super().execute_immediate_effect(executed_player_id)
            if self.game_state.players[executed_player_id].buildings[1] < 9:
                if self.game_state.invoke_immediate_aciton(executed_player_id, ('select_position', 'controlled', (1, 'alone_or_neighbor'))): return 
                self.game_state.adjust(executed_player_id,[('building', 'upgrade_special', 2, False)])
            
    class BookAction5(BookAction):

        id = 5
        
        def cost(self, player_id):
            return [('book', 'self', 'any', 2)], [('book', 'use', 'any', 2)]
        
        def execute_immediate_effect(self, executed_player_id):
            self.immediate_effect.extend([
                ('score', 'get', 'board', 2 * (4 - self.game_state.players[executed_player_id].buildings[2] + self.game_state.players[executed_player_id].buildings[10])),
            ])
            super().execute_immediate_effect(executed_player_id)

    class BookAction6(BookAction):

        id = 6
        
        def cost(self, player_id):
            return [('book', 'self', 'any', 3)], [('book', 'use', 'any', 3)]
        
        def execute_immediate_effect(self, executed_player_id):
            self.immediate_effect.extend([
                ('spade',3),
            ])
            super().execute_immediate_effect(executed_player_id)
    
    class CityTileBook(CityTile):

        id = 1

        def execute_immediate_effect(self, executed_player_id):
            self.immediate_effect.extend([
                ('book', 'get', 'any', 2),
                ('score', 'get', 'board', 5),
            ])
            super().execute_immediate_effect(executed_player_id)

    class CityTileTrack(CityTile):

        id = 2

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

        id = 3

        def execute_immediate_effect(self, executed_player_id):
            self.immediate_effect.extend([
                ('spade', 2),
                ('score', 'get', 'board', 5),
            ])
            super().execute_immediate_effect(executed_player_id)
    
    class CityTileMagics(CityTile):

        id = 4

        def execute_immediate_effect(self, executed_player_id):
            self.immediate_effect.extend([
                ('magics', 'get', 8),
                ('score', 'get', 'board', 8),
            ])
            super().execute_immediate_effect(executed_player_id)
    
    class CityTileOre(CityTile):

        id = 5

        def execute_immediate_effect(self, executed_player_id):
            self.immediate_effect.extend([
                ('ore', 'get', 3),
                ('score', 'get', 'board', 4),
            ])
            super().execute_immediate_effect(executed_player_id)
    
    class CityTileMeeple(CityTile):

        id = 6

        def execute_immediate_effect(self, executed_player_id):
            self.immediate_effect.extend([
                ('meeple', 'get', 1),
                ('score', 'get', 'board', 8),
            ])
            super().execute_immediate_effect(executed_player_id)
    
    class CityTileMoney(CityTile):

        id = 7
        
        def execute_immediate_effect(self, executed_player_id):
            self.immediate_effect.extend([
                ('money', 'get', 6),
                ('score', 'get', 'board', 6),
            ])
            super().execute_immediate_effect(executed_player_id)

    class MagicsActionBridge(MagicsAction):

        id = 1

        def cost(self, player_id):
            return [('magics',3,3)], [('magics', 'use', 3)]
        
        def execute_immediate_effect(self, executed_player_id):
            self.immediate_effect.extend([
                ('bridge',)
            ])
            super().execute_immediate_effect(executed_player_id)

    class MagicsActionMeeple(MagicsAction):

        id = 2
        
        def cost(self, player_id):
            return [('magics',3,3)], [('magics', 'use', 3)]
        
        def execute_immediate_effect(self, executed_player_id):
            self.immediate_effect.extend([
                ('meeple','get',1)
            ])
            super().execute_immediate_effect(executed_player_id)
        
    class MagicsActionOre(MagicsAction):

        id = 3
        
        def cost(self, player_id):
            return [('magics',3,4)], [('magics', 'use', 4)]
        
        def execute_immediate_effect(self, executed_player_id):
            self.immediate_effect.extend([
                ('ore','get', 2)
            ])
            super().execute_immediate_effect(executed_player_id)

    class MagicsActionMoney(MagicsAction):

        id = 4
        
        def cost(self, player_id):
            return [('magics',3,4)], [('magics', 'use', 4)]
        
        def execute_immediate_effect(self, executed_player_id):
            self.immediate_effect.extend([
                ('money','get',7)
            ])
            super().execute_immediate_effect(executed_player_id)

    class MagicsActionShovel1(MagicsAction):

        id = 5
        
        def cost(self, player_id):
            return [('magics',3,4)], [('magics', 'use', 4)]
        
        def execute_immediate_effect(self, executed_player_id):
            self.immediate_effect.extend([
                ('spade',1)
            ])
            super().execute_immediate_effect(executed_player_id)

    class MagicsActionShovel2(MagicsAction):

        id = 6
        
        def cost(self, player_id):
            return [('magics',3,6)], [('magics', 'use', 6)]

        def execute_immediate_effect(self, executed_player_id):
            self.immediate_effect.extend([
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
                10: self.RoundScoring10,
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
            
    def create_actual_object(self,typ: str, object_id: int): 
        return self.all_object_dict[typ][object_id](self.game_state)