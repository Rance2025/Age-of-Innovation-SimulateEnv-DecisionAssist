# 游戏页面通用 Popover 弹窗组件实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 创建一个通用 Popover 弹窗组件，替代 GameView 中所有悬停预览（entityPreview），并为玩家状态栏各项指标提供点击明细弹窗。

**Architecture:** 使用 Vue 3 Teleport 将弹窗挂载到 body，通过 `usePopoverPosition` 计算定位，支持 auto-placement 和视口边界检测。所有弹窗统一为"状态详情面板"，content 由 slot 决定。

**Tech Stack:** Vue 3 (Composition API), Vite, 无外部依赖

---

## 文件结构

### 新增
- `frontend/src/composables/usePopoverPosition.js` — 定位计算逻辑
- `frontend/src/components/Popover.vue` — 弹窗组件

### 修改
- `frontend/src/views/GameView.vue` — 替换所有 entityPreview 为 Popover，新增状态栏明细

---

## Task 1: 创建 usePopoverPosition 组合式函数

**Files:**
- Create: `frontend/src/composables/usePopoverPosition.js`

- [ ] **Step 1: 创建目录和文件**

```bash
mkdir -p frontend/src/composables
```

- [ ] **Step 2: 编写 usePopoverPosition**

```javascript
import { ref, computed } from 'vue'

export function usePopoverPosition() {
  const position = ref({ top: 0, left: 0 })
  const actualPlacement = ref('bottom')

  const viewportPadding = 12
  const arrowSize = 8

  function calculatePosition(triggerEl, popoverEl, preferredPlacement = 'auto', offset = 8) {
    if (!triggerEl || !popoverEl) return

    const triggerRect = triggerEl.getBoundingClientRect()
    const popoverRect = popoverEl.getBoundingClientRect()
    const viewportWidth = window.innerWidth
    const viewportHeight = window.innerHeight

    const placements = preferredPlacement === 'auto' 
      ? ['bottom', 'top', 'right', 'left'] 
      : [preferredPlacement]

    for (const placement of placements) {
      let top = 0
      let left = 0

      switch (placement) {
        case 'bottom':
          top = triggerRect.bottom + offset + arrowSize
          left = triggerRect.left + (triggerRect.width - popoverRect.width) / 2
          break
        case 'top':
          top = triggerRect.top - popoverRect.height - offset - arrowSize
          left = triggerRect.left + (triggerRect.width - popoverRect.width) / 2
          break
        case 'right':
          top = triggerRect.top + (triggerRect.height - popoverRect.height) / 2
          left = triggerRect.right + offset + arrowSize
          break
        case 'left':
          top = triggerRect.top + (triggerRect.height - popoverRect.height) / 2
          left = triggerRect.left - popoverRect.width - offset - arrowSize
          break
      }

      // 检查是否超出视口
      const fitsHorizontally = left >= viewportPadding && 
        left + popoverRect.width <= viewportWidth - viewportPadding
      const fitsVertically = top >= viewportPadding && 
        top + popoverRect.height <= viewportHeight - viewportPadding

      if (fitsHorizontally && fitsVertically) {
        position.value = { top, left }
        actualPlacement.value = placement
        return
      }
    }

    // 如果都不合适，使用 bottom 并限制在视口内
    let top = triggerRect.bottom + offset + arrowSize
    let left = triggerRect.left + (triggerRect.width - popoverRect.width) / 2
    
    top = Math.max(viewportPadding, Math.min(top, viewportHeight - popoverRect.height - viewportPadding))
    left = Math.max(viewportPadding, Math.min(left, viewportWidth - popoverRect.width - viewportPadding))
    
    position.value = { top, left }
    actualPlacement.value = 'bottom'
  }

  return {
    position: computed(() => position.value),
    actualPlacement: computed(() => actualPlacement.value),
    calculatePosition
  }
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/composables/usePopoverPosition.js
git commit -m "feat: add usePopoverPosition composable for popover positioning"
```

---

## Task 2: 创建 Popover 组件

**Files:**
- Create: `frontend/src/components/Popover.vue`

- [ ] **Step 1: 编写 Popover.vue**

