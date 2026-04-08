# 前后端数据接口对齐文档

## 文档信息
- **创建日期**: 2026-04-07
- **版本**: 2.0
- **状态**: 基于实际代码实现

---

## 1. 架构概述

### 1.1 数据流向

```
后端 GameEngine (yield ActionRequest)
    │
    ▼
GameController._get_action_id()
    │
    ├── 有 Agent ──> 直接获取 action_id ──> 打印 Agent log
    │
    └── 无 Agent ──> _push_available_actions() ──> MessageQueueManager
                                                    │
                                                    ▼
                                            SSE 推送至前端
                                                    │
                                                    ▼
                                            前端显示可选行动
                                                    │
                                                    ▼
                                            用户选择后 POST /input
                                                    │
                                                    ▼
                                            GameController.submit_action()
                                                    │
                                                    ▼
                                            game.send(action_id)
```

### 1.2 核心文件位置

| 组件 | 文件路径 |
|------|----------|
| 前端主视图 | `frontend/src/views/GameView.vue` |
| 前端状态Store | `frontend/src/stores/gameState.js` |
| 后端游戏控制器 | `backend/game/start_game.py` |
| 后端状态管理器 | `backend/game/utils/game_state_manager.py` |
| 后端数据类型 | `backend/game/utils/frontend_state_types.py` |
| 后端ActionRequest | `backend/game/aoi_game/utils/action_request.py` |
| 后端游戏状态 | `backend/game/aoi_game/game_state.py` |

---

## 2. 数据接口对齐表

### 2.1 游戏元信息 (GameMeta)

| 状态 | 后端 yield 数据 | 前端接收数据 | 前端可视化行为 |
|------|----------------|-------------|---------------|
| **玩家数量** |
| [✅] | `num_players: 3` | `num_players: 3` | 显示3个玩家卡片框 |
| [✅] | `num_players: 4` | `num_players: 4` | 显示4个玩家卡片框 |
| [✅] | `num_players: 5` | `num_players: 5` | 显示5个玩家卡片框 |
| **回合信息** |
| [ ] | `round: 0` | `round: 0` | 右上角"对局状态"显示"初始选择阶段" |
| [ ] | `round: 1-6` | `round: 1-6` | 右上角显示"第 N 回合"，对应轮次计分板块高亮 |
| **当前玩家** |
| [ ] | `current_player_id: 0` | `current_player_id: 0` | 玩家1卡片边框高亮，可选行动列表显示玩家1的行动 |
| [ ] | `current_player_id: 1` | `current_player_id: 1` | 玩家2卡片边框高亮，可选行动列表显示玩家2的行动 |
| [ ] | `current_player_id: 2` | `current_player_id: 2` | 玩家3卡片边框高亮，可选行动列表显示玩家3的行动 |
| [ ] | `current_player_id: 3` | `current_player_id: 3` | 玩家4卡片边框高亮，可选行动列表显示玩家4的行动 |
| [ ] | `current_player_id: 4` | `current_player_id: 4` | 玩家5卡片边框高亮，可选行动列表显示玩家5的行动 |
| **行动类型** |
| [ ] | `action_type: "normal"` | `action_type: "normal"` | 可选行动区域显示主行动选项 |
| [ ] | `action_type: "special"` | `action_type: "special"` | 可选行动区域显示特殊行动选项 |
| [ ] | `action_type: "immediate"` | `action_type: "immediate"` | 可选行动区域显示立即行动选项 |
| **游戏结束** |
| [ ] | `is_game_over: true` | `is_game_over: true` | 显示游戏结束画面，展示最终得分 |

### 2.2 游戏设置 (GameSetup)

**说明：** `selected` 表示在游戏开始前的初始设置阶段，从所有可用板块中筛选出本局游戏公共可用的板块。在后续游戏进行中，玩家从这些公共板块中选择属于自己的板块。

