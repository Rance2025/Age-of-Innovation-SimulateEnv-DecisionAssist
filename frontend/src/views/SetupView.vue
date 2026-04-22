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
              <div class="mode-desc">
                <div class="mode-desc-line1">{{ mode.desc.split('\n')[0] }}</div>
                <div class="mode-desc-line2">{{ mode.desc.split('\n')[1] || '' }}</div>
              </div>
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

    <div v-if="isLoading" class="loading-overlay">
      <div class="loading-content" :class="{ 'loading-content-countdown': isCountdownPhase }">
        <template v-if="!isCountdownPhase">
          <div class="loading-spinner">
            <i class="fas fa-circle-notch fa-spin"></i>
          </div>
          <div class="loading-text">{{ loadingText }}</div>
          <div class="loading-subtext">请稍候，正在等待后端返回游戏状态...</div>
        </template>
      </div>
    </div>

    <!-- 自定义游戏模式配置弹窗 -->
    <div v-if="isLoading && isCountdownPhase" class="countdown-overlay">
      <div class="loading-content loading-content-countdown">
        <div class="countdown-badge">
          <span :key="loadingCountdown" class="countdown-digit">{{ loadingCountdown }}</span>
        </div>
        <div class="loading-text">{{ loadingText }}</div>
        <div class="loading-subtext loading-subtext-emphasis">游戏即将开始</div>
        <div class="countdown-progress">
          <span class="countdown-progress-bar"></span>
        </div>
      </div>
    </div>

    <Modal v-model="showCustomModeModal" title="自定义游戏配置">
      <div class="custom-mode-options">
        <div class="custom-option">
          <div class="custom-option-label">基础时间</div>
          <div class="custom-option-desc">每位玩家的主要思考时间</div>
          <div class="slider-container">
            <div class="slider-track-wrapper" ref="mainTimeTrackRef">
              <input
                v-model.number="customSettings.mainTime"
                type="range"
                min="0"
                max="100"
                class="slider"
              />
              <div class="slider-marks">
                <div class="slider-marks-inner">
                  <span class="slider-mark" :style="getMainTimeMarkStyle(0)">0</span>
                  <span class="slider-mark" :style="getMainTimeMarkStyle(30)">30</span>
                  <span class="slider-mark" :style="getMainTimeMarkStyle(45)">45</span>
                  <span class="slider-mark" :style="getMainTimeMarkStyle(60)">60</span>
                  <span class="slider-mark" :style="getMainTimeMarkStyle(75)">75</span>
                  <span class="slider-mark" :style="getMainTimeMarkStyle(100)">100</span>
                </div>
              </div>
            </div>
            <span class="slider-value">{{ customSettings.mainTime }} 分钟</span>
          </div>
        </div>
        <div class="custom-option">
          <div class="custom-option-label">读秒时间</div>
          <div class="custom-option-desc">基础时间耗尽后每回合的限时</div>
          <div class="slider-container">
            <div class="slider-track-wrapper" ref="byoYomiTrackRef">
              <input
                v-model.number="customSettings.byoYomiTime"
                type="range"
                min="10"
                max="90"
                class="slider"
              />
              <div class="slider-marks">
                <div class="slider-marks-inner">
                  <span class="slider-mark" :style="getByoYomiMarkStyle(10)">10</span>
                  <span class="slider-mark" :style="getByoYomiMarkStyle(30)">30</span>
                  <span class="slider-mark" :style="getByoYomiMarkStyle(45)">45</span>
                  <span class="slider-mark" :style="getByoYomiMarkStyle(60)">60</span>
                  <span class="slider-mark" :style="getByoYomiMarkStyle(75)">75</span>
                  <span class="slider-mark" :style="getByoYomiMarkStyle(90)">90</span>
                </div>
              </div>
            </div>
            <span class="slider-value">{{ customSettings.byoYomiTime }} 秒</span>
          </div>
        </div>
        <div class="custom-option">
          <div class="custom-option-label">超时策略</div>
          <div class="custom-option-desc">读秒超时后自动执行的策略</div>
          <div class="custom-option-input custom-option-input-single">
            <button
              type="button"
              class="custom-option-btn custom-option-btn-full"
              :class="{ active: customSettings.timeoutStrategy === 'random_pure' }"
              @click="customSettings.timeoutStrategy = 'random_pure'"
            >
              完全随机
            </button>
            <button
              type="button"
              class="custom-option-btn custom-option-btn-full"
              :class="{ active: customSettings.timeoutStrategy === 'random_fast_action' }"
              @click="customSettings.timeoutStrategy = 'random_fast_action'"
            >
              经快速行动优化的随机策略
            </button>
          </div>
        </div>
      </div>
      <template #footer>
        <button type="button" class="btn btn-primary" @click="showCustomModeModal = false">
          确认
        </button>
      </template>
    </Modal>

    <!-- AI策略弹窗 -->
    <StrategyPickerModal
      v-model="showStrategyModalOpen"
      :title="`AI策略 - 玩家 ${(showStrategyModal ?? 0) + 1}`"
      :selected-strategy="showStrategyModal !== null ? form.players[showStrategyModal].strategy : ''"
      @select="selectStrategy"
    />

    <!-- 初始板块弹窗 -->
    <Modal v-model="showInitModal" title="初始板块配置" class="init-modal">
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
                class="fas fa-check nav-complete-icon"
                :class="{ 'is-hidden': !(initNavRandom[item.id] || (!initNavRandom[item.id] && isNavItemComplete(item.id))) }"
                aria-hidden="true"
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
                <span>请选择 {{ requiredFactionCount }} 个派系参与本局游戏（已选 {{ selectedFactions.length }} / {{ requiredFactionCount }} 个）</span>
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
                <span>请选择 {{ requiredPalaceCount }} 个宫殿板块参与本局游戏（已选 {{ selectedPalaces.length }} / {{ requiredPalaceCount }} 个）</span>
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
                    <div class="palace-card-label">{{ getPalaceBackendCode(index) }}</div>
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
                    <div class="palace-card-label">{{ getPalaceBackendCode(index) }}</div>
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
                    <div class="palace-card-label">{{ getPalaceBackendCode(index) }}</div>
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
                    <div class="palace-card-label">{{ getPalaceBackendCode(index) }}</div>
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

          <!-- 回合助推板配置 -->
          <div v-else-if="activeInitNav === 'roundBoosters'">
            <div v-if="!initNavRandom.roundBoosters" class="round-boosters-config">
              <p class="round-boosters-hint">
                <i class="fas fa-info-circle"></i>
                <span>请选择 {{ requiredRoundBoosterCount }} 个回合助推板参与本局游戏（已选 {{ selectedRoundBoosters.length }} / {{ requiredRoundBoosterCount }} 个）</span>
              </p>
              <div class="round-boosters-grid">
                <!-- 第一行：5个 -->
                <div class="round-boosters-row row-5">
                  <div
                    v-for="index in [0, 1, 2, 3, 4]"
                    :key="index"
                    class="round-booster-card"
                    :class="{ active: selectedRoundBoosters.includes(index) }"
                    @click="toggleRoundBoosterSelection(index)"
                  >
                    <div class="round-booster-card-image" :style="getRoundBoosterCardStyle(index)"></div>
                    <div class="round-booster-card-label">{{ getRoundBoosterBackendCode(index) }}</div>
                    <div v-if="selectedRoundBoosters.includes(index)" class="round-booster-card-check">
                      <i class="fas fa-check"></i>
                    </div>
                  </div>
                </div>
                <!-- 第二行：5个 -->
                <div class="round-boosters-row row-5">
                  <div
                    v-for="index in [5, 6, 7, 8, 9]"
                    :key="index"
                    class="round-booster-card"
                    :class="{ active: selectedRoundBoosters.includes(index) }"
                    @click="toggleRoundBoosterSelection(index)"
                  >
                    <div class="round-booster-card-image" :style="getRoundBoosterCardStyle(index)"></div>
                    <div class="round-booster-card-label">{{ getRoundBoosterBackendCode(index) }}</div>
                    <div v-if="selectedRoundBoosters.includes(index)" class="round-booster-card-check">
                      <i class="fas fa-check"></i>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div v-else class="init-random-notice">
              <i class="fas fa-shuffle"></i>
              <p>已启用随机设置，回合助推板将随机分配</p>
            </div>
          </div>

          <!-- 轮次计分板块配置 -->
          <div v-else-if="activeInitNav === 'roundScoring'">
            <div v-if="!initNavRandom.roundScoring" class="round-scoring-config">
              <p class="round-scoring-hint">
                <i class="fas fa-info-circle"></i>
                <span>请依次选择第 1 至 6 轮的回合计分板块（已选定前 {{ selectedRoundScoring.length }} 轮）</span>
              </p>
              <!-- 判定条件提示 -->
              <div class="round-scoring-rules">
                <div class="rule-item" :class="{ satisfied: isRule1Satisfied(), violated: isRule1Violated() }">
                  <i class="fas" :class="getRule1Icon()"></i>
                  <span>同一学科的 3 个计分板不能同时出现在前 5 轮</span>
                </div>
                <div class="rule-item" :class="{ satisfied: isRule2Satisfied(), violated: isRule2Violated() }">
                  <i class="fas" :class="getRule2Icon()"></i>
                  <span>8 号轮次计分板不能出现在后 2 轮</span>
                </div>
              </div>
              <div class="round-scoring-grid">
                <!-- 第一行：3个 -->
                <div class="round-scoring-row row-3">
                  <div
                    v-for="index in [0, 1, 2]"
                    :key="index"
                    class="round-scoring-card"
                    :class="{ active: selectedRoundScoring.includes(index) }"
                    @click="toggleRoundScoringSelection(index)"
                  >
                    <div class="round-scoring-card-image" :style="getRoundScoringCardStyle(index)"></div>
                    <div class="round-scoring-card-label">{{ getRoundScoringBackendCode(index) }}</div>
                    <div v-if="getRoundScoringOrder(index) > 0" class="round-scoring-card-order">
                      {{ getRoundScoringOrder(index) }}
                    </div>
                  </div>
                </div>
                <!-- 第二行：3个 -->
                <div class="round-scoring-row row-3">
                  <div
                    v-for="index in [3, 4, 5]"
                    :key="index"
                    class="round-scoring-card"
                    :class="{ active: selectedRoundScoring.includes(index) }"
                    @click="toggleRoundScoringSelection(index)"
                  >
                    <div class="round-scoring-card-image" :style="getRoundScoringCardStyle(index)"></div>
                    <div class="round-scoring-card-label">{{ getRoundScoringBackendCode(index) }}</div>
                    <div v-if="getRoundScoringOrder(index) > 0" class="round-scoring-card-order">
                      {{ getRoundScoringOrder(index) }}
                    </div>
                  </div>
                </div>
                <!-- 第三行：3个 -->
                <div class="round-scoring-row row-3">
                  <div
                    v-for="index in [6, 7, 8]"
                    :key="index"
                    class="round-scoring-card"
                    :class="{ active: selectedRoundScoring.includes(index) }"
                    @click="toggleRoundScoringSelection(index)"
                  >
                    <div class="round-scoring-card-image" :style="getRoundScoringCardStyle(index)"></div>
                    <div class="round-scoring-card-label">{{ getRoundScoringBackendCode(index) }}</div>
                    <div v-if="getRoundScoringOrder(index) > 0" class="round-scoring-card-order">
                      {{ getRoundScoringOrder(index) }}
                    </div>
                  </div>
                </div>
                <!-- 第四行：3个 -->
                <div class="round-scoring-row row-3">
                  <div
                    v-for="index in [9, 10, 11]"
                    :key="index"
                    class="round-scoring-card"
                    :class="{ active: selectedRoundScoring.includes(index) }"
                    @click="toggleRoundScoringSelection(index)"
                  >
                    <div class="round-scoring-card-image" :style="getRoundScoringCardStyle(index)"></div>
                    <div class="round-scoring-card-label">{{ getRoundScoringBackendCode(index) }}</div>
                    <div v-if="getRoundScoringOrder(index) > 0" class="round-scoring-card-order">
                      {{ getRoundScoringOrder(index) }}
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div v-else class="init-random-notice">
              <i class="fas fa-shuffle"></i>
              <p>已启用随机设置，轮次计分板块将随机分配</p>
            </div>
          </div>

          <!-- 最终计分板块配置 -->
          <div v-else-if="activeInitNav === 'finalScoring'">
            <div v-if="!initNavRandom.finalScoring" class="final-scoring-config">
              <p class="final-scoring-hint">
                <i class="fas fa-info-circle"></i>
                <span>请选择 1 个最终计分板块</span>
              </p>
              <div class="final-scoring-grid">
                <!-- 一行4个 -->
                <div class="final-scoring-row row-4">
                  <div
                    v-for="index in [0, 1, 2, 3]"
                    :key="index"
                    class="final-scoring-card"
                    :class="{ active: selectedFinalScoring === index }"
                    @click="toggleFinalScoringSelection(index)"
                  >
                    <div class="final-scoring-card-image" :style="getFinalScoringCardStyle(index)"></div>
                    <div class="final-scoring-card-label">{{ getFinalScoringBackendCode(index) }}</div>
                    <div v-if="selectedFinalScoring === index" class="final-scoring-card-check">
                      <i class="fas fa-check"></i>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div v-else class="init-random-notice">
              <i class="fas fa-shuffle"></i>
              <p>已启用随机设置，最终计分板块将随机分配</p>
            </div>
          </div>

          <!-- 能力板块配置 -->
          <div v-else-if="activeInitNav === 'abilities'">
            <div v-if="!initNavRandom.abilities" class="abilities-config">
              <p class="abilities-hint">
                <i class="fas fa-info-circle"></i>
                <span>请从 12 个能力板块中选择 12 个摆放进上方区域（已摆放 {{ abilityOrder.filter(a => a !== null).length }} / 12 个）</span>
              </p>
              <!-- 上方：摆放区域（board图片背景 + 3行4列位置） -->
              <div class="abilities-board-container">
                <div class="abilities-board" :style="{ backgroundImage: 'url(/assets/images/ability_tiles_board.jpg)' }">
                  <div class="abilities-board-grid">
                    <div
                      v-for="positionIndex in 12"
                      :key="positionIndex - 1"
                      class="ability-board-slot"
                      :class="{ 'is-occupied': abilityOrder[positionIndex - 1] !== null, 'is-selected': selectedAbilitySlot === positionIndex - 1 }"
                      @dragover="handleAbilityDragOver($event, positionIndex - 1)"
                      @drop="handleAbilityDrop($event, positionIndex - 1)"
                      @click="handleAbilitySlotClick(positionIndex - 1)"
                    >
                      <div v-if="abilityOrder[positionIndex - 1] !== null" class="ability-placed-card">
                        <div
                          class="ability-card-image"
                          :style="getAbilityCardStyle(abilityOrder[positionIndex - 1])"
                          draggable="true"
                          @dragstart="handleAbilityDragStart($event, abilityOrder[positionIndex - 1], positionIndex - 1)"
                          @dragend="handleAbilityDragEnd"
                          @click="removeAbilityFromPosition(positionIndex - 1)"
                        ></div>
                      </div>
                      <span v-else class="ability-slot-number">{{ positionIndex }}</span>
                    </div>
                  </div>
                </div>
              </div>
              <!-- 下方：12个能力板块选择区（2行6列） -->
              <div class="abilities-selection">
                <div class="abilities-row">
                  <div
                    v-for="index in [0, 1, 2, 3, 4, 5]"
                    :key="index"
                    class="ability-card"
                    :class="{ 'is-placed': abilityOrder.includes(index), 'is-selected': selectedAbilityCard === index }"
                    draggable="true"
                    @dragstart="handleAbilityDragStart($event, index)"
                    @dragend="handleAbilityDragEnd"
                    @click="handleAbilityCardClick(index)"
                  >
                    <div class="ability-card-image" :style="getAbilityCardStyle(index)"></div>
                    <div class="ability-card-label">{{ getAbilityBackendCode(index) }}</div>
                  </div>
                </div>
                <div class="abilities-row">
                  <div
                    v-for="index in [6, 7, 8, 9, 10, 11]"
                    :key="index"
                    class="ability-card"
                    :class="{ 'is-placed': abilityOrder.includes(index), 'is-selected': selectedAbilityCard === index }"
                    draggable="true"
                    @dragstart="handleAbilityDragStart($event, index)"
                    @dragend="handleAbilityDragEnd"
                    @click="handleAbilityCardClick(index)"
                  >
                    <div class="ability-card-image" :style="getAbilityCardStyle(index)"></div>
                    <div class="ability-card-label">{{ getAbilityBackendCode(index) }}</div>
                  </div>
                </div>
              </div>
            </div>
            <div v-else class="init-random-notice">
              <i class="fas fa-shuffle"></i>
              <p>已启用随机设置，能力板块将随机分配</p>
            </div>
          </div>

          <!-- 书行动配置 -->
          <div v-else-if="activeInitNav === 'bookActions'">
            <div v-if="!initNavRandom.bookActions" class="book-actions-config">
              <p class="book-actions-hint">
                <i class="fas fa-info-circle"></i>
                <span>请选择 3 个书行动参与本局游戏（已选 {{ selectedBookActions.length }} / 3 个）</span>
              </p>
              <div class="book-actions-grid">
                <!-- 第一行：2个 -->
                <div class="book-actions-row row-2">
                  <div
                    v-for="index in [0, 1]"
                    :key="index"
                    class="book-action-card"
                    :class="{ active: selectedBookActions.includes(index) }"
                    @click="toggleBookActionSelection(index)"
                  >
                    <div class="book-action-card-image" :style="getBookActionCardStyle(index)"></div>
                    <div class="book-action-card-label">{{ getBookActionBackendCode(index) }}</div>
                    <div v-if="selectedBookActions.includes(index)" class="book-action-card-check">
                      <i class="fas fa-check"></i>
                    </div>
                  </div>
                </div>
                <!-- 第二行：2个 -->
                <div class="book-actions-row row-2">
                  <div
                    v-for="index in [2, 3]"
                    :key="index"
                    class="book-action-card"
                    :class="{ active: selectedBookActions.includes(index) }"
                    @click="toggleBookActionSelection(index)"
                  >
                    <div class="book-action-card-image" :style="getBookActionCardStyle(index)"></div>
                    <div class="book-action-card-label">{{ getBookActionBackendCode(index) }}</div>
                    <div v-if="selectedBookActions.includes(index)" class="book-action-card-check">
                      <i class="fas fa-check"></i>
                    </div>
                  </div>
                </div>
                <!-- 第三行：2个 -->
                <div class="book-actions-row row-2">
                  <div
                    v-for="index in [4, 5]"
                    :key="index"
                    class="book-action-card"
                    :class="{ active: selectedBookActions.includes(index) }"
                    @click="toggleBookActionSelection(index)"
                  >
                    <div class="book-action-card-image" :style="getBookActionCardStyle(index)"></div>
                    <div class="book-action-card-label">{{ getBookActionBackendCode(index) }}</div>
                    <div v-if="selectedBookActions.includes(index)" class="book-action-card-check">
                      <i class="fas fa-check"></i>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div v-else class="init-random-notice">
              <i class="fas fa-shuffle"></i>
              <p>已启用随机设置，书行动将随机分配</p>
            </div>
          </div>

          <!-- 高科板块配置 -->
          <div v-else-if="activeInitNav === 'techs'">
            <div v-if="!initNavRandom.techs" class="techs-config">
              <p class="techs-hint">
                <i class="fas fa-info-circle"></i>
                <span>请从 18 个高科板块中选择 {{ requiredTechCount }} 个摆放进上方区域（已摆放 {{ techOrder.filter(t => t !== null).length }} / {{ requiredTechCount }} 个）</span>
              </p>
              <!-- 上方：摆放区域（2+2n个格子） -->
              <div class="techs-board-container">
                <div class="techs-board" :class="'techs-board-' + form.playerCount" :style="{ backgroundImage: 'url(/assets/images/science_board_' + form.playerCount + '.png)' }">
                  <div class="techs-board-grid">
                    <div
                      v-for="positionIndex in requiredTechCount"
                      :key="positionIndex - 1"
                      class="tech-board-slot"
                      :class="{ 'is-occupied': techOrder[positionIndex - 1] !== null, 'is-selected': selectedTechSlot === positionIndex - 1 }"
                      @dragover="handleTechDragOver($event, positionIndex - 1)"
                      @drop="handleTechDrop($event, positionIndex - 1)"
                      @click="handleTechSlotClick(positionIndex - 1)"
                    >
                      <div v-if="techOrder[positionIndex - 1] !== null" class="tech-placed-card">
                        <div
                          class="tech-card-image"
                          :style="getTechCardStyle(techOrder[positionIndex - 1])"
                          draggable="true"
                          @dragstart="handleTechDragStart($event, techOrder[positionIndex - 1], positionIndex - 1)"
                          @dragend="handleTechDragEnd"
                          @click="removeTechFromPosition(positionIndex - 1)"
                        ></div>
                      </div>
                      <span v-else class="tech-slot-number">{{ positionIndex }}</span>
                    </div>
                  </div>
                </div>
              </div>
              <!-- 下方：18个高科板块选择区（3行6列） -->
              <div class="techs-selection">
                <div class="techs-row">
                  <div
                    v-for="index in [0, 1, 2, 3, 4, 5]"
                    :key="index"
                    class="tech-card"
                    :class="{ 'is-placed': techOrder.includes(index), 'is-selected': selectedTechCard === index }"
                    draggable="true"
                    @dragstart="handleTechDragStart($event, index)"
                    @dragend="handleTechDragEnd"
                    @click="handleTechCardClick(index)"
                  >
                    <div class="tech-card-image" :style="getTechCardStyle(index)"></div>
                    <div class="tech-card-label">{{ getTechBackendCode(index) }}</div>
                  </div>
                </div>
                <div class="techs-row">
                  <div
                    v-for="index in [6, 7, 8, 9, 10, 11]"
                    :key="index"
                    class="tech-card"
                    :class="{ 'is-placed': techOrder.includes(index), 'is-selected': selectedTechCard === index }"
                    draggable="true"
                    @dragstart="handleTechDragStart($event, index)"
                    @dragend="handleTechDragEnd"
                    @click="handleTechCardClick(index)"
                  >
                    <div class="tech-card-image" :style="getTechCardStyle(index)"></div>
                    <div class="tech-card-label">{{ getTechBackendCode(index) }}</div>
                  </div>
                </div>
                <div class="techs-row">
                  <div
                    v-for="index in [12, 13, 14, 15, 16, 17]"
                    :key="index"
                    class="tech-card"
                    :class="{ 'is-placed': techOrder.includes(index), 'is-selected': selectedTechCard === index }"
                    draggable="true"
                    @dragstart="handleTechDragStart($event, index)"
                    @dragend="handleTechDragEnd"
                    @click="handleTechCardClick(index)"
                  >
                    <div class="tech-card-image" :style="getTechCardStyle(index)"></div>
                    <div class="tech-card-label">{{ getTechBackendCode(index) }}</div>
                  </div>
                </div>
              </div>
            </div>
            <div v-else class="init-random-notice">
              <i class="fas fa-shuffle"></i>
              <p>已启用随机设置，高科板块将随机分配</p>
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

