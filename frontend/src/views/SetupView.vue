<template>
  <main class="setup-page">
    <div class="setup-container">
    <!-- 顶部区域 -->
    <div class="setup-header">
      <h1 class="setup-title">游戏设置</h1>
      <div class="header-actions">
        <button type="button" class="btn btn-secondary" @click="goBack">
          <i class="fas fa-times"></i>
          <span>取消</span>
        </button>
        <button type="button" class="btn btn-danger" @click="resetForm">
          <i class="fas fa-rotate-left"></i>
          <span>重置</span>
        </button>
        <button type="button" class="btn btn-primary" @click="handleSubmit">
          <span>开始游戏</span>
          <i class="fas fa-play"></i>
        </button>
      </div>
    </div>

    <!-- 主内容区 - 三列布局 -->
    <div class="setup-main">
      <!-- 左侧：玩家配置 -->
      <div class="setup-section">
        <div class="section-title">
          <i class="fas fa-users"></i>
          <span>玩家配置</span>
        </div>

        <!-- 玩家数量选择 -->
        <div class="player-count-row">
          <button
            v-for="count in [3, 4, 5]"
            :key="count"
            type="button"
            class="count-btn"
            :class="{ active: form.playerCount === count }"
            @click="form.playerCount = count"
          >
            {{ count }}人
          </button>
        </div>

        <!-- 玩家卡片列表 -->
        <div class="player-cards">
          <div
            v-for="player in form.playerCount"
            :key="player"
            class="player-card"
          >
            <span class="player-label">玩家 {{ player }}</span>
            <div class="player-type-selector">
              <button
                type="button"
                class="type-btn"
                :class="{ active: form.players[player - 1].type === 'human' }"
                @click="form.players[player - 1].type = 'human'"
              >
                <i class="fas fa-user"></i>
                人类
              </button>
              <button
                type="button"
                class="type-btn"
                :class="{ active: form.players[player - 1].type === 'ai' }"
                @click="form.players[player - 1].type = 'ai'"
              >
                <i class="fas fa-robot"></i>
                电脑
              </button>
            </div>
            <div class="player-id-input-wrapper">
              <div
                v-if="form.players[player - 1].type === 'human'"
                class="input-with-check"
                :class="{ 'is-filled': form.players[player - 1].playerId }"
              >
                <input
                  v-model="form.players[player - 1].playerId"
                  type="text"
                  class="player-id-input"
                  placeholder="输入玩家ID"
                />
                <i class="fas fa-check check-icon"></i>
              </div>
              <button
                v-else
                type="button"
                class="strategy-btn"
                :class="{ 'has-strategy': form.players[player - 1].strategy }"
                @click="openStrategyModal(player - 1)"
              >
                <span>{{ form.players[player - 1].strategy ? getStrategyName(form.players[player - 1].strategy) : '选择策略' }}</span>
                <i class="fas fa-chevron-right"></i>
                <i class="fas fa-check check-icon"></i>
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- 中间：游戏模式 -->
      <div class="setup-section">
        <div class="section-title">
          <i class="fas fa-gamepad"></i>
          <span>游戏模式</span>
        </div>

        <div class="mode-selector">
          <div
            v-for="mode in gameModes"
            :key="mode.value"
            class="mode-card"
            :class="{ active: form.gameMode === mode.value }"
            @click="form.gameMode = mode.value"
          >
            <div class="mode-icon"><i :class="mode.icon"></i></div>
            <div class="mode-info">
              <div class="mode-name">{{ mode.name }}</div>
              <div class="mode-desc">{{ mode.desc }}</div>
            </div>
            <!-- 自定义模式配置按钮 -->
            <button
              v-if="mode.value === 'custom' && form.gameMode === 'custom'"
              type="button"
              class="mode-config-btn"
              @click.stop="showCustomModeModal = true"
            >
              <i class="fas fa-cog"></i>
              配置
            </button>
          </div>
        </div>
      </div>

      <!-- 右侧：初始设置 -->
      <div class="setup-section">
        <div class="section-title">
          <i class="fas fa-sliders-h"></i>
          <span>初始设置</span>
        </div>

        <!-- 玩家顺序 -->
        <div class="init-item">
          <div class="init-label">
            <i class="fas fa-list-ol"></i>
            <span>玩家顺序</span>
          </div>
          <div class="order-toggle">
            <button
              type="button"
              class="order-btn"
              :class="{ active: form.playerOrder === '随机' }"
              @click="form.playerOrder = '随机'"
            >
              <i class="fas fa-shuffle"></i>
              随机
            </button>
            <button
              type="button"
              class="order-btn"
              :class="{ active: form.playerOrder === '指定' }"
              @click="form.playerOrder = '指定'"
            >
              <i class="fas fa-sort-amount-down"></i>
              指定
            </button>
          </div>
          <!-- 指定顺序时的排序列表 -->
          <div v-if="form.playerOrder === '指定'" class="player-order-container">
            <!-- 玩家卡片区域（可拖拽） -->
            <div class="player-cards-row">
              <div
                v-for="(player, index) in playerOrderList"
                :key="'card-'+player.id"
                class="player-card-slot"
                :class="{ dragging: dragIndex === index }"
                draggable="true"
                @dragstart="handleOrderDragStart($event, index)"
                @dragover.prevent="handleOrderDragOver($event, index)"
                @drop="handleOrderDrop($event, index)"
                @dragend="handleOrderDragEnd"
              >
                <span class="slot-name">{{ player.name.replace(' ', '') }}</span>
                <i class="fas fa-grip-vertical slot-handle"></i>
              </div>
            </div>
            <!-- 位置序号区域（固定） -->
            <div class="position-numbers-row">
              <span
                v-for="index in playerOrderList.length"
                :key="'num-'+index"
                class="position-number"
              >{{ index }}</span>
            </div>
            <!-- 控制按钮区域（固定） -->
            <div class="position-controls-row">
              <div
                v-for="index in playerOrderList.length"
                :key="'ctrl-'+index"
                class="position-controls"
              >
                <button
                  type="button"
                  class="slot-btn"
                  :disabled="index === 1"
                  @click="movePlayer(index - 1, index - 2)"
                >
                  <i class="fas fa-chevron-left"></i>
                </button>
                <button
                  type="button"
                  class="slot-btn"
                  :disabled="index === playerOrderList.length"
                  @click="movePlayer(index - 1, index)"
                >
                  <i class="fas fa-chevron-right"></i>
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- 初始板块配置 -->
        <div class="init-item">
          <div class="init-label">
            <i class="fas fa-th-large"></i>
            <span>初始板块</span>
          </div>
          <div class="order-toggle">
            <button
              type="button"
              class="order-btn"
              :class="{ active: form.initSettings.mode === '随机' }"
              @click="form.initSettings.mode = '随机'"
            >
              <i class="fas fa-shuffle"></i>
              随机
            </button>
            <button
              type="button"
              class="order-btn"
              :class="{ active: form.initSettings.mode === '自定义' }"
              @click="form.initSettings.mode = '自定义'"
            >
              <i class="fas fa-cogs"></i>
              自定义
            </button>
          </div>
          <!-- 自定义入口 -->
          <button
            v-if="form.initSettings.mode === '自定义'"
            type="button"
            class="custom-entry-btn"
            @click="showInitModal = true"
          >
            <i class="fas fa-edit"></i>
            <span>进入配置</span>
            <i class="fas fa-chevron-right"></i>
          </button>
        </div>
      </div>
    </div>

    <!-- 自定义游戏模式配置弹窗 -->
    <Modal v-model="showCustomModeModal" title="自定义游戏配置">
      <div class="custom-mode-options">
        <div class="custom-option">
          <div class="custom-option-label">回合数</div>
          <div class="custom-option-input">
            <button
              v-for="round in [4, 5, 6]"
              :key="round"
              type="button"
              class="custom-option-btn"
              :class="{ active: customSettings.rounds === round }"
              @click="customSettings.rounds = round"
            >
              {{ round }}轮
            </button>
          </div>
        </div>
        <div class="custom-option">
          <div class="custom-option-label">初始资源倍率</div>
          <div class="custom-option-input">
            <button
              v-for="rate in [0.5, 1, 1.5, 2]"
              :key="rate"
              type="button"
              class="custom-option-btn"
              :class="{ active: customSettings.resourceRate === rate }"
              @click="customSettings.resourceRate = rate"
            >
              {{ rate }}x
            </button>
          </div>
        </div>
        <div class="custom-option">
          <div class="custom-option-label">计分板类型</div>
          <div class="custom-option-input">
            <button
              v-for="type in ['标准', '随机', '自定义']"
              :key="type"
              type="button"
              class="custom-option-btn"
              :class="{ active: customSettings.scoringType === type }"
              @click="customSettings.scoringType = type"
            >
              {{ type }}
            </button>
          </div>
        </div>
      </div>
      <template #footer>
        <button type="button" class="btn btn-secondary" @click="showCustomModeModal = false">
          取消
        </button>
        <button type="button" class="btn btn-primary" @click="saveCustomSettings">
          保存
        </button>
      </template>
    </Modal>

    <!-- AI策略弹窗 -->
    <Modal
      v-model="showStrategyModalOpen"
      :title="`AI策略 - 玩家 ${(showStrategyModal ?? 0) + 1}`"
      size="small"
      @close="closeStrategyModal"
    >
      <div class="strategy-options">
        <div
          v-for="strategy in aiStrategies"
          :key="strategy.value"
          class="strategy-option"
          :class="{ active: form.players[showStrategyModal]?.strategy === strategy.value }"
          @click="selectStrategy(strategy.value)"
        >
          <div class="strategy-icon"><i :class="strategy.icon"></i></div>
          <div class="strategy-info">
            <div class="strategy-name">{{ strategy.name }}</div>
            <div class="strategy-desc">{{ strategy.desc }}</div>
          </div>
        </div>
      </div>
    </Modal>

    <!-- 初始板块弹窗 -->
    <Modal v-model="showInitModal" title="初始板块配置">
      <div class="init-modal-layout">
        <!-- 左侧导航 -->
        <div class="init-nav">
          <button
            v-for="item in initNavItems"
            :key="item.id"
            type="button"
            class="init-nav-item"
            :class="{ active: activeInitNav === item.id }"
            @click="activeInitNav = item.id"
          >
            <div class="nav-item-left">
              <i :class="item.icon"></i>
              <span>{{ item.name }}</span>
              <i
                v-if="initNavRandom[item.id] || (!initNavRandom[item.id] && isNavItemComplete(item.id))"
                class="fas fa-check nav-complete-icon"
              ></i>
            </div>
            <label class="nav-toggle" @click.stop>
              <input
                type="checkbox"
                v-model="initNavRandom[item.id]"
                @change="handleNavRandomChange(item.id)"
              >
              <span class="nav-toggle-switch"></span>
            </label>
          </button>
        </div>

        <!-- 右侧内容 -->
        <div class="init-content">
          <!-- 规划卡配置 -->
          <div v-if="activeInitNav === 'planningCards'">
            <div v-if="!initNavRandom.planningCards" class="planning-cards-config">
              <p class="planning-cards-hint">
                <i class="fas fa-info-circle"></i>
                <span>请选择一种颜色的规划卡，其将不参与本局游戏</span>
              </p>
              <div class="planning-cards-grid">
                <!-- 第一行：3张 -->
                <div class="planning-cards-row row-3">
                  <div
                    v-for="index in [0, 1, 2]"
                    :key="index"
                    class="planning-card"
                    :class="{ active: selectedPlanningCard === index }"
                    @click="selectedPlanningCard = selectedPlanningCard === index ? null : index"
                  >
                    <div class="planning-card-image" :style="getPlanningCardStyle(index)"></div>
                    <div class="planning-card-name">{{ planningCardNames[index] }}</div>
                    <div v-if="selectedPlanningCard === index" class="planning-card-check">
                      <i class="fas fa-check"></i>
                    </div>
                  </div>
                </div>
                <!-- 第二行：4张 -->
                <div class="planning-cards-row row-4">
                  <div
                    v-for="index in [3, 4, 5, 6]"
                    :key="index"
                    class="planning-card"
                    :class="{ active: selectedPlanningCard === index }"
                    @click="selectedPlanningCard = selectedPlanningCard === index ? null : index"
                  >
                    <div class="planning-card-image" :style="getPlanningCardStyle(index)"></div>
                    <div class="planning-card-name">{{ planningCardNames[index] }}</div>
                    <div v-if="selectedPlanningCard === index" class="planning-card-check">
                      <i class="fas fa-check"></i>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div v-else class="init-random-notice">
              <i class="fas fa-shuffle"></i>
              <p>已启用随机设置，规划卡将随机分配</p>
            </div>
          </div>

          <!-- 派系配置 -->
          <div v-else-if="activeInitNav === 'factions'">
            <div v-if="!initNavRandom.factions" class="factions-config">
              <p class="factions-hint">
                <i class="fas fa-info-circle"></i>
                <span>请选择 {{ requiredFactionCount }} 个派系参与本局游戏（已选 {{ selectedFactions.length }} 个）</span>
              </p>
              <div class="factions-grid">
                <!-- 第一行：3个 -->
                <div class="factions-row row-3">
                  <div
                    v-for="index in [0, 1, 2]"
                    :key="index"
                    class="faction-card"
                    :class="{ active: selectedFactions.includes(index) }"
                    @click="toggleFactionSelection(index)"
                  >
                    <div class="faction-card-image" :style="getFactionCardStyle(index)"></div>
                    <div class="faction-card-name">{{ factionNames[index] }}</div>
                    <div v-if="selectedFactions.includes(index)" class="faction-card-check">
                      <i class="fas fa-check"></i>
                    </div>
                  </div>
                </div>
                <!-- 第二行：3个 -->
                <div class="factions-row row-3">
                  <div
                    v-for="index in [3, 4, 5]"
                    :key="index"
                    class="faction-card"
                    :class="{ active: selectedFactions.includes(index) }"
                    @click="toggleFactionSelection(index)"
                  >
                    <div class="faction-card-image" :style="getFactionCardStyle(index)"></div>
                    <div class="faction-card-name">{{ factionNames[index] }}</div>
                    <div v-if="selectedFactions.includes(index)" class="faction-card-check">
                      <i class="fas fa-check"></i>
                    </div>
                  </div>
                </div>
                <!-- 第三行：3个 -->
                <div class="factions-row row-3">
                  <div
                    v-for="index in [6, 7, 8]"
                    :key="index"
                    class="faction-card"
                    :class="{ active: selectedFactions.includes(index) }"
                    @click="toggleFactionSelection(index)"
                  >
                    <div class="faction-card-image" :style="getFactionCardStyle(index)"></div>
                    <div class="faction-card-name">{{ factionNames[index] }}</div>
                    <div v-if="selectedFactions.includes(index)" class="faction-card-check">
                      <i class="fas fa-check"></i>
                    </div>
                  </div>
                </div>
                <!-- 第四行：3个 -->
                <div class="factions-row row-3">
                  <div
                    v-for="index in [9, 10, 11]"
                    :key="index"
                    class="faction-card"
                    :class="{ active: selectedFactions.includes(index) }"
                    @click="toggleFactionSelection(index)"
                  >
                    <div class="faction-card-image" :style="getFactionCardStyle(index)"></div>
                    <div class="faction-card-name">{{ factionNames[index] }}</div>
                    <div v-if="selectedFactions.includes(index)" class="faction-card-check">
                      <i class="fas fa-check"></i>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div v-else class="init-random-notice">
              <i class="fas fa-shuffle"></i>
              <p>已启用随机设置，派系将随机分配</p>
            </div>
          </div>

          <!-- 宫殿板块配置 -->
          <div v-else-if="activeInitNav === 'palace'">
            <div v-if="!initNavRandom.palace" class="palace-config">
              <p class="palace-hint">
                <i class="fas fa-info-circle"></i>
                <span>请选择 {{ requiredPalaceCount }} 个宫殿板块参与本局游戏（已选 {{ selectedPalaces.length }} 个）</span>
              </p>
              <div class="palace-grid">
                <!-- 第一行：4个 -->
                <div class="palace-row row-4">
                  <div
                    v-for="index in [0, 1, 2, 3]"
                    :key="index"
                    class="palace-card"
                    :class="{ active: selectedPalaces.includes(index) }"
                    @click="togglePalaceSelection(index)"
                  >
                    <div class="palace-card-image" :style="getPalaceCardStyle(index)"></div>
                    <div v-if="selectedPalaces.includes(index)" class="palace-card-check">
                      <i class="fas fa-check"></i>
                    </div>
                  </div>
                </div>
                <!-- 第二行：4个 -->
                <div class="palace-row row-4">
                  <div
                    v-for="index in [4, 5, 6, 7]"
                    :key="index"
                    class="palace-card"
                    :class="{ active: selectedPalaces.includes(index) }"
                    @click="togglePalaceSelection(index)"
                  >
                    <div class="palace-card-image" :style="getPalaceCardStyle(index)"></div>
                    <div v-if="selectedPalaces.includes(index)" class="palace-card-check">
                      <i class="fas fa-check"></i>
                    </div>
                  </div>
                </div>
                <!-- 第三行：4个 -->
                <div class="palace-row row-4">
                  <div
                    v-for="index in [8, 9, 10, 11]"
                    :key="index"
                    class="palace-card"
                    :class="{ active: selectedPalaces.includes(index) }"
                    @click="togglePalaceSelection(index)"
                  >
                    <div class="palace-card-image" :style="getPalaceCardStyle(index)"></div>
                    <div v-if="selectedPalaces.includes(index)" class="palace-card-check">
                      <i class="fas fa-check"></i>
                    </div>
                  </div>
                </div>
                <!-- 第四行：4个 -->
                <div class="palace-row row-4">
                  <div
                    v-for="index in [12, 13, 14, 15]"
                    :key="index"
                    class="palace-card"
                    :class="{ active: selectedPalaces.includes(index) }"
                    @click="togglePalaceSelection(index)"
                  >
                    <div class="palace-card-image" :style="getPalaceCardStyle(index)"></div>
                    <div v-if="selectedPalaces.includes(index)" class="palace-card-check">
                      <i class="fas fa-check"></i>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div v-else class="init-random-notice">
              <i class="fas fa-shuffle"></i>
              <p>已启用随机设置，宫殿板块将随机分配</p>
            </div>
          </div>

          <!-- 其他配置项的占位 -->
          <div v-else-if="!initNavRandom[activeInitNav]" class="init-config">
            <p class="config-placeholder">
              {{ getInitNavName(activeInitNav) }} 配置内容（待实现）
            </p>
          </div>
          <div v-else class="init-random-notice">
            <i class="fas fa-shuffle"></i>
            <p>已启用随机设置，{{ getInitNavName(activeInitNav) }}将随机分配</p>
          </div>
        </div>
      </div>
    </Modal>
    </div>

  </main>