| 状态 | 后端 yield 数据 | 前端接收数据 | 前端可视化行为 |
|------|----------------|-------------|---------------|
| **规划卡设置**（固定6个，与人数无关） |
| [ ] | `selected_planning_cards: [1,2,3,4,5,6]` | `selected_planning_cards: [1,2,3,4,5,6]` | 显示6个规划卡选项供玩家选择（从7个中排除1个） |
| **派系设置**（num_players + 1） |
| [ ] | `selected_factions: [1,2,3,4]` (3人局) | `selected_factions: [1,2,3,4]` | 显示4个派系选项供玩家选择 |
| [ ] | `selected_factions: [1,2,3,4,5]` (4人局) | `selected_factions: [1,2,3,4,5]` | 显示5个派系选项供玩家选择 |
| [ ] | `selected_factions: [1,2,3,4,5,6]` (5人局) | `selected_factions: [1,2,3,4,5,6]` | 显示6个派系选项供玩家选择 |
| **宫殿瓦片设置**（num_players + 1） |
| [ ] | `selected_palace_tiles: [1,2,3,4]` (3人局) | `selected_palace_tiles: [1,2,3,4]` | 显示4个宫殿瓦片选项 |
| [ ] | `selected_palace_tiles: [1,2,3,4,5]` (4人局) | `selected_palace_tiles: [1,2,3,4,5]` | 显示5个宫殿瓦片选项 |
| [ ] | `selected_palace_tiles: [1,2,3,4,5,6]` (5人局) | `selected_palace_tiles: [1,2,3,4,5,6]` | 显示6个宫殿瓦片选项 |
| **回合助推器设置**（num_players + 3） |
| [✅] | `selected_round_boosters: [1,2,3,4,5,6]` (3人局) | `selected_round_boosters: [1,2,3,4,5,6]` | 回合信息区显示6个助推板块 |
| [✅] | `selected_round_boosters: [1,2,3,4,5,6,7]` (4人局) | `selected_round_boosters: [1,2,3,4,5,6,7]` | 回合信息区显示7个助推板块 |
| [✅] | `selected_round_boosters: [1,2,3,4,5,6,7,8]` (5人局) | `selected_round_boosters: [1,2,3,4,5,6,7,8]` | 回合信息区显示8个助推板块 |
| **轮次计分设置**（固定6个） |
| [✅] | `round_scoring_order: [1,2,3,4,5,6]` | `round_scoring_order: [1,2,3,4,5,6]` | 6个轮次计分板块按顺序显示图片 |
| **最终计分设置**（固定1个） |
| [✅] | `final_scoring: 1` (范围1-4) | `final_scoring: 13` (映射+12) | 第6回合板块上叠加显示 `/images/scoring/13.png` |
| [✅] | `final_scoring: 2` | `final_scoring: 14` | 第6回合板块上叠加显示 `/images/scoring/14.png` |
| [✅] | `final_scoring: 3` | `final_scoring: 15` | 第6回合板块上叠加显示 `/images/scoring/15.png` |
| [✅] | `final_scoring: 4` | `final_scoring: 16` | 第6回合板块上叠加显示 `/images/scoring/16.png` |
| **能力瓦片设置**（固定12个，与人数无关） |
| [ ] | `ability_tiles_order: [1,2,3,4,5,6,7,8,9,10,11,12]` | `ability_tiles_order: [1,2,3,4,5,6,7,8,9,10,11,12]` | 能力瓦片区按顺序显示12个能力瓦片 |
| **科技瓦片设置**（num_players * 2 + 2） |
| [ ] | `science_tiles_order: [1,2,3,4,5,6,7,8]` (3人局，8个) | `science_tiles_order: [1,2,3,4,5,6,7,8]` | 科技瓦片区按顺序显示8个科技瓦片 |
| [ ] | `science_tiles_order: [1,2,3,4,5,6,7,8,9,10]` (4人局，10个) | `science_tiles_order: [1,2,3,4,5,6,7,8,9,10]` | 科技瓦片区按顺序显示10个科技瓦片 |
| [ ] | `science_tiles_order: [1,2,3,4,5,6,7,8,9,10,11,12]` (5人局，12个) | `science_tiles_order: [1,2,3,4,5,6,7,8,9,10,11,12]` | 科技瓦片区按顺序显示12个科技瓦片 |
| **书本行动设置**（固定3个，与人数无关） |
| [ ] | `selected_book_actions: [1,2,3]` | `selected_book_actions: [1,2,3]` | 书本行动区显示3个可选书本行动 |
| **初始玩家顺序** |
| [ ] | `init_player_order: [0,1,2]` (3人局) | `init_player_order: [0,1,2]` | 玩家1、玩家2、玩家3按此顺序进行初始选择 |
| [ ] | `init_player_order: [0,1,2,3]` (4人局) | `init_player_order: [0,1,2,3]` | 玩家1-4按此顺序进行初始选择 |
| [ ] | `init_player_order: [0,1,2,3,4]` (5人局) | `init_player_order: [0,1,2,3,4]` | 玩家1-5按此顺序进行初始选择 |
| **全局书本库存** |
| [ ] | `current_global_books: {bank_book: 12, law_book: 12, engineering_book: 12, medical_book: 12}` | `current_global_books` | 展示板显示各学科学书剩余数量（初始各12本） |

