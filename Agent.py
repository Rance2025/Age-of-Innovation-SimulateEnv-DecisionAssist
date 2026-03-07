from ActionSystem import ActionSystem
from DetailedAction import DetailedAction
import random
from web_io import GamePanel, Silence_IO
from AIAssistant import ai_assistant

class AgentBase:

    def __init__(self, game_state, player_id: int, game_args):
        self.player_id = player_id
        self.game_state = game_state
        self.player = self.game_state.players[player_id]
        self.action_system = ActionSystem(game_state, player_id)
        self.web_io: GamePanel|Silence_IO = game_args['web_io']
        self.all_detailed_actions = DetailedAction().all_detailed_actions
        self.game_args = game_args
        self.need_estimate = False
        self.action_mode = self.game_args['action_mode'][player_id]
        self.simulation_path = self.game_args['simulation_path']
        self.AI_selection_action_ids = []

    def action_turn(self, typ: str, args: tuple = tuple()):

        # 匹配行动类型（常规 / 立即）
        match typ:

            # 常规行动
            case 'normal':
                
                # 玩家先执行一常规行动
                data = self.action_stragety(self.action_mode, typ='normal', args=args)
                if data[0]:
                    return data

                # 当玩家仍有下一常规行动时
                while self.action_system.is_next_action_exist():
                    # 则继续执行一个常规行动
                    data = self.action_stragety(self.action_mode, typ='normal', args=args)
                    if data[0]:
                        return data
                    
                # 否则重置当前行动状态为每轮初始状态
                self.action_system.reset_action_state()

            # 立即行动
            case 'immediate':
                # 玩家执行一立即行动
                data = self.action_stragety(self.action_mode, typ='immediate', args=args)
                if data[0]:
                    return data
                
            # 其他非法行动
            case _:

                # 报错
                raise ValueError(f"非法动作模式: {typ}")
        
        return (False,)
    
    def action_stragety(self, action_mode:str, typ:str, args: tuple=tuple()):

        # 匹配行动模式（human | random_simulate | reproduce）
        match action_mode:

            # 若是人类，则手动输入
            case 'human':
                self.action_step(mode='input',typ=typ, args=args)

            # 若是随机模拟，则有模拟路径就按路径，无路径就随机选择
            case 'random_simulate':
                path_idx = self.game_args['remaining_path_length']
                if path_idx > 0:
                    action_player_id, action_typ, action_id = self.simulation_path[-path_idx]
                    path_idx -= 1
                    assert action_player_id == self.player_id
                    assert action_typ == typ
                    self.action_step('target', typ, action_id)
                else:
                    self.action_step('random', typ, args)

            # 若是复现，则按路径模拟完毕立即返回
            case 'reproduce':
                if self.game_args['next_immediate_action']:
                    return (True, *self.game_args['next_immediate_action'])
                
                path_idx = self.game_args['remaining_path_length']
                if path_idx > 0:
                    action_player_id, action_typ, action_id = self.simulation_path[-path_idx]
                    path_idx -= 1
                    assert action_player_id == self.player_id
                    assert action_typ == typ
                    self.action_step('target', typ, action_id)
                else:
                    return (True, self.player_id, typ, args)
            # 若是AI ，则由AI提供选择
            case 'AI_selection_per_step':
                available_action_ids = self.action_system.get_available_actions(typ, args)
                readable_action_ids = {id: self.all_detailed_actions[id]['description'] for id in available_action_ids}
                
                AI_selection = 0

            case 'AI_selection_per_turn':
                if self.AI_selection_action_ids:
                    pass
                else:
                    pass
                    self.AI_selection_action_ids.extend()
                pass
                
        return (False,)
                    
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
                while True:
                    try:
                        action_id = self.web_io.get_input()
                        # 当有输入时，则按输入行动执行
                        if action_id:
                            action_id = int(action_id)
                            self.web_io.output(self.player_id + 1, readable_action_ids[action_id], color='blue' if typ == 'normal' else 'celeste')
                            print(f'玩家{self.player_id + 1}执行了{readable_action_ids[action_id]}')
                            # 记录该行动
                            self.game_args['action_history'].append((self.player_id, typ, action_id))
                            # 执行该行动
                            self.action_system.execute_action(typ, action_id)
                        # 当无输入时，则随机选择一个行动（若65：跳过在其中，则直接选择这个）
                        else:
                            if 65 in available_action_ids:
                                action_id = 65
                            else:
                                action_id = random.choice(available_action_ids)
                            self.web_io.output(self.player_id + 1, readable_action_ids[action_id], color='blue' if typ == 'normal' else 'celeste')
                            print(f'玩家{self.player_id + 1}执行了{readable_action_ids[action_id]}')
                            # 记录该行动
                            self.game_args['action_history'].append((self.player_id, typ, action_id))
                            # 执行该行动
                            self.action_system.execute_action(typ, action_id)
                        
                        # 跳出循环
                        break

                    except (KeyError, ValueError):
                        pass
                    
            case 'target':
                action_id = args
                # 记录该行动
                self.game_args['action_history'].append((self.player_id, typ, action_id))
                # 执行该行动
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
                # 记录该行动
                self.game_args['action_history'].append((self.player_id, typ, action_id))
                # 执行该行动
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
