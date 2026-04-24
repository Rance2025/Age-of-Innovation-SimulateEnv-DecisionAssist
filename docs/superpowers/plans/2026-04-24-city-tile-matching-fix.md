# 城市板块匹配与显示修复计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修复城市板块匹配时机与前端城片显示位置问题，确保匹配逻辑正确且城片只显示在城市根节点上。

**Architecture:** 后端在每次状态更新时执行三步检测与匹配流程，前端仅根据根节点坐标渲染城片，不再为城市内每个建筑都显示。

**Tech Stack:** Vue 3 (frontend), Python 3.12 (backend)

---

## 文件结构

- `frontend/src/views/GameView.vue` — 修改 `getCityTileIdForCell` 函数，限制只在根节点显示城片
- `backend/game/utils/game_state_manager.py` — 修改 `_update_city_tile_matches` 方法，确保每次更新都执行完整的三步匹配流程

---

## Task 1: 修复前端城片显示逻辑

**Files:**
- Modify: `frontend/src/views/GameView.vue:5967-5992`

- [ ] **Step 1: 修改 `getCityTileIdForCell` 函数**

将当前逻辑（为城市内每个建筑都显示城片）改为只在该坐标本身是根节点且是城市时才显示。

```javascript
function getCityTileIdForCell(row, col) {
  const cell = ensureMapCell(row, col)
  if (!cell.controller || cell.controller < 0) return null

  const player = players.value[cell.controller]
  if (!player) return null

  const assignments = player.city_tile_assignments || {}
  const sac = player.settlements_and_cities || {}
  const posKey = `${row},${col}`

  // 只在该坐标是根节点且是城市时才显示城片
  if (sac[posKey]) {
    const [rootKey, isCity] = sac[posKey]
    // 必须是根节点（自己是自己的根）且是城市
    if (rootKey === posKey && isCity) {
      return assignments[posKey] || null
    }
  }

  return null
}
```

- [ ] **Step 2: 验证前端编译通过**

Run: `cd frontend && npm run build`
Expected: 编译成功，无错误。

---

## Task 2: 修复后端城市板块增量匹配逻辑

**Files:**
- Modify: `backend/game/utils/game_state_manager.py:1014-1104`

- [ ] **Step 1: 重写 `_update_city_tile_matches` 方法**

确保每次调用时都严格执行以下三步，无论前两步是否有新数据产生：

**Step 1 — 检测聚落根节点变城市：**
遍历所有玩家的 `settlements_and_cities`，对比 old_state 与 new_state：
- 若某坐标在 new_state 中是根节点（`value[0] == pos_key`）且是城市（`value[1] == True`），而在 old_state 中不满足此条件，则记录到 `_city_establishment_log[player_id]`，格式为 `(pos_key, current_ah_length)`。

**Step 2 — 检测城市板块持有者新增：**
遍历 `display_board.city_tile_owners`，对比 old_state 与 new_state：
- 若某城市板块的 `owner_list` 中新增了某玩家，则记录到 `_city_tile_acquisition_log[player_id]`，格式为 `(tile_id, current_ah_length)`。

**Step 3 — 执行匹配（无论前两步是否有新数据）：**
- 遍历所有在 `_city_establishment_log` 或 `_city_tile_acquisition_log` 中有记录的玩家。
- 对该玩家的 establishment_log 和 acquisition_log 进行双重循环匹配。
- 匹配条件：`acq_ah_length == est_ah_length + 1`（同一玩家，acquisition 的 action_history 长度恰好比 establishment 大 1）。
- 匹配成功：将 `city_tile_assignments[player_id][est_pos_key] = acq_tile_id`。
- 匹配失败：不做任何处理，保留 log 中的记录供后续再次尝试匹配（不删除）。

**Step 4 — 处理路径压缩导致的根节点迁移（保留原有逻辑）：**
- 遍历 `_city_tile_assignments` 中已有的匹配记录。
- 若某 `pos_key` 在 `settlements_and_cities` 中的根节点已变化，则将匹配记录迁移到新的根节点（前提是新的根节点仍是城市）。

完整实现代码：

