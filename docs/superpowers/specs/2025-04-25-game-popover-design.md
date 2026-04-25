# 游戏页面通用 Popover 弹窗组件设计

## 概述

设计一个轻量级通用 Popover 弹窗组件，用于替代 GameView 中现有的悬停预览（entityPreview），并为玩家状态栏的每个指标提供点击明细弹窗。

## 现有系统分析

### Modal.vue（全屏弹窗）
- 用途：全局模态框（策略选择、结算等）
- 特征：全屏遮罩、背景模糊、有关闭按钮
- 保留：不影响，继续用于全屏场景

### entityPreview（悬停预览系统）
- 用途：状态详情展示（规划卡、宫殿板块、派系、回合计分板等，均包含大图）
- 特征：mouseenter 触发、无点击关闭机制、耦合在 GameView 中
- 状态：将被本 Popover 组件完全替代。所有现有图片预览本质上也是"状态详情弹窗"的一种形式——只是在 content 中放了一张（或几张）大图。

## 设计目标

1. **点击触发**：所有弹窗通过点击触发，不再使用悬停
2. **点击外部关闭**：无关闭按钮，点击弹窗外任意位置关闭
3. **不遮挡背景**：无遮罩层、无背景模糊
4. **灵活定位**：支持上下左右四个方位，自动检测视口边界并翻转
5. **轻量化风格**：沿用 entityPreview 的视觉风格（半透明卡片、无标题栏）
6. **统一组件**：一个 Popover 组件覆盖所有场景，content 完全由 slot 决定，可以是图片、文本、表格或混合内容

## 组件设计

### Popover.vue

```
Props:
- trigger: 'click' | 'hover' (默认 'click')
- placement: 'top' | 'bottom' | 'left' | 'right' | 'auto' (默认 'auto')
- offset: number (默认 8px)
- width: string | number (默认 'auto')
- maxWidth: number (默认 320)
- showArrow: boolean (默认 true)

Slots:
- default: 触发元素（必须）
- content: 弹窗内容

Events:
- show: 弹窗打开时
- hide: 弹窗关闭时
```

### usePopoverPosition() 组合式函数

负责：
1. 计算触发元素的位置（getBoundingClientRect）
2. 根据 placement 计算弹窗初始位置
3. 检测视口边界（上下左右各留 padding）
4. 空间不足时自动翻转 placement
5. 使用 fixed 定位确保不受父级 overflow: hidden 影响

## 视觉风格

- 背景：`rgba(30, 30, 40, 0.95)`（深色半透明）
- 边框：1px solid `rgba(255, 255, 255, 0.1)`
- 圆角：12px
- 阴影：`0 8px 32px rgba(0, 0, 0, 0.4)`
- 无标题栏、无关闭按钮
- 箭头：8px 小三角，颜色与背景一致
- padding：16px

## 迁移计划

### Phase 1: 创建 Popover 组件
1. 创建 `components/Popover.vue`
2. 创建 `composables/usePopoverPosition.js`

### Phase 2: 全量替换所有悬停预览（统一为点击弹窗）
将所有现有的 `mouseenter/mouseleave` 触发改为 `click` 触发，用 Popover 包裹触发元素：
1. 规划卡详情（包含大图）
2. 宫殿板块详情（包含大图）
3. 派系详情（包含大图）
4. 回合计分板详情（包含大图）
5. 回合助推板详情（包含大图）
6. 科学板块详情（包含大图）
7. 能力板块详情（包含大图）
8. 玩家状态栏各项指标详情（内容暂空，预留 slot）

### Phase 3: 清理 entityPreview
1. 删除 GameView 中所有 entityPreview 相关代码
2. 删除相关的 reactive 状态、timer、事件处理函数

## 文件变更

### 新增
- `frontend/src/components/Popover.vue`
- `frontend/src/composables/usePopoverPosition.js`

### 修改
- `frontend/src/views/GameView.vue`（替换 entityPreview、新增状态弹窗）

### 删除
- GameView.vue 中的 entityPreview 相关代码（约 300 行）

## API 示例

```vue
<!-- 规划卡详情（包含大图） -->
<Popover placement="auto" :offset="12">
  <div class="planning-card-circle" />
  <template #content>
    <div class="detail-header">规划卡名称</div>
    <div class="detail-image" :style="imageStyle" />
  </template>
</Popover>

<!-- 金币明细（纯文本/表格，内容暂空） -->
<Popover placement="bottom" width="280">
  <div class="stat-item">
    <i class="fas fa-coins" />
    <span>15</span>
  </div>
  <template #content>
    <div class="detail-header">金币明细</div>
    <div class="detail-body">
      <!-- 预留内容：收入来源、支出明细等 -->
    </div>
  </template>
</Popover>

<!-- 回合计分板详情（多图叠加） -->
<Popover placement="top" :offset="12">
  <div class="round-scoring-cell" />
  <template #content>
    <div class="detail-header">第 3 回合</div>
    <div class="detail-images">
      <div class="detail-image" :style="baseLayerStyle" />
      <div class="detail-image overlay" :style="overlayLayerStyle" />
    </div>
  </template>
</Popover>
```

## 边界情况

1. **触发元素靠近视口边缘**：自动翻转 placement，确保弹窗完整可见
2. **快速点击多个触发器**：先关闭已打开的弹窗，再打开新的（单例模式）
3. **滚动时**：弹窗随触发元素位置更新（监听 scroll + resize）
4. **内容高度变化**：使用 ResizeObserver 重新计算位置

## 废弃声明

本设计完成后，以下代码将被删除：
- `entityPreview` reactive 对象
- `entityPreviewTimer` / `entityPreviewHideTimer`
- `queueEntityPreview` / `clearEntityPreviewTimer` / `scheduleEntityPreviewHide`
- 所有 `handle*MouseEnter` / `handle*MouseLeave` 函数
- 所有 `@mouseenter` / `@mouseleave` 事件绑定