<style scoped>
/* 页面样式 */
.setup-page {
  width: 100%;
}
</style>

<script setup>
import { reactive, ref, watch, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useGameStore } from '../stores/game'
import Modal from '../components/Modal.vue'
import StrategyPickerModal from '../components/StrategyPickerModal.vue'
import { STRATEGY_OPTIONS } from '../constants/strategies.js'
import {
  getFinalScoringSelectionSpriteStyleByBackendId,
  getRoundBoosterFrontSpriteStyleByBackendId,
  getRoundScoringSpriteStyleByBackendId,
  getAbilityTileStyleByBackendId,
  getScienceTileStyleByBackendId
} from '../utils/tileSprites'

defineOptions({
  name: 'SetupView'
})

const router = useRouter()
const gameStore = useGameStore()

const gameModes = [
  { value: 'standard', name: '标准模式', desc: '45min 基础时间 + 45s 读秒\n超时采用经快速行动优化的随机策略', icon: 'fas fa-chess' },
  { value: 'quick', name: '快速模式', desc: '25min 基础时间 + 25s 读秒\n超时采用经快速行动优化的随机策略', icon: 'fas fa-bolt' },
  { value: 'custom', name: '自定义', desc: '自由配置各项参数', icon: 'fas fa-cogs' }
]