**注意：**
- 游戏支持 3-5 人局
- **规划卡**：总共7个，本局固定选 **6个**（与人数无关）
- **派系**：总共12个，本局选 **num_players + 1** 个
- **宫殿瓦片**：总共16个，本局选 **num_players + 1** 个
- **回合助推器**：总共10个，本局选 **num_players + 3** 个
- **轮次计分**：总共12个，本局固定选 **6个**（与人数无关）
- **最终计分**：总共4个，本局固定选 **1个**（与人数无关），前端需要 +12 映射到图片资源ID
- **能力瓦片**：总共12个，本局固定选 **12个**（与人数无关）
- **科技瓦片**：总共18个，本局选 **num_players * 2 + 2** 个
- **书本行动**：总共6个，本局固定选 **3个**（与人数无关）
- `current_global_books` 初始值：bank_book=12, law_book=12, engineering_book=12, medical_book=12

### 2.3 玩家状态 (PlayerState)

| 状态 | 后端 yield 数据 | 前端接收数据 | 前端可视化行为 |
|------|----------------|-------------|---------------|
| [✅] | `planning_card_id: 1` | `planningCard: "平原"` | 玩家卡片左上角显示棕色圆形指示器 |
| [✅] | `planning_card_id: 2` | `planningCard: "沼泽"` | 玩家卡片左上角显示灰色圆形指示器 |
| [✅] | `planning_card_id: 3` | `planningCard: "湖泊"` | 玩家卡片左上角显示蓝色圆形指示器 |
| [✅] | `planning_card_id: 4` | `planningCard: "森林"` | 玩家卡片左上角显示绿色圆形指示器 |
| [✅] | `planning_card_id: 5` | `planningCard: "山脉"` | 玩家卡片左上角显示灰色圆形指示器 |
| [✅] | `planning_card_id: 6` | `planningCard: "荒地"` | 玩家卡片左上角显示红色圆形指示器 |
| [✅] | `planning_card_id: 7` | `planningCard: "沙漠"` | 玩家卡片左上角显示黄色圆形指示器 |
| [✅] | `faction_id: 1` | `faction: "神佑者"` | 玩家名称旁显示派系徽章 |
| [✅] | `faction_id: 2` | `faction: "猫人"` | 玩家名称旁显示派系徽章 |
| [✅] | `faction_id: 3` | `faction: "哥布林"` | 玩家名称旁显示派系徽章 |
| [✅] | `faction_id: 4` | `faction: "幻术师"` | 玩家名称旁显示派系徽章 |
| [✅] | `faction_id: 5` | `faction: "发明家"` | 玩家名称旁显示派系徽章 |
| [✅] | `faction_id: 6` | `faction: "蜥蜴人"` | 玩家名称旁显示派系徽章 |
| [✅] | `faction_id: 7` | `faction: "鼹鼠"` | 玩家名称旁显示派系徽章 |
| [✅] | `faction_id: 8` | `faction: "僧侣"` | 玩家名称旁显示派系徽章 |
| [✅] | `faction_id: 9` | `faction: "航海家"` | 玩家名称旁显示派系徽章 |
| [✅] | `faction_id: 10` | `faction: "奥马尔"` | 玩家名称旁显示派系徽章 |
| [✅] | `faction_id: 11` | `faction: "哲学家"` | 玩家名称旁显示派系徽章 |
| [✅] | `faction_id: 12` | `faction: "通灵师"` | 玩家名称旁显示派系徽章 |
| [✅] | `resources.money: 15` | `money: 15` | 玩家状态区金币图标旁显示15 |
| [✅] | `resources.ore: 5` | `mineral: 5` | 玩家状态区矿石图标旁显示5 |
| [✅] | `resources.meeples: 3` | `mibao: 3` | 玩家状态区米宝图标旁显示3 |
| [✅] | `resources.bank_book: 2` | `bank: 2` | 玩家状态区银行学书图标旁显示2 |
| [✅] | `resources.law_book: 1` | `law: 1` | 玩家状态区法学书图标旁显示1 |
| [✅] | `resources.engineering_book: 0` | `engineering: 0` | 玩家状态区工程学书图标旁显示0 |
| [ ] | `resources.medical_book: 3` | `medical: 3` | 玩家状态区医学书图标旁显示3 |
| [ ] | `magics.zone1: 5` | `magic1: 5` | 玩家状态区魔力1区显示5 |
| [ ] | `magics.zone2: 7` | `magic2: 7` | 玩家状态区魔力2区显示7 |
| [ ] | `magics.zone3: 3` | `magic3: 3` | 玩家状态区魔力3区显示3 |
| [ ] | `boardscore: 25` | `score: 25` | 玩家卡片右上角显示25分 |
| [ ] | `booster_ids: [1, 3]` | `booster_ids: [1, 3]` | 玩家已拿取的助推板块高亮显示 |
| [ ] | `main_action_is_done: true` | `main_action_is_done: true` | 玩家状态区显示主行动已完成标记 |
| [ ] | `ispass: true` | `ispass: true` | 玩家状态区显示已跳过标记 |