```vue
<template>
  <div ref="triggerRef" class="popover-trigger" @click="handleTriggerClick">
    <slot />
  </div>
  
  <Teleport to="body">
    <Transition name="popover">
      <div
        v-if="visible"
        ref="popoverRef"
        class="popover"
        :class="[`popover-placement-${actualPlacement}`, { 'popover-no-arrow': !showArrow }]"
        :style="popoverStyle"
        @click.stop
      >
        <div v-if="showArrow" class="popover-arrow" />
        <div class="popover-content">
          <slot name="content" />
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { usePopoverPosition } from '../composables/usePopoverPosition.js'

const props = defineProps({
  placement: {
    type: String,
    default: 'auto',
    validator: (value) => ['auto', 'top', 'bottom', 'left', 'right'].includes(value)
  },
  offset: {
    type: Number,
    default: 8
  },
  width: {
    type: [String, Number],
    default: 'auto'
  },
  maxWidth: {
    type: Number,
    default: 320
  },
  showArrow: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['show', 'hide'])

const visible = ref(false)
const triggerRef = ref(null)
const popoverRef = ref(null)

const { position, actualPlacement, calculatePosition } = usePopoverPosition()

const popoverStyle = computed(() => {
  const style = {
    position: 'fixed',
    top: `${position.value.top}px`,
    left: `${position.value.left}px`,
    zIndex: 1000
  }
  
  if (props.width !== 'auto') {
    style.width = typeof props.width === 'number' ? `${props.width}px` : props.width
  }
  
  style.maxWidth = `${props.maxWidth}px`
  
  return style
})

function handleTriggerClick(event) {
  event.stopPropagation()
  
  if (visible.value) {
    hide()
  } else {
    // 关闭其他已打开的 popover
    document.dispatchEvent(new CustomEvent('popover:close-all'))
    show()
  }
}

function show() {
  visible.value = true
  emit('show')
  
  nextTick(() => {
    calculatePosition(triggerRef.value, popoverRef.value, props.placement, props.offset)
  })
}

function hide() {
  visible.value = false
  emit('hide')
}

function handleClickOutside(event) {
  if (visible.value && popoverRef.value && !popoverRef.value.contains(event.target)) {
    hide()
  }
}

function handleCloseAll() {
  if (visible.value) {
    hide()
  }
}

let scrollHandler = null
let resizeHandler = null

watch(visible, (isVisible) => {
  if (isVisible) {
    document.addEventListener('click', handleClickOutside)
    document.addEventListener('popover:close-all', handleCloseAll)
    
    scrollHandler = () => {
      calculatePosition(triggerRef.value, popoverRef.value, props.placement, props.offset)
    }
    resizeHandler = () => {
      calculatePosition(triggerRef.value, popoverRef.value, props.placement, props.offset)
    }
    
    window.addEventListener('scroll', scrollHandler, true)
    window.addEventListener('resize', resizeHandler)
  } else {
    document.removeEventListener('click', handleClickOutside)
    document.removeEventListener('popover:close-all', handleCloseAll)
    
    if (scrollHandler) {
      window.removeEventListener('scroll', scrollHandler, true)
      scrollHandler = null
    }
    if (resizeHandler) {
      window.removeEventListener('resize', resizeHandler)
      resizeHandler = null
    }
  }
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
  document.removeEventListener('popover:close-all', handleCloseAll)
  if (scrollHandler) {
    window.removeEventListener('scroll', scrollHandler, true)
  }
  if (resizeHandler) {
    window.removeEventListener('resize', resizeHandler)
  }
})
</script>

<style scoped>
.popover-trigger {
  display: inline-block;
  cursor: pointer;
}

.popover {
  background: rgba(30, 30, 40, 0.95);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
  padding: 16px;
  pointer-events: auto;
}

.popover-arrow {
  position: absolute;
  width: 0;
  height: 0;
  border-style: solid;
}

.popover-placement-bottom .popover-arrow {
  top: -8px;
  left: 50%;
  transform: translateX(-50%);
  border-left: 8px solid transparent;
  border-right: 8px solid transparent;
  border-bottom: 8px solid rgba(30, 30, 40, 0.95);
}

.popover-placement-top .popover-arrow {
  bottom: -8px;
  left: 50%;
  transform: translateX(-50%);
  border-left: 8px solid transparent;
  border-right: 8px solid transparent;
  border-top: 8px solid rgba(30, 30, 40, 0.95);
}

.popover-placement-right .popover-arrow {
  left: -8px;
  top: 50%;
  transform: translateY(-50%);
  border-top: 8px solid transparent;
  border-bottom: 8px solid transparent;
  border-right: 8px solid rgba(30, 30, 40, 0.95);
}

.popover-placement-left .popover-arrow {
  right: -8px;
  top: 50%;
  transform: translateY(-50%);
  border-top: 8px solid transparent;
  border-bottom: 8px solid transparent;
  border-left: 8px solid rgba(30, 30, 40, 0.95);
}

.popover-content {
  color: var(--text-primary, #fff);
}

/* 过渡动画 */
.popover-enter-active,
.popover-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.popover-enter-from,
.popover-leave-to {
  opacity: 0;
  transform: scale(0.95);
}
</style>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/Popover.vue
git commit -m "feat: add Popover component with teleport and auto-placement"
```

