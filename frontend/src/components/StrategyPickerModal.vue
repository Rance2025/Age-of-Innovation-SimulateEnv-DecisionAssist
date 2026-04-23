<script setup>
/**
 * StrategyPickerModal - 策略选择弹窗组件
 * 
 * 用于统一展示策略选择界面，可在多处复用：
 * - 游戏内控制中台的策略选择
 * - 初始设置页面为AI选择策略
 * 
 * 使用方法:
 * <StrategyPickerModal
 *   v-model="modalOpen"
 *   title="选择策略"
 *   :selected-strategy="currentStrategyId"
 *   @select="handleStrategySelect"
 * />
 */

import { computed } from 'vue'
import Modal from './Modal.vue'
import { SELECTABLE_STRATEGY_GROUPS, STRATEGY_OPTIONS } from '../constants/strategies.js'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  title: {
    type: String,
    default: '选择策略'
  },
  selectedStrategy: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['update:modelValue', 'select'])

const isOpen = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

// 选择策略（点击后只切换选中状态，不关闭弹窗，允许二次点击取消）
function selectStrategy(strategyId) {
  if (!STRATEGY_OPTIONS.some((strategy) => strategy.id === strategyId)) {
    return
  }
  // 如果点击已选中的策略，则取消选择
  if (props.selectedStrategy === strategyId) {
    emit('select', '')
  } else {
    emit('select', strategyId)
  }
}
</script>

<template>
  <Modal
    v-model="isOpen"
    :title="title"
    size="default"
    :show-close="true"
    :close-on-overlay="true"
  >
    <div class="strategy-picker">
      <div class="strategy-picker-body">
        <!-- 三列布局容器 -->
        <div class="strategy-columns">
          <!-- 策略分组列 -->
          <div
            v-for="group in SELECTABLE_STRATEGY_GROUPS"
            :key="group.id"
            class="strategy-column"
          >
            <!-- 分组标题栏 -->
            <div class="column-header">
              <div class="column-icon">
                <i :class="group.icon || 'fas fa-layer-group'"></i>
              </div>
              <div class="column-title">
                <div class="column-name">{{ group.label }}</div>
                <div v-if="group.description" class="column-desc">
                  {{ group.description }}
                </div>
              </div>
            </div>
            
            <!-- 策略选项列表 -->
            <div class="column-options">
              <button
                v-for="strategy in group.options"
                :key="strategy.id"
                type="button"
                class="strategy-card"
                :class="{ 
                  'is-selected': selectedStrategy === strategy.id,
                  'is-disabled': strategy.isAvailable === false
                }"
                :disabled="strategy.isAvailable === false"
                @click="selectStrategy(strategy.id)"
              >
                <!-- 左侧图标区域 - 标签式布局 -->
                <div class="card-icon-section">
                  <div class="card-icon">
                    <i :class="strategy.icon || 'fas fa-chess-pawn'"></i>
                  </div>
                </div>
                
                <!-- 右侧内容区域 -->
                <div class="card-content-section">
                  <div class="card-text">
                    <div class="card-name">{{ strategy.label }}</div>
                    <div v-if="strategy.description" class="card-desc">
                      {{ strategy.description }}
                    </div>
                  </div>
                  
                  <!-- 选中状态通过左侧图标区域高亮表示，无需对勾 -->
                </div>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </Modal>
</template>

