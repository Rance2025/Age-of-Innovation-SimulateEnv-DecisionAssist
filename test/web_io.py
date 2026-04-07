"""
Web IO 模块 - 与前端交互的实现
提供 WebIO 和 SilentIO 两种实现
"""
import json
import queue
import threading
from abc import ABC, abstractmethod
from typing import Optional, List, Tuple, Dict, Any

try:
    from .logger import get_logger
except ImportError:
    from logger import get_logger

logger = get_logger(__name__)


class IOInterface(ABC):
    """IO 接口抽象基类"""

    @abstractmethod
    def get_input(self, prompt: str = "> ") -> str: pass

    @abstractmethod
    def output(self, channel: int, message: str, color: Optional[str] = None) -> None: pass

    @abstractmethod
    def update_player_state(self, player_id: int, updates: dict) -> bool: pass

    @abstractmethod
    def update_global_status(self, message: str) -> None: pass

    @abstractmethod
    def update_terrain(self, row: int, col: int, terrain_type: int) -> None: pass

    @abstractmethod
    def update_building(self, hex_row: int, hex_col: int, building_color: int, building_id: int, mode: str = 'replace') -> bool: pass

    @abstractmethod
    def set_round_scoring(self, round_num: int, round_scoring_id: int) -> bool: pass

    @abstractmethod
    def set_final_round_bonus(self, final_scoring_id: int) -> bool: pass

    @abstractmethod
    def set_bonus_columns(self, round_bonus_ids: List[int]) -> bool: pass

    @abstractmethod
    def round_update(self, round_num: int) -> bool: pass

    @abstractmethod
    def get_round_bonus(self, setup_round_booster_ids: List[int], round_booster_id: int) -> bool: pass

    @abstractmethod
    def return_round_bonus(self, setup_round_booster_ids: List[int], round_booster_id: int) -> bool: pass

    @abstractmethod
    def highlight_hex(self, hex_list: List[Tuple[int, int]]) -> bool: pass


class MessageQueueManager:
    """消息队列管理器 - 单例模式（简化版：单一队列）"""

    _instance = None

    def __new__(cls, player_count: int = 3):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, player_count: int = 3):
        if self._initialized:
            return
        self._player_count = player_count
        self._queues = {
            'input': queue.Queue(),
            'output': queue.Queue()  # 单一输出队列，所有消息都通过这里
        }
        # 全量状态缓存
        self._state_lock = threading.Lock()
        self._full_state: Dict[str, Any] = {
            "players": [],
            "round_info": {
                "current_round": 0,
                "round_scoring": [],
                "final_scoring": 0,
                "bonus_columns": []
            },
            "map": {
                "terrain": [],
                "highlights": []
            },
            "global_status": "",
            "actions": []
        }
        self._initialized = True

    @property
    def input_queue(self): return self._queues['input']

    @property
    def output_queue(self): return self._queues['output']

    def put_input(self, message: str): self._queues['input'].put(message)

    def get_input(self, timeout: Optional[float] = None): return self._queues['input'].get(timeout=timeout)

    def put_message(self, message: dict) -> bool:
        """发送消息到统一队列

        Args:
            message: 包含 type 和 data 的字典
        """
        # 同步更新状态缓存
        self._update_state_cache(message)
        self._queues['output'].put(json.dumps(message))
        return True

    def get_message(self, timeout: Optional[float] = None):
        """从队列获取消息"""
        return self._queues['output'].get(timeout=timeout)

    def _update_state_cache(self, message: dict):
        """根据消息类型更新状态缓存"""
        with self._state_lock:
            msg_type = message.get('type')
            data = message.get('data', {})
            player_id = message.get('player_id', -1)

            if msg_type == 'player_state' and player_id >= 0:
                # 确保 players 列表长度足够
                while len(self._full_state["players"]) <= player_id:
                    self._full_state["players"].append({
                        "id": len(self._full_state["players"]),
                        "faction": "", "planningCard": None, "score": 20,
                        "money": 0, "mineral": 0, "mibao": 0,
                        "bank": 0, "law": 0, "engineering": 0, "medical": 0,
                        "magic1": 5, "magic2": 7, "magic3": 0,
                        "cities": 0, "navigation": 0, "shovel": 3, "logs": []
                    })
                self._full_state["players"][player_id].update(data)

            elif msg_type == 'global_status':
                self._full_state["global_status"] = data.get('message', '')

            elif msg_type == 'actions':
                self._full_state["actions"] = data.get('actions', [])

            elif msg_type == 'terrain_update':
                row, col = data.get('row'), data.get('col')
                terrain_type = data.get('terrain_type')
                if row is not None and col is not None and terrain_type is not None:
                    # 移除旧的地形记录
                    self._full_state["map"]["terrain"] = [
                        t for t in self._full_state["map"]["terrain"]
                        if not (t.get('row') == row and t.get('col') == col)
                    ]
                    self._full_state["map"]["terrain"].append({
                        "row": row, "col": col, "terrain_type": terrain_type
                    })

            elif msg_type == 'highlight_hex':
                self._full_state["map"]["highlights"] = data.get('hex_list', [])

            elif msg_type == 'round_scoring':
                round_num = data.get('round')
                scoring_id = data.get('scoring_id')
                if round_num and scoring_id:
                    while len(self._full_state["round_info"]["round_scoring"]) < round_num:
                        self._full_state["round_info"]["round_scoring"].append(-1)
                    self._full_state["round_info"]["round_scoring"][round_num - 1] = scoring_id

            elif msg_type == 'final_scoring':
                self._full_state["round_info"]["final_scoring"] = data.get('scoring_id', 0)

            elif msg_type == 'bonus_columns':
                self._full_state["round_info"]["bonus_columns"] = data.get('bonus_ids', [])

            elif msg_type == 'round_update':
                self._full_state["round_info"]["current_round"] = data.get('round', 0)

    def get_full_state(self) -> Dict[str, Any]:
        """获取完整游戏状态（供前端全量查询）"""
        with self._state_lock:
            import copy
            return copy.deepcopy(self._full_state)

    def init_state(self, state: Dict[str, Any]):
        """初始化状态"""
        with self._state_lock:
            self._full_state = state


