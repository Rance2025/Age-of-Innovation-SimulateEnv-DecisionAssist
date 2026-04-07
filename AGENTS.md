# Agent 行为规范

## 重要规则

### 1. `backend/game/` 目录保护
- **`backend/game/aoi_game/` 目录下的所有文件都经过可靠验证，不应被修改**
- **特别重要：`backend/game/aoi_game/` 目录下的任何文件都不得修改**
- 除非得到用户的明确指令，否则不要修改这些文件
- 这包括：`Agent.py`、`ActionSystem.py`、`GameState.py`、`EffectObject.py` 等
- 允许修改的文件在 `backend/game/` 目录下仅限于：
  - `backend/game/start_game.py`，游戏启动入口
  - `backend/game/utils/` 目录下的工具文件，如 `game_state_manager.py`、`frontend_state_types.py`

### 2. 前后端玩家编号映射
- 后端 `player_id` 从 `0` 开始，即 `0`、`1`、`2`
- 前端显示为玩家 `1`、`2`、`3`，对应后端 `player_id 0`、`1`、`2`
- 如果后端返回结构或字段命名发生变化，应同步更新前端映射和相关文档，不再引入或沿用已经废弃的中间概念

### 3. 可修改的文件范围
- `frontend/` 目录下的文件
- `backend/api/` 目录下的文件
- `backend/app.py`
- `backend/game/start_game.py`
- `backend/game/utils/` 目录下的文件
- 其他配置文件

### 4. 修改 `backend/game/` 前必须确认
在修改任何 `backend/game/` 目录下的文件之前，必须：
1. 得到用户的明确指令
2. 说明为什么要修改
3. 说明修改的具体内容

### 5. 后端关闭时的清理规范
每当后端通过 `Ctrl+C` 退出时，必须确保：
1. 清除游戏状态：清除 localStorage 中的 `gameInProgress` 和 `gameSettings`
2. 后端安全关闭：确保所有线程正确结束，没有残留进程
3. 游戏自动关闭：前端应能检测后端断开并清理状态
4. 资源释放：关闭所有打开的文件句柄和网络连接

### 6. Git 版本与版本变更记录维护
- 每次进行任何可感知的小更新、修复、样式调整、交互调整或数据结构调整后，都必须同步维护版本变更文档：`docs/version-change-log.md`
- Git 提交版本名默认使用纯数字版本号，例如：`0.9.5.4`
- 具体更新内容不写在提交名里，统一写入 `docs/version-change-log.md`
- 在用户尚未提供版本号前，所有未提交改动统一写入 `docs/version-change-log.md` 的 `本次修改` 区域
- 当用户后续提供版本号并准备 Git 时，再将 `本次修改` 中的内容归档到对应版本号条目
- `更新内容` 下的每一条都必须使用 `type: 中文描述` 的格式，例如：`feat: 新增功能说明`、`fix: 修复问题说明`、`ui: 界面调整说明`、`chore: 杂项维护说明`
- `type` 必须使用 Git 常用英文术语并保持小写，优先使用：`feat`、`fix`、`ui`、`chore`、`docs`、`refactor`、`test`
- 如果版本记录格式规范发生变化，需要同步追溯修正 `docs/version-change-log.md` 中的现有内容，保持整份文档格式一致
- `本次修改` 至少包含：
  - 日期
  - 分支
  - 影响范围
  - 更新内容（每条均为 `type: 中文描述` 格式）
  - 验证方式
- 正式版本条目至少包含：
  - 日期
  - 分支
  - 影响范围
  - 更新内容（每条均为 `type: 中文描述` 格式）
  - 验证方式
- 如果本次只是很小的补丁，也仍然需要写入 `本次修改`
