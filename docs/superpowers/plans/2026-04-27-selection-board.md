# 初选板块卡片实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在游戏区域新增第4个卡片"初选板块"，展示本局可用的规划卡、派系、宫殿板块图片

**Architecture:** 在 GameView.vue 的 game-grid 中添加新的 game-card，复用现有的图片预览样式函数和折叠卡片机制。采用上中下三栏布局，每栏横向排列图片。

**Tech Stack:** Vue 3, CSS, 现有 sprite 图片系统

---

## 文件结构

- **Modify:** `frontend/src/views/GameView.vue` — 添加卡片模板、数据绑定、样式
- **Modify:** `docs/version-change-log.md` — 记录版本变更

---

## Task 1: 添加卡片模板和折叠状态

**Files:**
- Modify: `frontend/src/views/GameView.vue`

**Context:**
- 现有卡片使用 `collapsedCards` reactive 对象管理折叠状态（line 2185）
- 现有3个卡片：map、round、tactical
- 需要添加第4个：draft（初选板块）

- [ ] **Step 1: 添加 draft 到 collapsedCards 初始化**

```javascript
// Line 2185 附近
const collapsedCards = reactive({ map: false, round: false, tactical: false, draft: false })
```

- [ ] **Step 2: 在 game-grid 中插入第4个卡片模板**

在"科学能力卡片"（tactical）之后、game-grid 结束之前插入：

```html
<!-- 初选板块卡片 -->
<div class="game-card" :class="{ collapsed: collapsedCards['draft'] }">
  <div class="game-header" @click="toggleCard('draft')">
    <div class="game-header-left">
      <div class="game-title">
        <i class="fas fa-hand-pointer"></i>
        <span>初选板块</span>
      </div>
    </div>
    <div class="game-indicator">
      <i class="fas fa-chevron-down"></i>
    </div>
  </div>
  <div class="draft-board-status">
    <div class="draft-board-content">
      <!-- 规划卡栏 -->
      <div class="draft-section">
        <div class="draft-section-title">规划卡</div>
        <div class="draft-section-items">
          <div
            v-for="cardId in gameStateStore.setup.selected_planning_cards"
            :key="`draft-planning-${cardId}`"
            class="draft-item"
          >
            <div
              class="draft-item-image"
              :style="getPlanningCardPreviewStyle(cardId)"
            ></div>
          </div>
        </div>
      </div>
      <!-- 派系栏 -->
      <div class="draft-section">
        <div class="draft-section-title">派系</div>
        <div class="draft-section-items">
          <div
            v-for="factionId in gameStateStore.setup.selected_factions"
            :key="`draft-faction-${factionId}`"
            class="draft-item"
          >
            <div
              class="draft-item-image"
              :style="getFactionPreviewStyle(factionId)"
            ></div>
          </div>
        </div>
      </div>
      <!-- 宫殿板块栏 -->
      <div class="draft-section">
        <div class="draft-section-title">宫殿板块</div>
        <div class="draft-section-items">
          <div
            v-for="palaceId in gameStateStore.setup.selected_palace_tiles"
            :key="`draft-palace-${palaceId}`"
            class="draft-item"
          >
            <div
              class="draft-item-image"
              :style="getPalacePreviewStyle(palaceId)"
            ></div>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>
```

---

## Task 2: 添加 CSS 样式

**Files:**
- Modify: `frontend/src/views/GameView.vue`（在 style 区域添加）

**Context:**
- 现有 .game-card 样式定义在约 line 8028
- .game-card.collapsed 样式在约 line 8046
- 需要添加初选板块特有的样式

- [ ] **Step 1: 添加初选板块内容区样式**

在 style 区域（约 line 8600 附近，其他 game-status 样式之后）添加：

```css
/* 初选板块卡片 */
.draft-board-status {
  padding: 16px;
  min-height: 0;
}

.draft-board-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.draft-section {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.draft-section-title {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text-secondary);
  padding-left: 4px;
}

.draft-section-items {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.draft-item {
  flex-shrink: 0;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
}

.draft-item-image {
  width: var(--draft-item-width);
  height: var(--draft-item-height);
  background-repeat: no-repeat;
  background-position: center;
  background-size: cover;
}

/* 规划卡尺寸 */
.draft-section:nth-child(1) .draft-item-image {
  --draft-item-width: 88px;
  --draft-item-height: 139px;
}

/* 派系尺寸 */
.draft-section:nth-child(2) .draft-item-image {
  --draft-item-width: 160px;
  --draft-item-height: 91px;
}

/* 宫殿板块尺寸 */
.draft-section:nth-child(3) .draft-item-image {
  --draft-item-width: 140px;
  --draft-item-height: 73px;
}

/* 折叠状态 */
.game-card.collapsed .draft-board-status {
  display: none;
}
```

---

## Task 3: 更新版本变更文档

**Files:**
- Modify: `docs/version-change-log.md`

- [ ] **Step 1: 在文档顶部添加本次修改记录**

```markdown
## 本次修改

- **日期**: 2026-04-27
- **分支**: main
- **影响范围**: frontend/src/views/GameView.vue
- **更新内容**:
  - `feat: 在游戏区域新增初选板块卡片，展示本局可用的规划卡、派系、宫殿板块图片`
  - `ui: 采用上中下三栏布局，每栏横向排列对应板块图片`
  - `ui: 卡片支持折叠/展开，与现有游戏卡片交互一致`
- **验证方式**:
  - 启动游戏后，游戏区域显示"初选板块"卡片
  - 卡片正确展示本局的规划卡、派系、宫殿板块图片
  - 卡片可折叠/展开
```

---

## 自我审查

**1. Spec coverage:**
- ✅ 上中下三栏布局 — Task 1 模板中三个 draft-section
- ✅ 每栏横向排列 — Task 2 中 draft-section-items 使用 flex + wrap
- ✅ 不可点击 — 没有添加任何 @click 事件
- ✅ 不显示标记 — 没有添加玩家标记元素
- ✅ 可折叠 — 复用现有 collapsedCards 机制

**2. Placeholder scan:**
- ✅ 无 TBD/TODO/占位符

**3. Type consistency:**
- ✅ 使用现有函数：getPlanningCardPreviewStyle、getFactionPreviewStyle、getPalacePreviewStyle
- ✅ 使用现有数据：gameStateStore.setup.selected_planning_cards 等

---

## 验证清单

- [ ] 初选板块卡片显示在游戏区域
- [ ] 三栏布局正确（规划卡/派系/宫殿板块）
- [ ] 每栏图片横向排列
- [ ] 图片尺寸合理，无变形
- [ ] 卡片可折叠/展开
- [ ] 折叠状态下内容隐藏
- [ ] 无 JavaScript 错误
