# 全局单例弹窗重构文档

## 一、重构目标

将现有分散的 `<Popover>` 组件实例统一替换为全局单例弹窗系统。核心原则：**触发点只提供"位置"和"内容数据"，其余所有逻辑（定位、动画、生命周期、全局唯一性）由单例弹窗实例托管。**

## 二、当前问题分析

### 2.1 现有架构
- 44 个 `<Popover>` 实例分散在 `GameView.vue` 中
- 每个实例独立管理自己的状态（visible、位置、事件监听）
- 需要 `Teleport`、`ref`、`@show/@hide` 等繁琐绑定
- 定位逻辑重复：每个实例都通过 `usePopoverPosition` 计算

### 2.2 核心痛点
1. **高耦合**：触发元素与弹窗组件深度嵌套，每个触发点都需要包裹 `<Popover>`
2. **低内聚**：定位、动画、关闭逻辑散落在 44 个实例中
3. **切换不流畅**：不同实例之间切换必须先关后开，无平滑过渡
4. **维护困难**：修改弹窗行为需要改动 40+ 处

## 三、新架构设计

### 3.1 第一性原理

弹窗的本质 = **位置 + 内容**。其他一切都是衍生需求。

```
触发点："我在哪，我要显示什么"
    ↓
单例弹窗："我来计算位置，我来管理动画，我来保证全局唯一"
```

### 3.2 架构图

```
GameView.vue
├── 触发元素（纯 DOM，@click → globalPopover.open(config)）
├── <GlobalPopover />（Teleport to body，页面唯一实例）
│   ├── 位置计算（usePopoverPosition）
│   ├── 动画控制（CSS transition）
│   ├── 生命周期管理（点击外部、ESC 关闭）
│   └── 内容渲染（GlobalPopoverContent）
└── 特殊：1×1px trigger div（地块弹窗用）

useGlobalPopover.js（全局状态）
├── state: { visible, currentTriggerId, position, data, ... }
├── open(config) → 打开或切换
├── close() → 关闭
└── calculatePosition() → 自动适配 placement
```

## 四、文件清单

### 4.1 新建文件

| 文件 | 职责 |
|------|------|
| `frontend/src/composables/useGlobalPopover.js` | 全局状态管理 + 定位计算 + open/close API |
| `frontend/src/components/GlobalPopover.vue` | 单例弹窗容器（Teleport、fixed、动画控制） |
| `frontend/src/components/GlobalPopoverContent.vue` | 内容渲染（复用现有三种布局逻辑） |

### 4.2 修改文件

| 文件 | 修改内容 |
|------|----------|
| `frontend/src/views/GameView.vue` | **核心改动**：移除所有 44 个 `<Popover>`，改为 `@click` 调用 API；引入 `<GlobalPopover />` |
| `frontend/src/main.js` | 注册全局弹窗实例（或在 App.vue 中引入） |

### 4.3 删除文件

| 文件 | 说明 |
|------|------|
| `frontend/src/components/Popover.vue` | 旧组件，功能被 GlobalPopover 替代 |
| `frontend/src/components/PopoverContent.vue` | 旧组件，功能被 GlobalPopoverContent 替代 |
| `frontend/src/composables/usePopoverPosition.js` | 逻辑合并到 useGlobalPopover |

## 五、接口设计

### 5.1 useGlobalPopover API

```javascript
// useGlobalPopover.js
import { reactive, computed } from 'vue'

const state = reactive({
  visible: false,
  isClosing: false,
  currentTriggerId: null,
  position: { top: 0, left: 0 },
  actualPlacement: 'bottom',
  data: null,
  config: null
})

export function useGlobalPopover() {
  return {
    // 状态（只读）
    visible: computed(() => state.visible),
    isClosing: computed(() => state.isClosing),
    position: computed(() => state.position),
    actualPlacement: computed(() => state.actualPlacement),
    data: computed(() => state.data),
    
    // 方法
    open,
    close,
    updatePosition
  }
}

/**
 * 打开弹窗或切换到新目标
 * @param {Object} config
 * @param {string} config.id - 触发器唯一标识（用于 toggle 判断）
 * @param {HTMLElement} config.triggerEl - 触发 DOM 元素
 * @param {string} config.type - 'preview' | 'detail'
 * @param {string} config.placement - 'auto' | 'top' | 'bottom' | 'left' | 'right'
 * @param {number} config.offset - 间距（默认 16）
 * @param {string|Function} config.clickOutsideExclude - 点击外部排除选择器
 * @param {Object} config.data - PopoverContent 数据
 */
function open(config) { ... }

/**
 * 关闭弹窗
 */
function close() { ... }

/**
 * 手动更新位置（用于外部布局变化后重新定位）
 */
function updatePosition() { ... }
```

