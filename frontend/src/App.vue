<template>
  <div id="app">
    <NavBar />
    <main class="main-content">
      <router-view v-slot="{ Component, route }">
        <transition name="page" mode="out-in">
          <component :is="Component" :key="route.path" />
        </transition>
      </router-view>
    </main>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import NavBar from './components/NavBar.vue'
import { useGameStore } from './stores/game'

const gameStore = useGameStore()

onMounted(() => {
  gameStore.loadFromStorage()
})
</script>

<style>
.main-content {
  padding-top: 56px;
  min-height: 100vh;
}

/* 页面统一缓入缓出效果 - 纯渐变 */
.page-enter-active,
.page-leave-active {
  transition: opacity 0.2s cubic-bezier(0.25, 0.1, 0.25, 1);
}

.page-enter-from,
.page-leave-to {
  opacity: 0;
}
</style>
