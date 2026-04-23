# 游戏界面引入AI Agent功能文档

## 文档信息

- **创建日期**: 2026-04-23
- **版本**: 1.0
- **状态**: 设计完成，待实施
- **目标**: 在游戏界面完整支持AI Agent玩家，确保AI/人类玩家体验一致且UI正确禁用

---

## 1. 功能概述

### 1.1 目标

实现完整的AI Agent支持，包括：
1. 游戏设置阶段配置AI玩家及策略
2. 游戏运行时AI自动决策
3. 前端UI根据当前玩家类型（AI/人类）动态调整
4. 控制中台在AI回合禁用人工操作
5. 完整的超时和异常处理机制

### 1.2 核心特性

| 特性 | 描述 |
|------|------|
| **自动决策** | AI玩家无需人工干预，自动执行行动 |
| **策略选择** | 支持多种AI策略（随机、快速行动优化等） |
| **统一链路** | AI和人类走相同的超时、计时、回退逻辑 |
| **UI适配** | AI回合自动禁用点击、按钮等人工操作 |
| **可追溯** | 行动历史记录AI使用的策略 |

---

## 2. 架构设计

### 2.1 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                        前端 (Vue.js)                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │   SetupView  │  │   GameView   │  │  Control Center  │  │
│  │  (配置AI玩家) │  │  (AI回合禁用) │  │  (AI禁用按钮)   │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP + SSE
┌────────────────────────▼────────────────────────────────────┐
│                      后端 (Flask)                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │    routes    │  │  GameController│  │  AI Agent线程   │  │
│  │   (API接口)  │  │  (统一控制)   │  │  (后台计算)    │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                   游戏引擎 (GameEngine)                     │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 数据流

```
1. 游戏设置
   SetupView ──POST /api/game/start──► routes.py
                                       └── _run_game()
                                           └── GameController.start()
                                               └── 注册AI Agent

2. AI回合运行
   GameController._game_loop()
   ├── yield ActionRequest
   ├── _get_action_decision()
   │   ├── _resolve_action_decision()
   │   │   ├── request_id = _get_next_request_id()
   │   │   ├── _start_ai_computation_thread() ──► AI线程启动
   │   │   └── _push_available_actions() ──► 前端（携带request_id）
   │   └── _wait_for_action_with_timeout()
   │       ├── queue.get() ◄── AI线程put结果
   │       └── 返回action_id
   └── game.send(action_id)

3. 前端响应
   SSE: actions消息 ──► GameView
   ├── 显示行动列表
   ├── 检测is_ai_player ──► 禁用点击
   └── 显示"AI思考中"状态
```

---

## 3. 后端实现

### 3.1 GameController修改

#### 3.1.1 新增成员变量

```python
class GameController:
    def __init__(self, game_id: str, num_players: int = 3, timer_config: dict = None):
        # ... 原有代码 ...
        
        # AI Agent注册表 {player_id: Agent}
        self._agents: Dict[int, Any] = {}
        
        # 当前AI计算线程列表
        self._active_ai_threads: List[threading.Thread] = []
        
        # request_id计数器
        self._current_request_id: int = 0
```

#### 3.1.2 AI Agent注册

```python
def register_agent(self, player_id: int, agent: Any) -> bool:
    """为指定玩家注册AI Agent"""
    if 0 <= player_id < self.num_players:
        self._agents[player_id] = agent
        return True
    return False

def is_ai_player(self, player_id: int) -> bool:
    """判断指定玩家是否为AI"""
    return player_id in self._agents
```

#### 3.1.3 request_id生成

```python
def _get_next_request_id(self) -> int:
    """生成下一个请求ID（单调递增）"""
    self._current_request_id += 1
    return self._current_request_id
```

#### 3.1.4 AI计算线程启动