### 5.2 GlobalPopover Props

```vue
<!-- GlobalPopover.vue -->
<script setup>
// 无 props，完全由 useGlobalPopover 状态驱动
</script>
```

### 5.3 GlobalPopoverContent Props

```vue
<!-- GlobalPopoverContent.vue -->
<script setup>
const props = defineProps({
  imageContainerStyle: Object,      // 图片容器样式
  imageLayerStyle: Object,          // 图片层样式（背景图）
  name: String,                     // 实体名称
  inactive: Boolean,                // 是否未激活（灰度）
  detailTitle: { type: String, default: '变更明细' },
  aspectRatio: String,              // 图片宽高比（用于判断 tall/wide）
  placeholderCount: { type: Number, default: 20 }
})
</script>
```

### 5.4 触发点调用示例

```vue
<!-- 玩家面板 - 规划卡 -->
<div
  class="planning-card-circle is-visible"
  @click="handlePlanningCardClick($event, player)"
></div>

<!-- 游戏版图 - 地块（特殊：1×1px trigger div） -->
<div
  ref="tileDetailTriggerRef"
  style="position: absolute; width: 1px; height: 1px; pointer-events: none;"
></div>
```

```javascript
// 规划卡点击
function handlePlanningCardClick(event, player) {
  globalPopover.open({
    id: `planning-${player.id}`,
    triggerEl: event.currentTarget,
    type: 'preview',
    placement: 'auto',
    data: {
      imageContainerStyle: { '--preview-width': '176px', '--preview-aspect-ratio': '118/187' },
      imageLayerStyle: getPlanningCardPreviewStyle(player.planningCardId),
      name: player.planningCard || planningCardIdToName[player.planningCardId] || '',
      aspectRatio: '118/187'
    }
  })
}

// 地块点击（特殊处理）
function handleTileClick(row, col) {
  const tileKey = `${row}-${col}`
  
  // Toggle：点击同一地块则关闭
  if (globalPopover.currentTriggerId === tileKey && globalPopover.visible) {
    globalPopover.close()
    return
  }
  
  // 设置 trigger div 位置到六边形中心
  const hex = document.querySelector(`.hexagon[data-row="${row}"][data-col="${col}"]`)
  const container = tileDetailTriggerRef.value.closest('.map-container-full')
  const containerRect = container.getBoundingClientRect()
  const hexRect = hex.getBoundingClientRect()
  
  tileDetailTriggerRef.value.style.left = (hexRect.left + hexRect.width/2 - containerRect.left) + 'px'
  tileDetailTriggerRef.value.style.top = (hexRect.top + hexRect.height/2 - containerRect.top) + 'px'
  
  globalPopover.open({
    id: tileKey,
    triggerEl: tileDetailTriggerRef.value,
    type: 'detail',
    placement: 'auto',
    offset: 32,
    clickOutsideExclude: '.hover-overlay',
    data: {
      detailTitle: `${position} 地块 · ${terrainName}`,
      placeholderCount: 20
    }
  })
}
```

## 六、动画策略

### 6.1 状态流转图

```
关闭状态 ──open(A)──→ 打开状态 A（fade-in）
  ↑                      │
  │                      │ open(B) 且 B ≠ A
  │                      ↓
  │                   切换状态 A→B（位置平移 + 内容瞬间切换）
  │                      │
  │                      │ open(A) 且 A = current（toggle）
  │                      ↓
  │                   关闭状态（fade-out）
  │                      │
  │                      │ 点击外部 / ESC
  └──────────────────────┘
```

### 6.2 动画定义

```css
/* GlobalPopover.vue */

/* 首次打开 */
.global-popover-enter-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.global-popover-enter-from {
  opacity: 0;
  transform: scale(0.95);
}

/* 关闭 */
.global-popover-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.global-popover-leave-to {
  opacity: 0;
  transform: scale(0.95);
}

/* 切换时位置平移 */
.global-popover.is-switching {
  transition: top 0.3s ease, left 0.3s ease;
}

/* 基础样式 */
.global-popover {
  position: fixed;
  z-index: 1000;
  background: #2a2a2a;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
  padding: 16px;
}
```

### 6.3 切换动画实现细节

**关键：切换时保持弹窗可见，不做 fade-out/fade-in**

```javascript
function performSwitch(newConfig) {
  // 1. 添加位置过渡类
  popoverEl.classList.add('is-switching')
  
  // 2. 瞬间切换内容数据（Vue 响应式自动更新 DOM）
  state.data = newConfig.data
  state.currentTriggerId = newConfig.id
  
  // 3. 计算新位置
  calculatePosition(newConfig.triggerEl, newConfig.placement, newConfig.offset)
  
  // 4. 300ms 后移除过渡类（避免后续非切换操作也有过渡）
  setTimeout(() => {
    popoverEl.classList.remove('is-switching')
  }, 300)
}
```

