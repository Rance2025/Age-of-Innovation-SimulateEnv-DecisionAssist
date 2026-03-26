<template>
  <div class="game-page">
    <div class="main-container">
      <!-- 左侧：玩家监控区 (28%) -->
      <div class="players-monitor">
        <div class="monitor-header">
          <i class="fas fa-users"></i>
          <div>玩家监控</div>
        </div>
        <div class="monitor-content">
          <div class="player-grid">
            <div
              v-for="player in players"
              :key="player.id"
              class="player-card"
              :class="{ collapsed: collapsedPlayers[player.id] }"
            >
              <div class="player-header" @click="togglePlayer(player.id)">
                <div class="player-header-left">
                  <div
                    v-if="player.planningCard"
                    class="planning-card-indicator"
                  >
                    <div
                      class="planning-card-circle"
                      :style="{ backgroundColor: getPlanningCardColor(player.planningCard) }"
                    ></div>
                  </div>
                  <div class="player-title">
                    <span>玩家 {{ player.id + 1 }}</span>
                    <span v-if="player.faction" class="faction-badge">{{ player.faction }}</span>
                  </div>
                </div>
                <div class="player-score">{{ player.score }}</div>
              </div>
              <div class="player-status">
                <div class="player-stats">
                  <!-- 第一行：资源数量 -->
                  <div class="stat-row">
                    <div class="stat-item">
                      <div class="stat-content">
                        <i class="fas fa-coins stat-icon"></i>
                        <span class="stat-value">{{ player.money }}</span>
                      </div>
                    </div>
                    <div class="stat-item">
                      <div class="stat-content">
                        <i class="fas fa-cube stat-icon"></i>
                        <span class="stat-value">{{ player.mineral }}</span>
                      </div>
                    </div>
                    <div class="stat-item">
                      <div class="stat-content">
                        <i class="fas fa-user stat-icon"></i>
                        <span class="stat-value">{{ player.mibao }}</span>
                      </div>
                    </div>
                  </div>
                  <!-- 第二行：书籍数量 -->
                  <div class="stat-row">
                    <div class="stat-item">
                      <div class="stat-content">
                        <i class="fas fa-university stat-icon"></i>
                        <span class="stat-value">{{ player.bank }}</span>
                      </div>
                    </div>
                    <div class="stat-item">
                      <div class="stat-content">
                        <i class="fas fa-gavel stat-icon"></i>
                        <span class="stat-value">{{ player.law }}</span>
                      </div>
                    </div>
                    <div class="stat-item">
                      <div class="stat-content">
                        <i class="fas fa-cog stat-icon"></i>
                        <span class="stat-value">{{ player.engineering }}</span>
                      </div>
                    </div>
                    <div class="stat-item">
                      <div class="stat-content">
                        <i class="fas fa-heartbeat stat-icon"></i>
                        <span class="stat-value">{{ player.medical }}</span>
                      </div>
                    </div>
                  </div>
                  <!-- 第三行：三区魔力 -->
                  <div class="stat-row">
                    <div class="stat-item">
                      <div class="stat-content">
                        <div class="icon-stack">
                          <i class="fa-solid fa-circle icon-background"></i>
                          <i class="fa-solid fa-1 icon-foreground"></i>
                        </div>
                        <span class="stat-value">{{ player.magic1 }}</span>
                      </div>
                    </div>
                    <div class="stat-item">
                      <div class="stat-content">
                        <div class="icon-stack">
                          <i class="fa-solid fa-circle icon-background"></i>
                          <i class="fa-solid fa-2 icon-foreground"></i>
                        </div>
                        <span class="stat-value">{{ player.magic2 }}</span>
                      </div>
                    </div>
                    <div class="stat-item">
                      <div class="stat-content">
                        <div class="icon-stack">
                          <i class="fa-solid fa-circle icon-background"></i>
                          <i class="fa-solid fa-3 icon-foreground"></i>
                        </div>
                        <span class="stat-value">{{ player.magic3 }}</span>
                      </div>
                    </div>
                  </div>
                  <!-- 第四行：其他状态 -->
                  <div class="stat-row">
                    <div class="stat-item">
                      <div class="stat-content">
                        <i class="fas fa-city stat-icon"></i>
                        <span class="stat-value">{{ player.cities }}</span>
                      </div>
                    </div>
                    <div class="stat-item">
                      <div class="stat-content">
                        <i class="fas fa-ship stat-icon"></i>
                        <span class="stat-value">{{ player.navigation }}</span>
                      </div>
                    </div>
                    <div class="stat-item">
                      <div class="stat-content">
                        <i class="fas fa-digging stat-icon"></i>
                        <span class="stat-value">{{ player.shovel }}</span>
                      </div>
                    </div>
                  </div>
                </div>
                <div class="player-log" :id="'player-log-' + (player.id + 1)">
                  <div
                    v-for="(log, idx) in player.logs"
                    :key="idx"
                    class="log-item"
                    :data-color="log.color"
                  >
                    {{ log.text }}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 中间区域 (47%) -->
      <div class="middle-section">
        <div class="middle-header">
          <i class="fas fa-gamepad"></i>
          <div>游戏区域</div>
        </div>
        <div class="middle-content">
          <div class="game-grid">
            <!-- 游戏版图卡片 -->
            <div class="game-card" :class="{ collapsed: collapsedCards['map'] }">
              <div class="game-header" @click="toggleCard('map')">
                <div class="game-header-left">
                  <div class="game-title">
                    <i class="fas fa-map"></i>
                    <span>游戏版图</span>
                  </div>
                </div>
                <div class="game-header-right">
                  <div class="terrain-tooltip-container">
                    <div
                      class="terrain-tooltip-trigger"
                      @mouseenter="showTerrainTooltip"
                      @mouseleave="hideTerrainTooltip"
                    >
                      <i class="fas fa-question-circle"></i>
                    </div>
                    <div
                      class="terrain-tooltip"
                      :class="{ show: terrainTooltipOpen }"
                      @mouseenter="showTerrainTooltip"
                      @mouseleave="hideTerrainTooltip"
                    >
                      <div class="tooltip-content">
                        <h3>地形色环与图例</h3>
                        <div class="color-ring-wrapper">
                          <svg
                            width="200"
                            height="200"
                            viewBox="0 0 400 400"
                            xmlns="http://www.w3.org/2000/svg"
                          >
                            <path
                              d="M 200 200 L 200 20 A 180 180 0 0 1 340.73 87.77 Z"
                              fill="#37af37"
                              stroke="rgb(219, 219, 219)"
                              stroke-width="3"
                            />
                            <path
                              d="M 200 200 L 340.73 87.77 A 180 180 0 0 1 375.49 240.05 Z"
                              fill="#a1a1a1"
                              stroke="rgb(219, 219, 219)"
                              stroke-width="3"
                            />
                            <path
                              d="M 200 200 L 375.49 240.05 A 180 180 0 0 1 278.10 362.17 Z"
                              fill="#cc2828"
                              stroke="rgb(219, 219, 219)"
                              stroke-width="3"
                            />
                            <path
                              d="M 200 200 L 278.10 362.17 A 180 180 0 0 1 121.90 362.17 Z"
                              fill="#e8e83d"
                              stroke="rgb(219, 219, 219)"
                              stroke-width="3"
                            />
                            <path
                              d="M 200 200 L 121.90 362.17 A 180 180 0 0 1 24.51 240.05 Z"
                              fill="#85491D"
                              stroke="rgb(219, 219, 219)"
                              stroke-width="3"
                            />
                            <path
                              d="M 200 200 L 24.51 240.05 A 180 180 0 0 1 59.27 87.77 Z"
                              fill="#595959"
                              stroke="rgb(219, 219, 219)"
                              stroke-width="3"
                            />
                            <path
                              d="M 200 200 L 59.27 87.77 A 180 180 0 0 1 200 20 Z"
                              fill="#35a0d5"
                              stroke="rgb(219, 219, 219)"
                              stroke-width="3"
                            />
                            <circle
                              cx="200"
                              cy="200"
                              r="75"
                              fill="var(--bg-secondary)"
                              stroke="rgb(219, 219, 219)"
                              stroke-width="3"
                            />
                          </svg>
                        </div>
                        <div class="legend">
                          <div class="legend-item">
                            <div class="color-box" style="background-color: #37af37"></div>
                            <span>森林</span>
                          </div>
                          <div class="legend-item">
                            <div class="color-box" style="background-color: #a1a1a1"></div>
                            <span>山脉</span>
                          </div>
                          <div class="legend-item">
                            <div class="color-box" style="background-color: #35a0d5"></div>
                            <span>湖泊</span>
                          </div>
                          <div class="legend-item">
                            <div class="color-box" style="background-color: #cc2828"></div>
                            <span>荒地</span>
                          </div>
                          <div class="legend-item">
                            <div class="color-box" style="background-color: #595959"></div>
                            <span>沼泽</span>
                          </div>
                          <div class="legend-item">
                            <div class="color-box" style="background-color: #e8e83d"></div>
                            <span>沙漠</span>
                          </div>
                          <div class="legend-item">
                            <div class="color-box" style="background-color: #85491d"></div>
                            <span>平原</span>
                          </div>
                          <div class="legend-item">
                            <div class="color-box water-legend"></div>
                            <span>水域</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                  <div class="game-indicator">
                    <i class="fas fa-chevron-down"></i>
                  </div>
                </div>
              </div>
              <div class="map-board-status">
                <div class="map-container-full">
                  <svg
                    id="hex-grid-svg"
                    width="100%"
                    height="100%"
                    viewBox="0 0 800 640"
                    preserveAspectRatio="xMidYMid slice"
                  >
                    <g id="hex-elements"></g>
                  </svg>
                </div>
              </div>
            </div>

            <!-- 回合信息卡片 -->
            <div class="game-card" :class="{ collapsed: collapsedCards['round'] }">
              <div class="game-header" @click="toggleCard('round')">
                <div class="game-header-left">
                  <div class="game-title">
                    <i class="fas fa-flag-checkered"></i>
                    <span>回合信息</span>
                  </div>
                </div>
                <div class="game-indicator">
                  <i class="fas fa-chevron-down"></i>
                </div>
              </div>
              <div class="round-info-status">
                <div class="round-info-container">
                  <div class="left-column">
                    <div
                      v-for="round in roundInfo"
                      :key="round.number"
                      class="grid-cell"
                      :class="[
                        'round-' + round.number,
                        {
                          'current-round': currentRound === round.number,
                          flipped: round.flipped,
                        },
                      ]"
                      :data-round="round.number"
                    >
                      <span class="round-label">第 {{ round.number }} 回合</span>
                      <div class="card-container">
                        <div class="card-face front">
                          <img
                            :src="`/images/scoring/${round.currentX}.png`"
                            alt="计分图标"
                            class="scoring-image"
                          />
                        </div>
                        <div class="card-face back">
                          <img
                            :src="`/images/scoring/${round.backX}.png`"
                            alt="计分图标背面"
                            class="scoring-image"
                          />
                        </div>
                      </div>
                      <img
                        v-if="round.number === 6 && round.overlayImage"
                        :src="round.overlayImage"
                        alt="叠加奖励图标"
                        class="overlay-image"
                      />
                    </div>
                  </div>
                  <div class="right-column" id="right-bonus-grid">
                    <div
                      v-for="(bonus, index) in bonusColumns"
                      :key="index"
                      class="bonus-cell"
                      :class="{ flipped: bonus.flipped }"
                      :data-index="index"
                      :data-x="bonus.x"
                    >
                      <div class="card-container">
                        <div class="card-face front">
                          <img :src="`/images/bonus/${bonus.x}.png`" alt="助推板块" />
                        </div>
                        <div class="card-face back">
                          <img :src="`/images/bonus/${bonus.backX}.png`" alt="助推板块背面" />
                        </div>
                      </div>
                      <span class="bonus-label">回合助推板 {{ bonus.x }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 战术地图卡片 -->
            <div class="game-card" :class="{ collapsed: collapsedCards['tactical'] }">
              <div class="game-header" @click="toggleCard('tactical')">
                <div class="game-header-left">
                  <div class="game-title">
                    <i class="fas fa-map"></i>
                    <span>战术地图</span>
                  </div>
                </div>
                <div class="game-indicator">
                  <i class="fas fa-chevron-down"></i>
                </div>
              </div>
              <div class="game-status">
                <div class="game-stats">
                  <div class="map-container">
                    <div class="map-placeholder">
                      <i class="fas fa-map-marked-alt"></i>
                      <div>战术地图区域</div>
                      <div class="map-hint">此区域将显示游戏地图和战术信息</div>
                    </div>
                  </div>
                </div>
                <div class="game-log" id="game-log-tactical">
                  <div
                    v-for="(log, idx) in tacticalLogs"
                    :key="idx"
                    class="log-item"
                  >
                    {{ log }}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧：全局信息区 (25%) -->
      <div class="global-section">
        <!-- 顶部全局状态 -->
        <div class="global-status">
          <div class="status-title">
            <i class="fas fa-info-circle"></i>
            <div>对局状态</div>
          </div>
          <!-- 更多菜单按钮 -->
          <div class="more-menu-container">
            <button class="more-menu-btn" @click="toggleMoreMenu">
              <i class="fas fa-bars"></i>
            </button>
            <div class="more-menu-dropdown" :class="{ show: moreMenuOpen }">
              <button class="menu-item end-game" @click="endGame">
                <i class="fas fa-flag-checkered"></i>
                <span>结束游戏</span>
              </button>
            </div>
          </div>
          <div class="status-content" id="global-status-content">{{ globalStatus }}</div>
        </div>

        <!-- 可选行动区 -->
        <div class="action-section">
          <div class="action-header">
            <div class="action-title">
              <i class="fas fa-play-circle"></i>
              <div>可选行动</div>
            </div>
            <div class="action-count">共<span id="action-count">{{ actionCount }}</span>条</div>
          </div>
          <div id="action-content" class="action-content">
            <div
              v-for="(action, idx) in actions"
              :key="idx"
              class="action-item"
              :data-color="action.color"
            >
              {{ action.text }}
            </div>
          </div>
        </div>

        <!-- 底部输入区 -->
        <div class="global-input">
          <div class="input-group">
            <input
              v-model="commandInput"
              type="text"
              id="command"
              placeholder="输入行动编号..."
              autofocus
              @keypress.enter="sendCommand"
            />
            <button class="send-btn" @click="sendCommand">
              <i class="fas fa-paper-plane"></i>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useGameStore } from '../stores/game'

