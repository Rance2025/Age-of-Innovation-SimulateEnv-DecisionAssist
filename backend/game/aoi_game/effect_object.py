from .game_state import GameStateBase
from .utils.generatorize import generatorize
from typing import Generator, Callable

class AllEffectObject:

    class EffectObject:
        """效果对象抽象基类"""

        max_owner = 1
        additional_action_name = 'Effect_Object_Base'
        name_dict = {}
        effect_desc_dict = {}
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
            yield from self.game_state.adjust(executed_player_id, self.immediate_effect)
            # 清空本版块立即效果列表（以防多玩家获取同一板块时，后获得者重复执行效果）
            self.immediate_effect.clear()

        # 回合收入方法
        def execute_income_effect(self, executed_player_id:int):
            # 执行收入效果
            yield from self.game_state.adjust(executed_player_id, self.income_effect)
            # 清空本版块收入效果列表（以防多玩家获取同一板块时，后获得者重复执行效果）
            self.income_effect.clear()

        # 略过回合方法
        def execute_pass_effect(self, executed_player_id:int):
            # 执行略过回合效果
            yield from self.game_state.adjust(executed_player_id, self.pass_effect)
            # 清空本版块略过回合效果列表（以防多玩家获取同一板块时，后获得者重复执行效果）
            self.pass_effect.clear()

        # 初始设置方法
        def execute_setup_effect(self, executed_player_id:int):
            # 执行初始设置效果
            yield from self.game_state.adjust(executed_player_id, self.setup_effect)
            # 清空初始设置效果
            self.setup_effect.clear()

        # 额外行动方法
        def additional_action(self, mode, player_id:int, args = tuple()) -> list[int]|Callable[[], Generator]:
            match mode:
                case 'check':
                    return []
                case 'execute':
                    def execute_function(): 
                        yield from ()
                    return execute_function
        
        # 当获取时
        def get(self, got_player_id:int):
            # 记录该板块的拥有者
            self.owner_list.append(got_player_id)
            # 支付该板块费用
            yield from self.game_state.adjust(got_player_id, self.cost(got_player_id)[1])
            # 执行立即效果
            yield from self.execute_immediate_effect(got_player_id)
            # 添加收入效果
            self.game_state.players[got_player_id].income_effect_list.append(self.execute_income_effect)
            # 添加略过效果
            self.game_state.players[got_player_id].pass_effect_list.append(self.execute_pass_effect)
            # 添加初始设置效果
            self.game_state.players[got_player_id].setup_effect_list.append(self.execute_setup_effect)
            # 添加额外行动 
            self.game_state.players[got_player_id].additional_actions_dict[self.additional_action_name] = self.additional_action

        # 当激活时
        @generatorize
        def activate(self, executed_player_id):
            pass

        # 当回合结束时
        @generatorize
        def round_end(self):
            # 重置每回合一次附加行动已执行标记
            self.additional_action_is_done = [False] * self.game_state.num_players

        # 当交还时
        @generatorize
        def back(self, executed_player_id):
            pass

        # 获取效果板块名称
        def get_name(self):
            return self.name_dict[self.id]
        
        # 获取效果版块的效果描述
        def get_effect_desc(self):
            return self.effect_desc_dict[self.id]
        
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
        
        effect_desc_dict = {
            1: "行动效果 - 升级铲子减少4金币",
            2: "立即效果 - 获取1个米宝 + 2个魔力",
            3: "立即效果 - 免费提升1级航行轨道",
            4: "立即效果 - 获取1个魔力 + 四个学科轨道各推进1格",
            5: "收入阶段效果 - 每回合额外收入2金币，且第一个工会建筑额外收入1金币",
            6: "初始设置 - 获取任意1本书；立即效果 - 获取1个矿；行动效果 - 第二项发明研究少付1本书",
            7: "初始设置 - 初始建筑摆放完毕后立即获得1个铲子（但该铲子不可用于建造房屋）"
        }
                
        id = 0

        def get(self, got_player_id):
            yield from super().get(got_player_id)

        def execute_income_effect(self, executed_player_id):
            '''回合收入效果: 规划卡 (即个人板面) 建筑收入'''
            buildings = self.game_state.players[executed_player_id].buildings
            self.income_effect.extend([
                ('ore', 'get', 10-buildings[1] if buildings[1]>=5 else 9-buildings[1]),
                ('money', 'get', 2*(4-buildings[2])),
                ('magics', 'get', 4-buildings[2] if buildings[2]>=2 else 2*(4-buildings[2])-2),
                ('meeple', 'get', 3-buildings[4] + 1-buildings[5])
            ])
            yield from super().execute_income_effect(executed_player_id)

        def execute_immediate_effect(self, executed_player_id: int):
            self.immediate_effect.extend([
                ('money', 'get', 15),
                ('ore', 'get', 3),
            ])
            yield from super().execute_immediate_effect(executed_player_id)

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

        effect_desc_dict = {
            1: "立即效果：四个学科轨道各推一格；行动效果：结算轮次计分板块的科学奖励效果时，轨道被视为额外+3",
            2: "立即效果：银行、医学轨道各推一格；行动效果：当建城时，任意轨道推一格执行3次 + 获取1本书",
            3: "立即效果：银行、工程轨道各推一格 + 获取1个矿；行动效果：每用一铲获得2块钱",
            4: "立即效果：医学轨道推两格；行动效果：每次执行魔力行动时，少花费1点魔力并获得版面分数（1分，5人局2分）",
            5: "初始设置：获取任一能力板块",
            6: "初始设置：任意轨道推一格执行两次；行动效果：当建城时，立即免费1铲 + 免费建造一个车间（无需在刚刚铲的地块上）",
            7: "立即效果：工程轨道推两格；附加行动：支付1矿跨越一个地块执行地形改造和/或建造车间并获得4分；特殊效果：终局计分将跨越1地块视为可抵达，即使无剩余矿",
            8: "立即效果：法律轨道推一格；初始设置：取消摆放两个工会，而是摆放一个大学作为初始建筑",
            9: "立即效果：法律轨道推三格；行动效果：当工会建造在河边时，获得2版面分数",
            10: "立即效果：银行、工程轨道各推一格；初始设置：可额外摆放一个中立塔楼作为初始建筑；收入效果：每回合获得2魔力 + 2块钱",
            11: "立即效果：银行轨道推两格；行动效果：获取能力板块时，多获得对应学科的书1本；附加行动：每回合一次获取1本书",
            12: "立即效果：银行、医学轨道各推一格 + 获取1个矿；附加行动：每回合一次转换5点魔力，并立即进行下一动"
        }

        id = 0
        
        def get(self, got_player_id):
            yield from super().get(got_player_id)

    class PalaceTile(EffectObject):

        name_dict = {i: f"宫殿板块{i}" for i in range(1,17)}

        effect_desc_dict = {
            1: "收入效果：获得5魔力；附加行动：每回合一次获得2个矿",
            2: "附加行动：每回合一次立即获得2个铲子并可选择建造",
            3: "收入效果：获得2魔力；附加行动：将1个学院降级为工会，并获得3分+1个矿",
            4: "收入效果：获得2魔力；附加行动：将1个车间升级为工会",
            5: "收入效果：获得4魔力；激活效果：获得1个能力板块",
            6: "收入效果：获得2魔力+1本书；附加行动：每回合一次任意轨道推2格",
            7: "收入效果：获得4魔力；略过效果：每1个学院获得3分",
            8: "收入效果：获得2块钱+1个矿+2魔力；特殊效果：允许花费6魔力建城",
            9: "收入效果：获得1个米宝；附加行动：支付1米宝跨越一至两个地块执行地形改造和/或建造车间并获得5分；特殊效果：终局计分将跨越2地块视为可抵达，即使无剩余米宝",
            10: "收入效果：获得6块钱；激活效果：获得12魔力+2本书",
            11: "收入效果：获得1个矿；激活效果：获得1个城市板块",
            12: "收入效果：获得8魔力；行动效果：每建造1个车间获得2分",
            13: "附加行动：每回合一次获得3块钱+1本书；行动效果：每建造1个工会获得3分",
            14: "收入效果：获得6魔力；附加行动：跨越1河流地块建城；激活效果：提升2级航行轨道",
            15: "收入效果：获得6魔力；激活效果：获得2个铲子（可建造）+2本书+立即建造2座桥梁",
            16: "收入效果：获得2魔力+1本书；激活效果：在任意原生地建造1个工会"
        }
        
        id = 0

        # 当获取时
        @generatorize
        def get(self, got_player_id):
            self.owner_list.append(got_player_id)

        # 当激活时
        def activate(self, executed_player_id:int):
            # 执行立即效果
            yield from self.execute_immediate_effect(executed_player_id)
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
        
        effect_desc_dict = {
            1: "立即效果：获得临时加1级航行；略过效果：取消临时航行效果；行动效果：每建造1个位于河边的车间获得2分",
            2: "收入效果：获得1个矿；略过效果：每一宫殿或大学获得4分",
            3: "收入效果：获得2个矿；附加行动：每回合一次任意轨道推1格",
            4: "收入效果：获得1个米宝；行动效果：每插入1个米宝获得2分",
            5: "附加行动：每回合一次获得1个铲子；收入效果：获得1本书",
            6: "收入效果：获得4块钱；略过效果：每1个学院获得1格任意轨道",
            7: "收入效果：获得3魔力；行动效果：每建造1个工会获得3分",
            8: "附加行动：每回合一次立即建造1座桥梁；收入效果：获得1本书",
            9: "收入效果：获得4魔力+2块钱",
            10: "收入效果：获得6块钱"
        }
        id = 0

        # 当回合结束时
        def round_end(self):
            if not self.owner_list:
                # print(f"回合助推板{self.id} -> 获取时额外获得1块钱")
                self.immediate_effect.extend([
                    ('money', 'get', 1),
                ])
            yield from super().round_end()

        # 当获取时
        def get(self, got_player_id:int):
            yield from super().get(got_player_id)
            # 设置玩家新一轮回合助推板
            self.game_state.players[got_player_id].booster_ids.append(self.id)

        # 当交还时
        def back(self, executed_player_id:int):
            # 从将交还的回合助推板的持有者列表中移除玩家id，即标记为未被持有
            self.owner_list.remove(executed_player_id)
            # 执行该玩家所有略过动作效果
            for effect_function in self.game_state.players[executed_player_id].pass_effect_list.copy():
                yield from effect_function(executed_player_id)
            # 使用函数引用和实例标识来移除
            self._remove_effect_functions(executed_player_id)
            # 移除该玩家属于回合助推板的额外行动
            if self.additional_action_name in self.game_state.players[executed_player_id].additional_actions_dict:
                self.game_state.players[executed_player_id].additional_actions_dict.pop(self.additional_action_name)
            # 将该玩家id从当前回合玩家行动顺序中移除
            self.game_state.current_player_order.remove(executed_player_id)
            # 将该玩家id加入当前回合跳过顺序列表
            self.game_state.pass_order.append(executed_player_id)

        def _remove_effect_functions(self, player_id:int):
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

        effect_desc_dict = {
            1: "收入效果：获得1个矿 + 1格任意轨道",
            2: "收入效果：获得3分 + 2块钱",
            3: "收入效果：获得1本书 + 1魔力",
            4: "立即效果：获得1个矿 + 5分 + 2块钱",
            5: "立即效果：立即获得2个铲子并可选择建造",
            6: "立即效果：获得2个侧楼；附加行动：建造1个侧楼",
            7: "附加行动：每回合一次获得4魔力",
            8: "行动效果：每插入1个米宝获得2分",
            9: "略过效果：每一个城市板块获得2分",
            10: "行动效果：每建造1个处于边地的车间获得3分",
            11: "立即效果：建造1个中立的塔楼；收入效果：获得2魔力 + 2块钱",
            12: "略过效果：获得等同四学科轨道中最低值的分数"
        }
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
            yield from self.game_state.adjust(got_player_id, reward)
            # 获取能力板块行动效果
            yield from self.game_state.action_effect(player_id=got_player_id, get_ability_tile_typ=typ)
            yield from super().get(got_player_id)
            
    class ScienceTile(EffectObject):

        name_dict = {i: f"高科板块{i}" for i in range(1,19)}

        effect_desc_dict = {
            1: "附加行动：每回合一次获得1个铲子；立即效果：获得1本书 + 四个学科轨道各推1格",
            2: "略过效果：每已建1个工会获得2分",
            3: "附加行动：每回合一次获得1个米宝 + 3分",
            4: "立即效果：每有1种不同形状建筑推1格任意轨道 + 获取10分",
            5: "立即效果：已建7-8个建筑获取8分，9-10个获取12分，11个以上获取18分",
            6: "立即效果：每已建1个学院获取5分",
            7: "立即效果：已有4个聚落获得8分，5个聚落12分，6个以上18分",
            8: "立即效果：每有1个城市板块获取5分",
            9: "立即效果：获得等同最高2个学科轨道等级之和的分数",
            10: "立即效果：每已建1个车间获取2分",
            11: "立即效果：获得1个米宝 + 提升1级航行 + 提升1级铲子",
            12: "立即效果：已建1座桥获取8分，2座桥12分，3座桥18分",
            13: "立即效果：建造1个中立的车间；收入效果：获得3个矿石",
            14: "立即效果：建造1个中立的工会；收入效果：获得5块钱",
            15: "立即效果：建造1个中立的学院 + 获取1个能力板块",
            16: "立即效果：建造1个中立的大学；收入效果：获得2分",
            17: "立即效果：建造1个中立的宫殿 + 向3区添加2魔力；收入效果：获得4魔力",
            18: "立即效果：建造1个中立的纪念碑 + 获得7分"
        }

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
            yield from super().get(got_player_id)
            # 添加该高科板块id至玩家列表
            self.game_state.players[got_player_id].science_tile_ids.append(self.id)
            # 获取高科板块行动效果触发
            yield from self.game_state.action_effect(player_id=got_player_id, get_science_tile=True)

    class RoundScoring(EffectObject):
        
        name_dict = {i: f"回合计分板块{i}" for i in range(1,13)}

        effect_desc_dict = {
            1: "回合结束效果：每有3格法律轨道，获得1个米宝；行动效果：每建造1个车间获得2分",
            2: "回合结束效果：每有3格银行轨道，获得4魔力；行动效果：每建造1个车间获得2分",
            3: "回合结束效果：每有3格法律轨道，获得1本书；行动效果：每建造1个工会获得3分",
            4: "回合结束效果：每有4格医疗轨道，获得1个铲子；行动效果：每建造1个工会获得3分",
            5: "回合结束效果：每有1格银行轨道，获得1块钱；行动效果：每建造1个学院获得4分",
            6: "回合结束效果：每有2格医疗轨道，获得1个矿；行动效果：每建造1个宫殿或大学获得5分",
            7: "回合结束效果：每有2格银行轨道，获得1个矿；行动效果：每建造1个宫殿或大学获得5分",
            8: "回合结束效果：每有1格工程轨道，获得1块钱；行动效果：每铲1次获得2分",
            9: "回合结束效果：每有3格医疗轨道，获得1本书；行动效果：每提升1格学科轨道获得1分",
            10: "回合结束效果：每有4格工程轨道，获得1个铲子；行动效果：每次建城获得5分",
            11: "回合结束效果：每有3格工程轨道，获得1个米宝；行动效果：每次升级航行或铲子获得3分",
            12: "回合结束效果：每有2格法律轨道，获得3魔力；行动效果：每次获得高科板块获得5分"
        }

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
                    yield from self.game_state.adjust(player_idx, round_end_effect)
            yield from super().round_end()
        
        '''其左侧行动效果均已写入action_effect方法中'''
        # 回合计分板块的行动效果
        
    class FinalScoring(EffectObject):
        
        name_dict = {i: f"最终计分板块{i}" for i in range(1,5)}
        
        effect_desc_dict = {
            1: "行动效果：每建造1个车间获得2分",
            2: "行动效果：每建造1个学院获得4分",
            3: "行动效果：每建造1个位于边缘地带的车间获得3分",
            4: "行动效果：每建造1个工会获得3分"
        }

        id = 0
        '''其行动效果均已写入action_effect方法中'''
            
    class BookAction(EffectObject):

        name_dict = {i: f"书行动板块{i}" for i in range(1,7)}

        effect_desc_dict = {
            1: "花费1本书：获得5魔力",
            2: "花费1本书：选一轨道推2格",
            3: "花费2本书：获得6块钱",
            4: "花费2本书：将1个车间免费升级为工会",
            5: "花费2本书：每已有1个工会获得2分",
            6: "花费3本书：获得3个铲子"
        }
        
        id = 0
        
        # 当回合结束时
        def round_end(self):
            # 清空控制者列表
            self.owner_list.clear()
            yield from super().round_end()

    class CityTile(EffectObject):

        name_dict = {i: f"城片板块{i}" for i in range(1,8)}

        effect_desc_dict = {
            1: "立即效果：获得2本书 + 5分",
            2: "立即效果：四个学科轨道各推1格 + 7分",
            3: "立即效果：获得2个铲子 + 5分",
            4: "立即效果：获得8魔力 + 8分",
            5: "立即效果：获得3个矿石 + 4分",
            6: "立即效果：获得1个米宝 + 8分",
            7: "立即效果：获得6块钱 + 6分"
        }
        
        id = 0
        max_owner = 3

        # 同一玩家可重复获取
        def check_get(self, player_id: int) -> bool:
            if len(self.owner_list) >= self.max_owner:
                return False
            return True
        
        def get(self, got_player_id):
            yield from super().get(got_player_id)
            yield from self.game_state.action_effect(player_id=got_player_id, get_city_tile=True)

        def execute_immediate_effect(self, executed_player_id):
            self.game_state.players[executed_player_id].citys_amount += 1
            yield from super().execute_immediate_effect(executed_player_id)

    class MagicsAction(EffectObject):
        
        name_dict = {i: f"魔力行动板块{i}" for i in range(1,7)}

        effect_desc_dict = {
            1: "花费 3 魔力：建造 1 座桥梁",
            2: "花费 3 魔力：获得 1 个米宝",
            3: "花费 4 魔力：获得 2 个矿",
            4: "花费 4 魔力：获得 7 块钱",
            5: "花费 4 魔力：获得 1 个铲子",
            6: "花费 6 魔力：获得 2 个铲子"
        }

        id = 0
        
        # 立即效果
        def execute_immediate_effect(self, executed_player_id):
            # 幻术师行动效果
            if self.game_state.players[executed_player_id].faction_id == 4:
                self.immediate_effect.extend([
                    ('score','get','board',2 if self.game_state.num_players in [4,5] else 1)
                ])
            yield from super().execute_immediate_effect(executed_player_id)
        
        # 当回合结束时
        def round_end(self):
            # 清空控制者列表
            self.owner_list.clear()
            yield from super().round_end()

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
            yield from super().execute_immediate_effect(executed_player_id)

    class LakePlanningCard(PlanningCard):

        id = 3

        def execute_immediate_effect(self, executed_player_id):
            '''立即效果: 免费提升1航行'''
            self.immediate_effect.extend([
                ('navigation',),
            ])
            yield from super().execute_immediate_effect(executed_player_id)
        
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
            yield from super().execute_immediate_effect(executed_player_id)
        
    class MountainPlanningCard(PlanningCard):

        id = 5
        
        def execute_income_effect(self, executed_player_id):
            '''收入阶段: 收入额外2块+第一个工会多收入1块'''
            self.income_effect.extend([
                ('money', 'get', 2),
                ('money', 'get', min(1, 4-self.game_state.players[executed_player_id].buildings[2]))
            ])
            yield from super().execute_income_effect(executed_player_id)
                
    class WastelandPlanningCard(PlanningCard):

        id = 6

        def execute_setup_effect(self, executed_player_id):
            '''初始设置阶段: 获取任意1书'''
            self.setup_effect.extend([ 
                ('book','get','any',1), 
            ])
            yield from super().execute_setup_effect(executed_player_id)

        def execute_immediate_effect(self, executed_player_id):
            '''立即效果: 获取1矿'''
            self.immediate_effect.extend([
                ('ore','get',1)
            ])
            yield from super().execute_immediate_effect(executed_player_id)

            '''行动效果：第二项发明少付1书'''
            # 已写进获取高科板块的检查获取花费中

    class DesertPlanningCard(PlanningCard):

        id = 7

        def execute_setup_effect(self, executed_player_id):
            '''初始设置阶段: 在初始建筑摆放完毕后立即一铲不可建房'''
            self.setup_effect.extend([
                ('spade', 1, False)
            ])
            yield from super().execute_setup_effect(executed_player_id)

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
            yield from super().execute_immediate_effect(executed_player_id)
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
            yield from super().execute_immediate_effect(executed_player_id)
            
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
            yield from super().execute_immediate_effect(executed_player_id)

        '''行动效果: 每用一铲获得2块钱'''
        # 哥布林行动效果已写入action_effect中

    class IllusionistsFaction(Faction):

        id = 4

        def execute_immediate_effect(self, executed_player_id):
            '''立即效果: 医学轨道推两格'''
            self.immediate_effect.extend([
                ('tracks','medical',2)
            ])
            yield from super().execute_immediate_effect(executed_player_id)
        
        '''行动效果: 每次执行魔力行动时, 少花费一点魔力并获得板面分数 (1分, 4-5人局2分)'''
        # 已写进EffectObject的MagicsAction中

    class InventorsFaction(Faction):

        id = 5

        def execute_setup_effect(self, executed_player_id):
            '''初始设置阶段: 获取任一能力板块'''
            self.setup_effect.extend([
                ('ability_tile',)
            ])
            yield from super().execute_setup_effect(executed_player_id)

    class LizardsFaction(Faction):

        id = 6

        def execute_setup_effect(self, executed_player_id):
            '''初始设置阶段: 任意轨道推一格执行两次'''
            self.setup_effect.extend([
                ('tracks','any',2)
            ])
            yield from super().execute_setup_effect(executed_player_id)

        '''行动效果: 当建城时, 立即免费一铲 + 免费建造一个车间 (无需在刚刚铲的地块上)'''
        # 已写进GameState的action_effect和adjust_building方法中

    class MolesFaction(Faction):

        id = 7

        def execute_immediate_effect(self, executed_player_id):
            '''立即效果: 工程轨道推两格'''
            self.immediate_effect.extend([
                ('tracks','engineering',2)
            ])
            yield from super().execute_immediate_effect(executed_player_id)
        
        additional_action_name = 'additional_action_moles_faction'
        
        def additional_action(self, mode, player_id, args=tuple()) -> list[int]|Callable[[], Generator]:
            '''附加行动: 支付1矿跨越一个地块执行地形改造和/或建造车间并获得2+num_players分'''
            '''附加可用行动: 支付1矿, 建造1座桥梁, 连接两侧建筑, 视为相邻''' # TODO 鼹鼠 附加可用行动
            match mode:
                case 'check':
                    if (
                        # 判断不处于初始阶段
                        self.game_state.round != 0
                        # 判断主要行动是否未完成
                        and self.game_state.players[player_id].main_action_is_done == False
                    ):
                        # 所有可用行动id: 339-345
                        available_action_ids_list = []
                        # 遍历查找最大支持铲i下再建造车间的花销（隧道费用+铲地费用+建房费用），得到i
                        max_shovel_times_for_build = 3
                        for i in range(4):
                            if not self.game_state.check(player_id, [('money',2), ('ore',2+i*self.game_state.players[player_id].shovel_level),('building',1)]):
                                max_shovel_times_for_build = i-1
                                break
                        # 遍历查找最大支持铲i下单不建造的花销（隧道费用+铲地费用），得到i
                        max_shovel_times_for_only_shovel = 3
                        for i in range(1,4):
                            if not self.game_state.check(player_id, [('ore', 1+i*self.game_state.players[player_id].shovel_level)]):
                                max_shovel_times_for_only_shovel = i-1
                                break
              
                        # 创建可抵达范围内需要x铲才能成为原生地的地形是否存在的字典
                        reachable_terrain_need_shovel_times_typs = {i: False for i in range(4)}

                        # 创建跨一地块范围坐标集合（未排除已被控制与水域地块）
                        available_map_ids = set()
                        for i,j in self.game_state.players[player_id].controlled_map_ids:
                            two_direction = [(-2,-1),(-2,0),(-2,1),(-1,i%2-2),(-1,i%2+1),(0,-2),(0,2),(1,i%2-2),(1,i%2+1),(2,-1),(2,0),(2,1)]
                            available_map_ids |= {(i+dx,j+dy) for dx,dy in two_direction if 0 <= i+dx <= 8 and 0 <= j+dy <= 12}
                        for i,j in self.game_state.players[player_id].controlled_map_ids:
                            one_direction = [(-1,i%2-1),(-1,i%2),(0,-1),(0,1),(1,i%2-1),(1,i%2)]
                            available_map_ids -= {(i+dx,j+dy) for dx,dy in one_direction if 0 <= i+dx <= 8 and 0 <= j+dy <= 12}

                        # 遍历跨一地块范围坐标集合，确定存在几铲地类型
                        for i,j in available_map_ids:
                            # 获取当前地块地形和控制者
                            terrain, controller = self.game_state.map_board_state.map_grid[i][j][:2]
                            # 排除水域与已有控制者的地块
                            if terrain != 0 and controller == -1:
                                # 将需要x铲才能成为原生地的地形标记为存在
                                reachable_terrain_need_shovel_times_typs[self.game_state.players[player_id].terrain_id_need_shovel_times[terrain]] = True

                        # 如果合法范围地块中铲成原生地所需的最小次数 小于等于 最大可支持建造车间前铲的次数，则允许该行动：跨越一地块铲成原生地（如需）并建造一个车间
                        for temp_max_shovel_times_for_build in range(max_shovel_times_for_build,-1,-1):
                            if reachable_terrain_need_shovel_times_typs[temp_max_shovel_times_for_build] == True:
                                available_action_ids_list.append(339 + temp_max_shovel_times_for_build)
                                break

                        # 合法范围地块中铲成原生地所需的最大次数 与 最大可支持不建造仅铲的次数 的两者小值 是最大可铲次数
                        # 则允许行动：跨越一地块铲 1~最大可铲次数 下但不建造（若最大可铲次数为0，则无可用行动）
                        for temp_shovel_times_for_only_shovel in range(1, max_shovel_times_for_only_shovel+1):
                            if any(
                                reachable_terrain_need_shovel_times_typs[t] == True
                                for t in range(temp_shovel_times_for_only_shovel, 4)
                            ):
                                action_id = 342 + temp_shovel_times_for_only_shovel
                                available_action_ids_list.append(action_id)

                        # 返回可用行动id列表
                        return available_action_ids_list    
                    else:
                        return []
                    
                case 'execute':
                    def execute_function():
                        # 设置主行动已执行
                        self.game_state.players[player_id].main_action_is_done = True
                        # 参数长度大于1，则未铲后建造行动，反之为仅铲行动
                        if len(args) > 1:
                            # 获取铲子和建筑参数
                            max_shovel_times, *build_args = args
                            # 支付1矿，执行建造行动，并获得2+num_players分
                            yield from self.game_state.adjust(player_id, [('ore','use',1),('building',*build_args),('score','get','board',2+self.game_state.num_players)])
                        else:
                            # 获取铲子参数
                            shovel_times = args[0]
                            # 立即选择位置
                            yield from self.game_state.invoke_immediate_action(player_id, ('select_position','non_adjacent',(2,'shovel',shovel_times))) 
                            # 支付1矿，执行铲子行动，并获得2+num_players分
                            yield from self.game_state.adjust(player_id, [('ore','use',1),('land', shovel_times),('score','get','board',2+self.game_state.num_players)])
                    
                    return execute_function

            '''特殊效果: 终局计分将跨越1地块视为可抵达,即使无剩余矿'''
            # 已在最终计分中实现
        
    class MonksFaction(Faction):

        id = 8

        def execute_immediate_effect(self, executed_player_id):
            '''立即效果: 法律轨道推一格'''
            self.immediate_effect.extend([
                ('tracks','law',1)
            ])
            yield from super().execute_immediate_effect(executed_player_id)

        '''初始设置阶段: 取消摆放两个工会，而是摆放一个大学作为初始建筑'''
        # 写成check_setup_building_action中了

    class NavigatorsFaction(Faction):

        id = 9

        def execute_immediate_effect(self, executed_player_id):
            '''立即效果: 法律轨道推三格'''
            self.immediate_effect.extend([
                ('tracks','law',3)
            ])
            yield from super().execute_immediate_effect(executed_player_id)

        '''行动效果: 当工会建造在河边时, 获得2版面分数'''
        # 航海家行动效果已写入action_effect中

    class OmarFaction(Faction):

        id = 10

        def execute_immediate_effect(self, executed_player_id):
            '''立即效果: 银行、工程轨道推一格'''
            self.immediate_effect.extend([
                ('tracks','bank',1), 
                ('tracks','engineering',1)
            ])
            yield from super().execute_immediate_effect(executed_player_id)
            
        '''初始设置阶段: 可额外摆放一个中立塔楼作为初始建筑'''
        # 写成check_setup_building_action中了

        def execute_income_effect(self, executed_player_id):
            '''回合收入阶段: 获得2魔力 + 2块钱'''
            self.income_effect.extend([
                ('magics','get',2),
                ('money','get',2)
            ])
            yield from super().execute_income_effect(executed_player_id)

    class PhilosophersFaction(Faction):

        id = 11

        def execute_immediate_effect(self, executed_player_id):
            '''立即效果: 银行轨道推两格'''
            self.immediate_effect.extend([
                ('tracks','bank',2)
            ])
            yield from super().execute_immediate_effect(executed_player_id)

        '''行动效果: 获取能力板块时, 多获得对应学科的书1本'''
        # 哲学家行动效果已写入action_effect中

        additional_action_name = 'additional_action_philosophers_faction'
        
        def additional_action(self, mode, player_id, args=tuple()) -> list[int]|Callable[[], Generator]:
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
                    def execute_function():
                        # 设置主行动已执行
                        self.game_state.players[player_id].main_action_is_done = True
                        # 设置每回合一次附加行动已执行
                        self.additional_action_is_done[player_id] = True
                        # 获取奖励
                        yield from self.game_state.adjust(player_id, [('book', 'get', 'any', 1)])
                    return execute_function

    class PsychicsFaction(Faction):

        id = 12

        def execute_immediate_effect(self, executed_player_id):
            '''立即效果: 银行、医学轨道推一格 + 获取1矿'''
            self.immediate_effect.extend([
                ('tracks','bank',1), 
                ('tracks','medical',1),
                ('ore','get',1)
            ])
            yield from super().execute_immediate_effect(executed_player_id)

        additional_action_name = 'additional_action_psychics_faction'
        
        def additional_action(self, mode, player_id, args=tuple()) -> list[int]|Callable[[], Generator]:
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
                    def execute_function():
                        # 不设置主行动执行
                        # 设置每回合一次附加行动已执行
                        self.additional_action_is_done[player_id] = True
                        # 获取奖励
                        yield from self.game_state.adjust(player_id, [('magics', 'get', 5)])
                    
                    return execute_function

    class PalaceTile1(PalaceTile):

        id = 1
        
        def execute_income_effect(self, executed_player_id):
            '''收入效果: 获得5魔力'''
            self.income_effect.extend([
                ('magics','get', 5)
            ])
            yield from super().execute_income_effect(executed_player_id)

        additional_action_name = 'additional_action_palace_tile_1'
        
        def additional_action(self, mode, player_id, args=tuple()) -> list[int]|Callable[[], Generator]:
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
                        # 检查其宫殿板块是否已激活
                        and self.game_state.players[player_id].is_got_palace == True
                    ):
                        return [290]
                    else:
                        return []
                    
                case 'execute':
                    def execute_function():
                        # 设置主行动已执行
                        self.game_state.players[player_id].main_action_is_done = True
                        # 设置每回合一次附加行动已执行
                        self.additional_action_is_done[player_id] = True
                        # 获取奖励
                        yield from self.game_state.adjust(player_id, [('ore', 'get', 2)])

                    return execute_function

    class PalaceTile2(PalaceTile):
        
        id = 2
        additional_action_name = 'additional_action_palace_tile_2'
        
        def additional_action(self, mode, player_id, args=tuple()) -> list[int]|Callable[[], Generator]:
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
                        # 检查其宫殿板块是否已激活
                        and self.game_state.players[player_id].is_got_palace == True
                    ):
                        return [291]
                    else:
                        return []
                    
                case 'execute':
                    def execute_function():
                        # 设置主行动已执行
                        self.game_state.players[player_id].main_action_is_done = True
                        # 设置每回合一次附加行动已执行
                        self.additional_action_is_done[player_id] = True
                        # 获取奖励
                        yield from self.game_state.adjust(player_id, [('spade', 2)])

                    return execute_function

    class PalaceTile3(PalaceTile):
        
        id = 3
        
        def execute_income_effect(self, executed_player_id):
            '''收入效果: 获得2魔力'''
            self.income_effect.extend([
                ('magics','get', 2)
            ])
            yield from super().execute_income_effect(executed_player_id)

        additional_action_name = 'additional_action_palace_tile_3'
        
        def additional_action(self, mode, player_id, args=tuple()) -> list[int]|Callable[[], Generator]:
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
                        # 检查其宫殿板块是否已激活
                        and self.game_state.players[player_id].is_got_palace == True
                    ):
                        return [292]
                    else:
                        return []
                    
                case 'execute':
                    def execute_function():
                        # 设置主行动已执行
                        self.game_state.players[player_id].main_action_is_done = True
                        # 设置每回合一次附加行动已执行
                        self.additional_action_is_done[player_id] = True
                        # 选择降级位置
                        yield from self.game_state.invoke_immediate_action(player_id, ('select_position', 'controlled', (4, None))) 
                        # 执行降级行动并获取奖励
                        yield from self.game_state.adjust(player_id, [
                            ('building', 'degrade', 2, False), 
                            ('score', 'get', 'board', 3), 
                            ('ore', 'get', 1)
                        ]) 
                    return execute_function

    class PalaceTile4(PalaceTile):

        id = 4
        
        def execute_income_effect(self, executed_player_id):
            '''收入效果: 获得2魔力'''
            self.income_effect.extend([
                ('magics','get', 2)
            ])
            yield from super().execute_income_effect(executed_player_id)

        additional_action_name = 'additional_action_palace_tile_4'
        
        def additional_action(self, mode, player_id, args=tuple()) -> list[int]|Callable[[], Generator]:
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
                        # 检查其宫殿板块是否已激活
                        and self.game_state.players[player_id].is_got_palace == True
                    ):
                        return [293]
                    else:
                        return []
                    
                case 'execute':
                    def execute_function():
                        # 设置主行动已执行
                        self.game_state.players[player_id].main_action_is_done = True
                        # 设置每回合一次附加行动已执行
                        self.additional_action_is_done[player_id] = True
                        # 选择升级位置
                        yield from self.game_state.invoke_immediate_action(player_id, ('select_position', 'controlled', (1, 'alone_or_neighbor'))) 
                        # 执行升级行动
                        yield from self.game_state.adjust(player_id, [('building', 'upgrade_special', 2, False)])
                    return execute_function

    class PalaceTile5(PalaceTile):

        id = 5
        
        def execute_income_effect(self, executed_player_id):
            '''收入效果: 获得4魔力'''
            self.income_effect.extend([
                ('magics','get', 4)
            ])
            yield from super().execute_income_effect(executed_player_id)

        def execute_immediate_effect(self, executed_player_id):
            '''立即效果: 获得1能力板块'''
            self.immediate_effect.extend([
                ('ability_tile',)
            ])
            yield from super().execute_immediate_effect(executed_player_id)

    class PalaceTile6(PalaceTile):

        id = 6
        
        def execute_income_effect(self, executed_player_id):
            '''收入效果: 获得2魔力 + 1书'''
            self.income_effect.extend([
                ('magics','get', 4),
                ('book', 'get', 'any', 1)
            ])
            yield from super().execute_income_effect(executed_player_id)

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
                        # 检查其宫殿板块是否已激活
                        and self.game_state.players[player_id].is_got_palace == True
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
                    yield from self.game_state.adjust(player_id, [('tracks', 'any', 2)])        

    class PalaceTile7(PalaceTile):

        id = 7
        
        def execute_income_effect(self, executed_player_id):
            '''收入效果: 获得4魔力'''
            self.income_effect.extend([
                ('magics', 'get', 4)
            ])
            yield from super().execute_income_effect(executed_player_id)

        def execute_pass_effect(self, executed_player_id):
            '''略过效果: 每1学院获得1分'''
            building_nums = (
                (3 - self.game_state.players[executed_player_id].buildings[4])
                + self.game_state.players[executed_player_id].buildings[12]
            )
            self.pass_effect.extend([
                ('score', 'get', 'board', 3 * building_nums)
            ])
            yield from super().execute_pass_effect(executed_player_id)

    class PalaceTile8(PalaceTile):

        id = 8
        
        def execute_income_effect(self, executed_player_id):
            '''收入效果: 获得2块钱 + 1矿 + 2魔力'''
            self.income_effect.extend([
                ('money', 'get', 2),
                ('ore', 'get', 1),
                ('magics', 'get', 2)
            ])
            yield from super().execute_income_effect(executed_player_id)
        
        # 允许6魔力建城，已写进city_establishment_check特判中

    class PalaceTile9(PalaceTile):

        id = 9

        def execute_income_effect(self, executed_player_id):
            '''收入效果: 获得1米宝'''
            self.income_effect.extend([
                ('meeple', 'get', 1)
            ])
            yield from super().execute_income_effect(executed_player_id)


        additional_action_name = 'additional_action_palace_tile_9'
        
        def additional_action(self, mode, player_id, args=tuple()) -> list[int]|Callable[[], Generator]:
            '''附加行动: 支付1米宝跨越一至两个地块执行地形改造和/或建造车间并获得5分'''
            match mode:
                case 'check':
                    if (
                        # 判断不处于初始阶段
                        self.game_state.round != 0
                        # 判断主要行动是否未完成
                        and self.game_state.players[player_id].main_action_is_done == False
                        # 检查是否能支付飞行的1米宝费用
                        and self.game_state.check(player_id, [('meeple','self',1)])
                        # 检查其宫殿板块是否已激活
                        and self.game_state.players[player_id].is_got_palace == True
                    ):  
                        # 所有可用行动id: 349-355
                        available_action_ids_list = []
                        # 遍历查找最大支持铲i下再建造车间的花销（铲地费用+建房费用），得到i
                        max_shovel_times_for_build = 3
                        for i in range(4):
                            if not self.game_state.check(player_id, [('money',2), ('ore',1+i*self.game_state.players[player_id].shovel_level),('building',1)]):
                                max_shovel_times_for_build = i-1
                                break
                        # 遍历查找最大支持铲i下单不建造的花销（铲地费用），得到i
                        max_shovel_times_for_only_shovel = 3
                        for i in range(1,4):
                            if not self.game_state.check(player_id, [('ore', i*self.game_state.players[player_id].shovel_level)]):
                                max_shovel_times_for_only_shovel = i-1
                                break
              
                        # 创建可抵达范围内需要x铲才能成为原生地的地形是否存在的字典
                        reachable_terrain_need_shovel_times_typs = {i: False for i in range(4)}

                        # 创建跨一地块范围坐标集合（未排除已被控制与水域地块）
                        available_map_ids = set()
                        for i,j in self.game_state.players[player_id].controlled_map_ids:
                            two_direction = [(-2,-1),(-2,0),(-2,1),(-1,i%2-2),(-1,i%2+1),(0,-2),(0,2),(1,i%2-2),(1,i%2+1),(2,-1),(2,0),(2,1)]
                            available_map_ids |= {(i+dx,j+dy) for dx,dy in two_direction if 0 <= i+dx <= 8 and 0 <= j+dy <= 12}
                        for i,j in self.game_state.players[player_id].controlled_map_ids:
                            three_direction = [(-3,i%2-2),(-3,i%2-1),(-3,i%2),(-3,i%2+1),(-2,-2),(-2,1),(-1,i%2-3),(-1,i%2+2),(0,-3),(0,3),(1,i%2-3),(1,i%2+2),(2,-2),(2,1),(3,i%2-2),(3,i%2-1),(3,i%2),(3,i%2+1)]
                            available_map_ids |= {(i+dx,j+dy) for dx,dy in three_direction if 0 <= i+dx <= 8 and 0 <= j+dy <= 12}
                        for i,j in self.game_state.players[player_id].controlled_map_ids:
                            one_direction = [(-1,i%2-1),(-1,i%2),(0,-1),(0,1),(1,i%2-1),(1,i%2)]
                            available_map_ids -= {(i+dx,j+dy) for dx,dy in one_direction if 0 <= i+dx <= 8 and 0 <= j+dy <= 12}

                        # 遍历跨一地块范围坐标集合，确定存在几铲地类型
                        for i,j in available_map_ids:
                            # 获取当前地块地形和控制者
                            terrain, controller = self.game_state.map_board_state.map_grid[i][j][:2]
                            # 排除水域与已有控制者的地块
                            if terrain != 0 and controller == -1:
                                # 将需要x铲才能成为原生地的地形标记为存在
                                reachable_terrain_need_shovel_times_typs[self.game_state.players[player_id].terrain_id_need_shovel_times[terrain]] = True

                        # 如果合法范围地块中铲成原生地所需的最小次数 小于等于 最大可支持建造车间前铲的次数，则允许该行动：跨越一地块铲成原生地（如需）并建造一个车间
                        for temp_max_shovel_times_for_build in range(max_shovel_times_for_build,-1,-1):
                            if reachable_terrain_need_shovel_times_typs[temp_max_shovel_times_for_build] == True:
                                available_action_ids_list.append(349 + temp_max_shovel_times_for_build)
                                break

                        # 合法范围地块中铲成原生地所需的最大次数 与 最大可支持不建造仅铲的次数 的两者小值 是最大可铲次数
                        # 则允许行动：跨越一地块铲 1~最大可铲次数 下但不建造（若最大可铲次数为0，则无可用行动）
                        for temp_shovel_times_for_only_shovel in range(1, max_shovel_times_for_only_shovel+1):
                            if any(
                                reachable_terrain_need_shovel_times_typs[t] == True
                                for t in range(temp_shovel_times_for_only_shovel, 4)
                            ):
                                action_id = 352 + temp_shovel_times_for_only_shovel
                                available_action_ids_list.append(action_id)

                        # 返回可用行动id列表
                        return available_action_ids_list    
                    else:
                        return []
                    
                case 'execute':
                    def execute_function():
                        # 设置主行动已执行
                        self.game_state.players[player_id].main_action_is_done = True
                        # 参数长度大于1，则未铲后建造行动，反之为仅铲行动
                        if len(args) > 1:
                            # 获取铲子和建筑参数
                            max_shovel_times, *build_args = args
                            # 支付1米宝，执行建造行动，并获得5分
                            yield from self.game_state.adjust(player_id, [('meeple','use',1),('building',*build_args),('score','get','board',5)])
                        else:
                            # 获取铲子参数
                            shovel_times = args[0]
                            # 立即选择位置
                            yield from self.game_state.invoke_immediate_action(player_id, ('select_position','non_adjacent',(3,'shovel',shovel_times))) 
                            # 支付1米宝，执行铲子行动，并获得5分
                            yield from self.game_state.adjust(player_id, [('meeple','use',1),('land', shovel_times),('score','get','board',5)])
                    
                    return execute_function
            '''特殊效果: 终局计分将跨越1-2地块视为可抵达，即使无剩余米宝'''
            # 已在最终计分中实现

    class PalaceTile10(PalaceTile):

        id = 10
        
        def execute_income_effect(self, executed_player_id):
            '''收入效果: 获得6块钱'''
            self.income_effect.extend([
                ('money', 'get', 6)
            ])
            yield from super().execute_income_effect(executed_player_id)

        def execute_immediate_effect(self, executed_player_id):
            '''立即效果: 获得12转魔 + 2书'''
            self.immediate_effect.extend([
                ('magics', 'get', 12),
                ('book', 'get', 'any', 2)
            ])
            yield from super().execute_immediate_effect(executed_player_id)

    class PalaceTile11(PalaceTile):

        id = 11
        
        def execute_income_effect(self, executed_player_id):
            '''收入效果: 获得1矿'''
            self.income_effect.extend([
                ('ore', 'get', 1)
            ])
            yield from super().execute_income_effect(executed_player_id)

        def execute_immediate_effect(self, executed_player_id):
            '''立即效果: 获得1城片'''
            self.immediate_effect.extend([
                ('ability_tile',)
            ])
            yield from super().execute_immediate_effect(executed_player_id)

    class PalaceTile12(PalaceTile):

        id = 12
        
        def execute_income_effect(self, executed_player_id):
            '''收入效果: 获得8转魔'''
            self.income_effect.extend([
                ('magics', 'get', 8)
            ])
            yield from super().execute_income_effect(executed_player_id)
        
        '''行动效果: 每建造1车间获得2分'''
        # 建造行动效果已写入action_effect中

    class PalaceTile13(PalaceTile):

        id = 13
        
        additional_action_name = 'additional_action_palace_tile_13'
        
        def additional_action(self, mode, player_id, args=tuple()) -> list[int]|Callable[[], Generator]:
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
                        # 检查其宫殿板块是否已激活
                        and self.game_state.players[player_id].is_got_palace == True
                    ):
                        return [295]
                    else:
                        return []
                    
                case 'execute':
                    def execute_function():
                        # 设置主行动已执行
                        self.game_state.players[player_id].main_action_is_done = True
                        # 设置每回合一次附加行动已执行
                        self.additional_action_is_done[player_id] = True
                        # 获取奖励
                        yield from self.game_state.adjust(player_id, [
                            ('money', 'get', 3),
                            ('book', 'get', 'any', 1)
                        ])
                    return execute_function
                    
        '''行动效果: 每建造1工会获得3分'''
        # 建造行动效果已写入action_effect中

    class PalaceTile14(PalaceTile):

        id = 14
        
        def execute_income_effect(self, executed_player_id):
            '''收入效果: 获得6转魔'''
            self.income_effect.extend([
                ('magics', 'get', 6)
            ])
            yield from super().execute_income_effect(executed_player_id)

        additional_action_name = 'additional_action_palace_tile_14'
        
        def additional_action(self, mode, player_id, args=tuple()) -> list[int]|Callable[[], Generator]:
            '''附加行动: 跨越1河流地块建城'''
            match mode:
                case 'check':
                    if (
                        # 判断不处于初始阶段
                        self.game_state.round != 0
                        # 检查其宫殿板块是否已激活
                        and self.game_state.players[player_id].is_got_palace == True
                    ):
                        # 获取所有水域地块
                        all_water_pos = [
                            (x,y) for x in range(9) for y in range(13) 
                            if self.game_state.map_board_state.map_grid[x][y][0] == 0
                        ]

                        # 遍历所有水域地块
                        for i,j in all_water_pos:
                            # 获取相邻的聚落（以根节点为代表）
                            adjacent_settlements = set()

                            # 建立搜索方向
                            direction = [(-1,i%2-1),(-1,i%2),(0,-1),(0,1),(1,i%2-1),(1,i%2)]

                            # 遍历所有相邻的地块
                            for dx,dy in direction:
                                new_i, new_j = i+dx, j+dy
                                if (
                                    # 边界检查
                                    0 <= new_i <= 8 and 0 <= new_j <= 12
                                    # 排除水域地块
                                    and self.game_state.map_board_state.map_grid[new_i][new_j][0] != 0
                                    # 确保控制者为当前玩家
                                    and self.game_state.map_board_state.map_grid[new_i][new_j][1] == player_id
                                ): 
                                    # 获取该相邻地块上的建筑的聚落根节点
                                    building_root, building_root_is_city = self.game_state.map_board_state.find_settlement_root(
                                        self.game_state.players[player_id].settlements_and_cities,
                                        (new_i, new_j)
                                    )
                                    # 如果该聚落尚未建城
                                    if building_root_is_city == False:
                                        # 则将根节点加入相邻聚落集合中
                                        adjacent_settlements.add(building_root) 

                            # 判断该水域地块相邻地块中是否为存在两个以上未建城聚落    
                            if len(adjacent_settlements) >= 2:

                                curent_settlement_magics_total = 0  # 当前聚落魔力点之和
                                curent_settlement_building_nums = 0 # 当前聚落建筑数量
                                # 遍历所有控制地块，获取其上建筑形成聚落的最少所需要的建筑数
                                city_min_needed_building_nums = 4
                                # 判断建城所需最少的总魔力点数
                                city_min_needed_magics_nums = 7

                                # 遍历所有控制地块
                                for controlled_pos in self.game_state.players[player_id].controlled_map_ids:
                                    # 获取控制地库的根节点
                                    controlled_pos_root, _ = self.game_state.map_board_state.find_settlement_root(
                                        self.game_state.players[player_id].settlements_and_cities,
                                        controlled_pos
                                    )
                                    # 如果该控制地块的根节点在相邻聚落集合中
                                    if controlled_pos_root in adjacent_settlements:
                                        cur_i,cur_j = controlled_pos
                                        # 则获取该建筑对应魔力点
                                        building_id, num_side_building = self.game_state.map_board_state.map_grid[cur_i][cur_j][2:4]
                                        magics_num = self.game_state.map_board_state.building_magic[building_id] + num_side_building
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

                                # 判断当前聚落是否满足建城条件
                                if (
                                    # 判断当前聚落魔力点数和是否大于等于最低建城所需总魔力点数
                                    curent_settlement_magics_total >= city_min_needed_magics_nums
                                    # 判断当前聚落建筑数量是否大于等于最低建城所需建筑数
                                    and curent_settlement_building_nums >= city_min_needed_building_nums
                                ): 
                                    return [302]
                        return []     
                    else:
                        return []
                    
                case 'execute':
                    def execute_function():
                        # 可选择建城的水域地块
                        available_water_pos = []
                        # 获取所有水域地块
                        all_water_pos = [
                            (x,y) for x in range(9) for y in range(13) 
                            if self.game_state.map_board_state.map_grid[x][y][0] == 0
                        ]

                        # 遍历所有水域地块
                        for i,j in all_water_pos:
                            # 获取相邻的聚落（以根节点为代表）
                            adjacent_settlements = set()

                            # 建立搜索方向
                            direction = [(-1,i%2-1),(-1,i%2),(0,-1),(0,1),(1,i%2-1),(1,i%2)]

                            # 遍历所有相邻的地块
                            for dx,dy in direction:
                                new_i, new_j = i+dx, j+dy
                                if (
                                    # 边界检查
                                    0 <= new_i <= 8 and 0 <= new_j <= 12
                                    # 排除水域地块
                                    and self.game_state.map_board_state.map_grid[new_i][new_j][0] != 0
                                    # 确保控制者为当前玩家
                                    and self.game_state.map_board_state.map_grid[new_i][new_j][1] == player_id
                                ): 
                                    # 获取该相邻地块上的建筑的聚落根节点
                                    building_root, building_root_is_city = self.game_state.map_board_state.find_settlement_root(
                                        self.game_state.players[player_id].settlements_and_cities,
                                        (new_i, new_j)
                                    )
                                    # 如果该聚落尚未建城
                                    if building_root_is_city == False:
                                        # 则将根节点加入相邻聚落集合中
                                        adjacent_settlements.add(building_root) 

                            # 判断该水域地块相邻地块中是否为存在两个以上未建城聚落    
                            if len(adjacent_settlements) >= 2:

                                curent_settlement_magics_total = 0  # 当前聚落魔力点之和
                                curent_settlement_building_nums = 0 # 当前聚落建筑数量
                                # 遍历所有控制地块，获取其上建筑形成聚落的最少所需要的建筑数
                                city_min_needed_building_nums = 4
                                # 判断建城所需最少的总魔力点数
                                city_min_needed_magics_nums = 7

                                # 遍历所有控制地块
                                for controlled_pos in self.game_state.players[player_id].controlled_map_ids:
                                    # 获取控制地库的根节点
                                    controlled_pos_root, _ = self.game_state.map_board_state.find_settlement_root(
                                        self.game_state.players[player_id].settlements_and_cities,
                                        controlled_pos
                                    )
                                    # 如果该控制地块的根节点在相邻聚落集合中
                                    if controlled_pos_root in adjacent_settlements:
                                        cur_i,cur_j = controlled_pos
                                        # 则获取该建筑对应魔力点
                                        building_id, num_side_building = self.game_state.map_board_state.map_grid[cur_i][cur_j][2:4]
                                        magics_num = self.game_state.map_board_state.building_magic[building_id] + num_side_building
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

                                # 判断当前聚落是否满足建城条件
                                if (
                                    # 判断当前聚落魔力点数和是否大于等于最低建城所需总魔力点数
                                    curent_settlement_magics_total >= city_min_needed_magics_nums
                                    # 判断当前聚落建筑数量是否大于等于最低建城所需建筑数
                                    and curent_settlement_building_nums >= city_min_needed_building_nums
                                ): 
                                    # 将合法可建城水域地块加入集合中
                                    available_water_pos.append((i,j))
                        
                        # 调起选位行动，从合法可建城水域地块中选择一个
                        if available_water_pos:
                            yield from self.game_state.invoke_immediate_action(player_id, ('select_position', 'water', available_water_pos)) 
                        else:
                            raise Exception('没有可建城水域地块')
                        
                        # 待合并聚落集合（以跟节点坐标为代表）
                        to_be_merged_settlements = set()
                        # 获取选择的地块坐标
                        i,j = self.game_state.players[player_id].choice_position
                        # 遍历相邻地块获取待合并聚落的根节点
                        direction = [(-1,i%2-1),(-1,i%2),(0,-1),(0,1),(1,i%2-1),(1,i%2)]
                        for dx,dy in direction:
                            new_i, new_j = i + dx, j + dy
                            if (
                                # 边界检查
                                0 <= new_i <= 8 and 0 <= new_j <= 12
                                # 排除水域地块
                                and self.game_state.map_board_state.map_grid[new_i][new_j][0] != 0
                                # 确保控制者为当前玩家
                                and self.game_state.map_board_state.map_grid[new_i][new_j][1] == player_id
                            ): 
                                # 获取该相邻地块上的建筑的聚落根节点
                                building_root, building_root_is_city = self.game_state.map_board_state.find_settlement_root(
                                    self.game_state.players[player_id].settlements_and_cities,
                                    (new_i, new_j)
                                )
                                # 如果该聚落尚未建城
                                if building_root_is_city == False:
                                    # 则将根节点加入相邻聚落集合中
                                    to_be_merged_settlements.add(building_root)
                        # 合并聚落
                        to_be_merged_settlements = list(to_be_merged_settlements)
                        if len(to_be_merged_settlements) == 3:
                            self.game_state.map_board_state.merge_settlement_root(
                                self.game_state.players[player_id].settlements_and_cities,
                                to_be_merged_settlements[2],
                                to_be_merged_settlements[0]
                            )
                            self.game_state.map_board_state.merge_settlement_root(
                                self.game_state.players[player_id].settlements_and_cities,
                                to_be_merged_settlements[1],
                                to_be_merged_settlements[0]
                            )
                        elif len(to_be_merged_settlements) == 2:
                            self.game_state.map_board_state.merge_settlement_root(
                                self.game_state.players[player_id].settlements_and_cities,
                                to_be_merged_settlements[1],
                                to_be_merged_settlements[0]
                            )
                        else:
                            if len(to_be_merged_settlements) == 1: 
                                raise Exception('没有可合并的聚落或两岸同属一个聚落')
                            if len(to_be_merged_settlements) >= 4:
                                raise Exception('两岸不可能存在4个及以上的聚落')
                        # 获取当前跨越河流合并后多聚落的根节点
                        current_root, current_is_city = self.game_state.map_board_state.find_settlement_root(
                            self.game_state.players[player_id].settlements_and_cities,
                            to_be_merged_settlements[0]
                        )
                        assert current_is_city == False
                        # 标记根节点为城市
                        self.game_state.players[player_id].settlements_and_cities[current_root] = [current_root, True]
                        # 触发立即行动，选取城片（保证一定存在可选城片）
                        for city_tile_id in range(1,8):
                            if self.game_state.all_available_object_dict['city_tile'][city_tile_id].check_get(player_id):                 
                                yield from self.game_state.invoke_immediate_action(player_id, ('select_city_tile',))
                                break

                    return execute_function

        def execute_immediate_effect(self, executed_player_id):
            '''立即效果: 升2级航海'''
            self.immediate_effect.extend([
                ('navigation',),
                ('navigation',)
            ])
            yield from super().execute_immediate_effect(executed_player_id)

    class PalaceTile15(PalaceTile):

        id = 15
        
        def execute_income_effect(self, executed_player_id):
            '''收入效果: 获得6转魔'''
            self.income_effect.extend([
                ('magics', 'get', 6)
            ])
            yield from super().execute_income_effect(executed_player_id)

        def execute_immediate_effect(self, executed_player_id):
            '''立即效果: 获得立即2铲（可建造） + 2书 + 立即建造2桥'''
            self.immediate_effect.extend([
                ('spade', 2),
                ('book', 'get', 'any', 2)
            ])
            for i in range(2):
                if self.game_state.check(executed_player_id, [('bridge',)]):
                    yield from self.game_state.adjust(executed_player_id, [('bridge',)])
                else:
                    break
            yield from super().execute_immediate_effect(executed_player_id)

    class PalaceTile16(PalaceTile):

        id = 16
        
        def execute_income_effect(self, executed_player_id):
            '''收入效果: 获得2转魔 + 1书'''
            self.income_effect.extend([
                ('magics', 'get', 2),
                ('book', 'get', 'any', 1)
            ])
            yield from super().execute_income_effect(executed_player_id)
        
        def execute_immediate_effect(self, executed_player_id):
            '''立即效果: 在任意原生地建造1工会'''
            self.immediate_effect.extend([
                ('building', 'build_special_palace_tile_16', 2, False)
            ])
            yield from super().execute_immediate_effect(executed_player_id)

    class RoundBooster1(RoundBooster):

        id = 1
        
        def execute_immediate_effect(self, executed_player_id):
            '''收入效果: 获得临时1航行'''
            self.game_state.players[executed_player_id].temp_navigation = True
            yield from super().execute_immediate_effect(executed_player_id)
        
        def execute_pass_effect(self, executed_player_id):
            '''略过效果: 取消临时1航行'''
            self.game_state.players[executed_player_id].temp_navigation = False
            yield from super().execute_pass_effect(executed_player_id)

        '''行动效果: 每建造1个位于河边的车间获得2分'''
        # 建筑建造行动效果已写入action_effect方法中

    class RoundBooster2(RoundBooster):

        id = 2
        
        def execute_income_effect(self, executed_player_id):
            '''收入效果: 获得1矿'''
            self.income_effect.extend([
                ('ore', 'get', 1),
            ])
            yield from super().execute_income_effect(executed_player_id)

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
            yield from super().execute_pass_effect(executed_player_id)

    class RoundBooster3(RoundBooster):

        id = 3

        def execute_income_effect(self, executed_player_id):
            '''收入效果: 获取2矿'''
            self.income_effect.extend([
                ('ore', 'get', 2)
            ])
            yield from super().execute_income_effect(executed_player_id)
        
        additional_action_name = 'additional_action_round_booster_3'
        
        def additional_action(self, mode, player_id, args=tuple()) -> list[int]|Callable[[], Generator]:
            '''每回合一次附加行动: 获取1轨'''
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
                    def execute_function():
                        # 设置主行动已执行
                        self.game_state.players[player_id].main_action_is_done = True
                        # 设置每回合一次附加行动已执行
                        self.additional_action_is_done[player_id] = True
                        # 获取奖励
                        yield from self.game_state.adjust(player_id, [
                            ('tracks', 'any', 1)
                        ])
                    return execute_function

    class RoundBooster4(RoundBooster):

        id = 4
        
        def execute_income_effect(self, executed_player_id):
            '''收入效果: 获得1米宝'''
            self.income_effect.extend([
                ('meeple', 'get', 1)
            ])
            yield from super().execute_income_effect(executed_player_id)

        '''行动效果: 每插入1个米宝获得2分'''
        # 插入米宝行动效果已写入action_effect方法中

    class RoundBooster5(RoundBooster):

        id = 5
        
        additional_action_name = 'additional_action_round_booster_5'
        
        def additional_action(self, mode, player_id, args=tuple()) -> list[int]|Callable[[], Generator]:
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
                    def execute_function():
                        # 设置主行动已执行
                        self.game_state.players[player_id].main_action_is_done = True
                        # 设置每回合一次附加行动已执行
                        self.additional_action_is_done[player_id] = True
                        # 获取奖励
                        yield from self.game_state.adjust(player_id, [
                            ('spade', 1)
                        ])
                    return execute_function
        
        def execute_income_effect(self, executed_player_id):
            '''收入效果: 获得1书'''
            self.income_effect.extend([
                ('book', 'get', 'any', 1)
            ])
            yield from super().execute_income_effect(executed_player_id)

    class RoundBooster6(RoundBooster):

        id = 6
        
        def execute_income_effect(self, executed_player_id):
            '''收入效果: 获得4块钱'''
            self.income_effect.extend([
                ('money', 'get', 4)
            ])
            yield from super().execute_income_effect(executed_player_id)
        
        def execute_pass_effect(self, executed_player_id):
            '''略过效果: 每1学院获得1轨'''
            building_nums = (
                (3 - self.game_state.players[executed_player_id].buildings[4])
                + self.game_state.players[executed_player_id].buildings[12]
            )
            self.pass_effect.extend([
                ('tracks', 'any', building_nums)
            ])
            yield from super().execute_pass_effect(executed_player_id)

    class RoundBooster7(RoundBooster):

        id = 7
        
        def execute_income_effect(self, executed_player_id):
            '''收入效果: 获得3转魔'''
            self.income_effect.extend([
                ('magics', 'get', 3)
            ])
            yield from super().execute_income_effect(executed_player_id)

        '''行动效果: 每建造1个工会获得3分'''
        # 建筑建造行动效果已写入action_effect方法中

    class RoundBooster8(RoundBooster):

        id = 8

        additional_action_name = 'additional_action_round_booster_8'
        
        def additional_action(self, mode, player_id, args=tuple()) -> list[int]|Callable[[], Generator]:
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
                        return [298]
                    else:
                        return []
                    
                case 'execute':
                    def execute_function():
                        # 设置主行动已执行
                        self.game_state.players[player_id].main_action_is_done = True
                        # 设置每回合一次附加行动已执行
                        self.additional_action_is_done[player_id] = True
                        # 建造桥梁
                        yield from self.game_state.adjust(player_id, [('bridge',)])
                    return execute_function
        
        def execute_income_effect(self, executed_player_id):
            '''收入效果: 获得1书'''
            self.income_effect.extend([
                ('book', 'get', 'any', 1)
            ])
            yield from super().execute_income_effect(executed_player_id)

    class RoundBooster9(RoundBooster):

        id = 9
        
        def execute_income_effect(self, executed_player_id):
            '''收入效果: 获得4转魔 + 2块钱'''
            self.income_effect.extend([
                ('magics', 'get', 4),
                ('money', 'get', 2)
            ])
            yield from super().execute_income_effect(executed_player_id)

    class RoundBooster10(RoundBooster):

        id = 10
        
        def execute_income_effect(self, executed_player_id):
            '''收入效果: 获得6块钱'''
            self.income_effect.extend([
                ('money', 'get', 6)
            ])
            yield from super().execute_income_effect(executed_player_id)

    class AbilityTile1(AbilityTile):

        id = 1
        
        def execute_income_effect(self, executed_player_id):
            '''收入效果: 获得1矿 + 1轨'''
            self.income_effect.extend([
                ('ore', 'get', 1),
                ('tracks', 'any', 1)
            ])
            yield from super().execute_income_effect(executed_player_id)

    class AbilityTile2(AbilityTile):

        id = 2

        def execute_income_effect(self, executed_player_id):
            '''收入效果: 获得2分 + 2块钱'''
            self.income_effect.extend([
                ('score', 'get', 'board', 3),
                ('money', 'get', 2)
            ])
            yield from super().execute_income_effect(executed_player_id)
        
    class AbilityTile3(AbilityTile):
        
        id = 3

        def execute_income_effect(self, executed_player_id):
            '''收入效果: 获得1书 + 1魔力'''
            self.income_effect.extend([
                ('book', 'get', 'any', 1),
                ('magics', 'get', 1)
            ])
            yield from super().execute_income_effect(executed_player_id)
        
    class AbilityTile4(AbilityTile):

        id = 4
        
        def execute_immediate_effect(self, executed_player_id):
            '''立即效果: 获得1矿 + 5分 + 2块钱'''
            self.immediate_effect.extend([
                ('ore', 'get', 1),
                ('score', 'get', 'board', 5),
                ('money', 'get', 2)
            ])
            yield from super().execute_immediate_effect(executed_player_id)

    class AbilityTile5(AbilityTile):

        id = 5
        
        def execute_immediate_effect(self, executed_player_id):
            '''立即效果: 立即2铲并可选建造'''
            self.immediate_effect.extend([
                ('spade', 2)
            ])
            yield from super().execute_immediate_effect(executed_player_id)

    class AbilityTile6(AbilityTile):

        id = 6
        
        def execute_immediate_effect(self, executed_player_id):
            '''立即效果: 获得2个侧楼'''
            self.game_state.players[executed_player_id].buildings[8] += 2  
            yield from super().execute_immediate_effect(executed_player_id)

        additional_action_name = 'additional_action_ability_tile_6'
        
        def additional_action(self, mode, player_id, args=tuple()) -> list[int]|Callable[[], Generator]:
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
                    def execute_function():
                        # 设置主行动已执行
                        self.game_state.players[player_id].main_action_is_done = True
                        # 选择建造位置
                        yield from self.game_state.invoke_immediate_action(player_id, ('select_position', 'controlled', (8, None))) 
                        # 执行建造行动
                        yield from self.game_state.adjust(player_id, [('building', 'build_annex', 8, True)])
                    return execute_function

    class AbilityTile7(AbilityTile):

        id = 7
        
        additional_action_name = 'additional_action_ability_tile_7'
        
        def additional_action(self, mode, player_id, args=tuple()) -> list[int]|Callable[[], Generator]:
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
                    def execute_function():
                        # 设置主行动已执行
                        self.game_state.players[player_id].main_action_is_done = True
                        # 设置每回合一次附加行动已执行
                        self.additional_action_is_done[player_id] = True
                        # 获取奖励
                        yield from self.game_state.adjust(player_id, [('magics', 'get', 4)])
                    return execute_function

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
            yield from super().execute_pass_effect(executed_player_id)

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
            yield from super().execute_immediate_effect(executed_player_id)
        
        def execute_income_effect(self, executed_player_id):
            '''收入效果: 获得2魔力 + 2块钱'''
            self.income_effect.extend([
                ('magics', 'get', 2),
                ('money', 'get', 2)
            ])
            yield from super().execute_income_effect(executed_player_id)

    class AbilityTile12(AbilityTile):

        id = 12
        
        def execute_pass_effect(self, executed_player_id):
            '''略过效果: 获得四学科轨最低值的分数'''
            self.pass_effect.extend([
                ('score', 'get', 'board', min(self.game_state.players[executed_player_id].tracks.values()))
            ])
            yield from super().execute_pass_effect(executed_player_id)

    class ScienceTile1(ScienceTile):
        
        id = 1
        additional_action_name = 'additional_action_science_tile_1'
        
        def additional_action(self, mode, player_id, args=tuple()) -> list[int]|Callable[[], Generator]:
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
                    def execute_function():
                        # 设置主行动已执行
                        self.game_state.players[player_id].main_action_is_done = True
                        # 设置每回合一次附加行动已执行
                        self.additional_action_is_done[player_id] = True
                        # 获取奖励
                        yield from self.game_state.adjust(player_id, [
                            ('spade', 1)
                        ])
                    return execute_function
        
        def execute_immediate_effect(self, executed_player_id):
            self.immediate_effect.extend([
                ('book', 'get', 'any', 1),
                ('tracks', 'bank', 1),
                ('tracks', 'law', 1),
                ('tracks', 'engineering', 1),
                ('tracks', 'medical', 1),
            ])
            yield from super().execute_immediate_effect(executed_player_id)

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
            yield from super().execute_pass_effect(executed_player_id)

    class ScienceTile3(ScienceTile):

        id = 3
        additional_action_name = 'additional_action_science_tile_3'
        
        def additional_action(self, mode, player_id, args=tuple()) -> list[int]|Callable[[], Generator]:
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
                    def execute_function():
                        # 设置主行动已执行
                        self.game_state.players[player_id].main_action_is_done = True
                        # 设置每回合一次附加行动已执行
                        self.additional_action_is_done[player_id] = True
                        # 获取奖励
                        yield from self.game_state.adjust(player_id, [
                            ('meeple', 'get', 1),
                            ('score', 'get', 'board', 3)
                        ])
                    return execute_function

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
            yield from super().execute_immediate_effect(executed_player_id)

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
            yield from super().execute_immediate_effect(executed_player_id)

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
            yield from super().execute_immediate_effect(executed_player_id)

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
            yield from super().execute_immediate_effect(executed_player_id)

    class ScienceTile8(ScienceTile):
        
        id = 8
        
        def execute_immediate_effect(self, executed_player_id):
            '''立即效果: 每有1城片获取5分'''
            city_num = self.game_state.players[executed_player_id].citys_amount
            self.immediate_effect.extend([
                ('score', 'get', 'board', 5 * city_num),
            ])
            yield from super().execute_immediate_effect(executed_player_id)

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
            yield from super().execute_immediate_effect(executed_player_id)

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
            yield from super().execute_immediate_effect(executed_player_id)

    class ScienceTile11(ScienceTile):

        id = 11
        
        def execute_immediate_effect(self, executed_player_id: int):
            '''立即效果: 获取1米宝 + 提升1航行 + 提升1铲子'''
            self.immediate_effect.extend([
                ('meeple', 'get', 1),
                ('navigation',),
                ('shovel',),
            ])
            yield from super().execute_immediate_effect(executed_player_id)

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
            yield from super().execute_immediate_effect(executed_player_id)

    class ScienceTile13(ScienceTile):
        
        id = 13
        
        def execute_immediate_effect(self, executed_player_id: int):
            '''立即效果: 建造1个中立的车间'''
            self.immediate_effect.extend([
                ('building', 'build_neutral', 1, True),
            ])
            yield from super().execute_immediate_effect(executed_player_id)

        def execute_income_effect(self, executed_player_id: int):
            '''收入效果: 获取3矿'''
            self.income_effect.extend([
                ('ore', 'get', 3),
            ])
            yield from super().execute_income_effect(executed_player_id)

    class ScienceTile14(ScienceTile):
        
        id = 14
        
        def execute_immediate_effect(self, executed_player_id: int):
            '''立即效果: 建造1个中立的工会'''
            self.immediate_effect.extend([
                ('building', 'build_neutral', 2, True),
            ])
            yield from super().execute_immediate_effect(executed_player_id)
        
        def execute_income_effect(self, executed_player_id: int):
            '''收入效果: 获取5块'''
            self.income_effect.extend([
                ('money', 'get', 5),
            ])
            yield from super().execute_income_effect(executed_player_id)

    class ScienceTile15(ScienceTile):
        
        id = 15
        
        def execute_immediate_effect(self, executed_player_id: int):
            '''立即效果: 建造1个中立的学院 + 获取1能力板块'''
            self.immediate_effect.extend([
                ('building', 'build_neutral', 4, True),
                ('ability_tile',)
            ])
            yield from super().execute_immediate_effect(executed_player_id)

    class ScienceTile16(ScienceTile):
        
        id = 16
        
        def execute_immediate_effect(self, executed_player_id: int):
            '''立即效果: 建造1个中立的大学'''
            self.immediate_effect.extend([
                ('building', 'build_neutral', 5, True),
            ])
            yield from super().execute_immediate_effect(executed_player_id)

        def execute_income_effect(self, executed_player_id: int):
            '''收入效果: 获取2分'''
            self.income_effect.extend([
                ('score', 'get', 'board', 2),
            ])
            yield from super().execute_income_effect(executed_player_id)

    class ScienceTile17(ScienceTile):
        
        id = 17

        def execute_immediate_effect(self, executed_player_id: int):
            '''立即效果: 建造1个中立的宫殿， 并向3区添加2魔力'''
            self.immediate_effect.extend([
                ('building', 'build_neutral', 3, True),
                ('magics', 'science_tile_18', 2)
            ])
            yield from super().execute_immediate_effect(executed_player_id)

        def execute_income_effect(self, executed_player_id: int):
            '''收入效果: 获取4转魔'''
            self.income_effect.extend([
                ('magics', 'get', 4),
            ])
            yield from super().execute_income_effect(executed_player_id)

    class ScienceTile18(ScienceTile):
        
        id = 18
        
        def execute_immediate_effect(self, executed_player_id: int):
            '''立即效果: 建造1个中立的纪念碑 + 获得7分'''
            self.immediate_effect.extend([
                ('building', 'build_neutral', 7, True),
                ('score', 'get', 'board', 7)
            ])
            yield from super().execute_immediate_effect(executed_player_id)

    class RoundScoring1(RoundScoring):

        id = 1
        
        def round_end(self):
            '''回合结束效果: 每有3法律轨，获得1米宝'''
            self.round_end_effect_args = ('meeple', 1, 'law', 3)
            yield from super().round_end()

    class RoundScoring2(RoundScoring):
        
        id = 2
        
        def round_end(self):
            '''回合结束效果: 每有3银行轨，获得4转魔'''
            self.round_end_effect_args = ('magics', 4, 'bank', 3)
            yield from super().round_end()

    class RoundScoring3(RoundScoring):
        
        id = 3
        
        def round_end(self):
            '''回合结束效果: 每有3法律轨，获得1书'''
            self.round_end_effect_args = ('book', 1, 'law', 3)
            yield from super().round_end()

    class RoundScoring4(RoundScoring):
        
        id = 4
        
        def round_end(self):
            '''回合结束效果: 每有4医疗轨，获得1铲'''
            self.round_end_effect_args = ('spade', 1, 'medical', 4)
            yield from super().round_end()

    class RoundScoring5(RoundScoring):
        
        id = 5
        
        def round_end(self):
            '''回合结束效果: 每有1银行轨，获得1块'''
            self.round_end_effect_args = ('money', 1, 'bank', 1)
            yield from super().round_end()

    class RoundScoring6(RoundScoring):
        
        id = 6
        
        def round_end(self):
            '''回合结束效果: 每有2医疗轨，获得1矿'''
            self.round_end_effect_args = ('ore', 1, 'medical', 2)
            yield from super().round_end()

    class RoundScoring7(RoundScoring):
        
        id = 7
        
        def round_end(self):
            '''回合结束效果: 每有2银行轨，获得1矿'''
            self.round_end_effect_args = ('ore', 1, 'bank', 2)
            yield from super().round_end()

    class RoundScoring8(RoundScoring):
        
        id = 8
        
        def round_end(self):
            '''回合结束效果: 每有1工程轨，获得1块'''
            self.round_end_effect_args = ('money', 1, 'engineering', 1)
            yield from super().round_end()

    class RoundScoring9(RoundScoring):
        
        id = 9
        
        def round_end(self):
            '''回合结束效果: 每有3医疗轨，获得1书'''
            self.round_end_effect_args = ('book', 1, 'medical', 3)
            yield from super().round_end()

    class RoundScoring10(RoundScoring):
        
        id = 10
        
        def round_end(self):
            '''回合结束效果: 每有4工程轨，获得1铲'''
            self.round_end_effect_args = ('spade', 1, 'engineering', 4)
            yield from super().round_end()

    class RoundScoring11(RoundScoring):
        
        id = 11
        
        def round_end(self):
            '''回合结束效果: 每有3工程轨，获得1米宝'''
            self.round_end_effect_args = ('meeple', 1, 'engineering', 3)
            yield from super().round_end()

    class RoundScoring12(RoundScoring):
        
        id = 12
        
        def round_end(self):
            '''回合结束效果: 每有2法律轨，获得3转魔'''
            self.round_end_effect_args = ('magics', 3, 'law', 2)
            yield from super().round_end()

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
            yield from super().execute_immediate_effect(executed_player_id)

    class BookAction2(BookAction):

        id = 2
        
        def cost(self, player_id):
            return [('book', 'self', 'any', 1)], [('book', 'use', 'any', 1)]
        
        def execute_immediate_effect(self, executed_player_id):
            self.immediate_effect.extend([
                ('tracks', 'any', 2, False),
            ])
            yield from super().execute_immediate_effect(executed_player_id)

    class BookAction3(BookAction):

        id = 3
        
        def cost(self, player_id):
            return [('book', 'self', 'any', 2)], [('book', 'use', 'any', 2)]
        
        def execute_immediate_effect(self, executed_player_id):
            self.immediate_effect.extend([
                ('money', 'get', 6),
            ])
            yield from super().execute_immediate_effect(executed_player_id)

    class BookAction4(BookAction):

        id = 4
        
        def cost(self, player_id):
            return [('book', 'self', 'any', 2)], [('book', 'use', 'any', 2)]
        
        def execute_immediate_effect(self, executed_player_id):
            yield from super().execute_immediate_effect(executed_player_id)
            if self.game_state.players[executed_player_id].buildings[1] < 9:
                yield from self.game_state.invoke_immediate_action(executed_player_id, ('select_position', 'controlled', (1, 'alone_or_neighbor'))) 
                yield from self.game_state.adjust(executed_player_id,[('building', 'upgrade_special', 2, False)])
            
    class BookAction5(BookAction):

        id = 5
        
        def cost(self, player_id):
            return [('book', 'self', 'any', 2)], [('book', 'use', 'any', 2)]
        
        def execute_immediate_effect(self, executed_player_id):
            self.immediate_effect.extend([
                ('score', 'get', 'board', 2 * (4 - self.game_state.players[executed_player_id].buildings[2] + self.game_state.players[executed_player_id].buildings[10])),
            ])
            yield from super().execute_immediate_effect(executed_player_id)

    class BookAction6(BookAction):

        id = 6
        
        def cost(self, player_id):
            return [('book', 'self', 'any', 3)], [('book', 'use', 'any', 3)]
        
        def execute_immediate_effect(self, executed_player_id):
            self.immediate_effect.extend([
                ('spade',3),
            ])
            yield from super().execute_immediate_effect(executed_player_id)
    
    class CityTileBook(CityTile):

        id = 1

        def execute_immediate_effect(self, executed_player_id):
            self.immediate_effect.extend([
                ('book', 'get', 'any', 2),
                ('score', 'get', 'board', 5),
            ])
            yield from super().execute_immediate_effect(executed_player_id)

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
            yield from super().execute_immediate_effect(executed_player_id)
    
    class CityTileShovel(CityTile):

        id = 3

        def execute_immediate_effect(self, executed_player_id):
            self.immediate_effect.extend([
                ('spade', 2),
                ('score', 'get', 'board', 5),
            ])
            yield from super().execute_immediate_effect(executed_player_id)
    
    class CityTileMagics(CityTile):

        id = 4

        def execute_immediate_effect(self, executed_player_id):
            self.immediate_effect.extend([
                ('magics', 'get', 8),
                ('score', 'get', 'board', 8),
            ])
            yield from super().execute_immediate_effect(executed_player_id)
    
    class CityTileOre(CityTile):

        id = 5

        def execute_immediate_effect(self, executed_player_id):
            self.immediate_effect.extend([
                ('ore', 'get', 3),
                ('score', 'get', 'board', 4),
            ])
            yield from super().execute_immediate_effect(executed_player_id)
    
    class CityTileMeeple(CityTile):

        id = 6

        def execute_immediate_effect(self, executed_player_id):
            self.immediate_effect.extend([
                ('meeple', 'get', 1),
                ('score', 'get', 'board', 8),
            ])
            yield from super().execute_immediate_effect(executed_player_id)
    
    class CityTileMoney(CityTile):

        id = 7
        
        def execute_immediate_effect(self, executed_player_id):
            self.immediate_effect.extend([
                ('money', 'get', 6),
                ('score', 'get', 'board', 6),
            ])
            yield from super().execute_immediate_effect(executed_player_id)

    class MagicsActionBridge(MagicsAction):

        id = 1

        def cost(self, player_id):
            # 幻术师行动效果特判
            if self.game_state.players[player_id].faction_id == 4:
                return [('magics',3,2)], [('magics', 'use', 2)]
            return [('magics',3,3)], [('magics', 'use', 3)]
        
        def execute_immediate_effect(self, executed_player_id):
            self.immediate_effect.extend([
                ('bridge',)
            ])
            yield from super().execute_immediate_effect(executed_player_id)

    class MagicsActionMeeple(MagicsAction):

        id = 2
        
        def cost(self, player_id):
            # 幻术师行动效果特判
            if self.game_state.players[player_id].faction_id == 4:
                return [('magics',3,2)], [('magics', 'use', 2)]
            return [('magics',3,3)], [('magics', 'use', 3)]
        
        def execute_immediate_effect(self, executed_player_id):
            self.immediate_effect.extend([
                ('meeple','get',1)
            ])
            yield from super().execute_immediate_effect(executed_player_id)
        
    class MagicsActionOre(MagicsAction):

        id = 3
        
        def cost(self, player_id):
            # 幻术师行动效果特判
            if self.game_state.players[player_id].faction_id == 4:
                return [('magics',3,3)], [('magics', 'use', 3)]
            return [('magics',3,4)], [('magics', 'use', 4)]
        
        def execute_immediate_effect(self, executed_player_id):
            self.immediate_effect.extend([
                ('ore','get', 2)
            ])
            yield from super().execute_immediate_effect(executed_player_id)

    class MagicsActionMoney(MagicsAction):

        id = 4
        
        def cost(self, player_id):
            # 幻术师行动效果特判
            if self.game_state.players[player_id].faction_id == 4:
                return [('magics',3,3)], [('magics', 'use', 3)]
            return [('magics',3,4)], [('magics', 'use', 4)]
        
        def execute_immediate_effect(self, executed_player_id):
            self.immediate_effect.extend([
                ('money','get',7)
            ])
            yield from super().execute_immediate_effect(executed_player_id)

    class MagicsActionShovel1(MagicsAction):

        id = 5
        
        def cost(self, player_id):
            # 幻术师行动效果特判
            if self.game_state.players[player_id].faction_id == 4:
                return [('magics',3,3)], [('magics', 'use', 3)]
            return [('magics',3,4)], [('magics', 'use', 4)]
        
        def execute_immediate_effect(self, executed_player_id):
            self.immediate_effect.extend([
                ('spade',1)
            ])
            yield from super().execute_immediate_effect(executed_player_id)

    class MagicsActionShovel2(MagicsAction):

        id = 6
        
        def cost(self, player_id):
            # 幻术师行动效果特判
            if self.game_state.players[player_id].faction_id == 4:
                return [('magics',3,5)], [('magics', 'use', 5)]
            return [('magics',3,6)], [('magics', 'use', 6)]

        def execute_immediate_effect(self, executed_player_id):
            self.immediate_effect.extend([
                ('spade',2)
            ])
            yield from super().execute_immediate_effect(executed_player_id)

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