</template>

<script setup>
import { reactive, ref, watch, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useGameStore } from '../stores/game'
import Modal from '../components/Modal.vue'

const router = useRouter()
const gameStore = useGameStore()

const gameModes = [
  { value: 'standard', name: '标准模式', desc: '45分钟基础时间 + 60秒读秒', icon: 'fas fa-chess' },
  { value: 'quick', name: '快速模式', desc: '25分钟基础时间 + 30秒读秒', icon: 'fas fa-bolt' },
  { value: 'custom', name: '自定义', desc: '自由配置各项参数', icon: 'fas fa-cogs' }
]

const aiStrategies = [
  { value: 'random', name: '随机策略', desc: '随机选择行动', icon: 'fas fa-dice' },
  { value: 'aggressive', name: '激进策略', desc: '优先扩张和进攻', icon: 'fas fa-fire' },
  { value: 'defensive', name: '保守策略', desc: '优先防守和发展', icon: 'fas fa-shield' }
]

const initNavItems = [
  { id: 'planningCards', name: '规划卡', icon: 'fas fa-address-card' },
  { id: 'factions', name: '派系', icon: 'fas fa-users' },
  { id: 'palace', name: '宫殿板块', icon: 'fas fa-building' },
  { id: 'roundScoring', name: '轮次计分', icon: 'fas fa-calendar' },
  { id: 'finalScoring', name: '最终计分', icon: 'fas fa-trophy' },
  { id: 'abilities', name: '能力板块', icon: 'fas fa-magic' },
  { id: 'techs', name: '高科板块', icon: 'fas fa-microchip' },
  { id: 'bookActions', name: '书行动', icon: 'fas fa-book' }
]