const router = useRouter()
const gameStore = useGameStore()

// 玩家数据
const players = ref([
  {
    id: 0,
    faction: '',
    planningCard: null,
    score: 20,
    money: 0,
    mineral: 0,
    mibao: 0,
    bank: 0,
    law: 0,
    engineering: 0,
    medical: 0,
    magic1: 5,
    magic2: 7,
    magic3: 0,
    cities: 0,
    navigation: 0,
    shovel: 3,
    logs: [],
  },
  {
    id: 1,
    faction: '',
    planningCard: null,
    score: 20,
    money: 0,
    mineral: 0,
    mibao: 0,
    bank: 0,
    law: 0,
    engineering: 0,
    medical: 0,
    magic1: 5,
    magic2: 7,
    magic3: 0,
    cities: 0,
    navigation: 0,
    shovel: 3,
    logs: [],
  },
  {
    id: 2,
    faction: '',
    planningCard: null,
    score: 20,
    money: 0,
    mineral: 0,
    mibao: 0,
    bank: 0,
    law: 0,
    engineering: 0,
    medical: 0,
    magic1: 5,
    magic2: 7,
    magic3: 0,
    cities: 0,
    navigation: 0,
    shovel: 3,
    logs: [],
  },
])

// 折叠状态
const collapsedPlayers = reactive({})
const collapsedCards = reactive({
  map: false,
  round: false,
  tactical: false,
})

