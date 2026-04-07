# Age of Innovation - 项目架构文档

## 项目概述

《大创造时代》(Age of Innovation) 桌游的数字实现版本，采用前后端分离架构。

## 目录结构

```
Age-of-Innovation_TableGame/
├── backend/                    # 后端代码
│   ├── api/                    # API 层 - HTTP 接口
│   │   ├── __init__.py
│   │   ├── server.py           # Flask 应用创建和服务器运行
│   │   ├── middleware/         # 中间件
│   │   │   ├── __init__.py
│   │   │   ├── cors.py         # CORS 配置
│   │   │   └── error_handler.py # 错误处理
│   │   └── routes/             # 路由模块
│   │       ├── __init__.py
│   │       ├── game.py         # 游戏相关 API
│   │       ├── history.py      # 历史记录 API
│   │       ├── stream.py       # SSE 流端点
│   │       └── static.py       # 静态文件服务
│   │
│   ├── core/                   # 核心层 - 游戏生命周期管理
│   │   ├── __init__.py
│   │   ├── io_interface.py     # IO 接口定义（抽象基类）
│   │   ├── game_manager.py     # 游戏管理器
│   │   └── game_runner.py      # 游戏运行器（线程管理）
│   │
│   ├── io/                     # IO 层 - 与前端交互
│   │   ├── __init__.py
│   │   ├── web_io.py           # Web IO 实现（SSE + HTTP）
│   │   ├── silent_io.py        # 静默 IO 实现（模拟模式）
│   │   └── message_queue.py    # 消息队列管理
│   │
│   ├── services/               # 服务层 - 业务逻辑
│   │   ├── __init__.py
│   │   ├── game_service.py     # 游戏业务逻辑
│   │   └── history_service.py  # 历史记录业务逻辑
│   │
│   ├── models/                 # 数据模型
│   │   ├── __init__.py
│   │   └── dto/                # 数据传输对象
│   │       ├── __init__.py
│   │       ├── game_config.py  # 游戏配置 DTO
│   │       └── player_config.py # 玩家配置 DTO
│   │
│   ├── database/               # 数据访问层
│   │   ├── __init__.py
│   │   ├── models.py           # SQLAlchemy ORM 模型
│   │   └── repository.py       # 数据访问对象
│   │
│   ├── config/                 # 配置
│   │   ├── __init__.py
│   │   └── settings.py         # 应用配置
│   │
│   ├── utils/                  # 工具
│   │   ├── __init__.py
│   │   └── logger.py           # 日志配置
│   │
│   ├── game/                   # 游戏逻辑（核心业务）
│   │   ├── __init__.py
│   │   ├── GameEngine.py       # 游戏引擎
│   │   ├── GameState.py        # 游戏状态
│   │   ├── ActionSystem.py     # 行动系统
│   │   ├── DetailedAction.py   # 详细行动
│   │   ├── EffectObject.py     # 效果对象
│   │   ├── Agent.py            # AI 代理
│   │   └── GameHistoryRecorder.py # 游戏历史记录器
│   │
│   ├── app.py                  # 应用入口（新架构）
│   ├── game_init.py            # 游戏初始化（兼容层）
│   ├── web_io.py               # Web IO 兼容层（已弃用）
│   ├── database.py             # 数据库兼容层（已弃用）
│   ├── AIAssistant.py          # AI 助手
│   └── test.py                 # 测试代码
│
├── frontend/                   # 前端代码 (Vue.js)
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   ├── src/
│   │   ├── main.js
│   │   ├── App.vue
│   │   ├── components/
│   │   ├── stores/
│   │   └── styles/
│   └── assets/
│       └── images/             # 游戏图片资源
│
├── data/                       # 数据文件
│   └── game_history.db         # SQLite 数据库
│
├── game_logs/                  # 游戏日志
│
├── rule/                       # 游戏规则文档
│
├── start.py                    # 一键启动脚本
└── PROJECT_STRUCTURE.md        # 本文档
```

## 架构分层

### 1. API 层 (`backend/api/`)

负责处理 HTTP 请求和响应。

