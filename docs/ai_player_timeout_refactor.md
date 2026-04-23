# AI 玩家超时策略重构设计文档

## 文档信息

- **创建日期**: 2026-04-23
- **版本**: 1.0
- **状态**: 待实施
- **作者**: AI Assistant

---

## 1. 问题描述

### 1.1 当前问题

AI 玩家与人类玩家走**两条完全不同的链路**，导致：

1. **AI 没有超时检测**：AI 分支直接返回 action_id，不检查 `_action_deadline`
2. **AI 不扣减主时间**：主时间耗尽后 AI 仍然可以无限次 sleep 3 秒
3. **AI 不触发读秒**：人类玩家进入读秒后必须在 byo_yomi_time（45秒）内提交，AI 没有此限制
4. **AI 不使用超时回退策略**：人类超时后使用 `timeout_strategy`（如 `random_fast_action`），AI 仍用自身 Agent 策略
5. **AI 不推送可用行动到前端**：前端无法看到 AI 的思考状态
6. **代码重复与冗余**：计时器更新、时间扣减、超时回退等逻辑在两条链路上重复实现
7. **竞态条件风险**：
   - **AI 竞态**：AI 后台线程在超时后才放入 queue，数据被下一回合误用
   - **人类竞态**：用户在倒计时最后一秒提交，后端已先走超时策略，导致冲突

### 1.2 目标

让 AI 玩家**完全复用**人类玩家的行动链路，仅有一个差异点：

> **差异点**：AI 的最小思考时间为 3 秒（即使计算很快，也至少等 3 秒）。
>
> 其余全部一致：计时器检测、主时间扣减、读秒切换、超时回退策略、前端推送。

---

## 2. 架构设计

### 2.1 核心思路

**统一入口**：所有玩家（人类/AI）都通过 `_wait_for_action_with_timeout` 获取行动。

**request_id 机制**：
- 每回合生成唯一的 `request_id`（单调递增整数）
- AI 后台线程和人类前端提交都携带 `request_id`
- 主线程从 queue 取出后验证 `request_id`，不匹配则丢弃
- 彻底解决竞态条件（AI 超时数据、人类延迟提交）

**AI 的特殊处理**：
- 在调用 `_wait_for_action_with_timeout` **之前**，启动后台线程计算 AI 决策
- 后台线程计算完成后，将结果（携带 `request_id`）放入 `_input_queue`
- 后台线程确保最少 3 秒后才会放入 queue
- 主线程进入 `_wait_for_action_with_timeout`，与人类完全一致

### 2.2 调用链对比

#### 重构前（当前实现）

```
GameController._game_loop()
│
├─ while 游戏未结束:
│   │
│   ├─ _get_action_decision(request)
│   │   │
│   │   ├─ 初始化计时器（统一）
│   │   │       _action_start_time, _action_deadline
│   │   │       _update_timer_in_state_manager()
│   │   │
│   │   ├─ _resolve_action_decision(request, player_id)  # 👈 分叉点（过早）
│   │   │   │
│   │   │   ├─ AI 玩家（player_id in _agents）
│   │   │   │       agent.get_action(request)
│   │   │   │       time.sleep(3)  # ❌ 固定 sleep，不检查 deadline
│   │   │   │       return action_id, metadata  # ❌ 直接返回，绕过超时检测
│   │   │   │
│   │   │   └─ 人类玩家
│   │   │           _push_available_actions()  # 推送到前端
│   │   │           _wait_for_action_with_timeout(player_id)
│   │   │               ├── 主时间耗尽 → 切换到读秒
│   │   │               ├── 读秒耗尽 → _execute_timeout_action() ✅
│   │   │               └── 从 queue 取出前端提交
│   │   │
│   │   ├─ _update_player_time_after_action()  # 扣减时间（AI也走，但读秒逻辑不一致）
│   │   └─ _push_timer_update_after_action()
│   │
│   ├─ game.send(action_id)
│   └─ 下一回合...
```

#### 重构后（目标实现）