const initNavItems = [
  { id: 'planningCards', name: '规划卡', icon: 'fas fa-address-card' },
  { id: 'factions', name: '派系', icon: 'fas fa-users' },
  { id: 'palace', name: '宫殿板块', icon: 'fas fa-building' },
  { id: 'roundBoosters', name: '回合助推板', icon: 'fas fa-rocket' },
  { id: 'roundScoring', name: '轮次计分', icon: 'fas fa-calendar' },
  { id: 'finalScoring', name: '最终计分', icon: 'fas fa-trophy' },
  { id: 'abilities', name: '能力板块', icon: 'fas fa-magic' },
  { id: 'techs', name: '高科板块', icon: 'fas fa-microchip' },
  { id: 'bookActions', name: '书行动', icon: 'fas fa-book' }
]

const showInitModal = ref(false)
const showStrategyModal = ref(null)
const showCustomModeModal = ref(false)
const isLoading = ref(false)
const loadingStage = ref('loading')
const loadingCountdown = ref(3)
const isCountdownPhase = computed(() => loadingStage.value === 'countdown')
let loadingCountdownTimer = null
const loadingText = ref('正在启动游戏...')

const mainTimeTrackRef = ref(null)
const byoYomiTrackRef = ref(null)

const THUMB_RADIUS = 9
const TRACK_HEIGHT = 20

function getSliderMarkPositions(trackEl) {
  if (!trackEl) return { leftPercent: 0, rightPercent: 100 }
  const trackWidth = trackEl.offsetWidth
  const leftPos = THUMB_RADIUS
  const rightPos = trackWidth - THUMB_RADIUS
  return {
    leftPercent: (leftPos / trackWidth) * 100,
    rightPercent: (rightPos / trackWidth) * 100
  }
}

function getMainTimeMarkStyle(value) {
  const trackWidth = mainTimeTrackRef.value?.offsetWidth || 1
  const leftPx = THUMB_RADIUS + (value / 100) * (trackWidth - 2 * THUMB_RADIUS)
  return { left: leftPx + 'px' }
}

function getByoYomiMarkStyle(value) {
  const trackWidth = byoYomiTrackRef.value?.offsetWidth || 1
  const min = 10, max = 90
  const leftPx = THUMB_RADIUS + ((value - min) / (max - min)) * (trackWidth - 2 * THUMB_RADIUS)
  return { left: leftPx + 'px' }
}

// 策略弹窗的显示状态（转换为布尔值）
const showStrategyModalOpen = computed({
  get: () => showStrategyModal.value !== null,
  set: (val) => { if (!val) showStrategyModal.value = null }
})

// 选择策略
function selectStrategy(strategyId) {
  if (showStrategyModal.value !== null) {
    form.players[showStrategyModal.value].strategy = strategyId
  }
}

function clearLoadingCountdownTimer() {
  if (loadingCountdownTimer !== null) {
    clearInterval(loadingCountdownTimer)
    loadingCountdownTimer = null
  }
}

function runStartCountdown(seconds = 3) {
  clearLoadingCountdownTimer()
  loadingCountdown.value = seconds

  return new Promise((resolve) => {
    loadingCountdownTimer = setInterval(() => {
      if (loadingCountdown.value <= 0) {
        clearLoadingCountdownTimer()
        resolve()
        return
      }

      loadingCountdown.value -= 1

      if (loadingCountdown.value <= 0) {
        clearLoadingCountdownTimer()
        resolve()
      }
    }, 1000)
  })
}

onUnmounted(() => {
  clearLoadingCountdownTimer()
})

const activeInitNav = ref('planningCards')

// 恢复设置标志，用于阻止 watch 干扰
let isRestoringSettings = false

