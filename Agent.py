from ActionSystem import ActionSystem
from DetailedAction import DetailedAction
from GameState import GameState

class Agent:
    def __init__(self, game_state: GameState, player_id: int):
        self.player_id = player_id
        self.game_state = game_state
        self.player = self.game_state.players[player_id]
        self.action_system = ActionSystem(game_state, player_id)
        self.detailed_action = DetailedAction().all_detailed_actions

    def execute_primary_action(self):

        print(f'玩家{self.player_id + 1}的可选行动： ',end = '')
        self.available_action_ids = self.action_system.get_available_actions()
        print(self.available_action_ids)

        action_id = int(input('请输入要执行的行动编号：'))
        # action_id = random.choice(self.available_actions))
        self.action_system.execute_action(action_id)
    
    def execute_non_primary_action_and_effect(self, mode: str):
        match mode:
            case 'setup':
                # 获取该玩家初始设置行动中的第一个
                setup_action_function = self.game_state.all_players_setup_action_list[0][1]
                # 执行该初始设置行动
                setup_action_function(self.player_id)
            case 'income':
                # 获取该玩家回合收入效果中的第一个
                income_effect_function = self.player.income_effect_list[0]
                # 执行该回合收入效果
                income_effect_function(self.player_id)
            case 'round_end':
                # 获取该玩家轮次结束效果中的第一个
                round_end_effect_function = self.player.round_end_effect_list[0]
                # 执行该轮次结束效果
                round_end_effect_function(self.player_id)
            case 'immediate':
                action_data = self.game_state.all_players_immediate_action_list[0][1]
                print(f'玩家{self.player_id + 1}的可选立即行动： ',end = '')
                available_immediate_action_ids = self.action_system.get_available_immediate_actions(action_data)
                print(available_immediate_action_ids)
                action_id = int(input('请输入要执行的行动编号：'))
                # action_id = random.choice(self.available_immediate_action_ids))
                self.action_system.execute_immediate_actions(action_id)  
                pass
        pass