### 6.4 内容切换策略

**无交叉淡化，瞬间切换**：
- 数据通过 Vue reactive 替换
- DOM 瞬间更新（无 transition）
- 用户感知：弹窗"飞"到新位置，内容瞬间刷新

## 七、定位逻辑

### 7.1 自动适配方向

```javascript
function calculatePosition(triggerEl, preferredPlacement = 'auto', offset = 16) {
  // 处理 display: contents 的 trigger
  let actualTrigger = triggerEl
  const style = window.getComputedStyle(triggerEl)
  if (style.display === 'contents' && triggerEl.firstElementChild) {
    actualTrigger = triggerEl.firstElementChild
  }
  
  const triggerRect = actualTrigger.getBoundingClientRect()
  const popoverEl = getPopoverElement() // 获取当前弹窗 DOM
  const popoverWidth = popoverEl.offsetWidth
  const popoverHeight = popoverEl.offsetHeight
  
  const viewportPadding = 12
  const placements = preferredPlacement === 'auto' 
    ? ['bottom', 'top', 'right', 'left'] 
    : [preferredPlacement]
  
  // 遍历候选方向，找到不超出视口的
  for (const placement of placements) {
    const { top, left } = computePosition(placement, triggerRect, popoverWidth, popoverHeight, offset)
    if (isInViewport(top, left, popoverWidth, popoverHeight, viewportPadding)) {
      state.position = { top, left }
      state.actualPlacement = placement
      return
    }
  }
  
  // 回退：bottom 并限制在视口内
  fallbackToBottom(triggerRect, popoverWidth, popoverHeight, offset, viewportPadding)
}
```

### 7.2 地块弹窗特殊处理

- trigger 为绝对定位的 1×1px div
- 点击时计算六边形中心坐标，设置 div 的 left/top
- offset 设为 32（比默认 16 更远）
- clickOutsideExclude: '.hover-overlay'（点击 overlay 不关闭）

## 八、替换策略（重点）

### 8.1 必须分派多 Agents 执行

**原因**：
- GameView.vue 中共有 **44 个 `<Popover>` 实例**
- 涉及 **玩家面板、游戏区域-回合信息、游戏区域-科学能力、游戏版图** 四大区域
- 每个区域的触发逻辑、数据结构、特殊处理不同
- 单 Agent 容易遗漏或出错

### 8.2 分片方案

**Agent 1：玩家面板区域（~22 个 Popover）**
- 规划卡（active + passed 玩家）
- 宫殿板块（active + passed 玩家）
- 派系徽章（active + passed 玩家）
- 分数（active + passed 玩家）
- 统计项（active + passed 玩家的所有资源/建筑/魔法）
- **特殊处理**：统计项在 `v-for` 中，需要提取为独立方法

**Agent 2：游戏区域-回合信息（~10 个 Popover）**
- 6 个回合计分板
- 回合助推板（bonusColumns）

**Agent 3：游戏区域-科学能力（~8 个 Popover）**
- 科学板块（scienceTilesOrder，条件渲染 v-if/else）
- 能力板块（abilityTilesOrder）
- 信仰轨道点击区（TRACK_TYPES）

**Agent 4：游戏版图-地块弹窗（1 个 Popover）**
- 地块明细弹窗
- **特殊处理**：1×1px trigger div、toggle 行为、clickOutsideExclude

**Agent 5：整合与清理**
- 在 GameView.vue 顶部引入 `<GlobalPopover />`
- 删除所有 `import Popover from...` 和 `import PopoverContent from...`
- 删除旧文件（Popover.vue、PopoverContent.vue、usePopoverPosition.js）
- 全局搜索确保无遗漏

### 8.3 每个 Agent 的执行步骤

```
1. 阅读目标区域的现有 Popover 代码
2. 提取每个 Popover 的：
   - trigger 元素（slot 内容）
   - PopoverContent 的 props（imageContainerStyle, imageLayerStyle, name, aspectRatio 等）
   - Popover 的 props（placement, width, offset, clickOutsideExclude）
3. 编写 handleXXXClick(event, item) 方法
4. 将 <Popover>...</Popover> 替换为 <div @click="handleXXXClick($event, item)">...</div>
5. 移除 template #content
6. 测试：确保触发器样式不变，点击后调用 globalPopover.open()
```

### 8.4 协作规范