// 左侧导航栏各项目的随机开关状态（默认关闭，即非随机）
const initNavRandom = reactive({
  planningCards: false,
  factions: false,
  palace: false,
  roundBoosters: false,
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

// 选中的轮次计分板块索引数组（有序选择，必须选6个，只取前12张）
const selectedRoundScoring = ref([])

// 轮次计分板块选择是否完成（必须刚好6个）
const isRoundScoringComplete = computed(() => selectedRoundScoring.value.length === 6)

// 选中的最终计分板块索引（单选，取第13-16个即索引12-15）
const selectedFinalScoring = ref(null)

// 最终计分板块选择是否完成
const isFinalScoringComplete = computed(() => selectedFinalScoring.value !== null)

// 能力板块拖拽排序状态（12个位置，null表示空位，数字0-11表示能力板块索引）
const abilityOrder = ref(Array(12).fill(null))

// 能力板块选择是否完成（12个全部摆放）
const isAbilitiesComplete = computed(() => abilityOrder.value.every(pos => pos !== null))

// 高科板块数量（2 + 2 * 玩家数）
const requiredTechCount = computed(() => 2 + 2 * form.playerCount)

// 高科板块拖拽排序状态（动态数量个位置，null表示空位，数字0-17表示高科板块索引）
const techOrder = ref(Array(8).fill(null)) // 默认8个位置（3人局）

// 高科板块选择是否完成（所有位置都填满）
const isTechsComplete = computed(() => techOrder.value.every(pos => pos !== null))

// 选中的书行动索引数组（多选，必须选3个）
const selectedBookActions = ref([])

// 书行动选择是否完成（必须刚好3个）
const isBookActionsComplete = computed(() => selectedBookActions.value.length === 3)

// 选中的回合助推板索引数组（多选，数量 = 玩家数 + 3）
const selectedRoundBoosters = ref([])

// 获取需要选择的回合助推板数量（玩家数量 + 3）
const requiredRoundBoosterCount = computed(() => form.playerCount + 3)

// 回合助推板选择是否完成
const isRoundBoostersComplete = computed(() => selectedRoundBoosters.value.length === requiredRoundBoosterCount.value)

// 派系选择是否完成
const isFactionsComplete = computed(() => selectedFactions.value.length === requiredFactionCount.value)

// 派系名称列表（12个）- 按后端编码 1-12 顺序
// 后端: 1神佑者, 2猫人, 3哥布林, 4幻术师, 5发明家, 6蜥蜴人, 7鼹鼠, 8僧侣, 9航海家, 10奥马尔, 11哲学家, 12通灵师
const factionNames = [
  '神佑者', '猫人', '哥布林',
  '幻术师', '发明家', '蜥蜴人',
  '鼹鼠', '僧侣', '航海家',
  '奥马尔', '哲学家', '通灵师'
]

// 后端编码到图片索引的映射（后端1-12 -> 图片0-11）
// 后端: 1神佑者, 2猫人, 3哥布林, 4幻术师, 5发明家, 6蜥蜴人, 7鼹鼠, 8僧侣, 9航海家, 10奥马尔, 11哲学家, 12通灵师
// 图片顺序: 0幻术师, 1航海家, 2哲学家, 3通灵师, 4猫人, 5鼹鼠, 6奥马尔, 7哥布林, 8发明家, 9蜥蜴人, 10僧侣, 11神佑者
const factionBackendToImageMap = [11, 4, 7, 0, 8, 9, 5, 10, 1, 6, 2, 3]

// 规划卡名称列表（7个）- 按后端编码 1-7 顺序：平原、沼泽、湖泊、森林、山脉、荒地、沙漠
const planningCardNames = ['平原', '沼泽', '湖泊', '森林', '山脉', '荒地', '沙漠']

// 后端编码到图片索引的映射（后端1-7 -> 图片0-6）
// 后端: 1平原, 2沼泽, 3湖泊, 4森林, 5山脉, 6荒地, 7沙漠
// 图片顺序: 0沙漠, 1森林, 2沼泽, 3荒地, 4湖泊, 5山脉, 6平原
const planningCardBackendToImageMap = [6, 2, 4, 1, 5, 3, 0]

// 获取规划卡背景样式（7等分切割）
function getPlanningCardStyle(index) {
  // 7张卡片横向排列，使用精确百分比定位
  // 每张卡片占 100/7 ≈ 14.2857%，中心点在 7.1429%, 21.4286%, 35.7143%...
  const positions = [0, 16.6667, 33.3333, 50, 66.6667, 83.3333, 100]
  // 将前端显示索引映射到正确的图片位置
  const imageIndex = planningCardBackendToImageMap[index]
  return {
    backgroundImage: 'url(/assets/images/planning_cards.jpg)',
    backgroundSize: '700% 100%',
    backgroundPositionX: `${positions[imageIndex]}%`
  }
}

// 获取派系卡片背景样式（12等分切割）
function getFactionCardStyle(index) {
  // 12张卡片横向排列，使用精确百分比定位
  // 位置点：0%, 9.091%, 18.182%, 27.273%, 36.364%, 45.455%, 54.545%, 63.636%, 72.727%, 81.818%, 90.909%, 100%
  const positions = [0, 9.0909, 18.1818, 27.2727, 36.3636, 45.4545, 54.5455, 63.6364, 72.7273, 81.8182, 90.9091, 100]
  // 将前端显示索引映射到正确的图片位置
  const imageIndex = factionBackendToImageMap[index]
  return {
    backgroundImage: 'url(/assets/images/faction_tiles.jpg)',
    backgroundSize: '1200% 100%',
    backgroundPositionX: `${positions[imageIndex]}%`
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

// 宫殿板块后端编码到图片索引的映射（后端1-16 -> 图片0-15）
// 宫殿板块后端编码与图片顺序一致：1->0, 2->1, ..., 16->15
const palaceBackendToImageMap = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]

// 获取宫殿板块背景样式（18等分切割，只展示前16张）
function getPalaceCardStyle(index) {
  // 18张卡片横向排列，使用精确百分比定位
  // 位置点：0%, 5.882%, 11.765%, 17.647%, 23.529%, 29.412%, 35.294%, 41.176%,
  //        47.059%, 52.941%, 58.824%, 64.706%, 70.588%, 76.471%, 82.353%, 88.235%, 94.118%, 100%
  const positions = [0, 5.8824, 11.7647, 17.6471, 23.5294, 29.4118, 35.2941, 41.1765,
                     47.0588, 52.9412, 58.8235, 64.7059, 70.5882, 76.4706, 82.3529, 88.2353, 94.1176, 100]
  // 将前端显示索引映射到正确的图片位置
  const imageIndex = palaceBackendToImageMap[index]
  return {
    backgroundImage: 'url(/assets/images/palace_tiles.jpg)',
    backgroundSize: '1800% 100%',
    backgroundPositionX: `${positions[imageIndex]}%`
  }
}

// 获取宫殿板块后端编码（前端索引0-15对应后端编码1-16）
function getPalaceBackendCode(index) {
  return index + 1
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

function getRoundScoringCardStyle(index) {
  return getRoundScoringSpriteStyleByBackendId(index + 1)
}

// 获取轮次计分板块后端编码（前端索引0-11对应后端编码1-12）
function getRoundScoringBackendCode(index) {
  return index + 1
}

// 获取卡片的选择序号（1-6），未选中返回0
function getRoundScoringOrder(index) {
  const order = selectedRoundScoring.value.indexOf(index)
  return order > -1 ? order + 1 : 0
}

// 切换轮次计分板块选择状态（有序选择）
function toggleRoundScoringSelection(index) {
  const currentIndex = selectedRoundScoring.value.indexOf(index)
  if (currentIndex > -1) {
    // 已选中，取消选择并重新排序
    selectedRoundScoring.value.splice(currentIndex, 1)
  } else {
    // 未选中，检查是否已达到最大选择数量（6个）
    if (selectedRoundScoring.value.length >= 6) {
      return // 已达上限，点击无效
    }
    selectedRoundScoring.value.push(index)
  }
}

// 判定条件1：同一学科的三个计分板不能同时出现在前5轮
// 学科分组：[2,5,7], [1,3,12], [8,10,11], [4,6,9] 对应索引 [1,4,6], [0,2,11], [7,9,10], [3,5,8]

// 规则1是否确定达成（前5轮已选满且没有违规，或者已选数量>=3但不可能再凑齐一组）
function isRule1Satisfied() {
  const selected = selectedRoundScoring.value
  const firstFiveRounds = selected.slice(0, 5)
  const sameTrackGroups = [
    [1, 4, 6],   // [2,5,7]
    [0, 2, 11],  // [1,3,12]
    [7, 9, 10],  // [8,10,11]
    [3, 5, 8]    // [4,6,9]
  ]

  // 检查是否有任何一组已经凑齐（违规）
  for (const group of sameTrackGroups) {
    const allInFirstFive = group.every(tileIndex => firstFiveRounds.includes(tileIndex))
    if (allInFirstFive) return false // 违规了，不是达成
  }

  // 前5轮已选满6个且没有违规，确定达成
  if (selected.length >= 5) return true

  // 检查是否所有组都不可能再凑齐（每组至少有一个板块在前5轮之外）
  // 这种情况比较复杂，暂时只在选满5轮时判定
  return false
}

// 规则1是否确定违反
function isRule1Violated() {
  const selected = selectedRoundScoring.value
  if (selected.length < 3) return false

  const firstFiveRounds = selected.slice(0, 5)
  const sameTrackGroups = [
    [1, 4, 6],   // [2,5,7]
    [0, 2, 11],  // [1,3,12]
    [7, 9, 10],  // [8,10,11]
    [3, 5, 8]    // [4,6,9]
  ]

  for (const group of sameTrackGroups) {
    const allInFirstFive = group.every(tileIndex => firstFiveRounds.includes(tileIndex))
    if (allInFirstFive) return true
  }
  return false
}

// 规则1图标
function getRule1Icon() {
  if (isRule1Satisfied()) return 'fa-check-circle'
  if (isRule1Violated()) return 'fa-times-circle'
  return 'fa-question-circle' // 未确定状态
}

// 判定条件2：8号轮次计分板（索引7）不能出现在第5和第6轮（索引4和5）

// 规则2是否确定达成
function isRule2Satisfied() {
  const selected = selectedRoundScoring.value
  const tile8Index = 7 // 8号板块对应的索引是7
  const position = selected.indexOf(tile8Index)

  // 8号板块未被选中，且已选满6个，确定不会出现在第5和第6轮
  if (position === -1 && selected.length >= 6) return true

  // 8号板块被选中且位置在前4轮（索引0-3）
  if (position >= 0 && position <= 3) return true

  return false
}

// 规则2是否确定违反
function isRule2Violated() {
  const selected = selectedRoundScoring.value
  const tile8Index = 7 // 8号板块对应的索引是7
  const position = selected.indexOf(tile8Index)

  // 8号板块被选中且位置在第5或第6轮（索引4或5）
  if (position >= 4) return true
  return false
}

// 规则2图标
function getRule2Icon() {
  if (isRule2Satisfied()) return 'fa-check-circle'
  if (isRule2Violated()) return 'fa-times-circle'
  return 'fa-question-circle' // 未确定状态
}

function getFinalScoringCardStyle(index) {
  return getFinalScoringSelectionSpriteStyleByBackendId(index + 1)
}

// 获取最终计分板块后端编码（前端索引0-3对应后端编码1-4）
function getFinalScoringBackendCode(index) {
  return index + 1
}

// 切换最终计分板块选择状态（单选）
function toggleFinalScoringSelection(index) {
  if (selectedFinalScoring.value === index) {
    selectedFinalScoring.value = null
  } else {
    selectedFinalScoring.value = index
  }
}

// 书行动后端编码到图片索引的映射（后端1-6 -> 图片0-5）
// 后端: 1, 2, 3, 4, 5, 6
// 图片: 4, 0, 3, 1, 2, 5
const bookActionBackendToImageMap = [4, 0, 3, 1, 2, 5]

// 获取书行动卡片背景样式（6等分切割）
function getBookActionCardStyle(index) {
  // 6张卡片横向排列，位置点：0%, 20%, 40%, 60%, 80%, 100%
  const positions = [0, 20, 40, 60, 80, 100]
  // 将前端显示索引映射到正确的图片位置
  const imageIndex = bookActionBackendToImageMap[index]
  return {
    backgroundImage: 'url(/assets/images/book_actions.png)',
    backgroundSize: '600% 100%',
    backgroundPositionX: `${positions[imageIndex]}%`
  }
}

// 获取书行动后端编码（前端索引0-5对应后端编码1-6）
function getBookActionBackendCode(index) {
  return index + 1
}

// 切换书行动选择状态（多选，必须选3个）
function toggleBookActionSelection(index) {
  const currentIndex = selectedBookActions.value.indexOf(index)
  if (currentIndex > -1) {
    // 已选中，取消选择
    selectedBookActions.value.splice(currentIndex, 1)
  } else {
    // 未选中，检查是否已达到最大选择数量（3个）
    if (selectedBookActions.value.length >= 3) {
      return // 已达上限，点击无效（不提示）
    }
    selectedBookActions.value.push(index)
  }
}

function getRoundBoosterCardStyle(index) {
  return getRoundBoosterFrontSpriteStyleByBackendId(index + 1)
}

// 获取回合助推板后端编码（前端索引0-9对应后端编码1-10）
function getRoundBoosterBackendCode(index) {
  return index + 1
}

// 切换回合助推板选择状态（多选，数量 = 玩家数 + 3）
function toggleRoundBoosterSelection(index) {
  const currentIndex = selectedRoundBoosters.value.indexOf(index)
  if (currentIndex > -1) {
    // 已选中，取消选择
    selectedRoundBoosters.value.splice(currentIndex, 1)
  } else {
    // 未选中，检查是否已达到最大选择数量
    if (selectedRoundBoosters.value.length >= requiredRoundBoosterCount.value) {
      return // 已达上限，点击无效（不提示）
    }
    selectedRoundBoosters.value.push(index)
  }
}

// 获取能力板块背景样式
function getAbilityCardStyle(index) {
  return getAbilityTileStyleByBackendId(index + 1)
}

// 获取能力板块后端编码（前端索引0-11对应后端编码1-12）
function getAbilityBackendCode(index) {
  return index + 1
}

// 能力板块拖拽相关
const draggedAbilityIndex = ref(null)
const draggedFromPosition = ref(null)

// 点击选择方式相关
const selectedAbilityCard = ref(null)
const selectedAbilitySlot = ref(null)

// 开始拖拽能力板块
function handleAbilityDragStart(event, abilityIndex, fromPosition = null) {
  draggedAbilityIndex.value = abilityIndex
  draggedFromPosition.value = fromPosition
  event.dataTransfer.effectAllowed = 'move'
}

// 拖拽经过摆放位置
function handleAbilityDragOver(event, positionIndex) {
  event.preventDefault()
}

// 放置能力板块到摆放位置
function handleAbilityDrop(event, positionIndex) {
  event.preventDefault()
  if (draggedAbilityIndex.value === null) return

  // 如果该位置已有板块，先清空原位置
  const existingAbility = abilityOrder.value[positionIndex]
  if (existingAbility !== null && draggedFromPosition.value !== null) {
    // 交换位置
    abilityOrder.value[draggedFromPosition.value] = existingAbility
  }

  // 放置新板块
  abilityOrder.value[positionIndex] = draggedAbilityIndex.value

  // 如果是从其他位置拖来的，清空原位置
  if (draggedFromPosition.value !== null && draggedFromPosition.value !== positionIndex) {
    abilityOrder.value[draggedFromPosition.value] = null
  }

  draggedAbilityIndex.value = null
  draggedFromPosition.value = null
}

// 拖拽结束
function handleAbilityDragEnd() {
  draggedAbilityIndex.value = null
  draggedFromPosition.value = null
}

// 从摆放位置移除能力板块
function removeAbilityFromPosition(positionIndex) {
  abilityOrder.value[positionIndex] = null
}

// 点击选择能力卡片
function handleAbilityCardClick(abilityIndex) {
  // 如果卡片已放置，不能选择
  if (abilityOrder.value.includes(abilityIndex)) return

  // 如果已经选中了这张卡片，取消选中
  if (selectedAbilityCard.value === abilityIndex) {
    selectedAbilityCard.value = null
    return
  }

  // 如果已经选中了摆放框，直接放置
  if (selectedAbilitySlot.value !== null) {
    abilityOrder.value[selectedAbilitySlot.value] = abilityIndex
    selectedAbilitySlot.value = null
    selectedAbilityCard.value = null
  } else {
    // 否则选中这张卡片
    selectedAbilityCard.value = abilityIndex
  }
}

// 点击选择摆放框
function handleAbilitySlotClick(positionIndex) {
  // 如果该位置已有板块，不做任何事（或可以移除）
  if (abilityOrder.value[positionIndex] !== null) return

  // 如果已经选中了这个位置，取消选中
  if (selectedAbilitySlot.value === positionIndex) {
    selectedAbilitySlot.value = null
    return
  }

  // 如果已经选中了卡片，直接放置
  if (selectedAbilityCard.value !== null) {
    abilityOrder.value[positionIndex] = selectedAbilityCard.value
    selectedAbilityCard.value = null
    selectedAbilitySlot.value = null
  } else {
    // 否则选中这个框
    selectedAbilitySlot.value = positionIndex
  }
}

// 获取高科板块背景样式
function getTechCardStyle(index) {
  return getScienceTileStyleByBackendId(index + 1)
}

// 获取高科板块后端编码（前端索引0-17对应后端编码1-18）
function getTechBackendCode(index) {
  return index + 1
}

// 高科板块拖拽相关
const draggedTechIndex = ref(null)
const draggedTechFromPosition = ref(null)

// 点击选择方式相关
const selectedTechCard = ref(null)
const selectedTechSlot = ref(null)

// 开始拖拽高科板块
function handleTechDragStart(event, techIndex, fromPosition = null) {
  draggedTechIndex.value = techIndex
  draggedTechFromPosition.value = fromPosition
  event.dataTransfer.effectAllowed = 'move'
}

// 拖拽经过摆放位置
function handleTechDragOver(event, positionIndex) {
  event.preventDefault()
}

// 放置高科板块到摆放位置
function handleTechDrop(event, positionIndex) {
  event.preventDefault()
  if (draggedTechIndex.value === null) return

  // 如果该位置已有板块，先清空原位置
  const existingTech = techOrder.value[positionIndex]
  if (existingTech !== null && draggedTechFromPosition.value !== null) {
    // 交换位置
    techOrder.value[draggedTechFromPosition.value] = existingTech
  }

  // 放置新板块
  techOrder.value[positionIndex] = draggedTechIndex.value

  // 如果是从其他位置拖来的，清空原位置
  if (draggedTechFromPosition.value !== null && draggedTechFromPosition.value !== positionIndex) {
    techOrder.value[draggedTechFromPosition.value] = null
  }

  draggedTechIndex.value = null
  draggedTechFromPosition.value = null
}

// 拖拽结束
function handleTechDragEnd() {
  draggedTechIndex.value = null
  draggedTechFromPosition.value = null
}

// 从摆放位置移除高科板块
function removeTechFromPosition(positionIndex) {
  techOrder.value[positionIndex] = null
}

// 点击选择高科卡片
function handleTechCardClick(techIndex) {
  // 如果卡片已放置，不能选择
  if (techOrder.value.includes(techIndex)) return

  // 如果已经选中了这张卡片，取消选中
  if (selectedTechCard.value === techIndex) {
    selectedTechCard.value = null
    return
  }

  // 如果已经选中了摆放框，直接放置
  if (selectedTechSlot.value !== null) {
    techOrder.value[selectedTechSlot.value] = techIndex
    selectedTechSlot.value = null
    selectedTechCard.value = null
  } else {
    // 否则选中这张卡片
    selectedTechCard.value = techIndex
  }
}

// 点击选择高科摆放框
function handleTechSlotClick(positionIndex) {
  // 如果该位置已有板块，不做任何事
  if (techOrder.value[positionIndex] !== null) return

  // 如果已经选中了这个位置，取消选中
  if (selectedTechSlot.value === positionIndex) {
    selectedTechSlot.value = null
    return
  }

  // 如果已经选中了卡片，直接放置
  if (selectedTechCard.value !== null) {
    techOrder.value[positionIndex] = selectedTechCard.value
    selectedTechCard.value = null
    selectedTechSlot.value = null
  } else {
    // 否则选中这个框
    selectedTechSlot.value = positionIndex
  }
}

// 自定义游戏模式设置
const customSettings = reactive({
  mainTime: 45,
  byoYomiTime: 45,
  timeoutStrategy: 'random_fast_action'
})

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
  const strategy = STRATEGY_OPTIONS.find(s => s.id === value)
  return strategy ? strategy.label : '选择策略'
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
    case 'roundBoosters':
      return isRoundBoostersComplete.value
    case 'roundScoring':
      return isRoundScoringComplete.value && isRule1Satisfied() && isRule2Satisfied()
    case 'finalScoring':
      return isFinalScoringComplete.value
    case 'abilities':
      return isAbilitiesComplete.value
    case 'techs':
      return isTechsComplete.value
    case 'bookActions':
      return isBookActionsComplete.value
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
  // 同步更新顺序列表（恢复期间不覆盖）
  if (!isRestoringSettings) {
    const newList = []
    for (let i = 0; i < newCount; i++) {
      newList.push({ id: i + 1, name: `玩家 ${i + 1}` })
    }
    playerOrderList.value = newList
  }

  // 调整高科板块摆放区域大小
  const newTechSize = 2 + 2 * newCount
  const currentTechOrder = techOrder.value
  if (newTechSize > currentTechOrder.length) {
    // 增加位置
    techOrder.value = [...currentTechOrder, ...Array(newTechSize - currentTechOrder.length).fill(null)]
  } else if (newTechSize < currentTechOrder.length) {
    // 减少位置，保留已摆放的板块
    techOrder.value = currentTechOrder.slice(0, newTechSize)
  }
})

function goBack() {
  gameStore.endGame()
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
  // 重置各配置项的选择状态
  selectedPlanningCard.value = null
  selectedFactions.value = []
  selectedPalaces.value = []
  selectedRoundBoosters.value = []
  selectedRoundScoring.value = []
  selectedFinalScoring.value = null
  abilityOrder.value = Array(12).fill(null)
  techOrder.value = Array(8).fill(null)
  selectedBookActions.value = []
  // 重置随机开关
  Object.keys(initNavRandom).forEach(key => {
    initNavRandom[key] = false
  })
}

async function handleSubmit() {
  if (isLoading.value) {
    return
  }

  // 1. 检查玩家配置
  for (let i = 0; i < form.players.length; i++) {
    const player = form.players[i]
    if (player.type === 'human') {
      // 人类玩家需要填写ID
      if (!player.playerId || player.playerId.trim() === '') {
        alert(`玩家 ${i + 1} 未输入ID，请输入玩家ID`)
        return
      }
    }
    // AI玩家策略检查（预留，默认通过）
  }

  // 2. 检查游戏模式（预留，默认通过）
  if (form.gameMode === 'custom') {
    // 自定义模式检查（预留）
  }

  // 3. 检查初始板块配置
  if (form.initSettings.mode === '自定义') {
    // 检查是否所有导航项都已完成
    const incompleteItems = []
    for (const item of initNavItems) {
      const isRandom = initNavRandom[item.id]
      if (!isRandom && !isNavItemComplete(item.id)) {
        incompleteItems.push(item.name)
      }
    }
    if (incompleteItems.length > 0) {
      alert(`初始板块配置未完成：${incompleteItems.join('、')}，请完成配置或开启随机`)
      return
    }
  }

  isLoading.value = true
  clearLoadingCountdownTimer()
  loadingStage.value = 'countdown'
  loadingCountdown.value = 3
  loadingText.value = '游戏即将开始'
  await runStartCountdown(3)
  await new Promise(resolve => setTimeout(resolve, 360))

  loadingStage.value = 'loading'
  loadingText.value = '正在启动游戏...'

  // 组装返回数据
  const gameSettings = buildGameSettings()

  try {
    // 发送到后端并等待响应
    await sendGameSettingsToBackend(gameSettings)

    loadingText.value = '正在准备游戏状态...'
    const isReady = await waitForGameStateReady()
    if (!isReady) {
      throw new Error('游戏状态准备超时')
    }

    // 保存到 store 并跳转
    gameStore.setSettings(gameSettings)
    gameStore.startGame()
    await router.push('/game')
  } catch (error) {
    console.error('启动游戏失败:', error)
    alert('启动游戏失败，请检查后端服务是否运行')
  } finally {
    clearLoadingCountdownTimer()
    loadingStage.value = 'loading'
    loadingCountdown.value = 3
    loadingText.value = '正在启动游戏...'
    isLoading.value = false
  }
}

// 获取计时器配置
function getTimerConfig() {
  if (form.gameMode === 'standard') {
    return {
      main_time: 45 * 60 * 1000,
      byo_yomi_time: 45 * 1000,
      timeout_strategy: 'random_fast_action'
    }
  } else if (form.gameMode === 'quick') {
    return {
      main_time: 25 * 60 * 1000,
      byo_yomi_time: 25 * 1000,
      timeout_strategy: 'random_fast_action'
    }
  } else {
    // 自定义模式
    return {
      main_time: customSettings.mainTime * 60 * 1000,
      byo_yomi_time: customSettings.byoYomiTime * 1000,
      timeout_strategy: customSettings.timeoutStrategy
    }
  }
}

// 组装游戏设置数据
function buildGameSettings() {
  const players = form.players.map((player, index) => ({
    type: player.type,
    args: player.type === 'human' ? player.playerId : (player.strategy || 'random')
  }))

  const initPlayerOrder = form.playerOrder === '随机'
    ? 'random'
    : playerOrderList.value.map(p => p.id)

  const setupTiles = buildSetupTiles()

  return {
    num_players: form.playerCount,
    players: players,
    game_mode: {
      type: form.gameMode
    },
    timer_config: getTimerConfig(),
    init_settings: {
      init_player_order: initPlayerOrder,
      setup_tiles: setupTiles,
      _init_mode: form.initSettings.mode === '随机' ? 'global_random' : 'custom'
    }
  }
}

// 组装初始板块配置
function buildSetupTiles() {
  const isRandom = form.initSettings.mode === '随机'

  if (isRandom) {
    return {
      planning_cards: 'random',
      factions: 'random',
      palace_tiles: 'random',
      round_boosters: 'random',
      round_scoring: 'random',
      final_scoring: 'random',
      ability_tiles: 'random',
      science_tiles: 'random',
      book_actions: 'random'
    }
  }

  // 规划卡：前端索引0-6对应后端编码1-7，直接返回 index + 1
  const planningCardValue = selectedPlanningCard.value !== null ? selectedPlanningCard.value + 1 : 'random'

  return {
    planning_cards: initNavRandom.planningCards ? 'random' : planningCardValue,
    factions: initNavRandom.factions ? 'random' : selectedFactions.value.map(i => i + 1),
    palace_tiles: initNavRandom.palace ? 'random' : selectedPalaces.value.map(i => i + 1),
    round_boosters: initNavRandom.roundBoosters ? 'random' : selectedRoundBoosters.value.map(i => i + 1),
    round_scoring: initNavRandom.roundScoring ? 'random' : selectedRoundScoring.value.map(i => i + 1),
    final_scoring: initNavRandom.finalScoring ? 'random' : (selectedFinalScoring.value !== null ? selectedFinalScoring.value + 1 : 'random'),
    ability_tiles: initNavRandom.abilities ? 'random' : abilityOrder.value.map(i => i !== null ? i + 1 : null),
    science_tiles: initNavRandom.techs ? 'random' : techOrder.value.map(i => i !== null ? i + 1 : null),
    book_actions: initNavRandom.bookActions ? 'random' : selectedBookActions.value.map(i => i + 1)
  }
}

// 发送游戏设置到后端
async function sendGameSettingsToBackend(settings) {
  const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:5001'
  try {
    const response = await fetch(`${apiBaseUrl}/api/game/start`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(settings)
    })
    const result = await response.json()
    console.log('后端响应:', result)

    if (!response.ok || result?.status !== 'success') {
      throw new Error(result?.error || result?.message || '启动游戏失败')
    }

    return result
  } catch (error) {
    console.error('发送游戏设置失败:', error)
    throw error
  }
}

async function waitForGameStateReady(retries = 60, delay = 250) {
  const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:5001'

  for (let i = 0; i < retries; i++) {
    try {
      const response = await fetch(`${apiBaseUrl}/api/game/state`)
      const result = await response.json()

      if (response.ok && result?.status === 'success' && result?.state) {
        return true
      }
    } catch (error) {
      console.warn('等待游戏状态就绪时重试:', error)
    }

    await new Promise(resolve => setTimeout(resolve, delay))
  }

  return false
}

// ========== 恢复 pending 设置（从游戏菜单跳转回来）==========
function restoreSettingsFromPending() {
  const pending = localStorage.getItem('pendingSetupSettings')
  if (!pending) return

  isRestoringSettings = true
  try {
    const { mode, settings } = JSON.parse(pending)
    if (!settings) return

    // 1. 解析初始设置（先解析，后续依赖这些数据）
    const initSettings = settings.init_settings || {}
    const tiles = initSettings.setup_tiles || {}

    // 2. 恢复玩家数量
    const targetPlayerCount = settings.num_players || 3
    form.playerCount = targetPlayerCount

    // 3. 恢复玩家配置
    if (settings.players) {
      // 先填充到目标数量
      while (form.players.length < targetPlayerCount) {
        form.players.push({ type: 'human', playerId: '', strategy: '' })
      }
      if (form.players.length > targetPlayerCount) {
        form.players.splice(targetPlayerCount)
      }
      // 再设置具体值
      settings.players.forEach((p, i) => {
        if (i < form.players.length) {
          form.players[i].type = p.type
          if (p.type === 'human') {
            form.players[i].playerId = p.args || ''
            form.players[i].strategy = ''
          } else {
            form.players[i].playerId = ''
            form.players[i].strategy = p.args || 'random'
          }
        }
      })
    }

    // 4. 恢复计时器配置
    const tc = settings.timer_config || {}
    if (tc.main_time === 45 * 60 * 1000 && tc.byo_yomi_time === 45 * 1000) {
      form.gameMode = 'standard'
    } else if (tc.main_time === 25 * 60 * 1000 && tc.byo_yomi_time === 25 * 1000) {
      form.gameMode = 'quick'
    } else {
      form.gameMode = 'custom'
      customSettings.mainTime = Math.round((tc.main_time || 2700000) / 60000)
      customSettings.byoYomiTime = Math.round((tc.byo_yomi_time || 45000) / 1000)
      customSettings.timeoutStrategy = tc.timeout_strategy || 'random_fast_action'
    }

    // 5. 恢复玩家顺序和拖动列表
    if (initSettings.init_player_order === 'random') {
      form.playerOrder = '随机'
      playerOrderList.value = Array.from({ length: targetPlayerCount }, (_, i) => ({
        id: i + 1,
        name: `玩家 ${i + 1}`
      }))
    } else if (Array.isArray(initSettings.init_player_order)) {
      form.playerOrder = '指定'
      playerOrderList.value = initSettings.init_player_order.map((id) => ({
        id,
        name: `玩家 ${id}`
      }))
    } else {
      // 默认回退
      form.playerOrder = '随机'
      playerOrderList.value = Array.from({ length: targetPlayerCount }, (_, i) => ({
        id: i + 1,
        name: `玩家 ${i + 1}`
      }))
    }

    // 6. 判断初始板块模式
    // 使用前端发送的 _init_mode 标记精确区分全局随机和自定义
    if (initSettings._init_mode === 'global_random') {
      form.initSettings.mode = '随机'
    } else {
      form.initSettings.mode = '自定义'
    }

    // 4. 恢复 setup_tiles
    // 规划卡（后端 1-7，前端 0-6 索引）
    if (tiles.planning_cards === 'random') {
      initNavRandom.planningCards = true
      selectedPlanningCard.value = null
    } else if (typeof tiles.planning_cards === 'number') {
      initNavRandom.planningCards = false
      selectedPlanningCard.value = tiles.planning_cards - 1
    }

    // 派系（后端 1-12，前端 0-11 索引）
    if (tiles.factions === 'random') {
      initNavRandom.factions = true
      selectedFactions.value = []
    } else if (Array.isArray(tiles.factions)) {
      initNavRandom.factions = false
      selectedFactions.value = tiles.factions.map(v => v - 1)
    }

    // 宫殿
    if (tiles.palace_tiles === 'random') {
      initNavRandom.palace = true
      selectedPalaces.value = []
    } else if (Array.isArray(tiles.palace_tiles)) {
      initNavRandom.palace = false
      selectedPalaces.value = tiles.palace_tiles.map(v => v - 1)
    }

    // 回合助推板
    if (tiles.round_boosters === 'random') {
      initNavRandom.roundBoosters = true
      selectedRoundBoosters.value = []
    } else if (Array.isArray(tiles.round_boosters)) {
      initNavRandom.roundBoosters = false
      selectedRoundBoosters.value = tiles.round_boosters.map(v => v - 1)
    }

    // 轮次计分
    if (tiles.round_scoring === 'random') {
      initNavRandom.roundScoring = true
      selectedRoundScoring.value = []
    } else if (Array.isArray(tiles.round_scoring)) {
      initNavRandom.roundScoring = false
      selectedRoundScoring.value = tiles.round_scoring.map(v => v - 1)
    }

    // 最终计分
    if (tiles.final_scoring === 'random') {
      initNavRandom.finalScoring = true
      selectedFinalScoring.value = null
    } else if (typeof tiles.final_scoring === 'number') {
      initNavRandom.finalScoring = false
      selectedFinalScoring.value = tiles.final_scoring - 1
    }

    // 能力板块（顺序数组，后端 1-12 -> 前端 0-11）
    if (tiles.ability_tiles === 'random') {
      initNavRandom.abilities = true
      abilityOrder.value = Array(12).fill(null)
    } else if (Array.isArray(tiles.ability_tiles)) {
      initNavRandom.abilities = false
      abilityOrder.value = tiles.ability_tiles.map(v => v !== null ? v - 1 : null)
    }

    // 科学板块（动态数量：2 + 2 * 玩家数）
    if (tiles.science_tiles === 'random') {
      initNavRandom.techs = true
      techOrder.value = Array(2 + 2 * form.playerCount).fill(null)
    } else if (Array.isArray(tiles.science_tiles)) {
      initNavRandom.techs = false
      techOrder.value = tiles.science_tiles.map(v => v !== null ? v - 1 : null)
    }

    // 书行动
    if (tiles.book_actions === 'random') {
      initNavRandom.bookActions = true
      selectedBookActions.value = []
    } else if (Array.isArray(tiles.book_actions)) {
      initNavRandom.bookActions = false
      selectedBookActions.value = tiles.book_actions.map(v => v - 1)
    }

    // 清理 pending
    localStorage.removeItem('pendingSetupSettings')
  } catch (e) {
    console.error('恢复设置失败:', e)
    localStorage.removeItem('pendingSetupSettings')
  }
  
  // 延迟到下一个 tick 重置标志，确保 watch 回调先执行
  nextTick(() => {
    isRestoringSettings = false
  })
}

// 页面加载时尝试恢复
onMounted(() => {
  restoreSettingsFromPending()
})
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
  line-height: 1.5;
}

