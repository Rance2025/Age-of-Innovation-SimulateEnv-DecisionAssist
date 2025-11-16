from ActionSystem import ActionSystem
from DetailedAction import DetailedAction
import random
import time
import copy

class Agent:

    def __init__(self, game_state, player_id: int, game_args):
        self.player_id = player_id
        self.game_state = game_state
        self.player = self.game_state.players[player_id]
        self.action_system = ActionSystem(game_state, player_id)
        self.web_io = game_args['web_io']
        self.all_detailed_actions = DetailedAction().all_detailed_actions
        self.game_args = game_args
        self.need_estimate = True
        self.need_estimate_id = -1

    def action_turn(self, typ: str, args: tuple = tuple()):
        match self.game_args['action_mode']:
            case 'input':
                match typ:
                    case 'normal':
                        if self.need_estimate:
                            self.need_estimate = False
                            # self.simulate(typ, args, mode = 'normal')
                            
                        # 当前玩家执行一个行动
                        self.action_step(mode='input',typ='normal', args=tuple())

                        # 如果当前玩家当前轮中仍可继续行动
                        if self.action_system.is_next_action_exist():
                            # 则递归让该玩家继续行动
                            self.action_turn('normal')
                        else:
                            # 否则重置当前行动状态为每轮初始状态
                            self.action_system.reset_action_state()

                    case 'immediate':
                        if self.need_estimate:
                            self.need_estimate = False
                            # self.simulate(typ, args, mode = 'immediate')
                            
                        self.action_step(mode='input',typ='immediate', args=args)
                    case _ :
                        raise ValueError(f"非法动作模式: {typ}")
                    
            case 'simulate':
                if self.game_args['action_history']:
                    action_player_id, action_typ, action_id = self.game_args['action_history'].pop(0)
                    assert action_player_id == self.player_id
                    assert action_typ == typ
                    self.action_step(mode='target',typ=action_typ, args=action_id)
                else:
                    self.action_step(mode='random',typ=typ, args=args)

                if typ == 'normal':
                    if self.action_system.is_next_action_exist():
                        return self.action_turn('normal')
                    else:
                        self.action_system.reset_action_state()

    def action_step(self, mode, typ, args):
        match mode:
            case 'input':
                available_action_ids = self.action_system.get_available_actions(typ, args)
                readable_action_ids = {id: self.all_detailed_actions[id]['description'] for id in available_action_ids}
                res_str = f'玩家{self.player_id + 1}的可选{typ}行动: \n'
                for key,value in readable_action_ids.items():
                    res_str += f'{key}: {value}\n'
                res_str = res_str[:-1]
                self.web_io.output(0,res_str)
                print(res_str)
                action_id = self.web_io.get_input()
                if action_id:
                    action_id = int(action_id)
                    self.web_io.output(self.player_id + 1, readable_action_ids[action_id])
                    print(f'玩家{self.player_id + 1}执行了{readable_action_ids[action_id]}')
                    self.action_system.execute_action(typ, action_id)
                else:
                    if 65 in available_action_ids:
                        action_id = 65
                    else:
                        action_id = random.choice(available_action_ids)
                    self.web_io.output(self.player_id + 1, readable_action_ids[action_id])
                    print(f'玩家{self.player_id + 1}执行了{readable_action_ids[action_id]}')
                    self.action_system.execute_action(typ, action_id)
                # 记录该行动
                self.game_args['action_history'].append((self.player_id, typ, action_id))

            case 'target':
                action_id = args
                self.action_system.execute_action(typ, action_id) 

            case 'random':
                self.seedid = int(time.strftime("%S%H%M", time.localtime()))
                random.seed(self.seedid)
                # print(f'seed:{self.seedid}')
                available_action_ids = self.action_system.get_available_actions(typ, args)
                if 65 in available_action_ids and random.random()<=0.9:
                    action_id = 65
                else:
                    action_id = random.choice(available_action_ids)
                self.action_system.execute_action(typ, action_id)

            case _:
                raise Exception('Invalid mode')
            
    def simulate(self):
        from GameEngine import GameEngine
        class silence_io:
            def get_input(self, prompt):
                pass
            def output(self, channel, message):
                pass
            def update_player_states(self, states):
                pass
            def update_global_status(self, message):
                pass

        game_args = {
            'num_players': self.game_args['num_players'],
            'setup_mode': 'target',
            'setup_tile_args' : self.game_args['setup_tile_args'],
            'setup_player_order_args': self.game_args['setup_player_order_args'],
            'action_mode': 'simulate',
            'action_history': self.game_args['action_history'].copy(),
            'web_io': silence_io,
            'invoke_immediate_action_mode': 'step'
        }
        simulate_game = GameEngine(game_args)
        for step in simulate_game.step():
            if self.game_args['action_history']:
                action_player_id, action_typ, action_id = self.game_args['action_history'].pop(0)
                step.agents[action_player_id
            
    # def simulate(self, typ, args, mode):
    #     from GameEngine import GameEngine
    #     
    #     def single_simulate(self, game_args):
    #         single_game_args = copy.deepcopy(game_args)
    #         simulate_game = GameEngine(single_game_args)
    #         res = simulate_game.run_game()
    #         return res
        
    #     simulate_game = GameEngine(game_args)
    #     simulate_action_system = simulate_game.agents[self.player_id].action_system
    #     match mode:
    #         case 'normal':    
    #             ans = []
    #             tmp = []

    #             def tracebacking():
    #                 if not simulate_action_system.is_next_action_exist():
    #                     ans.append(tmp.copy())
                    
    #                 for action_id in simulate_action_system.get_available_actions(typ, args):
    #                     self.action_system.reset_action_state()

    #         case 'immediate':
    #             for action_id in simulate_action_system.get_available_actions(typ, args):
    #                 action_res = []
    #                 for i in range(100):
    #                     simulate_game_args = {
    #                         'num_players': self.game_args['num_players'],
    #                         'setup_mode': 'target',
    #                         'setup_tile_args' : self.game_args['setup_tile_args'],
    #                         'setup_player_order_args': self.game_args['setup_player_order_args'],
    #                         'action_mode': 'simulate',
    #                         'action_history': self.game_args['action_history'].copy() + [(self.player_id, typ, action_id)],
    #                         'web_io': silence_io
    #                     }
    #                     simulate_game = GameEngine(simulate_game_args)
    #                     res = simulate_game.run_game()
    #                     action_res.append(res)
    #                 )
                    