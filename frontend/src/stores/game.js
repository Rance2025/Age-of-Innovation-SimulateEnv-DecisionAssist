import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useGameStore = defineStore('game', () => {
  // State
  const settings = ref(null)
  const isPlaying = ref(false)
  const currentRound = ref(1)
  const players = ref([])

  // Getters
  const gameState = computed(() => {
    if (isPlaying.value) return 'playing'
    if (settings.value) return 'setup'
    return 'home'
  })

  // Actions
  function setSettings(newSettings) {
    settings.value = newSettings
    localStorage.setItem('gameSettings', JSON.stringify(newSettings))
  }

  function startGame() {
    isPlaying.value = true
    localStorage.setItem('gameInProgress', 'true')
  }

  function endGame() {
    isPlaying.value = false
    localStorage.removeItem('gameInProgress')
  }

  function resetGame() {
    settings.value = null
    isPlaying.value = false
    currentRound.value = 1
    players.value = []
    localStorage.removeItem('gameSettings')
    localStorage.removeItem('gameInProgress')
  }

  function loadFromStorage() {
    const savedSettings = localStorage.getItem('gameSettings')
    const savedProgress = localStorage.getItem('gameInProgress')

    if (savedSettings) {
      settings.value = JSON.parse(savedSettings)
    }
    if (savedProgress === 'true') {
      isPlaying.value = true
    }
  }

  return {
    settings,
    isPlaying,
    currentRound,
    players,
    gameState,
    setSettings,
    startGame,
    endGame,
    resetGame,
    loadFromStorage
  }
})
