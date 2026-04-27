# 初选板块卡片设计文档

## 概述

在游戏区域新增第4个卡片"初选板块"，用于展示本局游戏中可用的规划卡、派系和宫殿板块图片。采用只读展示模式，不支持交互和玩家标记。

## 需求确认

- **展示内容**：本局游戏的规划卡、派系、宫殿板块图片
- **布局方式**：分上中下三栏，每栏横向排列图片
- **交互方式**：不可点击，纯展示
- **玩家标记**：不显示

## 架构

### 组件结构

在 `GameView.vue` 的 `game-grid` 中新增第4个 `game-card`：

```
game-grid
└── game-card (初选板块)
    ├── game-header (可折叠)
    │   ├── game-title (图标 + "初选板块")
    │   └── game-indicator (折叠箭头)
    └── selection-board-status (内容区)
        ├── selection-section (规划卡栏)
        │   ├── section-title ("规划卡")
        │   └── section-items (横向排列)
        ├── selection-section (派系栏)
        │   ├── section-title ("派系")
        │   └── section-items (横向排列)
        └── selection-section (宫殿板块栏)
            ├── section-title ("宫殿板块")
            └── section-items (横向排列)
```

### 数据流

1. 从 `gameStateStore.setup` 获取：
   - `selected_planning_cards: number[]`
   - `selected_factions: number[]`
   - `selected_palace_tiles: number[]`

2. 使用现有工具函数将 backend ID 映射为 sprite 样式：
   - 规划卡：`getPlanningCardPreviewStyle()`（已有）
   - 派系：`getFactionPreviewStyle()`（已有）
   - 宫殿板块：新建 `getPalaceTilePreviewStyle()`

### 样式规范

- 与现有 `game-card` 风格一致
- 三栏间距使用 `gap: 16px`
- 每栏标题使用 `section-title` 样式（参考 `round-label`）
- 图片项使用固定尺寸，横向 flex 排列
- 图片间距 `gap: 12px`
- 支持横向滚动（当图片过多时）

## 实现范围

### 修改文件

1. `frontend/src/views/GameView.vue`
   - 添加 `collapsedCards['draft']` 状态
   - 添加卡片模板（第4个 game-card）
   - 添加 `getPalaceTilePreviewStyle()` 函数
   - 添加相关 CSS 样式

2. `docs/version-change-log.md`
   - 记录本次修改

### 不修改的文件

- `backend/game/aoi_game/` 目录下的任何文件（受保护）
- 现有 popover 系统
- 现有图片工具函数（除新增宫殿板块预览函数外）

## 验证方式

1. 启动游戏后，游戏区域显示"初选板块"卡片
2. 卡片正确展示本局的规划卡、派系、宫殿板块图片
3. 卡片可折叠/展开
4. 图片排列整齐，无重叠