```
GameController._game_loop()
│
├─ while 游戏未结束:
│   │
│   ├─ _get_action_decision(request)  # 统一入口
│   │   │
│   │   ├─ 【阶段1】初始化计时器（AI/人类完全一样）
│   │   │       _action_start_time = now
│   │   │       _action_deadline = now + remaining
│   │   │       _update_timer_in_state_manager(player_id)  # 推送前端
│   │   │
│   │   ├─ 【阶段2】决策准备（AI/人类完全一样）
│   │   │       │
│   │   │       ├─ _resolve_action_decision(request, player_id)
│   │   │       │   │
│   │   │       │   ├─ request_id = _get_next_request_id()  # 生成本回合唯一ID
│   │   │       │   │
│   │   │       │   ├─ 准备输入源（唯一差异点）
│   │   │       │   │   ├─ AI 玩家 → 启动 ai_compute_thread(request_id)
│   │   │       │   │   │       后台线程：agent.get_action() → sleep(3s) → put queue(request_id)
│   │   │       │   │   └─ 人类玩家 → 无需操作（等待前端提交request_id）
│   │   │       │   │
│   │   │       │   └─ _push_available_actions(request, request_id)  # AI/人类都推送
│   │   │       │
│   │   │       └─ 返回（等待外部输入）
│   │   │
│   │   ├─ 【阶段3】统一等待（AI/人类完全一样）
│   │   │       │
│   │   │       ▼
│   │   │   _wait_for_action_with_timeout(player_id, request_id)  # 核心复用
│   │   │       │
│   │   │       ├─ 主时间阶段（remaining > 0）
│   │   │       │       _input_queue.get(timeout=remaining_ms)
│   │   │       │       │
│   │   │       │       ├─ ✅ 收到结果
│   │   │       │       │       request_id 匹配？→ ✅ return payload
│   │   │       │       │       request_id 不匹配？→ ❌ 丢弃，继续等待
│   │   │       │       └─ ❌ 超时（queue.Empty）
│   │   │       │               _player_remaining_times[player_id] = 0
│   │   │       │               _action_deadline = now + byo_yomi_time
│   │   │       │               _push_timer_state_update()  # 推送：开始读秒
│   │   │       │
│   │   │       ├─ 读秒阶段
│   │   │       │       _input_queue.get(timeout=byo_yomi_ms)
│   │   │       │       │
│   │   │       │       ├─ ✅ 收到结果
│   │   │       │       │       request_id 匹配？→ ✅ return payload
│   │   │       │       │       request_id 不匹配？→ ❌ 丢弃，继续等待
│   │   │       │       └─ ❌ 超时（queue.Empty）
│   │   │       │               return _execute_timeout_action(player_id)
│   │   │       │               # 统一超时回退策略 ✅
│   │   │       │
│   │   │       └─ return payload / 超时结果
│   │   │
│   │   ├─ 【阶段4】结果解析（AI/人类完全一样）
│   │   │       解析 action_id, selection_source, selection_strategy
│   │   │       return (action_id, metadata)
│   │   │
│   │   ├─ 【阶段5】时间扣减（AI/人类完全一样）
│   │   │       _update_player_time_after_action(player_id, action_index)
│   │   │
│   │   └─ 【阶段6】推送更新（AI/人类完全一样）
│   │           _push_timer_update_after_action()
│   │
│   ├─ _record_action_selection_metadata(request, metadata)  # 记录元数据
│   │
│   ├─ request = game.send(action_id)  # 推进游戏引擎
│   │
│   └─ 下一回合...
```

### 2.3 关键设计原则

1. **单一入口**：所有玩家都走 `_wait_for_action_with_timeout`
2. **后台计算**：AI 的 Agent 计算在独立线程，不阻塞主线程
3. **最小延迟**：通过后台线程 sleep 确保 3 秒，不影响主线程的计时逻辑
4. **完全复用**：`_wait_for_action_with_timeout`、`_execute_timeout_action`、`_update_player_time_after_action` 都不需要修改

---

## 3. 详细设计

### 3.1 文件清单

| 文件 | 修改类型 | 说明 |
|------|---------|------|
| `backend/game/start_game.py` | 修改 | 重构 `_resolve_action_decision` |

### 3.2 修改内容

#### 3.2.1 新增 `_get_next_request_id` 方法

**位置**：`backend/game/start_game.py`，在 `__init__` 中初始化，新增方法

**代码**：

```python
def __init__(self, game_id: str, num_players: int = 3, timer_config: dict = None):
    ...
    # request_id 计数器，每回合递增
    self._current_request_id: int = 0

def _get_next_request_id(self) -> int:
    """生成下一个请求ID（单调递增）"""
    self._current_request_id += 1
    return self._current_request_id
```

---

#### 3.2.2 `_resolve_action_decision` 方法（完整重写）

**位置**：`backend/game/start_game.py` lines 277-320

**当前代码**：

```python
def _resolve_action_decision(self, request: ActionRequest, player_id: int) -> Tuple[int, Dict[str, Optional[str]]]:
    """解析行动决策，不在此处处理计时扣减。"""
    if player_id in self._agents:
        agent = self._agents[player_id]
        start_time = time.time()
        action_id = agent.get_action(request)
        elapsed = time.time() - start_time
        
        # AI 玩家最小3秒延迟（非阻塞式：游戏线程独立运行）
        min_delay = 3.0
        if elapsed < min_delay:
            time.sleep(min_delay - elapsed)
        
        strategy_name = getattr(agent, 'strategy_name', None) or getattr(agent, 'name', None) or agent.__class__.__name__
        return action_id, {
            'selection_source': 'system',
            'selection_strategy': strategy_name
        }

    self._push_available_actions(request)
    payload = self._wait_for_action_with_timeout(player_id)
    # ... 人类分支解析逻辑
```

**重构后代码**：

