<template>
  <nav class="navbar">
    <div class="nav-container">
      <div class="nav-left">
        <div class="nav-logo">
          <span>Age of Innovation</span>
          <span class="divider">|</span>
          <span class="subtitle">大创造时代</span>
        </div>
        <div class="nav-menu">
          <!-- 动态返回按钮：根据状态返回不同页面 -->
          <a
            class="nav-item"
            :class="{ active: isGameRoute }"
            @click="handleGameClick"
          >
            <i class="fas fa-play"></i>
            <span>{{ gameStatusText }}</span>
          </a>
          <a
            class="nav-item"
            :class="{ active: $route.name === 'History' }"
            @click="handleHistoryClick"
          >
            <i class="fas fa-history"></i>
            <span>历史对局</span>
          </a>
        </div>
      </div>
      <div class="nav-right">
        <!-- 预留右侧区域 -->
      </div>
    </div>
  </nav>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useGameStore } from '../stores/game'
import { useNavigationStore } from '../stores/navigation'

const route = useRoute()
const router = useRouter()
const gameStore = useGameStore()
const navStore = useNavigationStore()

const isGameRoute = computed(() =>
  ['Home', 'Setup', 'Game'].includes(route.name)
)

// 根据游戏状态显示不同文字
const gameStatusText = computed(() => {
  // 如果在游戏页面，显示"游戏中…"
  if (route.name === 'Game') return '游戏中…'
  // 如果在设置页面，显示"初始中…"
  if (route.name === 'Setup') return '初始中…'
  // 如果在历史页面，检查来源页面
  if (route.name === 'History') {
    const source = navStore.getHistorySource()
    if (source === 'Setup') return '初始中…'
    if (source === 'Game') return '游戏中…'
  }
  // 默认显示"开始游戏"
  return '开始游戏'
})

// 点击游戏按钮：根据当前路由决定行为
function handleGameClick() {
  // 如果已经在游戏相关路由，不执行任何操作
  if (route.name === 'Game' || route.name === 'Setup' || route.name === 'Home') {
    return
  }

  if (route.name === 'History') {
    // 从历史页面返回：回到之前的页面
    const source = navStore.getHistorySource()
    router.push({ name: source })
  }
}

// 点击历史按钮：记录当前页面，然后跳转
function handleHistoryClick() {
  // 如果已经在历史页面，不执行任何操作
  if (route.name === 'History') return

  // 记录从哪个页面跳转过来的
  navStore.setHistorySource(route.name)
  router.push('/history')
}
</script>

<style scoped>
.navbar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 56px;
  background: rgba(10, 10, 10, 0.95);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid var(--border);
  z-index: 1000;
}

.nav-container {
  width: 100%;
  height: 100%;
  padding: 0 48px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.nav-left {
  display: flex;
  align-items: center;
  gap: 0;
}

.nav-logo {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--text-primary);
  user-select: none;
  margin-right: 48px;
}

.nav-logo .divider {
  color: var(--text-secondary);
  font-weight: 400;
}

.nav-logo .subtitle {
  font-size: 0.95rem;
  font-weight: 500;
}

.nav-menu {
  display: flex;
  align-items: center;
  gap: 32px;
}

.nav-item {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 0 4px;
  height: 56px;
  color: var(--text-secondary);
  text-decoration: none;
  font-size: 0.9rem;
  font-weight: 500;
  line-height: 1;
  transition: color 0.2s;
  cursor: pointer;
  position: relative;
  min-width: 84px;
}

.nav-item:hover {
  color: var(--text-primary);
}

.nav-item i {
  font-size: 0.85rem;
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
}

.nav-item.active {
  color: #4D9EFF;
}

.nav-item.active::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: #4D9EFF;
  border-radius: 1px 1px 0 0;
}

.nav-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

@media (max-width: 768px) {
  .nav-container {
    padding: 0 24px;
  }

  .nav-logo {
    margin-right: 24px;
  }

  .nav-menu {
    gap: 16px;
  }

  .nav-item span {
    display: none;
  }

  .nav-item {
    padding: 8px;
    min-width: auto;
  }
}
</style>
