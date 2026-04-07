import { createRouter, createWebHistory } from 'vue-router'
import { useGameStore } from '../stores/game'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('../views/HomeView.vue'),
    meta: { title: '大创造时代 | Age of Innovation' }
  },
  {
    path: '/setup',
    name: 'Setup',
    component: () => import('../views/SetupView.vue'),
    meta: { title: '游戏设置 | Age of Innovation' }
  },
  {
    path: '/game',
    name: 'Game',
    component: () => import('../views/GameView.vue'),
    meta: { title: '对局信息面板 | Age of Innovation' }
  },
  {
    path: '/history',
    name: 'History',
    component: () => import('../views/HistoryView.vue'),
    meta: { title: '历史对局 | Age of Innovation' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 检查后端是否重启，返回 { restarted: boolean, serverStartTime: number }
async function checkServerRestart() {
  try {
    const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:5001'
    const response = await fetch(`${apiBaseUrl}/api/server/info`)
    if (response.ok) {
      const data = await response.json()
      const serverStartTime = data.start_time
      const savedServerTime = localStorage.getItem('serverStartTime')

      // 如果服务器启动时间变化了，说明后端重启了
      if (savedServerTime && savedServerTime !== String(serverStartTime)) {
        return { restarted: true, serverStartTime }
      }

      // 保存服务器启动时间
      if (!savedServerTime) {
        localStorage.setItem('serverStartTime', serverStartTime)
      }
    }
  } catch (e) {
    // 服务器可能还没启动，忽略错误
  }
  return { restarted: false, serverStartTime: null }
}

router.beforeEach(async (to, from, next) => {
  if (to.meta.title) {
    document.title = to.meta.title
  }

  // 检查是否是页面刷新（from.name为undefined表示是首次加载）
  const isPageRefresh = !from.name

  // 只有在页面刷新时才检查后端是否重启
  if (isPageRefresh) {
    const { restarted, serverStartTime } = await checkServerRestart()
    if (restarted) {
      // 后端重启了，清理游戏状态（localStorage + Pinia store）
      localStorage.removeItem('gameInProgress')
      localStorage.removeItem('gameSettings')
      localStorage.setItem('serverStartTime', serverStartTime)

      // 重置 Pinia store
      const gameStore = useGameStore()
      gameStore.resetGame()

      // 如果当前不在首页，重定向到首页
      if (to.path !== '/') {
        next('/')
        return
      }
    }
  }

  next()
})

export default router
