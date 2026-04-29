<template>
  <div class="history-page">
    <div class="history-container">
      <!-- 头部区域 -->
      <div class="history-header">
        <div class="header-left">
          <h1 class="history-title">历史对局</h1>
          <span class="history-count">共 {{ pagination.total }} 局</span>
        </div>
        <div class="header-right">
          <!-- 排序选择 -->
          <div class="custom-select-wrapper">
            <div
              class="custom-select"
              :class="{ active: sortDropdownOpen }"
              @click="toggleSortDropdown"
            >
              <span>{{ sortOptions.find((o) => o.value === sortBy)?.label }}</span>
              <i class="fas fa-chevron-down"></i>
            </div>
            <div class="custom-select-dropdown" :class="{ active: sortDropdownOpen }">
              <div
                v-for="option in sortOptions"
                :key="option.value"
                class="custom-select-option"
                :class="{ active: sortBy === option.value }"
                @click="selectSortOption(option)"
              >
                <span>{{ option.label }}</span>
                <i class="fas fa-check"></i>
              </div>
            </div>
          </div>
          <!-- 正序倒序按钮 -->
          <button class="order-btn" title="切换排序方向" @click="toggleSortOrder">
            <i :class="sortOrder === 'desc' ? 'fas fa-arrow-down' : 'fas fa-arrow-up'"></i>
          </button>
          <!-- 筛选按钮 -->
          <div class="filter-wrapper">
            <button
              class="filter-btn"
              :class="{ active: filterPopupOpen || hasActiveFilters }"
              @click="toggleFilterPopup"
            >
              <i class="fas fa-filter"></i>
              <span>筛选</span>
            </button>
            <!-- 筛选弹窗 -->
            <div class="filter-popup" :class="{ active: filterPopupOpen }">
              <div class="filter-section">
                <div class="filter-title">搜索对局</div>
                <div class="filter-search-box">
                  <i class="fas fa-search"></i>
                  <input v-model="searchQuery" type="text" placeholder="输入关键词..." />
                </div>
              </div>
              <div class="filter-section">
                <div class="filter-title">玩家数量</div>
                <div class="filter-options">
                  <label
                    v-for="num in [2, 3, 4, 5]"
                    :key="num"
                    class="filter-option"
                    :class="{ active: selectedPlayerCounts.includes(num) }"
                  >
                    <input v-model="selectedPlayerCounts" type="checkbox" :value="num" />
                    <span>{{ num }}人</span>
                  </label>
                </div>
              </div>
              <div class="filter-actions">
                <button class="filter-clear" @click="clearFilters">重置</button>
                <button class="filter-apply" @click="applyFilters">应用</button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="history-body">
        <!-- 对局列表 -->
        <div v-if="loading" class="empty-state history-feedback">
          <i class="fas fa-spinner fa-spin"></i>
          <p>加载中...</p>
        </div>

        <div v-else-if="error" class="empty-state history-feedback">
          <i class="fas fa-exclamation-circle"></i>
          <p>{{ error }}</p>
        </div>

        <div v-else-if="games.length === 0 && deletingGameIds.length === 0" class="empty-state history-feedback">
          <i class="fas fa-inbox"></i>
          <p>暂无历史对局</p>
        </div>

        <template v-else>
          <div class="games-scroll-area">
            <TransitionGroup
              name="history-list"
              tag="div"
              class="games-list"
              @before-leave="pinLeavingGameCard"
            >
              <div
                v-for="game in games"
                :key="game.id"
                class="game-card"
                :class="{ 'is-pending-delete': deletingGameIds.includes(game.id) }"
                @click="showDetail(game)"
              >
                <div class="game-icon">
                  <i :class="getGameModeIcon(game.game_mode)"></i>
                </div>
                <div class="game-info">
                  <div class="game-title">
                    <span class="game-mode">{{ getModeText(game.game_mode) }}</span>
                    <span class="game-players">{{ game.num_players }}人局</span>
                    <span class="game-status" :class="`is-${game.end_status}`">{{ getEndStatusText(game.end_status) }}</span>
                  </div>
                  <div class="game-meta">
                    <span><i class="fas fa-calendar"></i> {{ formatDateTime(game.started_at) }}</span>
                    <span><i class="fas fa-route"></i> {{ game.path_length }} 步</span>
                  </div>
                </div>
                <div class="game-actions">
                  <button class="action-btn view-btn" title="查看详情">
                    <i class="fas fa-eye"></i>
                  </button>
                  <button
                    class="action-btn delete-btn"
                    :class="{ 'is-confirming': pendingDeleteGameId === game.id }"
                    :disabled="deletingGameIds.includes(game.id)"
                    :title="pendingDeleteGameId === game.id ? '再次点击确认删除' : '删除'"
                    @click.stop="deleteGame(game.id)"
                  >
                    <i :class="pendingDeleteGameId === game.id ? 'fas fa-check' : 'fas fa-trash'"></i>
                  </button>
                </div>
              </div>
            </TransitionGroup>
          </div>

          <!-- 分页 -->
          <div class="pagination">
            <div class="pagination-info">
              第 {{ pagination.page }} / {{ pagination.total_pages }} 页
            </div>
            <div class="pagination-buttons">
              <button class="page-btn" :disabled="pagination.page === 1" @click="changePage(-1)">
                <i class="fas fa-chevron-left"></i>
              </button>
              <div class="page-numbers">
                <template v-for="pageNum in visiblePageNumbers" :key="pageNum">
                  <span v-if="pageNum === '...'" class="page-ellipsis">...</span>
                  <button
                    v-else
                    class="page-number"
                    :class="{ active: pageNum === pagination.page }"
                    @click="goToPage(pageNum)"
                  >
                    {{ pageNum }}
                  </button>
                </template>
              </div>
              <button
                class="page-btn"
                :disabled="pagination.page === pagination.total_pages"
                @click="changePage(1)"
              >
                <i class="fas fa-chevron-right"></i>
              </button>
            </div>
          </div>
        </template>
      </div>
    </div>

    <!-- 对局详情弹窗 -->
    <div class="modal-overlay" :class="{ active: modalOpen }" @click.self="closeModal">
      <div class="modal-content">
        <div class="modal-header">
          <h2>对局详情</h2>
          <button class="modal-close" @click="closeModal">
            <i class="fas fa-times"></i>
          </button>
        </div>
        <div v-if="selectedGame" class="modal-body">
          <div class="detail-section">
            <h3>基本信息</h3>
            <div class="detail-grid">
              <div class="detail-item">
                <span class="detail-label">开始时间</span>
                <span class="detail-value">{{ formatDateTime(selectedGame.started_at) }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">结束时间</span>
                <span class="detail-value">{{ formatDateTime(selectedGame.ended_at) }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">结束状态</span>
                <span class="detail-value">{{ getEndStatusText(selectedGame.end_status) }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">模式</span>
                <span class="detail-value">{{ getModeText(selectedGame.game_mode) }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">玩家数</span>
                <span class="detail-value">{{ selectedGame.num_players }}人</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">行动数</span>
                <span class="detail-value">{{ selectedGame.path_length }}步</span>
              </div>
            </div>
          </div>

          <div class="detail-section">
            <h3>最终得分</h3>
            <div class="score-table">
              <div class="score-header">
                <span>名次</span>
                <span>玩家</span>
                <span>ID/策略</span>
                <span>总分</span>
                <span>板块</span>
                <span>连锁</span>
                <span>轨道</span>
                <span>资源</span>
              </div>
              <div
                v-for="(pr, idx) in selectedGameScoreRows"
                :key="idx"
                class="score-row"
              >
                <span class="score-rank">
                  <i
                    v-if="pr.rank_icon_class"
                    :class="[pr.rank_icon_class, `is-${pr.rank_tone}`]"
                    class="score-rank-icon"
                  ></i>
                </span>
                <span class="player-name" :class="{ 'is-ai': pr.identity_is_ai }">
                  <span>{{ pr.player_label }}</span>
                  <i v-if="pr.identity_icon" :class="pr.identity_icon"></i>
                </span>
                <span class="player-identity" :title="pr.identity_text">{{ pr.identity_text }}</span>
                <span class="total-score">{{ formatScoreValue(pr.total) }}</span>
                <span>{{ formatScoreValue(pr.board) }}</span>
                <span>{{ formatScoreValue(pr.chain) }}</span>
                <span>{{ formatScoreValue(pr.track) }}</span>
                <span>{{ formatScoreValue(pr.resource) }}</span>
              </div>
            </div>
          </div>

          <div class="detail-section">
            <h3>行动统计</h3>
            <p>共 {{ selectedGame.action_history?.length || 0 }} 个行动</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted, onUnmounted } from 'vue'
import { getGameModeIcon } from '../utils/gameModeMeta.js'
import { buildHistoryScoreRows } from '../utils/historyScoreRows.js'

const API_BASE = 'http://127.0.0.1:5001'
const GAME_LIST_TRANSITION_MS = 320

// 状态
const games = ref([])
const loading = ref(false)
const error = ref(null)
const pagination = ref({
  page: 1,
  total_pages: 1,
  total: 0,
})

// 排序和筛选
const sortBy = ref('timestamp')
const sortOrder = ref('desc')
const sortDropdownOpen = ref(false)
const filterPopupOpen = ref(false)
const searchQuery = ref('')
const selectedPlayerCounts = ref([])
const pendingDeleteGameId = ref(null)
const deletingGameIds = ref([])

// 弹窗
const modalOpen = ref(false)
const selectedGame = ref(null)

const sortOptions = [
  { value: 'timestamp', label: '按时间' },
  { value: 'num_players', label: '按玩家数' },
]

// 计算属性
const hasActiveFilters = computed(() => {
  return searchQuery.value.trim() !== '' || selectedPlayerCounts.value.length > 0
})

const selectedGameScoreRows = computed(() =>
  buildHistoryScoreRows({
    players: selectedGame.value?.players,
    finalScores: selectedGame.value?.final_scores,
  })
)

const visiblePageNumbers = computed(() => {
  const pages = []
  const maxVisible = 5
  const current = pagination.value.page
  const total = pagination.value.total_pages

  let startPage = Math.max(1, current - Math.floor(maxVisible / 2))
  let endPage = Math.min(total, startPage + maxVisible - 1)

  if (endPage - startPage < maxVisible - 1) {
    startPage = Math.max(1, endPage - maxVisible + 1)
  }

  if (startPage > 1) {
    pages.push(1)
    if (startPage > 2) pages.push('...')
  }

  for (let i = startPage; i <= endPage; i++) {
    pages.push(i)
  }

  if (endPage < total) {
    if (endPage < total - 1) pages.push('...')
    pages.push(total)
  }

  return pages
})

// 方法
function toggleSortDropdown() {
  sortDropdownOpen.value = !sortDropdownOpen.value
  if (sortDropdownOpen.value) filterPopupOpen.value = false
}

function selectSortOption(option) {
  sortBy.value = option.value
  sortDropdownOpen.value = false
  pagination.value.page = 1
  loadGames()
}

function toggleSortOrder() {
  sortOrder.value = sortOrder.value === 'desc' ? 'asc' : 'desc'
  pagination.value.page = 1
  loadGames()
}

function toggleFilterPopup() {
  filterPopupOpen.value = !filterPopupOpen.value
  if (filterPopupOpen.value) sortDropdownOpen.value = false
}

function clearFilters() {
  searchQuery.value = ''
  selectedPlayerCounts.value = []
  pagination.value.page = 1
  loadGames()
}

function applyFilters() {
  pagination.value.page = 1
  loadGames()
  filterPopupOpen.value = false
}

function changePage(delta) {
  const newPage = pagination.value.page + delta
  if (newPage >= 1 && newPage <= pagination.value.total_pages) {
    goToPage(newPage)
  }
}

function goToPage(page) {
  pagination.value.page = page
  loadGames()
}

function getModeText(mode) {
  const modeMap = {
    standard: '标准模式',
    quick: '快速模式',
    custom: '自定义模式',
  }
  return modeMap[mode] || mode
}

function getEndStatusText(status) {
  const statusMap = {
    finished: '已结束',
    interrupted: '已中断',
    error: '异常',
  }
  return statusMap[status] || status || '--'
}

function formatDateTime(value) {
  if (!value) {
    return '--'
  }

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return value
  }

  const pad = (num) => String(num).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`
}

function formatScoreValue(value) {
  return value ?? '--'
}

async function loadGames() {
  loading.value = true
  error.value = null

  try {
    let url = `${API_BASE}/api/games?page=${pagination.value.page}&per_page=10&sort_by=${sortBy.value}&sort_order=${sortOrder.value}`

    if (searchQuery.value.trim()) {
      url += `&search=${encodeURIComponent(searchQuery.value.trim())}`
    }

    const response = await fetch(url)
    const data = await response.json()

    if (data.error) {
      throw new Error(data.error)
    }

    games.value = data.games || []
    pagination.value = data.pagination || { page: 1, total_pages: 1, total: 0 }
  } catch (err) {
    error.value = '加载失败，请检查后端服务是否运行'
    console.error('Failed to load games:', err)
  } finally {
    loading.value = false
  }
}

async function showDetail(game) {
  if (deletingGameIds.value.includes(game.id)) {
    return
  }

  clearPendingDelete()

  try {
    const response = await fetch(`${API_BASE}/api/games/${game.id}`)
    const data = await response.json()

    if (data.error) {
      throw new Error(data.error)
    }

    selectedGame.value = data
    modalOpen.value = true
  } catch (err) {
    console.error('Failed to load game detail:', err)
    alert('加载详情失败')
  }
}

function closeModal() {
  modalOpen.value = false
  selectedGame.value = null
}

function clearPendingDelete() {
  pendingDeleteGameId.value = null
}

function pinLeavingGameCard(el) {
  el.style.left = `${el.offsetLeft}px`
  el.style.top = `${el.offsetTop}px`
  el.style.width = `${el.offsetWidth}px`
  el.style.height = `${el.offsetHeight}px`
}

async function waitForGameListTransition() {
  await nextTick()
  await new Promise((resolve) => setTimeout(resolve, GAME_LIST_TRANSITION_MS))
}

async function deleteGame(id) {
  if (deletingGameIds.value.includes(id)) {
    return
  }

  if (pendingDeleteGameId.value !== id) {
    pendingDeleteGameId.value = id
    return
  }

  clearPendingDelete()
  deletingGameIds.value = [...deletingGameIds.value, id]

  try {
    const wasLastGameOnPage = games.value.length === 1 && pagination.value.page > 1
    const response = await fetch(`${API_BASE}/api/games/${id}`, {
      method: 'DELETE',
    })
    const result = await response.json()

    if (result.error) {
      throw new Error(result.error)
    }

    games.value = games.value.filter((game) => game.id !== id)
    pagination.value.total = Math.max(0, pagination.value.total - 1)

    await waitForGameListTransition()

    if (wasLastGameOnPage) {
      pagination.value.page -= 1
    }

    await loadGames()
  } catch (err) {
    console.error('Failed to delete game:', err)
    alert('删除失败')
  } finally {
    deletingGameIds.value = deletingGameIds.value.filter((gameId) => gameId !== id)
  }
}

// 点击外部关闭弹窗
function handleDocumentClick(e) {
  const filterWrapper = e.target.closest('.filter-wrapper')
  if (!filterWrapper && filterPopupOpen.value) {
    filterPopupOpen.value = false
  }

  const sortWrapper = e.target.closest('.custom-select-wrapper')
  if (!sortWrapper && sortDropdownOpen.value) {
    sortDropdownOpen.value = false
  }

  const deleteButton = e.target.closest('.delete-btn')
  if (!deleteButton && pendingDeleteGameId.value !== null) {
    clearPendingDelete()
  }
}

onMounted(() => {
  loadGames()
  document.addEventListener('click', handleDocumentClick)
})

onUnmounted(() => {
  document.removeEventListener('click', handleDocumentClick)
})
</script>

<style scoped>
/* ===== 历史对局页面样式 ===== */

.history-page {
  height: calc(100vh - 56px);
  min-height: calc(100vh - 56px);
  background: var(--bg-primary);
  overflow: hidden;
}

.history-container {
  max-width: 900px;
  height: 100%;
  margin: 0 auto;
  padding: 44px 24px 24px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* 头部区域 */
.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
}

.history-body {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding-top: 24px;
}

.history-feedback {
  flex: 1;
  min-height: 0;
}

.games-scroll-area {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  scrollbar-gutter: stable;
  padding-right: 4px;
  margin-right: -4px;
}

.header-left {
  display: flex;
  align-items: baseline;
  gap: 12px;
}

.history-title {
  font-size: var(--font-size-page-title);
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.history-count {
  font-size: 0.85rem;
  color: var(--text-secondary);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 自定义下拉选择框 */
.custom-select-wrapper {
  position: relative;
}

.custom-select {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 8px 16px;
  font-size: 0.85rem;
  color: var(--text-primary);
  cursor: pointer;
  min-width: 160px;
  height: 36px;
  box-sizing: border-box;
  transition: all 0.2s;
  user-select: none;
}

.custom-select:hover {
  border-color: var(--accent);
}

.custom-select.active {
  border-color: var(--accent);
  border-bottom-color: transparent;
  border-radius: 8px 8px 0 0;
}

.custom-select i {
  font-size: 0.75rem;
  color: var(--text-secondary);
  transition: transform 0.2s;
}

.custom-select.active i {
  transform: rotate(180deg);
}

.custom-select-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  min-width: 160px;
  background: var(--bg-secondary);
  border: 1px solid var(--accent);
  border-top: none;
  border-radius: 0 0 8px 8px;
  overflow: hidden;
  z-index: 100;
  opacity: 0;
  visibility: hidden;
  transform: translateY(-4px);
  transition: all 0.2s ease;
}

.custom-select-dropdown.active {
  opacity: 1;
  visibility: visible;
  transform: translateY(0);
}

.custom-select-option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  font-size: 0.85rem;
  color: var(--text-primary);
  cursor: pointer;
  transition: all 0.15s;
}

.custom-select-option:hover {
  background: rgba(0, 123, 255, 0.1);
}

.custom-select-option.active {
  color: var(--accent-light);
}

.custom-select-option i {
  font-size: 0.75rem;
  opacity: 0;
}

.custom-select-option.active i {
  opacity: 1;
}

/* 正序倒序按钮 */
.order-btn {
  width: 36px;
  height: 36px;
  border-radius: 6px;
  border: 1px solid var(--border);
  background: var(--bg-secondary);
  color: var(--text-secondary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.order-btn:hover {
  border-color: var(--accent);
  color: var(--text-primary);
}

.order-btn.active {
  border-color: var(--accent);
}

/* 筛选按钮和弹窗 */
.filter-wrapper {
  position: relative;
}

.filter-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: 6px;
  color: var(--text-primary);
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.2s;
}

.filter-btn:hover {
  border-color: var(--accent);
}

.filter-btn.active {
  background: var(--accent);
  border-color: var(--accent);
  color: white;
}

/* 筛选弹窗 */
.filter-popup {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  width: 280px;
  background: var(--bg-secondary);
  border: 1px solid var(--accent);
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
  z-index: 100;
  opacity: 0;
  visibility: hidden;
  transform: translateY(-8px);
  transition: all 0.2s ease;
}

.filter-popup.active {
  opacity: 1;
  visibility: visible;
  transform: translateY(0);
}

.filter-section {
  margin-bottom: 16px;
}

.filter-section:last-of-type {
  margin-bottom: 0;
}

.filter-title {
  font-size: 0.8rem;
  font-weight: 500;
  color: var(--text-secondary);
  margin-bottom: 10px;
}

.filter-search-box {
  position: relative;
  display: flex;
  align-items: center;
}

.filter-search-box i {
  position: absolute;
  left: 12px;
  color: var(--text-secondary);
  font-size: 0.85rem;
}

.filter-search-box input {
  width: 100%;
  background: var(--bg-tertiary);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 10px 12px 10px 36px;
  font-size: 0.85rem;
  color: var(--text-primary);
}

.filter-search-box input::placeholder {
  color: var(--text-secondary);
}

.filter-search-box input:focus {
  outline: none;
  border-color: var(--accent);
}

.filter-options {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.filter-option {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: var(--bg-tertiary);
  border: 1px solid var(--border);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.filter-option:hover {
  border-color: var(--accent);
}

.filter-option.active {
  background: rgba(0, 123, 255, 0.15);
  border-color: var(--accent);
}

.filter-option input {
  display: none;
}

.filter-option span {
  font-size: 0.85rem;
  color: var(--text-primary);
}

.filter-option.active span {
  color: var(--accent-light);
}

.filter-actions {
  display: flex;
  gap: 8px;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--border);
}

.filter-actions button {
  flex: 1;
  padding: 8px 16px;
  border-radius: 6px;
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.2s;
}

.filter-clear {
  background: transparent;
  border: 1px solid var(--border);
  color: var(--text-secondary);
}

.filter-clear:hover {
  background: var(--bg-tertiary);
  color: var(--text-primary);
}

.filter-apply {
  background: var(--accent);
  border: 1px solid var(--accent);
  color: white;
}

.filter-apply:hover {
  background: #0069d9;
}

/* 对局列表 */
.games-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  position: relative;
  padding-bottom: 24px;
}

/* 对局卡片 */
.game-card {
  display: flex;
  align-items: center;
  gap: 16px;
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 16px 20px;
  cursor: pointer;
  transition:
    background-color 0.2s ease,
    border-color 0.2s ease,
    box-shadow 0.2s ease;
}

.game-card.is-pending-delete {
  pointer-events: none;
  background: rgba(239, 68, 68, 0.08);
  border-color: rgba(239, 68, 68, 0.24);
  box-shadow: inset 0 0 0 1px rgba(239, 68, 68, 0.18);
}

.game-card:hover {
  background: var(--bg-tertiary);
  border-color: rgba(0, 123, 255, 0.5);
}

.history-list-enter-active,
.history-list-leave-active {
  transition:
    opacity 0.22s ease,
    transform 0.22s cubic-bezier(0.22, 1, 0.36, 1);
  transform-origin: center center;
  will-change: opacity, transform;
}

.history-list-enter-from {
  opacity: 0;
  transform: scale(0.985);
}

.history-list-leave-to {
  opacity: 0;
  transform: scale(0.985);
}

.history-list-leave-active {
  position: absolute;
  pointer-events: none;
  z-index: 3;
}

.history-list-move {
  transition: transform 0.32s cubic-bezier(0.22, 1, 0.36, 1);
}

.game-icon {
  width: 48px;
  height: 48px;
  background: var(--bg-tertiary);
  border: 1px solid var(--border);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.game-icon i {
  font-size: 1.25rem;
  color: var(--accent-light);
}

.game-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.game-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.game-mode {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
}

.game-players {
  font-size: 0.75rem;
  color: var(--accent-light);
  background: rgba(0, 123, 255, 0.15);
  padding: 2px 8px;
  border-radius: 4px;
}

.game-status {
  font-size: 0.75rem;
  padding: 2px 8px;
  border-radius: 999px;
  border: 1px solid transparent;
}

.game-status.is-finished {
  color: #22c55e;
  background: rgba(34, 197, 94, 0.12);
  border-color: rgba(34, 197, 94, 0.22);
}

.game-status.is-interrupted {
  color: #f59e0b;
  background: rgba(245, 158, 11, 0.12);
  border-color: rgba(245, 158, 11, 0.22);
}

.game-status.is-error {
  color: #ef4444;
  background: rgba(239, 68, 68, 0.12);
  border-color: rgba(239, 68, 68, 0.22);
}

.game-meta {
  display: flex;
  align-items: center;
  gap: 16px;
  font-size: 0.85rem;
  color: var(--text-secondary);
}

.game-meta span {
  display: flex;
  align-items: center;
  gap: 6px;
}

.game-meta i {
  font-size: 0.8rem;
}

/* 操作按钮 */
.game-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.action-btn {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  border: none;
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.action-btn:hover {
  background: var(--bg-tertiary);
  color: var(--text-primary);
}

.action-btn.delete-btn:hover {
  background: rgba(239, 68, 68, 0.15);
  color: #ef4444;
}

.action-btn.delete-btn.is-confirming {
  background: rgba(239, 68, 68, 0.18);
  color: #fca5a5;
  box-shadow: inset 0 0 0 1px rgba(239, 68, 68, 0.36);
}

.action-btn.delete-btn.is-confirming:hover {
  background: rgba(239, 68, 68, 0.24);
  color: #fecaca;
}

/* 空状态 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 64px 20px;
  color: var(--text-secondary);
  gap: 16px;
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: 12px;
}

.empty-state i {
  font-size: 3rem;
  opacity: 0.5;
}

.empty-state p {
  font-size: 1rem;
}

/* 分页 */
.pagination {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-shrink: 0;
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid var(--border);
}

.pagination-info {
  font-size: 0.85rem;
  color: var(--text-secondary);
}

.pagination-buttons {
  display: flex;
  align-items: center;
  gap: 8px;
}

.page-btn {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  border: 1px solid var(--border);
  background: var(--bg-secondary);
  color: var(--text-primary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.page-btn:hover:not(:disabled) {
  background: var(--bg-tertiary);
  border-color: var(--accent);
}

.page-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.page-numbers {
  display: flex;
  align-items: center;
  gap: 4px;
}

.page-number {
  min-width: 36px;
  height: 36px;
  border-radius: 8px;
  border: 1px solid var(--border);
  background: var(--bg-secondary);
  color: var(--text-primary);
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.2s;
}

.page-number:hover {
  background: var(--bg-tertiary);
  border-color: var(--accent);
}

.page-number.active {
  background: var(--accent);
  border-color: var(--accent);
  color: white;
}

.page-ellipsis {
  color: var(--text-secondary);
  padding: 0 8px;
}

/* 弹窗 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  opacity: 0;
  visibility: hidden;
  transition: all 0.2s;
}

.modal-overlay.active {
  opacity: 1;
  visibility: visible;
}

.modal-content {
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: 16px;
  width: 90%;
  max-width: 860px;
  max-height: 80vh;
  overflow: hidden;
  transform: scale(0.95);
  transition: transform 0.2s;
}

.modal-overlay.active .modal-content {
  transform: scale(1);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid var(--border);
}

.modal-header h2 {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.modal-close {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  border: none;
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.modal-close:hover {
  background: var(--bg-tertiary);
  color: var(--text-primary);
}

.modal-body {
  padding: 24px;
  overflow-y: auto;
  max-height: calc(80vh - 80px);
}

/* 详情样式 */
.detail-section {
  margin-bottom: 24px;
}

.detail-section:last-child {
  margin-bottom: 0;
}

.detail-section h3 {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 16px 0;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.detail-label {
  font-size: 0.8rem;
  color: var(--text-secondary);
}

.detail-value {
  font-size: 0.95rem;
  color: var(--text-primary);
  font-weight: 500;
}

/* 分数表格 */
.score-table {
  background: var(--bg-tertiary);
  border-radius: 8px;
  overflow: hidden;
}

.score-header,
.score-row {
  display: grid;
  grid-template-columns: 0.7fr 0.9fr 2.08fr repeat(5, minmax(0, 0.88fr));
  gap: 8px;
  padding: 12px 16px;
  align-items: center;
}

.score-header {
  background: rgba(0, 123, 255, 0.1);
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--accent-light);
}

.score-header > span:first-child,
.score-row > span:first-child {
  justify-self: center;
  text-align: center;
  transform: translateX(-8px);
}

.score-rank {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 20px;
}

.score-rank-icon {
  display: block;
}

.score-rank-icon.is-gold {
  color: #f5c451;
}

.score-rank-icon.is-silver {
  color: #c2ccd6;
}

.score-rank-icon.is-bronze {
  color: #c9895a;
}

.score-row {
  font-size: 0.9rem;
  color: var(--text-primary);
  border-top: 1px solid var(--border);
}

.score-row:first-child {
  border-top: none;
}

.player-name {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
}

.player-name.is-ai i {
  color: var(--accent-light);
  font-size: 0.85em;
  flex-shrink: 0;
}

.player-identity {
  display: block;
  min-width: 0;
  overflow: hidden;
  color: var(--text-secondary);
  font-size: 0.82rem;
  line-height: 1.3;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.score-row > span:nth-child(n + 4),
.score-header > span:nth-child(n + 4) {
  text-align: right;
}

.total-score {
  font-weight: 600;
  color: var(--accent-light);
}

/* 响应式 */
@media (max-width: 768px) {
  .history-container {
    padding: 28px 16px 16px;
  }

  .history-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }

  .header-right {
    width: 100%;
    flex-wrap: wrap;
  }

  .filter-popup {
    right: -50px;
    width: 260px;
  }

  .game-card {
    padding: 12px 16px;
  }

  .game-icon {
    width: 40px;
    height: 40px;
  }

  .game-icon i {
    font-size: 1rem;
  }

  .game-meta {
    flex-wrap: wrap;
    gap: 8px;
  }

  .pagination {
    flex-direction: column;
    gap: 16px;
  }

  .detail-grid {
    grid-template-columns: 1fr;
  }

  .score-header,
  .score-row {
    grid-template-columns: 0.58fr 0.72fr 1.84fr repeat(2, minmax(0, 0.8fr));
    gap: 4px;
    font-size: 0.8rem;
  }

  .score-header span:nth-child(6),
  .score-header span:nth-child(7),
  .score-header span:nth-child(8),
  .score-row span:nth-child(6),
  .score-row span:nth-child(7),
  .score-row span:nth-child(8) {
    display: none;
  }
}
</style>