```python
def _resolve_action_decision(self, request: ActionRequest, player_id: int) -> Tuple[int, Dict[str, Optional[str]]]:
    """解析行动决策，不在此处处理计时扣减。
    
    所有玩家（人类/AI）统一走 _wait_for_action_with_timeout 链路，
    确保计时器、超时检测、读秒切换、超时回退策略、request_id 验证完全一致。
    """
    # 生成本回合唯一的 request_id
    request_id = self._get_next_request_id()
    
    # AI 玩家：启动后台线程计算决策（绑定 request_id）
    if player_id in self._agents:
        self._start_ai_computation_thread(request, player_id, request_id)
    
    # 推送可用行动到前端（携带 request_id，供人类提交使用）
    self._push_available_actions(request, request_id)
    
    # 统一等待行动提交（验证 request_id）
    payload = self._wait_for_action_with_timeout(player_id, request_id)
    
    # 解析 payload（完全复用现有逻辑）
    if isinstance(payload, dict) and payload.get('__stop__') is True:
        raise GameStopped()
    
    if isinstance(payload, dict):
        action_id = int(payload.get('action_id'))
        selection_source = 'system' if payload.get('selection_source') == 'system' else 'manual'
        selection_strategy = payload.get('selection_strategy')
        selection_mode = payload.get('selection_mode')
        normalized_strategy = selection_strategy.strip() if isinstance(selection_strategy, str) else None
        normalized_mode = selection_mode.strip() if isinstance(selection_mode, str) else None
        metadata = {
            'selection_source': selection_source,
            'selection_strategy': normalized_strategy
        }
        if normalized_mode:
            metadata['selection_mode'] = normalized_mode
        return action_id, metadata
    
    return int(payload), {
        'selection_source': 'manual',
        'selection_strategy': None
    }
```

#### 3.2.3 新增 `_start_ai_computation_thread` 方法

**位置**：`backend/game/start_game.py`，在 `_resolve_action_decision` 之后

**代码**：

```python
def _start_ai_computation_thread(self, request: ActionRequest, player_id: int, request_id: int):
    """启动 AI 计算后台线程。
    
    后台线程执行 Agent 计算，确保最少 3 秒后才将结果放入 input_queue。
    主线程不受阻塞，继续走 _wait_for_action_with_timeout 链路。
    
    Args:
        request: 当前行动请求
        player_id: AI 玩家 ID
        request_id: 本回合唯一请求ID（放入queue时携带，用于验证）
    """
    agent = self._agents[player_id]
    
    def ai_compute_and_enqueue():
        """AI 计算并放入队列（携带 request_id）。"""
        try:
            # 计算决策
            start_time = time.time()
            action_id = agent.get_action(request)
            elapsed = time.time() - start_time
            
            # 确保最少 3 秒（如果计算很快，sleep 补足）
            min_delay = 3.0
            if elapsed < min_delay:
                # 分段 sleep，可响应 _stop_event
                remaining = min_delay - elapsed
                while remaining > 0 and not self._stop_event.is_set():
                    sleep_chunk = min(0.1, remaining)
                    time.sleep(sleep_chunk)
                    remaining -= sleep_chunk
            
            # 检查游戏是否仍在运行（避免游戏结束后放入脏数据）
            if self.is_running and not self._stop_event.is_set():
                strategy_name = getattr(agent, 'strategy_name', None) or \
                               getattr(agent, 'name', None) or \
                               agent.__class__.__name__
                
                # 放入 queue（携带 request_id，用于主线程验证）
                self._input_queue.put({
                    'action_id': action_id,
                    'request_id': request_id,  # 关键：绑定本回合ID
                    'selection_source': 'system',
                    'selection_strategy': strategy_name
                })
        except Exception:
            # Agent 计算失败：不放入 queue，让 _wait_for_action_with_timeout 自然超时
            import traceback
            traceback.print_exc()
    
    # 启动后台线程（daemon=True，主线程结束时自动退出）
    ai_thread = threading.Thread(target=ai_compute_and_enqueue, daemon=True)
    ai_thread.start()
```

### 3.3 复用分析

| 组件 | 人类玩家 | AI 玩家（重构后） | 是否复用 |
|------|---------|-----------------|---------|
| `_get_action_decision` | ✅ | ✅ | 完全复用 |
| `_resolve_action_decision` | ✅ | ✅ | 完全复用（增加 AI 线程启动） |
| `_push_available_actions` | ✅ | ✅ | 完全复用（新增 AI 也推送） |
| `_wait_for_action_with_timeout` | ✅ | ✅ | **核心复用** |
| 主时间耗尽检测 | ✅ | ✅ | 完全复用 |
| 读秒切换 | ✅ | ✅ | 完全复用 |
| 读秒耗尽检测 | ✅ | ✅ | 完全复用 |
| `_execute_timeout_action` | ✅ | ✅ | 完全复用 |
| `_update_player_time_after_action` | ✅ | ✅ | 完全复用 |
| `_update_timer_in_state_manager` | ✅ | ✅ | 完全复用 |
| 前端状态推送 | ✅ | ✅ | 完全复用 |

### 3.4 新增与修改对比

| 类型 | 内容 | 说明 |
|------|------|------|
| **修改** | `_resolve_action_decision` | 重构为统一入口，生成 request_id |
| **修改** | `_wait_for_action_with_timeout` | 增加 request_id 验证 |
| **修改** | `_push_available_actions` | 推送 request_id 到前端 |
| **新增** | `_get_next_request_id` | request_id 生成器 |
| **新增** | `_start_ai_computation_thread` | 封装 AI 后台线程逻辑 |
| **不变** | `_execute_timeout_action` | 无需任何修改 |
| **不变** | `_update_player_time_after_action` | 无需任何修改 |
| **不变** | `_get_action_decision` | 无需任何修改 |

---

### 3.5 Queue 清理策略

**问题**：当前代码只在 `start()` 和 `stop()` 时清理 queue，但**回合切换时**没有清理。

