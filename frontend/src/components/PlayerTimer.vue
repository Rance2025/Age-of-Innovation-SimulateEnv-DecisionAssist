<template>
  <div
    class="player-timer"
    :class="{
      'is-compact': !isExpanded,
      'is-expanded': isExpanded,
      'is-current-action-player': isCurrentPlayer,
      'is-warning': progress > 0.1 && progress <= 0.3,
      'is-danger': progress > 0 && progress <= 0.1
    }"
    :title="isExpanded ? '点击切换为简洁模式' : '点击切换为扇面倒计时'"
    @click.stop="toggleMode"
  >
    <template v-if="!isExpanded">
      <span class="timer-text">{{ displayTime }}</span>
    </template>

    <template v-else>
      <div class="timer-pie-container">
        <svg class="timer-pie-svg" viewBox="0 0 36 36">
          <circle
            class="timer-pie-bg"
            cx="18"
            cy="18"
            r="14"
            fill="none"
            stroke="currentColor"
            stroke-width="3"
          />
          <circle
            v-if="hasVisibleProgress"
            class="timer-pie-progress"
            cx="18"
            cy="18"
            r="14"
            fill="none"
            stroke="currentColor"
            stroke-width="3"
            :stroke-dasharray="strokeDasharray"
            :stroke-dashoffset="strokeDashoffset"
            stroke-linecap="round"
            transform="rotate(-90 18 18)"
          />
        </svg>
        <span class="timer-pie-percentage">{{ expandedDisplayText }}</span>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useTimerStore } from '../stores/timer'

const props = defineProps({
  playerId: {
    type: Number,
    required: true
  },
  currentPlayerId: {
    type: Number,
    required: true
  }
})

const timerStore = useTimerStore()
const isExpanded = ref(false)

const isCurrentPlayer = computed(() => props.playerId === props.currentPlayerId)
const displayTime = computed(() => (
  timerStore.getPlayerTimerDisplay(props.playerId, props.currentPlayerId)
))
const progress = computed(() => (
  timerStore.getPlayerTimerProgress(props.playerId, props.currentPlayerId)
))
const expandedDisplayText = computed(() => (
  timerStore.getPlayerExpandedDisplay(props.playerId, props.currentPlayerId)
))
const hasVisibleProgress = computed(() => progress.value > 0)

function toggleMode() {
  isExpanded.value = !isExpanded.value
}

const CIRCLE_RADIUS = 14
const circumference = 2 * Math.PI * CIRCLE_RADIUS

const strokeDashoffset = computed(() => (
  circumference * (1 - progress.value)
))

const strokeDasharray = `${circumference}`
</script>

<style scoped>
.player-timer {
  font-family: 'SF Mono', 'Menlo', 'Monaco', 'Consolas', 'Liberation Mono', 'Courier New', monospace;
  font-weight: 600;
  cursor: pointer;
  user-select: none;
  transition: all 0.3s ease;
}

.player-timer.is-compact {
  font-size: 0.9rem;
  color: #9ca3af;
  letter-spacing: 0.02em;
  width: 50px;
  text-align: right;
  display: inline-flex;
  align-items: center;
  justify-content: flex-end;
}

.player-timer.is-compact.is-current-action-player {
  color: #ffffff;
}

.player-timer.is-expanded {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.timer-pie-container {
  position: relative;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.timer-pie-svg {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
}

.timer-pie-bg {
  color: rgba(156, 163, 175, 0.2);
}

.timer-pie-progress {
  color: #4ade80;
  transition:
    stroke-dashoffset 0.3s ease,
    color 0.2s ease;
}

.player-timer.is-expanded.is-warning .timer-pie-progress {
  color: #fbbf24;
}

.player-timer.is-expanded.is-danger .timer-pie-progress {
  color: #ef4444;
}

.timer-pie-percentage {
  position: relative;
  z-index: 1;
  font-size: 0.65rem;
  font-weight: 700;
  color: #ffffff;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
}
</style>