### 2.4 地图状态 (MapState)

| 状态 | 后端 yield 数据 | 前端接收数据 | 前端可视化行为 |
|------|----------------|-------------|---------------|
| [ ] | `grid[row][col].terrain: 0` | `terrain: 0` | 六边形地块透明（水域） |
| [ ] | `grid[row][col].terrain: 1` | `terrain: 1` | 六边形地块棕色（平原） |
| [ ] | `grid[row][col].terrain: 2` | `terrain: 2` | 六边形地块深灰（沼泽） |
| [ ] | `grid[row][col].terrain: 3` | `terrain: 3` | 六边形地块蓝色（湖泊） |
| [ ] | `grid[row][col].terrain: 4` | `terrain: 4` | 六边形地块绿色（森林） |
| [ ] | `grid[row][col].terrain: 5` | `terrain: 5` | 六边形地块浅灰（山脉） |
| [ ] | `grid[row][col].terrain: 6` | `terrain: 6` | 六边形地块红色（荒地） |
| [ ] | `grid[row][col].terrain: 7` | `terrain: 7` | 六边形地块黄色（沙漠） |
| [ ] | `grid[row][col].controller: -1` | `controller: -1` | 地块无边框高亮 |
| [ ] | `grid[row][col].controller: 0` | `controller: 0` | 地块显示玩家1颜色边框 |
| [ ] | `grid[row][col].controller: 1` | `controller: 1` | 地块显示玩家2颜色边框 |
| [ ] | `grid[row][col].controller: 2` | `controller: 2` | 地块显示玩家3颜色边框 |
| [ ] | `grid[row][col].building_id: 0` | `building_id: 0` | 地块无建筑 |
| [ ] | `grid[row][col].building_id: 1` | `building_id: 1` | 地块显示车间图片 |
| [ ] | `grid[row][col].building_id: 2` | `building_id: 2` | 地块显示工会图片 |
| [ ] | `grid[row][col].building_id: 3` | `building_id: 3` | 地块显示宫殿图片 |
| [ ] | `grid[row][col].building_id: 4` | `building_id: 4` | 地块显示学校图片 |
| [ ] | `grid[row][col].building_id: 5` | `building_id: 5` | 地块显示大学图片 |
| [ ] | `grid[row][col].building_id: 6` | `building_id: 6` | 地块显示塔楼图片 |
| [ ] | `grid[row][col].building_id: 7` | `building_id: 7` | 地块显示纪念碑图片 |
| [ ] | `grid[row][col].building_id: 8` | `building_id: 8` | 地块显示侧楼图片 |
| [ ] | `grid[row][col].is_neutral: true` | `is_neutral: true` | 建筑显示为中立样式 |
| [ ] | `grid[row][col].has_annex: true` | `has_annex: true` | 主建筑旁叠加显示侧楼 |