// 地形提示弹窗
const terrainTooltipOpen = ref(false)
let terrainTooltipTimeout = null

// 更多菜单
const moreMenuOpen = ref(false)

// 回合信息
const currentRound = ref(1)
const roundInfo = ref([
  { number: 1, currentX: -1, backX: 0, flipped: false, overlayImage: null },
  { number: 4, currentX: -1, backX: 0, flipped: false, overlayImage: null },
  { number: 2, currentX: -1, backX: 0, flipped: false, overlayImage: null },
  { number: 5, currentX: -1, backX: 0, flipped: false, overlayImage: null },
  { number: 3, currentX: -1, backX: 0, flipped: false, overlayImage: null },
  { number: 6, currentX: -1, backX: 0, flipped: false, overlayImage: null },
])

// 助推板块
const bonusColumns = ref([
  { x: 0, backX: 0, flipped: false },
  { x: 0, backX: 0, flipped: false },
  { x: 0, backX: 0, flipped: false },
  { x: 0, backX: 0, flipped: false },
  { x: 0, backX: 0, flipped: false },
  { x: 0, backX: 0, flipped: false },
])

// 全局状态
const globalStatus = ref('所有玩家已就绪，对局即将开始')
const actionCount = ref(0)
const actions = ref([])
const tacticalLogs = ref([])
const commandInput = ref('')