**解决方案**：在生成新 `request_id` 后、进入 `_wait_for_action_with_timeout` 前，清理 queue 中所有残留数据。

```python
def _resolve_action_decision(self, request, player_id):
    """解析行动决策"""
    # 1. 生成新 request_id
    request_id = self._get_next_request_id()
    
    # 2. 清理上一回合的残留数据（关键补充）
    self._clear_input_queue()
    
    # 3. 启动 AI 线程（如果是 AI 玩家）
    if player_id in self._agents:
        self._start_ai_computation_thread(request, player_id, request_id)
    
    # 4. 推送可用行动
    self._push_available_actions(request, request_id)
    
    # 5. 等待输入
    payload = self._wait_for_action_with_timeout(player_id, request_id)
    # ...
```

**清理时机**：
| 时机 | 操作 | 说明 |
|------|------|------|
| **游戏启动** | `_clear_input_queue()` | 已有 |
| **游戏停止** | `_clear_input_queue()` | 已有 |
| **每回合开始** | `_clear_input_queue()` | **新增** |

**为什么需要每回合清理**：
- AI 线程在超时后才放入 queue（如场景3中的 request_id=3）
- 下一回合开始时，这些过期数据仍在 queue 中
- 虽然 `request_id` 验证会丢弃它们，但清理可以减少 queue 堆积

---

### 3.6 Player ID 验证

**问题**：当前 queue 是全局共享的，虽然游戏流程是单玩家回合制，但代码层面没有防止错误 player 提交的保护。

**解决方案**：在 `_wait_for_action_with_timeout` 中增加 `player_id` 验证。

```python
def _wait_for_action_with_timeout(self, player_id, request_id):
    """等待玩家行动，验证 request_id 和 player_id"""
    
    def validate_payload(payload):
        """验证 payload 的有效性"""
        if not isinstance(payload, dict):
            return False, "Invalid payload type"
        
        # 验证 request_id
        if payload.get('request_id') != request_id:
            return False, f"Request ID mismatch: {payload.get('request_id')} != {request_id}"
        
        # 验证 player_id（关键补充）
        # 人类提交时携带 player_id，AI 提交时不携带（默认当前玩家）
        payload_player_id = payload.get('player_id')
        if payload_player_id is not None and payload_player_id != player_id:
            return False, f"Player ID mismatch: {payload_player_id} != {player_id}"
        
        return True, None
    
    # 主时间阶段
    remaining = self._player_remaining_times[player_id]
    if remaining > 0:
        deadline = time.time() + remaining / 1000.0
        while time.time() < deadline:
            try:
                payload = self._input_queue.get(timeout=min(0.1, deadline - time.time()))
                
                valid, error = validate_payload(payload)
                if valid:
                    return payload
                else:
                    # 记录丢弃原因（调试用途）
                    print(f"[Queue] Discarded invalid payload: {error}")
                    continue
                    
            except queue.Empty:
                continue
        
        # 切换到读秒...
    
    # 读秒阶段（同样验证）
    # ...
```

**验证规则**：
| 数据类型 | request_id | player_id | 处理 |
|---------|-----------|-----------|------|
| AI 提交 | 必须匹配 | 不携带 | ✅ 通过 |
| 人类提交 | 必须匹配 | 必须匹配 | ✅ 通过 |
| 过期数据 | 不匹配 | - | ❌ 丢弃 |
| 错误玩家 | 匹配 | 不匹配 | ❌ 丢弃 |

---

## 4. AI 计算超时参数讨论

### 4.1 问题提出

用户提问：能否在 `ai_compute_and_enqueue` 中传入一个超时参数，超出时间抛出异常，进入 except 块？

### 4.2 方案分析

#### 方案A：在 Agent 内部实现超时检查（推荐未来使用）

**思路**：修改 `BaseActionAgent` 接口，增加超时检查点。

```python
class BaseActionAgent:
    def __init__(self, rng=None):
        self._rng = rng or random
        self._timeout_deadline = None  # 超时截止时间
    
    def set_timeout(self, timeout_ms: float):
        """GameController 在启动计算前设置超时"""
        self._timeout_deadline = time.time() * 1000 + timeout_ms
    
    def _check_timeout(self):
        """子类应在计算关键点调用"""
        if self._timeout_deadline and time.time() * 1000 > self._timeout_deadline:
            raise TimeoutError("AI computation timeout")
    
    def get_action(self, request: ActionRequest) -> int:
        raise NotImplementedError
```

**复杂 Agent 实现示例**：

```python
class LLMAgent(BaseActionAgent):
    def get_action(self, request):
        # 检查点1：构建 prompt
        self._check_timeout()
        prompt = self.build_prompt(request)
        
        # 检查点2：调用 LLM
        self._check_timeout()
        response = self.llm.generate(prompt)
        
        # 检查点3：解析结果
        self._check_timeout()
        return self.parse(response)
```

**优点**：
- 优雅退出，资源正确释放
- 跨平台（Windows/Linux 都可用）
- 无需强制终止线程

**缺点**：
- 需要修改所有 Agent 实现
- 如果 Agent 某个步骤内部阻塞（如网络请求），仍无法中断

#### 方案B：使用信号量（仅 Unix）