.mode-desc-line1 {
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--text-secondary);
}

.mode-desc-line2 {
  font-size: 0.85rem;
  font-weight: 400;
  color: var(--text-secondary);
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
  margin-bottom: 24px;
}

.custom-option:last-child {
  margin-bottom: 0;
}

.custom-option-label {
  font-size: var(--font-size-body);
  font-weight: 600;
  color: var(--text-primary);
}

.custom-option-desc {
  font-size: var(--font-size-small);
  color: var(--text-secondary);
  margin-top: -8px;
}

.custom-option-input {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.custom-option-input-single {
  flex-wrap: nowrap;
}

.custom-option-btn-full {
  flex: 1;
  min-width: auto;
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

/* 拖动条容器 */
.slider-container {
  display: flex;
  align-items: center;
  gap: 16px;
}

.slider-track-wrapper {
  flex: 1;
  position: relative;
  height: 20px;
}

.slider {
  width: 100%;
  -webkit-appearance: none;
  appearance: none;
  height: 20px;
  background: rgba(255, 255, 255, 0.12);
  border-radius: 10px;
  outline: none;
  cursor: pointer;
}

.slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 18px;
  height: 18px;
  background: var(--accent);
  border-radius: 50%;
  cursor: pointer;
  transition: transform 0.15s ease;
  margin-top: 1px;
}

.slider::-webkit-slider-thumb:hover {
  transform: scale(1.1);
}

.slider::-moz-range-thumb {
  width: 18px;
  height: 18px;
  background: var(--accent);
  border-radius: 50%;
  cursor: pointer;
  border: none;
}

.slider-marks {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  margin-top: 2px;
}

.slider-marks-inner {
  position: relative;
  height: 18px;
  width: 100%;
  box-sizing: border-box;
}

.slider-mark {
  position: absolute;
  top: 0;
  transform: translateX(-50%);
  font-size: 0.75rem;
  color: var(--text-secondary);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.slider-mark::before {
  content: '';
  width: 1px;
  height: 6px;
  background: rgba(255, 255, 255, 0.25);
}

.slider-value {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 70px;
  height: 20px;
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

/* TODO占位符样式 */
.todo-placeholder {
  padding: 40px 20px;
  text-align: center;
  color: var(--text-secondary);
}

.todo-placeholder p {
  font-size: var(--font-size-body);
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
:deep(.init-modal .modal-content) {
  height: 720px;
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

.nav-item-left .nav-complete-icon.is-hidden {
  visibility: hidden;
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
  margin-bottom: 36px;
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
  margin-bottom: 32px;
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
  border: 3.5px solid var(--accent);
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
  margin-bottom: 32px;
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
  border: 3.5px solid var(--accent);
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

/* 宫殿板块后端编码标签 */
.palace-card-label {
  position: absolute;
  bottom: 4px;
  left: 4px;
  width: 20px;
  height: 20px;
  background: rgba(0, 0, 0, 0.8);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 0.7rem;
  font-weight: 600;
  z-index: 2;
}

/* 回合助推板配置 */
.round-boosters-config {
  padding: 4px 20px 20px;
}

.round-boosters-hint {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.85rem;
  color: var(--text-secondary);
  margin-bottom: 44px;
}

.round-boosters-hint i {
  color: var(--text-secondary);
  font-size: 0.9rem;
}

.round-boosters-grid {
  display: flex;
  flex-direction: column;
  gap: 16px;
  align-items: center;
}

.round-boosters-row {
  display: flex;
  gap: 18px;
  justify-content: center;
}

.round-booster-card {
  position: relative;
  /* 助推板原比例 3:8（宽:高），卡片比例与之匹配 */
  /* 设置高度 190px，宽度按 3:8 计算为 71.25px */
  width: 71.25px;
  height: 190px;
  border-radius: 12px;
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  border: 3px solid transparent;
  background: transparent;
  box-sizing: border-box;
  display: flex;
  align-items: center;
  justify-content: center;
}

.round-booster-card:hover {
  transform: translateY(-3px);
}

.round-booster-card.active {
  border: 3.5px solid var(--accent);
  box-shadow: 0 6px 20px rgba(0, 123, 255, 0.2);
}

.round-booster-card-image {
  /* 原图尺寸：1500x800，2行10列布局 */
  /* 单个助推板尺寸：150x400，宽高比 3:8 */
  /* 卡片尺寸 71.25x190px，图片占85%即 60.56x161.5px */
  width: 60.56px;
  height: 161.5px;
  background-repeat: no-repeat;
  background-size: cover;
  background-position: center;
  border-radius: 4px;
}

.round-booster-card-check {
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

/* 回合助推板后端编码标签 */
.round-booster-card-label {
  position: absolute;
  bottom: 14px;
  left: 8px;
  width: 18px;
  height: 18px;
  background: rgba(0, 0, 0, 0.8);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 0.65rem;
  font-weight: 600;
  z-index: 2;
}

/* 轮次计分板块配置 */
.round-scoring-config {
  padding: 4px 20px 20px;
}

.round-scoring-hint {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.85rem;
  color: var(--text-secondary);
  margin-bottom: 24px;
}

.round-scoring-hint i {
  color: var(--text-secondary);
  font-size: 0.9rem;
}

/* 判定条件提示 */
.round-scoring-rules {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 12px;
  padding: 10px 12px;
  background: var(--bg-secondary);
  border-radius: 6px;
  border: 1px solid var(--border);
}

.rule-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.75rem;
  color: var(--text-secondary);
  transition: color 0.2s ease;
}

.rule-item i {
  font-size: 0.85rem;
  color: var(--text-secondary);
  transition: color 0.2s ease;
}

.rule-item.satisfied {
  color: #28a745;
}

.rule-item.satisfied i {
  color: #28a745;
}

.rule-item.violated {
  color: #dc3545;
}

.rule-item.violated i {
  color: #dc3545;
}

.round-scoring-grid {
  display: flex;
  flex-direction: column;
  gap: 9px;
  align-items: center;
}

.round-scoring-row {
  display: flex;
  gap: 15.7px;
  justify-content: center;
}

.round-scoring-card {
  position: relative;
  width: 156.8px;
  height: 90.7px;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  border: 2px solid transparent;
  background: transparent;
  box-sizing: border-box;
  display: flex;
  align-items: center;
  justify-content: center;
}

.round-scoring-card:hover {
  transform: translateY(-2px);
}

.round-scoring-card.active {
  border: 2.5px solid var(--accent);
  box-shadow: 0 4px 12px rgba(0, 123, 255, 0.2);
}

.round-scoring-card-image {
  width: 85%;
  height: 85%;
  background-repeat: no-repeat;
  background-size: cover;
  background-position: center;
  border-radius: 4px;
  transform: translateY(2px);
}

.round-scoring-card-order {
  position: absolute;
  top: 0;
  right: 0;
  width: 24.6px;
  height: 24.6px;
  background: var(--accent);
  border-radius: 0 0 0 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 0.8rem;
  font-weight: 700;
  z-index: 3;
}

/* 轮次计分板块后端编码标签 */
.round-scoring-card-label {
  position: absolute;
  bottom: 12px;
  left: 14px;
  width: 18px;
  height: 18px;
  background: rgba(0, 0, 0, 0.8);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 0.65rem;
  font-weight: 600;
  z-index: 2;
}

/* 最终计分板块配置 */
.final-scoring-config {
  padding: 4px 20px 20px;
}

.final-scoring-hint {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.85rem;
  color: var(--text-secondary);
  margin-bottom: 60px;
}

.final-scoring-hint i {
  color: var(--text-secondary);
  font-size: 0.9rem;
}

.final-scoring-grid {
  display: flex;
  flex-direction: column;
  gap: 16px;
  align-items: center;
}

.final-scoring-row {
  display: flex;
  gap: 20px;
  justify-content: center;
}

.final-scoring-card {
  position: relative;
  width: 104px;
  height: 120px;
  border-radius: 12px;
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  border: 3.5px solid transparent;
  background: transparent;
  box-sizing: border-box;
  display: flex;
  align-items: center;
  justify-content: center;
}

.final-scoring-card:hover {
  transform: translateY(-3px);
}

.final-scoring-card.active {
  border: 3.5px solid var(--accent);
  box-shadow: 0 6px 20px rgba(0, 123, 255, 0.2);
}

.final-scoring-card-image {
  width: 85%;
  height: 85%;
  background-repeat: no-repeat;
  background-size: cover;
  background-position: center;
  border-radius: 4px;
  transform: translateY(3px);
}

.final-scoring-card-check {
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

/* 最终计分板块后端编码标签 */
.final-scoring-card-label {
  position: absolute;
  bottom: 14px;
  left: 8px;
  width: 20px;
  height: 20px;
  background: rgba(0, 0, 0, 0.8);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 0.7rem;
  font-weight: 600;
  z-index: 2;
}

/* 能力板块配置 */
.abilities-config {
  padding: 4px 20px 20px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.abilities-hint {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.85rem;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.abilities-hint i {
  color: var(--text-secondary);
  font-size: 0.9rem;
}

/* 上方选择区 */
.abilities-selection {
  display: flex;
  flex-direction: column;
  gap: 10px;
  align-items: center;
}

.abilities-row {
  display: flex;
  gap: 12px;
  justify-content: center;
}

.ability-card {
  position: relative;
  width: 75px;
  height: 73px;
  border-radius: 8px;
  overflow: hidden;
  cursor: grab;
  transition: transform 0.2s ease, opacity 0.2s ease;
  border: 2px solid transparent;
  background: var(--bg-tertiary);
  box-sizing: border-box;
}

.ability-card:hover {
  transform: translateY(-2px);
}

.ability-card.is-placed {
  opacity: 0.4;
  cursor: not-allowed;
}

.ability-card.is-selected {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.3);
}

.ability-card-image {
  width: 100%;
  height: 100%;
  background-repeat: no-repeat;
  background-size: cover;
  background-position: center;
}

/* 能力板块后端编码标签 */
.ability-card-label {
  position: absolute;
  bottom: 2px;
  left: 2px;
  width: 16px;
  height: 16px;
  background: rgba(0, 0, 0, 0.8);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 0.6rem;
  font-weight: 600;
  z-index: 2;
}

/* 下方摆放区 */
.abilities-board-container {
  display: flex;
  justify-content: center;
  padding: 8px 0;
}

.abilities-board {
  width: 534.6px;
  height: 253.0px;
  background-size: 534.6px 253.0px;
  background-repeat: no-repeat;
  background-position: center;
  position: relative;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}

.abilities-board-grid {
  position: absolute;
  top: 0;
  left: 0;
  width: 534.6px;
  height: 253.0px;
}

.ability-board-slot {
  position: absolute;
  width: 63.8px;
  height: 61.6px;
  background: rgba(0, 123, 255, 0.125);
  border: 3.5px dashed rgba(0, 123, 255, 0.8);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

/* 12个位置的具体坐标（基于534.6x253.0的显示尺寸，3行4列布局，列优先顺序）
   列宽：534.6/4 = 133.7px
   第1列中心偏右约50.6px，之后每列+133.1px
   行高：253.0/3 = 84.3px */
.ability-board-slot:nth-child(1) { left: 50.6px; top: 18.7px; }
.ability-board-slot:nth-child(2) { left: 50.6px; top: 97.9px; }
.ability-board-slot:nth-child(3) { left: 50.6px; top: 174.9px; }
.ability-board-slot:nth-child(4) { left: 183.7px; top: 18.7px; }
.ability-board-slot:nth-child(5) { left: 183.7px; top: 97.9px; }
.ability-board-slot:nth-child(6) { left: 183.7px; top: 174.9px; }
.ability-board-slot:nth-child(7) { left: 317.9px; top: 18.7px; }
.ability-board-slot:nth-child(8) { left: 317.9px; top: 97.9px; }
.ability-board-slot:nth-child(9) { left: 317.9px; top: 174.9px; }
.ability-board-slot:nth-child(10) { left: 451.0px; top: 18.7px; }
.ability-board-slot:nth-child(11) { left: 451.0px; top: 97.9px; }
.ability-board-slot:nth-child(12) { left: 451.0px; top: 174.9px; }

.ability-board-slot:hover {
  border-color: rgba(0, 123, 255, 0.95);
  background: rgba(0, 123, 255, 0.4);
}

.ability-board-slot.is-occupied {
  border-style: solid;
  border-color: transparent;
  background: transparent;
}

.ability-board-slot.is-selected {
  border-style: solid;
  border-color: var(--accent);
  background: rgba(0, 123, 255, 0.35);
  box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.3);
}

.ability-slot-number {
  font-size: 1.75rem;
  font-weight: 700;
  color: rgba(0, 123, 255, 0.8);
  text-shadow:
    -1px -1px 0 rgba(255, 255, 255, 0.9),
    1px -1px 0 rgba(255, 255, 255, 0.9),
    -1px 1px 0 rgba(255, 255, 255, 0.9),
    1px 1px 0 rgba(255, 255, 255, 0.9),
    0 1px 3px rgba(0, 0, 0, 0.5);
  user-select: none;
  -webkit-user-select: none;
}

.ability-board-slot:hover .ability-slot-number {
  color: rgba(0, 123, 255, 1);
  text-shadow:
    -1px -1px 0 rgba(255, 255, 255, 1),
    1px -1px 0 rgba(255, 255, 255, 1),
    -1px 1px 0 rgba(255, 255, 255, 1),
    1px 1px 0 rgba(255, 255, 255, 1),
    0 1px 4px rgba(0, 0, 0, 0.6);
}

.ability-placed-card {
  position: relative;
  width: 100%;
  height: 100%;
  cursor: grab;
}

.ability-placed-card .ability-card-image {
  border-radius: 6px;
}

.ability-order-number {
  position: absolute;
  top: 4px;
  left: 4px;
  width: 22px;
  height: 22px;
  background: var(--accent);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 0.75rem;
  font-weight: 700;
  z-index: 2;
}

/* 书行动配置 */
.book-actions-config {
  padding: 4px 20px 20px;
}

.book-actions-hint {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.85rem;
  color: var(--text-secondary);
  margin-bottom: 32px;
}

.book-actions-hint i {
  color: var(--text-secondary);
  font-size: 0.9rem;
}

/* 高科板块配置 */
.techs-config {
  padding: 4px 20px 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.techs-hint {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.85rem;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.techs-hint i {
  color: var(--text-secondary);
  font-size: 0.9rem;
}

/* 上方选择区 */
.techs-selection {
  display: flex;
  flex-direction: column;
  gap: 6px;
  align-items: center;
}

.techs-row {
  display: flex;
  gap: 8px;
  justify-content: center;
}

.tech-card {
  position: relative;
  width: 83px;
  height: 53px;
  border-radius: 6px;
  overflow: hidden;
  cursor: grab;
  transition: transform 0.2s ease, opacity 0.2s ease;
  border: 2px solid transparent;
  background: var(--bg-tertiary);
  box-sizing: border-box;
}

.tech-card:hover {
  transform: translateY(-2px);
}

.tech-card.is-placed {
  opacity: 0.4;
  cursor: not-allowed;
}

.tech-card.is-selected {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.3);
}

.tech-card-image {
  width: 100%;
  height: 100%;
  background-repeat: no-repeat;
  background-size: cover;
  background-position: center;
}

/* 高科板块后端编码标签 */
.tech-card-label {
  position: absolute;
  bottom: 2px;
  left: 2px;
  width: 14px;
  height: 14px;
  background: rgba(0, 0, 0, 0.8);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 0.55rem;
  font-weight: 600;
  z-index: 2;
}

/* 下方摆放区 */
.techs-board-container {
  display: flex;
  justify-content: center;
  padding: 8px 0;
}

.techs-board {
  width: 428px;
  height: 214px;
  background-size: 428px 248px;
  background-repeat: no-repeat;
  background-position: bottom;
  position: relative;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
  overflow: hidden;
}

/* 3人局：2行4列布局，完整显示图片 */
.techs-board-3 {
  height: 248px;
  background-size: 428px 248px;
  background-position: center;
}

/* 4人局：3行2列布局，完整显示图片 */
.techs-board-4 {
  height: 319px;
  background-size: 428px 319px;
  background-position: center;
}

/* 5人局：3行4列布局，宽度与4人局一致428px，高度319px（图片等比例缩放后裁剪/压缩显示） */
.techs-board-5 {
  height: 319px;
  background-size: 428px auto;
  background-position: center top;
}

.techs-board-grid {
  position: absolute;
  top: 0;
  left: 0;
  width: 428px;
  height: 214px;
}

/* 3人局grid高度适配 */
.techs-board-3 .techs-board-grid {
  height: 248px;
}

/* 4人局grid高度适配 */
.techs-board-4 .techs-board-grid {
  height: 319px;
}

/* 5人局grid高度适配 */
.techs-board-5 .techs-board-grid {
  height: 319px;
}

.tech-board-slot {
  position: absolute;
  width: 86px;
  height: 55px;
  background: rgba(0, 123, 255, 0.125);
  border: 3.5px dashed rgba(0, 123, 255, 0.8);
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  cursor: pointer;
}

/* 8个位置的具体坐标（基于428x214的显示尺寸，2行4列布局，列优先顺序）
   宽度86px高度55px */
.tech-board-slot:nth-child(1) { left: 10.5px; top: 32px; }
.tech-board-slot:nth-child(2) { left: 10.5px; top: 107.5px; }
.tech-board-slot:nth-child(3) { left: 117.5px; top: 32px; }
.tech-board-slot:nth-child(4) { left: 117.5px; top: 107.5px; }
.tech-board-slot:nth-child(5) { left: 224.5px; top: 32px; }
.tech-board-slot:nth-child(6) { left: 224.5px; top: 107.5px; }
.tech-board-slot:nth-child(7) { left: 331.5px; top: 32px; }
.tech-board-slot:nth-child(8) { left: 331.5px; top: 107.5px; }

/* 3人局槽位位置调整 - 下移34px（列优先） */
.techs-board-3 .tech-board-slot:nth-child(1) { left: 10.5px; top: 66px; }
.techs-board-3 .tech-board-slot:nth-child(2) { left: 10.5px; top: 141.5px; }
.techs-board-3 .tech-board-slot:nth-child(3) { left: 117.5px; top: 66px; }
.techs-board-3 .tech-board-slot:nth-child(4) { left: 117.5px; top: 141.5px; }
.techs-board-3 .tech-board-slot:nth-child(5) { left: 224.5px; top: 66px; }
.techs-board-3 .tech-board-slot:nth-child(6) { left: 224.5px; top: 141.5px; }
.techs-board-3 .tech-board-slot:nth-child(7) { left: 331.5px; top: 66px; }
.techs-board-3 .tech-board-slot:nth-child(8) { left: 331.5px; top: 141.5px; }

/* 4人局槽位位置调整（基于428x319的显示尺寸，1-8列优先，9-10不变） */
/* 第1行2个槽位（9-10）- 水平中心对齐第2行两两中点 */
.techs-board-4 .tech-board-slot:nth-child(9) { left: 64px; top: 27.5px; }
.techs-board-4 .tech-board-slot:nth-child(10) { left: 278px; top: 27.5px; }
/* 第2-3行8个槽位（1-8）- 列优先 */
.techs-board-4 .tech-board-slot:nth-child(1) { left: 10.5px; top: 142px; }
.techs-board-4 .tech-board-slot:nth-child(2) { left: 10.5px; top: 217.5px; }
.techs-board-4 .tech-board-slot:nth-child(3) { left: 117.5px; top: 142px; }
.techs-board-4 .tech-board-slot:nth-child(4) { left: 117.5px; top: 217.5px; }
.techs-board-4 .tech-board-slot:nth-child(5) { left: 224.5px; top: 142px; }
.techs-board-4 .tech-board-slot:nth-child(6) { left: 224.5px; top: 217.5px; }
.techs-board-4 .tech-board-slot:nth-child(7) { left: 331.5px; top: 142px; }
.techs-board-4 .tech-board-slot:nth-child(8) { left: 331.5px; top: 217.5px; }

/* 5人局槽位位置调整（基于428x426的显示尺寸，1-8列优先，9-12不变） */
/* 第1行4个槽位（9-12） */
.techs-board-5 .tech-board-slot:nth-child(9) { left: 10.5px; top: 66px; }
.techs-board-5 .tech-board-slot:nth-child(10) { left: 117.5px; top: 66px; }
.techs-board-5 .tech-board-slot:nth-child(11) { left: 224.5px; top: 66px; }
.techs-board-5 .tech-board-slot:nth-child(12) { left: 331.5px; top: 66px; }
/* 第2-3行8个槽位（1-8）- 列优先 */
.techs-board-5 .tech-board-slot:nth-child(1) { left: 10.5px; top: 142px; }
.techs-board-5 .tech-board-slot:nth-child(2) { left: 10.5px; top: 217.5px; }
.techs-board-5 .tech-board-slot:nth-child(3) { left: 117.5px; top: 142px; }
.techs-board-5 .tech-board-slot:nth-child(4) { left: 117.5px; top: 217.5px; }
.techs-board-5 .tech-board-slot:nth-child(5) { left: 224.5px; top: 142px; }
.techs-board-5 .tech-board-slot:nth-child(6) { left: 224.5px; top: 217.5px; }
.techs-board-5 .tech-board-slot:nth-child(7) { left: 331.5px; top: 142px; }
.techs-board-5 .tech-board-slot:nth-child(8) { left: 331.5px; top: 217.5px; }

.tech-board-slot:hover {
  border-color: rgba(0, 123, 255, 0.85);
  background: rgba(0, 123, 255, 0.3);
}

.tech-board-slot.is-occupied {
  border-style: solid;
  border-color: transparent;
  background: transparent;
}

.tech-board-slot.is-selected {
  border-style: solid;
  border-color: var(--accent);
  background: rgba(0, 123, 255, 0.3);
  box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.25);
}

.tech-slot-number {
  font-size: 1.75rem;
  font-weight: 700;
  color: rgba(0, 123, 255, 0.8);
  text-shadow:
    -1px -1px 0 rgba(255, 255, 255, 0.9),
    1px -1px 0 rgba(255, 255, 255, 0.9),
    -1px 1px 0 rgba(255, 255, 255, 0.9),
    1px 1px 0 rgba(255, 255, 255, 0.9),
    0 1px 3px rgba(0, 0, 0, 0.5);
  user-select: none;
  -webkit-user-select: none;
}

.tech-board-slot:hover .tech-slot-number {
  color: rgba(0, 123, 255, 1);
  text-shadow:
    -1px -1px 0 rgba(255, 255, 255, 1),
    1px -1px 0 rgba(255, 255, 255, 1),
    -1px 1px 0 rgba(255, 255, 255, 1),
    1px 1px 0 rgba(255, 255, 255, 1),
    0 1px 4px rgba(0, 0, 0, 0.6);
}

.tech-placed-card {
  position: relative;
  width: 100%;
  height: 100%;
  cursor: grab;
}

.tech-placed-card .tech-card-image {
  border-radius: 4px;
}

.book-actions-grid {
  display: flex;
  flex-direction: column;
  gap: 24px;
  align-items: center;
}

.book-actions-row {
  display: flex;
  gap: 32px;
  justify-content: center;
}

.book-action-card {
  position: relative;
  width: 165px;
  height: 90px;
  border-radius: 12px;
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  border: 3px solid transparent;
  background: transparent;
  box-sizing: border-box;
  display: flex;
  align-items: center;
  justify-content: center;
}

.book-action-card:hover {
  transform: translateY(-3px);
}

.book-action-card.active {
  border: 3.5px solid var(--accent);
  box-shadow: 0 6px 20px rgba(0, 123, 255, 0.2);
}

.book-action-card-image {
  width: 124px;
  height: 68px;
  background-repeat: no-repeat;
  background-size: cover;
  background-position: center;
  border-radius: 4px;
}

.book-action-card-check {
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

/* 书行动后端编码标签 */
.book-action-card-label {
  position: absolute;
  bottom: 10px;
  left: 22px;
  width: 20px;
  height: 20px;
  background: rgba(0, 0, 0, 0.8);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 0.7rem;
  font-weight: 600;
  z-index: 2;
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

.loading-overlay {
  position: fixed;
  inset: 0;
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(10, 10, 10, 0.84);
  backdrop-filter: blur(8px);
  animation: setup-loading-fade-in 0.24s ease;
}

.countdown-overlay {
  position: fixed;
  inset: 0;
  z-index: 10000;
  display: flex;
  align-items: center;
  justify-content: center;
  pointer-events: none;
}

@keyframes setup-loading-fade-in {
  from {
    opacity: 0;
  }

  to {
    opacity: 1;
  }
}

.loading-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
  padding: 44px 60px;
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: 16px;
  box-shadow: 0 12px 36px rgba(0, 0, 0, 0.42);
}

.loading-overlay > .loading-content.loading-content-countdown {
  opacity: 0;
  transform: scale(0.96);
  pointer-events: none;
}

.countdown-overlay .loading-content-countdown {
  min-width: 360px;
  gap: 18px;
  padding: 48px 64px;
  border-color: rgba(0, 123, 255, 0.32);
  box-shadow:
    0 20px 54px rgba(0, 0, 0, 0.48),
    0 0 0 1px rgba(0, 123, 255, 0.12);
  animation: countdown-panel-in 0.32s ease;
}

.loading-spinner {
  font-size: 2.75rem;
  color: var(--accent);
}

.loading-text {
  font-size: 1.2rem;
  font-weight: 600;
  color: var(--text-primary);
}

.loading-subtext {
  font-size: 0.9rem;
  color: var(--text-secondary);
}

.loading-subtext-emphasis {
  color: rgba(255, 255, 255, 0.86);
  letter-spacing: 0.08em;
}

.countdown-badge {
  position: relative;
  width: 112px;
  height: 112px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  color: #ffffff;
  background:
    radial-gradient(circle at 30% 28%, rgba(164, 217, 255, 0.96), rgba(0, 123, 255, 0.92) 56%, rgba(0, 88, 204, 0.92) 100%);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.28),
    inset 0 -12px 20px rgba(0, 66, 158, 0.22),
    0 18px 42px rgba(0, 123, 255, 0.22);
  isolation: isolate;
  overflow: visible;
  animation: countdown-pop 0.42s cubic-bezier(0.22, 1, 0.36, 1);
}

.countdown-badge::before,
.countdown-badge::after {
  content: '';
  position: absolute;
  border-radius: 50%;
  pointer-events: none;
}

.countdown-badge::before {
  inset: -18px;
  z-index: -2;
  background:
    conic-gradient(
      from 0deg,
      rgba(0, 123, 255, 0) 0deg,
      rgba(110, 190, 255, 0.18) 48deg,
      rgba(0, 123, 255, 0.52) 122deg,
      rgba(0, 123, 255, 0.1) 192deg,
      rgba(110, 190, 255, 0.28) 286deg,
      rgba(0, 123, 255, 0) 360deg
    );
  filter: blur(10px);
  opacity: 0.6;
  animation: countdown-halo-spin 3.8s linear infinite;
}

.countdown-badge::after {
  inset: -14px;
  z-index: -1;
  background:
    radial-gradient(circle, rgba(92, 176, 255, 0.26) 0%, rgba(0, 123, 255, 0.12) 48%, rgba(0, 123, 255, 0) 72%);
  opacity: 0.8;
  animation: countdown-halo-breathe 1.9s ease-in-out infinite;
}

.countdown-digit {
  position: relative;
  z-index: 1;
  display: block;
  font-size: 3.1rem;
  font-weight: 700;
  line-height: 1;
  text-shadow: 0 4px 18px rgba(0, 0, 0, 0.25);
  animation: countdown-digit 0.6s cubic-bezier(0.22, 1, 0.36, 1);
}

.countdown-progress {
  width: 100%;
  max-width: 260px;
  height: 6px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.08);
  overflow: hidden;
}

.countdown-progress-bar {
  display: block;
  width: 100%;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, rgba(0, 123, 255, 1), rgba(115, 193, 255, 0.92));
  transform-origin: left center;
  animation: countdown-bar 3s linear forwards;
}

@keyframes countdown-panel-in {
  from {
    opacity: 0;
    transform: translateY(8px) scale(0.98);
  }

  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

@keyframes countdown-pop {
  from {
    transform: scale(0.78);
  }

  to {
    transform: scale(1);
  }
}

@keyframes countdown-digit {
  from {
    opacity: 0;
    transform: scale(0.7);
  }

  to {
    opacity: 1;
    transform: scale(1);
  }
}

@keyframes countdown-halo-spin {
  from {
    transform: rotate(0deg) scale(0.98);
  }

  to {
    transform: rotate(360deg) scale(1.02);
  }
}

@keyframes countdown-halo-breathe {
  0%,
  100% {
    opacity: 0.52;
    transform: scale(0.94);
  }

  50% {
    opacity: 0.82;
    transform: scale(1.04);
  }
}

@keyframes countdown-bar {
  from {
    transform: scaleX(1);
  }

  to {
    transform: scaleX(0);
  }
}
</style>
