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
      <div class="timer-byoyomi-row">
        <span class="timer-text byo-yomi-time">{{ displayTime }}</span>
        <div class="timer-pie">
          <svg class="timer-pie-svg" viewBox="0 0 36 36">
            <!-- 底色完整圆 -->
            <circle
              class="timer-pie-bg"
              cx="18"
              cy="18"
              r="16"
              fill="currentColor"
            />
            <!-- 进度扇形 -->
            <path
              v-if="hasVisibleProgress"
              class="timer-pie-progress"
              :d="sectorPath"
              fill="currentColor"
            />
          </svg>
        </div>
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

function polarToCartesian(cx, cy, radius, angleInDegrees) {
  const angleInRadians = (angleInDegrees - 90) * Math.PI / 180.0
  return {
    x: cx + (radius * Math.cos(angleInRadians)),
    y: cy + (radius * Math.sin(angleInRadians))
  }
}

function getSectorPath(cx, cy, r, startAngle, endAngle) {
  const start = polarToCartesian(cx, cy, r, endAngle)
  const end = polarToCartesian(cx, cy, r, startAngle)
  const largeArcFlag = endAngle - startAngle <= 180 ? '0' : '1'
  return [
    'M', cx, cy,
    'L', start.x, start.y,
    'A', r, r, 0, largeArcFlag, 0, end.x, end.y,
    'Z'
  ].join(' ')
}

const sectorPath = computed(() => {
  const angle = progress.value * 360
  return getSectorPath(18, 18, 16, 0, angle)
})
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

.timer-byoyomi-row {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.timer-pie {
  width: 36px;
  height: 36px;
  flex-shrink: 0;
}

.timer-pie-svg {
  width: 100%;
  height: 100%;
}

.timer-pie-bg {
  color: rgba(255, 255, 255, 0.15);
}

.timer-pie-progress {
  color: #4ade80;
  transition:
    d 0.1s linear,
    color 0.2s ease;
}

.timer-text.byo-yomi-time {
  font-size: 0.85em;
  color: #4ade80;
}

.action-timer.is-warning .timer-pie-progress,
.action-timer.is-warning .timer-text.byo-yomi-time {
  color: #fbbf24;
  animation: pulse 1s ease-in-out infinite;
}

.action-timer.is-danger .timer-pie-progress,
.action-timer.is-danger .timer-text.byo-yomi-time,
.action-timer.is-timeout .timer-pie-progress,
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