```python
import signal

def handler(signum, frame):
    raise TimeoutError()

# 设置超时信号
signal.signal(signal.SIGALRM, handler)
signal.alarm(timeout_seconds)

try:
    action_id = agent.get_action(request)
finally:
    signal.alarm(0)  # 取消信号
```

**缺点**：
- ❌ Windows 不支持 `SIGALRM`
- ❌ 无法中断 C 扩展（numpy、PyTorch 等）
- ❌ 信号处理与多线程冲突

#### 方案C：使用第三方库（不稳定）

```python
# stopit 库（不推荐生产环境）
import stopit

with stopit.ThreadingTimeout(timeout_seconds) as to_ctx_mgr:
    action_id = agent.get_action(request)

if to_ctx_mgr.state == to_ctx_mgr.TIMED_OUT:
    raise TimeoutError()
```

**缺点**：
- ❌ 使用 `ctypes` 注入异常，不稳定
- ❌ 无法中断 C 扩展
- ❌ 非官方 API

### 4.3 推荐方案：GameController 统一控制（当前使用）

**不在 Agent 内部实现超时**，而是由 `GameController._wait_for_action_with_timeout` 统一控制：

```python
def _start_ai_computation_thread(self, agent, request):
    def ai_compute_and_enqueue():
        try:
            # 不传入超时参数，让 Agent 自己计算
            # 超时由 _wait_for_action_with_timeout 控制
            action_id = agent.get_action(request)
            
            # 确保最少 3 秒
            elapsed = time.time() - start
            if elapsed < 3.0:
                time.sleep(3.0 - elapsed)
            
            # 放入 queue
            if self.is_running:
                self._input_queue.put({...})
        except Exception:
            # 不放入 queue，让 _wait_for_action_with_timeout 自然超时
            pass
```

**为什么这样设计**：

1. **当前 Agent 都是 O(1)**：`RandomAgent`、`FastActionRandomAgent` 计算时间 < 1ms，不需要超时
2. **统一超时控制**：`_wait_for_action_with_timeout` 已经处理了主时间耗尽、读秒耗尽、超时回退，无需重复实现
3. **未来可扩展**：当添加复杂 Agent（如 LLM）时，再在 `BaseActionAgent` 中引入 `_check_timeout()` 机制

### 4.4 决策矩阵

| Agent 类型 | 计算时间 | 推荐方案 | 原因 |
|-----------|---------|---------|------|
| **随机策略**（当前） | < 1ms | 无需超时 | 计算太快，超时无意义 |
| **启发式策略** | 1-100ms | 无需超时 | 仍很快，Controller 统一控制足够 |
| **搜索算法**（MCTS） | 1-10s | 协作式检查点 | 需要 `_check_timeout()` |
| **LLM 推理** | 10-30s | 协作式检查点 + 多进程 | 需要 `_check_timeout()` + 进程隔离 |

### 4.5 结论

**当前阶段**：不传入超时参数，使用 `GameController._wait_for_action_with_timeout` 统一控制。

**未来复杂 Agent**：在 `BaseActionAgent` 中预留 `_check_timeout()` 接口，让复杂 Agent 在计算间隙自行检查。

---

## 5. API 变更清单

### 5.1 后端 API 修改

| 文件 | 位置 | 修改内容 |
|------|------|---------|
| `backend/api/routes.py` | `submit_action()` 函数 | 增加 `request_id` 参数接收和传递 |
| `backend/game/start_game.py` | `submit_action()` 方法 | 增加 `request_id` 参数，放入 queue 时携带 |
| `backend/game/start_game.py` | `_get_next_request_id()` | **新增** request_id 生成器 |
| `backend/game/start_game.py` | `_resolve_action_decision()` | 生成 request_id，清理 queue，启动 AI 线程 |
| `backend/game/start_game.py` | `_wait_for_action_with_timeout()` | 增加 `request_id` 和 `player_id` 验证 |
| `backend/game/start_game.py` | `_push_available_actions()` | 推送 request_id 到前端 |
| `backend/game/start_game.py` | `_start_ai_computation_thread()` | **新增** AI 后台线程（携带 request_id） |

### 5.2 后端 API 详细变更

**`backend/api/routes.py:240` - submit_action 路由**：

```python
@routes_bp.route('/api/game/action', methods=['POST'])
def submit_action():
    data = request.get_json()
    action_id = data.get('action_id')
    player_id = data.get('player_id')
    request_id = data.get('request_id')  # 新增：接收 request_id
    selection_source = data.get('selection_source', 'manual')
    selection_strategy = data.get('selection_strategy')
    selection_mode = data.get('selection_mode')
    
    controller = get_active_game_controller()
    
    # 传递 request_id
    success = controller.submit_action(
        action_id,
        player_id,
        request_id=request_id,  # 新增
        selection_source=selection_source,
        selection_strategy=selection_strategy,
        selection_mode=selection_mode
    )
    # ...
```

**`backend/game/start_game.py` - GameController.submit_action()**：

```python
def submit_action(self, action_id, player_id=None, request_id=None,
                  selection_source='manual', selection_strategy=None,
                  selection_mode=None):
    """提交行动（人类玩家通过 API 调用）"""
    # ... 验证逻辑 ...
    
    self._input_queue.put({
        'action_id': action_id,
        'request_id': request_id,      # 新增：携带 request_id
        'player_id': player_id,         # 新增：携带 player_id（用于验证）
        'selection_source': selection_source,
        'selection_strategy': selection_strategy,
        'selection_mode': selection_mode
    })
    return True
```