```python
def _start_ai_computation_thread(self, request: ActionRequest, player_id: int, request_id: int):
    """启动AI计算后台线程"""
    agent = self._agents[player_id]
    
    def ai_compute_and_enqueue():
        """AI计算并放入队列（携带request_id）"""
        try:
            # 检查点1：计算开始前
            if self._stop_event.is_set():
                return
            
            start_time = time.time()
            action_id = agent.get_action(request)
            elapsed = time.time() - start_time
            
            # 检查点2：计算完成后
            if self._stop_event.is_set():
                return
            
            # 确保最少3秒（分段sleep，可响应_stop_event）
            min_delay = 3.0
            if elapsed < min_delay:
                remaining = min_delay - elapsed
                while remaining > 0 and not self._stop_event.is_set():
                    sleep_chunk = min(0.1, remaining)
                    time.sleep(sleep_chunk)
                    remaining -= sleep_chunk
            
            # 检查点3：放入queue前
            if self._stop_event.is_set() or not self.is_running:
                return
            
            strategy_name = getattr(agent, 'strategy_name', None) or \
                           getattr(agent, 'name', None) or \
                           agent.__class__.__name__
            
            # 放入queue（携带request_id）
            self._input_queue.put({
                'action_id': action_id,
                'request_id': request_id,
                'selection_source': 'system',
                'selection_strategy': strategy_name
            })
        except Exception:
            import traceback
            traceback.print_exc()
        finally:
            # 从活跃列表移除
            current_thread = threading.current_thread()
            if current_thread in self._active_ai_threads:
                self._active_ai_threads.remove(current_thread)
    
    ai_thread = threading.Thread(target=ai_compute_and_enqueue, daemon=True)
    self._active_ai_threads.append(ai_thread)
    ai_thread.start()
```

#### 3.1.5 统一决策解析

```python
def _resolve_action_decision(self, request: ActionRequest, player_id: int):
    """解析行动决策（AI/人类统一入口）"""
    # 生成本回合唯一request_id
    request_id = self._get_next_request_id()
    
    # 清理上一回合残留数据
    self._clear_input_queue()
    
    # 如果是AI玩家，启动计算线程
    if self.is_ai_player(player_id):
        self._start_ai_computation_thread(request, player_id, request_id)
    
    # 推送可用行动（携带request_id）
    self._push_available_actions(request, request_id)
    
    # 统一等待（验证request_id）
    payload = self._wait_for_action_with_timeout(player_id, request_id)
    
    # 解析结果
    if isinstance(payload, dict) and payload.get('__stop__') is True:
        raise GameStopped()
    
    if isinstance(payload, dict):
        action_id = int(payload.get('action_id'))
        selection_source = 'system' if payload.get('selection_source') == 'system' else 'manual'
        selection_strategy = payload.get('selection_strategy')
        selection_mode = payload.get('selection_mode')
        return action_id, {
            'selection_source': selection_source,
            'selection_strategy': selection_strategy,
            'selection_mode': selection_mode
        }
    
    return int(payload), {'selection_source': 'manual', 'selection_strategy': None}
```

#### 3.1.6 带验证的等待

```python
def _wait_for_action_with_timeout(self, player_id: int, request_id: int):
    """等待玩家行动，验证request_id"""
    if self._stop_event.is_set():
        return dict(STOP_INPUT)
    
    remaining = self._player_remaining_times[player_id]
    
    # 主时间阶段
    if remaining > 0:
        deadline = time.time() + remaining / 1000.0
        while time.time() < deadline:
            try:
                timeout = min(0.1, deadline - time.time())
                if timeout <= 0:
                    break
                
                payload = self._input_queue.get(timeout=timeout)
                
                # 验证request_id
                if isinstance(payload, dict) and 'request_id' in payload:
                    if payload['request_id'] != request_id:
                        print(f"[Queue] Discarded stale request_id: {payload['request_id']}")
                        continue
                
                if isinstance(payload, dict) and payload.get('__stop__') is True:
                    return dict(STOP_INPUT)
                if self._stop_event.is_set():
                    return dict(STOP_INPUT)
                return payload
                
            except queue.Empty:
                continue
        
        # 切换到读秒
        if self._stop_event.is_set():
            return dict(STOP_INPUT)
        now = int(time.time() * 1000)
        self._player_remaining_times[player_id] = 0
        self._action_deadline = now + self._byo_yomi_time
        self._push_timer_state_update()
    
    # 读秒阶段（同样验证request_id）
    # ... 类似逻辑 ...
    try:
        payload = self._input_queue.get(timeout=self._byo_yomi_time / 1000.0)
        if isinstance(payload, dict) and 'request_id' in payload:
            if payload['request_id'] != request_id:
                return self._execute_timeout_action(player_id)
        return payload
    except queue.Empty:
        if self._stop_event.is_set():
            return dict(STOP_INPUT)
        return self._execute_timeout_action(player_id)
```

#### 3.1.7 推送可用行动（携带request_id）

