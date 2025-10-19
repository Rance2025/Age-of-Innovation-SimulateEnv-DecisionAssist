from GameState import GameState
from Agent import Agent


class GameEngine:
    """游戏引擎"""
    def __init__(self, num_players: int):
        self.num_players = num_players                                                              # 玩家数量
        self.game_state = GameState(num_players)                                                    # 游戏状态
        self.agents = [Agent(self.game_state,i) for i in range(num_players)]                        # 行动系统
        self.action_history = []                                                                    # 行动记录
    
    def action(self, player_id: int):

        # 当前玩家执行一个主要行动（含快速行动）
        immediate_action_list = self.agents[player_id].execute_action()

        # 如有立即行动，则根据主要行动返回值，遍历执行立即行动（可能涉及多个玩家）
        if immediate_action_list:
            for temp_player_id, immediate_action_data in immediate_action_list:
                self.agents[temp_player_id].execute_immediate_action(*immediate_action_data)

        # 执行完毕后，重置该主要行动所致的待执行立即行动列表
        self.agents[player_id].action_system.immediate_action_need_to_be_executed_list.clear()

        # 如果当前玩家当前轮中仍可继续行动
        if self.agents[player_id].action_system.is_next_action_exist():
            # 则递归让该玩家继续行动
            return self.action(player_id)
        else:
            # 否则重置当前行动状态为每轮初始状态
            self.agents[player_id].action_system.reset_action_state()
        
        return True
    
    def show_players_state(self):
        for player in self.game_state.players:
            print(player)

    def run_game(self):
        """运行整个游戏"""

        # 初始设置阶段
        self.setup_completed = self.initial_setup_phase()

        if not self.setup_completed:
            print(f"游戏异常结束：初始设置未完成")
            return False
        
        # TODO 正式轮次阶段
        print(f"\n=== 正式轮次阶段 ===")
        for round_idx in range(1,3): # TODO 调试
            
            # 设置游戏当前轮次
            self.game_state.round = round_idx
            # 设置第一回合回合玩家行动顺序为初始设置阶段跳过顺序
            self.game_state.current_player_order = self.game_state.pass_order.copy()

            print(f"\n--- 第{round_idx}轮 ---")
            res = self.execute_formal_round()

            if not res:
                print(f"游戏异常结束: 第{round_idx}轮未完成")
                return False
            
        # TODO 终局结算阶段
        print("\n=== 终局结算阶段 ===\n")
 
    def initial_setup_phase(self) -> bool:
        """初始设置阶段"""
        print("\n=== 初始设置阶段 ===")
        
        # 4轮选择（前3轮顺序，第4轮倒序）
        for round_idx in range(4):
            print(f"\n--- 第{round_idx + 1}轮选择 ---")

            # 确定本轮玩家顺序
            if round_idx % 2 == 0:
                current_turn_order = self.game_state.current_player_order
            else:
                current_turn_order = self.game_state.pass_order

            for player_idx in current_turn_order:
                res = self.action(player_idx)
                if not res:
                    return False
        
        # 设置完成
        print("\n初始设置及轮抽完成!")
        return True
        
    def execute_formal_round(self) -> bool:

        self.game_state.pass_order.clear()
        
        current_player_order = self.game_state.current_player_order.copy()
        print(f"当前轮玩家行动顺序：{','.join(map(lambda x:str(x+1),current_player_order))}")

        while current_player_order:
            for player_idx in current_player_order:
                res = self.action(player_idx)
                if not res:
                    return False
            current_player_order = self.game_state.current_player_order.copy()
        
        self.game_state.current_player_order = self.game_state.pass_order.copy()
        
        return True
    