const showInitModal = ref(false)
const showStrategyModal = ref(null)
const showCustomModeModal = ref(false)

// 策略弹窗的显示状态（转换为布尔值）
const showStrategyModalOpen = computed({
  get: () => showStrategyModal.value !== null,
  set: (val) => { if (!val) showStrategyModal.value = null }
})

// 选择策略
function selectStrategy(strategyValue) {
  if (showStrategyModal.value !== null) {
    form.players[showStrategyModal.value].strategy = strategyValue
  }
  closeStrategyModal()
}
const activeInitNav = ref('planningCards')

// 左侧导航栏各项目的随机开关状态（默认关闭，即非随机）
const initNavRandom = reactive({
  planningCards: false,
  factions: false,
  palace: false,
  roundScoring: false,
  finalScoring: false,
  abilities: false,
  techs: false,
  bookActions: false
})

// 处理导航栏随机开关变化
function handleNavRandomChange(navId) {
  console.log(`${navId} 随机设置:`, initNavRandom[navId])
}

// 选中的规划卡索引
const selectedPlanningCard = ref(null)

// 选中的派系卡片索引数组（多选）
const selectedFactions = ref([])

// 获取需要选择的派系数量（玩家数量 + 1）
const requiredFactionCount = computed(() => form.playerCount + 1)

