from ActionSystem import ActionSystem
from DetailedAction import DetailedAction
import random
import time
import copy
from web_io import GamePanel, Silence_IO
from typing import Union

class AgentBase:

    def __init__(self, game_state, player_id: int, game_args):
        self.player_id = player_id
        self.game_state = game_state
        self.player = self.game_state.players[player_id]
        self.action_system = ActionSystem(game_state, player_id)
        self.web_io: Union[GamePanel,Silence_IO] = game_args['web_io']
        self.all_detailed_actions = DetailedAction().all_detailed_actions
        self.game_args = game_args
        self.need_estimate = False

    def action_turn(self, typ: str, args: tuple = tuple()):
        match typ:
            case 'normal':
                if self.need_estimate and self.game_args['need_estimate']:
                    self.need_estimate = False
                    self.estimate()
                    
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
                if self.need_estimate and self.game_args['need_estimate']:
                    self.need_estimate = False
                    self.estimate()
                    
                self.action_step(mode='input',typ='immediate', args=args)
            
            case _ :
                raise ValueError(f"非法动作模式: {typ}")
                    
    def action_step(self, mode, typ, args):
        match mode:
            case 'input':
                available_action_ids = self.action_system.get_available_actions(typ, args)
                readable_action_ids = {id: self.all_detailed_actions[id]['description'] for id in available_action_ids}
                res_str = f'玩家{self.player_id + 1}的可选{typ}行动: \n'
                for key,value in readable_action_ids.items():
                    res_str += f'{key}: {value}\n'
                res_str = res_str[:-1]
                color_dict = {
                    0: 'white',
                    1: 'brown',
                    2: 'black',
                    3: 'blue',
                    4: 'green',
                    5: 'grey',
                    6: 'red',
                    7: 'yellow',
                }
                self.web_io.output(0,res_str,color=color_dict[self.player.planning_card_id])
                action_id = self.web_io.get_input()
                if action_id:
                    action_id = int(action_id)
                    self.web_io.output(self.player_id + 1, readable_action_ids[action_id])
                    print(f'玩家{self.player_id + 1}执行了{readable_action_ids[action_id]}')
                    # 记录该行动
                    self.game_args['action_history'].append((self.player_id, typ, action_id))
                    # 执行该行动
                    self.action_system.execute_action(typ, action_id)
                else:
                    if 65 in available_action_ids:
                        action_id = 65
                    else:
                        action_id = random.choice(available_action_ids)
                    self.web_io.output(self.player_id + 1, readable_action_ids[action_id])
                    print(f'玩家{self.player_id + 1}执行了{readable_action_ids[action_id]}')
                    # 记录该行动
                    self.game_args['action_history'].append((self.player_id, typ, action_id))
                    # 执行该行动
                    self.action_system.execute_action(typ, action_id)
                

            case 'target':
                action_id = args
                self.action_system.execute_action(typ, action_id) 

            case 'random':
                # self.seedid = int(time.strftime("%S%H%M", time.localtime()))
                # random.seed(self.seedid)
                # print(f'seed:{self.seedid}')
                available_action_ids = self.action_system.get_available_actions(typ, args)
                if 65 in available_action_ids and random.random()<=0.9:
                    action_id = 65
                else:
                    action_id = random.choice(available_action_ids)
                self.action_system.execute_action(typ, action_id)

            case _:
                raise Exception('Invalid mode')
    
    def reproduce(self, action_history_appendix: list = []) -> dict:
        return {}
    
    def simulate(self, action_history_appendix: list = []):
        pass

    def estimate(self):
        all_available_action_path = []
        max_deepth = 3
        def tracebacking(action_path: list = []): 
            reproduce_dict = self.reproduce(action_path)
            reproduce_game = reproduce_dict['reproduce_game']
            action_player_id ,action_typ, action_args = self.reproduce(action_path)['next_action']

            if action_player_id != self.player_id or len(action_path) >= max_deepth:
                all_available_action_path.append(action_path.copy())
                return
            
            available_action_ids = reproduce_game.agents[action_player_id].action_system.get_available_actions(mode=action_typ,args=action_args)

            for try_action_id in available_action_ids:
                action = (action_player_id, action_typ, try_action_id)
                action_path.append(action)
                tracebacking(action_path)
                action_path.pop()

        # start_time = time.time()
        tracebacking()
        # all_path_results = []
        # for action_path in all_available_action_path:
        #     results = []
        #     for i in range(100):
        #         seedid = int(time.strftime("%S%H%M", time.localtime()))+i
        #         random.seed(seedid)
        #         res = self.simulate(action_path)
        #         results.append(res)
        #     all_path_results.append(sum(results)/len(results))
        
        # end_time = time.time()
        # print(end_time-start_time)

        print(all_available_action_path)