```python
def _push_available_actions(self, request: ActionRequest, request_id: int):
    """推送可选行动到前端（携带request_id）"""
    if not self._message_callback:
        return
    
    try:
        actions = [
            {'id': k, 'description': v}
            for k, v in request.available_actions.items()
        ]
        
        self._message_callback({
            'type': 'actions',
            'player_id': request.player_id,
            'request_id': request_id,
            'is_ai_player': self.is_ai_player(request.player_id),  # 关键：标记是否为AI
            'data': {
                'actions': actions,
                'count': len(actions),
                'current_player': request.player_id
            }
        })
    except Exception:
        pass
```

#### 3.1.8 增强的stop方法

```python
def stop(self):
    """停止游戏（增强版）"""
    self.is_running = False
    self._stop_event.set()
    self._clear_input_queue()
    self._input_queue.put(dict(STOP_INPUT))
    
    # 等待主游戏线程
    if self._game_thread and self._game_thread.is_alive():
        self._game_thread.join(timeout=2.0)
    
    # 等待AI线程（最多3秒）
    self._wait_for_ai_threads(timeout=3.0)
    
    # 最终清理
    self._active_ai_threads.clear()
    self._clear_input_queue()
    self.current_request = None
    self._game_thread = None
    self._game_engine = None

def _wait_for_ai_threads(self, timeout=3.0):
    """等待AI线程退出"""
    start = time.time()
    while self._active_ai_threads and time.time() - start < timeout:
        time.sleep(0.1)
    
    if self._active_ai_threads:
        print(f"[Warning] {len(self._active_ai_threads)} AI threads still running")
        self._clear_input_queue()
```

---

## 4. 前端实现

### 4.1 游戏Store修改

```javascript
// stores/game.js
export const useGameStore = defineStore('game', () => {
  // ... 原有状态 ...
  
  // 新增：当前玩家是否为AI
  const currentPlayerIsAi = ref(false)
  
  // 新增：当前request_id
  const currentRequestId = ref(null)
  
  // 更新游戏状态时检测AI玩家
  function updateGameState(state) {
    // ... 原有逻辑 ...
    
    // 检测当前玩家是否为AI
    const currentPlayerId = state.meta?.current_player_id
    if (currentPlayerId !== undefined) {
      currentPlayerIsAi.value = state.players?.[currentPlayerId]?.type === 'ai'
    }
  }
  
  // 处理SSE消息
  function handleSSEMessage(message) {
    if (message.type === 'actions') {
      currentRequestId.value = message.request_id
      currentPlayerIsAi.value = message.is_ai_player  // 后端推送的标记
      // ... 其他处理 ...
    }
  }
  
  return {
    // ... 原有导出 ...
    currentPlayerIsAi,
    currentRequestId,
    updateGameState,
    handleSSEMessage
  }
})
```

### 4.2 GameView.vue - 禁用点击

```vue
<template>
  <!-- 可选行动列表 -->
  <div class="available-actions" 
       :class="{ 'ai-turn': gameStore.currentPlayerIsAi }">
    <button 
      v-for="action in availableActions" 
      :key="action.id"
      @click="handleActionClick(action.id)"
      :disabled="gameStore.currentPlayerIsAi"  <!-- AI回合禁用 -->
      class="action-button"
    >
      {{ action.description }}
    </button>
    
    <!-- AI思考中提示 -->
    <div v-if="gameStore.currentPlayerIsAi" class="ai-thinking">
      <i class="fas fa-robot"></i>
      <span>AI思考中...</span>
      <span class="ai-strategy">{{ currentAiStrategy }}</span>
    </div>
  </div>
</template>

<script setup>
import { useGameStore } from '../stores/game'

const gameStore = useGameStore()

function handleActionClick(actionId) {
  // 额外防护：AI回合不处理点击
  if (gameStore.currentPlayerIsAi) {
    console.warn('AI回合，禁止人工操作')
    return
  }
  
  submitAction(actionId)
}
</script>

<style scoped>
.available-actions.ai-turn {
  opacity: 0.7;
  pointer-events: none;  /* 额外防护 */
}

.ai-thinking {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  background: rgba(99, 102, 241, 0.1);
  border-radius: 8px;
  color: var(--accent);
}
</style>
```

### 4.3 控制中台禁用按钮

