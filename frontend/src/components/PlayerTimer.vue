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
    :title="timerTitle"
    @click.stop="toggleMode"
  >
    <div class="player-timer-shell">
      <span
        class="timer-text"
        :class="{ 'is-visible': isTextVisible }"
        :aria-hidden="!isTextVisible"
      >
        {{ displayTime }}
      </span>

      <div
        class="timer-pie-container"
        :class="{ 'is-visible': isRingVisible }"
        :aria-hidden="!isRingVisible"
      >
        <svg class="timer-pie-svg" viewBox="0 0 36 36">
          <circle
            class="timer-pie-bg"
            cx="18"
            cy="18"
            :r="CIRCLE_RADIUS"
            fill="none"
            stroke="currentColor"
            :stroke-width="CIRCLE_STROKE_WIDTH"
          />
          <circle
            v-if="hasVisibleProgress"
            class="timer-pie-progress"
            cx="18"
            cy="18"
            :r="CIRCLE_RADIUS"
            fill="none"
            stroke="currentColor"
            :stroke-width="PROGRESS_STROKE_WIDTH"
            :stroke-dasharray="strokeDasharray"
            :stroke-dashoffset="strokeDashoffset"
            stroke-linecap="round"
            transform="rotate(-90 18 18)"
          />
        </svg>
        <span class="timer-pie-content">
          <span class="timer-pie-value">{{ expandedDisplayValue }}</span>
        </span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onUnmounted, ref } from 'vue'
import { useTimerStore } from '../stores/timer'
import { useGlobalPopover } from '../composables/useGlobalPopover.js'

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
const globalPopover = useGlobalPopover()
const visibleMode = ref('compact')
const transitionPhase = ref('idle')

let fadeOutTimerId = null
let fadeInTimerId = null
let fadeInFrameId = null

const isCurrentPlayer = computed(() => props.playerId === props.currentPlayerId)
const isExpanded = computed(() => visibleMode.value === 'expanded')
const displayTime = computed(() => (
  timerStore.getPlayerTimerDisplay(props.playerId, props.currentPlayerId)
))
const progress = computed(() => (
  timerStore.getPlayerTimerProgress(props.playerId, props.currentPlayerId)
))
const expandedDisplayValue = computed(() => (
  String(Math.round(progress.value * 100))
))
const hasVisibleProgress = computed(() => progress.value > 0)
const timerTitle = computed(() => (
  isExpanded.value ? '点击切换为简洁模式' : '点击切换为扇面倒计时'
))
const isTextVisible = computed(() => (
  visibleMode.value === 'compact'
  && transitionPhase.value !== 'fading-out'
  && transitionPhase.value !== 'pre-fade-in'
))
const isRingVisible = computed(() => (
  visibleMode.value === 'expanded'
  && transitionPhase.value !== 'fading-out'
  && transitionPhase.value !== 'pre-fade-in'
))

function toggleMode() {
  globalPopover.close()

  if (transitionPhase.value !== 'idle') {
    return
  }

  const nextMode = visibleMode.value === 'expanded' ? 'compact' : 'expanded'
  transitionPhase.value = 'fading-out'

  clearTransitionHandles()

  fadeOutTimerId = window.setTimeout(() => {
    fadeOutTimerId = null
    visibleMode.value = nextMode
    transitionPhase.value = 'pre-fade-in'

    fadeInFrameId = window.requestAnimationFrame(() => {
      fadeInFrameId = null
      transitionPhase.value = 'fading-in'
      fadeInTimerId = window.setTimeout(() => {
        transitionPhase.value = 'idle'
        fadeInTimerId = null
      }, MODE_FADE_DURATION_MS)
    })
  }, MODE_FADE_DURATION_MS)
}

function clearTransitionHandles() {
  if (fadeOutTimerId !== null) {
    window.clearTimeout(fadeOutTimerId)
    fadeOutTimerId = null
  }

  if (fadeInTimerId !== null) {
    window.clearTimeout(fadeInTimerId)
    fadeInTimerId = null
  }

  if (fadeInFrameId !== null) {
    window.cancelAnimationFrame(fadeInFrameId)
    fadeInFrameId = null
  }
}

onUnmounted(() => {
  clearTransitionHandles()
})

const CIRCLE_RADIUS = 13.5
const CIRCLE_STROKE_WIDTH = 4
const PROGRESS_STROKE_WIDTH = 3.6
const MODE_FADE_DURATION_MS = 200
const circumference = 2 * Math.PI * CIRCLE_RADIUS

const strokeDashoffset = computed(() => (
  circumference * (1 - progress.value)
))

const strokeDasharray = `${circumference}`
</script>

<style scoped>
.player-timer {
  --player-timer-slot-width: 50px;
  --player-timer-slot-height: 34px;
  --player-timer-ring-size: 29px;
  font-family: 'SF Mono', 'Menlo', 'Monaco', 'Consolas', 'Liberation Mono', 'Courier New', monospace;
  font-weight: 600;
  cursor: pointer;
  user-select: none;
  transition: color 0.2s ease;
  width: var(--player-timer-slot-width);
  height: var(--player-timer-slot-height);
  display: inline-flex;
  align-items: center;
}

.player-timer-shell {
  position: relative;
  width: 100%;
  height: 100%;
}

.player-timer.is-compact {
  font-size: 0.9rem;
  color: #9ca3af;
  letter-spacing: 0.02em;
}

.timer-text,
.timer-pie-container {
  position: absolute;
  inset: 0;
  margin: auto;
  align-items: center;
  justify-content: center;
  display: flex;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.timer-text.is-visible,
.timer-pie-container.is-visible {
  opacity: 1;
}

.timer-text {
  text-align: center;
}

.player-timer.is-compact.is-current-action-player {
  color: #ffffff;
}

.timer-pie-container {
  width: var(--player-timer-ring-size);
  height: var(--player-timer-ring-size);
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

.timer-pie-content {
  position: relative;
  z-index: 1;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
  color: #ffffff;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
}

.timer-pie-value {
  display: block;
  font-size: 0.76rem;
  font-weight: 700;
  letter-spacing: -0.04em;
  line-height: 1;
}
</style>