class WebIO(IOInterface):
    """Web IO 实现 - 通过统一 SSE 队列与前端通信（简化版）"""

    def __init__(self, player_count: int = 3):
        self._player_count = player_count
        self._queues = MessageQueueManager(player_count)
        self._player_states = [self._create_default_state() for _ in range(player_count)]
        self.planning_card_colors = {
            "development": "#ff4444", "military": "#4444ff", "trade": "#44ff44",
            "technology": "#ffff44", "diplomacy": "#ff44ff",
            "infrastructure": "#ffaa44", "expansion": "#44ffff"
        }

    def _create_default_state(self) -> dict:
        return {
            'money': 0, 'ore': 0, 'meeple': 0, 'bank_book': 0, 'law_book': 0,
            'engineering_book': 0, 'medical_book': 0, 'magics_1': 0, 'magics_2': 0,
            'magics_3': 0, 'city_amount': 0, 'navigation_level': 0, 'shovel_level': 0,
            'planning_card': None, 'faction': None, 'score': 0
        }

    def get_input(self, prompt: str = "> ") -> str:
        return self._queues.get_input()

    def output(self, channel: int, message: str, color: Optional[str] = None) -> None:
        """发送日志消息到统一队列"""
        self._queues.put_message({
            'type': 'log',
            'player_id': channel,
            'data': {'content': str(message), 'color': color}
        })

    def update_player_state(self, player_id: int, updates: dict) -> bool:
        """更新玩家状态 - 使用统一队列"""
        if not 0 <= player_id < self._player_count:
            return False

        state = self._player_states[player_id]
        for key, value in updates.items():
            if key in state:
                state[key] = value

        # 字段映射：后端字段 -> 前端字段
        field_mapping = {
            'money': 'money', 'ore': 'mineral', 'meeple': 'mibao',
            'bank_book': 'bank', 'law_book': 'law',
            'engineering_book': 'engineering', 'medical_book': 'medical',
            'magics_1': 'magic1', 'magics_2': 'magic2', 'magics_3': 'magic3',
            'city_amount': 'cities', 'navigation_level': 'navigation',
            'shovel_level': 'shovel', 'planning_card': 'planningCard',
            'faction': 'faction', 'score': 'score'
        }

        frontend_updates = {}
        for backend_field, frontend_field in field_mapping.items():
            if backend_field in updates:
                frontend_updates[frontend_field] = state[backend_field]

        self._queues.put_message({
            'type': 'player_state',
            'player_id': player_id,
            'data': frontend_updates
        })
        return True

    def update_global_status(self, message: str) -> None:
        """更新全局状态"""
        self._queues.put_message({
            'type': 'global_status',
            'data': {'message': message}
        })

    def update_terrain(self, row: int, col: int, terrain_type: int) -> None:
        """更新地形"""
        self._queues.put_message({
            'type': 'terrain_update',
            'data': {'row': row, 'col': col, 'terrain_type': terrain_type}
        })

    def update_building(self, hex_row: int, hex_col: int, building_color: int, building_id: int, mode: str = 'replace') -> bool:
        """更新建筑"""
        self._queues.put_message({
            'type': 'building_update',
            'data': {'hex_row': hex_row, 'hex_col': hex_col, 'color': building_color, 'id': building_id, 'mode': mode}
        })
        return True

    def set_round_scoring(self, round_num: int, round_scoring_id: int) -> bool:
        """设置回合计分"""
        self._queues.put_message({
            'type': 'round_scoring',
            'data': {'round': round_num, 'scoring_id': round_scoring_id}
        })
        return True

    def set_final_round_bonus(self, final_scoring_id: int) -> bool:
        """设置终局奖励"""
        self._queues.put_message({
            'type': 'final_scoring',
            'data': {'scoring_id': final_scoring_id}
        })
        return True

    def set_bonus_columns(self, round_bonus_ids: List[int]) -> bool:
        """设置助推板块"""
        self._queues.put_message({
            'type': 'bonus_columns',
            'data': {'bonus_ids': round_bonus_ids}
        })
        return True

    def round_update(self, round_num: int) -> bool:
        """回合更新 - 触发回合计分板翻面和强调下一回合"""
        self._queues.put_message({
            'type': 'round_scoring_update',
            'data': {'round': round_num}
        })
        return True

    def get_round_bonus(self, setup_round_booster_ids: List[int], round_booster_id: int) -> bool:
        """获取回合奖励"""
        self._queues.put_message({
            'type': 'round_bonus_get',
            'data': {'booster_index': setup_round_booster_ids.index(round_booster_id)}
        })
        return True

    def return_round_bonus(self, setup_round_booster_ids: List[int], round_booster_id: int) -> bool:
        """归还回合奖励"""
        self._queues.put_message({
            'type': 'round_bonus_back',
            'data': {'booster_index': setup_round_booster_ids.index(round_booster_id)}
        })
        return True

    def highlight_hex(self, hex_list: List[Tuple[int, int]]) -> bool:
        """高亮地块"""
        self._queues.put_message({
            'type': 'highlight_hex',
            'data': {'hex_list': hex_list}
        })
        return True


