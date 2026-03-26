<template>
  <div class="hero" @click="startGame">
    <div class="hero-content">
      <div class="hero-title">
        <span class="title-cn">大创造时代</span>
        <span class="title-divider"></span>
        <span class="title-en">Age of Innovation</span>
      </div>

      <p class="hero-description">
        在这个前所未有的创新纪元，策略与想象力交织，创造无限可能。我们正站在历史与未来的交汇点，每一次决策都将重塑世界。
      </p>

      <div class="hero-keywords">
        <span>探索</span>
        <span class="keyword-dot">•</span>
        <span>建造</span>
        <span class="keyword-dot">•</span>
        <span>征服</span>
      </div>

      <p class="hero-hint">
        点击任意位置开始游戏
      </p>
    </div>

    <!-- 背景装饰 -->
    <div class="hero-bg">
      <div class="bg-grid"></div>
      <div class="bg-glow"></div>
    </div>

    <!-- 浮动元素 -->
    <div class="floating-elements">
      <div class="float-item float-1"><i class="fas fa-cube"></i></div>
      <div class="float-item float-2"><i class="fas fa-coins"></i></div>
      <div class="float-item float-3"><i class="fas fa-user"></i></div>
      <div class="float-item float-4"><i class="fas fa-university"></i></div>
      <div class="float-item float-5"><i class="fas fa-city"></i></div>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { useGameStore } from '../stores/game'

const router = useRouter()
const gameStore = useGameStore()

function startGame() {
  const state = gameStore.gameState
  if (state === 'playing') {
    router.push('/game')
  } else {
    gameStore.resetGame()
    router.push('/setup')
  }
}
</script>