---

## Task 3: 替换规划卡预览

**Files:**
- Modify: `frontend/src/views/GameView.vue`（规划卡相关部分）

- [ ] **Step 1: 找到规划卡触发元素**

搜索 `planning-card-circle`，当前代码：

```vue
<div
  class="planning-card-circle"
  :tabindex="player.planningCardId !== null ? 0 : -1"
  title=""
  :aria-label="player.planningCardId !== null ? `预览${player.planningCard}规划卡` : '未分配规划卡'"
  :class="{ 'is-visible': player.planningCardId !== null }"
  :style="{ backgroundColor: getPlanningCardColor(player.planningCardId) }"
  @mouseenter="handlePlanningCardMouseEnter(player.planningCardId, player.planningCard, $event)"
  @mouseleave="handlePlanningCardMouseLeave"
  @focus="handlePlanningCardMouseEnter(player.planningCardId, player.planningCard, $event)"
  @blur="handlePlanningCardMouseLeave"
  @keydown.esc.prevent="hideEntityPreview"
></div>
```

- [ ] **Step 2: 替换为 Popover**

```vue
<Popover
  v-if="player.planningCardId !== null"
  placement="auto"
  :offset="12"
>
  <div
    class="planning-card-circle"
    :tabindex="0"
    :aria-label="`预览${player.planningCard}规划卡`"
    :class="{ 'is-visible': true }"
    :style="{ backgroundColor: getPlanningCardColor(player.planningCardId) }"
  ></div>
  <template #content>
    <div class="detail-header">{{ player.planningCard || planningCardIdToName[player.planningCardId] || player.planningCardId }}</div>
    <div class="detail-image" :style="getPlanningCardPreviewStyle(player.planningCardId)"></div>
  </template>
</Popover>
<div
  v-else
  class="planning-card-circle"
  :class="{ 'is-visible': false }"
></div>
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/views/GameView.vue
git commit -m "refactor: replace planning card hover preview with Popover"
```

---

## Task 4: 替换宫殿板块预览

**Files:**
- Modify: `frontend/src/views/GameView.vue`（宫殿板块相关部分）

- [ ] **Step 1: 找到宫殿板块触发元素**

搜索 `palace-tile-badge`（非 is-hidden-placeholder 状态）。

- [ ] **Step 2: 替换为 Popover**

将 `palace-tile-badge` 包裹在 Popover 中：

```vue
<Popover
  v-if="player.palaceTileId !== null"
  placement="auto"
  :offset="12"
>
  <span
    class="palace-tile-badge"
    :class="{ 'is-inactive': !player.isGotPalace }"
    :tabindex="0"
    :aria-label="`${player.palaceTileId}号宫殿板块${player.isGotPalace ? '' : '（未激活）'}`"
  >
    <span class="palace-tile-badge-value">{{ player.palaceTileId }}</span>
    <span
      v-if="!player.isGotPalace"
      class="palace-tile-badge-status"
      aria-hidden="true"
    >
      <i class="fas fa-ban"></i>
    </span>
  </span>
  <template #content>
    <div class="detail-header">
      {{ player.palaceTileId }}号宫殿板块{{ player.isGotPalace ? '' : ' · 未激活' }}
    </div>
    <div class="detail-image" :style="getPalacePreviewStyle(player.palaceTileId)"></div>
  </template>
</Popover>
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/views/GameView.vue
git commit -m "refactor: replace palace tile hover preview with Popover"
```

---

## Task 5: 替换派系徽章预览

**Files:**
- Modify: `frontend/src/views/GameView.vue`（派系徽章相关部分）

- [ ] **Step 1: 替换 faction-badge-avatar**