// 规划卡颜色映射
const planningCardColors = {
  森林: '#37af37',
  湖泊: '#35a0d5',
  沙漠: '#e8e83d',
  山脉: '#a1a1a1',
  平原: '#85491D',
  沼泽: '#595959',
  荒地: '#cc2828',
}

function getPlanningCardColor(card) {
  return planningCardColors[card] || '#ffffff'
}

// 切换玩家卡片折叠
function togglePlayer(playerId) {
  collapsedPlayers[playerId] = !collapsedPlayers[playerId]
}

// 切换游戏卡片折叠
function toggleCard(cardName) {
  collapsedCards[cardName] = !collapsedCards[cardName]
}

// 地形提示弹窗控制
function showTerrainTooltip() {
  clearTimeout(terrainTooltipTimeout)
  terrainTooltipTimeout = setTimeout(() => {
    terrainTooltipOpen.value = true
  }, 300)
}

function hideTerrainTooltip() {
  clearTimeout(terrainTooltipTimeout)
  terrainTooltipTimeout = setTimeout(() => {
    terrainTooltipOpen.value = false
  }, 300)
}

// 更多菜单控制
function toggleMoreMenu() {
  moreMenuOpen.value = !moreMenuOpen.value
}

// 结束游戏
function endGame() {
  if (confirm('确定要结束当前游戏吗？')) {
    gameStore.resetGame() // 使用resetGame完全重置游戏状态
    moreMenuOpen.value = false
    router.push('/')
  }
}

// 发送命令
function sendCommand() {
  if (commandInput.value.trim()) {
    console.log('发送命令:', commandInput.value)
    commandInput.value = ''
  }
}

// 点击外部关闭菜单
function handleDocumentClick(e) {
  const moreMenu = e.target.closest('.more-menu-container')
  if (!moreMenu && moreMenuOpen.value) {
    moreMenuOpen.value = false
  }

  const tooltipContainer = e.target.closest('.terrain-tooltip-container')
  if (!tooltipContainer && terrainTooltipOpen.value) {
    terrainTooltipOpen.value = false
  }
}

onMounted(() => {
  gameStore.loadFromStorage()
  document.addEventListener('click', handleDocumentClick)
})

onUnmounted(() => {
  document.removeEventListener('click', handleDocumentClick)
  clearTimeout(terrainTooltipTimeout)
})
</script>

<style scoped>
/* 使用与 setup 界面一致的 CSS 变量 */
@import '../assets/variables.css';

