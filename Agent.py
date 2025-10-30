from ActionSystem import ActionSystem
from DetailedAction import DetailedAction

class Agent:

    def __init__(self, game_state, player_id: int):
        self.player_id = player_id
        self.game_state = game_state
        self.player = self.game_state.players[player_id]
        self.action_system = ActionSystem(game_state, player_id)

    def action(self, mode, args) -> int:

        print(f'玩家{self.player_id + 1}的可选{mode}行动： ',end = '')
        available_action_ids = self.action_system.get_available_actions(mode, args)
        readable_action_ids = {id: DetailedAction().all_detailed_actions[id]['description'] for id in available_action_ids}
        print(readable_action_ids)

        action_id = int(input('请输入要执行的行动编号：'))
        self.action_system.execute_action(action_id)

        return action_id