// 选中的宫殿板块索引数组（多选，只取前16张）
const selectedPalaces = ref([])

// 获取需要选择的宫殿板块数量（玩家数量 + 1）
const requiredPalaceCount = computed(() => form.playerCount + 1)

// 宫殿板块选择是否完成
const isPalaceComplete = computed(() => selectedPalaces.value.length === requiredPalaceCount.value)

// 派系选择是否完成
const isFactionsComplete = computed(() => selectedFactions.value.length === requiredFactionCount.value)

// 派系名称列表（12个）
const factionNames = [
  '幻术师', '航海家', '哲学家',
  '通灵师', '猫人', '鼹鼠',
  '奥马尔', '哥布林', '发明家',
  '蜥蜴人', '僧侣', '神佑者'
]

// 规划卡名称列表（7个）
const planningCardNames = ['沙漠', '森林', '沼泽', '荒地', '湖泊', '山脉', '平原']

// 获取规划卡背景样式（7等分切割）
function getPlanningCardStyle(index) {
  // 7张卡片横向排列，使用精确百分比定位
  // 每张卡片占 100/7 ≈ 14.2857%，中心点在 7.1429%, 21.4286%, 35.7143%...
  const positions = [0, 16.6667, 33.3333, 50, 66.6667, 83.3333, 100]
  return {
    backgroundImage: 'url(/assets/images/terrain_tiles.jpg)',
    backgroundSize: '700% 100%',
    backgroundPositionX: `${positions[index]}%`
  }
}

// 获取派系卡片背景样式（12等分切割）
function getFactionCardStyle(index) {
  // 12张卡片横向排列，使用精确百分比定位
  // 位置点：0%, 9.091%, 18.182%, 27.273%, 36.364%, 45.455%, 54.545%, 63.636%, 72.727%, 81.818%, 90.909%, 100%
  const positions = [0, 9.0909, 18.1818, 27.2727, 36.3636, 45.4545, 54.5455, 63.6364, 72.7273, 81.8182, 90.9091, 100]
  return {
    backgroundImage: 'url(/assets/images/faction_tiles.jpg)',
    backgroundSize: '1200% 100%',
    backgroundPositionX: `${positions[index]}%`
  }
}

// 切换派系选择状态
function toggleFactionSelection(index) {
  const currentIndex = selectedFactions.value.indexOf(index)
  if (currentIndex > -1) {
    // 已选中，取消选择
    selectedFactions.value.splice(currentIndex, 1)
  } else {
    // 未选中，检查是否已达到最大选择数量
    if (selectedFactions.value.length >= requiredFactionCount.value) {
      return // 已达上限，点击无效
    }
    selectedFactions.value.push(index)
  }
}

// 获取宫殿板块背景样式（18等分切割，只展示前16张）
function getPalaceCardStyle(index) {
  // 18张卡片横向排列，使用精确百分比定位
  // 位置点：0%, 5.882%, 11.765%, 17.647%, 23.529%, 29.412%, 35.294%, 41.176%,
  //        47.059%, 52.941%, 58.824%, 64.706%, 70.588%, 76.471%, 82.353%, 88.235%, 94.118%, 100%
  const positions = [0, 5.8824, 11.7647, 17.6471, 23.5294, 29.4118, 35.2941, 41.1765,
                     47.0588, 52.9412, 58.8235, 64.7059, 70.5882, 76.4706, 82.3529, 88.2353, 94.1176, 100]
  return {
    backgroundImage: 'url(/assets/images/stronghold_tiles.jpg)',
    backgroundSize: '1800% 100%',
    backgroundPositionX: `${positions[index]}%`
  }
}

// 切换宫殿板块选择状态
function togglePalaceSelection(index) {
  const currentIndex = selectedPalaces.value.indexOf(index)
  if (currentIndex > -1) {
    // 已选中，取消选择
    selectedPalaces.value.splice(currentIndex, 1)
  } else {
    // 未选中，检查是否已达到最大选择数量
    if (selectedPalaces.value.length >= requiredPalaceCount.value) {
      return // 已达上限，点击无效
    }
    selectedPalaces.value.push(index)
  }
}

// 自定义游戏模式设置
const customSettings = reactive({
  rounds: 5,
  resourceRate: 1,
  scoringType: '标准'
})

function saveCustomSettings() {
  showCustomModeModal.value = false
}

// 玩家顺序列表（用于指定顺序）
const playerOrderList = ref([
  { id: 1, name: '玩家 1' },
  { id: 2, name: '玩家 2' },
  { id: 3, name: '玩家 3' }
])

// 位置列表
const positionList = computed(() => {
  return Array.from({ length: form.playerCount }, (_, i) => i + 1)
})

// 拖动排序相关
const dragIndex = ref(null)

function handleOrderDragStart(event, index) {
  dragIndex.value = index
  event.dataTransfer.effectAllowed = 'move'
}

function handleOrderDragOver(event, index) {
  event.preventDefault()
}