### 2.5 可选行动 (AvailableActions)

| 状态 | 后端 yield 数据 | 前端接收数据 | 前端可视化行为 |
|------|----------------|-------------|---------------|
| [ ] | `available_actions: {1: "选择规划卡1", 2: "选择规划卡2"}` | `actions: [{id:1, text:"选择规划卡1"}, {id:2, text:"选择规划卡2"}]` | 右侧"可选行动"区域显示行动列表 |
| [ ] | `available_actions` 为空且有Agent | 不推送到前端 | 直接执行Agent决策，打印Agent log |
| [ ] | `available_actions` 为空且无Agent | 等待状态 | 显示"等待其他玩家..." |

### 2.6 游戏结束 (GameOver)

| 状态 | 后端 yield 数据 | 前端接收数据 | 前端可视化行为 |
|------|----------------|-------------|---------------|
| [ ] | `is_game_over: true` | `is_game_over: true` | 显示游戏结束弹窗 |
| [ ] | `final_scores[0].total: 120` | `final_scores[0].total: 120` | 显示玩家1最终总分120 |
| [ ] | `final_scores[0].board: 40` | `final_scores[0].board: 40` | 显示玩家1板面得分40 |
| [ ] | `final_scores[0].track: 30` | `final_scores[0].track: 30` | 显示玩家1科技轨得分30 |
| [ ] | `final_scores[0].chain: 25` | `final_scores[0].chain: 25` | 显示玩家1连锁得分25 |
| [ ] | `final_scores[0].resource: 25` | `final_scores[0].resource: 25` | 显示玩家1资源得分25 |

---

## 3. Agent 模式处理

### 3.1 Agent 检测逻辑

在 `GameController._get_action_id()` 中：

```python
if player_id in self._agents:
    # 当前玩家是Agent，直接获取行动ID
    agent = self._agents[player_id]
    action_id = agent.get_action(request)
    # 打印Agent决策日志到对应玩家的log框
    return action_id
else:
    # 当前玩家是人类，推送可选行动到前端
    self._push_available_actions(request)
    action_id = self._input_queue.get()
    return action_id
```

### 3.2 前端行为

| 场景 | 前端行为 |
|------|----------|
| 当前玩家是人类 | 显示可选行动列表，等待用户点击或输入 |
| 当前玩家是Agent | 不显示可选行动列表，在对应玩家log框显示Agent决策日志 |

---

## 4. 数据映射详情

### 4.1 规划卡ID映射

| ID | 颜色名称 | 颜色值 |
|----|---------|--------|
| 1 | 平原 | #85491D (棕色) |
| 2 | 沼泽 | #595959 (深灰) |
| 3 | 湖泊 | #35a0d5 (蓝色) |
| 4 | 森林 | #37af37 (绿色) |
| 5 | 山脉 | #a1a1a1 (浅灰) |
| 6 | 荒地 | #cc2828 (红色) |
| 7 | 沙漠 | #e8e83d (黄色) |

### 4.2 派系ID映射

| ID | 派系名称 |
|----|---------|
| 1 | 神佑者 |
| 2 | 猫人 |
| 3 | 哥布林 |
| 4 | 幻术师 |
| 5 | 发明家 |
| 6 | 蜥蜴人 |
| 7 | 鼹鼠 |
| 8 | 僧侣 |
| 9 | 航海家 |
| 10 | 奥马尔 |
| 11 | 哲学家 |
| 12 | 通灵师 |

### 4.3 建筑ID映射

