# 项目架构说明

## 目录结构

```
Age-of-Innovation_TableGame/
├── backend/                    # 后端代码
│   ├── app.py                 # Flask API服务主文件
│   └── web_io.py              # 兼容旧版的IO类
├── frontend/                   # 前端代码
│   ├── index.html             # 主HTML文件
│   ├── css/
│   │   └── style.css          # 样式文件
│   └── js/
│       ├── config.js          # 配置文件
│       ├── main.js            # 主入口
│       ├── ui.js              # UI交互
│       ├── hexMap.js          # 六边形地图
│       ├── roundInfo.js       # 回合信息
│       ├── playerState.js     # 玩家状态
│       └── eventStream.js     # SSE事件流
├── assets/                     # 静态资源
│   └── images/                 # 图片资源
│       ├── bonus/
│       ├── buildings/
│       ├── items/
│       └── scoring/
├── game_logs/                  # 游戏日志
├── main.py                     # 游戏主入口（使用新架构）
├── start_backend.py            # 启动后端服务
├── start_frontend.py           # 启动前端服务
└── PROJECT_STRUCTURE.md        # 本文档
```

## 端口配置

- **前端**: 端口 5000 (http://127.0.0.1:5000)
- **后端**: 端口 5001 (http://127.0.0.1:5001)

## 启动方式

### 方式1: 分别启动前后端

1. 启动后端服务:
```bash
python start_backend.py
```

2. 启动前端服务:
```bash
python start_frontend.py
```

### 方式2: 运行完整游戏（自动启动后端）

```bash
python main.py
```

然后手动启动前端:
```bash
python start_frontend.py
```

## 架构变更说明

### 1. 前后端分离

**原架构:**
- Flask同时提供API和渲染HTML模板
- 所有前端代码在单个HTML文件中
- 前后端共用端口5000

**新架构:**
- 后端Flask只提供API服务（端口5001）
- 前端使用纯HTML/CSS/JS，独立部署（端口5000）
- 通过CORS实现跨域通信
- 前端通过SSE连接后端数据流

### 2. 前端文件拆分

**原架构:**
- `templates/game_panel.html` - 3000+行，包含所有CSS和JS

**新架构:**
- `frontend/index.html` - 精简的HTML结构
- `frontend/css/style.css` - 所有样式
- `frontend/js/*.js` - 按功能拆分的JavaScript模块

### 3. 后端代码组织

**原架构:**
- `web_io.py` - 包含Flask应用和GamePanel类

**新架构:**
- `backend/app.py` - 核心API服务（GamePanelAPI类）
- `backend/web_io.py` - 兼容层（GamePanel类，保持旧接口）

## API端点

### SSE数据流
- `GET /stream/status` - 全局状态流
- `GET /stream/actions` - 可选行动流
- `GET /stream/player{N}` - 玩家N的数据流

### 其他接口
- `POST /input` - 提交用户输入
- `GET /images/{filename}` - 获取图片资源
- `GET /config` - 获取配置信息

## 配置修改

前端配置在 `frontend/js/config.js`:
```javascript
const CONFIG = {
    API_BASE_URL: 'http://127.0.0.1:5001',  // 后端地址
    PLAYER_COUNT: 3                          // 玩家数量
};
```

## 兼容性

- 原有 `main.py` 的调用方式保持不变
- `GamePanel` 和 `Silence_IO` 类接口保持不变
- 游戏逻辑代码无需修改
