from GameState import GameStateBase

class AllEffectObject:

    class EffectObject:
        """效果对象抽象基类"""

        def __init__(self, game_state: GameStateBase) -> None:
            self.max_owner = 1
            self.game_state = game_state
            self.owner_list = []
            self.immediate_effect = []
            self.income_effect = []
            self.round_end_effect = []
            self.pass_effect = []
            self.setup_effect = []
        
        # 检查是否可获取
        def check_get(self, player_id: int) -> bool:
            if player_id in self.owner_list or len(self.owner_list) >= self.max_owner:
                return False
            if not self.game_state.check(player_id, self.cost_check()):
                return False
            return True
        # 获取代价检查
        def cost_check(self) -> list:
            return [] 
        
        # 立即执行方法
        def execute_immediate_effect(self, executed_player_id):
            self.game_state.adjust(executed_player_id, self.immediate_effect)
        # 回合收入方法
        def execute_income_effect(self, executed_player_id):
            self.game_state.adjust(executed_player_id, self.income_effect)
        # 回合结束方法
        def execute_round_end_effect(self, executed_player_id):
            self.game_state.adjust(executed_player_id, self.round_end_effect)
        # 略过回合方法
        def execute_pass_effect(self, executed_player_id):
            self.game_state.adjust(executed_player_id, self.pass_effect)
        # 初始设置方法
        def execute_setup_effect(self, executed_player_id):
            self.game_state.adjust(executed_player_id, self.setup_effect)
        
        # 当获取时
        def get(self, got_player_id):
            self.owner_list.append(got_player_id)
            self.execute_immediate_effect(got_player_id)
            self.game_state.players[got_player_id].income_effect_list.append(self.execute_income_effect)
            self.game_state.players[got_player_id].pass_effect_list.append(self.execute_pass_effect)
            self.game_state.players[got_player_id].round_end_effect_list.append(self.execute_round_end_effect)
            self.game_state.players[got_player_id].setup_effect_list.append(self.execute_setup_effect)      
                
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
        pass
        
    class FinalScoring(EffectObject):
        pass
            
    class BookAction(EffectObject):
        pass

    class PlainPlanningCard(PlanningCard):
        
        # 行动效果：减少升级铲子花费
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
            self.setup_effect.extend([
                ('land', 1, False)
            ])
            super().execute_setup_effect(executed_player_id)

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
    
    def __init__(self, game_state: GameStateBase) -> None:
        self.game_state = game_state
        self.EffectObject(game_state)

    def create_actual_object(self,typ: str, object_id: int):
        all_object_dict = {
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
            }
        }

        return all_object_dict[typ][object_id](self.game_state)