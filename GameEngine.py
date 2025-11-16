from GameState import GameStateBase
from Agent import Agent
import copy


class GameEngine:
    """游戏引擎"""
    def __init__(self, game_args: dict):
        self.game_args = game_args                                                                          # 游戏参数
        self.num_players = game_args['num_players']                                                         # 玩家数量
        self.web_io = game_args['web_io']                                                                   # 网页IO
        self.game_state = self.create_game_state()                                                          # 游戏状态
        self.game_state.effect_object()                                                                     # 效果板块
        self.action_history = game_args['action_history']                                                   # 行动记录
        self.agents = [Agent(self.game_state,i,game_args) for i in range(self.num_players)]                 # 行动系统
    
    def create_game_state(self):
        """创建游戏状态"""
        out_ref = self

        class GameState(GameStateBase):
            def __init__(self, web_io, num_players, game_args) -> None:
                super().__init__(web_io=web_io, num_players=num_players,game_args=game_args)
                return
            def invoke_immediate_aciton(self, player_id: int, args: tuple):
                match out_ref.game_args['invoke_immediate_action_mode']:
                    case'normal':
                        out_ref.agents[player_id].need_estimate = True
                        out_ref.agents[player_id].action_turn('immediate', args)
                    case 'step':
                        yield from self.invoke_immediate_action_step(player_id, args)
            def invoke_immediate_action_step(self, player_id:int, args: tuple):
                yield out_ref
                out_ref.agents[player_id].action_turn('immediate', args)
                

        return GameState(self.web_io, self.num_players, self.game_args)

    def run_game(self):
        """运行整个游戏"""
        
        def initial_setup_phase():
            """初始设置阶段"""
            self.web_io.update_global_status("初始设置阶段")
            
            # 4轮选择（逆蛇轮抽）
            for round_idx in range(1,5):
                self.web_io.update_global_status(f"第{round_idx }轮初始设置行动")

                # 确定本轮玩家顺序
                if round_idx % 2 == 1:
                    current_turn_order = self.game_state.current_player_order
                else:
                    current_turn_order = self.game_state.pass_order

                for player_idx in current_turn_order:
                    self.agents[player_idx].need_estimate = True
                    self.agents[player_idx].action_turn('normal')
                    

            self.game_state.setup_choice_is_completed = True    

            self.web_io.update_global_status("初始建筑摆放阶段")
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
                self.agents[player_idx].need_estimate = True
                self.agents[player_idx].action_turn('normal')

            self.web_io.update_global_status("初始阶段效果结算")
            for player_idx in self.game_state.pass_order:
                cur_player_setup_list = self.game_state.players[player_idx].setup_effect_list
                if cur_player_setup_list:
                    cur_player_setup_list.pop(0)(player_idx)

            # 初始未选各回合助推板的获取立即效果加一块钱
            for round_booster in self.game_state.all_available_object_dict['round_booster'].values():
                round_booster.round_end()

            self.game_state.current_player_order = self.game_state.pass_order.copy()

        def execute_formal_round():
            # 备份本回合初始时的玩家行动顺序
            self.current_round_init_player_order = self.game_state.current_player_order.copy()

            self.game_state.pass_order.clear()
            current_player_order = self.game_state.current_player_order.copy()      

            self.web_io.update_global_status(f'第{self.game_state.round}轮收入阶段\n玩家行动顺序：{','.join(map(lambda x:str(x+1),current_player_order))}')
            # TODO 打印可视化收入阶段
            for player_idx in self.current_round_init_player_order:
                print(self.game_state.players[player_idx].income_effect_list)
                for income_effect in self.game_state.players[player_idx].income_effect_list:
                    income_effect(player_idx)
            
            self.web_io.update_global_status(f'第{self.game_state.round}轮行动阶段\n玩家行动顺序：{','.join(map(lambda x:str(x+1),current_player_order))}')
            while current_player_order:
                for player_idx in current_player_order:
                    self.agents[player_idx].need_estimate = True
                    self.agents[player_idx].action_turn('normal')
                current_player_order = self.game_state.current_player_order.copy()

            self.web_io.update_global_status(f'第{self.game_state.round}轮回合结束结算阶段\n玩家行动顺序：{','.join(map(lambda x:str(x+1),current_player_order))}')
            # TODO 打印可视化结算阶段
            for player_idx in self.current_round_init_player_order:
                for round_end_effect in self.game_state.players[player_idx].round_end_effect_list:
                    round_end_effect(player_idx)

            # 初始未选各回合助推板的获取立即效果加一块钱
            for round_booster in self.game_state.all_available_object_dict['round_booster'].values():
                round_booster.round_end()
            
            self.game_state.current_player_order = self.game_state.pass_order.copy()
        
        self.current_round_init_player_order = []  # 当前轮初始玩家行动顺序

        # 初始设置阶段
        initial_setup_phase()

        print(f"\n=== 正式轮次阶段 ===")
        for round_idx in range(1, 7):
            # 设置游戏当前轮次
            self.game_state.round = round_idx  
            print(f"\n--- 第{round_idx}轮 ---")
            
            execute_formal_round()

        print("\n=== 终局结算阶段 ===\n")
        # TODO 终局结算
        "游戏结束，进入终局结算"

    def step(self):
        """逐步运行游戏"""
        
        def initial_setup_phase():
            """初始设置阶段"""
            self.web_io.update_global_status("初始设置阶段")
            
            # 4轮选择（逆蛇轮抽）
            for round_idx in range(1,5):
                self.web_io.update_global_status(f"第{round_idx }轮初始设置行动")

                # 确定本轮玩家顺序
                if round_idx % 2 == 1:
                    current_turn_order = self.game_state.current_player_order
                else:
                    current_turn_order = self.game_state.pass_order

                for player_idx in current_turn_order:
                    yield self
                    self.agents[player_idx].need_estimate = True
                    self.agents[player_idx].action_turn('normal')
                    

            self.game_state.setup_choice_is_completed = True    

            self.web_io.update_global_status("初始建筑摆放阶段")
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
                yield self
                self.agents[player_idx].need_estimate = True
                self.agents[player_idx].action_turn('normal')

            self.web_io.update_global_status("初始阶段效果结算")
            for player_idx in self.game_state.pass_order:
                cur_player_setup_list = self.game_state.players[player_idx].setup_effect_list
                if cur_player_setup_list:
                    cur_player_setup_list.pop(0)(player_idx)

            # 初始未选各回合助推板的获取立即效果加一块钱
            for round_booster in self.game_state.all_available_object_dict['round_booster'].values():
                round_booster.round_end()

            self.game_state.current_player_order = self.game_state.pass_order.copy()

        def execute_formal_round():
            # 备份本回合初始时的玩家行动顺序
            self.current_round_init_player_order = self.game_state.current_player_order.copy()

            self.game_state.pass_order.clear()
            current_player_order = self.game_state.current_player_order.copy()      

            self.web_io.update_global_status(f'第{self.game_state.round}轮收入阶段\n玩家行动顺序：{','.join(map(lambda x:str(x+1),current_player_order))}')
            # TODO 打印可视化收入阶段
            for player_idx in self.current_round_init_player_order:
                print(self.game_state.players[player_idx].income_effect_list)
                for income_effect in self.game_state.players[player_idx].income_effect_list:
                    income_effect(player_idx)
            
            self.web_io.update_global_status(f'第{self.game_state.round}轮行动阶段\n玩家行动顺序：{','.join(map(lambda x:str(x+1),current_player_order))}')
            while current_player_order:
                for player_idx in current_player_order:
                    yield self
                    self.agents[player_idx].need_estimate = True
                    self.agents[player_idx].action_turn('normal')
                current_player_order = self.game_state.current_player_order.copy()

            self.web_io.update_global_status(f'第{self.game_state.round}轮回合结束结算阶段\n玩家行动顺序：{','.join(map(lambda x:str(x+1),current_player_order))}')
            # TODO 打印可视化结算阶段
            for player_idx in self.current_round_init_player_order:
                for round_end_effect in self.game_state.players[player_idx].round_end_effect_list:
                    round_end_effect(player_idx)

            # 初始未选各回合助推板的获取立即效果加一块钱
            for round_booster in self.game_state.all_available_object_dict['round_booster'].values():
                round_booster.round_end()
            
            self.game_state.current_player_order = self.game_state.pass_order.copy()
        
        self.current_round_init_player_order = []  # 当前轮初始玩家行动顺序

        # 初始设置阶段
        yield from initial_setup_phase()
        
        print(f"\n=== 正式轮次阶段 ===")
        for round_idx in range(1, 7):
            # 设置游戏当前轮次
            self.game_state.round = round_idx  
            print(f"\n--- 第{round_idx}轮 ---")
            
            yield from execute_formal_round()

        print("\n=== 终局结算阶段 ===\n")
        # TODO 终局结算