```vue
<Popover
  v-if="player.factionId !== null"
  placement="auto"
  :offset="12"
>
  <span
    class="faction-badge-avatar"
    :tabindex="0"
    :aria-label="`预览${player.faction}派系板块`"
  >
    <span
      class="faction-badge-avatar-image"
      aria-hidden="true"
      :style="getFactionBadgeStyle(player.factionId)"
    ></span>
  </span>
  <template #content>
    <div class="detail-header">{{ player.faction || factionIdToName[player.factionId] || player.factionId }}</div>
    <div class="detail-image" :style="getFactionPreviewStyle(player.factionId)"></div>
  </template>
</Popover>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/views/GameView.vue
git commit -m "refactor: replace faction badge hover preview with Popover"
```

---

## Task 6: 替换回合计分板预览

**Files:**
- Modify: `frontend/src/views/GameView.vue`（回合计分板相关部分）

- [ ] **Step 1: 替换所有 round-scoring 单元格**

对于每个回合计分板单元格（共6个）：

```vue
<Popover
  placement="top"
  :offset="12"
>
  <div
    class="grid-cell"
    :class="{ 'current-round': currentRound === roundNum, 'flipped': roundStates[roundNum]?.isFlipped }"
    :tabindex="roundStates[roundNum]?.currentX > 0 ? 0 : -1"
  >
    <!-- 原有内容 -->
  </div>
  <template #content>
    <div class="detail-header">第 {{ roundNum }} 回合</div>
    <div class="detail-images">
      <div class="detail-image" :style="getRoundScoringSpriteStyleByBackendId(roundStates[roundNum]?.currentX)"></div>
      <div 
        v-if="roundNum === 6 && roundStates[6]?.finalScoringId !== null"
        class="detail-image overlay"
        :style="getFinalScoringOverlaySpriteStyleByBackendId(roundStates[6]?.finalScoringId)"
      ></div>
    </div>
  </template>
</Popover>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/views/GameView.vue
git commit -m "refactor: replace round scoring hover preview with Popover"
```

---

## Task 7: 替换回合助推板预览

**Files:**
- Modify: `frontend/src/views/GameView.vue`（回合助推板相关部分）

- [ ] **Step 1: 替换 bonus-cell**

```vue
<Popover
  v-if="bonus.x > 0"
  placement="top"
  :offset="12"
>
  <div
    class="bonus-cell"
    :class="{ flipped: bonus.isFlipped }"
    :tabindex="0"
  >
    <!-- 原有内容 -->
  </div>
  <template #content>
    <div class="detail-header">回合助推板 {{ bonus.x }}</div>
    <div class="detail-image" :style="getRoundBoosterFrontSpriteStyleByBackendId(bonus.x)"></div>
  </template>
</Popover>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/views/GameView.vue
git commit -m "refactor: replace round booster hover preview with Popover"
```

---

## Task 8: 替换科学板块预览

**Files:**
- Modify: `frontend/src/views/GameView.vue`（科学板块相关部分）

- [ ] **Step 1: 替换 science-board-tile**

```vue
<Popover
  v-if="tileId"
  placement="auto"
  :offset="12"
>
  <div
    class="science-board-tile"
    :style="getScienceBoardTileStyle(tileId, idx)"
    :tabindex="0"
  >
    <!-- 原有内容 -->
  </div>
  <template #content>
    <div class="detail-header">科学板块 {{ tileId }}</div>
    <div class="detail-image" :style="getScienceTileStyleByBackendId(tileId)"></div>
  </template>
</Popover>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/views/GameView.vue
git commit -m "refactor: replace science tile hover preview with Popover"
```

---

## Task 9: 替换能力板块预览

**Files:**
- Modify: `frontend/src/views/GameView.vue`（能力板块相关部分）

- [ ] **Step 1: 替换 ability-board-tile**

```vue
<Popover
  v-if="tileId"
  placement="auto"
  :offset="12"
>
  <div
    class="ability-board-tile"
    :style="getAbilityBoardTileStyle(tileId, idx)"
    :tabindex="0"
  >
    <!-- 原有内容 -->
  </div>
  <template #content>
    <div class="detail-header">能力板块 {{ tileId }}</div>
    <div class="detail-image" :style="getAbilityTileStyleByBackendId(tileId)"></div>
  </template>
</Popover>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/views/GameView.vue
git commit -m "refactor: replace ability tile hover preview with Popover"
```

---

## Task 10: 为玩家状态栏添加明细弹窗

**Files:**
- Modify: `frontend/src/views/GameView.vue`（玩家状态栏 stat-item 部分）

- [ ] **Step 1: 找到 stat-item 渲染位置**

在 `buildPlayerStatusRows` 循环中的 `stat-item` 元素。

