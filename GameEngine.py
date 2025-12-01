from GameState import GameStateBase
from Agent import AgentBase
from web_io import Silence_IO

class GameEngine:
    """游戏引擎"""
    def __init__(self, game_args: dict):
        self.game_args = game_args                                     # 游戏参数
        self.num_players = game_args['num_players']                    # 玩家数量
        self.action_history = game_args['action_history']              # 行动记录
        self.web_io = game_args['web_io']                              # 网页IO
        self.game_state = self.create_game_state()                     # 游戏状态
        self.game_state.effect_object()                                # 效果板块
        self.agents = self.create_agents()                             # 代理系统
        self.next_immediate_action = []
    
    def create_game_state(self):
        """创建游戏状态"""
        out_ref = self

        class GameState(GameStateBase):
            """游戏状态类"""
            def __init__(self, num_players, game_args) -> None:
                super().__init__(num_players=num_players,game_args=game_args)
                return
            
            def invoke_immediate_aciton(self, player_id: int, args: tuple):
                flag, *data = out_ref.action(player_id, 'immediate', args)
                if flag:
                    out_ref.next_immediate_action = data
                    return True
                else:
                    out_ref.next_immediate_action = []
                return False
            
        return GameState(self.num_players, self.game_args)
    
    def create_agents(self):
        """创建代理系统"""
        out_ref = self

        class Agent(AgentBase):
            """代理类"""
            def __init__(self, game_state, player_id: int, game_args):
                super().__init__(game_state, player_id, game_args)
                return
            
            def reproduce(self, action_history_appendix: list = []):
                return out_ref.reproduce(action_history_appendix)
            
            def simulate(self, action_history_appendix: list = []):
                return out_ref.simulate(action_history_appendix)

        return [Agent(self.game_state,i,self.game_args) for i in range(self.num_players)]
    
    def action(self, player_id, typ= 'normal', args = tuple()):
        match self.game_args['action_mode']:
            case 'input':
                self.agents[player_id].need_estimate = True
                self.agents[player_id].action_turn(typ, args)
            case 'simulate':
                if self.action_history:
                    action_player_id, action_typ, action_id = self.action_history.pop(0)
                    assert action_player_id == player_id
                    assert action_typ == typ
                    self.agents[player_id].action_step('target', typ, action_id)
                else:
                    self.agents[player_id].action_step('random', typ, args)
                    
                if typ == 'normal':
                    if self.agents[player_id].action_system.is_next_action_exist():
                        self.action(player_id, 'normal')
                    else:
                        self.agents[player_id].action_system.reset_action_state()
            case 'reproduce':
                if self.next_immediate_action:
                    return (True, *self.next_immediate_action)
                
                if self.action_history:
                    action_player_id, action_typ, action_id = self.action_history.pop(0)
                    assert action_player_id == player_id
                    assert action_typ == typ
                    self.agents[player_id].action_step('target', typ, action_id)
                    if typ == 'normal':
                        if self.agents[player_id].action_system.is_next_action_exist():
                            self.action(player_id, 'normal')
                        else:
                            self.agents[player_id].action_system.reset_action_state()
                else:
                    return (True, player_id, typ, args)
        return (False,)

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
                    flag, *data = self.action(player_idx)
                    if flag:
                        return (True, *data)
                    
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
                flag, *data = self.action(player_idx)
                if flag:
                    return (True, *data)

            self.web_io.update_global_status("初始阶段效果结算")
            for player_idx in self.game_state.pass_order:
                cur_player_setup_list = self.game_state.players[player_idx].setup_effect_list
                if cur_player_setup_list:
                    cur_player_setup_list.pop(0)(player_idx)
                    if self.next_immediate_action:
                        return (True, *self.next_immediate_action)

            # 将初始未选的回合助推板的获取立即效果加一块钱
            for effect_object in self.game_state.all_available_object_dict['round_booster'].values():
                effect_object.round_end()
            
            self.game_state.current_player_order = self.game_state.pass_order.copy()

            self.web_io.round_update(self.game_state.round)
            return (False,)

        def execute_formal_round():
            # 备份本回合初始时的玩家行动顺序
            self.current_round_init_player_order = self.game_state.current_player_order.copy()

            self.game_state.pass_order.clear()
            current_player_order = self.game_state.current_player_order.copy()      

            self.web_io.update_global_status(f'第{self.game_state.round}轮收入阶段\n玩家行动顺序：{','.join(map(lambda x:str(x+1),current_player_order))}')

            for player_idx in self.current_round_init_player_order:
                # print(self.game_state.players[player_idx].income_effect_list)
                for income_effect in self.game_state.players[player_idx].income_effect_list:
                    income_effect(player_idx)
                    if self.next_immediate_action:
                        return (True, *self.next_immediate_action)
            
            self.web_io.update_global_status(f'第{self.game_state.round}轮行动阶段\n玩家行动顺序：{','.join(map(lambda x:str(x+1),current_player_order))}')
            while current_player_order:
                for player_idx in current_player_order:
                    flag, *data = self.action(player_idx)
                    if flag:
                        return (True, *data)
                current_player_order = self.game_state.current_player_order.copy()

            self.web_io.update_global_status(f'第{self.game_state.round}轮回合结束结算阶段\n玩家行动顺序：{','.join(map(lambda x:str(x+1),self.game_state.pass_order))}')

            for effect_object_typ in [
                # 回合结束奖励，并添加下一回合的回合计分
                'round_scoring', 'final_scoring',
                # 清空以下板块的每回合一次行动标记
                'book_action', 'magics_action', 'faction', 'palace_tile', 'ability_tile', 'science_tile', 
                # 并将未选的回合助推板的获取立即效果加一块钱
                'round_booster'
            ]:
                for effect_object in self.game_state.all_available_object_dict[effect_object_typ].values():
                    effect_object.round_end()
                    if self.next_immediate_action:
                        return (True, *self.next_immediate_action)
                
            self.game_state.current_player_order = self.game_state.pass_order.copy()

            self.web_io.round_update(self.game_state.round)
            return (False,)
        
        self.current_round_init_player_order = []  # 当前轮初始玩家行动顺序

        # 初始设置阶段
        flag, *data = initial_setup_phase()
        if flag:
            return data

        # print(f"\n=== 正式轮次阶段 ===")
        for round_idx in range(1, 7):
            # 设置游戏当前轮次
            self.game_state.round = round_idx  
            # print(f"\n--- 第{round_idx}轮 ---")
            
            flag, *data = execute_formal_round()
            if flag:
                return data

        # print("\n=== 终局结算阶段 ===\n")
        rank = sorted(self.game_state.calculate_players_total_score().items(),key=lambda x:x[1],reverse=True)
        
        return tuple(map(lambda x:x[1],rank))
        return (None,None)

    def reproduce(self, action_history_appendix: list):
        reproduce_args = {
            'num_players': self.game_args['num_players'],
            'setup_mode': 'target',
            'setup_tile_args' : self.game_args['setup_tile_args'],
            'setup_player_order_args': self.game_args['setup_player_order_args'].copy(),
            'action_history': self.game_args['action_history'].copy() + action_history_appendix.copy(),
            'action_mode': 'reproduce',
            'web_io': Silence_IO(),
        }
        reproduce_game = GameEngine(reproduce_args)
        next_action_data = reproduce_game.run_game()
        return {
            'next_action': next_action_data,
            'reproduce_game': reproduce_game,
        }
    
    def simulate(self, action_history_appendix: list):
        simulate_args = {
            'num_players': self.game_args['num_players'],
            'setup_mode': 'target',
            'setup_tile_args' : self.game_args['setup_tile_args'],
            'setup_player_order_args': self.game_args['setup_player_order_args'].copy(),
            'action_history': self.game_args['action_history'].copy() + action_history_appendix.copy(),
            'action_mode': 'simulate',
            'web_io': Silence_IO(),
        }
        simulate_game = GameEngine(simulate_args)
        simulate_game.run_game()
        return {}