| ID | 建筑类型 | 图片文件名格式 |
|----|---------|---------------|
| 0 | 无 | - |
| 1 | 车间 | `{planning_card_id}-workshop.png` |
| 2 | 工会 | `{planning_card_id}-guild.png` |
| 3 | 宫殿 | `{planning_card_id}-palace.png` |
| 4 | 学校 | `{planning_card_id}-school.png` |
| 5 | 大学 | `{planning_card_id}-university.png` |
| 6 | 塔楼 | `neutral-tower.png` |
| 7 | 纪念碑 | `neutral-monument.png` |
| 8 | 侧楼 | `{planning_card_id}-annex.png` |

### 4.4 地形ID映射

| ID | 地形类型 | 颜色值 |
|----|---------|--------|
| 0 | 水域 | transparent |
| 1 | 平原 | #85491D |
| 2 | 沼泽 | #595959 |
| 3 | 湖泊 | #35a0d5 |
| 4 | 森林 | #37af37 |
| 5 | 山脉 | #a1a1a1 |
| 6 | 荒地 | #cc2828 |
| 7 | 沙漠 | #e8e83d |

### 4.5 最终计分ID映射

| 后端值 | 前端映射值 | 图片路径 |
|--------|-----------|----------|
| 1 | 13 | `/images/scoring/13.png` |
| 2 | 14 | `/images/scoring/14.png` |
| 3 | 15 | `/images/scoring/15.png` |
| 4 | 16 | `/images/scoring/16.png` |

**映射公式：** `frontend_id = backend_id + 12`

---

## 5. 状态更新流程

### 5.1 全量更新流程

```
1. 页面加载/刷新
2. GameView.vue onMounted 调用 gameStateStore.init(gameId)
3. gameStateStore 发送 GET /api/game/state
4. 后端返回完整状态
5. gameStateStore.applyFullState() 更新 store 状态
6. GameView.vue 的 watch 监听到变化，同步到本地状态
7. UI 更新显示
```

### 5.2 增量更新流程

```
1. 游戏引擎 yield ActionRequest
2. GameStateManager.update_from_action_request() 计算 diff
3. GameStateManager._push_to_frontend() 推送 SSE 消息
4. 前端接收 SSE 消息
5. gameStateStore.handleSSEMessage() 处理消息
6. gameStateStore.applyChanges() 应用增量变更
7. GameView.vue 的 watch 监听到变化，同步到本地状态
8. UI 更新显示
```

### 5.3 增量更新路径格式

| 更新类型 | 路径示例 |
|----------|----------|
| 回合数 | `meta.round` |
| 当前玩家 | `meta.current_player_id` |
| 玩家资源 | `players[0].resources.money` |
| 玩家魔力 | `players[0].magics.zone1` |
| 地图地形 | `map_state.grid[3][5].terrain` |
| 地图建筑 | `map_state.grid[3][5].building_id` |
| 地图控制者 | `map_state.grid[3][5].controller` |
| 可选行动 | `available_actions` |

---

## 6. 附录

### 6.1 消息推送机制

游戏状态通过 **回调函数** 机制推送到前端：

```
GameStateManager / GameController
    │
    ▼ 调用回调函数
put_message(message: dict)
    │
    ▼ 放入队列
_message_queue
    │
    ▼ SSE 拉取
前端 EventSource
```

### 6.2 Player ID 映射

| 后端 player_id | 前端显示 |
|----------------|----------|
| 0 | 玩家 1 |
| 1 | 玩家 2 |
| 2 | 玩家 3 |

### 6.3 游戏设置数量规则

| 设置项 | 数量规则 | 说明 |
|--------|---------|------|
| `selected_planning_cards` | `num_players` | 每人选1个 |
| `selected_factions` | `num_players + 1` | 多1个供选择 |
| `selected_palace_tiles` | `num_players + 1` | 多1个供选择 |
| `selected_round_boosters` | `num_players + 3` | 每回合1个 + 3个额外 |
| `round_scoring_order` | 6 | 固定6个回合 |
| `final_scoring` | 1 | 固定1个最终计分 |

---

## 7. 版本历史

| 版本 | 日期 | 修改内容 |
|------|------|----------|
| 1.0 | 2026-04-07 | 初始版本 |
| 2.0 | 2026-04-07 | 重构为三列表格格式，修正数据映射错误，添加进度跟踪复选框 |