.game-page {
  width: 100%;
  height: calc(100vh - 56px);
  background-color: var(--bg-primary);
  color: var(--text-primary);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.main-container {
  display: flex;
  gap: var(--gap);
  flex: 1;
  height: 100%;
  overflow: hidden;
  padding: var(--gap);
  box-sizing: border-box;
}

/* ===== 左侧：玩家监控区 (28%) ===== */
.players-monitor {
  width: 28%;
  height: 100%;
  overflow: hidden;
  background-color: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: var(--border-radius);
}

.monitor-header {
  padding: 10px var(--panel-padding);
  height: 5%;
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 600;
  font-size: 1.1rem;
  color: var(--text-primary);
}

.monitor-header i {
  color: var(--accent);
}

.monitor-content {
  flex: 1;
  display: flex;
  height: 94%;
  flex-direction: column;
  overflow: hidden;
  padding: 0;
  border-radius: 10px;
  border: 1px solid #262626;
  margin-left: 9px;
  margin-right: 9px;
  margin-bottom: 8px;
  background-color: #171717;
}

.player-grid {
  display: flex;
  flex-direction: column;
  gap: var(--gap);
  padding: var(--gap);
  flex: 1;
  overflow-y: auto;
  max-height: 100%;
}

.player-grid::-webkit-scrollbar {
  display: none;
}

.player-card {
  background-color: var(--bg-tertiary);
  border-radius: var(--border-radius);
  border: 1px solid var(--border);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  height: 32.3%;
  flex-shrink: 0;
  transition: height 0.3s ease;
}

.player-card:hover {
  border-color: var(--accent);
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.3);
}

.player-card.collapsed {
  height: 50px;
}

.player-card.collapsed .player-status {
  opacity: 0;
}

.player-header {
  padding: 8px var(--panel-padding);
  background-color: var(--bg-tertiary);
  border-bottom: 1px solid var(--border);
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  user-select: none;
  transition: background-color 0.2s;
  flex-shrink: 0;
  height: 50px;
  box-sizing: border-box;
}

.player-header:hover {
  background-color: rgba(77, 166, 255, 0.1);
}

.player-header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.planning-card-indicator {
  display: flex;
  align-items: center;
}

.planning-card-circle {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background-color: #ffffff;
  border: 0;
}

.faction-badge {
  background-color: rgba(77, 166, 255, 0.2);
  color: var(--accent-light);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: 600;
  margin-left: 6px;
  border: 1px solid rgba(77, 166, 255, 0.3);
}

.player-title {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
  display: flex;
  align-items: center;
}

.player-score {
  background-color: transparent;
  color: var(--accent);
  padding: 0;
  border: none;
  font-weight: 700;
  font-size: 1.1rem;
}

.player-status {
  flex: 1;
  display: flex;
  overflow: hidden;
  min-height: 0;
  transition: opacity 0.3s ease;
  opacity: 1;
}

.player-stats {
  flex: 1;
  padding: var(--panel-padding);
  border-right: 1px solid var(--border);
  overflow: hidden;
  background-color: var(--bg-elevated);
}

.stat-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 2px solid var(--border);
}

.stat-row:last-child {
  border-bottom: none;
  margin-bottom: 0;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
  border-right: 1px solid var(--border);
  margin-top: 6px;
  margin-bottom: 6px;
}

.stat-item:last-child {
  border-right: none;
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 6px;
  justify-content: center;
  width: 100%;
}

.stat-icon {
  font-size: 1rem;
  flex-shrink: 0;
}