```vue
<template>
  <div class="control-center">
    <!-- 策略推荐按钮 - AI回合禁用 -->
    <button 
      class="strategy-btn"
      @click="openStrategyModal"
      :disabled="gameStore.currentPlayerIsAi"
    >
      <i class="fas fa-chess-knight"></i>
      策略推荐
    </button>
    
    <!-- 接受推荐按钮 - AI回合禁用 -->
    <button 
      class="accept-btn"
      @click="acceptRecommendation"
      :disabled="!hasRecommendation || gameStore.currentPlayerIsAi"
    >
      接受推荐
    </button>
    
    <!-- 撤销按钮 - AI回合禁用 -->
    <button 
      class="undo-btn"
      @click="undoAction"
      :disabled="!canUndo || gameStore.currentPlayerIsAi"
    >
      撤销
    </button>
    
    <!-- 其他人工操作按钮同理 -->
  </div>
</template>

<script setup>
import { useGameStore } from '../stores/game'

const gameStore = useGameStore()

// 所有操作函数都要检查
function openStrategyModal() {
  if (gameStore.currentPlayerIsAi) {
    showToast('AI回合，无法使用策略推荐')
    return
  }
  // ... 原有逻辑 ...
}

function acceptRecommendation() {
  if (gameStore.currentPlayerIsAi) {
    showToast('AI回合，无法手动操作')
    return
  }
  // ... 原有逻辑 ...
}
</script>
```

### 4.4 提交行动携带request_id

```javascript
// services/gameApi.js
async function submitAction(actionId, playerId) {
  const gameStore = useGameStore()
  
  const response = await fetch(`${API_BASE}/api/game/action`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      action_id: actionId,
      player_id: playerId,
      request_id: gameStore.currentRequestId,  // 关键：携带request_id
      selection_source: 'manual',
      selection_mode: 'player_choice'
    })
  })
  
  if (!response.ok) {
    const error = await response.json()
    if (error.message === '本回合已结束') {
      showToast('本回合已超时，请等待下一回合')
    }
    throw new Error(error.message)
  }
  
  return response.json()
}
```

---

## 5. API变更清单

### 5.1 后端API修改

| 文件 | 位置 | 修改内容 |
|------|------|---------|
| `backend/game/start_game.py` | `GameController.__init__` | 新增 `_agents`, `_active_ai_threads`, `_current_request_id` |
| `backend/game/start_game.py` | 新增方法 | `register_agent()`, `is_ai_player()`, `_get_next_request_id()` |
| `backend/game/start_game.py` | 新增方法 | `_start_ai_computation_thread()` |
| `backend/game/start_game.py` | 修改方法 | `_resolve_action_decision()` - 统一入口 |
| `backend/game/start_game.py` | 修改方法 | `_wait_for_action_with_timeout()` - 验证request_id |
| `backend/game/start_game.py` | 修改方法 | `_push_available_actions()` - 携带request_id和is_ai标记 |
| `backend/game/start_game.py` | 修改方法 | `stop()` - 等待AI线程 |
| `backend/api/routes.py` | `submit_action()` | 接收并传递request_id |

### 5.2 前端修改

| 文件 | 修改内容 |
|------|---------|
| `frontend/src/stores/game.js` | 新增 `currentPlayerIsAi`, `currentRequestId` 状态 |
| `frontend/src/stores/game.js` | 修改 `handleSSEMessage()` - 处理is_ai标记 |
| `frontend/src/views/GameView.vue` | 可选行动列表添加 `disabled` 和 `ai-turn` 样式 |
| `frontend/src/views/GameView.vue` | 添加AI思考中提示UI |
| `frontend/src/views/GameView.vue` | 所有操作函数检查 `currentPlayerIsAi` |
| `frontend/src/components/ControlCenter.vue` | 所有按钮添加 `disabled="currentPlayerIsAi"` |
| `frontend/src/services/gameApi.js` | `submitAction` 携带 `request_id` |

---

## 6. 边界情况处理

### 6.1 AI计算超时

**场景**：AI计算超过主时间+读秒时间

**处理**：
1. 主线程触发 `_execute_timeout_action()`
2. 使用统一的 `timeout_strategy` 回退
3. AI线程后续放入的数据因 `request_id` 过期被丢弃

### 6.2 游戏停止时AI还在运行

**场景**：用户点击"结束游戏"时AI正在计算

**处理**：
1. `stop()` 设置 `_stop_event`
2. AI线程在检查点（计算后/sleep中/放入前）检测到退出
3. `stop()` 等待最多3秒，超时后强制清理queue
4. 游戏优雅退出

