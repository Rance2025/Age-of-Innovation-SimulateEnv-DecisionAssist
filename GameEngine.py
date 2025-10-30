from GameState import GameStateBase
from Agent import Agent


class GameEngine:
    """游戏引擎"""
    def __init__(self, num_players: int):
        self.num_players = num_players                                                              # 玩家数量
        self.game_state = self.create_game_state()                                                  # 游戏状态
        self.game_state.effect_object()                                                             # 效果板块
        self.agents = [Agent(self.game_state,i) for i in range(num_players)]                        # 行动系统
        self.action_history = []                                                                    # 行动记录
    
    def create_game_state(self):
        """创建游戏状态"""
        out_ref = self

        class GameState(GameStateBase):
            def __init__(self) -> None:
                super().__init__(out_ref.num_players)
                return
            def invoke_immediate_aciton(self, player_id: int, args: tuple):
                out_ref.action(player_id, 'immediate', args)

        return GameState()
        
    
    def action(self, player_id: int = -1, mode: str = '', args: tuple = tuple()):
        match mode:
            case 'normal' | 'immediate':
                # 当前玩家执行一个行动
                id = self.agents[player_id].action(mode, args)
                # 记录该行动
                self.action_history.append((player_id, mode, id))

                if mode == 'normal':
                    # 如果当前玩家当前轮中仍可继续行动
                    if self.agents[player_id].action_system.is_next_action_exist():
                        # 则递归让该玩家继续行动
                        return self.action(player_id, 'normal')
                    else:
                        # 否则重置当前行动状态为每轮初始状态
                        self.agents[player_id].action_system.reset_action_state()
            case _ :
                raise ValueError(f"非法动作模式: {mode}")

    def show_players_state(self):
        for player in self.game_state.players:
            print(player)

    def run_game(self):
        """运行整个游戏"""
        
        def initial_setup_phase(self: GameEngine):
            """初始设置阶段"""
            print("\n=== 初始设置阶段 ===")
            
            # 4轮选择（逆蛇轮抽）
            for round_idx in range(1,5):
                print(f"\n--- 第{round_idx }轮初始设置行动 ---")

                # 确定本轮玩家顺序
                if round_idx % 2 == 1:
                    current_turn_order = self.game_state.current_player_order
                else:
                    current_turn_order = self.game_state.pass_order

                for player_idx in current_turn_order:
                    print()
                    self.action(player_idx, 'normal')
                    
            self.game_state.setup_choice_is_completed = True
            print("\n初始设置及轮抽完成!")

            print("\n=== 初始建筑摆放阶段 ===")
            build_order = []
            faction_8_owner_id = -1
            faction_10_owner_id = -1

            for idx in range(self.num_players):
                if self.game_state.players[idx].faction_id == 8:
                    faction_8_owner_id = idx
                if self.game_state.players[idx].faction_id == 10:
                    faction_10_owner_id = idx
            match faction_8_owner_id, faction_10_owner_id:
                case -1, -1:
                    build_order = self.game_state.pass_order + self.game_state.current_player_order
                case _, -1:
                    build_order = [idx for idx in self.game_state.pass_order + self.game_state.current_player_order if idx != faction_8_owner_id] + [faction_8_owner_id]
                case -1, _:
                    build_order = self.game_state.pass_order + self.game_state.current_player_order + [faction_10_owner_id]
                case _, _:
                    build_order = [idx for idx in self.game_state.pass_order + self.game_state.current_player_order if idx != faction_8_owner_id] + [faction_10_owner_id, faction_8_owner_id]

            for player_idx in build_order:
                print()
                self.action(player_idx, 'normal')
            
            self.game_state.current_player_order = self.game_state.pass_order.copy()

        def execute_formal_round(self: GameEngine):
            # 备份本回合初始时的玩家行动顺序
            self.current_round_init_player_order = self.game_state.current_player_order.copy()

            self.game_state.pass_order.clear()
            current_player_order = self.game_state.current_player_order.copy()
            print(f"当前轮玩家行动顺序：{','.join(map(lambda x:str(x+1),current_player_order))}")       

            print(f'\n--- 第{self.game_state.round}轮收入阶段 ---')
            for player_idx in self.current_round_init_player_order:
                for income_effect in self.game_state.players[player_idx].income_effect_list:
                    income_effect(player_idx)
            
            print(f'\n--- 第{self.game_state.round}轮行动阶段 ---')
            while current_player_order:
                for player_idx in current_player_order:
                    print()
                    self.action(player_idx, 'normal')
                current_player_order = self.game_state.current_player_order.copy()

            print(f'\n--- 第{self.game_state.round}轮回合结束结算阶段 ---')
            for player_idx in self.current_round_init_player_order:
                for round_end_effect in self.game_state.players[player_idx].round_end_effect_list:
                    round_end_effect(player_idx)
            
            self.game_state.current_player_order = self.game_state.pass_order.copy()
        
        self.current_round_init_player_order = []  # 当前轮初始玩家行动顺序

        # 初始设置阶段
        initial_setup_phase(self)
        
        # TODO 正式轮次阶段
        print(f"\n=== 正式轮次阶段 ===")
        for round_idx in range(1,7): # TODO 调试
            
            # 设置游戏当前轮次
            self.game_state.round = round_idx  

            print(f"\n--- 第{round_idx}轮 ---")
            execute_formal_round(self)

            
        # TODO 终局结算阶段
        print("\n=== 终局结算阶段 ===\n")
     