function handleOrderDrop(event, targetIndex) {
  event.preventDefault()
  if (dragIndex.value === null || dragIndex.value === targetIndex) return

  // 移动元素到新位置
  const item = playerOrderList.value[dragIndex.value]
  playerOrderList.value.splice(dragIndex.value, 1)
  playerOrderList.value.splice(targetIndex, 0, item)

  dragIndex.value = null
}

function handleOrderDragEnd() {
  dragIndex.value = null
}

// 通过按钮移动玩家
function movePlayer(fromIndex, toIndex) {
  if (toIndex < 0 || toIndex >= playerOrderList.value.length) return
  const item = playerOrderList.value[fromIndex]
  playerOrderList.value.splice(fromIndex, 1)
  playerOrderList.value.splice(toIndex, 0, item)
}

function getStrategyName(value) {
  if (!value) return '选择策略'
  const strategy = aiStrategies.find(s => s.value === value)
  return strategy ? strategy.name : '选择策略'
}

function getInitNavName(id) {
  const item = initNavItems.find(i => i.id === id)
  return item ? item.name : ''
}

// 检查导航项是否已完成配置（开关关闭状态下）
function isNavItemComplete(navId) {
  switch (navId) {
    case 'planningCards':
      return selectedPlanningCard.value !== null
    case 'factions':
      return isFactionsComplete.value
    case 'palace':
      return isPalaceComplete.value
    case 'roundScoring':
      // TODO: 实现轮次计分选择完成条件
      return false
    case 'finalScoring':
      // TODO: 实现最终计分选择完成条件
      return false
    case 'abilities':
      // TODO: 实现能力板块选择完成条件
      return false
    case 'techs':
      // TODO: 实现高科板块选择完成条件
      return false
    case 'bookActions':
      // TODO: 实现书行动选择完成条件
      return false
    default:
      return false
  }
}

function openStrategyModal(playerIndex) {
  if (form.players[playerIndex].type === 'ai') {
    showStrategyModal.value = playerIndex
  }
}

function closeStrategyModal() {
  showStrategyModal.value = null
}

// 初始化玩家配置
function createPlayers(count) {
  const players = []
  for (let i = 0; i < count; i++) {
    players.push({ type: 'human', strategy: '' })
  }
  return players
}

const form = reactive({
  playerCount: 3,
  gameMode: 'standard',
  playerOrder: '随机',
  players: createPlayers(3),
  initSettings: {
    mode: '随机'
  }
})

// 监听玩家数量变化
watch(() => form.playerCount, (newCount) => {
  if (newCount > form.players.length) {
    for (let i = form.players.length; i < newCount; i++) {
      form.players.push({ type: 'human', strategy: '' })
    }
  } else {
    form.players.splice(newCount)
  }
  // 同步更新顺序列表
  const newList = []
  for (let i = 0; i < newCount; i++) {
    newList.push({ id: i + 1, name: `玩家 ${i + 1}` })
  }
  playerOrderList.value = newList
})

function goBack() {
  gameStore.resetGame()
  router.push('/')
}

function resetForm() {
  form.playerCount = 3
  form.gameMode = 'standard'
  form.playerOrder = '随机'
  form.players = createPlayers(3)
  form.initSettings.mode = '随机'
  // 重置顺序列表
  playerOrderList.value = [
    { id: 1, name: '玩家 1' },
    { id: 2, name: '玩家 2' },
    { id: 3, name: '玩家 3' }
  ]
}

function handleSubmit() {
  gameStore.setSettings({ ...form })
  gameStore.startGame()
  router.push('/game')
}
</script>

<style scoped>
.setup-page {
  height: calc(100vh - var(--navbar-height));
  padding: 64px 96px;
  display: flex;
  flex-direction: column;
  background: var(--bg-primary);
  position: relative;
  box-sizing: border-box;
  overflow: hidden;
  align-items: center;
}

.setup-container {
  width: 100%;
  max-width: 90%;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.setup-page::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-image:
    linear-gradient(rgba(0, 123, 255, 0.02) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0, 123, 255, 0.02) 1px, transparent 1px);
  background-size: 50px 50px;
  pointer-events: none;
}

/* 顶部区域 */
.setup-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 0 48px;
  position: relative;
  z-index: 1;
  flex-shrink: 0;
}

.setup-title {
  font-size: var(--font-size-page-title);
  font-weight: 700;
  color: var(--text-primary);
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px 20px;
  border: none;
  border-radius: 8px;
  font-size: var(--font-size-body);
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.2s, color 0.2s, border-color 0.2s, box-shadow 0.2s;
  height: 44px;
  box-sizing: border-box;
  line-height: 1;
}

.btn i {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 1em;
  width: 1em;
}

.btn-secondary {
  background: var(--bg-tertiary);
  color: var(--text-secondary);
  border: 1px solid var(--border);
}

.btn-secondary:hover {
  background: var(--bg-secondary);
  color: var(--text-primary);
}

.btn-primary {
  background: var(--accent);
  color: white;
}

.btn-primary:hover {
  background: #0069d9;
  box-shadow: 0 4px 12px rgba(0, 123, 255, 0.3);
}

.btn-danger {
  background: var(--bg-tertiary);
  color: var(--text-secondary);
  border: 1px solid var(--border);
}

.btn-danger:hover {
  background: #dc3545;
  color: white;
  border-color: #dc3545;
  box-shadow: 0 4px 12px rgba(220, 53, 69, 0.3);
}

/* 主内容区 */
.setup-main {
  flex: 1;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 32px;
  min-height: 0;
  position: relative;
  z-index: 1;
}

.setup-section {
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 32px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: var(--font-size-card-title);
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 32px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
}

.section-title i {
  color: var(--accent);
}

/* 玩家配置 */
.player-count-row {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
  flex-shrink: 0;
}

