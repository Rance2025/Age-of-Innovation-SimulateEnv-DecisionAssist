<template>
  <div
    class="action-timer"
    :class="{
      'is-byo-yomi': isByoYomi,
      'is-warning': isWarning,
      'is-danger': isDanger,
      'is-timeout': isTimeout
    }"
  >
    <template v-if="!isByoYomi">
      <span class="timer-text main-time">{{ displayTime }}</span>
    </template>

    <template v-else>
      <div class="timer-circle">
        <svg class="timer-svg" viewBox="0 0 36 36">
          <circle
            class="timer-circle-bg"
            cx="18"
            cy="18"
            r="16"
            fill="none"
            stroke="currentColor"
            stroke-width="3"
          />
          <circle
            v-if="hasVisibleProgress"
            class="timer-circle-progress"
            cx="18"
            cy="18"
            r="16"
            fill="none"
            stroke="currentColor"
            stroke-width="3"
            :stroke-dasharray="strokeDasharray"
            :stroke-dashoffset="strokeDashoffset"
            stroke-linecap="round"
            transform="rotate(-90 18 18)"
          />
        </svg>
        <span class="timer-text byo-yomi-time">{{ displayTime }}</span>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useTimerStore } from '../stores/timer'

const timerStore = useTimerStore()

const isByoYomi = computed(() => timerStore.isByoYomi)
const displayTime = computed(() => timerStore.displayTime)
const progress = computed(() => timerStore.byoYomiProgress)
const hasVisibleProgress = computed(() => progress.value > 0)
const isWarning = computed(() => (
  isByoYomi.value && progress.value > 0.1 && progress.value <= 0.3
))
const isDanger = computed(() => (
  isByoYomi.value && progress.value > 0 && progress.value <= 0.1
))
const isTimeout = computed(() => (
  isByoYomi.value && progress.value <= 0
))

const CIRCLE_RADIUS = 16
const circumference = 2 * Math.PI * CIRCLE_RADIUS

const strokeDashoffset = computed(() => (
  circumference * (1 - progress.value)
))

const strokeDasharray = `${circumference}`
</script>

<style scoped>
.action-timer {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-family: 'SF Mono', 'Menlo', 'Monaco', 'Consolas', 'Liberation Mono', 'Courier New', monospace;
  font-weight: 600;
}

.timer-text.main-time {
  font-size: 1.1em;
  color: #e0e0e0;
  letter-spacing: 0.05em;
}

.timer-circle {
  position: relative;
  width: 42px;
  height: 42px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.timer-svg {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
}

.timer-circle-bg {
  color: rgba(255, 255, 255, 0.15);
}

.timer-circle-progress {
  color: #4ade80;
  transition:
    stroke-dashoffset 0.1s linear,
    color 0.2s ease;
}

.timer-text.byo-yomi-time {
  font-size: 0.85em;
  color: #4ade80;
  z-index: 1;
}

.action-timer.is-warning .timer-circle-progress,
.action-timer.is-warning .timer-text.byo-yomi-time {
  color: #fbbf24;
  animation: pulse 1s ease-in-out infinite;
}

.action-timer.is-danger .timer-circle-progress,
.action-timer.is-danger .timer-text.byo-yomi-time,
.action-timer.is-timeout .timer-circle-progress,
.action-timer.is-timeout .timer-text.byo-yomi-time {
  color: #ef4444;
}

@keyframes pulse {
  0%,
  100% {
    opacity: 1;
  }

  50% {
    opacity: 0.6;
  }
}
</style>