- **server.py**: Flask 应用创建和配置
- **routes/**: 按功能划分的路由模块
  - `game.py`: 游戏启动、状态查询
  - `history.py`: 历史记录 CRUD
  - `stream.py`: SSE 实时数据流
  - `static.py`: 静态文件服务
- **middleware/**: 可复用的中间件
  - `cors.py`: 跨域配置
  - `error_handler.py`: 统一错误处理

### 2. 核心层 (`backend/core/`)

游戏生命周期管理，与具体 IO 实现解耦。

- **io_interface.py**: 定义 IO 接口契约，所有 IO 实现必须遵守
- **game_manager.py**: 管理游戏状态（启动、停止、查询）
- **game_runner.py**: 在后台线程中运行游戏

### 3. IO 层 (`backend/io/`)

实现与前端的具体交互方式。

- **web_io.py**: 通过 SSE 与前端实时通信
- **silent_io.py**: 静默模式（用于模拟）
- **message_queue.py**: 管理 SSE 消息队列

### 4. 服务层 (`backend/services/`)

业务逻辑实现，协调各层工作。

- **game_service.py**: 处理游戏启动等业务流程
- **history_service.py**: 处理历史记录业务逻辑

### 5. 数据层 (`backend/models/`, `backend/database/`)

数据模型和持久化。

- **models/dto/**: 数据传输对象，用于 API 交互
- **database/**: ORM 模型和数据访问对象

## 关键改进

### 1. 分层清晰

每个模块职责单一，通过接口进行交互：

```
API Layer (Flask Routes)
    ↓
Service Layer (Business Logic)
    ↓
Core Layer (Game Lifecycle)
    ↓
IO Layer (Web/Silent)
    ↓
Game Engine (Core Logic)
```

### 2. 依赖注入

通过抽象接口 `IOInterface`，游戏引擎不依赖具体的 IO 实现：

```python
# 生产环境使用 WebIO
game_manager.set_io(WebIO(player_count=3))

# 模拟环境使用 SilentIO
game_manager.set_io(SilentIO())
```

### 3. 向后兼容

保留旧接口作为兼容层：

- `backend/app.py`: 提供旧的 `GamePanelAPI` 和 `Silence_IO`
- `backend/web_io.py`: 提供旧的 `GamePanel` 类
- `backend/game_init.py`: 提供旧的 `start_game()` 和 `simulate()` 函数

### 4. 默认 Human 模式

`start_game` 现在忽略传入的 `players` 参数，默认使用全部 human 模式：

```python
# 无论传入什么 players 配置，都使用 ['human', 'human', 'human']
action_mode = ['human'] * num_players
```

## API 端点

### 游戏相关

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/game/start` | 启动游戏 |
| GET | `/api/game/status` | 获取游戏状态 |
| GET | `/config` | 获取配置信息 |
| POST | `/input` | 提交用户输入 |

### 历史记录

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/games` | 获取游戏列表 |
| POST | `/api/games` | 创建游戏记录 |
| GET | `/api/games/<id>` | 获取游戏详情 |
| DELETE | `/api/games/<id>` | 删除游戏记录 |
| GET | `/api/games/stats` | 获取统计信息 |

### SSE 数据流

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/stream/status` | 全局状态流 |
| GET | `/stream/actions` | 可选行动流 |
| GET | `/stream/player<N>` | 玩家 N 的数据流 |

## 配置

配置位于 `backend/config/settings.py`：

```python
@dataclass
class Settings:
    host: str = '127.0.0.1'
    port: int = 5001
    player_count: int = 3
    min_players: int = 3
    max_players: int = 5
    static_folder: Optional[str] = None
    db_path: Optional[str] = None
```

## 启动方式

### 方式1: 使用启动脚本（推荐）

```bash
python start.py
```

### 方式2: 直接运行后端

```bash
python -m backend.app
```

### 方式3: 分别启动

```bash
# 后端
python -c "from backend.api import run_app; run_app()"

# 前端
cd frontend && npm run dev
```

## 开发指南

### 添加新的 API 端点

1. 在 `backend/api/routes/` 创建或修改路由文件
2. 在 `backend/services/` 添加对应的业务逻辑
3. 在 `backend/api/server.py` 注册蓝图（如需要）

### 实现新的 IO 方式

1. 创建类继承 `IOInterface`
2. 实现所有抽象方法
3. 在需要的地方使用：`game_manager.set_io(YourIO())`

### 修改游戏配置

编辑 `backend/models/dto/game_config.py` 中的 DTO 类。

## 端口配置

- **前端**: 端口 5050 (http://127.0.0.1:5050)
- **后端**: 端口 5001 (http://127.0.0.1:5001)

## 迁移说明

### 从旧代码迁移

旧代码仍然可用，但会收到弃用警告：

```python
# 旧方式（仍然可用）
from backend.web_io import GamePanel
panel = GamePanel(player_count=3)

# 新方式（推荐）
from backend.io import WebIO
from backend.core import get_game_manager
io = WebIO(player_count=3)
manager = get_game_manager()
manager.set_io(io)
```

### 数据库兼容性

数据库模型保持不变，自动兼容旧数据。