.count-btn {
  flex: 1;
  padding: 12px 16px;
  background: var(--bg-tertiary);
  border: 1px solid var(--border);
  border-radius: 8px;
  color: var(--text-secondary);
  font-size: var(--font-size-small);
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.count-btn:hover {
  border-color: var(--accent);
  color: var(--text-primary);
}

.count-btn.active {
  background: var(--accent);
  border-color: var(--accent);
  color: white;
}

.player-cards {
  display: flex;
  flex-direction: column;
  gap: 12px;
  overflow-y: auto;
  flex: 1;
}

.player-card {
  display: flex;
  align-items: center;
  gap: 20px;
  background: var(--bg-tertiary);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 14px 18px;
  transition: all 0.2s;
}

.player-card:hover {
  border-color: rgba(0, 123, 255, 0.3);
}

.player-label {
  font-size: 0.9rem;
  font-weight: 700;
  color: var(--text-primary);
  min-width: 56px;
  letter-spacing: 0.5px;
}

.player-type-selector {
  display: flex;
  gap: 10px;
  flex: 1;
}

.type-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px 14px;
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: 8px;
  color: var(--text-secondary);
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.type-btn:hover {
  border-color: var(--accent);
  color: var(--text-primary);
  background: var(--bg-primary);
}

.type-btn.active {
  background: var(--accent);
  border-color: var(--accent);
  color: white;
  box-shadow: 0 2px 8px rgba(0, 123, 255, 0.25);
}

.type-btn i {
  font-size: 0.9rem;
}

.player-id-input-wrapper {
  margin-left: 4px;
  width: 110px;
}

/* 带检查图标的输入框容器 */
.input-with-check {
  position: relative;
  width: 100%;
}

.input-with-check .player-id-input {
  width: 100%;
  height: 38px;
  padding: 10px 28px 10px 12px;
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: 8px;
  color: var(--text-secondary);
  font-size: 0.8rem;
  font-weight: 500;
  text-align: left;
  outline: none;
  transition: all 0.2s;
  box-sizing: border-box;
}

.input-with-check .check-icon {
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 0.7rem;
  color: var(--accent);
  opacity: 0;
  transition: opacity 0.2s;
}

.input-with-check.is-filled .player-id-input {
  border-color: var(--accent);
  color: var(--text-primary);
}

.input-with-check.is-filled .check-icon {
  opacity: 1;
}

.player-id-input:focus {
  border-color: var(--accent);
  background: var(--bg-primary);
  color: var(--text-primary);
}

.player-id-input::placeholder {
  color: var(--text-secondary);
  font-size: 0.8rem;
}

/* 策略按钮 */
.strategy-btn {
  width: 100%;
  height: 38px;
  padding: 0 28px 0 12px;
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: 8px;
  color: var(--text-secondary);
  font-size: 0.8rem;
  font-weight: 500;
  line-height: 36px;
  cursor: pointer;
  display: flex;
  align-items: center;
  position: relative;
  transition: all 0.2s;
  box-sizing: border-box;
}

.strategy-btn span {
  text-align: left;
  line-height: 1;
}

.strategy-btn .fa-chevron-right {
  position: absolute;
  right: 10px;
  font-size: 0.7rem;
  color: var(--text-secondary);
}

.strategy-btn .check-icon {
  position: absolute;
  right: 10px;
  font-size: 0.7rem;
  color: var(--accent);
  opacity: 0;
  transition: opacity 0.2s;
}

.strategy-btn.has-strategy {
  border-color: var(--accent);
  color: var(--text-primary);
}

.strategy-btn.has-strategy .fa-chevron-right {
  display: none;
}

.strategy-btn.has-strategy .check-icon {
  opacity: 1;
}

.strategy-btn:hover {
  border-color: var(--accent);
  background: var(--bg-primary);
}

/* 游戏模式 */
.mode-selector {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.mode-card {
  display: flex;
  align-items: stretch;
  padding: 0;
  background: var(--bg-tertiary);
  border: 1px solid var(--border);
  border-radius: 16px;
  cursor: pointer;
  transition: all 0.25s ease;
  min-height: 120px;
  overflow: hidden;
}

.mode-card:hover {
  border-color: rgba(0, 123, 255, 0.5);
}

.mode-card.active {
  border-color: var(--accent);
}

.mode-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 120px;
  min-width: 120px;
  font-size: 2.5rem;
  color: var(--accent);
  background: var(--bg-secondary);
  transition: all 0.2s;
}

.mode-card.active .mode-icon {
  background: var(--accent);
  color: white;
}

.mode-config-btn {
  position: absolute;
  top: 12px;
  right: 12px;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: var(--accent);
  border: none;
  border-radius: 6px;
  color: white;
  font-size: 0.75rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  z-index: 10;
}

.mode-config-btn:hover {
  background: #0069d9;
  box-shadow: 0 2px 8px rgba(0, 123, 255, 0.3);
}

.mode-card {
  position: relative;
}

.mode-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 24px 28px;
}

.mode-name {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.mode-desc {
  font-size: 0.95rem;
  color: var(--text-secondary);
  line-height: 1.5;
}

/* 初始设置 */
.init-item {
  background: var(--bg-tertiary);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 16px;
}

.init-item:last-child {
  margin-bottom: 0;
}

.init-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: var(--font-size-small);
  color: var(--text-secondary);
  margin-bottom: 10px;
}

.init-label i {
  color: var(--accent);
}

.init-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: 6px;
  color: var(--text-primary);
  font-size: var(--font-size-small);
  cursor: pointer;
  transition: all 0.2s;
}

.init-btn:hover {
  border-color: var(--accent);
}

/* 玩家顺序切换 */
.order-toggle {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.order-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 10px 12px;
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: 8px;
  color: var(--text-secondary);
  font-size: var(--font-size-small);
  cursor: pointer;
  transition: all 0.2s;
}

.order-btn:hover {
  border-color: var(--accent);
  color: var(--text-primary);
}

.order-btn.active {
  background: var(--accent);
  border-color: var(--accent);
  color: white;
}

.order-btn i {
  font-size: 0.9rem;
}

/* 玩家顺序容器 - 三行独立布局 */
.player-order-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 16px;
  align-items: center;
}

/* 玩家卡片行（可拖拽） */
.player-cards-row {
  display: flex;
  flex-direction: row;
  gap: 28px;
  justify-content: center;
  flex-wrap: nowrap;
}

.player-card-slot {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 10px 4px;
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: 10px;
  cursor: grab;
  transition: all 0.2s ease;
  user-select: none;
  width: 40px;
  flex-shrink: 0;
}

.player-card-slot:hover {
  border-color: var(--accent);
  background: var(--bg-primary);
  transform: translateY(-2px);
}

.player-card-slot.dragging {
  opacity: 0.5;
  cursor: grabbing;
  border-color: var(--accent);
  background: rgba(0, 123, 255, 0.1);
}

.slot-name {
  font-size: 0.85rem;
  font-weight: 500;
  color: var(--text-primary);
  writing-mode: vertical-rl;
  text-orientation: upright;
  line-height: 1;
  letter-spacing: 0.4em;
}

.slot-handle {
  color: var(--text-secondary);
  font-size: 0.9rem;
  transition: color 0.2s;
}

.player-card-slot:hover .slot-handle {
  color: var(--accent);
}

/* 位置序号行（固定） */
.position-numbers-row {
  display: flex;
  flex-direction: row;
  gap: 28px;
  justify-content: center;
  flex-wrap: nowrap;
}

.position-number {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--accent);
  color: white;
  font-size: 0.85rem;
  font-weight: 700;
  border-radius: 50%;
  flex-shrink: 0;
  margin: 0 6px;
}

/* 控制按钮行（固定） */
.position-controls-row {
  display: flex;
  flex-direction: row;
  gap: 28px;
  justify-content: center;
  flex-wrap: nowrap;
}