### 5.3 前端修改

| 文件 | 位置 | 修改内容 |
|------|------|---------|
| `frontend/src/stores/game.js` | `handleSSEMessage()` | 接收并保存 `request_id` |
| `frontend/src/stores/game.js` | `submitAction()` | 提交时携带 `request_id` |
| `frontend/src/views/GameView.vue` | `submitActionAndSync()` | 传递 `request_id` |

### 5.4 前端详细变更

**接收 request_id**：

```javascript
// frontend/src/stores/game.js
const currentRequestId = ref(null)

function handleSSEMessage(message) {
  if (message.type === 'actions') {
    currentRequestId.value = message.request_id  // 新增：保存 request_id
    // ... 显示行动列表
  }
}
```

**提交时携带 request_id**：

```javascript
// frontend/src/views/GameView.vue:5557
async function submitActionAndSync(actionId) {
  const response = await fetch(`${apiBaseUrl}/api/game/action`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      action_id: actionId,
      player_id: currentPlayerId.value,
      request_id: gameStore.currentRequestId,  // 新增：携带 request_id
      selection_source: 'manual',
      selection_mode: 'player_choice'
    })
  })
  
  if (!response.ok) {
    const error = await response.json()
    if (error.message === '本回合已结束') {
      showToast('本回合已超时，请等待下一回合')
    }
  }
}
```

---

## 6. 边界情况处理

### 5.1 AI 计算失败

**场景**：Agent.get_action() 抛出异常。

**处理**：
- 后台线程捕获异常，打印 traceback，**不放入 input_queue**
- 主线程在 `_wait_for_action_with_timeout` 中等待
- 主时间耗尽 → 读秒 → 读秒耗尽 → 触发 `_execute_timeout_action`
- 使用统一的 `timeout_strategy`（如 `random_fast_action`）

**结果**：AI 玩家超时，与人类玩家超时行为完全一致。

### 5.2 AI 在主时间耗尽前完成计算，但还没 sleep 满 3 秒

**场景**：Agent 计算耗时 0.5 秒，需要 sleep 2.5 秒，但主时间只剩 1 秒。

**处理**：
- 主线程进入 `_wait_for_action_with_timeout`
- 主时间 1 秒后耗尽，主线程进入读秒阶段
- AI 后台线程继续 sleep 到满 3 秒
- AI 线程放入 queue
- 主线程在读秒阶段从 queue 取出结果，正常提交

**结果**：行动在**读秒阶段**提交，时间扣减逻辑由 `_update_player_time_after_action` 统一处理。

### 5.3 AI 在读秒阶段也未能完成

**场景**：主时间耗尽，进入读秒，但 AI 后台线程因某种原因（如死锁）未能完成。

**处理**：
- 读秒耗尽 → `_wait_for_action_with_timeout` 调用 `_execute_timeout_action`
- 使用统一的 `timeout_strategy` 生成 action_id
- 主线程返回超时结果（request_id 已过期）
- AI 后台线程后续放入 queue 的数据：
  - request_id 已过期（当前 request_id 已递增）
  - 被 `_wait_for_action_with_timeout` 丢弃

**结果**：AI 玩家超时，与人类玩家超时行为完全一致。过期数据被 request_id 机制自动过滤。

### 5.4 游戏在 AI 计算期间被停止

**场景**：用户点击"停止游戏"，`_stop_event` 被设置。

**处理**：
- 主线程：`_wait_for_action_with_timeout` 检查到 `_stop_event.is_set()`，返回 `STOP_INPUT`
- AI 线程：`ai_compute_and_enqueue` 检查到 `_stop_event.is_set()`，不放入 queue

**结果**：双方优雅退出，无脏数据。

### 5.5 人类延迟提交（网络延迟）

**场景**：用户在倒计时最后一秒点击提交，网络延迟 2 秒到达后端。

**处理**：
- **情况A**：后端仍在读秒阶段
  - 数据到达时，主线程在读秒阶段等待
  - request_id 匹配 ✅，正常处理
- **情况B**：后端已超时（读秒也耗尽）
  - 主线程已返回超时结果
  - 新到达的数据：request_id 已过期
  - 被丢弃或返回错误给前端（"本回合已结束"）

**结果**：通过 request_id 机制，避免人类提交与超时策略的冲突。

---

## 7. 状态推送变化

### 7.1 重构前

- AI 玩家的回合：**不推送** `available_actions` 到前端
- 前端表现：看不到 AI 在思考，AI 行动后状态突然变化

### 7.2 重构后

- AI 玩家的回合：**推送** `available_actions` 到前端
- 前端表现：
  - 能看到 AI 的可用行动列表（虽然不需要人类操作）
  - 能看到计时器倒计时
  - 能看到 AI 的思考状态（计时器在走）
  - 如果配置显示 AI 策略，可以看到当前 AI 使用的策略名

### 7.3 前端适配说明

**需要修改前端代码**：人类玩家提交时需携带 `request_id`。