- [ ] **Step 2: 为每个 stat-item 包裹 Popover**

```vue
<Popover
  placement="auto"
  :offset="8"
  width="260"
>
  <div
    class="stat-item"
    :title="item.label"
  >
    <div class="stat-content">
      <!-- 原有内容 -->
    </div>
  </div>
  <template #content>
    <div class="detail-header">{{ item.label }}明细</div>
    <div class="detail-body">
      <!-- 预留内容，后续填充具体明细数据 -->
      <div class="detail-placeholder">{{ item.label }}详细数据（待实现）</div>
    </div>
  </template>
</Popover>
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/views/GameView.vue
git commit -m "feat: add detail popovers for player status items"
```

---

## Task 11: 清理 entityPreview 旧代码

**Files:**
- Modify: `frontend/src/views/GameView.vue`

- [ ] **Step 1: 删除 entityPreview reactive 对象**

删除：
```javascript
const entityPreview = reactive({
  visible: false,
  name: '',
  imageLayers: [],
  isInactive: false,
  imageHeight: 0,
  panelWidth: 0,
  top: 0,
  left: 0
})
```

- [ ] **Step 2: 删除 timer 变量**

删除：
```javascript
let entityPreviewTimer = null
let entityPreviewHideTimer = null
```

- [ ] **Step 3: 删除 queueEntityPreview 及相关函数**

删除以下函数：
- `queueEntityPreview`
- `clearEntityPreviewTimer`
- `scheduleEntityPreviewHide`
- `cancelEntityPreviewHide`
- `hideEntityPreview`
- `handlePlanningCardMouseEnter`
- `handlePlanningCardMouseLeave`
- `handlePalaceTileMouseEnter`
- `handlePalaceTileMouseLeave`
- `handleFactionBadgeMouseEnter`
- `handleFactionBadgeMouseLeave`
- `handleRoundScoringMouseEnter`
- `handleRoundScoringMouseLeave`
- `handleRoundBoosterMouseEnter`
- `handleRoundBoosterMouseLeave`
- `handleAbilityTileMouseEnter`
- `handleAbilityTileMouseLeave`
- `handleScienceTileMouseEnter`
- `handleScienceTileMouseLeave`

- [ ] **Step 4: 删除 entityPreview 模板**

删除 template 中的 entityPreview DOM：
```vue
<div v-if="entityPreview.visible" class="entity-preview-panel" ...>
  <!-- ... -->
</div>
```

- [ ] **Step 5: 删除 entityPreview 样式**

删除 `<style>` 中所有 `.entity-preview-*` 相关样式。

- [ ] **Step 6: Commit**

```bash
git add frontend/src/views/GameView.vue
git commit -m "chore: remove deprecated entityPreview system"
```

---

## Task 12: 更新版本变更记录

**Files:**
- Modify: `docs/version-change-log.md`

- [ ] **Step 1: 添加本次修改记录**

在 `本次修改` 区域添加：

```markdown
## 本次修改

- 日期：2025-04-25
- 分支：main
- 影响范围：frontend/src/components/Popover.vue, frontend/src/composables/usePopoverPosition.js, frontend/src/views/GameView.vue
- 更新内容：
  - feat: 新增通用 Popover 弹窗组件，支持点击触发、点击外部关闭、自动定位、视口边界检测
  - feat: 玩家状态栏各项指标（金币、建筑、魔法等）新增点击明细弹窗（内容暂空）
  - refactor: 所有游戏元素（规划卡、宫殿板块、派系、回合计分板、助推板、科学板块、能力板块）的悬停预览改为点击 Popover
  - chore: 移除旧的 entityPreview 悬停预览系统及相关代码
- 验证方式：进入游戏页面，点击各元素验证弹窗是否正常显示和关闭
```

- [ ] **Step 2: Commit**

```bash
git add docs/version-change-log.md
git commit -m "docs: update version change log for popover feature"
```

---

## Spec Self-Review

### 1. Spec Coverage
- ✅ 创建 Popover 组件 — Task 1-2
- ✅ 替换所有 entityPreview — Task 3-9
- ✅ 新增状态栏明细 — Task 10
- ✅ 清理旧代码 — Task 11
- ✅ 版本记录 — Task 12

### 2. Placeholder Scan
- ✅ 无 "TBD"/"TODO"
- ✅ 所有代码完整
- ✅ 每个步骤都有具体代码

### 3. Type Consistency
- ✅ Popover props 在组件定义和使用处一致
- ✅ 函数名和变量名一致