### 6.3 快速连续回合

**场景**：AI决策很快，多回合连续进行

**处理**：
1. 每回合生成新的 `request_id`
2. `_clear_input_queue()` 清理上一回合残留
3. `request_id` 验证过滤过期数据

### 6.4 人类延迟提交

**场景**：用户在倒计时最后一秒点击，网络延迟到达后端

**处理**：
1. 后端在读秒阶段：验证 `request_id` 通过，正常处理
2. 后端已超时：返回错误"本回合已结束"

---

## 7. 测试验证清单

### 7.1 基础功能

- [ ] AI玩家能够正常自动行动
- [ ] AI玩家行动间隔至少3秒
- [ ] AI玩家超时后使用`timeout_strategy`回退
- [ ] 人类玩家正常操作不受影响

### 7.2 UI适配

- [ ] AI回合可选行动列表禁用点击
- [ ] AI回合显示"AI思考中"提示
- [ ] 控制中台按钮在AI回合禁用
- [ ] 人类回合所有功能正常启用

### 7.3 健壮性

- [ ] 游戏停止时AI线程优雅退出
- [ ] request_id过期数据被正确丢弃
- [ ] 快速连续回合request_id不混淆
- [ ] 网络延迟提交正确处理

### 7.4 性能

- [ ] AI计算不阻塞主线程
- [ ] 前端UI响应流畅
- [ ] 内存无泄漏（线程正确清理）

---

## 8. 实施建议

### 8.1 实施顺序

1. **Phase 1**: 后端基础实现
   - GameController修改
   - AI线程管理
   - request_id机制

2. **Phase 2**: 前端基础适配
   - Store状态管理
   - UI禁用逻辑

3. **Phase 3**: 集成测试
   - AI/人类混合对局
   - 边界情况测试

4. **Phase 4**: 优化
   - 性能调优
   - UI细节打磨

### 8.2 风险点

| 风险 | 缓解措施 |
|------|---------|
| AI线程未正确清理 | 使用_active_ai_threads列表监控，stop()超时清理 |
| request_id冲突 | 单调递增，每回合递增，不会冲突 |
| UI禁用不彻底 | 多处防护：disabled属性、pointer-events、函数内检查 |

---

## 9. 版本历史

| 版本 | 日期 | 修改内容 |
|------|------|---------|
| 1.0 | 2026-04-23 | 初始版本，完整AI Agent集成方案 |

---

## 10. 附录

### 10.1 时序图：AI正常决策

```
时间轴:  T0        T1        T2        T3
         │         │         │         │
后端:    ├─_resolve_action_decision()
         │  ├─request_id = 1
         │  ├─启动AI线程(request_id=1)
         │  ├─推送actions(is_ai=true, request_id=1)──┐
         │  └─_wait_for_action_with_timeout()        │
         │     ├─queue.get() ◄──┐                     │
         │     │              │                     │
前端:    │     │              └───► 接收actions    │
         │     │                   显示"AI思考中"   │
         │     │                   禁用点击         │
         │     │                                  │
AI线程:  │     │     ├─agent.get_action()          │
         │     │     ├─sleep(3s)                   │
         │     │     ├─queue.put(request_id=1)────┘
         │     │                                  │
后端:    │     └─返回action_id                    │
         │        解析metadata                     │
         │        game.send(action_id)             │
         │                                         │
前端:    ◄────────── 状态更新                      │
                   显示AI行动                      │
                   切换到下一玩家                   │
```

### 10.2 时序图：游戏停止时

```
时间轴:  T0        T0.1s     T0.2s     ...       T3s
         │         │         │         │         │
用户:    ├─点击"结束游戏"
         │
前端:    ├─POST /api/game/stop
         │
后端:    ├─controller.stop()
         │  ├─is_running = false
         │  ├─_stop_event.set() ⭐
         │  ├─queue.put(STOP_INPUT) ⭐
         │  ├─等待主线程(2s) ◄── 收到STOP_INPUT，退出
         │  ├─等待AI线程(3s)
         │  │   T0.1s: AI检查_stop_event → 退出sleep
         │  │   T0.1s: AI跳过put queue
         │  │   T0.1s: AI从活跃列表移除
         │  └─清理完成
         │
结果:    游戏在0.1s内优雅停止
```

---

**文档完成**。这是完整的AI Agent集成方案，包含了所有技术细节、代码示例和边界处理。
