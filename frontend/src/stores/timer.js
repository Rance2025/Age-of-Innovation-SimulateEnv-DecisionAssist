import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

function normalizeMilliseconds(value) {
  const normalized = Number(value)
  if (!Number.isFinite(normalized)) {
    return 0
  }

  return Math.max(0, normalized)
}

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value))
}

function formatMMSS(ms) {
  const normalized = normalizeMilliseconds(ms)
  if (normalized <= 0) {
    return '00:00'
  }

  const totalSeconds = Math.ceil(normalized / 1000)
  const minutes = Math.floor(totalSeconds / 60)
  const seconds = totalSeconds % 60
  return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`
}

export const useTimerStore = defineStore('timer', () => {
  const actionDeadline = ref(0)
  const currentPlayerRemaining = ref(0)
  const allPlayersRemaining = ref([])
  const mainTimeLimit = ref(0)
  const byoYomiTimeLimit = ref(0)

  const now = ref(Date.now())
  let timerInterval = null

  const hasActiveDeadline = computed(() => actionDeadline.value > 0)
  const remaining = computed(() => (
    hasActiveDeadline.value
      ? Math.max(0, actionDeadline.value - now.value)
      : 0
  ))
  const isByoYomi = computed(() => (
    hasActiveDeadline.value && currentPlayerRemaining.value <= 0
  ))
  const mainTimeRemaining = computed(() => (
    isByoYomi.value ? 0 : remaining.value
  ))
  const byoYomiRemaining = computed(() => (
    isByoYomi.value ? remaining.value : 0
  ))

  const displayTime = computed(() => (
    isByoYomi.value
      ? String(Math.max(0, Math.ceil(byoYomiRemaining.value / 1000)))
      : formatMMSS(mainTimeRemaining.value)
  ))
  const byoYomiProgress = computed(() => {
    if (!isByoYomi.value || byoYomiTimeLimit.value <= 0) {
      return 0
    }

    return clamp(byoYomiRemaining.value / byoYomiTimeLimit.value, 0, 1)
  })

  function startLocalTimer() {
    stopLocalTimer()

    if (actionDeadline.value <= 0) {
      return
    }

    now.value = Date.now()
    timerInterval = setInterval(() => {
      now.value = Date.now()

      if (remaining.value <= 0) {
        stopLocalTimer()
      }
    }, 100)
  }

  function stopLocalTimer() {
    if (!timerInterval) {
      return
    }

    clearInterval(timerInterval)
    timerInterval = null
  }

  function syncLocalTimer() {
    if (actionDeadline.value > 0) {
      startLocalTimer()
      return
    }

    stopLocalTimer()
  }

  function applyTimerState(timerState) {
    if ('action_deadline' in timerState) {
      actionDeadline.value = normalizeMilliseconds(timerState.action_deadline)
    }

    if ('current_player_remaining' in timerState) {
      currentPlayerRemaining.value = normalizeMilliseconds(timerState.current_player_remaining)
    }

    if ('all_players_remaining' in timerState) {
      allPlayersRemaining.value = Array.isArray(timerState.all_players_remaining)
        ? timerState.all_players_remaining.map(normalizeMilliseconds)
        : []
    }

    if ('main_time_limit' in timerState) {
      mainTimeLimit.value = normalizeMilliseconds(timerState.main_time_limit)
    }

    if ('byo_yomi_time_limit' in timerState) {
      byoYomiTimeLimit.value = normalizeMilliseconds(timerState.byo_yomi_time_limit)
    }
  }

  function updateFromTimerState(timerState) {
    if (!timerState || typeof timerState !== 'object') {
      return
    }

    applyTimerState(timerState)
    syncLocalTimer()
  }

  function getStoredPlayerRemaining(playerId) {
    return normalizeMilliseconds(allPlayersRemaining.value[playerId])
  }

  function getPlayerMainTimeRemaining(playerId, currentPlayerId) {
    if (playerId !== currentPlayerId) {
      return getStoredPlayerRemaining(playerId)
    }

    return isByoYomi.value ? 0 : mainTimeRemaining.value
  }

  function getPlayerTimerDisplay(playerId, currentPlayerId) {
    return formatMMSS(getPlayerMainTimeRemaining(playerId, currentPlayerId))
  }

  function getPlayerTimerProgress(playerId, currentPlayerId) {
    if (mainTimeLimit.value <= 0) {
      return 0
    }

    return clamp(
      getPlayerMainTimeRemaining(playerId, currentPlayerId) / mainTimeLimit.value,
      0,
      1
    )
  }

  function getPlayerExpandedDisplay(playerId, currentPlayerId) {
    return `${Math.round(getPlayerTimerProgress(playerId, currentPlayerId) * 100)}%`
  }

  function reset() {
    stopLocalTimer()

    actionDeadline.value = 0
    currentPlayerRemaining.value = 0
    allPlayersRemaining.value = []
    mainTimeLimit.value = 0
    byoYomiTimeLimit.value = 0
  }

  function dispose() {
    stopLocalTimer()
  }

  return {
    isByoYomi,
    displayTime,
    byoYomiProgress,

    updateFromTimerState,
    reset,
    dispose,
    getPlayerTimerDisplay,
    getPlayerTimerProgress,
    getPlayerExpandedDisplay
  }
})
