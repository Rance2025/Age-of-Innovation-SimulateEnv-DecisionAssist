from ActionSystem import ActionSystem
from DetailedAction import DetailedAction

class Agent:
    def __init__(self, game_state, player_id):
        self.player_id = player_id
        self.action_system = ActionSystem(game_state, player_id)
        self.detailed_action = DetailedAction().all_detailed_actions

    def execute_action(self):

        print(f'玩家{self.player_id + 1}的可选行动： ',end = '')
        self.available_action_ids = self.action_system.get_available_actions()
        print(self.available_action_ids)

        action_id = int(input('请输入要执行的行动编号：'))

        '''
        action_id = random.choice(self.available_actions))
        '''

        immediate_action_to_be_executed_list = self.action_system.execute_action(action_id)

        if immediate_action_to_be_executed_list:
            return immediate_action_to_be_executed_list
    
    def execute_immediate_action(self):
        pass