.position-controls {
  display: flex;
  flex-direction: row;
  gap: 4px;
  width: 40px;
  justify-content: center;
}

.slot-btn {
  width: 18px;
  height: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-tertiary);
  border: 1px solid var(--border);
  border-radius: 5px;
  color: var(--text-secondary);
  font-size: 0.65rem;
  cursor: pointer;
  transition: all 0.2s;
  padding: 0;
}

.slot-btn:hover:not(:disabled) {
  border-color: var(--accent);
  color: var(--accent);
  background: var(--bg-secondary);
}

.slot-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

/* 自定义入口按钮 */
.custom-entry-btn {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: 8px;
  color: var(--text-primary);
  font-size: var(--font-size-small);
  cursor: pointer;
  transition: all 0.2s;
}

.custom-entry-btn:hover {
  border-color: var(--accent);
  background: var(--bg-primary);
}

.custom-entry-btn i:first-child {
  color: var(--accent);
}

.custom-entry-btn i:last-child {
  margin-left: auto;
  color: var(--text-secondary);
}

/* 自定义游戏模式配置 */
.custom-mode-options {
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.custom-option {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.custom-option-label {
  font-size: var(--font-size-body);
  font-weight: 600;
  color: var(--text-primary);
}

.custom-option-input {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.custom-option-btn {
  flex: 1;
  min-width: 60px;
  padding: 10px 16px;
  background: var(--bg-tertiary);
  border: 1px solid var(--border);
  border-radius: 8px;
  color: var(--text-secondary);
  font-size: var(--font-size-small);
  cursor: pointer;
  transition: all 0.2s;
}

.custom-option-btn:hover {
  border-color: var(--accent);
  color: var(--text-primary);
}

.custom-option-btn.active {
  background: var(--accent);
  border-color: var(--accent);
  color: white;
}

.init-btn span {
  flex: 1;
  text-align: left;
}

.init-btn i {
  color: var(--text-secondary);
}

/* 弹窗内容样式 */
.init-modal-layout {
  display: flex;
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

/* AI策略选项 */
.strategy-options {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.strategy-option {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 18px;
  background: var(--bg-tertiary);
  border: 1px solid var(--border);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
}

.strategy-option:hover {
  border-color: var(--accent);
}

.strategy-option.active {
  border-color: var(--accent);
  background: rgba(0, 123, 255, 0.1);
}

.strategy-icon {
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-secondary);
  border-radius: 10px;
  color: var(--accent);
  font-size: 1.2rem;
}

.strategy-option.active .strategy-icon {
  background: var(--accent);
  color: white;
}

.strategy-info {
  flex: 1;
}

.strategy-name {
  font-size: var(--font-size-body);
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.strategy-desc {
  font-size: var(--font-size-small);
  color: var(--text-secondary);
}

/* 初始板块弹窗 */
:deep(.modal-content) {
  height: 600px;
  max-height: 80vh;
}

.init-modal-layout {
  display: flex;
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.init-nav {
  width: 225px;
  flex-shrink: 0;
  padding: 16px 12px;
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  gap: 12px;
  overflow-y: auto;
  background: var(--bg-tertiary);
}

.init-nav-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0;
  background: transparent;
  border: 2px solid transparent;
  border-radius: 12px;
  color: var(--text-secondary);
  font-size: var(--font-size-small);
  text-align: left;
  cursor: pointer;
  overflow: hidden;
  position: relative;
  height: 44px;
}

/* 左侧标签部分 */
.nav-item-left {
  display: flex;
  align-items: center;
  gap: 0;
  padding: 0;
  flex: 1;
  height: 100%;
}

/* icon容器 - 固定宽度水平居中 */
.nav-item-left i {
  width: 44px;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--accent);
  font-size: 0.9rem;
  flex-shrink: 0;
}

/* 文字部分 - 左对齐，与蓝色背景保持距离 */
.nav-item-left span {
  color: var(--text-primary);
  flex: 1;
  padding-left: 12px;
}

/* 完成状态对钩图标 - 使用更高优先级覆盖 .nav-item-left i */
.nav-item-left .nav-complete-icon {
  width: 14px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--accent);
  font-size: 0.75rem;
  margin-left: auto;
  flex-shrink: 0;
}

/* 悬停状态 */
.init-nav-item:hover {
  background: rgba(0, 123, 255, 0.05);
}

/* 选中状态：蓝色外框包含全部内容 */
.init-nav-item.active {
  border-color: var(--accent);
  background: var(--bg-secondary);
}

/* 选中态：icon背景蓝色，文字保持原样（排除对钩图标） */
.init-nav-item.active .nav-item-left i:not(.nav-complete-icon) {
  background: var(--accent);
  color: white;
  border-radius: 10px 0 0 10px;
}

.init-nav-item.active .nav-item-left span {
  color: var(--text-primary);
  font-weight: 600;
}

/* 选中态：对钩保持蓝色内容透明底 */
.init-nav-item.active .nav-complete-icon {
  color: var(--accent);
  background: transparent;
}

/* 开关按钮样式 */
.nav-toggle {
  display: flex;
  align-items: center;
  padding: 0 12px;
  cursor: pointer;
  flex-shrink: 0;
  height: 100%;
}

.nav-toggle input {
  display: none;
}

.nav-toggle-switch {
  width: 32px;
  height: 18px;
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: 9px;
  position: relative;
}

.nav-toggle-switch::after {
  content: '';
  position: absolute;
  top: 1px;
  left: 1px;
  width: 14px;
  height: 14px;
  background: var(--text-secondary);
  border-radius: 50%;
  transition: left 0.2s ease;
}

/* 开关开启状态：蓝色背景 + 白色圆点 */
.nav-toggle input:checked + .nav-toggle-switch {
  background: var(--accent);
  border-color: var(--accent);
}

.nav-toggle input:checked + .nav-toggle-switch::after {
  left: 15px;
  background: white;
}

.init-content {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  min-height: 0;
}

.init-content-header {
  margin-bottom: 20px;
}

.toggle-label {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  font-size: var(--font-size-body);
  color: var(--text-primary);
}

.toggle-label input {
  display: none;
}

.toggle-switch {
  width: 44px;
  height: 24px;
  background: var(--bg-tertiary);
  border-radius: 12px;
  position: relative;
  transition: background 0.2s;
}

.toggle-switch::after {
  content: '';
  position: absolute;
  top: 2px;
  left: 2px;
  width: 20px;
  height: 20px;
  background: var(--text-secondary);
  border-radius: 50%;
  transition: all 0.2s;
}

.toggle-label input:checked + .toggle-switch {
  background: var(--accent);
}

.toggle-label input:checked + .toggle-switch::after {
  left: 22px;
  background: white;
}

.init-config {
  padding: 40px 20px;
  background: var(--bg-tertiary);
  border-radius: 10px;
  text-align: center;
}

.config-placeholder {
  color: var(--text-secondary);
  font-size: var(--font-size-body);
}

.init-random-notice {
  padding: 40px 20px;
  text-align: center;
  color: var(--text-secondary);
}

.init-random-notice i {
  font-size: 2rem;
  margin-bottom: 12px;
  color: var(--accent);
}

.init-random-notice p {
  font-size: var(--font-size-body);
}

/* 规划卡配置 */
.planning-cards-config {
  padding: 4px 20px 20px;
}

.planning-cards-hint {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.85rem;
  color: var(--text-secondary);
  margin-bottom: 24px;
}

.planning-cards-hint i {
  color: var(--text-secondary);
  font-size: 0.9rem;
}

.planning-cards-grid {
  display: flex;
  flex-direction: column;
  gap: 24px;
  align-items: center;
}

.planning-cards-row {
  display: flex;
  gap: 24px;
  justify-content: center;
}

.planning-card {
  position: relative;
  width: 118px;
  height: 187px;
  border-radius: 12px;
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  border: 3.5px solid transparent;
  background: var(--bg-tertiary);
  box-sizing: border-box;
}

.planning-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  border-radius: 9px;
  box-shadow:
    inset 0 0 20px rgba(0, 0, 0, 0.25),
    inset 0 0 8px rgba(0, 0, 0, 0.15);
  pointer-events: none;
  z-index: 1;
}

.planning-card.active::before {
  display: none;
}

.planning-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
}

.planning-card.active {
  border: 3.5px solid var(--accent);
  box-shadow: 0 8px 24px rgba(0, 123, 255, 0.15);
}

.planning-card-image {
  width: 100%;
  height: 100%;
  background-repeat: no-repeat;
  background-size: cover;
  background-position: center;
  border-radius: 0;
}

.planning-card-check {
  position: absolute;
  top: 0;
  right: 0;
  width: 34px;
  height: 34px;
  background: var(--accent);
  border-radius: 0 0 0 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 0.9rem;
  z-index: 2;
}

.planning-card-name {
  position: absolute;
  bottom: 6px;
  left: 50%;
  transform: translateX(-50%);
  padding: 3px 8px;
  background: rgba(0, 0, 0, 0.6);
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
  color: white;
  white-space: nowrap;
  z-index: 2;
}

/* 派系配置 */
.factions-config {
  padding: 4px 20px 20px;
}

.factions-hint {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.85rem;
  color: var(--text-secondary);
  margin-bottom: 20px;
}

.factions-hint i {
  color: var(--text-secondary);
  font-size: 0.9rem;
}

.factions-grid {
  display: flex;
  flex-direction: column;
  gap: 16px;
  align-items: center;
}

.factions-row {
  display: flex;
  gap: 20px;
  justify-content: center;
}

.faction-card {
  position: relative;
  width: 158px;
  height: 90px;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  border: 3px solid transparent;
  background: var(--bg-tertiary);
  box-sizing: border-box;
}

.faction-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  border-radius: 5px;
  box-shadow:
    inset 0 0 12px rgba(0, 0, 0, 0.3),
    inset 0 0 4px rgba(0, 0, 0, 0.2);
  pointer-events: none;
  z-index: 1;
}