<style scoped>
.strategy-picker {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.strategy-picker-body {
  flex: 1;
  padding: 24px 32px 32px;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

/* 三列布局容器 */
.strategy-columns {
  display: flex;
  flex: 1;
  min-height: 0;
}

/* 单列容器 */
.strategy-column {
  flex: 1;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  padding: 0 20px;
  border-right: 1px solid rgba(255, 255, 255, 0.08);
  min-width: 0; /* 防止flex子项收缩 */
}

/* 策略卡片 */
.strategy-card {
  flex-shrink: 0;
  width: 100%;
  position: relative;
  display: flex;
  align-items: stretch;
  padding: 0;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.04);
  cursor: pointer;
  transition: all 0.2s ease;
  text-align: left;
  overflow: hidden;
}

/* 列选项列表 */
.column-options {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
  overflow-y: auto;
  min-height: 0;
}

/* 三列布局容器 */
.strategy-columns {
  display: flex;
  flex: 1;
  min-height: 0;
}

/* 单列容器 */
.strategy-column {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 0 20px;
  border-right: 1px solid rgba(255, 255, 255, 0.08);
  overflow: hidden;
}

.strategy-column:first-child {
  padding-left: 0;
}

.strategy-column:last-child {
  padding-right: 0;
  border-right: none;
}

/* 列标题栏 - 简洁标题样式，非卡片 */
.column-header {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 0 16px;
  margin-bottom: 16px;
  border-bottom: 2px solid rgba(255, 255, 255, 0.1);
}

.column-icon {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--accent, #6366f1);
  font-size: 1.25rem;
  flex-shrink: 0;
}

.column-title {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.column-name {
  color: rgba(255, 255, 255, 0.95);
  font-size: 1rem;
  font-weight: 700;
  line-height: 1.3;
}

.column-desc {
  color: rgba(255, 255, 255, 0.45);
  font-size: 0.8rem;
  font-weight: 400;
  line-height: 1.4;
}

/* 列选项列表 */
.column-options {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
  overflow-y: auto;
  padding: 0 1px;
  min-height: 0;
}

/* 隐藏滚动条但保留功能 */
.column-options::-webkit-scrollbar {
  width: 0px;
  background: transparent;
}

.column-options::-webkit-scrollbar-thumb {
  background: transparent;
}

/* Firefox 完全隐藏滚动条 */
.column-options {
  scrollbar-width: none;
  -ms-overflow-style: none;
}

/* 策略卡片 */
.strategy-card {
  position: relative;
  display: flex;
  align-items: stretch;
  padding: 0;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.04);
  cursor: pointer;
  transition: all 0.2s ease;
  text-align: left;
  overflow: hidden;
}

.strategy-card:hover {
  border-color: rgba(255, 255, 255, 0.2);
  background: rgba(255, 255, 255, 0.08);
}

.strategy-card.is-selected {
  border-color: var(--accent, #6366f1);
  box-shadow: 0 0 0 1px rgba(99, 102, 241, 0.3);
}

.strategy-card.is-selected:hover {
  background: rgba(255, 255, 255, 0.08);
}

/* 禁用状态 */
.strategy-card.is-disabled {
  opacity: 0.5;
  cursor: not-allowed;
  filter: grayscale(0.5);
}

.strategy-card.is-disabled:hover {
  border-color: rgba(255, 255, 255, 0.1);
  background: rgba(255, 255, 255, 0.04);
}

.strategy-card.is-disabled .card-name {
  color: rgba(255, 255, 255, 0.5);
}

.strategy-card.is-disabled .card-desc {
  color: rgba(255, 255, 255, 0.3);
}

.strategy-card.is-disabled .card-icon {
  color: rgba(255, 255, 255, 0.3);
}

/* 左侧图标区域 - 更深的背景色，参考游戏模式卡片 */
.card-icon-section {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 56px;
  min-width: 56px;
  background: rgba(0, 0, 0, 0.25);
  padding: 14px 0;
}

.card-icon {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(255, 255, 255, 0.6);
  font-size: 1rem;
}

.strategy-card:hover .card-icon-section {
  background: rgba(0, 0, 0, 0.35);
}

.strategy-card.is-selected .card-icon-section {
  background: var(--accent, #6366f1);
}

.strategy-card.is-selected .card-icon {
  color: white;
}

/* 右侧内容区域 */
.card-content-section {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 12px 14px;
  min-width: 0;
}

.card-text {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.card-name {
  color: rgba(255, 255, 255, 0.9);
  font-size: 0.8rem;
  font-weight: 600;
  line-height: 1.3;
}

.card-desc {
  color: rgba(255, 255, 255, 0.5);
  font-size: 0.68rem;
  font-weight: 400;
  line-height: 1.35;
}

.strategy-card.is-selected .card-name {
  color: white;
}

.strategy-card.is-selected .card-desc {
  color: rgba(255, 255, 255, 0.7);
}

/* 焦点状态 */
.strategy-card:focus-visible {
  outline: none;
  box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.5);
}

/* 响应式 - 移动端改为单列 */
@media (max-width: 640px) {
  .strategy-columns {
    grid-template-columns: 1fr;
  }
  
  .strategy-column {
    padding: 0;
    border-right: none;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    padding-bottom: 16px;
    margin-bottom: 16px;
  }
  
  .strategy-column:last-child {
    border-bottom: none;
    padding-bottom: 0;
    margin-bottom: 0;
  }
  
  .strategy-picker-body {
    padding: 16px 20px 20px;
  }
}
</style>