class SilentIO(IOInterface):
    """静默 IO - 用于模拟模式"""

    def get_input(self, prompt: str = "> ") -> str: return ""
    def output(self, channel: int, message: str, color: Optional[str] = None) -> None: pass
    def update_player_state(self, player_id: int, updates: dict) -> bool: return True
    def update_global_status(self, message: str) -> None: pass
    def update_terrain(self, row: int, col: int, terrain_type: int) -> None: pass
    def update_building(self, hex_row: int, hex_col: int, building_color: int, building_id: int, mode: str = 'replace') -> bool: return True
    def set_round_scoring(self, round_num: int, round_scoring_id: int) -> bool: return True
    def set_final_round_bonus(self, final_scoring_id: int) -> bool: return True
    def set_bonus_columns(self, round_bonus_ids: List[int]) -> bool: return True
    def round_update(self, round_num: int) -> bool: return True
    def get_round_bonus(self, setup_round_booster_ids: List[int], round_booster_id: int) -> bool: return True
    def return_round_bonus(self, setup_round_booster_ids: List[int], round_booster_id: int) -> bool: return True
    def highlight_hex(self, hex_list: List[Tuple[int, int]]) -> bool: return True


# 兼容旧版名称
GamePanel = WebIO
Silence_IO = SilentIO