```python
def _update_city_tile_matches(self, old_state: Dict, new_state: Dict, current_ah_length: int):
    """
    跨快照匹配 settlements_and_cities 新增城市与 city_tile 新增 owner。
    使用 action_history 长度作为"时间戳"，只有同一玩家内前后连续两动（ah_length 差值为1）才能匹配。
    
    三条记录：
    1. _city_establishment_log: {player_id: [(pos_key, action_history_length), ...]}
    2. _city_tile_acquisition_log: {player_id: [(tile_id, action_history_length), ...]}
    3. _city_tile_assignments: {player_id: {pos_key: city_tile_id}}
    """
    new_players = new_state.get('players', [])
    old_players = old_state.get('players', [])

    # Step 1: 检测 settlements_and_cities 新增的城市根节点
    for player_idx, player_data in enumerate(new_players):
        player_id = player_data.get('player_id', player_idx)
        old_sac = old_players[player_idx].get('settlements_and_cities', {}) if player_idx < len(old_players) else {}
        new_sac = player_data.get('settlements_and_cities', {})

        for pos_key, value in new_sac.items():
            is_new_establishment = False
            if pos_key not in old_sac:
                # 新增条目，检查是否是根节点且 is_city=True
                root_key, is_city = value[0], value[1]
                if root_key == pos_key and is_city:
                    is_new_establishment = True
            elif old_sac.get(pos_key) != value:
                # 已有条目变更，检查是否变为城市
                old_root, old_is_city = old_sac[pos_key][0], old_sac[pos_key][1]
                new_root, new_is_city = value[0], value[1]
                if not old_is_city and new_is_city and new_root == pos_key:
                    is_new_establishment = True
            
            if is_new_establishment:
                self._city_establishment_log.setdefault(player_id, []).append(
                    (pos_key, current_ah_length)
                )

    # Step 2: 检测 city_tile_owners 新增的 owner
    old_owners = old_state.get('display_board', {}).get('city_tile_owners', {})
    new_owners = new_state.get('display_board', {}).get('city_tile_owners', {})

    for tile_id_str, new_owner_list in new_owners.items():
        tile_id = int(tile_id_str)
        old_owner_list = old_owners.get(tile_id_str, [])
        added_players = [p for p in new_owner_list if p not in old_owner_list]

        for player_id in added_players:
            self._city_tile_acquisition_log.setdefault(player_id, []).append(
                (tile_id, current_ah_length)
            )

    # Step 3: 匹配检查（无论前面两步是否有新数据，每次都执行）
    all_player_ids = set(self._city_establishment_log.keys()) | set(self._city_tile_acquisition_log.keys())
    for player_id in all_player_ids:
        establishment_log = self._city_establishment_log.get(player_id, [])
        acquisition_log = self._city_tile_acquisition_log.get(player_id, [])
        
        for est_pos_key, est_ah_length in establishment_log:
            # 查找同一玩家中 ah_length 恰好为 est_ah_length + 1 的板块获取记录
            for acq_tile_id, acq_ah_length in acquisition_log:
                if acq_ah_length == est_ah_length + 1:
                    # 匹配成功，加入 assignments
                    self._city_tile_assignments.setdefault(player_id, {})[est_pos_key] = acq_tile_id
                    break

    # Step 4: 处理根节点路径压缩导致的匹配迁移
    for player_id, assignments in list(self._city_tile_assignments.items()):
        player_data = None
        for p in new_players:
            if p.get('player_id') == player_id:
                player_data = p
                break

        sac = player_data.get('settlements_and_cities', {}) if player_data else {}
        new_assignments = {}
        for pos_key, tile_id in assignments.items():
            if pos_key in sac:
                root_key = sac[pos_key][0]
                if sac.get(root_key, [None, False])[1]:
                    # 根节点仍是城市，更新到当前根节点
                    new_assignments[root_key] = tile_id
                else:
                    # 根节点不再是城市（异常情况），保留原记录
                    new_assignments[pos_key] = tile_id
            else:
                # 该坐标不在 settlements_and_cities 中，保留原记录
                new_assignments[pos_key] = tile_id
        self._city_tile_assignments[player_id] = new_assignments
```

- [ ] **Step 2: 验证 `_update_city_tile_matches` 的调用时机**

确认 `update_state` 方法（line ~175）中在每次状态更新时都调用了 `_update_city_tile_matches`，并且在调用后重新计算了 diff：

```python
# Step 2.5: 跨快照匹配城市板块
if self._last_pushed_state is not None:
    new_state_dict = self._state_to_dict(new_state)
    current_ah_length = len(new_state_dict.get('action_history', []))
    self._update_city_tile_matches(self._last_pushed_state, new_state_dict, current_ah_length)
    # 重新计算增量，因为匹配结果可能影响 city_tile_assignments
    diffs = self._calculate_optimized_diff(self._last_pushed_state, new_state)
```

此逻辑已存在，无需修改。

- [ ] **Step 3: 运行后端验证**

Run: `cd backend && python -c "from game.utils.game_state_manager import GameStateManager; print('OK')"`
Expected: 无异常输出。

---

## 任务总结与验证清单

- [ ] 前端 `getCityTileIdForCell` 只返回根节点的城片 ID
- [ ] 后端 `_update_city_tile_matches` 每次更新都执行完整三步
- [ ] 匹配规则：`acq_ah_length == est_ah_length + 1`，同一玩家
- [ ] 未匹配记录保留在 log 中不删除
- [ ] `city_tile_assignments` 正确包含在状态 diff 中推送到前端
- [ ] 前端编译通过
- [ ] 后端导入无异常

---

## Self-Review

**1. Spec coverage:**
- 前端只在根节点显示城片 ✅ Task 1
- 后端每次更新都执行三步检测与匹配 ✅ Task 2
- 匹配规则为 ah_length 差值 1 ✅ Task 2 Step 3
- 未匹配记录不删除 ✅ Task 2 Step 3

**2. Placeholder scan:**
- 无 TBD/TODO/"implement later" ✅
- 所有代码块包含完整实现 ✅

**3. Type consistency:**
- `getCityTileIdForCell` 返回类型一致（`number | null`）✅
- `_update_city_tile_matches` 中 log 和 assignments 的数据结构一致 ✅