**修改内容**：
1. **接收 request_id**：从 SSE 推送的 `actions` 消息中提取 `request_id`
2. **提交时携带**：`submit_action` 时附带 `request_id`
3. **处理过期错误**：后端返回 "本回合已结束" 时提示用户

```javascript
// 前端 stores/game.js
const currentRequestId = ref(null)

// 接收 SSE 消息时
function handleSSEMessage(message) {
  if (message.type === 'actions') {
    currentRequestId.value = message.request_id  // 保存当前 request_id
    // ... 显示行动列表
  }
}

// 提交行动时
async function submitAction(actionId) {
  const response = await fetch(`${apiBaseUrl}/api/game/action`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      action_id: actionId,
      player_id: currentPlayerId.value,
      request_id: currentRequestId.value,  // 携带 request_id
      selection_source: 'manual',
      selection_mode: 'player_choice'
    })
  })
  
  if (!response.ok) {
    const error = await response.json()
    if (error.message === '本回合已结束') {
      alert('本回合已超时，请等待下一回合')
    }
  }
}
```

**AI 回合无需修改**：AI 回合前端正常显示计时器和行动列表即可。

---

## 8. 测试验证清单

### 8.1 基础功能

- [ ] AI 玩家能够正常自动行动
- [ ] AI 玩家行动间隔至少 3 秒
- [ ] AI 玩家行动间隔不超过（3 秒 + 主时间/读秒限制）

### 8.2 计时器一致性

- [ ] AI 玩家的主时间正常扣减
- [ ] AI 玩家主时间耗尽后进入读秒
- [ ] AI 玩家读秒时间显示正确
- [ ] AI 玩家超时后使用 `timeout_strategy` 回退

### 8.3 边界情况

- [ ] AI 计算失败时，超时后使用 `timeout_strategy`
- [ ] 游戏停止时，AI 线程优雅退出
- [ ] 连续多回合 AI 行动，queue 无残留数据
- [ ] AI 在主时间快耗尽时行动，时间扣减正确
- [ ] request_id 过期数据被正确丢弃（AI 超时场景）
- [ ] 人类延迟提交时 request_id 验证正确（匹配/过期）
- [ ] 快速连续回合 request_id 不混淆

### 8.4 前端表现

- [ ] AI 回合前端能看到可用行动列表
- [ ] AI 回合前端能看到计时器倒计时
- [ ] AI 回合计时器结束后状态正确更新

---

## 9. 版本历史

| 版本 | 日期 | 修改内容 |
|------|------|----------|
| 1.0 | 2026-04-23 | 初始版本 |

---

## 10. 附录

### 10.1 相关代码位置

| 文件 | 行号 | 说明 |
|------|------|------|
| `backend/game/start_game.py` | 240-275 | `_get_action_decision` |
| `backend/game/start_game.py` | 277-320 | `_resolve_action_decision`（待重构） |
| `backend/game/start_game.py` | 322-356 | `_wait_for_action_with_timeout` |
| `backend/game/start_game.py` | 357-379 | `_execute_timeout_action` |
| `backend/game/start_game.py` | 433-465 | `_update_player_time_after_action` |
| `backend/game/start_game.py` | 94-100 | `_clear_input_queue` |

### 10.2 时序图

#### 场景1：AI 在主时间内正常完成（最常见）

```
时间轴:   0s        1s        2s        3s        4s        5s
           │         │         │         │         │         │
主线程:   ├─_get_action_decision()──────────────────────────────┤
          │  ├─初始化计时器(45min)                               │
          │  ├─_resolve_action_decision()                        │
          │  │  ├─request_id = 1 🔑                              │
          │  │  ├─启动AI线程(request_id=1)────────┐              │
          │  │  ├─_push_available_actions(req_id=1)│              │
          │  │  └─返回(等待外部输入)              │              │
          │  │                                   │              │
          │  ├─_wait_for_action_with_timeout(req_id=1)            │
          │  │  ├─主时间阶段: queue.get(timeout=45min)            │
          │  │  │                                 │              │
          │  │  │  [AI线程放入queue]              │              │
          │  │  │     │ request_id=1 ✅           │              │
          │  │  │  <──┘                           │              │
          │  │  │                                 │              │
          │  │  └─返回 payload ✅                  │              │
          │  │                                   │              │
          │  ├─_update_player_time_after_action()                │
          │  │  time_spent ≈ 3s (主时间扣减3秒)                  │
          │  │                                                │
          │  └─返回(action_id, metadata)                        │
          │                                                   │
AI线程:   │                                   ├─agent.get_action()
          │                                   │  (耗时 0.5s)     │
          │                                   ├─sleep(2.5s)      │
          │                                   │                  │
          │                                   ├─_input_queue.put()
          │                                   │  request_id=1    │
          │                                   │  action_id=65    │
          │                                   └─结束             │
          │                                                    │
结果:     AI在3秒时完成决策，request_id=1 验证通过，主时间正常扣减3秒。
```

#### 场景2：AI 在主时间耗尽后完成

