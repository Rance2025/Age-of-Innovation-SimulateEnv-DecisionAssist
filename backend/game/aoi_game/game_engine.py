from .game_state import GameStateBase
from .action_system import ActionSystem
from .utils.action_request import ActionRequest
from .utils.actions_loader import get_readable_actions
from typing import Generator

class GameEngine:
    """游戏引擎 - 同步惰性生成器版本"""
    def __init__(self, num_players: int, init_settings: dict[str, str|list[int]|dict[str,str|int|list[int]]]):
        self.init_settings = init_settings                                              # 初始设置参数
        self.num_players = num_players                                                  # 玩家数量
        self.game_state = self._create_game_state()                                     # 游戏状态
        self.action_history = self.game_state.action_history                            # 行动历史
        self.game_state.effect_object()                                                 # 效果板块
        self.action_system = ActionSystem(self.game_state)                              # 行动系统
        
    def _create_game_state(self):
        """创建游戏状态"""
        out_ref = self

        class GameState(GameStateBase):
            """游戏状态类"""
            def __init__(self, num_players, init_settings) -> None:
                super().__init__(num_players=num_players, init_settings=init_settings)
            
            def invoke_immediate_action(self, player_id: int, args: tuple):
                """
                【生成器】立即行动 - 产出状态，接收响应，立即执行
                """
                yield from out_ref._execute_action(player_id, 'immediate', args)
            
        return GameState(self.num_players, self.init_settings)
    
    def _normal_action_turn(self, player_id: int) -> Generator[ActionRequest, int, None]:
        '''常规行动生成器 - 处理玩家完整回合'''
        # 执行常规行动（内部会自动处理触发的立即行动）
        yield from self._execute_action(player_id)
        
        # 处理后续连锁行动
        while self.action_system.is_next_action_exist(player_id):
            yield from self._execute_action(player_id)
        
        self.action_system.reset_action_state(player_id)

    def _execute_action(self, player_id: int, typ: str = 'normal', args: tuple = ()) -> Generator[ActionRequest, int, None]:
        """
        执行基本行动 - 产出状态，接收action_id，执行行动
        执行后自动处理触发的立即行动
        """
        # 获取可用行动列表
        available_action_ids = self.action_system.get_available_actions(player_id, typ, args)
        available_actions = get_readable_actions(available_action_ids)
        
        # 产出状态，等待外部选择
        action_id = yield ActionRequest(
            player_id=player_id,
            action_type=typ,
            available_actions=available_actions,
            game_state=self.game_state
        )

        # 确保选择的行动ID在可用行动ID列表中
        assert action_id in available_action_ids, f"Invalid action id: {action_id}"

        # 执行选中的行动
        self.action_history.append((player_id, typ, action_id))
        yield from self.action_system.execute_action(player_id, typ, action_id)

    def run_game(self) -> Generator[ActionRequest, int, None]:
        """运行整个游戏"""
        
        # 初始化立即行动队列
        self._immediate_action_queue: list[tuple[int, tuple]] = []
        
        def initial_setup_phase() -> Generator[ActionRequest, int, None]:
            """初始设置阶段"""
            
            # 4轮选择（逆蛇轮抽）
            for round_idx in range(1, 5):
                # 确定本轮玩家顺序
                if round_idx % 2 == 1:
                    current_turn_order = self.game_state.pass_order
                else:
                    current_turn_order = self.game_state.current_player_order

                # 按照本轮玩家顺序轮流进行初始设置行动
                for player_idx in current_turn_order:
                    yield from self._normal_action_turn(player_idx)
            
            # 标记初始板块选择阶段完成，进入初始建筑摆放阶段
            self.game_state.setup_choice_is_completed = True

            # 初始化初始建筑摆放顺序列表
            build_order = []

            # 查找本局游戏是否有玩家选择8号僧侣或/和10号奥马尔
            faction_8_owner_id = -1
            faction_10_owner_id = -1
            for idx in range(self.num_players):
                if self.game_state.players[idx].faction_id == 8:
                    faction_8_owner_id = idx
                if self.game_state.players[idx].faction_id == 10:
                    faction_10_owner_id = idx
            
            # 构建初始建筑摆放顺序列表
            match faction_8_owner_id, faction_10_owner_id:
                case -1, -1:
                    build_order = self.game_state.pass_order + self.game_state.current_player_order
                case _, -1:
                    build_order = [idx for idx in self.game_state.pass_order + self.game_state.current_player_order if idx != faction_8_owner_id] + [faction_8_owner_id]
                case -1, _:
                    build_order = self.game_state.pass_order + self.game_state.current_player_order + [faction_10_owner_id]
                case _, _:
                    build_order = [idx for idx in self.game_state.pass_order + self.game_state.current_player_order if idx != faction_8_owner_id] + [faction_10_owner_id, faction_8_owner_id]

            # 按照初始建筑摆放顺序列表轮流进行初始建筑摆放行动
            for player_idx in build_order:
                yield from self._normal_action_turn(player_idx)

            # 标记初始建筑摆放阶段完成，进入初始效果结算阶段
            self.game_state.setup_build_is_completed = True

            # 执行可能存在的初始效果
            for player_idx in self.game_state.pass_order:
                cur_player_setup_list = self.game_state.players[player_idx].setup_effect_list
                while cur_player_setup_list:
                    effect = cur_player_setup_list.pop(0)
                    yield from effect(player_idx)

            # 将初始未选的回合助推板的获取立即效果加一块钱
            for effect_object in self.game_state.all_available_object_dict['round_booster'].values():
                yield from effect_object.round_end()

        def execute_formal_round() -> Generator[ActionRequest, int, None]:
            """正式回合"""
            
            # 清空上一轮pass顺序
            self.game_state.pass_order.clear()

            # 复制当前轮玩家行动顺序
            current_player_order = self.game_state.current_player_order.copy()      

            # 执行本轮玩家收入效果
            for player_idx in current_player_order:
                for income_effect in self.game_state.players[player_idx].income_effect_list:
                    yield from income_effect(player_idx)
            
            # 当剩余玩家行动顺序不为空时，轮流执行玩家行动
            while current_player_order:
                for player_idx in current_player_order:
                    yield from self._normal_action_turn(player_idx)
                # 更新当前轮玩家行动顺序
                current_player_order = self.game_state.current_player_order.copy()

            # 分别结算本回合结束效果
            for effect_object_typ in [
                'round_scoring', 'final_scoring',
                'book_action', 'magics_action', 'faction', 'palace_tile', 'ability_tile', 'science_tile', 
                'round_booster'
            ]:
                for effect_object in self.game_state.all_available_object_dict[effect_object_typ].values():
                    yield from effect_object.round_end()
            
            # 将本回合pass顺序作为下回合的行动顺序
            self.game_state.current_player_order = self.game_state.pass_order.copy()

        # 初始设置阶段
        yield from initial_setup_phase()

        # 正式轮次阶段
        for round_idx in range(1, 7):
            # 设置游戏当前轮次
            self.game_state.round = round_idx  
            yield from execute_formal_round()

        # 终局结算阶段
        final_scores = self.game_state.calculate_players_total_score()
        yield ActionRequest(
            is_game_over=True,
            final_scores=final_scores,
            game_state=self.game_state
        )