- **统一的 globalPopover 导入**：每个 Agent 在 GameView.vue 的 script setup 顶部添加
  ```javascript
  import { useGlobalPopover } from '../composables/useGlobalPopover.js'
  const globalPopover = useGlobalPopover()
  ```
- **统一的 triggerId 命名规范**：`{type}-{playerId}-{itemId}`，如 `planning-0-3`
- **数据准备**：提前准备所有 sprite style getter 函数（getPlanningCardPreviewStyle、getPalacePreviewStyle 等），Agent 直接调用

## 九、测试计划

### 9.1 功能测试

| 测试项 | 预期行为 |
|--------|----------|
| 点击规划卡 | 弹窗显示在规划卡下方/上方，显示图片+明细 |
| 点击宫殿板块 | 弹窗显示宫殿板块预览 |
| 点击派系徽章 | 弹窗显示派系大图 |
| 点击分数 | 弹窗显示分数明细（纯明细模式） |
| 点击资源/建筑统计 | 弹窗显示对应明细 |
| 点击回合计分板 | 弹窗显示回合预览 |
| 点击助推板 | 弹窗显示助推板预览 |
| 点击科学板块 | 弹窗显示科学板块预览 |
| 点击能力板块 | 弹窗显示能力板块预览 |
| 点击轨道 | 弹窗显示轨道明细（纯明细模式） |
| 点击地块 | 弹窗显示地块明细，trigger 在六边形中心 |
| 再次点击同一元素 | 弹窗关闭（toggle） |
| 点击元素 A 后点击元素 B | 弹窗平滑移动到 B，内容瞬间切换 |
| 点击外部 | 弹窗关闭 |
| 地块 overlay 点击 | 不触发关闭（clickOutsideExclude 生效） |

### 9.2 动画测试

| 测试项 | 预期行为 |
|--------|----------|
| 首次打开 | fade-in（opacity + scale） |
| 切换目标 | 位置平滑平移（300ms），内容瞬间切换，无 fade |
| 关闭 | fade-out（opacity + scale） |
| 快速连续点击不同元素 | 弹窗连续平滑移动，不闪烁 |

### 9.3 回归测试

- 玩家面板折叠/展开后，点击触发器仍能正确定位
- 窗口大小变化后，新点击的元素能正确计算位置
- 页面滚动后，新点击的元素能正确计算位置（不跟随滚动）

## 十、版本变更记录

```markdown
## 本次修改

- **日期**: 2026-04-27
- **分支**: main
- **影响范围**: frontend/src/views/GameView.vue, frontend/src/components/, frontend/src/composables/
- **更新内容**:
  - feat: 新增全局单例弹窗系统（useGlobalPopover + GlobalPopover + GlobalPopoverContent）
  - refactor: 将 44 个分散的 Popover 实例统一替换为全局单例调用
  - refactor: 移除旧 Popover 组件（Popover.vue、PopoverContent.vue、usePopoverPosition.js）
  - ui: 弹窗切换时支持位置平滑平移 + 内容瞬间切换
  - ui: 保持现有内容占位（明细列表为占位条目）
- **验证方式**:
  - 手动测试所有触发点（玩家面板、回合信息、科学能力、地块）
  - 验证 toggle 行为（再次点击关闭）
  - 验证切换动画（位置平移 + 内容瞬间切换）
  - 验证点击外部关闭 + 地块 overlay 排除
```

## 十一、风险与回滚方案

### 11.1 风险点

1. **44 个触发点遗漏**：某处 `<Popover>` 未替换导致编译错误或运行时错误
2. **定位偏移**：新定位逻辑与旧逻辑存在细微差异
3. **动画不流畅**：切换时内容或位置跳动

### 11.2 回滚方案

- 所有修改在 Git 分支中进行
- 保留旧文件直到验收完成再删除
- 若出现问题，可快速回滚到旧 Popover 组件

## 十二、实施 checklist

- [ ] 创建 Git 分支 `refactor/global-popover`
- [ ] 新建 `useGlobalPopover.js`
- [ ] 新建 `GlobalPopover.vue`
- [ ] 新建 `GlobalPopoverContent.vue`
- [ ] **Agent 1**：替换玩家面板所有 Popover
- [ ] **Agent 2**：替换回合信息所有 Popover
- [ ] **Agent 3**：替换科学能力所有 Popover
- [ ] **Agent 4**：替换地块弹窗
- [ ] **Agent 5**：整合、删除旧文件、全局检查
- [ ] 功能测试（所有触发点）
- [ ] 动画测试（打开、切换、关闭）
- [ ] 更新 `docs/version-change-log.md`
- [ ] Git commit & merge

---

**文档状态**: 规划完成，等待执行
**最后更新**: 2026-04-27