```
时间轴:   0s        1s        2s        3s        4s        5s        6s
           │         │         │         │         │         │         │
主线程:   ├─_get_action_decision()────────────────────────────────────────┤
          │  ├─初始化计时器(剩余主时间 2s)                                │
          │  ├─_resolve_action_decision()                                 │
          │  │  ├─request_id = 2 🔑                                      │
          │  │  ├─启动AI线程(request_id=2)──────────────┐               │
          │  │  └─_push_available_actions(req_id=2)       │               │
          │  │                                          │               │
          │  ├─_wait_for_action_with_timeout(req_id=2)   │               │
          │  │  ├─主时间阶段: queue.get(timeout=2s)       │               │
          │  │  │  [2秒后]                                │               │
          │  │  │  queue.Empty ❌                         │               │
          │  │  │                                         │               │
          │  │  ├─切换到读秒: byo_yomi=45s                 │               │
          │  │  │  _push_timer_state_update()             │               │
          │  │  │  推送前端: "进入读秒"                     │               │
          │  │  │                                         │               │
          │  │  ├─读秒阶段: queue.get(timeout=45s)        │               │
          │  │  │  [AI线程放入queue]                        │               │
          │  │  │     │ request_id=2 ✅                     │               │
          │  │  │  <──┘                                    │               │
          │  │  │                                          │               │
          │  │  └─返回 payload ✅                           │               │
          │  │                                           │               │
          │  ├─_update_player_time_after_action()                          │
          │  │  remaining_before=0 → 读秒阶段                            │
          │  │  检查是否超过 _action_deadline + _grace_period              │
          │  └─返回(action_id, metadata)                                   │
          │                                                              │
AI线程:   │                                          ├─agent.get_action()
          │                                          │  (耗时 4s)        │
          │                                          ├─sleep(0) [已超3s] │
          │                                          │                   │
          │                                          ├─_input_queue.put()│
          │                                          │  request_id=2 ✅  │
          │                                          │  action_id=65     │
          │                                          └─结束              │
          │                                                              │
结果:     AI在4秒时完成决策，request_id=2 验证通过，在读秒阶段提交成功。
         行动在读秒阶段提交，与人类读秒阶段提交行为一致。
```

#### 场景3：AI 读秒也超时（回退策略）

```
时间轴:   0s       10s       20s       30s       40s       48s       50s
           │         │         │         │         │         │         │
主线程:   ├─_get_action_decision()──────────────────────────────────────────┤
          │  ├─初始化计时器(剩余主时间 10s)                                 │
          │  ├─_resolve_action_decision()                                   │
          │  │  ├─request_id = 3 🔑                                        │
          │  │  └─启动AI线程(request_id=3)────────────────┐               │
          │  │                                             │               │
          │  ├─_wait_for_action_with_timeout(req_id=3)      │               │
          │  │  ├─主时间阶段: queue.get(timeout=10s)        │               │
          │  │  │  [10秒后]                                 │               │
          │  │  │  queue.Empty ❌                            │               │
          │  │  │                                           │               │
          │  │  ├─切换到读秒: byo_yomi=45s                   │               │
          │  │  │  _push_timer_state_update()               │               │
          │  │  │                                           │               │
          │  │  ├─读秒阶段: queue.get(timeout=45s)          │               │
          │  │  │  [38秒后，总计48秒]                        │               │
          │  │  │  queue.Empty ❌                            │               │
          │  │  │                                           │               │
          │  │  ├─触发超时回退                               │               │
          │  │  │  _execute_timeout_action()                │               │
          │  │  │  使用 timeout_strategy (如random_fast_action)│              │
          │  │  │  return {'action_id': ...,                 │               │
          │  │  │          'selection_source': 'system',     │               │
          │  │  │          'selection_strategy':             │               │
          │  │  │          'timeout_random_fast_action'}     │               │
          │  │  │                                           │               │
          │  │  └─返回超时结果                                │               │
          │  │                                             │               │
          │  ├─_update_player_time_after_action()                             │
          │  │  remaining_before=0 → 读秒阶段                               │
          │  │  action_end_time > deadline + grace? → 是，打印超时日志      │
          │  └─返回(action_id, metadata)                                    │
          │                                                               │
AI线程:   │                                             ├─agent.get_action()
          │                                             │  (耗时 50s，阻塞)  │
          │                                             │                  │
          │                                             ├─尝试放入queue      │
          │                                             │  request_id=3     │
          │                                             │  ⚠️ 已过期！      │
          │                                             │  主线程已超时     │
          │                                             └─结束             │
          │                                                               │
下一回合: ├─request_id = 4 🔑                                             │
          │  ├─_wait_for_action_with_timeout(req_id=4)                       │
          │  │  ├─从queue取出数据                                           │
          │  │  │  发现 request_id=3 ❌                                     │
          │  │  │  丢弃！继续等待 request_id=4                              │
          │  │  └─正常收到4的数据 ✅                                        │
结果:     AI在48秒时触发超时回退策略，与人类玩家超时行为完全一致。
         AI后台线程在50秒时放入queue(request_id=3)，但已过期。
         下一回合的request_id=4会丢弃这条过期数据。
```

### 10.3 与人类玩家的唯一差异

| 差异点 | 人类玩家 | AI 玩家 |
|--------|---------|---------|
| 输入来源 | 前端 HTTP POST | 后台 Agent 计算 + sleep(3s) |
| 输入时机 | 用户随时提交 | 最少 3 秒后自动提交 |
| 其余所有逻辑 | 一致 | 一致 |