/* 游戏相关 icon 颜色保持不变 */
.fa-coins { color: gold; }
.fa-cube { color: silver; }
.fa-user { color: #ff6b6b; }
.fa-university { color: #4ecdc4; }
.fa-gavel { color: #45b7d1; }
.fa-cog { color: #96ceb4; }
.fa-heartbeat { color: #feca57; }
.fa-city { color: #ff9ff3; }
.fa-ship { color: #54a0ff; }
.fa-digging { color: #a29bfe; }

.icon-stack {
  position: relative;
  display: inline-block;
  width: 1.5em;
  height: 1.5em;
  flex-shrink: 0;
}

.icon-background {
  position: absolute;
  top: 0;
  left: 0;
  font-size: 1.5em;
  color: #e4e4e4;
}

.icon-foreground {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: 0.7em;
  color: #0a0a0a;
}

.stat-value {
  font-size: 1rem;
  font-weight: 700;
  color: var(--text-primary);
  white-space: nowrap;
}

.player-log {
  flex: 1.5;
  padding: var(--panel-padding);
  overflow-y: auto;
  font-size: 0.8rem;
  line-height: 1.4;
  color: var(--text-secondary);
  background-color: var(--bg-secondary);
}

.player-log::-webkit-scrollbar {
  display: none;
}

.log-item {
  background-color: var(--bg-tertiary);
  border-left: 2px solid var(--accent);
  padding: 6px;
  margin-bottom: 4px;
  font-family: 'Consolas', monospace;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.log-item[data-color='blue'] { border-left-color: #007bff; }
.log-item[data-color='orange'] { border-left-color: #f1a61b; }
.log-item[data-color='purple'] { border-left-color: #ad32ef; }
.log-item[data-color='pink'] { border-left-color: #e57ea9; }
.log-item[data-color='celeste'] { border-left-color: #82d8d0; }

.log-item:hover {
  background-color: rgba(77, 166, 255, 0.1);
}

/* ===== 中间区域：游戏区域 (47%) ===== */
.middle-section {
  background-color: var(--bg-secondary);
  border-radius: var(--border-radius);
  width: 47%;
  height: 100%;
  display: flex;
  flex-direction: column;
  border: 1px solid var(--border);
  overflow: hidden;
}

.middle-header {
  padding: 10px var(--panel-padding);
  height: 5%;
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 600;
  font-size: 1.1rem;
  color: var(--text-primary);
  flex-shrink: 0;
}

.middle-header i {
  color: var(--accent);
}

.middle-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding: 0;
  border-radius: 10px;
  border: 1px solid #262626;
  margin-left: 9px;
  margin-right: 9px;
  margin-bottom: 8px;
  background-color: #171717;
}

.game-grid {
  display: flex;
  flex-direction: column;
  gap: var(--gap);
  padding: var(--gap);
  flex: 1;
  overflow-y: auto;
  max-height: 100%;
  min-height: 0;
}

.game-grid::-webkit-scrollbar {
  display: none;
}

.game-card {
  position: relative;
  background-color: var(--bg-tertiary);
  border-radius: var(--border-radius);
  border: 1px solid var(--border);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  max-height: 60%;
  flex-shrink: 0;
  transition: max-height 0.3s ease;
}

.game-card:hover {
  border-color: var(--accent);
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.3);
}

.game-card.collapsed {
  max-height: 50px;
}

.game-header {
  padding: 8px var(--panel-padding);
  background-color: var(--bg-tertiary);
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  user-select: none;
  flex-shrink: 0;
  height: 50px;
  box-sizing: border-box;
}

.game-header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.game-title {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
  display: flex;
  align-items: center;
  gap: 8px;
}

.game-title i {
  color: var(--accent);
  width: 16px;
  text-align: center;
}

.game-header-right {
  display: flex;
  align-items: center;
  gap: 10px;
  position: relative;
}

.terrain-tooltip-container {
  position: relative;
  display: flex;
  align-items: center;
  transition: opacity 0.3s ease;
}

.game-card.collapsed .terrain-tooltip-container {
  opacity: 0;
  transform: scale(0.85);
  pointer-events: none;
}

.game-card.collapsed .game-header-right {
  justify-content: flex-end;
}

.game-card.collapsed .terrain-tooltip {
  display: none !important;
}

.terrain-tooltip-trigger {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  color: var(--text-secondary);
  cursor: help;
  transition: all 0.3s ease;
  border-radius: 50%;
  font-size: 16px;
  z-index: 10;
}

.terrain-tooltip-trigger:hover {
  color: var(--accent);
  background-color: rgba(0, 123, 255, 0.1);
  transform: scale(1.1);
}

.terrain-tooltip {
  position: absolute;
  top: 100%;
  right: 0;
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 15px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 1000;
  min-width: 200px;
  opacity: 0;
  visibility: hidden;
  transform: translateY(-10px);
  transition: all 0.3s ease;
  margin-top: 8px;
  pointer-events: none;
}

.terrain-tooltip.show {
  opacity: 1;
  visibility: visible;
  transform: translateY(0);
  pointer-events: auto;
}

.terrain-tooltip::before {
  content: '';
  position: absolute;
  top: -6px;
  right: 12px;
  width: 12px;
  height: 12px;
  background: var(--bg-secondary);
  border-left: 1px solid var(--border);
  border-top: 1px solid var(--border);
  transform: rotate(45deg);
  z-index: -1;
}

.tooltip-content h3 {
  margin: 0 0 15px 0;
  font-size: 1rem;
  color: var(--text-primary);
  text-align: center;
  border-bottom: 1px solid var(--border);
  padding-bottom: 10px;
}

.color-ring-wrapper {
  display: flex;
  justify-content: center;
  margin-bottom: 20px;
}

.legend {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px 20px;
  justify-items: center;
  justify-content: center;
  margin: 0 auto;
  max-width: 280px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  justify-content: center;
}

.color-box {
  width: 16px;
  height: 16px;
  border-radius: 3px;
  flex-shrink: 0;
}

.water-legend {
  border: 2px dashed rgba(255, 255, 255, 0.6);
  background-color: transparent;
}

.game-indicator {
  color: var(--text-secondary);
  transition: all 0.3s ease;
  padding: 6px;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
}

.game-indicator:hover {
  color: var(--accent);
}

.game-card.collapsed .game-indicator i {
  transform: rotate(-90deg);
}

.game-indicator i {
  transition: transform 0.3s ease;
}

.map-board-status {
  flex: 1;
  display: flex;
  overflow: hidden;
  min-height: 0;
  transition: opacity 0.3s ease;
  opacity: 1;
  position: relative;
  z-index: 0;
}

.game-card.collapsed .map-board-status {
  opacity: 0;
}

.map-container-full {
  width: 100%;
  height: 100%;
  padding: 5px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: transparent;
  overflow: hidden;
}

#hex-grid-svg {
  display: block;
  width: 100%;
  min-height: 490px;
}

/* 回合信息 */
.round-info-status {
  padding: var(--panel-padding);
  opacity: 1;
  transition: opacity 0.3s ease;
}

.game-card.collapsed .round-info-status {
  opacity: 0;
}

.round-info-container {
  display: flex;
  gap: 20px;
}

.left-column {
  width: 30%;
  display: grid;
  grid-template-columns: 1fr 1fr;
  grid-template-rows: 1fr 1fr 1fr;
  gap: 10px;
  min-height: 100%;
}

.grid-cell {
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
  width: 100%;
  height: 100%;
  transition: all 0.3s ease;
}

.card-container {
  width: 100%;
  height: 100%;
  position: relative;
  transform-style: preserve-3d;
  transition: transform 0.6s;
}

.card-face {
  position: absolute;
  width: 100%;
  height: 100%;
  backface-visibility: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}

.card-face.back {
  transform: rotateY(180deg);
}

.grid-cell.flipped .card-container {
  transform: rotateY(180deg);
}

.grid-cell.flipped:hover .card-container {
  transform: rotateY(0deg);
}

.grid-cell.current-round {
  position: relative;
  z-index: 5;
  overflow: hidden;
  border-radius: 12px;
  padding: 6px;
}

.grid-cell.current-round::before {
  content: '';
  position: absolute;
  z-index: -1;
  left: -50%;
  top: -50%;
  width: 200%;
  height: 200%;
  background-color: #1a232a;
  background-repeat: no-repeat;
  background-position: 0 0;
  background-image: conic-gradient(
    transparent,
    rgba(0, 123, 255, 1),
    rgba(77, 166, 255, 1),
    transparent 30%
  );
  animation: rotate 6s linear infinite;
  border-radius: 12px;
}

.grid-cell.current-round::after {
  content: '';
  position: absolute;
  z-index: -1;
  left: 2px;
  top: 2px;
  width: calc(100% - 4px);
  height: calc(100% - 4px);
  background: var(--bg-tertiary);
  border-radius: 12px;
}

@keyframes rotate {
  100% {
    transform: rotate(1turn);
  }
}

.grid-cell.current-round .round-label {
  z-index: 30;
}

.grid-cell img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.round-6 {
  position: relative;
}

.grid-cell.current-round.round-6 {
  position: relative;
  z-index: 1;
}

.base-image,
.overlay-image {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.grid-cell.current-round.round-6 .overlay-image {
  position: absolute;
  top: 6px;
  left: 6px;
  width: calc(100% - 12px);
  height: calc(100% - 12px);
  object-fit: contain;
  z-index: 20;
  display: block;
  pointer-events: none;
}

.grid-cell.round-6 .overlay-image {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: contain;
  z-index: 2;
  display: none;
}

.round-label {
  position: absolute;
  bottom: 0px;
  font-size: 0.7rem;
  color: #ededed;
  background: rgba(0, 0, 0, 0.5);
  padding: 2px 4px;
  border-radius: 4px;
  z-index: 30;
  pointer-events: none;
}

.right-column {
  width: 70%;
  display: flex;
  gap: 6px;
  padding: 4px;
  min-height: 100px;
  box-sizing: border-box;
  overflow: hidden;
}

.bonus-cell {
  position: relative;
  flex: 1;
  min-width: 0;
  perspective: 1000px;
  border-radius: 4px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.bonus-cell .card-container {
  position: relative;
  width: 100%;
  padding-bottom: 266.67%;
  transform-style: preserve-3d;
  transition: transform 0.6s ease;
  flex-shrink: 0;
}

.bonus-cell .card-face {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  backface-visibility: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-tertiary);
  border-radius: 4px;
}

.bonus-cell .card-face.back {
  transform: rotateY(180deg);
}

.bonus-cell.flipped .card-container {
  transform: rotateY(180deg);
}

.bonus-cell img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  box-sizing: border-box;
}

.bonus-label {
  position: absolute;
  bottom: 6px;
  left: 8px;
  right: 8px;
  font-size: 0.6rem;
  color: #ededed;
  background: rgba(0, 0, 0, 0.5);
  padding: 2px 4px;
  border-radius: 4px;
  z-index: 10;
  pointer-events: none;
  text-align: center;
  white-space: nowrap;
  min-width: 0px;
}

/* 战术地图 */
.game-status {
  flex: 1;
  display: flex;
  overflow: hidden;
  min-height: 0;
  transition: opacity 0.3s ease;
  opacity: 1;
}

.game-card.collapsed .game-status {
  opacity: 0;
}

.game-stats {
  flex: 1;
  padding: var(--panel-padding);
  border-right: 1px solid var(--border);
  overflow-y: auto;
  background-color: var(--bg-elevated);
  min-height: 0;
}

.map-container {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.map-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
  gap: 8px;
}

.map-placeholder i {
  font-size: 3rem;
  opacity: 0.5;
}

.map-hint {
  font-size: 0.9rem;
  margin-top: 8px;
  color: var(--text-secondary);
}

.game-log {
  flex: 1.5;
  padding: var(--panel-padding);
  overflow-y: auto;
  font-size: 0.8rem;
  line-height: 1.4;
  color: var(--text-secondary);
  background-color: var(--bg-secondary);
}

.game-log::-webkit-scrollbar {
  display: none;
}

/* ===== 右侧：全局信息区 (25%) ===== */
.global-section {
  display: flex;
  flex-direction: column;
  gap: var(--gap);
  width: 25%;
  height: 100%;
}

.global-status {
  background-color: var(--bg-secondary);
  border-radius: var(--border-radius);
  padding: 16px var(--panel-padding);
  border: 1px solid var(--border);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  position: relative;
}

.status-title {
  font-size: 0.95rem;
  color: var(--accent);
  margin-bottom: 10px;
  display: flex;
  align-items: baseline;
  gap: 8px;
  font-weight: 700;
}

.status-title i {
  color: var(--accent);
}

.status-content {
  font-size: 1.1rem;
  color: var(--text-primary);
  line-height: 1.6;
  overflow: hidden;
  display: flex;
  white-space: pre-wrap;
  word-wrap: break-word;
}

/* 更多菜单 */
.more-menu-container {
  position: absolute;
  top: 12px;
  right: 12px;
}

.more-menu-btn {
  width: 32px;
  height: 32px;
  border-radius: 6px;
  border: 1px solid var(--border);
  background: var(--bg-tertiary);
  color: var(--text-secondary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.more-menu-btn:hover {
  border-color: var(--accent);
  color: var(--accent);
}

.more-menu-dropdown {
  position: absolute;
  top: calc(100% + 4px);
  right: 0;
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 4px;
  min-width: 140px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  z-index: 100;
  opacity: 0;
  visibility: hidden;
  transform: translateY(-4px);
  transition: all 0.2s ease;
}

.more-menu-dropdown.show {
  opacity: 1;
  visibility: visible;
  transform: translateY(0);
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 8px 12px;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: var(--text-primary);
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.2s;
}

.menu-item:hover {
  background: var(--bg-tertiary);
}

.menu-item.end-game {
  color: #ef4444;
}

.menu-item.end-game:hover {
  background: rgba(239, 68, 68, 0.1);
}

.action-section {
  background-color: var(--bg-secondary);
  border-radius: var(--border-radius);
  flex: 1;
  display: flex;
  flex-direction: column;
  border: 1px solid var(--border);
  overflow: hidden;
}

.action-header {
  padding: 8px var(--panel-padding);
  background-color: var(--bg-tertiary);
  border-bottom: 1px solid var(--border);
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  min-height: 36px;
}

.action-title {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
  display: flex;
  align-items: center;
  gap: 10px;
}

.action-title i {
  color: var(--accent);
}

.action-count {
  color: var(--text-secondary);
  font-size: 0.85rem;
}

.action-content {
  flex: 1;
  padding: var(--panel-padding);
  overflow-y: auto;
  font-size: 0.9rem;
  line-height: 1.5;
  color: var(--text-secondary);
  background-color: var(--bg-primary);
}

.action-content::-webkit-scrollbar {
  width: 6px;
}

.action-content::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.1);
}

.action-content::-webkit-scrollbar-thumb {
  background: var(--accent);
  border-radius: 3px;
}

.action-item {
  background-color: var(--bg-tertiary);
  border-left: 4px solid var(--accent);
  padding: 10px;
  margin-bottom: 8px;
  border-radius: 0 2px 2px 0;
  font-family: 'Consolas', monospace;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.action-item[data-color='red'] { border-left-color: #cc2828; }
.action-item[data-color='green'] { border-left-color: #37af37; }
.action-item[data-color='blue'] { border-left-color: #35a0d5; }
.action-item[data-color='yellow'] { border-left-color: #e8e83d; }
.action-item[data-color='grey'] { border-left-color: #a1a1a1; }
.action-item[data-color='brown'] { border-left-color: #85491d; }
.action-item[data-color='black'] { border-left-color: #595959; }
.action-item[data-color='white'] { border-left-color: #ffffff; }

.global-input {
  background-color: var(--bg-secondary);
  border-radius: var(--border-radius);
  padding: var(--panel-padding);
  height: 70px;
  border: 1px solid var(--border);
  display: flex;
  flex-direction: column;
}

.input-group {
  display: flex;
  gap: 8px;
  flex: 1;
}

.input-group input {
  flex: 1;
  padding: 10px 12px;
  border: 1px solid var(--border);
  border-radius: 4px;
  background-color: var(--bg-primary);
  color: var(--text-primary);
  font-size: 0.95rem;
  font-family: inherit;
  outline: none;
  transition: border-color 0.2s;
}

.input-group input:focus {
  border-color: var(--accent);
}

.send-btn {
  background-color: var(--accent);
  color: white;
  border: none;
  width: 44px;
  border-radius: 4px;
  font-size: 1.05rem;
  cursor: pointer;
  transition: background-color 0.2s;
  flex-shrink: 0;
}

.send-btn:hover {
  background-color: #0069d9;
}

/* 滚动条优化 */
::-webkit-scrollbar {
  width: 6px;
}

::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.1);
}

::-webkit-scrollbar-thumb {
  background: rgba(100, 100, 100, 0.5);
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: rgba(150, 150, 150, 0.7);
}

.player-log::-webkit-scrollbar-thumb,
.action-content::-webkit-scrollbar-thumb {
  background: var(--accent);
}

/* 响应式 */
@media (max-width: 1200px) {
  .players-monitor {
    width: 25%;
  }
  .middle-section {
    width: 50%;
  }
  .global-section {
    width: 25%;
  }
}

@media (max-width: 768px) {
  .main-container {
    flex-direction: column;
    height: auto;
    overflow-y: auto;
  }

  .players-monitor,
  .middle-section,
  .global-section {
    width: 100%;
    height: auto;
    min-height: 400px;
  }
}
</style>