.faction-card.active::before {
  display: none;
}

.faction-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.25);
}

.faction-card.active {
  border: 3px solid var(--accent);
  box-shadow: 0 6px 20px rgba(0, 123, 255, 0.2);
}

.faction-card-image {
  width: 100%;
  height: 100%;
  background-repeat: no-repeat;
  border-radius: 0;
}

.faction-card-name {
  position: absolute;
  bottom: 6px;
  left: 50%;
  transform: translateX(-50%);
  padding: 3px 8px;
  background: rgba(0, 0, 0, 0.75);
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
  color: white;
  white-space: nowrap;
  z-index: 2;
}

.faction-card-check {
  position: absolute;
  top: 0;
  right: 0;
  width: 26px;
  height: 26px;
  background: var(--accent);
  border-radius: 0 0 0 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 0.8rem;
  z-index: 3;
}

/* 宫殿板块配置 */
.palace-config {
  padding: 4px 20px 20px;
}

.palace-hint {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.85rem;
  color: var(--text-secondary);
  margin-bottom: 20px;
}

.palace-hint i {
  color: var(--text-secondary);
  font-size: 0.9rem;
}

.palace-grid {
  display: flex;
  flex-direction: column;
  gap: 16px;
  align-items: center;
}

.palace-row {
  display: flex;
  gap: 10px;
  justify-content: center;
}

.palace-card {
  position: relative;
  width: 142px;
  height: 74px;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  border: 3px solid transparent;
  background: var(--bg-tertiary);
  box-sizing: border-box;
}

.palace-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  border-radius: 5px;
  box-shadow:
    inset 0 0 12px rgba(0, 0, 0, 0.3),
    inset 0 0 4px rgba(0, 0, 0, 0.2);
  pointer-events: none;
  z-index: 1;
}

.palace-card.active::before {
  display: none;
}

.palace-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.25);
}

.palace-card.active {
  border: 3px solid var(--accent);
  box-shadow: 0 6px 20px rgba(0, 123, 255, 0.2);
}

.palace-card-image {
  width: 100%;
  height: 100%;
  background-repeat: no-repeat;
  background-size: cover;
  background-position: center;
  border-radius: 0;
}

.palace-card-check {
  position: absolute;
  top: 0;
  right: 0;
  width: 26px;
  height: 26px;
  background: var(--accent);
  border-radius: 0 0 0 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 0.8rem;
  z-index: 3;
}

/* 响应式 */
@media (max-width: 1024px) {
  .setup-header {
    padding: 16px 24px;
  }

  .setup-main {
    padding: 0 24px 24px;
    gap: 16px;
  }
}

@media (max-width: 768px) {
  .setup-main {
    grid-template-columns: 1fr;
  }

  .mode-selector {
    grid-template-columns: 1fr;
  }

  .mode-card {
    padding: 20px 16px;
  }

  .mode-icon {
    width: 56px;
    height: 56px;
    font-size: 1.6rem;
  }

  .mode-name {
    font-size: 1.1rem;
  }

  .init-modal-layout {
    grid-template-columns: 1fr;
    min-height: 300px;
  }

  .init-nav {
    flex-direction: row;
    flex-wrap: wrap;
    border-right: none;
    border-bottom: 1px solid var(--border);
    padding: 12px;
    gap: 8px;
  }

  .init-nav-item {
    flex: 1;
    min-width: 140px;
  }

  .nav-item-left {
    padding: 10px 12px;
  }

  .nav-toggle {
    padding: 10px 12px 10px 6px;
  }
}
</style>
