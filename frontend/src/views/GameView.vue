<template>
  <div class="game-page">
    <div class="main-container">
      <!-- 左侧：玩家面板 -->
      <div class="players-monitor">
        <div class="monitor-header">
          <i class="fas fa-users"></i>
          <div>玩家面板</div>
        </div>
        <div class="monitor-content">
          <TransitionGroup
            tag="div"
            class="player-grid"
            id="player-grid"
            name="player-card"
          >
            <div
              v-for="player in activePlayerItems"
              :key="`player-${player.id}`"
              class="player-card"
              :data-player-id="player.id"
              :class="{
                collapsed: collapsedPlayers[player.id],
                'is-current-action-player': currentActionPlayerId === player.id,
                'is-transitioning': playerCardTransitionStates[player.id]
              }"
              :ref="(element) => setPlayerCardRef(player.id, element)"
            >
              <svg
                v-if="currentActionPlayerId === player.id && hasPlayerCardRingGeometry(player.id)"
                class="player-card-ring"
                :viewBox="getPlayerCardRingViewBox(player.id)"
                :style="getPlayerCardRingStyle(player.id)"
                aria-hidden="true"
              >
                <path
                  class="player-card-ring-flow-aura"
                  :d="getPlayerCardRingPath(player.id)"
                  pathLength="100"
                />
                <path
                  class="player-card-ring-flow-soft"
                  :d="getPlayerCardRingPath(player.id)"
                  pathLength="100"
                />
                <path
                  class="player-card-ring-flow-mid"
                  :d="getPlayerCardRingPath(player.id)"
                  pathLength="100"
                />
                <path
                  class="player-card-ring-flow-core"
                  :d="getPlayerCardRingPath(player.id)"
                  pathLength="100"
                />
                <path
                  class="player-card-ring-flow-bright"
                  :d="getPlayerCardRingPath(player.id)"
                  pathLength="100"
                />
              </svg>
              <div class="player-header" @click="togglePlayer(player.id)">
                <div class="player-header-left">
                  <div class="planning-card-indicator">
                    <div
                      class="planning-card-circle"
                      :tabindex="player.planningCardId !== null ? 0 : -1"
                      title=""
                      :aria-label="player.planningCardId !== null ? `预览${player.planningCard}规划卡` : '未分配规划卡'"
                      :class="{ 'is-visible': player.planningCardId !== null }"
                      :style="{ backgroundColor: getPlanningCardColor(player.planningCardId) }"
                      @mouseenter="handlePlanningCardMouseEnter(player.planningCardId, player.planningCard, $event)"
                      @mouseleave="handlePlanningCardMouseLeave"
                      @focus="handlePlanningCardMouseEnter(player.planningCardId, player.planningCard, $event)"
                      @blur="handlePlanningCardMouseLeave"
                      @keydown.esc.prevent="hideEntityPreview"
                    ></div>
                  </div>
                  <div class="player-title">
                    <span class="player-name">玩家 {{ player.id + 1 }}</span>
                    <span
                      class="palace-tile-badge"
                      :class="{
                        'is-inactive': player.palaceTileId !== null && !player.isGotPalace,
                        'is-hidden-placeholder': player.palaceTileId === null
                      }"
                      :tabindex="player.palaceTileId !== null ? 0 : -1"
                      title=""
                      :aria-label="player.palaceTileId !== null ? `预览${player.palaceTileId}号宫殿板块${player.isGotPalace ? '' : '（未激活）'}` : undefined"
                      :aria-hidden="player.palaceTileId === null ? 'true' : 'false'"
                      @mouseenter="handlePalaceTileMouseEnter(player.palaceTileId, player.isGotPalace, $event)"
                      @mouseleave="handlePalaceTileMouseLeave"
                      @focus="handlePalaceTileMouseEnter(player.palaceTileId, player.isGotPalace, $event)"
                      @blur="handlePalaceTileMouseLeave"
                      @keydown.esc.prevent="hideEntityPreview"
                    >
                      <span class="palace-tile-badge-value">{{ player.palaceTileId }}</span>
                      <span
                        v-if="!player.isGotPalace"
                        class="palace-tile-badge-status"
                        aria-hidden="true"
                      >
                        <i class="fas fa-ban"></i>
                      </span>
                    </span>
                    <span
                      v-if="player.factionId !== null"
                      class="faction-badge"
                    >
                      <span
                        class="faction-badge-avatar"
                        tabindex="0"
                        title=""
                        :aria-label="`预览${player.faction}派系板块`"
                        @mouseenter="handleFactionBadgeMouseEnter(player.factionId, player.faction, $event)"
                        @mouseleave="handleFactionBadgeMouseLeave"
                        @focus="handleFactionBadgeMouseEnter(player.factionId, player.faction, $event)"
                        @blur="handleFactionBadgeMouseLeave"
                        @keydown.esc.prevent="hideEntityPreview"
                      >
                        <span
                          class="faction-badge-avatar-image"
                          aria-hidden="true"
                          :style="getFactionBadgeStyle(player.factionId)"
                        ></span>
                      </span>
                      <span class="faction-badge-name">{{ player.faction }}</span>
                    </span>
                  </div>
                </div>
                <div class="player-header-right">
                  <PlayerTimer :player-id="player.id" :current-player-id="currentActionPlayerId" />
                  <div class="player-score">{{ player.score }}</div>
                </div>
              </div>
              <div
                class="player-status"
                @transitionrun="handlePlayerStatusTransitionStart(player.id, $event)"
                @transitionend="handlePlayerStatusTransitionEnd(player.id, $event)"
                @transitioncancel="handlePlayerStatusTransitionEnd(player.id, $event)"
              >
                <div class="player-stats">
                  <div
                    v-for="(row, rowIndex) in buildPlayerStatusRows(player)"
                    :key="`player-${player.id}-row-${rowIndex}`"
                    class="stat-row"
                    :style="{ '--stat-columns': row.length }"
                    :class="{
                      'is-building-row': row.some((item) => item.type === 'building'),
                      'is-wide-row': row.length >= 5,
                      'is-ultra-wide-row': row.length >= 6
                    }"
                  >
                    <div
                      v-for="item in row"
                      :key="item.key"
                      class="stat-item"
                      :title="item.label"
                    >
                      <div class="stat-content">
                        <div class="stat-icon-wrapper">
                          <canvas
                            v-if="item.type === 'building'"
                            :key="`bld-${player.planningCardId}-${item.buildingId}`"
                            class="stat-image"
                            :ref="el => drawPlayerBuildingIcon(el, player, item.buildingId)"
                            :aria-label="item.label"
                          ></canvas>
                          <div
                            v-else-if="item.type === 'magic'"
                            class="icon-stack"
                            aria-hidden="true"
                          >
                            <span class="magic-disc"></span>
                            <span class="magic-disc-label">{{ item.magicValue }}</span>
                          </div>
                          <i
                            v-else
                            :class="[item.iconClass, 'stat-icon']"
                            aria-hidden="true"
                          ></i>
                          <span
                            v-if="item.badgeValue !== null && item.badgeValue !== undefined"
                            class="stat-badge"
                          >
                            {{ item.badgeValue }}
                          </span>
                        </div>
                        <span class="stat-value">{{ item.value }}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <!-- 活跃玩家空状态 -->
            <div
              v-if="stateVersion > 0 && activePlayerItems.length === 0"
              key="__active-empty__"
              class="player-empty-state"
            >
              <span class="player-empty-state-text">无活跃玩家</span>
            </div>
            <!-- 分割线 -->
            <div
              :key="'__divider__'"
              class="player-pass-divider"
            >
              <span class="player-pass-divider-line"></span>
              <span class="player-pass-divider-text">已略过</span>
              <span class="player-pass-divider-line"></span>
            </div>
            <!-- 已pass玩家空状态 -->
            <div
              v-if="stateVersion > 0 && passedPlayerItems.length === 0"
              key="__passed-empty__"
              class="player-empty-state"
            >
              <span class="player-empty-state-text">当前无已略过玩家</span>
            </div>
            <!-- 已pass玩家 -->
            <div
              v-for="player in passedPlayerItems"
              :key="`player-${player.id}`"
              class="player-card is-passed"
              :data-player-id="player.id"
              :class="{
                collapsed: collapsedPlayers[player.id],
                'is-current-action-player': currentActionPlayerId === player.id,
                'is-transitioning': playerCardTransitionStates[player.id]
              }"
              :ref="(element) => setPlayerCardRef(player.id, element)"
            >
              <svg
                v-if="currentActionPlayerId === player.id && hasPlayerCardRingGeometry(player.id)"
                class="player-card-ring"
                :viewBox="getPlayerCardRingViewBox(player.id)"
                :style="getPlayerCardRingStyle(player.id)"
                aria-hidden="true"
              >
                <path
                  class="player-card-ring-flow-aura"
                  :d="getPlayerCardRingPath(player.id)"
                  pathLength="100"
                />
                <path
                  class="player-card-ring-flow-soft"
                  :d="getPlayerCardRingPath(player.id)"
                  pathLength="100"
                />
                <path
                  class="player-card-ring-flow-mid"
                  :d="getPlayerCardRingPath(player.id)"
                  pathLength="100"
                />
                <path
                  class="player-card-ring-flow-core"
                  :d="getPlayerCardRingPath(player.id)"
                  pathLength="100"
                />
                <path
                  class="player-card-ring-flow-bright"
                  :d="getPlayerCardRingPath(player.id)"
                  pathLength="100"
                />
              </svg>
              <div class="player-header" @click="togglePlayer(player.id)">
                <div class="player-header-left">
                  <div class="planning-card-indicator">
                    <div
                      class="planning-card-circle"
                      :tabindex="player.planningCardId !== null ? 0 : -1"
                      title=""
                      :aria-label="player.planningCardId !== null ? `预览${player.planningCard}规划卡` : '未分配规划卡'"
                      :class="{ 'is-visible': player.planningCardId !== null }"
                      :style="{ backgroundColor: getPlanningCardColor(player.planningCardId) }"
                      @mouseenter="handlePlanningCardMouseEnter(player.planningCardId, player.planningCard, $event)"
                      @mouseleave="handlePlanningCardMouseLeave"
                      @focus="handlePlanningCardMouseEnter(player.planningCardId, player.planningCard, $event)"
                      @blur="handlePlanningCardMouseLeave"
                      @keydown.esc.prevent="hideEntityPreview"
                    ></div>
                  </div>
                  <div class="player-title">
                    <span class="player-name">玩家 {{ player.id + 1 }}</span>
                    <span
                      class="palace-tile-badge"
                      :class="{
                        'is-inactive': player.palaceTileId !== null && !player.isGotPalace,
                        'is-hidden-placeholder': player.palaceTileId === null
                      }"
                      :tabindex="player.palaceTileId !== null ? 0 : -1"
                      title=""
                      :aria-label="player.palaceTileId !== null ? `预览${player.palaceTileId}号宫殿板块${player.isGotPalace ? '' : '（未激活）'}` : undefined"
                      :aria-hidden="player.palaceTileId === null ? 'true' : 'false'"
                      @mouseenter="handlePalaceTileMouseEnter(player.palaceTileId, player.isGotPalace, $event)"
                      @mouseleave="handlePalaceTileMouseLeave"
                      @focus="handlePalaceTileMouseEnter(player.palaceTileId, player.isGotPalace, $event)"
                      @blur="handlePalaceTileMouseLeave"
                      @keydown.esc.prevent="hideEntityPreview"
                    >
                      <span class="palace-tile-badge-value">{{ player.palaceTileId }}</span>
                      <span
                        v-if="!player.isGotPalace"
                        class="palace-tile-badge-status"
                        aria-hidden="true"
                      >
                        <i class="fas fa-ban"></i>
                      </span>
                    </span>
                    <span
                      v-if="player.factionId !== null"
                      class="faction-badge"
                    >
                      <span
                        class="faction-badge-avatar"
                        tabindex="0"
                        title=""
                        :aria-label="`预览${player.faction}派系板块`"
                        @mouseenter="handleFactionBadgeMouseEnter(player.factionId, player.faction, $event)"
                        @mouseleave="handleFactionBadgeMouseLeave"
                        @focus="handleFactionBadgeMouseEnter(player.factionId, player.faction, $event)"
                        @blur="handleFactionBadgeMouseLeave"
                        @keydown.esc.prevent="hideEntityPreview"
                      >
                        <span
                          class="faction-badge-avatar-image"
                          aria-hidden="true"
                          :style="getFactionBadgeStyle(player.factionId)"
                        ></span>
                      </span>
                      <span class="faction-badge-name">{{ player.faction }}</span>
                    </span>
                  </div>
                </div>
                <div class="player-header-right">
                  <PlayerTimer :player-id="player.id" :current-player-id="currentActionPlayerId" />
                  <div class="player-score">{{ player.score }}</div>
                </div>
              </div>
              <div
                class="player-status"
                @transitionrun="handlePlayerStatusTransitionStart(player.id, $event)"
                @transitionend="handlePlayerStatusTransitionEnd(player.id, $event)"
                @transitioncancel="handlePlayerStatusTransitionEnd(player.id, $event)"
              >
                <div class="player-stats">
                  <div
                    v-for="(row, rowIndex) in buildPlayerStatusRows(player)"
                    :key="`player-${player.id}-row-${rowIndex}`"
                    class="stat-row"
                    :style="{ '--stat-columns': row.length }"
                    :class="{
                      'is-building-row': row.some((item) => item.type === 'building'),
                      'is-wide-row': row.length >= 5,
                      'is-ultra-wide-row': row.length >= 6
                    }"
                  >
                    <div
                      v-for="item in row"
                      :key="item.key"
                      class="stat-item"
                      :title="item.label"
                    >
                      <div class="stat-content">
                        <div class="stat-icon-wrapper">
                          <canvas
                            v-if="item.type === 'building'"
                            :key="`bld-${player.planningCardId}-${item.buildingId}`"
                            class="stat-image"
                            :ref="el => drawPlayerBuildingIcon(el, player, item.buildingId)"
                            :aria-label="item.label"
                          ></canvas>
                          <div
                            v-else-if="item.type === 'magic'"
                            class="icon-stack"
                            aria-hidden="true"
                          >
                            <span class="magic-disc"></span>
                            <span class="magic-disc-label">{{ item.magicValue }}</span>
                          </div>
                          <i
                            v-else
                            :class="[item.iconClass, 'stat-icon']"
                            aria-hidden="true"
                          ></i>
                          <span
                            v-if="item.badgeValue !== null && item.badgeValue !== undefined"
                            class="stat-badge"
                          >
                            {{ item.badgeValue }}
                          </span>
                        </div>
                        <span class="stat-value">{{ item.value }}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </TransitionGroup>
        </div>
      </div>

      <!-- 中间区域 -->
      <div class="middle-section">
        <div class="middle-header">
          <i class="fas fa-gamepad"></i>
          <div>游戏区域</div>
        </div>
        <div class="middle-content">
          <div class="game-grid" id="game-grid">
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
                            width="140"
                            height="140"
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
                    <!-- 六边形网格层 -->
                    <g id="hex-grid-group">
                      <!-- 六边形将通过JavaScript生成 -->
                    </g>
                    <!-- 元素层，用于放置图标 -->
                    <g id="hex-elements"></g>
                    <!-- 高亮层 -->
                    <g id="hex-highlight-layer"></g>
                    <!-- 悬停层 -->
                    <g id="hex-hover-layer"></g>
                    <!-- 编号层 -->
                    <g id="hex-numbers"></g>
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
                <div ref="roundInfoContainerRef" class="round-info-container">
                  <!-- 左侧计分区 -->
                  <div class="left-column" id="left-scoring-grid" :style="roundInfoLeftColumnStyle">
                    <!-- 第1回合 -->
                    <div
                      class="grid-cell round-1"
                      data-round="1"
                      :class="{ 'current-round': currentRound === 1, 'flipped': roundStates[1]?.isFlipped }"
                      :tabindex="roundStates[1]?.currentX > 0 ? 0 : -1"
                      title=""
                      :aria-label="getRoundScoringAriaLabel(1)"
                      @mouseenter="handleRoundScoringMouseEnter(1, $event)"
                      @mouseleave="handleRoundScoringMouseLeave"
                      @focus="handleRoundScoringMouseEnter(1, $event)"
                      @blur="handleRoundScoringMouseLeave"
                      @keydown.esc.prevent="hideEntityPreview"
                    >
                      <span class="round-label">第 1 回合</span>
                      <div class="card-container">
                        <div class="card-face front">
                          <div aria-hidden="true" class="scoring-image" :style="getRoundScoringSpriteStyleByBackendId(roundStates[1]?.currentX)"></div>
                        </div>
                        <div class="card-face back">
                          <div aria-hidden="true" class="scoring-image" :style="roundScoringBackSpriteStyle"></div>
                        </div>
                      </div>
                    </div>
                    <!-- 第4回合 -->
                    <div
                      class="grid-cell round-4"
                      data-round="4"
                      :class="{ 'current-round': currentRound === 4, 'flipped': roundStates[4]?.isFlipped }"
                      :tabindex="roundStates[4]?.currentX > 0 ? 0 : -1"
                      title=""
                      :aria-label="getRoundScoringAriaLabel(4)"
                      @mouseenter="handleRoundScoringMouseEnter(4, $event)"
                      @mouseleave="handleRoundScoringMouseLeave"
                      @focus="handleRoundScoringMouseEnter(4, $event)"
                      @blur="handleRoundScoringMouseLeave"
                      @keydown.esc.prevent="hideEntityPreview"
                    >
                      <span class="round-label">第 4 回合</span>
                      <div class="card-container">
                        <div class="card-face front">
                          <div aria-hidden="true" class="scoring-image" :style="getRoundScoringSpriteStyleByBackendId(roundStates[4]?.currentX)"></div>
                        </div>
                        <div class="card-face back">
                          <div aria-hidden="true" class="scoring-image" :style="roundScoringBackSpriteStyle"></div>
                        </div>
                      </div>
                    </div>
                    <!-- 第2回合 -->
                    <div
                      class="grid-cell round-2"
                      data-round="2"
                      :class="{ 'current-round': currentRound === 2, 'flipped': roundStates[2]?.isFlipped }"
                      :tabindex="roundStates[2]?.currentX > 0 ? 0 : -1"
                      title=""
                      :aria-label="getRoundScoringAriaLabel(2)"
                      @mouseenter="handleRoundScoringMouseEnter(2, $event)"
                      @mouseleave="handleRoundScoringMouseLeave"
                      @focus="handleRoundScoringMouseEnter(2, $event)"
                      @blur="handleRoundScoringMouseLeave"
                      @keydown.esc.prevent="hideEntityPreview"
                    >
                      <span class="round-label">第 2 回合</span>
                      <div class="card-container">
                        <div class="card-face front">
                          <div aria-hidden="true" class="scoring-image" :style="getRoundScoringSpriteStyleByBackendId(roundStates[2]?.currentX)"></div>
                        </div>
                        <div class="card-face back">
                          <div aria-hidden="true" class="scoring-image" :style="roundScoringBackSpriteStyle"></div>
                        </div>
                      </div>
                    </div>
                    <!-- 第5回合 -->
                    <div
                      class="grid-cell round-5"
                      data-round="5"
                      :class="{ 'current-round': currentRound === 5, 'flipped': roundStates[5]?.isFlipped }"
                      :tabindex="roundStates[5]?.currentX > 0 ? 0 : -1"
                      title=""
                      :aria-label="getRoundScoringAriaLabel(5)"
                      @mouseenter="handleRoundScoringMouseEnter(5, $event)"
                      @mouseleave="handleRoundScoringMouseLeave"
                      @focus="handleRoundScoringMouseEnter(5, $event)"
                      @blur="handleRoundScoringMouseLeave"
                      @keydown.esc.prevent="hideEntityPreview"
                    >
                      <span class="round-label">第 5 回合</span>
                      <div class="card-container">
                        <div class="card-face front">
                          <div aria-hidden="true" class="scoring-image" :style="getRoundScoringSpriteStyleByBackendId(roundStates[5]?.currentX)"></div>
                        </div>
                        <div class="card-face back">
                          <div aria-hidden="true" class="scoring-image" :style="roundScoringBackSpriteStyle"></div>
                        </div>
                      </div>
                    </div>
                    <!-- 第3回合 -->
                    <div
                      class="grid-cell round-3"
                      data-round="3"
                      :class="{ 'current-round': currentRound === 3, 'flipped': roundStates[3]?.isFlipped }"
                      :tabindex="roundStates[3]?.currentX > 0 ? 0 : -1"
                      title=""
                      :aria-label="getRoundScoringAriaLabel(3)"
                      @mouseenter="handleRoundScoringMouseEnter(3, $event)"
                      @mouseleave="handleRoundScoringMouseLeave"
                      @focus="handleRoundScoringMouseEnter(3, $event)"
                      @blur="handleRoundScoringMouseLeave"
                      @keydown.esc.prevent="hideEntityPreview"
                    >
                      <span class="round-label">第 3 回合</span>
                      <div class="card-container">
                        <div class="card-face front">
                          <div aria-hidden="true" class="scoring-image" :style="getRoundScoringSpriteStyleByBackendId(roundStates[3]?.currentX)"></div>
                        </div>
                        <div class="card-face back">
                          <div aria-hidden="true" class="scoring-image" :style="roundScoringBackSpriteStyle"></div>
                        </div>
                      </div>
                    </div>
                    <!-- 第6回合（支持叠加） -->
                    <div
                      class="grid-cell round-6"
                      data-round="6"
                      :class="{ 'current-round': currentRound === 6, 'flipped': roundStates[6]?.isFlipped }"
                      :tabindex="roundStates[6]?.currentX > 0 ? 0 : -1"
                      title=""
                      :aria-label="getRoundScoringAriaLabel(6)"
                      @mouseenter="handleRoundScoringMouseEnter(6, $event)"
                      @mouseleave="handleRoundScoringMouseLeave"
                      @focus="handleRoundScoringMouseEnter(6, $event)"
                      @blur="handleRoundScoringMouseLeave"
                      @keydown.esc.prevent="hideEntityPreview"
                    >
                      <span class="round-label">第 6 回合</span>
                      <div class="card-container">
                        <div class="card-face front">
                          <div aria-hidden="true" class="base-image" :style="getRoundScoringSpriteStyleByBackendId(roundStates[6]?.currentX)"></div>
                          <div
                            v-if="roundStates[6]?.finalScoringId !== null"
                            aria-hidden="true"
                            class="overlay-image"
                            :style="getFinalScoringOverlaySpriteStyleByBackendId(roundStates[6]?.finalScoringId)"
                          ></div>
                        </div>
                        <div class="card-face back">
                          <div aria-hidden="true" class="scoring-image" :style="roundScoringBackSpriteStyle"></div>
                        </div>
                      </div>
                    </div>
                  </div>

                  <!-- 右侧奖励区 -->
                  <div class="right-column" id="right-bonus-grid">
                    <div
                      v-for="(bonus, index) in bonusColumns"
                      :key="index"
                      class="bonus-cell"
                      :class="{ flipped: bonus.isFlipped }"
                      :data-index="index"
                      :data-x="bonus.x"
                      :tabindex="bonus.x > 0 ? 0 : -1"
                      title=""
                      :aria-label="bonus.x > 0 ? `预览回合助推板 ${bonus.x}` : undefined"
                      @mouseenter="handleRoundBoosterMouseEnter(bonus, $event)"
                      @mouseleave="handleRoundBoosterMouseLeave"
                      @focus="handleRoundBoosterMouseEnter(bonus, $event)"
                      @blur="handleRoundBoosterMouseLeave"
                      @keydown.esc.prevent="hideEntityPreview"
                    >
                      <div class="card-container">
                        <div class="card-face front">
                          <div aria-hidden="true" class="bonus-sprite-image" :style="getRoundBoosterFrontSpriteStyleByBackendId(bonus.x)"></div>
                        </div>
                        <div class="card-face back">
                          <div aria-hidden="true" class="bonus-sprite-image" :style="getRoundBoosterBackSpriteStyleByBackendId(bonus.x)"></div>
                        </div>
                      </div>
                      <canvas
                        v-if="bonus.isFlipped && bonus.holderMarkId !== null"
                        :key="`bm-${bonus.x}-${bonus.holderMarkId}`"
                        class="bonus-holder-mark"
                        :ref="el => drawBonusHolderMark(el, bonus.holderMarkId)"
                      ></canvas>
                      <span
                        v-if="!bonus.isFlipped && bonus.coinCount > 0"
                        class="bonus-coin-badge"
                        aria-hidden="true"
                      >
                        <i class="fas fa-coins"></i>
                        <span class="bonus-coin-badge-text">x{{ bonus.coinCount }}</span>
                      </span>
                      <span class="bonus-label" :aria-label="`回合助推板 ${bonus.x}`">{{ bonus.x }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 科学能力卡片 -->
            <div class="game-card" :class="{ collapsed: collapsedCards['tactical'] }">
              <div class="game-header" @click="toggleCard('tactical')">
                <div class="game-header-left">
                  <div class="game-title">
                    <i class="fas fa-flask"></i>
                    <span>科学能力</span>
                  </div>
                </div>
                <div class="game-indicator">
                  <i class="fas fa-chevron-down"></i>
                </div>
              </div>
              <div class="science-ability-status">
                <div ref="scienceAbilityLayoutRef" class="science-ability-layout">
                  <div class="science-ability-left">
                    <div ref="leftBoardsStackRef" :class="['left-boards-stack', 'left-boards-stack-' + numPlayers]">
                      <!-- 科学板块 -->
                      <div class="science-board-wrapper">
                        <div class="science-board" :class="['science-board-' + numPlayers, (numPlayers === 3 || numPlayers === 5) ? 'crop-top' : '']" :style="(numPlayers === 3 || numPlayers === 5) ? {} : { backgroundImage: 'url(/assets/images/science_board_' + numPlayers + '.png)' }">
                          <div v-if="numPlayers === 3 || numPlayers === 5" class="science-board-inner">
                            <img class="science-board-img" :src="'/assets/images/science_board_' + numPlayers + '.png'" alt="science board" />
                            <div
                              v-for="(tileId, idx) in scienceTilesOrder"
                              :key="'sci-' + idx"
                              class="science-board-tile"
                              :style="getScienceBoardTileStyle(tileId, idx)"
                              :tabindex="tileId ? 0 : -1"
                              :title="''"
                              :aria-label="tileId ? `预览科学板块 ${tileId}` : undefined"
                              @mouseenter="handleScienceTileMouseEnter(tileId, $event)"
                              @mouseleave="handleScienceTileMouseLeave"
                              @focus="handleScienceTileMouseEnter(tileId, $event)"
                              @blur="handleScienceTileMouseLeave"
@keydown.esc.prevent="hideEntityPreview"
                            >
                              <canvas
                                v-if="tileId && getScienceTileOwnerMarkId(tileId) !== null"
                                :key="`stm-${tileId}-${getScienceTileOwnerMarkId(tileId)}`"
                                class="science-tile-owner-mark"
                                :ref="el => drawScienceTileOwnerMark(el, getScienceTileOwnerMarkId(tileId))"
                              ></canvas>
                              <span v-if="tileId" class="tile-index-badge">{{ tileId }}</span>
                            </div>
                          </div>
                          <template v-else>
                            <div
                              v-for="(tileId, idx) in scienceTilesOrder"
                              :key="'sci-' + idx"
                              class="science-board-tile"
                              :style="getScienceBoardTileStyle(tileId, idx)"
                              :tabindex="tileId ? 0 : -1"
                              :title="''"
                              :aria-label="tileId ? `预览科学板块 ${tileId}` : undefined"
                              @mouseenter="handleScienceTileMouseEnter(tileId, $event)"
                              @mouseleave="handleScienceTileMouseLeave"
                              @focus="handleScienceTileMouseEnter(tileId, $event)"
                              @blur="handleScienceTileMouseLeave"
@keydown.esc.prevent="hideEntityPreview"
                            >
                              <canvas
                                v-if="tileId && getScienceTileOwnerMarkId(tileId) !== null"
                                :key="`stm2-${tileId}-${getScienceTileOwnerMarkId(tileId)}`"
                                class="science-tile-owner-mark"
                                :ref="el => drawScienceTileOwnerMark(el, getScienceTileOwnerMarkId(tileId))"
                              ></canvas>
                              <span v-if="tileId" class="tile-index-badge">{{ tileId }}</span>
                            </div>
                          </template>
                        </div>
                      </div>
                      <!-- 能力板块 -->
                      <div class="ability-board-wrapper">
                        <div class="ability-board" :style="{ backgroundImage: 'url(/assets/images/ability_tiles_board.jpg)' }">
                          <div
                            v-for="(tileId, idx) in abilityTilesOrder"
                            :key="'abi-' + idx"
                            class="ability-board-tile"
                            :style="getAbilityBoardTileStyle(tileId, idx)"
                            :tabindex="tileId ? 0 : -1"
                            :title="''"
                            :aria-label="tileId ? `预览能力板块 ${tileId}` : undefined"
                            @mouseenter="handleAbilityTileMouseEnter(tileId, $event)"
                            @mouseleave="handleAbilityTileMouseLeave"
                            @focus="handleAbilityTileMouseEnter(tileId, $event)"
                            @blur="handleAbilityTileMouseLeave"
                            @keydown.esc.prevent="hideEntityPreview"
                          >
                            <div v-if="tileId" class="ability-tile-owner-strip" aria-hidden="true">
                              <canvas
                                v-for="(markId, ownerIndex) in getAbilityTileOwnerMarkIds(tileId)"
                                :key="`abi-owner-${tileId}-${ownerIndex}-${markId}`"
                                class="ability-tile-owner-mark"
                                :ref="el => drawAbilityTileOwnerMark(el, markId)"
                              ></canvas>
                            </div>
                            <span v-if="tileId" class="tile-index-badge">{{ tileId }}</span>
                            <span v-if="tileId" class="ability-tile-remaining-badge">×{{ getAbilityTileRemainingCount(tileId) }}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                  <div ref="cultBoardSectionRef" class="cult-board-section">
                    <img src="/assets/images/tracks_board.png" alt="tracks board" class="cult-board-image" />
                    <div class="tracks-board-overlay">
                      <TransitionGroup name="track-marker-fade">
                        <canvas
                          v-for="m in allTrackMarkers"
                          :key="m.key"
                          class="track-marker track-tower-marker"
                          :style="m.style"
                          :ref="el => drawTrackTowerMarker(el, m.markId)"
                        ></canvas>
                      </TransitionGroup>
                      <canvas
                        v-for="m in allBaseMeepleMarkers"
                        :key="m.key"
                        class="track-marker track-base-marker"
                        :style="m.style"
                        :ref="el => drawTrackBaseMeeple(el, m.markId)"
                      ></canvas>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧：全局信息区 -->
      <div class="global-section">
        <div class="control-center-section">
          <div class="control-center-header">
            <div class="action-title">
              <i class="fas fa-sliders-h"></i>
              <div>控制中台</div>
            </div>
          </div>
          <div class="control-center-content">
            <div class="control-center-toolbar">
              <button
                type="button"
                class="control-center-button control-center-strategy-button"
                :class="{ 'is-open': controlCenterStrategyModalOpen }"
                @click="openControlCenterStrategyModal"
              >
                <span class="control-center-button-main">
                  <span class="control-center-button-label">策略</span>
                  <span class="control-center-button-value">{{ selectedControlStrategySummaryLabel }}</span>
                </span>
                <i class="fas fa-chevron-right control-center-button-arrow" aria-hidden="true"></i>
              </button>
              <button
                type="button"
                class="control-center-button control-center-recommend-button"
                :class="{ 'is-recommended': hasRecommendedAction }"
                :disabled="!controlCenterCanRun || controlCenterPendingMode !== '' || isAiPlayer"
                @click="recommendControlCenterStrategy"
              >
                <i :class="recommendedActionIconClass" aria-hidden="true"></i>
                <span>推荐</span>
              </button>
              <button
                type="button"
                class="control-center-button control-center-execute-button"
                :class="{ 'has-recommendation': hasRecommendedAction }"
                :disabled="!controlCenterCanRun || controlCenterPendingMode !== '' || isAiPlayer"
                @click="executeControlCenterAction"
              >
                <span>执行</span>
              </button>
            </div>
          </div>
        </div>

        <!-- 可选行动区 -->
        <div class="action-section">
          <div class="action-header">
            <div class="action-title-group">
              <div class="action-title">
                <i class="fas fa-play-circle"></i>
                <div>可选行动</div>
              </div>
              <div class="action-subtitle">{{ actionSubtitle }}</div>
            </div>
            <div v-if="!gameMeta.is_game_over" class="action-header-timer">
              <ActionTimer />
            </div>
            <div class="action-header-pills">
              <div class="action-owner-chip">
                <span class="action-owner-dot" :style="{ backgroundColor: currentActionPlayerColor }"></span>
                <span>{{ currentActionOwnerLabel }}</span>
              </div>
              <div class="action-mode-chip">{{ currentActionModeLabel }}</div>
              <div class="action-count">共<span id="action-count">{{ actionCount }}</span>项</div>
            </div>
            <div v-if="isAiPlayer && !gameMeta.is_game_over" class="ai-thinking-badge">
              <img src="https://img.icons8.com/3d-fluency/500/sparkles.png" alt="AI" />
              <span>AI Thinking ...</span>
            </div>
          </div>
          <div
            id="action-content"
            ref="actionContentRef"
            class="action-content"
            :class="{ 'is-accordion-mode': isActionOverflowMode, 'ai-turn': isAiPlayer }"
          >
            <div
              v-for="group in groupedActionCards"
              :key="group.key"
              class="action-group-card"
              :class="{
                'is-collapsed': isActionOverflowMode && !isActionGroupExpanded(group.groupKey),
                'is-submitting': group.hasPendingSelection,
                'is-disabled': pendingActionId !== null && !group.hasPendingSelection,
                'has-recommended-option': group.hasRecommendedOption
              }"
            >
              <div
                class="action-group-header"
                :class="{
                  'is-collapsible': isActionOverflowMode,
                  'is-expanded': isActionGroupExpanded(group.groupKey)
                }"
                :role="isActionOverflowMode ? 'button' : undefined"
                :tabindex="isActionOverflowMode ? 0 : -1"
                :aria-expanded="isActionOverflowMode ? String(isActionGroupExpanded(group.groupKey)) : undefined"
                @click="toggleActionGroup(group.groupKey)"
                @keydown.enter.prevent="toggleActionGroup(group.groupKey)"
                @keydown.space.prevent="toggleActionGroup(group.groupKey)"
              >
                <div class="action-group-title">{{ group.groupLabel }}</div>
                <div class="action-group-header-meta">
                  <div class="action-group-count-chip">{{ group.options.length }}</div>
                  <div
                    v-if="isActionOverflowMode"
                    class="action-group-toggle"
                    :class="{ 'is-expanded': isActionGroupExpanded(group.groupKey) }"
                    aria-hidden="true"
                  >
                    <i class="fas fa-chevron-right"></i>
                  </div>
                </div>
              </div>
              <div
                class="action-group-body"
                :class="{ 'is-collapsed': isActionOverflowMode && !isActionGroupExpanded(group.groupKey) }"
                :style="getActionGroupBodyStyle(group.groupKey)"
                :aria-hidden="isActionOverflowMode && !isActionGroupExpanded(group.groupKey) ? 'true' : 'false'"
              >
                <div class="action-group-body-inner">
                  <div
                    class="action-group-options"
                    :class="[
                      `is-${group.layoutHint}`,
                      {
                        'is-fixed-grid': group.fixedColumnCount !== null,
                        'has-detail': group.hasDetail,
                        'has-verbose-detail': group.hasVerboseDetail
                      }
                    ]"
                    :style="group.fixedColumnCount !== null ? { '--action-group-columns': group.fixedColumnCount } : undefined"
                  >
                    <button
                      v-for="option in group.options"
                      :key="option.key"
                      type="button"
                      class="action-option-button"
                      :data-color="option.color"
                      :class="{
                        'is-submitting': pendingActionId === option.id,
                        'is-disabled': pendingActionId !== null && pendingActionId !== option.id,
                        'is-compact': !option.detail && group.layoutHint !== 'chips_wrap',
                        'is-recommended': recommendedActionId === option.id
                      }"
                      :disabled="pendingActionId !== null || isAiPlayer || (isActionOverflowMode && !isActionGroupExpanded(group.groupKey))"
                      :title="option.description"
                      @click="selectAction(option)"
                    >
                      <span class="action-option-main">
                        <span class="action-option-label">{{ option.label }}</span>
                        <span v-if="option.detail" class="action-option-detail">{{ option.detail }}</span>
                      </span>
                    </button>
                  </div>
                </div>
              </div>
            </div>
            <div v-if="groupedActionCards.length === 0" key="empty-state" class="panel-empty-state panel-empty-state--action">
              {{ actionEmptyStateMessage }}
            </div>
          </div>
          <div
            v-if="groupedActionCards.length > 0"
            ref="actionMeasureRef"
            class="action-content action-content--measure"
            :style="actionMeasureStyle"
            aria-hidden="true"
          >
            <div
              v-for="group in groupedActionCards"
              :key="`measure-${group.key}`"
              class="action-group-card"
            >
              <div class="action-group-header">
                <div class="action-group-title">{{ group.groupLabel }}</div>
                <div class="action-group-header-meta">
                  <div class="action-group-count-chip">{{ group.options.length }}</div>
                </div>
              </div>
              <div class="action-group-body">
                <div class="action-group-body-inner">
                  <div
                    class="action-group-options"
                    :class="[
                      `is-${group.layoutHint}`,
                      {
                        'is-fixed-grid': group.fixedColumnCount !== null,
                        'has-detail': group.hasDetail,
                        'has-verbose-detail': group.hasVerboseDetail
                      }
                    ]"
                    :style="group.fixedColumnCount !== null ? { '--action-group-columns': group.fixedColumnCount } : undefined"
                  >
                    <div
                      v-for="option in group.options"
                      :key="`measure-${option.key}`"
                      class="action-option-button"
                      :data-color="option.color"
                      :class="{
                        'is-compact': !option.detail && group.layoutHint !== 'chips_wrap'
                      }"
                    >
                      <span class="action-option-main">
                        <span class="action-option-label">{{ option.label }}</span>
                        <span v-if="option.detail" class="action-option-detail">{{ option.detail }}</span>
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

      </div>

      <!-- 最右侧：统一行动记录 (14%) -->
      <div class="action-log-section">
        <div class="global-status">
          <div class="status-header">
            <div class="status-title">
              <i class="fas fa-info-circle"></i>
              <div>对局状态</div>
            </div>
            <button class="more-menu-btn" @click="openGameMenu">
              <i class="fas fa-bars"></i>
            </button>
          </div>
          <div
            class="status-body"
            :class="{ 'has-detail-action': gameMeta.is_game_over && hasFinalScores }"
          >
            <div class="status-content" id="global-status-content">{{ globalStatus }}</div>
            <div v-if="gameMeta.is_game_over && hasFinalScores" class="status-actions">
              <button
                type="button"
                class="status-detail-btn"
                @click="openFinalScoreModal"
              >
                查看最终比分
              </button>
            </div>
          </div>
        </div>

        <div class="action-log-panel">
          <div class="action-log-header">
            <div class="action-title-group">
              <div class="action-title">
                <i class="fas fa-stream"></i>
                <div>行动记录</div>
              </div>
            </div>
            <div class="action-log-toolbar">
              <div class="action-count action-log-count-chip">
                <span id="action-log-count">{{ filteredActionLogs.length }}</span> / {{ renderedActionLogs.length }} 条
              </div>
              <div class="action-log-filter">
                <button
                  type="button"
                  class="action-filter-btn"
                  :class="{ 'is-active': actionLogFilterModalOpen || hasActiveActionLogFilters }"
                  @click.stop="openActionLogFilterModal"
                >
                  <i class="fas fa-filter"></i>
                  <span>筛选</span>
                  <span v-if="actionLogActiveFilterCount > 0" class="action-filter-badge">
                    {{ actionLogActiveFilterCount }}
                  </span>
                </button>
              </div>
            </div>
          </div>
          <!-- 行动记录筛选全屏弹窗 -->
          <Modal
            v-model="actionLogFilterModalOpen"
            title="筛选行动记录"
            size="default"
            :show-close="true"
            :close-on-overlay="true"
            class="action-log-filter-modal"
          >
            <div class="action-filter-modal-body">
              <div class="action-filter-row">
                <!-- 第一列：检索、剩余时间、策略 -->
                <div class="action-filter-column">
                  <div class="action-filter-section">
                    <div class="action-filter-section-title">按记录检索</div>
                    <div class="action-filter-search-grid">
                      <label class="action-filter-search-field">
                        <span class="action-filter-search-label">行动编号</span>
                        <input
                          v-model="draftActionLogActionIdFilter"
                          type="text"
                          inputmode="numeric"
                          class="action-filter-search-input"
                          placeholder="例如 65"
                        >
                      </label>
                      <label class="action-filter-search-field">
                        <span class="action-filter-search-label">本局序号</span>
                        <input
                          v-model="draftActionLogUidFilter"
                          type="text"
                          class="action-filter-search-input"
                          placeholder="例如 act.001"
                        >
                      </label>
                    </div>
                  </div>
                  <div class="action-filter-section">
                    <div class="action-filter-section-title">按剩余时间筛选</div>
                    <div class="action-filter-options action-filter-options--wrap">
                      <button
                        v-for="remainingOption in ACTION_LOG_REMAINING_OPTIONS"
                        :key="remainingOption.id"
                        type="button"
                        class="action-filter-option"
                        :class="{ 'is-active': draftActionLogRemainingFilters.includes(remainingOption.id) }"
                        @click.stop="toggleDraftActionLogRemaining(remainingOption.id)"
                      >
                        <span>{{ remainingOption.label }}</span>
                      </button>
                    </div>
                  </div>
                  <div class="action-filter-section">
                    <div class="action-filter-section-title">按策略筛选</div>
                    <div class="action-filter-stage-groups">
                      <div class="action-filter-stage-group">
                        <div class="action-filter-stage-group-header">
                          <span class="action-filter-stage-group-title">选择方式</span>
                        </div>
                        <div class="action-filter-options action-filter-options--wrap">
                          <button
                            v-for="modeOption in ACTION_LOG_SELECTION_MODE_OPTIONS"
                            :key="modeOption.id"
                            type="button"
                            class="action-filter-option action-filter-option--sm"
                            :class="{ 'is-active': draftActionLogSelectionModeFilters.includes(modeOption.id) }"
                            @click.stop="toggleDraftActionLogSelectionMode(modeOption.id)"
                          >
                            <span>{{ modeOption.label }}</span>
                          </button>
                        </div>
                      </div>
                      <div class="action-filter-stage-group">
                        <div class="action-filter-stage-group-header">
                          <span class="action-filter-stage-group-title">策略类型</span>
                        </div>
                        <div class="action-filter-options action-filter-options--wrap">
                          <button
                            v-for="strategyOption in availableActionLogStrategyTypeOptions"
                            :key="strategyOption.id"
                            type="button"
                            class="action-filter-option action-filter-option--sm"
                            :class="{ 'is-active': draftActionLogStrategyTypeFilters.includes(strategyOption.id) }"
                            @click.stop="toggleDraftActionLogStrategyType(strategyOption.id)"
                          >
                            <span>{{ strategyOption.label }}</span>
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
                <!-- 第二列：阶段、玩家、行动类型、耗时 -->
                <div class="action-filter-column">
                  <div class="action-filter-section">
                    <div class="action-filter-section-title">按阶段筛选</div>
                    <div class="action-filter-stage-groups">
                      <div
                        v-for="stageGroup in ACTION_LOG_STAGE_FILTER_GROUPS"
                        :key="stageGroup.id"
                        class="action-filter-stage-group"
                      >
                        <div class="action-filter-stage-group-header">
                          <span class="action-filter-stage-group-title">{{ stageGroup.label }}</span>
                        </div>
                        <div
                          class="action-filter-options"
                          :class="{ 'is-compact-rounds': stageGroup.id === 'rounds' }"
                        >
                          <button
                            v-for="stageOption in stageGroup.options"
                            :key="stageOption.id"
                            type="button"
                            class="action-filter-option"
                            :class="{
                              'is-active': draftActionLogStageFilters.includes(stageOption.id),
                              'is-round-chip': stageGroup.id === 'rounds'
                            }"
                            @click.stop="toggleDraftActionLogStage(stageOption.id)"
                          >
                            <span>{{ stageOption.label }}</span>
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                  <div class="action-filter-section">
                    <div class="action-filter-section-title">按玩家筛选</div>
                    <div class="action-filter-options action-filter-options--wrap">
                      <button
                        v-for="playerOption in actionLogPlayerFilterOptions"
                        :key="playerOption.id"
                        type="button"
                        class="action-filter-option"
                        :class="{ 'is-active': draftActionLogPlayerFilters.includes(playerOption.id) }"
                        @click.stop="toggleDraftActionLogPlayer(playerOption.id)"
                      >
                        <span
                          class="action-filter-player-dot"
                          :style="{ backgroundColor: playerOption.color }"
                        ></span>
                        <span>{{ playerOption.label }}</span>
                      </button>
                    </div>
                  </div>
                  <div class="action-filter-section">
                    <div class="action-filter-section-title">按行动类型筛选</div>
                    <div class="action-filter-options action-filter-options--wrap">
                      <button
                        v-for="typeOption in ACTION_LOG_TYPE_OPTIONS"
                        :key="typeOption.id"
                        type="button"
                        class="action-filter-option"
                        :class="{ 'is-active': draftActionLogTypeFilters.includes(typeOption.id) }"
                        @click.stop="toggleDraftActionLogType(typeOption.id)"
                      >
                        <span>{{ typeOption.label }}</span>
                      </button>
                    </div>
                  </div>
                  <div class="action-filter-section">
                    <div class="action-filter-section-title">按单行动耗时筛选</div>
                    <div class="action-filter-options action-filter-options--wrap">
                      <button
                        v-for="durationOption in ACTION_LOG_DURATION_OPTIONS"
                        :key="durationOption.id"
                        type="button"
                        class="action-filter-option"
                        :class="{ 'is-active': draftActionLogDurationFilters.includes(durationOption.id) }"
                        @click.stop="toggleDraftActionLogDuration(durationOption.id)"
                      >
                        <span>{{ durationOption.label }}</span>
                      </button>
                    </div>
                  </div>
                </div>
                <!-- 第三列：大类、细类 -->
                <div class="action-filter-column">
                  <div class="action-filter-section">
                    <div class="action-filter-section-title">按行动大类筛选</div>
                    <div class="action-filter-options action-filter-options--wrap">
                      <button
                        v-for="categoryOption in actionLogCategoryFilterOptions"
                        :key="categoryOption.id"
                        type="button"
                        class="action-filter-option"
                        :class="{ 'is-active': draftActionLogCategoryFilters.includes(categoryOption.id) }"
                        @click.stop="toggleDraftActionLogCategory(categoryOption.id)"
                      >
                        <span>{{ categoryOption.label }}</span>
                      </button>
                    </div>
                  </div>
                  <div v-if="draftActionLogCategoryFilters.length > 0" class="action-filter-section">
                    <div class="action-filter-section-title">按行动细类筛选</div>
                    <div class="action-filter-options action-filter-options--wrap">
                      <button
                        v-for="subcategoryOption in actionLogSubcategoryFilterOptions"
                        :key="subcategoryOption.id"
                        type="button"
                        class="action-filter-option"
                        :class="{ 'is-active': draftActionLogSubcategoryFilters.includes(subcategoryOption.id) }"
                        @click.stop="toggleDraftActionLogSubcategory(subcategoryOption.id)"
                      >
                        <span>{{ subcategoryOption.label }}</span>
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <template #footer>
              <div class="action-filter-modal-footer">
                <button type="button" class="action-filter-footer-btn is-ghost" @click.stop="clearDraftActionLogFilters">
                  重置
                </button>
                <button type="button" class="action-filter-footer-btn is-primary" @click.stop="applyActionLogFilters">
                  应用
                </button>
              </div>
            </template>
          </Modal>
          <div id="action-log-content" class="action-log-content">
            <template
              v-for="log in filteredActionLogs"
              :key="log.uid"
            >
              <div
                v-if="log.kind === 'divider'"
                class="action-log-divider"
                :title="buildActionLogEntryTitle(log)"
              >
                <span class="action-log-divider-line"></span>
                <span class="action-log-divider-text">{{ log.description }}</span>
                <span class="action-log-divider-line"></span>
              </div>
              <div
                v-else
                class="action-log-entry"
                :class="[`is-${log.kind}`, `is-${log.actionType}`]"
                :style="getActionLogEntryStyle(log)"
                :title="buildActionLogEntryTitle(log)"
              >
                <span class="action-log-player-dot"></span>
                <span class="action-log-record-id">{{ log.uid }}</span>
                <span class="action-log-description-inline">
                  <span v-if="log.actionCategory" class="action-log-category-inline">{{ log.actionCategory }}</span>
                  <span v-if="log.actionSubcategory" class="action-log-subcategory-wrap">
                    <span class="action-log-separator">·</span>
                    <span class="action-log-subcategory-inline">{{ log.actionSubcategory }}</span>
                  </span>
                  <span v-if="log.actionDetail" class="action-log-detail-wrap">
                    <span class="action-log-separator">·</span>
                    <span class="action-log-detail-inline">{{ log.actionDetail }}</span>
                  </span>
                  <span v-if="!log.actionCategory && !log.actionSubcategory && !log.actionDetail" class="action-log-text">{{ log.description }}</span>
                </span>
              </div>
            </template>
            <div v-if="filteredActionLogs.length === 0" class="panel-empty-state panel-empty-state--log">
              当前筛选条件下还没有记录
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 游戏菜单弹窗 -->
    <Modal
      v-model="gameMenuOpen"
      title="游戏菜单"
      size="small"
      :show-close="true"
      :close-on-overlay="true"
  >
    <div class="game-menu-content">
      <button
        class="menu-modal-btn end-game"
        :class="{ 'confirm-state': confirmState === 'end' }"
        @click="handleEndGame"
      >
        <div class="btn-icon">
          <i class="fas fa-flag-checkered"></i>
        </div>
        <div class="btn-text">
          <span>{{ confirmState === 'end' ? '确认结束' : '结束游戏' }}</span>
          <small>{{ confirmState === 'end' ? '点击确认返回主界面' : '返回主界面' }}</small>
        </div>
      </button>
      <button
        class="menu-modal-btn reset-settings"
        :class="{ 'confirm-state': confirmState === 'reset' }"
        @click="handleResetSettings"
      >
        <div class="btn-icon">
          <i class="fas fa-cog"></i>
        </div>
        <div class="btn-text">
          <span>{{ confirmState === 'reset' ? '确认重置' : '重新初始' }}</span>
          <small>{{ confirmState === 'reset' ? '点击确认返回设置页面' : '返回设置页面，恢复原始设置' }}</small>
        </div>
      </button>
      <button
        class="menu-modal-btn restart-game"
        :class="{ 'confirm-state': confirmState === 'restart' }"
        @click="handleRestartGame"
      >
        <div class="btn-icon">
          <i class="fas fa-redo"></i>
        </div>
        <div class="btn-text">
          <span>{{ confirmState === 'restart' ? '确认重启' : '重新开始' }}</span>
          <small>{{ confirmState === 'restart' ? '点击确认重新开始游戏' : '返回设置页面，使用已随机结果' }}</small>
        </div>
      </button>
    </div>
    </Modal>

    <StrategyPickerModal
      v-model="controlCenterStrategyModalOpen"
      title="选择策略"
      :selected-strategy="selectedControlStrategyId"
      @select="selectControlCenterStrategy"
    />

    <Modal
      v-model="finalScoreModalOpen"
      title="最终比分"
      :show-close="true"
      :close-on-overlay="true"
    >
      <div class="final-score-modal">
        <div v-if="hasFinalScores" class="final-score-table">
          <div class="final-score-grid final-score-header">
            <span>玩家</span>
            <span>总分</span>
            <span>板块</span>
            <span>连锁</span>
            <span>轨道</span>
            <span>资源</span>
          </div>
          <div
            v-for="entry in finalScoreEntries"
            :key="entry.playerId"
            class="final-score-grid final-score-row"
            :class="{ 'is-winner': entry.isWinner }"
          >
            <span class="final-score-player">
              <span class="final-score-player-dot" :style="{ backgroundColor: entry.playerColor }"></span>
              <span>玩家 {{ entry.playerId + 1 }}</span>
            </span>
            <span class="final-score-total">{{ entry.total }}</span>
            <span>{{ entry.board }}</span>
            <span>{{ entry.chain }}</span>
            <span>{{ entry.track }}</span>
            <span>{{ entry.resource }}</span>
          </div>
        </div>
        <div v-else class="final-score-empty">最终比分尚未同步。</div>
      </div>
    </Modal>
    <div
      v-if="entityPreview.visible"
      class="entity-preview"
      :style="getEntityPreviewPositionStyle()"
      @mouseenter="cancelEntityPreviewHide"
      @mouseleave="scheduleEntityPreviewHide"
    >
      <div class="entity-preview-media">
        <div
          class="entity-preview-image"
          :class="{ 'is-inactive': entityPreview.isInactive }"
        >
          <div
            v-for="(layerStyle, index) in entityPreview.imageLayers"
            :key="`entity-preview-layer-${index}`"
            class="entity-preview-image-layer"
            :style="layerStyle"
          ></div>
        </div>
        <div
          v-if="entityPreview.isInactive"
          class="entity-preview-image-overlay"
          aria-hidden="true"
        >
          <span class="entity-preview-status-icon">
            <i class="fas fa-ban"></i>
          </span>
        </div>
      </div>
      <div class="entity-preview-name">{{ entityPreview.name }}</div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, reactive, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useGameStore } from '../stores/game'
import { useTimerStore } from '../stores/timer'
import Modal from '../components/Modal.vue'
import ActionTimer from '../components/ActionTimer.vue'
import PlayerTimer from '../components/PlayerTimer.vue'
import StrategyPickerModal from '../components/StrategyPickerModal.vue'
import { STRATEGY_OPTIONS, SUPPORTED_STRATEGY_IDS } from '../constants/strategies.js'
import {
  getFinalScoringOverlaySpriteStyleByBackendId,
  getRoundBoosterBackSpriteStyleByBackendId,
  getRoundBoosterFrontSpriteStyleByBackendId,
  getRoundScoringBackSpriteStyle,
  getRoundScoringSpriteStyleByBackendId,
  getAbilityTileStyleByBackendId,
  getScienceTileStyleByBackendId
} from '../utils/tileSprites'
import availableActionDisplayGroups from '../../../backend/game/utils/available_action_display_groups.json'

defineOptions({
  name: 'GameView'
})

const router = useRouter()
const gameStore = useGameStore()
const timerStore = useTimerStore()

// ========== 地图配置 ==========
const MAP_CONFIG = {
  rows: 9,  // A-I
  cols: 13, // 1-13
  hexSize: 33.5,
  rowLetters: ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I']
}

// 地形类型映射 - 与 game_panel.html 保持一致
const TERRAIN_TYPES = {
  0: 'water',     // 水域
  1: 'plains',    // 平原
  2: 'swamp',     // 沼泽
  3: 'lake',      // 湖泊
  4: 'forest',    // 森林
  5: 'mountain',  // 山脉
  6: 'wasteland', // 荒地
  7: 'desert'     // 沙漠
}

// 地形颜色映射 - 与 game_panel.html 保持一致
const TERRAIN_COLORS = {
  0: 'transparent',   // 水域 - 透明
  1: '#85491D',       // 平原 - 棕色
  2: '#595959',       // 沼泽 - 黑色
  3: '#35a0d5',       // 湖泊 - 蓝色
  4: '#37af37',       // 森林 - 绿色
  5: '#a1a1a1',       // 山脉 - 灰色
  6: '#cc2828',       // 荒地 - 红色
  7: '#e8e83d'        // 沙漠 - 黄色
}

// 初始地形数据 - 与 game_panel.html 保持一致
const INITIAL_TERRAIN = [
  [4,0,3,2,1,6,5,0,3,2,1,7,0],
  [5,0,0,4,3,4,7,0,4,5,3,0,2],
  [6,3,2,0,5,1,2,0,0,6,0,0,6],
  [7,5,6,0,7,6,0,2,0,0,1,5,4],
  [1,4,1,7,0,0,0,4,5,3,6,7,1],
  [2,0,0,0,3,5,0,7,1,0,2,3,6],
  [3,0,1,2,0,4,1,0,0,0,0,0,0],
  [0,7,3,0,6,2,7,6,2,3,4,2,0],
  [4,5,6,0,7,5,1,3,4,5,6,7,1]
]

function createDefaultMapCellState() {
  return {
    terrain: 0,
    controller: -1,
    building_id: 0,
    is_neutral: false,
    has_annex: false
  }
}

function createDefaultMapGrid() {
  return Array.from({ length: MAP_CONFIG.rows }, () =>
    Array.from({ length: MAP_CONFIG.cols }, () => createDefaultMapCellState())
  )
}

// ========== 玩家数据 ==========
// 动态根据 num_players 初始化，支持 3-5 人局
const players = ref([])
const PLAYER_STATUS_ROWS = [
  [
    { key: 'money', label: '金币', type: 'icon', iconClass: 'fas fa-coins' },
    { key: 'mineral', label: '矿石', type: 'icon', iconClass: 'fas fa-cube' },
    { key: 'mibao', label: '米宝', type: 'icon', iconClass: 'fas fa-user', badgeKey: 'allMeeples' },
    { key: 'bridges', label: '桥梁', type: 'icon', iconClass: 'fas fa-bridge-water' }
  ],
  [
    { key: 'workshop', label: '车间剩余', type: 'building', buildingId: 1 },
    { key: 'guild', label: '工会剩余', type: 'building', buildingId: 2 },
    { key: 'palace', label: '宫殿剩余', type: 'building', buildingId: 3 },
    { key: 'school', label: '学校剩余', type: 'building', buildingId: 4 },
    { key: 'university', label: '大学剩余', type: 'building', buildingId: 5 }
  ],
  [
    { key: 'bank', label: '银行', type: 'icon', iconClass: 'fas fa-university' },
    { key: 'law', label: '法学', type: 'icon', iconClass: 'fas fa-gavel' },
    { key: 'engineering', label: '工程', type: 'icon', iconClass: 'fas fa-cog' },
    { key: 'medical', label: '医学', type: 'icon', iconClass: 'fas fa-heartbeat' }
  ],
  [
    { key: 'magic1', label: '魔力1', type: 'magic', magicValue: '1' },
    { key: 'magic2', label: '魔力2', type: 'magic', magicValue: '2' },
    { key: 'magic3', label: '魔力3', type: 'magic', magicValue: '3' },
    { key: 'cities', label: '城市', type: 'icon', iconClass: 'fas fa-city' },
    { key: 'navigation', label: '航海', type: 'icon', iconClass: 'fas fa-ship' },
    { key: 'shovel', label: '铲力', type: 'icon', iconClass: 'fas fa-digging' }
  ]
]
const ACTION_LOG_LIMIT = 200
const ACTION_LOG_TYPE_OPTIONS = Object.freeze([
  { id: 'normal', label: 'normal' },
  { id: 'immediate', label: 'immediate' }
])
const ACTION_LOG_STAGE_DEFINITIONS = Object.freeze([
  { id: 'setup-choice', label: '初始板块选择阶段', dividerLabel: '初始板块选择阶段' },
  { id: 'setup-build', label: '初始建筑摆放阶段', dividerLabel: '初始建筑摆放阶段' },
  { id: 'setup-effect', label: '初始效果结算阶段', dividerLabel: '初始效果结算阶段' },
  { id: 'round-1', label: '第 1 回合开始', dividerLabel: '第 1 回合开始' },
  { id: 'round-2', label: '第 2 回合开始', dividerLabel: '第 2 回合开始' },
  { id: 'round-3', label: '第 3 回合开始', dividerLabel: '第 3 回合开始' },
  { id: 'round-4', label: '第 4 回合开始', dividerLabel: '第 4 回合开始' },
  { id: 'round-5', label: '第 5 回合开始', dividerLabel: '第 5 回合开始' },
  { id: 'round-6', label: '第 6 回合开始', dividerLabel: '第 6 回合开始' }
])
const ACTION_LOG_STAGE_FILTER_GROUPS = Object.freeze([
  {
    id: 'setup',
    label: '初始阶段',
    options: [
      { id: 'setup-choice', label: '板块选择' },
      { id: 'setup-build', label: '建筑摆放' },
      { id: 'setup-effect', label: '效果结算' }
    ]
  },
  {
    id: 'rounds',
    label: '正式轮次',
    options: Array.from({ length: 6 }, (_, index) => ({
      id: `round-${index + 1}`,
      label: String(index + 1)
    }))
  }
])
const ACTION_LOG_DURATION_OPTIONS = Object.freeze([
  { id: 'lt10', label: '< 10s', max: 10 * 1000 },
  { id: '10to30', label: '10 ~ 30s', min: 10 * 1000, max: 30 * 1000 },
  { id: '30to60', label: '30 ~ 60s', min: 30 * 1000, max: 60 * 1000 },
  { id: '60to180', label: '60 ~ 180s', min: 60 * 1000, max: 180 * 1000 },
  { id: 'gt180', label: '180s +', min: 180 * 1000 }
])
const ACTION_LOG_REMAINING_OPTIONS = Object.freeze([
  { id: '0', label: '0%', min: 0, max: 0 },
  { id: '0to30', label: '0 ~ 30%', min: 0.001, max: 0.3 },
  { id: '30to80', label: '30 ~ 80%', min: 0.3, max: 0.8 },
  { id: '80to100', label: '80% +', min: 0.8, max: 1 }
])
const ACTION_LOG_SELECTION_MODE_OPTIONS = Object.freeze([
  { id: 'player_choice', label: '玩家选择' },
  { id: 'accepted', label: '采纳推荐' },
  { id: 'rejected', label: '拒绝推荐' },
  { id: 'system', label: '系统执行' }
])
const ACTION_LOG_STRATEGY_TYPE_OPTIONS = Object.freeze([
  { id: 'random_pure', label: '随机 · 完全' },
  { id: 'random_fast_action', label: '随机 · 经快速行动优化' },
  { id: 'metric_single_step_best', label: '单步最优' },
  { id: 'ai_llm_reasoning', label: 'AI推理' }
])
const ACTION_LOG_STAGE_MAP = Object.freeze(Object.fromEntries(
  ACTION_LOG_STAGE_DEFINITIONS.map((stage, index) => [stage.id, { ...stage, index }])
))
const PLAYER_CARD_RING_BORDER_RADIUS = 10
const PLAYER_CARD_RING_CORE_STROKE_WIDTH = 3
const PLAYER_CARD_RING_MID_STROKE_WIDTH = 3.6
const PLAYER_CARD_RING_AURA_STROKE_WIDTH = 4
const PLAYER_CARD_RING_SVG_PADDING = 12
const PLANNING_CARD_ACTION_COLOR_NAMES = Object.freeze({
  1: 'brown',
  2: 'black',
  3: 'blue',
  4: 'green',
  5: 'grey',
  6: 'red',
  7: 'yellow'
})
const ACTION_DISPLAY_GROUPS = Object.freeze(
  (Array.isArray(availableActionDisplayGroups?.groups) ? availableActionDisplayGroups.groups : []).map((group) => {
    const actionIdRange = Array.isArray(group?.action_id_range)
      ? group.action_id_range.map((value) => Number(value))
      : [Number.NaN, Number.NaN]
    const items = group?.items && typeof group.items === 'object' ? group.items : {}
    const actionIdOrder = Array.isArray(group?.action_id_order)
      ? group.action_id_order.map((value) => Number(value)).filter(Number.isInteger)
      : Object.keys(items).map((value) => Number(value)).filter(Number.isInteger).sort((left, right) => left - right)

    return {
      groupKey: group?.group_key || '',
      groupLabel: group?.group_label || '未命名分组',
      presentation: group?.presentation || 'grouped_options',
      layoutHint: group?.layout_hint || 'chips_wrap',
      actionIdRange,
      actionIdOrder,
      items
    }
  })
)
const NAMED_LOG_COLORS = {
  default: '#5cbef0',
  blue: '#35a0d5',
  orange: '#f1a61b',
  purple: '#ad32ef',
  pink: '#e57ea9',
  celeste: '#82d8d0',
  red: '#cc2828',
  green: '#37af37',
  yellow: '#e8e83d',
  grey: '#a1a1a1',
  brown: '#85491d',
  black: '#595959',
  white: '#ffffff'
}
const mapState = reactive({
  grid: createDefaultMapGrid()
})
const mapBuildingRenderTokens = new Map()

function createDefaultPlayerDisplayState() {
  return {
    factionId: null,
    faction: '',
    palaceTileId: null,
    isGotPalace: false,
    planningCardId: null,
    planningCard: null,
    score: 20,
    money: 0,
    mineral: 0,
    mibao: 0,
    bank: 0,
    law: 0,
    engineering: 0,
    medical: 0,
    tracks: { bank: 0, law: 0, engineering: 0, medical: 0 },
    magic1: 5,
    magic2: 7,
    magic3: 0,
    cities: 0,
    navigation: 0,
    shovel: 3,
    allMeeples: 7,
    bridges: 3,
    workshop: 9,
    guild: 4,
    palace: 1,
    school: 3,
    university: 1,
    booster_ids: []
  }
}

// 创建默认玩家对象
function createDefaultPlayer(id) {
  return {
    id,
    ...createDefaultPlayerDisplayState()
  }
}

// 初始化玩家列表
function initPlayers(count) {
  const newPlayers = []
  for (let i = 0; i < count; i++) {
    newPlayers.push(createDefaultPlayer(i))
  }
  syncCollapsedPlayers(count)
  players.value = newPlayers
}

// 折叠状态
const collapsedPlayers = reactive({})
const collapsedCards = reactive({ map: false, round: false, tactical: false })

function syncCollapsedPlayers(count) {
  Object.keys(collapsedPlayers).forEach((playerId) => {
    delete collapsedPlayers[playerId]
  })

  for (let i = 0; i < count; i++) {
    collapsedPlayers[i] = true
  }

  expandCurrentActionPlayerCard()
}

// 地形提示弹窗
const terrainTooltipOpen = ref(false)
let terrainTooltipTimeout = null

// 更多菜单
const gameMenuOpen = ref(false)
const confirmState = ref(null) // 'end' | 'reset' | 'restart' | null

// 监听弹窗关闭，重置确认状态
watch(gameMenuOpen, (isOpen) => {
  if (!isOpen) {
    confirmState.value = null
  }
})

// 回合信息 - 默认currentRound为0表示没有高亮任何回合
const currentRound = ref(0)
const roundStates = reactive({
  1: { currentX: -1, actualX: -1, isFlipped: false, finalScoringId: null },
  2: { currentX: -1, actualX: -1, isFlipped: false, finalScoringId: null },
  3: { currentX: -1, actualX: -1, isFlipped: false, finalScoringId: null },
  4: { currentX: -1, actualX: -1, isFlipped: false, finalScoringId: null },
  5: { currentX: -1, actualX: -1, isFlipped: false, finalScoringId: null },
  6: { currentX: -1, actualX: -1, isFlipped: false, finalScoringId: null },
})
const roundScoringBackSpriteStyle = getRoundScoringBackSpriteStyle()

// 助推板块 - 动态初始化，根据实际人数调整 (num_players + 3)
const bonusColumns = ref([])

function createBonusColumnState(x = 0, previousBonus = null) {
  return {
    x,
    isFlipped: previousBonus?.isFlipped ?? false,
    holderMarkId: previousBonus?.holderMarkId ?? null,
    coinCount: previousBonus?.coinCount ?? 0
  }
}

// 初始化助推板块列
function initBonusColumns(count) {
  const columns = []
  for (let i = 0; i < count; i++) {
    columns.push(createBonusColumnState())
  }
  bonusColumns.value = columns
}

// 全局状态
const actionCount = ref(0)
const actions = ref([])
const isAiPlayer = ref(false)
const actionLogs = ref([])
const tacticalLogs = ref([])
const finalScores = ref(null)
const finalScoreModalOpen = ref(false)
const pendingActionId = ref(null)
const recommendedActionId = ref(null)

// 科学能力板块状态
const abilityTilesOrder = ref([])
const scienceTilesOrder = ref([])
const abilityTileOwners = reactive({})
const scienceTileOwners = reactive({})
const scienceTracks = reactive({
  bank: { is_crowned: false, meeples: [-1, -1, -1, -1] },
  law: { is_crowned: false, meeples: [-1, -1, -1, -1] },
  engineering: { is_crowned: false, meeples: [-1, -1, -1, -1] },
  medical: { is_crowned: false, meeples: [-1, -1, -1, -1] }
})
const numPlayers = ref(3)
const scienceAbilityLayoutRef = ref(null)
const leftBoardsStackRef = ref(null)
const cultBoardSectionRef = ref(null)
let scienceAbilityResizeObserver = null
const ABILITY_TILE_INITIAL_SUPPLY = 4

const SCIENCE_ABILITY_LEFT_WIDTH_PER_HEIGHT = Object.freeze({
  3: 850 / (443 + 403),
  4: 850 / (634 + 403),
  5: 850 / (584 + 403)
})
const CULT_BOARD_WIDTH_PER_HEIGHT = 861 / 1248

const SPRITESHEET_URL = new URL('../../assets/images/structures.png', import.meta.url).href
const SPRITE_CELL_WIDTH = 141
const SPRITE_CELL_HEIGHT = 158
const SPRITE_SCALE_MAP_BUILDING = 0.25

const COLOR_TO_SPRITE_COL = {
  0: 7,
  1: 3,
  2: 5,
  3: 2,
  4: 0,
  5: 6,
  6: 4,
  7: 1,
  8: 7
}

const BUILDING_TO_SPRITE_ROW = {
  1: 0,
  2: 1,
  3: 2,
  4: 3,
  5: 4,
  6: 6,
  7: 5,
  8: 7
}

const SPECIAL_BUILDINGS = new Set([6, 7, 8])

const spriteSheet = new Image()
spriteSheet.src = SPRITESHEET_URL
let spriteSheetLoaded = false
spriteSheet.onload = () => { spriteSheetLoaded = true }

// 城市板块精灵图
const CITY_TILES_URL = new URL('../../assets/images/city_tiles.png', import.meta.url).href
const CITY_TILE_COUNT = 7
const CITY_TILE_SCALE = 0.25
const CITY_TILE_ID_TO_INDEX = { 4: 0, 5: 1, 6: 2, 7: 3, 1: 4, 2: 5, 3: 6 }

const cityTilesSheet = new Image()
cityTilesSheet.src = CITY_TILES_URL
let cityTilesSheetLoaded = false
cityTilesSheet.onload = () => { cityTilesSheetLoaded = true }

function drawCityTileSprite(canvas, colIndex, width, height) {
  if (!canvas || !cityTilesSheet.complete || cityTilesSheet.naturalWidth === 0) {
    // 图片未加载完成，添加监听器
    if (canvas && !cityTilesSheet.complete) {
      const onLoad = () => {
        drawCityTileSprite(canvas, colIndex, width, height)
        cityTilesSheet.removeEventListener('load', onLoad)
      }
      cityTilesSheet.addEventListener('load', onLoad)
    }
    return
  }

  const ctx = canvas.getContext('2d')
  if (!ctx) return

  const dpr = window.devicePixelRatio || 1
  canvas.width = Math.round(width * dpr)
  canvas.height = Math.round(height * dpr)
  canvas.style.width = width + 'px'
  canvas.style.height = height + 'px'

  ctx.imageSmoothingEnabled = true
  ctx.imageSmoothingQuality = 'high'
  ctx.clearRect(0, 0, canvas.width, canvas.height)

  const tileWidth = cityTilesSheet.naturalWidth / CITY_TILE_COUNT
  const tileHeight = cityTilesSheet.naturalHeight
  const sx = colIndex * tileWidth
  const sy = 0

  ctx.save()
  ctx.scale(dpr, dpr)
  ctx.drawImage(cityTilesSheet, sx, sy, tileWidth, tileHeight, 0, 0, width, height)
  ctx.restore()
}

function drawSprite(canvas, sx, sy, sWidth, sHeight, cssWidth, cssHeight) {
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  if (!ctx) return

  let targetWidth = cssWidth
  let targetHeight = cssHeight
  if (!targetWidth || !targetHeight) {
    const rect = canvas.getBoundingClientRect()
    targetWidth = rect.width
    targetHeight = rect.height
  }
  if (!targetWidth || !targetHeight) {
    requestAnimationFrame(() => drawSprite(canvas, sx, sy, sWidth, sHeight, cssWidth, cssHeight))
    return
  }

  const dpr = window.devicePixelRatio || 1
  canvas.width = Math.round(targetWidth * dpr)
  canvas.height = Math.round(targetHeight * dpr)
  if (cssWidth && cssHeight) {
    canvas.style.width = cssWidth + 'px'
    canvas.style.height = cssHeight + 'px'
  }

  ctx.imageSmoothingEnabled = true
  ctx.imageSmoothingQuality = 'high'
  ctx.clearRect(0, 0, canvas.width, canvas.height)

  const doDraw = () => {
    ctx.save()
    ctx.scale(dpr, dpr)
    ctx.drawImage(spriteSheet, sx, sy, sWidth, sHeight, 0, 0, targetWidth, targetHeight)
    ctx.restore()
  }

  if (spriteSheet.complete && spriteSheet.naturalWidth !== 0) {
    doDraw()
  } else {
    const onLoad = () => {
      doDraw()
      spriteSheet.removeEventListener('load', onLoad)
    }
    spriteSheet.addEventListener('load', onLoad)
  }
}

function drawSpriteCell(canvas, col, row, width, height) {
  drawSprite(canvas, col * SPRITE_CELL_WIDTH, row * SPRITE_CELL_HEIGHT, SPRITE_CELL_WIDTH, SPRITE_CELL_HEIGHT, width, height)
}

const recommendedActionStrategyId = ref('')
const controlCenterPendingMode = ref('')
const actionLogFilterModalOpen = ref(false)
const controlCenterStrategyModalOpen = ref(false)
const selectedControlStrategyId = ref(STRATEGY_OPTIONS[0]?.id ?? 'random_pure')
const appliedActionLogPlayerFilters = ref([])
const appliedActionLogTypeFilters = ref([])
const appliedActionLogStageFilters = ref([])
const appliedActionLogCategoryFilters = ref([])
const appliedActionLogSubcategoryFilters = ref([])
const appliedActionLogDurationFilters = ref([])
const appliedActionLogRemainingFilters = ref([])
const appliedActionLogSelectionModeFilters = ref([])
const appliedActionLogStrategyTypeFilters = ref([])
const appliedActionLogActionIdFilter = ref('')
const appliedActionLogUidFilter = ref('')
const draftActionLogPlayerFilters = ref([])
const draftActionLogTypeFilters = ref([])
const draftActionLogStageFilters = ref([])
const draftActionLogCategoryFilters = ref([])
const draftActionLogSubcategoryFilters = ref([])
const draftActionLogDurationFilters = ref([])
const draftActionLogRemainingFilters = ref([])
const draftActionLogSelectionModeFilters = ref([])
const draftActionLogStrategyTypeFilters = ref([])
const draftActionLogActionIdFilter = ref('')
const draftActionLogUidFilter = ref('')
const pendingSelectionModes = ref([])
const stateVersion = ref(0)
const gameMeta = reactive({
  round: 0,
  num_players: 3,
  current_player_id: -1,
  action_type: '',
  is_game_over: false,
  setup_choice_is_completed: false,
  setup_build_is_completed: false,
  current_player_order: [],
  pass_order: []
})
const globalStatus = computed(() => buildGlobalStatusFromMeta())
const groupedActionCards = computed(() => buildGroupedActionCards(actions.value))
const actionContentRef = ref(null)
const actionMeasureRef = ref(null)
const roundInfoContainerRef = ref(null)
const isActionOverflowMode = ref(false)
const expandedActionGroupKey = ref(null)
const actionMeasureWidth = ref(0)
const actionGroupBodyHeights = reactive({})
const roundInfoLayout = reactive({
  leftWidthPx: null
})
const ROUND_INFO_COLUMN_GAP_PX = 24
const ROUND_SCORING_GRID_GAP_PX = 10
const ROUND_BONUS_GRID_GAP_PX = 8
const ROUND_BONUS_COLUMN_HORIZONTAL_PADDING_PX = 12
const ROUND_SCORING_TILE_HEIGHT_PER_WIDTH = 134 / 232
const ROUND_BOOSTER_TILE_HEIGHT_PER_WIDTH = 8 / 3
const actionMeasureStyle = computed(() => (
  actionMeasureWidth.value > 0
    ? { width: `${actionMeasureWidth.value}px` }
    : undefined
))
const roundInfoLeftColumnStyle = computed(() => (
  Number.isFinite(roundInfoLayout.leftWidthPx) && roundInfoLayout.leftWidthPx > 0
    ? {
        flexBasis: `${roundInfoLayout.leftWidthPx}px`,
        width: `${roundInfoLayout.leftWidthPx}px`
      }
    : undefined
))
let actionOverflowMeasurementFrame = 0
let actionContentResizeObserver = null
let roundInfoResizeObserver = null
let playerCardResizeObserver = null
let playerCardResizeFrame = 0
let playerCardResizeTimeout = 0
const actionGroupBodyInnerRefs = new Map()
const playerCardRefs = new Map()
const playerCardSizes = reactive({})
const playerCardRingGeometries = reactive({})
const playerCardTransitionStates = reactive({})
const pendingPlayerCardSizeUpdates = new Map()
const actionLogPlayerFilterOptions = computed(() => players.value.map((player) => ({
  id: player.id,
  label: `玩家 ${player.id + 1}`,
  color: getActionLogPlayerColor(player.id)
})))
const actionLogCategoryFilterOptions = computed(() => {
  const categories = new Set()
  renderedActionLogs.value.forEach((entry) => {
    if (entry.kind === 'action' && entry.actionCategory) {
      categories.add(entry.actionCategory)
    }
  })
  return Array.from(categories).sort().map((category) => ({
    id: category,
    label: category
  }))
})
const actionLogSubcategoryFilterOptions = computed(() => {
  const subcategories = new Set()
  renderedActionLogs.value.forEach((entry) => {
    if (entry.kind === 'action' && entry.actionSubcategory) {
      if (draftActionLogCategoryFilters.value.length === 0 || draftActionLogCategoryFilters.value.includes(entry.actionCategory)) {
        subcategories.add(entry.actionSubcategory)
      }
    }
  })
  return Array.from(subcategories).sort().map((subcategory) => ({
    id: subcategory,
    label: subcategory
  }))
})
const renderedActionLogs = computed(() => Array.isArray(actionLogs.value) ? actionLogs.value : [])
const availableActionLogStrategyTypeOptions = computed(() => {
  const usedStrategyIds = new Set(
    actionLogs.value
      .filter((entry) => entry.kind !== 'divider' && entry.selectionStrategy)
      .map((entry) => entry.selectionStrategy)
  )
  return ACTION_LOG_STRATEGY_TYPE_OPTIONS.filter((option) => usedStrategyIds.has(option.id))
})
const normalizedAppliedActionLogActionIdFilter = computed(() => normalizeActionLogSearchValue(appliedActionLogActionIdFilter.value))
const normalizedAppliedActionLogUidFilter = computed(() => normalizeActionLogSearchValue(appliedActionLogUidFilter.value))
const hasActiveActionLogFilters = computed(() => (
  appliedActionLogPlayerFilters.value.length > 0
  || appliedActionLogTypeFilters.value.length > 0
  || appliedActionLogStageFilters.value.length > 0
  || appliedActionLogCategoryFilters.value.length > 0
  || appliedActionLogSubcategoryFilters.value.length > 0
  || appliedActionLogDurationFilters.value.length > 0
  || appliedActionLogRemainingFilters.value.length > 0
  || appliedActionLogSelectionModeFilters.value.length > 0
  || appliedActionLogStrategyTypeFilters.value.length > 0
  || normalizedAppliedActionLogActionIdFilter.value.length > 0
  || normalizedAppliedActionLogUidFilter.value.length > 0
))
const actionLogActiveFilterCount = computed(() => (
  appliedActionLogPlayerFilters.value.length
  + appliedActionLogTypeFilters.value.length
  + appliedActionLogStageFilters.value.length
  + appliedActionLogCategoryFilters.value.length
  + appliedActionLogSubcategoryFilters.value.length
  + appliedActionLogDurationFilters.value.length
  + appliedActionLogRemainingFilters.value.length
  + appliedActionLogSelectionModeFilters.value.length
  + appliedActionLogStrategyTypeFilters.value.length
  + (normalizedAppliedActionLogActionIdFilter.value.length > 0 ? 1 : 0)
  + (normalizedAppliedActionLogUidFilter.value.length > 0 ? 1 : 0)
))
const filteredActionLogs = computed(() => {
  const actionIdFilter = normalizedAppliedActionLogActionIdFilter.value
  const uidFilter = normalizedAppliedActionLogUidFilter.value

  return renderedActionLogs.value.filter((entry) => {
    if (entry.kind === 'divider') {
      return appliedActionLogStageFilters.value.length === 0
        || appliedActionLogStageFilters.value.includes(entry.stageKey)
    }

    if (appliedActionLogPlayerFilters.value.length > 0 && !appliedActionLogPlayerFilters.value.includes(entry.playerId)) {
      return false
    }

    if (appliedActionLogTypeFilters.value.length > 0 && !appliedActionLogTypeFilters.value.includes(entry.actionType)) {
      return false
    }

    if (appliedActionLogStageFilters.value.length > 0 && !appliedActionLogStageFilters.value.includes(entry.stageKey)) {
      return false
    }

    if (appliedActionLogCategoryFilters.value.length > 0 && !appliedActionLogCategoryFilters.value.includes(entry.actionCategory)) {
      return false
    }

    if (appliedActionLogSubcategoryFilters.value.length > 0 && !appliedActionLogSubcategoryFilters.value.includes(entry.actionSubcategory)) {
      return false
    }

    if (actionIdFilter.length > 0 && entry.actionIdText !== actionIdFilter) {
      return false
    }

    if (uidFilter.length > 0 && !entry.uid.toLowerCase().includes(uidFilter)) {
      return false
    }

    // 单行动耗时筛选
    if (appliedActionLogDurationFilters.value.length > 0) {
      const durationMs = entry.durationMs || 0
      const matches = appliedActionLogDurationFilters.value.some((filterId) => {
        const option = ACTION_LOG_DURATION_OPTIONS.find((opt) => opt.id === filterId)
        if (!option) return false
        if (filterId === 'lt10') {
          // <10s包含0秒（四舍五入后小于1秒的情况）
          return durationMs <= option.max
        }
        if (filterId === 'gt180') {
          return durationMs >= option.min
        }
        return durationMs > option.min && durationMs <= option.max
      })
      if (!matches) return false
    }

    // 剩余时间筛选（基于百分比）
    if (appliedActionLogRemainingFilters.value.length > 0) {
      const remainingPct = getRemainingPercentage(entry)
      const matches = appliedActionLogRemainingFilters.value.some((filterId) => {
        const option = ACTION_LOG_REMAINING_OPTIONS.find((opt) => opt.id === filterId)
        if (!option) return false
        if (filterId === '0') {
          return remainingPct === 0
        }
        return remainingPct > option.min * 100 && remainingPct <= option.max * 100
      })
      if (!matches) return false
    }

    // 选择方式筛选
    if (appliedActionLogSelectionModeFilters.value.length > 0) {
      const selectionMode = entry.selectionMode || (entry.selectionSource === 'system' ? 'system' : 'player_choice')
      if (!appliedActionLogSelectionModeFilters.value.includes(selectionMode)) {
        return false
      }
    }

    // 策略类型筛选
    if (appliedActionLogStrategyTypeFilters.value.length > 0) {
      const strategyType = entry.selectionStrategy || ''
      if (!appliedActionLogStrategyTypeFilters.value.includes(strategyType)) {
        return false
      }
    }

    return true
  })
})

const activePlayerItems = computed(() => {
  const activeOrder = gameMeta.current_player_order || []
  return activeOrder
    .map((playerId) => players.value.find((p) => p.id === playerId))
    .filter(Boolean)
})

const passedPlayerItems = computed(() => {
  const passOrder = gameMeta.pass_order || []
  return passOrder
    .map((playerId) => players.value.find((p) => p.id === playerId))
    .filter(Boolean)
})

const hasPassedPlayers = computed(() => (gameMeta.pass_order || []).length > 0)

const currentActionPlayerId = computed(() => {
  if (gameMeta.is_game_over) {
    return null
  }

  return normalizeActionLogPlayerId(gameMeta.current_player_id)
})
watch(currentActionPlayerId, (playerId) => {
  // 当前玩家变化时不再自动展开卡片，保持用户手动控制折叠状态
  // expandCurrentActionPlayerCard(playerId)
}, { immediate: false })
watch(
  [currentActionPlayerId, () => gameMeta.action_type, () => gameMeta.is_game_over],
  () => {
    clearRecommendedAction()
  }
)

// 监听 pass_order 变化，自动折叠已pass玩家的卡片
watch(() => gameMeta.pass_order, (newPassOrder, oldPassOrder) => {
  const oldSet = new Set(oldPassOrder || [])

  // 新pass的玩家，自动折叠
  newPassOrder?.forEach((playerId) => {
    if (!oldSet.has(playerId)) {
      collapsedPlayers[playerId] = true
    }
  })

  // 回合刷新时，pass_order 清空，所有玩家回到活跃列表
  // 不需要特别处理展开，保持用户当前折叠状态即可
}, { deep: true })
const currentActionOwnerLabel = computed(() => {
  if (gameMeta.is_game_over) {
    return '游戏结束'
  }

  return currentActionPlayerId.value === null ? '等待后端' : getActionLogPlayerLabel(currentActionPlayerId.value)
})
const currentActionPlayerColor = computed(() => {
  if (gameMeta.is_game_over) {
    return '#94a3b8'
  }

  return currentActionPlayerId.value === null ? '#64748b' : getCurrentActionOwnerColor(currentActionPlayerId.value)
})
const currentActionModeLabel = computed(() => {
  if (gameMeta.is_game_over) {
    return '终局'
  }

  if (!gameMeta.action_type) {
    return '待定'
  }

  return formatActionModeLabel(gameMeta.action_type)
})
const selectedControlStrategyOption = computed(() => (
  STRATEGY_OPTIONS.find((strategy) => strategy.id === selectedControlStrategyId.value)
  || STRATEGY_OPTIONS[0]
  || {
    id: 'random_pure',
    label: '随机 · 完全'
  }
))
const selectedControlStrategySummaryLabel = computed(() => (
  selectedControlStrategyOption.value.label
))

const TRACK_TYPES = ['bank', 'law', 'engineering', 'medical']
const TRACK_CENTERS = { bank: 15.25, law: 37.75, engineering: 60.75, medical: 83.5 }
const TRACK_LEVEL_TOPS = [
  78.5, // 0
  71.5, // 1
  66.4, // 2
  59.2, // 3
  54.2, // 4
  46.5, // 5
  41.5, // 6
  34.5, // 7
  27.5, // 8
  22.5, // 9
  18.0, // 10
  13.5, // 11
  6.0   // 12
]

const allTrackMarkers = computed(() => {
  const markers = []
  for (const type of TRACK_TYPES) {
    const centerX = TRACK_CENTERS[type]
    const levelMap = new Map()
    for (const player of players.value) {
      const level = Number(player.tracks?.[type] ?? 0)
      if (!levelMap.has(level)) levelMap.set(level, [])
      levelMap.get(level).push(player.id)
    }
    for (const [level, playerIds] of levelMap) {
      const topPct = TRACK_LEVEL_TOPS[Math.min(Math.max(level, 0), 12)]
      const visiblePlayerIds = playerIds.filter(pid => getTileOwnerMarkIdByPlayerId(pid))
      const count = visiblePlayerIds.length
      visiblePlayerIds.forEach((pid, idx) => {
        const offsetPct = (idx - (count - 1) / 2) * 3.5
        const markId = getTileOwnerMarkIdByPlayerId(pid)
        markers.push({
          key: `tower-${type}-${pid}`,
          markId,
          style: {
            left: `${centerX + offsetPct}%`,
            top: `${topPct}%`,
            zIndex: 10 + level
          }
        })
      })
    }
  }
  return markers
})

const allBaseMeepleMarkers = computed(() => {
  const markers = []
  for (const type of TRACK_TYPES) {
    const centerX = TRACK_CENTERS[type]
    const meeples = scienceTracks[type]?.meeples ?? [-1, -1, -1, -1]
    const rowTops = [85.5, 94.5]
    const colOffsets = [-5.45, 5.45]
    for (let i = 0; i < 4; i++) {
      const pid = Number(meeples[i])
      if (pid < 0) continue
      const row = i < 2 ? 0 : 1
      const col = i % 2
      const markId = getTileOwnerMarkIdByPlayerId(pid)
      if (!markId) continue
      markers.push({
        key: `base-${type}-${i}-${pid}`,
        markId,
        style: {
          left: `${centerX + colOffsets[col]}%`,
          top: `${rowTops[row]}%`,
          zIndex: 5
        }
      })
    }
  }
  return markers
})

const hasRecommendedAction = computed(() => {
  const normalizedRecommendedActionId = normalizeAvailableActionId(recommendedActionId.value)
  if (normalizedRecommendedActionId === null) {
    return false
  }

  return actions.value.some((action) => normalizeAvailableActionId(action?.id) === normalizedRecommendedActionId)
})
const recommendedControlStrategyOption = computed(() => (
  STRATEGY_OPTIONS.find((strategy) => strategy.id === recommendedActionStrategyId.value)
  || null
))
const recommendedActionOption = computed(() => {
  const normalizedRecommendedActionId = normalizeAvailableActionId(recommendedActionId.value)
  if (normalizedRecommendedActionId === null) {
    return null
  }

  for (const group of groupedActionCards.value) {
    const matchedOption = Array.isArray(group.options)
      ? group.options.find((option) => option.id === normalizedRecommendedActionId)
      : null

    if (matchedOption) {
      return matchedOption
    }
  }

  return null
})
const recommendedActionChipLabel = computed(() => (
  recommendedActionOption.value?.label || '已推荐'
))
const recommendedActionChipTitle = computed(() => {
  if (!hasRecommendedAction.value) {
    return ''
  }

  const strategyLabel = recommendedControlStrategyOption.value?.description
    ? `${recommendedControlStrategyOption.value.label} / ${recommendedControlStrategyOption.value.description}`
    : (recommendedControlStrategyOption.value?.label || '当前策略')
  const actionDescription = recommendedActionOption.value?.description
    || recommendedActionOption.value?.label
    || `行动 ${recommendedActionId.value}`

  return `${strategyLabel} 推荐：${actionDescription}`
})
const recommendedActionIconClass = computed(() => (
  getControlCenterStrategyIconClass(recommendedActionStrategyId.value || selectedControlStrategyId.value)
))
const controlCenterCanRun = computed(() => (
  !gameMeta.is_game_over
  && currentActionPlayerId.value !== null
  && actions.value.length > 0
))
const actionSubtitle = computed(() => {
  if (gameMeta.is_game_over) {
    return '本局已结束'
  }

  return `当前为 ${currentActionOwnerLabel.value} 的 ${currentActionModeLabel.value} 行动阶段`
})
const finalScoreEntries = computed(() => {
  if (!finalScores.value || typeof finalScores.value !== 'object') {
    return []
  }

  const entries = Object.entries(finalScores.value).map(([playerId, score]) => {
    const normalizedPlayerId = normalizeActionLogPlayerId(playerId)
    if (normalizedPlayerId === null || !score || typeof score !== 'object') {
      return null
    }

    return {
      playerId: normalizedPlayerId,
      playerColor: getCurrentActionOwnerColor(normalizedPlayerId),
      total: normalizeFinalScoreValue(score.total),
      board: normalizeFinalScoreValue(score.board),
      chain: normalizeFinalScoreValue(score.chain),
      track: normalizeFinalScoreValue(score.track),
      resource: normalizeFinalScoreValue(score.resource)
    }
  }).filter(Boolean).sort((left, right) => left.playerId - right.playerId)

  const highestTotal = entries.reduce((currentMax, entry) => Math.max(currentMax, entry.total), Number.NEGATIVE_INFINITY)

  return entries.map((entry) => ({
    ...entry,
    isWinner: Number.isFinite(highestTotal) && entry.total === highestTotal
  }))
})
const hasFinalScores = computed(() => finalScoreEntries.value.length > 0)
const actionEmptyStateMessage = computed(() => {
  if (gameMeta.is_game_over) {
    return '本局已结束'
  }

  return '等待后端推送新的可选行动。'
})

// 规划卡与派系映射
const planningCardIdToName = {
  1: '平原', 2: '沼泽', 3: '湖泊', 4: '森林', 5: '山脉', 6: '荒地', 7: '沙漠'
}

const planningCardIdToColor = {
  1: '#85491d',
  2: '#6b6b6b',
  3: '#35a0d5',
  4: '#37af37',
  5: '#a1a1a1',
  6: '#cc2828',
  7: '#e8e83d'
}

const planningCardBackendToImageMap = [6, 2, 4, 1, 5, 3, 0]
const planningCardBackgroundPositions = [0, 16.6667, 33.3333, 50, 66.6667, 83.3333, 100]

const factionIdToName = {
  1: '神佑者', 2: '猫人', 3: '哥布林', 4: '幻术师', 5: '发明家',
  6: '蜥蜴人', 7: '鼹鼠', 8: '僧侣', 9: '航海家', 10: '奥马尔',
  11: '哲学家', 12: '通灵师'
}

const factionBackendToImageMap = [11, 4, 7, 0, 8, 9, 5, 10, 1, 6, 2, 3]
const factionTileBackgroundPositions = [0, 9.0909, 18.1818, 27.2727, 36.3636, 45.4545, 54.5455, 63.6364, 72.7273, 81.8182, 90.9091, 100]
const factionTileBackgroundSize = '1200% 100%'
const factionTileCount = 12
const factionTilePixelWidth = 592
const factionTilePixelHeight = 338
const factionSquareCropRightShiftPx = 24
const factionSheetPixelWidth = factionTilePixelWidth * factionTileCount
const factionSquareCropInsetPx = ((factionTilePixelWidth - factionTilePixelHeight) / 2) + factionSquareCropRightShiftPx
const factionSquareCropBackgroundSize = `${((factionSheetPixelWidth / factionTilePixelHeight) * 100).toFixed(4)}% 100%`
const factionSquareCropPositions = Array.from({ length: factionTileCount }, (_, index) => Number(
  (((index * factionTilePixelWidth + factionSquareCropInsetPx) / (factionSheetPixelWidth - factionTilePixelHeight)) * 100).toFixed(4)
))
const palaceTileBackgroundPositions = [
  0, 5.8824, 11.7647, 17.6471, 23.5294, 29.4118, 35.2941, 41.1765,
  47.0588, 52.9412, 58.8235, 64.7059, 70.5882, 76.4706, 82.3529, 88.2353, 94.1176, 100
]
const palaceTileBackgroundSize = '1800% 100%'
const palaceTileAspectRatio = 142 / 74
const factionTileAspectRatio = factionTilePixelWidth / factionTilePixelHeight
const planningCardPreviewAspectRatio = 118 / 187
const entityPreviewDelayMs = 300
const roundEntityPreviewDelayMs = 500
const entityPreviewOffsetPx = 12
const entityPreviewViewportPaddingPx = 12
const entityPreviewPaddingPx = 8
const entityPreviewNameHeightPx = 30
const factionPreviewCardWidthPx = 320
const factionPreviewImageHeightPx = Math.round(factionPreviewCardWidthPx / factionTileAspectRatio)
const palacePreviewCardWidthPx = 280
const palacePreviewImageHeightPx = Math.round(palacePreviewCardWidthPx / palaceTileAspectRatio)
const planningPreviewCardWidthPx = 176
const planningPreviewImageHeightPx = Math.round(planningPreviewCardWidthPx / planningCardPreviewAspectRatio)
const roundScoringPreviewCardWidthPx = 174
const roundScoringPreviewImageHeightPx = Math.round(roundScoringPreviewCardWidthPx * (134 / 232))
const roundBoosterPreviewCardWidthPx = 111
const roundBoosterPreviewImageHeightPx = Math.round(roundBoosterPreviewCardWidthPx * (8 / 3))
const abilityTilePreviewCardWidthPx = 116
const abilityTilePreviewImageHeightPx = 112
const scienceTilePreviewCardWidthPx = 140
const scienceTilePreviewImageHeightPx = 90
const entityPreview = reactive({
  visible: false,
  name: '',
  imageLayers: [],
  isInactive: false,
  imageHeight: 0,
  panelWidth: 0,
  top: 0,
  left: 0
})
let entityPreviewTimer = null
let entityPreviewHideTimer = null

// 建筑ID到建筑类型名称的映射
const buildingIdToType = {
  0: null,      // 无建筑
  1: 'workshop', // 车间
  2: 'guild',    // 工会
  3: 'palace',   // 宫殿
  4: 'school',   // 学校
  5: 'university', // 大学
  6: 'tower',    // 塔楼
  7: 'monument', // 纪念碑
  8: 'annex'     // 侧楼
}

function setPlayerPlanningCard(player, planningCardId) {
  const normalizedId = Number(planningCardId)
  const resolvedId = Number.isInteger(normalizedId) && normalizedId > 0 ? normalizedId : null
  player.planningCardId = resolvedId
  player.planningCard = resolvedId ? planningCardIdToName[resolvedId] || null : null
  refreshActionLogPlayerColors(player.id)
}

function normalizePlanningCardId(planningCardId) {
  const normalizedId = Number(planningCardId)
  return Number.isInteger(normalizedId) && normalizedId >= 1 && normalizedId <= 7 ? normalizedId : null
}

function setPlayerPalaceTile(player, palaceTileId) {
  const normalizedId = Number(palaceTileId)
  player.palaceTileId = Number.isInteger(normalizedId) && normalizedId > 0 ? normalizedId : null
}

function setPlayerPalaceActivation(player, isGotPalace) {
  player.isGotPalace = isGotPalace === true || isGotPalace === 1 || isGotPalace === '1' || isGotPalace === 'true'
}

function setPlayerFaction(player, factionId) {
  const normalizedId = Number(factionId)
  const resolvedId = Number.isInteger(normalizedId) && normalizedId > 0 ? normalizedId : null
  player.factionId = resolvedId
  player.faction = resolvedId ? factionIdToName[resolvedId] || '' : ''
}

function getPlanningCardColor(planningCardId) {
  return planningCardId ? planningCardIdToColor[planningCardId] || 'transparent' : 'transparent'
}

function drawBonusHolderMark(canvas, markId) {
  if (!markId || !canvas) return
  const col = COLOR_TO_SPRITE_COL[Number(markId)] ?? 7
  drawSpriteCell(canvas, col, 6)
}

function drawScienceTileOwnerMark(canvas, markId) {
  if (!markId || !canvas) return
  const col = COLOR_TO_SPRITE_COL[Number(markId)] ?? 7
  drawSpriteCell(canvas, col, 6, 48, 56)
}

function drawAbilityTileOwnerMark(canvas, markId) {
  if (!markId || !canvas) return
  const col = COLOR_TO_SPRITE_COL[Number(markId)] ?? 7
  drawSpriteCell(canvas, col, 6, 40, 48)
}

function drawTrackTowerMarker(canvas, markId) {
  if (!markId || !canvas) return
  const col = COLOR_TO_SPRITE_COL[Number(markId)] ?? 7
  drawSpriteCell(canvas, col, 6)
}

function drawTrackBaseMeeple(canvas, markId) {
  if (!markId || !canvas) return
  const col = COLOR_TO_SPRITE_COL[Number(markId)] ?? 7
  drawSpriteCell(canvas, col, 5)
}

function drawPlayerBuildingIcon(canvas, player, buildingId) {
  if (!canvas) return
  const colorId = player?.planningCardId ?? 0
  const col = SPECIAL_BUILDINGS.has(Number(buildingId)) ? 7 : (COLOR_TO_SPRITE_COL[colorId] ?? 7)
  const row = BUILDING_TO_SPRITE_ROW[Number(buildingId)] ?? 0

  const rect = canvas.getBoundingClientRect()
  const boxW = rect.width
  const boxH = rect.height
  if (!boxW || !boxH) return

  const spriteRatio = SPRITE_CELL_WIDTH / SPRITE_CELL_HEIGHT
  const boxRatio = boxW / boxH
  let drawW, drawH, offsetX, offsetY
  if (boxRatio > spriteRatio) {
    drawH = boxH
    drawW = boxH * spriteRatio
    offsetX = (boxW - drawW) / 2
    offsetY = 0
  } else {
    drawW = boxW
    drawH = boxW / spriteRatio
    offsetX = 0
    offsetY = (boxH - drawH) / 2
  }

  const dpr = window.devicePixelRatio || 1
  canvas.width = Math.round(boxW * dpr)
  canvas.height = Math.round(boxH * dpr)
  const ctx = canvas.getContext('2d')
  if (!ctx) return
  ctx.imageSmoothingEnabled = true
  ctx.imageSmoothingQuality = 'high'
  ctx.clearRect(0, 0, canvas.width, canvas.height)

  const doDraw = () => {
    ctx.save()
    ctx.scale(dpr, dpr)
    ctx.drawImage(spriteSheet, col * SPRITE_CELL_WIDTH, row * SPRITE_CELL_HEIGHT, SPRITE_CELL_WIDTH, SPRITE_CELL_HEIGHT, offsetX, offsetY, drawW, drawH)
    ctx.restore()
  }

  if (spriteSheet.complete && spriteSheet.naturalWidth !== 0) {
    doDraw()
  } else {
    const onLoad = () => {
      doDraw()
      spriteSheet.removeEventListener('load', onLoad)
    }
    spriteSheet.addEventListener('load', onLoad)
  }
}

function normalizeTileOwnerPlayerIds(ownerList) {
  if (!Array.isArray(ownerList)) {
    return []
  }

  return ownerList
    .map((playerId) => Number(playerId))
    .filter((playerId) => Number.isInteger(playerId) && playerId >= 0)
}

function normalizeTileOwnerMap(ownerMap, orderedTileIds = []) {
  const normalizedMap = {}

  if (ownerMap && typeof ownerMap === 'object') {
    Object.entries(ownerMap).forEach(([tileId, ownerList]) => {
      const normalizedTileId = Number(tileId)
      if (!Number.isInteger(normalizedTileId) || normalizedTileId <= 0) {
        return
      }

      normalizedMap[normalizedTileId] = normalizeTileOwnerPlayerIds(ownerList)
    })
  }

  if (Array.isArray(orderedTileIds)) {
    orderedTileIds.forEach((tileId) => {
      const normalizedTileId = Number(tileId)
      if (!Number.isInteger(normalizedTileId) || normalizedTileId <= 0) {
        return
      }

      if (!Object.prototype.hasOwnProperty.call(normalizedMap, normalizedTileId)) {
        normalizedMap[normalizedTileId] = []
      }
    })
  }

  return normalizedMap
}

function replaceTileOwnerMap(targetMap, ownerMap, orderedTileIds = []) {
  const normalizedMap = normalizeTileOwnerMap(ownerMap, orderedTileIds)

  Object.keys(targetMap).forEach((tileId) => {
    delete targetMap[tileId]
  })

  Object.entries(normalizedMap).forEach(([tileId, ownerList]) => {
    targetMap[tileId] = ownerList
  })
}

function applyTileOwnerMapChange(targetMap, remainingKeys, value, changeType, orderedTileIds = []) {
  if (!remainingKeys.length) {
    replaceTileOwnerMap(targetMap, value, orderedTileIds)
    return
  }

  const tileId = Number.parseInt(remainingKeys[0], 10)
  if (!Number.isInteger(tileId) || tileId <= 0) {
    return
  }

  if (remainingKeys.length === 1) {
    targetMap[tileId] = changeType === 'removed' ? [] : normalizeTileOwnerPlayerIds(value)
    return
  }

  const ownerIndex = Number.parseInt(remainingKeys[1], 10)
  if (!Number.isInteger(ownerIndex) || ownerIndex < 0) {
    return
  }

  const nextOwnerList = Array.isArray(targetMap[tileId]) ? [...targetMap[tileId]] : []
  if (changeType === 'removed' || value === null || value === undefined) {
    nextOwnerList.splice(ownerIndex, 1)
  } else {
    nextOwnerList[ownerIndex] = Number(value)
  }

  targetMap[tileId] = normalizeTileOwnerPlayerIds(nextOwnerList)
}

function applyDisplayBoardState(displayBoard) {
  replaceTileOwnerMap(
    abilityTileOwners,
    displayBoard?.ability_tile_owners,
    abilityTilesOrder.value
  )
  replaceTileOwnerMap(
    scienceTileOwners,
    displayBoard?.science_tile_owners,
    scienceTilesOrder.value
  )
  if (displayBoard?.science_tracks) {
    for (const type of ['bank', 'law', 'engineering', 'medical']) {
      const trackData = displayBoard.science_tracks[type]
      if (trackData) {
        scienceTracks[type].is_crowned = trackData.is_crowned ?? false
        scienceTracks[type].meeples = Array.isArray(trackData.meeples)
          ? [...trackData.meeples]
          : [-1, -1, -1, -1]
      }
    }
  }
}

function getTileOwnerPlayerIds(ownerMap, tileId) {
  const normalizedTileId = Number(tileId)
  if (!Number.isInteger(normalizedTileId) || normalizedTileId <= 0) {
    return []
  }

  return normalizeTileOwnerPlayerIds(ownerMap[normalizedTileId] ?? ownerMap[String(normalizedTileId)])
}

function getTileOwnerMarkIdByPlayerId(playerId) {
  const normalizedPlayerId = Number(playerId)
  if (!Number.isInteger(normalizedPlayerId) || normalizedPlayerId < 0) {
    return null
  }

  const planningCardId = normalizePlanningCardId(players.value[normalizedPlayerId]?.planningCardId)
  return planningCardId ?? null
}

function getScienceTileOwnerMarkId(tileId) {
  const [playerId] = getTileOwnerPlayerIds(scienceTileOwners, tileId)
  return getTileOwnerMarkIdByPlayerId(playerId)
}

function getAbilityTileOwnerMarkIds(tileId) {
  return getTileOwnerPlayerIds(abilityTileOwners, tileId)
    .slice(0, ABILITY_TILE_INITIAL_SUPPLY)
    .map((playerId) => getTileOwnerMarkIdByPlayerId(playerId))
    .filter((markId) => Number.isInteger(markId) && markId > 0)
}

function getAbilityTileRemainingCount(tileId) {
  return Math.max(ABILITY_TILE_INITIAL_SUPPLY - getTileOwnerPlayerIds(abilityTileOwners, tileId).length, 0)
}

function getFactionBadgeStyle(factionId) {
  if (!factionId) {
    return {}
  }

  const imageIndex = factionBackendToImageMap[factionId - 1]
  return {
    backgroundImage: 'url(/assets/images/faction_tiles.jpg)',
    backgroundSize: factionSquareCropBackgroundSize,
    backgroundPosition: `${factionSquareCropPositions[imageIndex]}% 50%`
  }
}

function getFactionPreviewStyle(factionId) {
  if (!factionId) {
    return {}
  }

  const imageIndex = factionBackendToImageMap[factionId - 1]
  return {
    backgroundImage: 'url(/assets/images/faction_tiles.jpg)',
    backgroundSize: factionTileBackgroundSize,
    backgroundPosition: `${factionTileBackgroundPositions[imageIndex]}% 50%`
  }
}

function getPalacePreviewStyle(palaceTileId) {
  if (!palaceTileId) {
    return {}
  }

  const imageIndex = Number(palaceTileId) - 1
  if (!Number.isInteger(imageIndex) || imageIndex < 0 || imageIndex >= 16) {
    return {}
  }

  return {
    backgroundImage: 'url(/assets/images/palace_tiles.jpg)',
    backgroundSize: palaceTileBackgroundSize,
    backgroundPosition: `${palaceTileBackgroundPositions[imageIndex]}% 50%`
  }
}

function getPlanningCardPreviewStyle(planningCardId) {
  if (!planningCardId) {
    return {}
  }

  const imageIndex = planningCardBackendToImageMap[planningCardId - 1]
  return {
    backgroundImage: 'url(/assets/images/planning_cards.jpg)',
    backgroundSize: '700% 100%',
    backgroundPosition: `${planningCardBackgroundPositions[imageIndex]}% 50%`
  }
}

function getEntityPreviewPositionStyle() {
  return {
    top: `${entityPreview.top}px`,
    left: `${entityPreview.left}px`,
    width: `${entityPreview.panelWidth}px`,
    '--entity-preview-image-height': `${entityPreview.imageHeight}px`
  }
}

function clearEntityPreviewTimer() {
  if (entityPreviewTimer !== null) {
    clearTimeout(entityPreviewTimer)
    entityPreviewTimer = null
  }
}

function clearEntityPreviewHideTimer() {
  if (entityPreviewHideTimer !== null) {
    clearTimeout(entityPreviewHideTimer)
    entityPreviewHideTimer = null
  }
}

function hideEntityPreview() {
  clearEntityPreviewTimer()
  clearEntityPreviewHideTimer()
  entityPreview.visible = false
  entityPreview.name = ''
  entityPreview.imageLayers = []
  entityPreview.isInactive = false
  entityPreview.imageHeight = 0
  entityPreview.panelWidth = 0
}

function hasRenderablePreviewLayer(style) {
  return Boolean(style && typeof style === 'object' && Object.keys(style).length > 0)
}

function resolveEntityPreviewPosition(rect, panelWidth, panelHeight, placement = 'side') {
  const maxLeft = Math.max(entityPreviewViewportPaddingPx, window.innerWidth - panelWidth - entityPreviewViewportPaddingPx)
  const maxTop = Math.max(entityPreviewViewportPaddingPx, window.innerHeight - panelHeight - entityPreviewViewportPaddingPx)

  if (placement === 'top') {
    const preferredLeft = rect.left + (rect.width - panelWidth) / 2
    const left = Math.min(Math.max(entityPreviewViewportPaddingPx, preferredLeft), maxLeft)
    const preferredTop = rect.top - entityPreviewOffsetPx - panelHeight
    const fallbackTop = rect.bottom + entityPreviewOffsetPx
    const top = preferredTop >= entityPreviewViewportPaddingPx
      ? preferredTop
      : Math.min(Math.max(entityPreviewViewportPaddingPx, fallbackTop), maxTop)
    return { left, top }
  }

  let left = rect.right + entityPreviewOffsetPx
  if (left + panelWidth > window.innerWidth - entityPreviewViewportPaddingPx) {
    left = rect.left - entityPreviewOffsetPx - panelWidth
  }

  const top = Math.min(
    Math.max(entityPreviewViewportPaddingPx, rect.top + (rect.height - panelHeight) / 2),
    maxTop
  )

  return {
    left: Math.max(entityPreviewViewportPaddingPx, left),
    top
  }
}

function showEntityPreview({
  name,
  imageStyle,
  imageLayers = [],
  isInactive = false,
  cardWidth,
  imageHeight,
  anchorElement,
  placement = 'side'
}) {
  if (!anchorElement?.isConnected) {
    return
  }

  const normalizedLayers = (Array.isArray(imageLayers) ? imageLayers : [])
    .filter(hasRenderablePreviewLayer)
  if (normalizedLayers.length === 0 && hasRenderablePreviewLayer(imageStyle)) {
    normalizedLayers.push(imageStyle)
  }
  if (normalizedLayers.length === 0) {
    return
  }

  const panelWidth = cardWidth + entityPreviewPaddingPx * 2
  const panelHeight = imageHeight + entityPreviewNameHeightPx + entityPreviewPaddingPx * 2
  const rect = anchorElement.getBoundingClientRect()
  const { left, top } = resolveEntityPreviewPosition(rect, panelWidth, panelHeight, placement)

  entityPreview.name = name
  entityPreview.imageLayers = normalizedLayers
  entityPreview.isInactive = Boolean(isInactive)
  entityPreview.imageHeight = imageHeight
  entityPreview.panelWidth = panelWidth
  entityPreview.left = left
  entityPreview.top = top
  entityPreview.visible = true
}

function queueEntityPreview(config) {
  clearEntityPreviewHideTimer()
  clearEntityPreviewTimer()
  const delayMs = Number.isFinite(config?.delayMs) ? Math.max(0, config.delayMs) : entityPreviewDelayMs
  entityPreviewTimer = setTimeout(() => {
    entityPreviewTimer = null
    showEntityPreview(config)
  }, delayMs)
}

function handlePlanningCardMouseEnter(planningCardId, planningCardName, event) {
  if (!planningCardId) {
    return
  }

  queueEntityPreview({
    name: planningCardName || planningCardIdToName[planningCardId] || '',
    imageStyle: getPlanningCardPreviewStyle(planningCardId),
    cardWidth: planningPreviewCardWidthPx,
    imageHeight: planningPreviewImageHeightPx,
    anchorElement: event?.currentTarget
  })
}

function handlePlanningCardMouseLeave() {
  clearEntityPreviewTimer()
  scheduleEntityPreviewHide()
}

function handlePalaceTileMouseEnter(palaceTileId, isGotPalace, event) {
  if (!palaceTileId) {
    return
  }

  const isInactive = !isGotPalace
  queueEntityPreview({
    name: isInactive ? `${palaceTileId}号宫殿板块 · 未激活` : `${palaceTileId}号宫殿板块`,
    imageStyle: getPalacePreviewStyle(palaceTileId),
    isInactive,
    cardWidth: palacePreviewCardWidthPx,
    imageHeight: palacePreviewImageHeightPx,
    anchorElement: event?.currentTarget
  })
}

function handlePalaceTileMouseLeave() {
  clearEntityPreviewTimer()
  scheduleEntityPreviewHide()
}

function handleFactionBadgeMouseEnter(factionId, factionName, event) {
  if (!factionId) {
    return
  }

  queueEntityPreview({
    name: factionName || factionIdToName[factionId] || '',
    imageStyle: getFactionPreviewStyle(factionId),
    cardWidth: factionPreviewCardWidthPx,
    imageHeight: factionPreviewImageHeightPx,
    anchorElement: event?.currentTarget
  })
}

function handleFactionBadgeMouseLeave() {
  clearEntityPreviewTimer()
  scheduleEntityPreviewHide()
}

function getRoundScoringPreviewLayers(round) {
  const normalizedRound = Number(round)
  const roundState = roundStates[normalizedRound]
  if (!Number.isInteger(normalizedRound) || normalizedRound < 1 || normalizedRound > 6 || !roundState) {
    return []
  }

  const layers = []
  const baseLayer = getRoundScoringSpriteStyleByBackendId(roundState.currentX)
  if (!hasRenderablePreviewLayer(baseLayer)) {
    return []
  }

  layers.push(baseLayer)

  if (normalizedRound === 6) {
    const overlayLayer = getFinalScoringOverlaySpriteStyleByBackendId(roundState.finalScoringId)
    if (hasRenderablePreviewLayer(overlayLayer)) {
      layers.push(overlayLayer)
    }
  }

  return layers
}

function getRoundScoringAriaLabel(round) {
  return getRoundScoringPreviewLayers(round).length > 0 ? `预览第 ${round} 回合计分板` : undefined
}

function handleRoundScoringMouseEnter(round, event) {
  const imageLayers = getRoundScoringPreviewLayers(round)
  if (imageLayers.length === 0) {
    return
  }

  queueEntityPreview({
    name: `第 ${round} 回合`,
    imageLayers,
    cardWidth: roundScoringPreviewCardWidthPx,
    imageHeight: roundScoringPreviewImageHeightPx,
    anchorElement: event?.currentTarget,
    placement: 'top',
    delayMs: roundEntityPreviewDelayMs
  })
}

function handleRoundScoringMouseLeave() {
  clearEntityPreviewTimer()
  scheduleEntityPreviewHide()
}

function handleRoundBoosterMouseEnter(bonus, event) {
  if (!bonus?.x) {
    return
  }

  const imageLayer = getRoundBoosterFrontSpriteStyleByBackendId(bonus.x)
  if (!hasRenderablePreviewLayer(imageLayer)) {
    return
  }

  queueEntityPreview({
    name: `回合助推板 ${bonus.x}`,
    imageLayers: [imageLayer],
    cardWidth: roundBoosterPreviewCardWidthPx,
    imageHeight: roundBoosterPreviewImageHeightPx,
    anchorElement: event?.currentTarget,
    placement: 'top',
    delayMs: roundEntityPreviewDelayMs
  })
}

function handleRoundBoosterMouseLeave() {
  clearEntityPreviewTimer()
  scheduleEntityPreviewHide()
}

function handleAbilityTileMouseEnter(tileId, event) {
  if (!tileId) {
    return
  }

  const imageLayer = getAbilityTileStyleByBackendId(tileId)
  if (!hasRenderablePreviewLayer(imageLayer)) {
    return
  }

  queueEntityPreview({
    name: `能力板块 ${tileId}`,
    imageLayers: [imageLayer],
    cardWidth: abilityTilePreviewCardWidthPx,
    imageHeight: abilityTilePreviewImageHeightPx,
    anchorElement: event?.currentTarget,
    placement: 'top',
    delayMs: roundEntityPreviewDelayMs
  })
}

function handleAbilityTileMouseLeave() {
  clearEntityPreviewTimer()
  scheduleEntityPreviewHide()
}

function handleScienceTileMouseEnter(tileId, event) {
  if (!tileId) {
    return
  }

  const imageLayer = getScienceTileStyleByBackendId(tileId)
  if (!hasRenderablePreviewLayer(imageLayer)) {
    return
  }

  queueEntityPreview({
    name: `科学板块 ${tileId}`,
    imageLayers: [imageLayer],
    cardWidth: scienceTilePreviewCardWidthPx,
    imageHeight: scienceTilePreviewImageHeightPx,
    anchorElement: event?.currentTarget,
    placement: 'top',
    delayMs: roundEntityPreviewDelayMs
  })
}

function handleScienceTileMouseLeave() {
  clearEntityPreviewTimer()
  scheduleEntityPreviewHide()
}

function cancelEntityPreviewHide() {
  clearEntityPreviewHideTimer()
}

function scheduleEntityPreviewHide() {
  clearEntityPreviewHideTimer()
  if (!entityPreview.visible) {
    return
  }

  entityPreviewHideTimer = setTimeout(() => {
    entityPreviewHideTimer = null
    hideEntityPreview()
  }, 120)
}

function buildGlobalStatusFromMeta() {
  if (gameMeta.is_game_over) {
    return '游戏结束'
  }

  const normalizedRound = Number(gameMeta.round)
  if (!Number.isInteger(normalizedRound) || normalizedRound <= 0) {
    if (gameMeta.setup_build_is_completed) {
      return '初始效果结算阶段'
    }

    if (gameMeta.setup_choice_is_completed) {
      return '初始建筑摆放阶段'
    }

    return '初始板块选择阶段'
  }

  return `第 ${normalizedRound} 回合`
}

function getActionLogStageDefinition(stageKey) {
  return ACTION_LOG_STAGE_MAP[stageKey] || ACTION_LOG_STAGE_MAP['setup-choice']
}

function getCurrentActionLogStageKey(metaLike = gameMeta) {
  const normalizedRound = Number(metaLike?.round)
  if (Number.isInteger(normalizedRound) && normalizedRound >= 1 && normalizedRound <= 6) {
    return `round-${normalizedRound}`
  }

  if (metaLike?.setup_build_is_completed) {
    return 'setup-effect'
  }

  if (metaLike?.setup_choice_is_completed) {
    return 'setup-build'
  }

  return 'setup-choice'
}

function getCurrentActionLogStage(metaLike = gameMeta) {
  return getActionLogStageDefinition(getCurrentActionLogStageKey(metaLike))
}

function normalizeActionLogSearchValue(value) {
  return typeof value === 'string' ? value.trim().toLowerCase() : ''
}

function resetActionLogHistory() {
  actionLogs.value = []
  systemRecordSequence = 0
}

function syncRoundScoringProgress(roundValue) {
  const normalizedRound = Number(roundValue)
  const currentActiveRound = Number.isInteger(normalizedRound) && normalizedRound >= 1 && normalizedRound <= 6
    ? normalizedRound
    : 0
  const endedRoundCount = Number.isInteger(normalizedRound)
    ? Math.max(0, Math.min(normalizedRound - 1, 6))
    : 0

  currentRound.value = currentActiveRound
  for (let round = 1; round <= 6; round++) {
    roundStates[round].isFlipped = round <= endedRoundCount
  }
}

function syncRoundInfoFromMeta() {
  syncRoundScoringProgress(gameMeta.round)
}

function applyMetaState(metaPatch) {
  if (!metaPatch || typeof metaPatch !== 'object') return

  if (Object.prototype.hasOwnProperty.call(metaPatch, 'is_game_over') && metaPatch.is_game_over === false) {
    finalScoreModalOpen.value = false
    finalScores.value = null
  }

  Object.assign(gameMeta, metaPatch)
  syncRoundInfoFromMeta()
}

function updateStateVersion(version) {
  const normalizedVersion = Number(version)
  if (Number.isInteger(normalizedVersion) && normalizedVersion >= 0) {
    stateVersion.value = normalizedVersion
  }
}

function normalizeAvailableActionId(value) {
  const normalizedActionId = Number(value)
  return Number.isInteger(normalizedActionId) ? normalizedActionId : null
}

function findActionDisplayGroupDefinition(actionId) {
  return ACTION_DISPLAY_GROUPS.find((group) => {
    const [start, end] = group.actionIdRange
    return Number.isInteger(start)
      && Number.isInteger(end)
      && actionId >= start
      && actionId <= end
      && Object.prototype.hasOwnProperty.call(group.items, String(actionId))
  }) || null
}

function findActionDisplayItemDefinition(actionId) {
  const groupDefinition = findActionDisplayGroupDefinition(actionId)
  if (!groupDefinition) {
    return { groupDefinition: null, itemDefinition: null }
  }

  return {
    groupDefinition,
    itemDefinition: groupDefinition.items[String(actionId)] || null
  }
}

function getActionOptionColor(actionId, itemDefinition, fallbackColor = 'default') {
  if (fallbackColor && fallbackColor !== 'default') {
    return fallbackColor
  }

  if (itemDefinition?.source_action === 'select_planning_card') {
    return PLANNING_CARD_ACTION_COLOR_NAMES[Number(itemDefinition.source_args)] || 'default'
  }

  return 'default'
}

function shouldKeepActionGroupSingleRow(options, layoutHint) {
  if (layoutHint !== 'chips_wrap' || !Array.isArray(options)) {
    return false
  }

  if (options.length < 2 || options.length > 3) {
    return false
  }

  return options.every((option) => {
    const labelLength = String(option?.label || '').trim().length
    const detailLength = String(option?.detail || '').trim().length

    return labelLength <= 6 && detailLength <= 4
  })
}

function normalizeAction(action, idx) {
  const normalizedActionId = normalizeAvailableActionId(action?.action_id ?? action?.id ?? action)
  const { itemDefinition } = Number.isInteger(normalizedActionId)
    ? findActionDisplayItemDefinition(normalizedActionId)
    : { itemDefinition: null }

  return {
    id: Number.isInteger(normalizedActionId) ? normalizedActionId : idx,
    description: action?.description ?? action?.text ?? itemDefinition?.description ?? '',
    color: action?.color || 'default'
  }
}

function createFallbackActionGroup(action, index) {
  const actionId = normalizeAvailableActionId(action?.id)
  const resolvedLabel = actionId === null ? '未分组行动' : `动作 ${actionId}`
  const resolvedDescription = action?.description || resolvedLabel

  return {
    key: `ungrouped-${actionId ?? index}`,
    groupKey: `ungrouped-${actionId ?? index}`,
    groupLabel: '其他可选行动',
    layoutHint: 'single_button',
    firstIndex: index,
    hasDetail: false,
    hasVerboseDetail: false,
    hasPendingSelection: pendingActionId.value === actionId,
    hasRecommendedOption: recommendedActionId.value === actionId,
    options: [
      {
        key: `ungrouped-option-${actionId ?? index}`,
        id: actionId,
        label: resolvedLabel,
        detail: '',
        description: resolvedDescription,
        color: action?.color || 'default'
      }
    ]
  }
}

function buildGroupedActionCards(actionList) {
  if (!Array.isArray(actionList) || actionList.length === 0) {
    return []
  }

  const normalizedRecommendedActionId = normalizeAvailableActionId(recommendedActionId.value)
  const groupedCards = new Map()
  const fallbackCards = []

  actionList.forEach((action, index) => {
    const actionId = normalizeAvailableActionId(action?.id)
    if (actionId === null) {
      fallbackCards.push(createFallbackActionGroup(action, index))
      return
    }

    const { groupDefinition, itemDefinition } = findActionDisplayItemDefinition(actionId)
    if (!groupDefinition || !itemDefinition) {
      fallbackCards.push(createFallbackActionGroup(action, index))
      return
    }

    if (!groupedCards.has(groupDefinition.groupKey)) {
      groupedCards.set(groupDefinition.groupKey, {
        key: groupDefinition.groupKey,
        groupKey: groupDefinition.groupKey,
        groupLabel: groupDefinition.groupLabel,
        layoutHint: groupDefinition.layoutHint,
        firstIndex: index,
        actionIdOrder: groupDefinition.actionIdOrder,
        optionsById: new Map()
      })
    }

    const groupCard = groupedCards.get(groupDefinition.groupKey)
    if (groupCard.optionsById.has(actionId)) {
      return
    }

    groupCard.optionsById.set(actionId, {
      key: `${groupDefinition.groupKey}-${actionId}`,
      id: actionId,
      label: itemDefinition.minor_label || String(actionId),
      detail: itemDefinition.minor_detail || '',
      description: itemDefinition.description || action.description || '',
      color: getActionOptionColor(actionId, itemDefinition, action.color)
    })
  })

  const normalizedGroupedCards = Array.from(groupedCards.values()).map((groupCard) => {
    const options = groupCard.actionIdOrder
      .filter((actionId) => groupCard.optionsById.has(actionId))
      .map((actionId) => groupCard.optionsById.get(actionId))

    const hasDetail = options.some((option) => Boolean(option.detail))
    const hasVerboseDetail = options.some((option) => typeof option.detail === 'string' && option.detail.length >= 14)
    const fixedColumnCount = shouldKeepActionGroupSingleRow(options, groupCard.layoutHint) ? options.length : null

    return {
      key: groupCard.key,
      groupKey: groupCard.groupKey,
      groupLabel: groupCard.groupLabel,
      layoutHint: groupCard.layoutHint,
      firstIndex: groupCard.firstIndex,
      fixedColumnCount,
      hasDetail,
      hasVerboseDetail,
      hasPendingSelection: options.some((option) => pendingActionId.value === option.id),
      hasRecommendedOption: options.some((option) => option.id === normalizedRecommendedActionId),
      options
    }
  })

  return [...normalizedGroupedCards, ...fallbackCards]
    .filter((groupCard) => Array.isArray(groupCard.options) && groupCard.options.length > 0)
    .sort((left, right) => left.firstIndex - right.firstIndex)
}

function isActionGroupExpanded(groupKey) {
  return !isActionOverflowMode.value || expandedActionGroupKey.value === groupKey
}

function setActionGroupBodyInnerRef(groupKey, element) {
  if (element && typeof element.scrollHeight === 'number') {
    actionGroupBodyInnerRefs.set(groupKey, element)
    return
  }

  actionGroupBodyInnerRefs.delete(groupKey)
}

function refreshActionGroupBodyHeights() {
  const activeGroupKeys = new Set(groupedActionCards.value.map((group) => group.groupKey))

  Object.keys(actionGroupBodyHeights).forEach((groupKey) => {
    if (!activeGroupKeys.has(groupKey)) {
      delete actionGroupBodyHeights[groupKey]
    }
  })

  groupedActionCards.value.forEach((group) => {
    const bodyInner = actionGroupBodyInnerRefs.get(group.groupKey)
    if (bodyInner) {
      actionGroupBodyHeights[group.groupKey] = Math.ceil(bodyInner.scrollHeight)
    }
  })
}

function getActionGroupBodyStyle(groupKey) {
  const height = actionGroupBodyHeights[groupKey]
  if (!Number.isFinite(height) || height <= 0) {
    return undefined
  }

  return {
    '--action-group-body-height': `${height}px`
  }
}

function toggleActionGroup(groupKey) {
  if (!isActionOverflowMode.value) {
    return
  }

  expandedActionGroupKey.value = expandedActionGroupKey.value === groupKey ? null : groupKey

  nextTick(() => {
    refreshActionGroupBodyHeights()
    const actionContent = actionContentRef.value
    if (actionContent) {
      actionContent.scrollTop = 0
    }
  })
}

// 预留接口：一键折叠/展开所有行动组
// 当前未调用，如需恢复手风琴模式可启用此函数
function toggleAllActionGroups() {
  isActionOverflowMode.value = !isActionOverflowMode.value
  if (!isActionOverflowMode.value) {
    expandedActionGroupKey.value = null
  }
  nextTick(() => {
    refreshActionGroupBodyHeights()
    const actionContent = actionContentRef.value
    if (actionContent) {
      actionContent.scrollTop = 0
    }
  })
}

function cancelActionOverflowMeasurement() {
  if (actionOverflowMeasurementFrame !== 0) {
    window.cancelAnimationFrame(actionOverflowMeasurementFrame)
    actionOverflowMeasurementFrame = 0
  }
}

async function measureActionOverflow(resetExpanded = false) {
  await nextTick()
  refreshActionGroupBodyHeights()

  if (groupedActionCards.value.length === 0) {
    isActionOverflowMode.value = false
    expandedActionGroupKey.value = null
    actionMeasureWidth.value = 0
    return
  }

  const actionContent = actionContentRef.value
  if (!actionContent) {
    return
  }

  const nextMeasureWidth = actionContent.clientWidth
  if (nextMeasureWidth <= 0) {
    return
  }

  if (actionMeasureWidth.value !== nextMeasureWidth) {
    actionMeasureWidth.value = nextMeasureWidth
    await nextTick()
    refreshActionGroupBodyHeights()
  }

  const actionMeasure = actionMeasureRef.value
  if (!actionMeasure) {
    return
  }

  const availableHeight = actionContent.clientHeight
  const expandedHeight = actionMeasure.scrollHeight
  const shouldUseOverflowMode = expandedHeight - availableHeight > 2
  const wasOverflowMode = isActionOverflowMode.value

  isActionOverflowMode.value = shouldUseOverflowMode

  if (!shouldUseOverflowMode) {
    expandedActionGroupKey.value = null
    actionContent.scrollTop = 0
    return
  }

  const expandedGroupStillExists = groupedActionCards.value.some((group) => group.groupKey === expandedActionGroupKey.value)
  if (resetExpanded || !wasOverflowMode || !expandedGroupStillExists) {
    expandedActionGroupKey.value = null
    actionContent.scrollTop = 0
  }
}

function scheduleActionOverflowMeasurement(options = {}) {
  const { resetExpanded = false } = options

  cancelActionOverflowMeasurement()
  actionOverflowMeasurementFrame = window.requestAnimationFrame(() => {
    actionOverflowMeasurementFrame = 0
    void measureActionOverflow(resetExpanded)
  })
}

function setupActionContentResizeObserver() {
  if (typeof ResizeObserver === 'undefined' || actionContentResizeObserver) {
    return
  }

  const actionContent = actionContentRef.value
  if (!actionContent) {
    return
  }

  actionContentResizeObserver = new ResizeObserver(() => {
    scheduleActionOverflowMeasurement()
  })
  actionContentResizeObserver.observe(actionContent)
}

function updateRoundInfoLayout() {
  const roundInfoContainer = roundInfoContainerRef.value
  const bonusCount = bonusColumns.value.length

  if (!roundInfoContainer || bonusCount <= 0) {
    roundInfoLayout.leftWidthPx = null
    return
  }

  const containerWidth = roundInfoContainer.clientWidth
  if (!Number.isFinite(containerWidth) || containerWidth <= 0) {
    roundInfoLayout.leftWidthPx = null
    return
  }

  const leftHeightSlope = (3 * ROUND_SCORING_TILE_HEIGHT_PER_WIDTH) / 2
  const leftHeightConstant = ROUND_SCORING_GRID_GAP_PX * (2 - leftHeightSlope)
  const rightHeightSlope = ROUND_BOOSTER_TILE_HEIGHT_PER_WIDTH / bonusCount
  const rightReservedWidth = ROUND_INFO_COLUMN_GAP_PX
    + ROUND_BONUS_COLUMN_HORIZONTAL_PADDING_PX
    + ROUND_BONUS_GRID_GAP_PX * Math.max(0, bonusCount - 1)
  const calculatedLeftWidth = (
    rightHeightSlope * (containerWidth - rightReservedWidth) - leftHeightConstant
  ) / (leftHeightSlope + rightHeightSlope)

  if (!Number.isFinite(calculatedLeftWidth) || calculatedLeftWidth <= 0) {
    roundInfoLayout.leftWidthPx = null
    return
  }

  const minimumRightCardWidth = 28
  const maxLeftWidth = containerWidth
    - ROUND_INFO_COLUMN_GAP_PX
    - ROUND_BONUS_COLUMN_HORIZONTAL_PADDING_PX
    - ROUND_BONUS_GRID_GAP_PX * Math.max(0, bonusCount - 1)
    - minimumRightCardWidth * bonusCount
  if (!Number.isFinite(maxLeftWidth) || maxLeftWidth <= 0) {
    roundInfoLayout.leftWidthPx = null
    return
  }
  const minimumLeftWidth = Math.min(120, maxLeftWidth)
  const normalizedLeftWidth = Math.max(
    minimumLeftWidth,
    Math.min(calculatedLeftWidth, maxLeftWidth)
  )

  roundInfoLayout.leftWidthPx = normalizedLeftWidth
}

function scheduleRoundInfoLayoutUpdate() {
  nextTick(() => {
    updateRoundInfoLayout()
  })
}

function resetScienceAbilityLayoutStyles() {
  const layout = scienceAbilityLayoutRef.value
  const stack = leftBoardsStackRef.value
  const cultSection = cultBoardSectionRef.value
  if (layout) {
    layout.style.maxHeight = ''
  }
  if (stack) {
    stack.style.height = ''
    stack.style.width = ''
    stack.style.maxWidth = ''
  }
  if (cultSection) {
    cultSection.style.height = ''
    cultSection.style.width = ''
  }
}

function getFlexGapPx(element) {
  if (!element || typeof window === 'undefined') return 0

  const styles = window.getComputedStyle(element)
  return Number.parseFloat(styles.columnGap || styles.gap || '0') || 0
}

function updateScienceAbilityLayout() {
  if (collapsedCards.tactical) return

  const layout = scienceAbilityLayoutRef.value
  const stack = leftBoardsStackRef.value
  const cultSection = cultBoardSectionRef.value
  if (!layout || !stack || !cultSection) return

  resetScienceAbilityLayoutStyles()

  // 基于父容器 .science-ability-status 的可用高度计算，避免 layout 自身被内容撑大
  const statusEl = layout.parentElement
  const statusStyles = statusEl ? window.getComputedStyle(statusEl) : null
  const paddingTop = statusStyles ? (Number.parseFloat(statusStyles.paddingTop) || 0) : 0
  const paddingBottom = statusStyles ? (Number.parseFloat(statusStyles.paddingBottom) || 0) : 0
  const availableHeight = statusEl ? (statusEl.clientHeight - paddingTop - paddingBottom) : layout.clientHeight
  const availableWidth = layout.clientWidth
  if (!Number.isFinite(availableHeight) || availableHeight <= 0 || !Number.isFinite(availableWidth) || availableWidth <= 0) return

  const leftRatio = SCIENCE_ABILITY_LEFT_WIDTH_PER_HEIGHT[numPlayers.value] ?? SCIENCE_ABILITY_LEFT_WIDTH_PER_HEIGHT[3]
  const cultRatio = CULT_BOARD_WIDTH_PER_HEIGHT
  const gap = getFlexGapPx(layout)
  if (!Number.isFinite(leftRatio) || leftRatio <= 0 || !Number.isFinite(cultRatio) || cultRatio <= 0 || availableWidth <= gap) {
    return
  }

  const commonHeight = Math.min(
    availableHeight,
    (availableWidth - gap) / (leftRatio + cultRatio)
  )
  if (!Number.isFinite(commonHeight) || commonHeight <= 0) {
    return
  }

  const leftWidth = commonHeight * leftRatio
  const cultWidth = commonHeight * cultRatio
  // 锁定 layout 自身的 max-height，确保内容不会溢出父容器
  layout.style.maxHeight = `${availableHeight}px`
  stack.style.height = `${commonHeight}px`
  stack.style.width = `${leftWidth}px`
  stack.style.maxWidth = `${leftWidth}px`
  cultSection.style.height = `${commonHeight}px`
  cultSection.style.width = `${cultWidth}px`
}

function setupScienceAbilityResizeObserver() {
  if (typeof ResizeObserver === 'undefined' || scienceAbilityResizeObserver) {
    return
  }

  const layout = scienceAbilityLayoutRef.value
  if (!layout) {
    return
  }

  scienceAbilityResizeObserver = new ResizeObserver(() => {
    updateScienceAbilityLayout()
  })
  scienceAbilityResizeObserver.observe(layout)
}

function setupRoundInfoResizeObserver() {
  if (typeof ResizeObserver === 'undefined' || roundInfoResizeObserver) {
    return
  }

  const roundInfoContainer = roundInfoContainerRef.value
  if (!roundInfoContainer) {
    return
  }

  roundInfoResizeObserver = new ResizeObserver(() => {
    updateRoundInfoLayout()
  })
  roundInfoResizeObserver.observe(roundInfoContainer)
}

function updatePlayerCardSize(playerId, width, height) {
  const normalizedPlayerId = normalizeActionLogPlayerId(playerId)
  if (normalizedPlayerId === null) {
    return
  }

  const normalizedWidth = Math.max(Math.round(Number(width) || 0), 0)
  const normalizedHeight = Math.max(Math.round(Number(height) || 0), 0)
  const previousSize = playerCardSizes[normalizedPlayerId]
  if (previousSize?.width === normalizedWidth && previousSize?.height === normalizedHeight) {
    return
  }

  playerCardSizes[normalizedPlayerId] = {
    width: normalizedWidth,
    height: normalizedHeight
  }
  playerCardRingGeometries[normalizedPlayerId] = createPlayerCardRingGeometry(normalizedWidth, normalizedHeight)
}

function flushPlayerCardSizeUpdates() {
  if (playerCardResizeTimeout !== 0) {
    window.clearTimeout(playerCardResizeTimeout)
    playerCardResizeTimeout = 0
  }

  pendingPlayerCardSizeUpdates.forEach((size, playerId) => {
    updatePlayerCardSize(playerId, size.width, size.height)
  })
  pendingPlayerCardSizeUpdates.clear()
  playerCardResizeFrame = 0
}

function hasTransitioningPendingPlayerCardUpdate() {
  for (const playerId of pendingPlayerCardSizeUpdates.keys()) {
    if (playerCardTransitionStates[playerId]) {
      return true
    }
  }

  return false
}

function schedulePendingPlayerCardSizeFlush() {
  if (playerCardResizeFrame !== 0 || playerCardResizeTimeout !== 0) {
    return
  }

  if (hasTransitioningPendingPlayerCardUpdate()) {
    playerCardResizeTimeout = window.setTimeout(() => {
      playerCardResizeTimeout = 0
      flushPlayerCardSizeUpdates()
    }, 34)
    return
  }

  playerCardResizeFrame = window.requestAnimationFrame(() => {
    flushPlayerCardSizeUpdates()
  })
}

function schedulePlayerCardSizeUpdate(playerId, width, height) {
  const normalizedPlayerId = normalizeActionLogPlayerId(playerId)
  if (normalizedPlayerId === null) {
    return
  }

  pendingPlayerCardSizeUpdates.set(normalizedPlayerId, { width, height })
  schedulePendingPlayerCardSizeFlush()
}

function cancelPlayerCardSizeUpdates() {
  if (playerCardResizeFrame !== 0) {
    window.cancelAnimationFrame(playerCardResizeFrame)
    playerCardResizeFrame = 0
  }

  if (playerCardResizeTimeout !== 0) {
    window.clearTimeout(playerCardResizeTimeout)
    playerCardResizeTimeout = 0
  }

  pendingPlayerCardSizeUpdates.clear()
}

function setPlayerCardRef(playerId, element) {
  const normalizedPlayerId = normalizeActionLogPlayerId(playerId)
  if (normalizedPlayerId === null) {
    return
  }

  const previousElement = playerCardRefs.get(normalizedPlayerId)
  if (previousElement && previousElement !== element && playerCardResizeObserver) {
    playerCardResizeObserver.unobserve(previousElement)
  }

  if (!(element instanceof HTMLElement)) {
    playerCardRefs.delete(normalizedPlayerId)
    delete playerCardSizes[normalizedPlayerId]
    delete playerCardRingGeometries[normalizedPlayerId]
    delete playerCardTransitionStates[normalizedPlayerId]
    return
  }

  playerCardRefs.set(normalizedPlayerId, element)
  updatePlayerCardSize(normalizedPlayerId, element.clientWidth, element.clientHeight)

  if (playerCardResizeObserver) {
    playerCardResizeObserver.observe(element)
  }
}

function setupPlayerCardResizeObserver() {
  if (typeof ResizeObserver === 'undefined' || playerCardResizeObserver) {
    return
  }

  playerCardResizeObserver = new ResizeObserver((entries) => {
    entries.forEach((entry) => {
      const playerId = Number(entry.target.dataset.playerId)
      schedulePlayerCardSizeUpdate(playerId, entry.contentRect.width, entry.contentRect.height)
    })
  })

  playerCardRefs.forEach((element, playerId) => {
    updatePlayerCardSize(playerId, element.clientWidth, element.clientHeight)
    playerCardResizeObserver.observe(element)
  })
}

function createPlayerCardRingGeometry(width, height) {
  const normalizedWidth = Math.max(Math.round(Number(width) || 0), 0)
  const normalizedHeight = Math.max(Math.round(Number(height) || 0), 0)
  const flowOuterExpansion = (PLAYER_CARD_RING_CORE_STROKE_WIDTH / 2) + 0.25
  const svgPadding = PLAYER_CARD_RING_SVG_PADDING
  const left = svgPadding - flowOuterExpansion
  const top = svgPadding - flowOuterExpansion
  const ringWidth = Math.max(normalizedWidth + flowOuterExpansion * 2, 0)
  const ringHeight = Math.max(normalizedHeight + flowOuterExpansion * 2, 0)
  const radius = Math.max(
    0,
    Math.min(PLAYER_CARD_RING_BORDER_RADIUS + flowOuterExpansion, ringWidth / 2, ringHeight / 2)
  )
  const hasGeometry = normalizedWidth > 0 && normalizedHeight > 0 && ringWidth > 0 && ringHeight > 0
  const right = left + ringWidth
  const bottom = top + ringHeight
  const path = hasGeometry
    ? [
        `M ${left + radius} ${top}`,
        `H ${right - radius}`,
        `A ${radius} ${radius} 0 0 1 ${right} ${top + radius}`,
        `V ${bottom - radius}`,
        `A ${radius} ${radius} 0 0 1 ${right - radius} ${bottom}`,
        `H ${left + radius}`,
        `A ${radius} ${radius} 0 0 1 ${left} ${bottom - radius}`,
        `V ${top + radius}`,
        `A ${radius} ${radius} 0 0 1 ${left + radius} ${top}`,
        'Z'
      ].join(' ')
    : ''

  return {
    width: normalizedWidth,
    height: normalizedHeight,
    svgPadding,
    left,
    top,
    ringWidth,
    ringHeight,
    radius,
    hasGeometry,
    viewBox: `0 0 ${Math.max(normalizedWidth + svgPadding * 2, 1)} ${Math.max(normalizedHeight + svgPadding * 2, 1)}`,
    style: {
      left: `${-svgPadding}px`,
      top: `${-svgPadding}px`,
      width: `${normalizedWidth + svgPadding * 2}px`,
      height: `${normalizedHeight + svgPadding * 2}px`
    },
    path
  }
}

function getPlayerCardRingGeometry(playerId) {
  const normalizedPlayerId = normalizeActionLogPlayerId(playerId)
  if (normalizedPlayerId === null) {
    return createPlayerCardRingGeometry(0, 0)
  }

  return playerCardRingGeometries[normalizedPlayerId]
    || createPlayerCardRingGeometry(playerCardSizes[normalizedPlayerId]?.width, playerCardSizes[normalizedPlayerId]?.height)
}

function hasPlayerCardRingGeometry(playerId) {
  return getPlayerCardRingGeometry(playerId).hasGeometry
}

function getPlayerCardRingViewBox(playerId) {
  return getPlayerCardRingGeometry(playerId).viewBox
}

function getPlayerCardRingStyle(playerId) {
  return getPlayerCardRingGeometry(playerId).style
}

function getPlayerCardRingPath(playerId) {
  return getPlayerCardRingGeometry(playerId).path
}

function isPlayerStatusSizeTransitionEvent(event) {
  return event?.target === event?.currentTarget && event?.propertyName === 'max-height'
}

function markPlayerCardTransitionState(playerId, isTransitioning) {
  const normalizedPlayerId = normalizeActionLogPlayerId(playerId)
  if (normalizedPlayerId === null) {
    return
  }

  if (isTransitioning) {
    playerCardTransitionStates[normalizedPlayerId] = true
    return
  }

  delete playerCardTransitionStates[normalizedPlayerId]
}

function syncPlayerCardSizeImmediately(playerId) {
  const normalizedPlayerId = normalizeActionLogPlayerId(playerId)
  if (normalizedPlayerId === null) {
    return
  }

  const element = playerCardRefs.get(normalizedPlayerId)
  if (!(element instanceof HTMLElement)) {
    return
  }

  updatePlayerCardSize(normalizedPlayerId, element.clientWidth, element.clientHeight)
}

function handlePlayerStatusTransitionStart(playerId, event) {
  if (!isPlayerStatusSizeTransitionEvent(event)) {
    return
  }

  markPlayerCardTransitionState(playerId, true)
  syncPlayerCardSizeImmediately(playerId)
}

function handlePlayerStatusTransitionEnd(playerId, event) {
  if (!isPlayerStatusSizeTransitionEvent(event)) {
    return
  }

  markPlayerCardTransitionState(playerId, false)
  syncPlayerCardSizeImmediately(playerId)
}

function setAvailableActions(rawActions) {
  const nextActions = Array.isArray(rawActions)
    ? rawActions.map((action, idx) => normalizeAction(action, idx))
    : []

  const normalizedRecommendedActionId = normalizeAvailableActionId(recommendedActionId.value)
  if (
    normalizedRecommendedActionId !== null
    && !nextActions.some((action) => normalizeAvailableActionId(action?.id) === normalizedRecommendedActionId)
  ) {
    clearRecommendedAction()
  }

  actions.value = nextActions
  actionCount.value = nextActions.length
}

function normalizeFinalScoreValue(value) {
  const normalizedValue = Number(value)
  return Number.isFinite(normalizedValue) ? normalizedValue : 0
}

function setFinalScores(rawScores) {
  if (!rawScores || typeof rawScores !== 'object') {
    finalScores.value = null
    finalScoreModalOpen.value = false
    return
  }

  finalScores.value = rawScores
}

function openFinalScoreModal() {
  if (!hasFinalScores.value) {
    return
  }

  finalScoreModalOpen.value = true
}

let systemRecordSequence = 0

function normalizeActionType(actionType) {
  if (actionType === 'normal' || actionType === 'immediate') {
    return actionType
  }

  return 'system'
}

function formatActionModeLabel(actionType) {
  return normalizeActionType(actionType)
}

function normalizeActionLogPlayerId(playerId) {
  const normalizedPlayerId = Number(playerId)
  return Number.isInteger(normalizedPlayerId) && normalizedPlayerId >= 0
    ? normalizedPlayerId
    : null
}

function resolveNamedLogColor(colorName) {
  if (typeof colorName !== 'string' || !colorName) {
    return NAMED_LOG_COLORS.default
  }

  return NAMED_LOG_COLORS[colorName] || NAMED_LOG_COLORS.default
}

function getPlayerResolvedPlanningColor(playerId) {
  const normalizedPlayerId = normalizeActionLogPlayerId(playerId)
  if (normalizedPlayerId === null) {
    return 'transparent'
  }

  const planningCardId = normalizePlanningCardId(players.value[normalizedPlayerId]?.planningCardId)
  return planningCardId ? planningCardIdToColor[planningCardId] || 'transparent' : 'transparent'
}

function getActionLogPlayerColor(playerId) {
  const normalizedPlayerId = normalizeActionLogPlayerId(playerId)
  if (normalizedPlayerId === null) {
    return '#64748b'
  }

  return getPlayerResolvedPlanningColor(normalizedPlayerId)
}

function getCurrentActionOwnerColor(playerId) {
  const resolvedPlanningColor = getPlayerResolvedPlanningColor(playerId)
  return resolvedPlanningColor === 'transparent' ? '#64748b' : resolvedPlanningColor
}

function expandCurrentActionPlayerCard(playerId = currentActionPlayerId.value) {
  const normalizedPlayerId = normalizeActionLogPlayerId(playerId)
  if (normalizedPlayerId === null) {
    return
  }

  if (!Object.prototype.hasOwnProperty.call(collapsedPlayers, normalizedPlayerId)) {
    return
  }

  collapsedPlayers[normalizedPlayerId] = false
}

function getActionLogPlayerLabel(playerId) {
  const normalizedPlayerId = normalizeActionLogPlayerId(playerId)
  if (normalizedPlayerId === null) {
    return '系统'
  }

  return `玩家 ${normalizedPlayerId + 1}`
}

function createSystemActionLogRecordId() {
  systemRecordSequence += 1
  return `sys.${String(systemRecordSequence).padStart(3, '0')}`
}

function prependActionLogRecord(record) {
  actionLogs.value.unshift(record)

  if (actionLogs.value.length > ACTION_LOG_LIMIT) {
    actionLogs.value.splice(ACTION_LOG_LIMIT)
  }
}

function refreshActionLogPlayerColors(targetPlayerId = null) {
  const normalizedTargetPlayerId = targetPlayerId === null
    ? null
    : normalizeActionLogPlayerId(targetPlayerId)

  actionLogs.value = actionLogs.value.map((entry) => {
    if (entry.kind === 'divider' || entry.playerId === null) {
      return entry
    }

    if (normalizedTargetPlayerId !== null && entry.playerId !== normalizedTargetPlayerId) {
      return entry
    }

    const nextPlayerColor = getActionLogPlayerColor(entry.playerId)
    const nextAccentColor = entry.accentColor === entry.playerColor
      ? nextPlayerColor
      : entry.accentColor

    if (entry.playerColor === nextPlayerColor && entry.accentColor === nextAccentColor) {
      return entry
    }

    return {
      ...entry,
      playerColor: nextPlayerColor,
      accentColor: nextAccentColor
    }
  })
}

function appendActionLogEntry(playerId, payload) {
  const text = payload?.content ?? payload?.message ?? ''
  if (!text) return

  const currentStage = getCurrentActionLogStage()
  const normalizedPlayerId = normalizeActionLogPlayerId(playerId)
  const playerColor = normalizedPlayerId === null
    ? resolveNamedLogColor(payload?.color)
    : getActionLogPlayerColor(normalizedPlayerId)
  const accentColor = payload?.color ? resolveNamedLogColor(payload.color) : playerColor

  prependActionLogRecord({
    uid: createSystemActionLogRecordId(),
    kind: 'system',
    actionId: null,
    actionIdText: '',
    playerId: normalizedPlayerId,
    playerLabel: getActionLogPlayerLabel(normalizedPlayerId),
    playerColor,
    accentColor,
    actionType: 'system',
    stageKey: currentStage.id,
    stageLabel: currentStage.label,
    description: text,
    selectionSource: 'system',
    selectionStrategy: ''
  })
}

function normalizeActionHistoryDividerEntry(entry, dividerSequence) {
  const stageDefinition = getActionLogStageDefinition(entry?.stage_key)

  return {
    uid: `div.${stageDefinition.id}.${String(dividerSequence).padStart(3, '0')}`,
    kind: 'divider',
    actionId: null,
    actionIdText: '',
    playerId: null,
    playerLabel: '',
    playerColor: 'transparent',
    accentColor: '#64748b',
    actionType: 'divider',
    stageKey: stageDefinition.id,
    stageLabel: stageDefinition.label,
    description: entry?.description || stageDefinition.dividerLabel
  }
}

function normalizeActionHistoryEntry(entry, actionSequence) {
  const stageDefinition = getActionLogStageDefinition(entry?.stage_key)
  const normalizedPlayerId = normalizeActionLogPlayerId(entry?.player_id)
  const normalizedActionType = normalizeActionType(entry?.action_type)
  const normalizedActionId = Number(entry?.action_id)

  // 查找待标记的选择方式
  const pendingIndex = pendingSelectionModes.value.findIndex(
    (item) => item.actionId === normalizedActionId
  )
  let selectionMode = null
  if (pendingIndex !== -1) {
    selectionMode = pendingSelectionModes.value[pendingIndex].selectionMode
    pendingSelectionModes.value.splice(pendingIndex, 1)
  }

  return {
    uid: `act.${String(actionSequence).padStart(3, '0')}`,
    kind: 'action',
    actionId: Number.isInteger(normalizedActionId) ? normalizedActionId : null,
    actionIdText: Number.isInteger(normalizedActionId) ? String(normalizedActionId) : '',
    playerId: normalizedPlayerId,
    playerLabel: getActionLogPlayerLabel(normalizedPlayerId),
    playerColor: getActionLogPlayerColor(normalizedPlayerId),
    accentColor: getActionLogPlayerColor(normalizedPlayerId),
    actionType: normalizedActionType,
    stageKey: stageDefinition.id,
    stageLabel: stageDefinition.label,
    description: entry?.description || '未提供行动描述',
    selectionSource: entry?.selection_source === 'system' ? 'system' : 'manual',
    selectionStrategy: typeof entry?.selection_strategy === 'string' ? entry.selection_strategy : '',
    selectionMode: selectionMode || entry?.selection_mode || (entry?.selection_source === 'system' ? 'system' : 'player_choice'),
    actionCategory: entry?.action_category || '',
    actionSubcategory: entry?.action_subcategory || '',
    actionDetail: entry?.action_detail || '',
    durationMs: entry?.duration_ms || 0,
    playerRemainingMs: entry?.player_remaining_ms || 0
  }
}

function setActionLogsFromHistory(rawHistory) {
  const normalizedHistory = Array.isArray(rawHistory) ? rawHistory : []
  const persistentLocalLogs = actionLogs.value.filter((entry) => (
    entry?.kind === 'system' || entry?.persistOnHistoryRefresh === true
  ))
  let actionSequence = 0
  let dividerSequence = 0

  const normalizedLogs = normalizedHistory.map((entry) => {
    if (entry?.kind === 'divider') {
      dividerSequence += 1
      return normalizeActionHistoryDividerEntry(entry, dividerSequence)
    }

    actionSequence += 1
    return normalizeActionHistoryEntry(entry, actionSequence)
  }).reverse()

  const normalizedLogUidSet = new Set(normalizedLogs.map((entry) => entry.uid))
  const retainedLocalLogs = persistentLocalLogs.filter((entry) => !normalizedLogUidSet.has(entry.uid))

  actionLogs.value = [...retainedLocalLogs, ...normalizedLogs]
  systemRecordSequence = retainedLocalLogs.filter((entry) => entry?.kind === 'system').length
}

function toggleFilterValue(listRef, value) {
  if (listRef.value.includes(value)) {
    listRef.value = listRef.value.filter((item) => item !== value)
    return
  }

  listRef.value = [...listRef.value, value]
}

function openActionLogFilterModal() {
  if (actionLogFilterModalOpen.value) {
    actionLogFilterModalOpen.value = false
    return
  }

  controlCenterStrategyModalOpen.value = false
  /*
  if (!isSupportedControlCenterStrategy()) {
    alert(getUnsupportedControlCenterStrategyMessage())
    return
  }

  const strategyId = normalizeControlCenterStrategyId(selectedControlStrategyId.value)
  controlCenterPendingMode.value = 'recommend'

  try {
    const { ok, payload } = await requestControlCenterStrategy('/api/game/strategy/recommend', strategyId)
    if (!ok) {
      clearRecommendedAction()
      alert(getControlCenterStrategyRequestErrorMessage(payload, '策略推荐失败。'))
      return
    }

    setRecommendedAction(payload.action_id, payload.selection_strategy || strategyId)
    return
  } finally {
    controlCenterPendingMode.value = ''
  }
  if (!isSupportedControlCenterStrategy()) {
    alert(getUnsupportedControlCenterStrategyMessage())
    return
  }

  const strategyId = normalizeControlCenterStrategyId(selectedControlStrategyId.value)
  const previousVersion = stateVersion.value
  controlCenterPendingMode.value = 'execute'

  try {
    const { ok, payload } = await requestControlCenterStrategy('/api/game/strategy/execute', strategyId)
    if (!ok) {
      alert(getControlCenterStrategyRequestErrorMessage(payload, '策略执行失败。'))
      return
    }

    clearRecommendedAction()
    await syncStateAfterActionSubmission(previousVersion)
    return
  } finally {
    controlCenterPendingMode.value = ''
  }
  */
  draftActionLogPlayerFilters.value = [...appliedActionLogPlayerFilters.value]
  draftActionLogTypeFilters.value = [...appliedActionLogTypeFilters.value]
  draftActionLogStageFilters.value = [...appliedActionLogStageFilters.value]
  draftActionLogCategoryFilters.value = [...appliedActionLogCategoryFilters.value]
  draftActionLogSubcategoryFilters.value = [...appliedActionLogSubcategoryFilters.value]
  draftActionLogDurationFilters.value = [...appliedActionLogDurationFilters.value]
  draftActionLogRemainingFilters.value = [...appliedActionLogRemainingFilters.value]
  draftActionLogSelectionModeFilters.value = [...appliedActionLogSelectionModeFilters.value]
  draftActionLogStrategyTypeFilters.value = [...appliedActionLogStrategyTypeFilters.value]
  draftActionLogActionIdFilter.value = appliedActionLogActionIdFilter.value
  draftActionLogUidFilter.value = appliedActionLogUidFilter.value
  actionLogFilterModalOpen.value = true
}

function openControlCenterStrategyModal() {
  actionLogFilterModalOpen.value = false
  controlCenterStrategyModalOpen.value = true
}

function normalizeControlCenterStrategyId(strategyId) {
  return typeof strategyId === 'string' ? strategyId.trim() : ''
}

function isSupportedControlCenterStrategy(strategyId = selectedControlStrategyId.value) {
  return SUPPORTED_STRATEGY_IDS.has(normalizeControlCenterStrategyId(strategyId))
}

function getControlCenterStrategyOption(strategyId) {
  return STRATEGY_OPTIONS.find((strategy) => strategy.id === strategyId) || null
}

function getControlCenterStrategyIconClass(strategyId) {
  switch (normalizeControlCenterStrategyId(strategyId)) {
    case 'random_pure':
      return 'fas fa-dice'
    case 'random_fast_action':
      return 'fas fa-bolt'
    case 'metric_single_step_best':
      return 'fas fa-chart-line'
    case 'ai_llm_reasoning':
      return 'fas fa-brain'
    default:
      return 'fas fa-star'
  }
}

function clearRecommendedAction() {
  recommendedActionId.value = null
  recommendedActionStrategyId.value = ''
}

function findActionGroupKeyByActionId(actionId) {
  const normalizedActionId = normalizeAvailableActionId(actionId)
  if (normalizedActionId === null) {
    return null
  }

  const matchedGroup = groupedActionCards.value.find((group) => (
    Array.isArray(group.options) && group.options.some((option) => option.id === normalizedActionId)
  ))
  return matchedGroup?.groupKey || null
}

function setRecommendedAction(actionId, strategyId) {
  const normalizedActionId = normalizeAvailableActionId(actionId)
  if (normalizedActionId === null) {
    clearRecommendedAction()
    return
  }

  recommendedActionId.value = normalizedActionId
  recommendedActionStrategyId.value = normalizeControlCenterStrategyId(strategyId)

  const targetGroupKey = findActionGroupKeyByActionId(normalizedActionId)
  if (!isActionOverflowMode.value || !targetGroupKey) {
    return
  }

  expandedActionGroupKey.value = targetGroupKey
  nextTick(() => {
    refreshActionGroupBodyHeights()
    const actionContent = actionContentRef.value
    if (actionContent) {
      actionContent.scrollTop = 0
    }
  })
}

function getUnsupportedControlCenterStrategyMessage() {
  return `${selectedControlStrategySummaryLabel.value}策略暂未接入后端，当前仅支持随机 · 完全和随机 · 经快速行动优化。`
}

function getControlCenterStrategyRequestErrorMessage(payload, fallbackMessage) {
  if (typeof payload?.error === 'string' && payload.error.trim()) {
    return payload.error.trim()
  }

  if (typeof payload?.message === 'string' && payload.message.trim()) {
    return payload.message.trim()
  }

  return fallbackMessage
}

async function requestControlCenterStrategy(endpoint, strategyId) {
  const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:5001'

  try {
    const response = await fetch(`${apiBaseUrl}${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        strategy_id: strategyId,
        player_id: currentActionPlayerId.value
      })
    })
    const payload = await response.json()

    return {
      ok: response.ok && payload?.status === 'success',
      payload
    }
  } catch (error) {
    return {
      ok: false,
      payload: {
        error: error instanceof Error ? error.message : '请求失败'
      }
    }
  }
}

function selectControlCenterStrategy(strategyId) {
  if (!STRATEGY_OPTIONS.some((strategy) => strategy.id === strategyId)) {
    return
  }

  selectedControlStrategyId.value = strategyId
  clearRecommendedAction()
}

async function runControlCenterStrategyPlaceholder() {
  if (!controlCenterCanRun.value) {
    return
  }

  controlCenterStrategyModalOpen.value = false
  alert(`${selectedControlStrategySummaryLabel.value}策略的后端执行逻辑开发中，当前仅保留入口。`)
}

async function recommendControlCenterStrategyPlaceholder() {
  if (!controlCenterCanRun.value) {
    return
  }

  controlCenterStrategyModalOpen.value = false
  alert(`${selectedControlStrategySummaryLabel.value}策略的推荐逻辑开发中，当前仅保留入口。`)
}

async function runControlCenterStrategy() {
  if (!controlCenterCanRun.value) {
    return
  }

  controlCenterStrategyModalOpen.value = false

  if (!isSupportedControlCenterStrategy()) {
    alert(getUnsupportedControlCenterStrategyMessage())
    return
  }

  const strategyId = normalizeControlCenterStrategyId(selectedControlStrategyId.value)
  const previousVersion = stateVersion.value
  controlCenterPendingMode.value = 'execute'

  try {
    const { ok, payload } = await requestControlCenterStrategy('/api/game/strategy/execute', strategyId)
    if (!ok) {
      alert(getControlCenterStrategyRequestErrorMessage(payload, '策略执行失败。'))
      return
    }

    clearRecommendedAction()
    await syncStateAfterActionSubmission(previousVersion)
  } finally {
    controlCenterPendingMode.value = ''
  }
}

async function recommendControlCenterStrategy() {
  if (!controlCenterCanRun.value) {
    return
  }

  controlCenterStrategyModalOpen.value = false

  if (!isSupportedControlCenterStrategy()) {
    alert(getUnsupportedControlCenterStrategyMessage())
    return
  }

  const strategyId = normalizeControlCenterStrategyId(selectedControlStrategyId.value)
  controlCenterPendingMode.value = 'recommend'

  try {
    const { ok, payload } = await requestControlCenterStrategy('/api/game/strategy/recommend', strategyId)
    if (!ok) {
      clearRecommendedAction()
      alert(getControlCenterStrategyRequestErrorMessage(payload, '策略推荐失败。'))
      return
    }

    setRecommendedAction(payload.action_id, payload.selection_strategy || strategyId)
  } finally {
    controlCenterPendingMode.value = ''
  }
}

async function executeControlCenterAction() {
  if (!controlCenterCanRun.value) {
    return
  }

  controlCenterStrategyModalOpen.value = false

  // 如果处于推荐态，直接执行推荐的选项
  if (hasRecommendedAction.value) {
    const normalizedActionId = normalizeAvailableActionId(recommendedActionId.value)
    if (normalizedActionId !== null) {
      const previousVersion = stateVersion.value
      controlCenterPendingMode.value = 'execute'

      try {
        const result = await submitActionAndSync(normalizedActionId, {
          selectionSource: 'system',
          selectionStrategy: recommendedActionStrategyId.value || selectedControlStrategyId.value
        })

        if (result.submitted) {
          clearRecommendedAction()
        }
      } finally {
        controlCenterPendingMode.value = ''
      }
    }
    return
  }

  // 非推荐态：调用策略并执行
  if (!isSupportedControlCenterStrategy()) {
    alert(getUnsupportedControlCenterStrategyMessage())
    return
  }

  const strategyId = normalizeControlCenterStrategyId(selectedControlStrategyId.value)
  const previousVersion = stateVersion.value
  controlCenterPendingMode.value = 'execute'

  try {
    const { ok, payload } = await requestControlCenterStrategy('/api/game/strategy/execute', strategyId)
    if (!ok) {
      alert(getControlCenterStrategyRequestErrorMessage(payload, '策略执行失败。'))
      return
    }

    clearRecommendedAction()
    await syncStateAfterActionSubmission(previousVersion)
  } finally {
    controlCenterPendingMode.value = ''
  }
}

function toggleDraftActionLogPlayer(playerId) {
  toggleFilterValue(draftActionLogPlayerFilters, playerId)
}

function toggleDraftActionLogType(actionType) {
  toggleFilterValue(draftActionLogTypeFilters, actionType)
}

function toggleDraftActionLogStage(stageKey) {
  toggleFilterValue(draftActionLogStageFilters, stageKey)
}

function toggleDraftActionLogCategory(category) {
  toggleFilterValue(draftActionLogCategoryFilters, category)
  // 清除不属于已选大类的细类筛选
  draftActionLogSubcategoryFilters.value = draftActionLogSubcategoryFilters.value.filter((sub) => {
    const validCategories = draftActionLogCategoryFilters.value
    if (validCategories.length === 0) return false
    // 检查这个细类是否属于已选大类
    return renderedActionLogs.value.some((entry) =>
      entry.kind === 'action' &&
      entry.actionSubcategory === sub &&
      validCategories.includes(entry.actionCategory)
    )
  })
}

function toggleDraftActionLogSubcategory(subcategory) {
  toggleFilterValue(draftActionLogSubcategoryFilters, subcategory)
}

function toggleDraftActionLogDuration(durationId) {
  toggleFilterValue(draftActionLogDurationFilters, durationId)
}

function toggleDraftActionLogRemaining(remainingId) {
  toggleFilterValue(draftActionLogRemainingFilters, remainingId)
}

function toggleDraftActionLogSelectionMode(modeId) {
  toggleFilterValue(draftActionLogSelectionModeFilters, modeId)
}

function toggleDraftActionLogStrategyType(strategyTypeId) {
  toggleFilterValue(draftActionLogStrategyTypeFilters, strategyTypeId)
}

function clearDraftActionLogFilters() {
  draftActionLogPlayerFilters.value = []
  draftActionLogTypeFilters.value = []
  draftActionLogStageFilters.value = []
  draftActionLogCategoryFilters.value = []
  draftActionLogSubcategoryFilters.value = []
  draftActionLogDurationFilters.value = []
  draftActionLogRemainingFilters.value = []
  draftActionLogSelectionModeFilters.value = []
  draftActionLogStrategyTypeFilters.value = []
  draftActionLogActionIdFilter.value = ''
  draftActionLogUidFilter.value = ''
}

function applyActionLogFilters() {
  appliedActionLogPlayerFilters.value = [...draftActionLogPlayerFilters.value]
  appliedActionLogTypeFilters.value = [...draftActionLogTypeFilters.value]
  appliedActionLogStageFilters.value = [...draftActionLogStageFilters.value]
  appliedActionLogCategoryFilters.value = [...draftActionLogCategoryFilters.value]
  appliedActionLogSubcategoryFilters.value = [...draftActionLogSubcategoryFilters.value]
  appliedActionLogDurationFilters.value = [...draftActionLogDurationFilters.value]
  appliedActionLogRemainingFilters.value = [...draftActionLogRemainingFilters.value]
  appliedActionLogSelectionModeFilters.value = [...draftActionLogSelectionModeFilters.value]
  appliedActionLogStrategyTypeFilters.value = [...draftActionLogStrategyTypeFilters.value]
  appliedActionLogActionIdFilter.value = normalizeActionLogSearchValue(draftActionLogActionIdFilter.value)
  appliedActionLogUidFilter.value = normalizeActionLogSearchValue(draftActionLogUidFilter.value)
  actionLogFilterModalOpen.value = false
}

function getActionLogEntryStyle(log) {
  const playerColor = typeof log?.playerColor === 'string' && log.playerColor ? log.playerColor : 'transparent'
  return {
    '--log-player-color': playerColor,
    '--log-player-dot-shadow': playerColor === 'transparent'
      ? 'none'
      : '0 0 0 1px rgba(255, 255, 255, 0.08)'
  }
}

function formatDuration(ms) {
  if (!ms || ms <= 0) return '0:00'
  const totalSeconds = Math.floor(ms / 1000)
  const minutes = Math.floor(totalSeconds / 60)
  const seconds = totalSeconds % 60
  return `${minutes}:${String(seconds).padStart(2, '0')}`
}

function getRemainingPercentage(log) {
  const remainingMs = log.playerRemainingMs || 0
  // 使用玩家总时长计算百分比
  const totalMs = timerStore.mainTimeLimit || 0
  if (totalMs <= 0) return remainingMs > 0 ? 100 : 0
  const pct = Math.round((remainingMs / totalMs) * 100)
  return Math.min(100, Math.max(0, pct))
}

function buildActionLogEntryTitle(log) {
  const titleLines = []

  if (log.kind !== 'divider') {
    titleLines.push(`本局序号 ${log.uid}`)
  }

  if (log.stageLabel) {
    titleLines.push(log.stageLabel)
  }

  if (log.playerLabel) {
    titleLines.push(log.playerLabel)
  }

  if (Number.isInteger(log.actionId)) {
    titleLines.push(`行动编号 ${log.actionId}`)
  }

  if (log.kind === 'action' || log.kind === 'system') {
    titleLines.push(log.actionType)
  }

  // 选择方式
  const selectionModeLabel = ACTION_LOG_SELECTION_MODE_OPTIONS.find((opt) => opt.id === log.selectionMode)?.label
  if (selectionModeLabel) {
    titleLines.push(selectionModeLabel)
  }

  if (log.selectionStrategy) {
    const strategyTypeLabel = ACTION_LOG_STRATEGY_TYPE_OPTIONS.find((opt) => opt.id === log.selectionStrategy)?.label
    titleLines.push(`策略类型：${strategyTypeLabel || log.selectionStrategy}`)
  }

  // 添加行动分类信息（大类、细类、细节），分三行显示
  if (log.actionCategory) {
    titleLines.push(`大类：${log.actionCategory}`)
  }
  if (log.actionSubcategory) {
    titleLines.push(`细类：${log.actionSubcategory}`)
  }
  if (log.actionDetail) {
    titleLines.push(`细节：${log.actionDetail}`)
  }

  if (log.description && titleLines[titleLines.length - 1] !== log.description) {
    titleLines.push(`描述：${log.description}`)
  }

  if (log.durationMs > 0) {
    titleLines.push(`用时 ${formatDuration(log.durationMs)}`)
  }

  if (log.playerRemainingMs > 0) {
    const pct = getRemainingPercentage(log)
    titleLines.push(`剩余时长 ${formatDuration(log.playerRemainingMs)} (${pct}%)`)
  }

  return titleLines.join('\n')
}

function buildPlayerStatusRows(player) {
  return PLAYER_STATUS_ROWS.map((row) => row.map((definition) => ({
    ...definition,
    value: player?.[definition.key] ?? 0,
    badgeValue: definition.badgeKey ? player?.[definition.badgeKey] ?? 0 : null
  })))
}

function getMapBuildingColorId(controller) {
  const normalizedController = Number(controller)
  if (!Number.isInteger(normalizedController) || normalizedController < 0) {
    return null
  }

  const planningCardId = players.value[normalizedController]?.planningCardId
  if (Number.isInteger(planningCardId) && planningCardId > 0) {
    return planningCardId
  }

  return normalizedController + 1
}

function getAbilityBoardTileStyle(tileId, idx) {
  if (!tileId) return { display: 'none' }
  const col = Math.floor(idx / 3)
  const row = idx % 3
  const lefts = ['9.465%', '34.363%', '59.465%', '84.362%']
  const tops = ['7.391%', '38.695%', '69.130%']
  return {
    ...getAbilityTileStyleByBackendId(tileId),
    position: 'absolute',
    left: lefts[col],
    top: tops[row],
    width: '11.934%',
    height: '24.348%',
    borderRadius: '6px'
  }
}

function getScienceBoardTileStyle(tileId, idx) {
  if (!tileId) return { display: 'none' }
  const pos = getScienceTilePercentPos(idx)
  return {
    ...getScienceTileStyleByBackendId(tileId),
    position: 'absolute',
    left: pos.left,
    top: pos.top,
    width: '20.093%',
    height: pos.height,
    borderRadius: '8px'
  }
}

function getScienceTilePercentPos(idx) {
  const playerCount = numPlayers.value
  const map35 = {
    0: { left: '2.453%', top: '26.613%', height: '22.177%' },
    1: { left: '2.453%', top: '57.056%', height: '22.177%' },
    2: { left: '27.453%', top: '26.613%', height: '22.177%' },
    3: { left: '27.453%', top: '57.056%', height: '22.177%' },
    4: { left: '52.453%', top: '26.613%', height: '22.177%' },
    5: { left: '52.453%', top: '57.056%', height: '22.177%' },
    6: { left: '77.453%', top: '26.613%', height: '22.177%' },
    7: { left: '77.453%', top: '57.056%', height: '22.177%' }
  }
  const map45 = {
    0: { left: '2.453%', top: '44.514%', height: '17.241%' },
    1: { left: '2.453%', top: '68.182%', height: '17.241%' },
    2: { left: '27.453%', top: '44.514%', height: '17.241%' },
    3: { left: '27.453%', top: '68.182%', height: '17.241%' },
    4: { left: '52.453%', top: '44.514%', height: '17.241%' },
    5: { left: '52.453%', top: '68.182%', height: '17.241%' },
    6: { left: '77.453%', top: '44.514%', height: '17.241%' },
    7: { left: '77.453%', top: '68.182%', height: '17.241%' }
  }
  if (playerCount === 3) {
    return map35[idx] || { left: '0%', top: '0%', height: '22.177%' }
  }
  if (playerCount === 4) {
    const extra = {
      8: { left: '14.953%', top: '8.621%', height: '17.241%' },
      9: { left: '64.953%', top: '8.621%', height: '17.241%' }
    }
    return map45[idx] || extra[idx] || { left: '0%', top: '0%', height: '17.241%' }
  }
  // 5人局
  const extra5 = {
    8: { left: '2.453%', top: '20.690%', height: '17.241%' },
    9: { left: '27.453%', top: '20.690%', height: '17.241%' },
    10: { left: '52.453%', top: '20.690%', height: '17.241%' },
    11: { left: '77.453%', top: '20.690%', height: '17.241%' }
  }
  return map45[idx] || extra5[idx] || { left: '0%', top: '0%', height: '17.241%' }
}

function applyPlayerState(player, backendPlayer) {
  if (!player || !backendPlayer) return

  // 先回到后端约定的默认展示值，避免同人数新局沿用上一局的旧资源。
  Object.assign(player, createDefaultPlayerDisplayState())

  if (backendPlayer.resources) {
    player.money = backendPlayer.resources.money ?? player.money
    player.mineral = backendPlayer.resources.ore ?? player.mineral
    player.mibao = backendPlayer.resources.meeples ?? player.mibao
    player.allMeeples = backendPlayer.resources.all_meeples ?? player.allMeeples
    player.bridges = backendPlayer.resources.all_bridges ?? player.bridges
    player.bank = backendPlayer.resources.bank_book ?? player.bank
    player.law = backendPlayer.resources.law_book ?? player.law
    player.engineering = backendPlayer.resources.engineering_book ?? player.engineering
    player.medical = backendPlayer.resources.medical_book ?? player.medical
  }

  if (backendPlayer.magics) {
    player.magic1 = backendPlayer.magics.zone1 ?? player.magic1
    player.magic2 = backendPlayer.magics.zone2 ?? player.magic2
    player.magic3 = backendPlayer.magics.zone3 ?? player.magic3
  }

  player.money = backendPlayer.money ?? player.money
  player.mineral = backendPlayer.mineral ?? player.mineral
  player.mibao = backendPlayer.mibao ?? player.mibao
  player.allMeeples = backendPlayer.allMeeples ?? player.allMeeples
  player.allMeeples = backendPlayer.all_meeples ?? player.allMeeples
  player.bridges = backendPlayer.bridges ?? player.bridges
  player.bridges = backendPlayer.allBridges ?? player.bridges
  player.bridges = backendPlayer.all_bridges ?? player.bridges
  player.bank = backendPlayer.bank ?? player.bank
  player.law = backendPlayer.law ?? player.law
  player.engineering = backendPlayer.engineering ?? player.engineering
  player.medical = backendPlayer.medical ?? player.medical
  if (backendPlayer.tracks) {
    player.tracks.bank = backendPlayer.tracks.bank ?? player.tracks.bank
    player.tracks.law = backendPlayer.tracks.law ?? player.tracks.law
    player.tracks.engineering = backendPlayer.tracks.engineering ?? player.tracks.engineering
    player.tracks.medical = backendPlayer.tracks.medical ?? player.tracks.medical
  }
  player.magic1 = backendPlayer.magic1 ?? player.magic1
  player.magic2 = backendPlayer.magic2 ?? player.magic2
  player.magic3 = backendPlayer.magic3 ?? player.magic3

  player.score = backendPlayer.boardscore ?? player.score
  player.score = backendPlayer.score ?? player.score
  player.cities = backendPlayer.citys_amount ?? player.cities
  player.cities = backendPlayer.cities ?? player.cities
  player.navigation = backendPlayer.navigation_level ?? player.navigation
  player.navigation = backendPlayer.navigation ?? player.navigation
  player.shovel = backendPlayer.shovel_level ?? player.shovel
  player.shovel = backendPlayer.shovel ?? player.shovel
  player.workshop = backendPlayer.buildings?.workshop ?? player.workshop
  player.guild = backendPlayer.buildings?.guild ?? player.guild
  player.palace = backendPlayer.buildings?.palace ?? player.palace
  player.school = backendPlayer.buildings?.school ?? player.school
  player.university = backendPlayer.buildings?.university ?? player.university
  player.workshop = backendPlayer.workshop ?? player.workshop
  player.guild = backendPlayer.guild ?? player.guild
  player.palace = backendPlayer.palace ?? player.palace
  player.school = backendPlayer.school ?? player.school
  player.university = backendPlayer.university ?? player.university
  player.booster_ids = Array.isArray(backendPlayer.booster_ids) ? [...backendPlayer.booster_ids] : []

  if (Object.prototype.hasOwnProperty.call(backendPlayer, 'planning_card_id')) {
    setPlayerPlanningCard(player, backendPlayer.planning_card_id)
  }

  if (Object.prototype.hasOwnProperty.call(backendPlayer, 'palace_tile_id')) {
    setPlayerPalaceTile(player, backendPlayer.palace_tile_id)
  }

  if (Object.prototype.hasOwnProperty.call(backendPlayer, 'is_got_palace')) {
    setPlayerPalaceActivation(player, backendPlayer.is_got_palace)
  }

  if (Object.prototype.hasOwnProperty.call(backendPlayer, 'faction_id')) {
    setPlayerFaction(player, backendPlayer.faction_id)
  }

  if (Object.prototype.hasOwnProperty.call(backendPlayer, 'settlements_and_cities')) {
    player.settlements_and_cities = backendPlayer.settlements_and_cities || {}
  }

  if (Object.prototype.hasOwnProperty.call(backendPlayer, 'city_tile_assignments')) {
    player.city_tile_assignments = backendPlayer.city_tile_assignments || {}
  }
}

function ensureMapCell(row, col) {
  if (!Array.isArray(mapState.grid) || mapState.grid.length !== MAP_CONFIG.rows) {
    mapState.grid = createDefaultMapGrid()
  }

  if (!Array.isArray(mapState.grid[row])) {
    mapState.grid[row] = Array.from(
      { length: MAP_CONFIG.cols },
      () => createDefaultMapCellState()
    )
  }

  if (!mapState.grid[row][col]) {
    mapState.grid[row][col] = createDefaultMapCellState()
  }

  return mapState.grid[row][col]
}

function resetMapState(nextGrid) {
  if (!Array.isArray(nextGrid)) {
    mapState.grid = createDefaultMapGrid()
    return
  }

  mapState.grid = nextGrid.map((row) =>
    Array.isArray(row)
      ? row.map((cell) => ({ ...createDefaultMapCellState(), ...cell }))
      : Array.from({ length: MAP_CONFIG.cols }, () => createDefaultMapCellState())
  )
}

function getHexPositionId(row, col) {
  const rowLetter = String.fromCharCode(65 + row)
  return `${rowLetter}${col + 1}`
}

function clearPlacedElementsAt(row, col) {
  const positionId = getHexPositionId(row, col)
  document.querySelectorAll(`.hex-element[data-position="${positionId}"]`).forEach((el) => {
    el.remove()
  })
}

function nextBuildingRenderToken(row, col) {
  const cellKey = `${row}-${col}`
  const nextToken = (mapBuildingRenderTokens.get(cellKey) ?? 0) + 1
  mapBuildingRenderTokens.set(cellKey, nextToken)
  return nextToken
}

function isLatestBuildingRender(row, col, renderToken) {
  return mapBuildingRenderTokens.get(`${row}-${col}`) === renderToken
}

function renderBuildingForCell(row, col) {
  const cell = ensureMapCell(row, col)
  const renderToken = nextBuildingRenderToken(row, col)

  // 1. 清除该位置所有已有元素
  clearPlacedElementsAt(row, col)

  // 2. 如果该位置无建筑、无侧楼、无城市标记，直接返回
  const hasMainBuilding = cell.building_id && cell.building_id > 0
  const hasAnnex = cell.has_annex
  const cityTileId = getCityTileIdForCell(row, col)

  if (!hasMainBuilding && !hasAnnex && !cityTileId) {
    return
  }

  const colorId = cell?.is_neutral ? 0 : getMapBuildingColorId(cell?.controller)
  if ((hasMainBuilding || hasAnnex) && (!Number.isInteger(colorId) || colorId < 0)) {
    return
  }

  // 3. 渲染主建筑（如果存在）
  if (hasMainBuilding) {
    placeElement(row, col, colorId, cell.building_id, 'append', renderToken)
  }

  // 4. 渲染侧楼（左上方）
  if (hasAnnex) {
    placeAnnex(row, col, colorId, renderToken)
  }

  // 5. 渲染城市标记（右上方）
  if (cityTileId) {
    placeCityTile(row, col, cityTileId, renderToken)
  }
}

function applyPlayerFieldChange(player, remainingKeys, value, changeType = '') {
  if (!remainingKeys.length) return

  const [firstKey, secondKey] = remainingKeys

  if (remainingKeys.length === 1) {
    switch (firstKey) {
      case 'planning_card_id':
        setPlayerPlanningCard(player, value)
        syncBonusColumnsFromPlayers()
        return
      case 'faction_id':
        setPlayerFaction(player, value)
        return
      case 'palace_tile_id':
        setPlayerPalaceTile(player, value)
        return
      case 'is_got_palace':
        setPlayerPalaceActivation(player, value)
        return
      case 'boardscore':
        player.score = value
        return
      case 'all_meeples':
        player.allMeeples = value
        return
      case 'all_bridges':
        player.bridges = value
        return
      case 'citys_amount':
        player.cities = value
        return
      case 'navigation_level':
        player.navigation = value
        return
      case 'shovel_level':
        player.shovel = value
        return
      case 'booster_ids':
        applyPlayerBoosterIdsChange(player, value)
        return
      case 'settlements_and_cities':
        player.settlements_and_cities = value || {}
        return
      case 'city_tile_assignments':
        player.city_tile_assignments = value || {}
        return
      default:
        player[firstKey] = value
        return
    }
  }

  if (firstKey === 'booster_ids') {
    const boosterIndex = Number.parseInt(secondKey, 10)
    if (Number.isInteger(boosterIndex) && boosterIndex >= 0) {
      const nextBoosterIds = Array.isArray(player.booster_ids) ? [...player.booster_ids] : []

      if (changeType === 'removed' || value === null || value === undefined) {
        nextBoosterIds.splice(boosterIndex, 1)
      } else {
        nextBoosterIds[boosterIndex] = value
      }

      while (
        nextBoosterIds.length > 0
        && (nextBoosterIds[nextBoosterIds.length - 1] === undefined || nextBoosterIds[nextBoosterIds.length - 1] === null)
      ) {
        nextBoosterIds.pop()
      }

      applyPlayerBoosterIdsChange(player, nextBoosterIds)
      return
    }
  }

  if (firstKey === 'resources') {
    switch (secondKey) {
      case 'money':
        player.money = value
        return
      case 'ore':
        player.mineral = value
        return
      case 'meeples':
        player.mibao = value
        return
      case 'all_meeples':
        player.allMeeples = value
        return
      case 'all_bridges':
        player.bridges = value
        return
      case 'bank_book':
        player.bank = value
        return
      case 'law_book':
        player.law = value
        return
      case 'engineering_book':
        player.engineering = value
        return
      case 'medical_book':
        player.medical = value
        return
      default:
        break
    }
  }

  if (firstKey === 'magics') {
    switch (secondKey) {
      case 'zone1':
        player.magic1 = value
        return
      case 'zone2':
        player.magic2 = value
        return
      case 'zone3':
        player.magic3 = value
        return
      default:
        break
    }
  }

  if (firstKey === 'buildings') {
    switch (secondKey) {
      case 'workshop':
        player.workshop = value
        return
      case 'guild':
        player.guild = value
        return
      case 'palace':
        player.palace = value
        return
      case 'school':
        player.school = value
        return
      case 'university':
        player.university = value
        return
      default:
        break
    }
  }

  updateNestedObject(player, remainingKeys, value)
}

// 监听可选行动变化，重新计算展开/折叠布局
watch(actions, () => {
  nextTick(() => {
    const actionContent = actionContentRef.value
    if (actionContent) {
      actionContent.scrollTop = 0
    }
  })
  // 默认全部展开，不再自动检测高度溢出
  // 卡片过多时允许在可选行动框内滚动
  // measureActionOverflow 已停用，如需恢复手风琴模式可手动调用
}, { deep: true })

// 监听行动记录变化，保持最新记录显示在最上方
watch(filteredActionLogs, () => {
  nextTick(() => {
    const actionLogContent = document.getElementById('action-log-content')
    if (actionLogContent) {
      actionLogContent.scrollTop = 0
    }
  })
})

watch(() => bonusColumns.value.length, () => {
  scheduleRoundInfoLayoutUpdate()
})

function togglePlayer(playerId) {
  collapsedPlayers[playerId] = !collapsedPlayers[playerId]
}

function toggleCard(cardName) {
  // 对地图卡片特殊处理：折叠前固定 SVG 高度，避免缩小动画
  if (cardName === 'map') {
    const svg = document.getElementById('hex-grid-svg')
    if (svg) {
      if (!collapsedCards['map']) {
        // 即将折叠：将 SVG 高度固定为当前渲染高度（像素值）
        const rect = svg.getBoundingClientRect()
        svg.style.height = `${rect.height}px`
      } else {
        // 即将展开：延迟恢复 height: 100%，等待动画完成
        setTimeout(() => {
          svg.style.height = ''
        }, 300)
      }
    }
  }

  collapsedCards[cardName] = !collapsedCards[cardName]

  if (cardName === 'tactical' && !collapsedCards[cardName]) {
    // 等待 CSS transition (max-height 0.3s) 完成后，父容器高度稳定了再计算布局
    setTimeout(() => {
      updateScienceAbilityLayout()
    }, 350)
  }
}

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

function openGameMenu() {
  gameMenuOpen.value = true
}

async function handleEndGame() {
  if (confirmState.value === 'end') {
    confirmState.value = null
    gameMenuOpen.value = false

    // 调用后端API停止游戏
    try {
      const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:5001'
      await fetch(`${apiBaseUrl}/api/game/stop`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      })
    } catch (e) {
      console.error('停止游戏请求失败:', e)
    }

    // 清理前端状态
    gameStore.endGame()
    timerStore.reset()
    resetActionLogHistory()

    // 关闭SSE连接
    if (eventSource) {
      eventSource.close()
      eventSource = null
    }

    setTimeout(() => router.push('/'), 500)
  } else {
    confirmState.value = 'end'
  }
}

async function handleResetSettings() {
  if (confirmState.value === 'reset') {
    confirmState.value = null
    gameMenuOpen.value = false

    const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:5001'

    // 1. 先获取原始设置（游戏还在运行，控制器存在）
    let apiInitSettings = null
    try {
      const resp = await fetch(`${apiBaseUrl}/api/game/settings?mode=original`)
      const result = await resp.json()
      if (result.status === 'success') {
        apiInitSettings = result.settings
      }
    } catch (e) {
      console.error('获取原始设置失败:', e)
    }

    // 2. 再停止后端游戏（stop会删除控制器）
    try {
      await fetch(`${apiBaseUrl}/api/game/stop`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      })
    } catch (e) {
      console.error('停止游戏请求失败:', e)
    }

    // 3. 合并完整设置：前端保存的完整配置 + 后端返回的 init_settings
    const fullSettings = JSON.parse(JSON.stringify(gameStore.settings || {}))
    const settingsToSave = {
      ...fullSettings,
      init_settings: apiInitSettings || fullSettings.init_settings
    }

    localStorage.setItem('pendingSetupSettings', JSON.stringify({
      mode: 'original',
      settings: settingsToSave
    }))

    // 4. 清理前端状态
    gameStore.endGame()
    timerStore.reset()
    resetActionLogHistory()

    // 5. 关闭 SSE
    if (eventSource) {
      eventSource.close()
      eventSource = null
    }

    setTimeout(() => router.push('/setup'), 500)
  } else {
    confirmState.value = 'reset'
  }
}

async function handleRestartGame() {
  if (confirmState.value === 'restart') {
    confirmState.value = null
    gameMenuOpen.value = false

    const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:5001'

    // 1. 先获取已解析设置（游戏还在运行，控制器存在）
    let apiInitSettings = null
    try {
      const resp = await fetch(`${apiBaseUrl}/api/game/settings?mode=resolved`)
      const result = await resp.json()
      if (result.status === 'success') {
        apiInitSettings = result.settings
      }
    } catch (e) {
      console.error('获取已解析设置失败:', e)
    }

    // 2. 再停止后端游戏（stop会删除控制器）
    try {
      await fetch(`${apiBaseUrl}/api/game/stop`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      })
    } catch (e) {
      console.error('停止游戏请求失败:', e)
    }

    // 3. 合并完整设置：前端保存的完整配置 + 后端返回的 init_settings
    const fullSettings = JSON.parse(JSON.stringify(gameStore.settings || {}))
    const settingsToSave = {
      ...fullSettings,
      init_settings: apiInitSettings || fullSettings.init_settings
    }

    localStorage.setItem('pendingSetupSettings', JSON.stringify({
      mode: 'resolved',
      settings: settingsToSave
    }))

    // 4. 清理前端状态
    gameStore.endGame()
    timerStore.reset()
    resetActionLogHistory()

    // 5. 关闭 SSE
    if (eventSource) {
      eventSource.close()
      eventSource = null
    }

    setTimeout(() => router.push('/setup'), 500)
  } else {
    confirmState.value = 'restart'
  }
}

async function syncStateAfterActionSubmission(previousVersion) {
  const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:5001'

  for (let i = 0; i < 8; i++) {
    if (stateVersion.value > previousVersion) {
      return true
    }

    await new Promise((resolve) => setTimeout(resolve, i === 0 ? 120 : 180))

    if (stateVersion.value > previousVersion) {
      return true
    }

    try {
      const response = await fetch(`${apiBaseUrl}/api/game/state?client_version=${stateVersion.value}`)
      const result = await response.json()

      if (result.up_to_date) {
        continue
      }

      if (result.status === 'success' && result.state) {
        applyGameViewFullState(result.state)
        updateStateVersion(result.version)

        if (stateVersion.value > previousVersion) {
          return true
        }
      }
    } catch (error) {
      console.error('提交行动后同步最新状态失败:', error)
    }
  }

  return stateVersion.value > previousVersion
}

async function submitActionAndSync(actionId, options = {}) {
  const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:5001'
  const previousVersion = stateVersion.value
  const normalizedSelectionSource = options.selectionSource === 'system' ? 'system' : 'manual'
  const normalizedSelectionStrategy = typeof options.selectionStrategy === 'string' && options.selectionStrategy.trim()
    ? options.selectionStrategy.trim()
    : null
  const normalizedActionId = Number(actionId)

  // 计算选择方式
  let selectionMode = 'player_choice'
  if (normalizedSelectionSource === 'system') {
    if (hasRecommendedAction.value) {
      const normalizedRecommendedActionId = normalizeAvailableActionId(recommendedActionId.value)
      selectionMode = (normalizedRecommendedActionId === normalizedActionId) ? 'accepted' : 'system'
    } else {
      selectionMode = 'system'
    }
  } else {
    if (hasRecommendedAction.value) {
      const normalizedRecommendedActionId = normalizeAvailableActionId(recommendedActionId.value)
      selectionMode = (normalizedRecommendedActionId === normalizedActionId) ? 'accepted' : 'rejected'
    } else {
      selectionMode = 'player_choice'
    }
  }
  pendingSelectionModes.value.push({ actionId: normalizedActionId, selectionMode })

  try {
    const response = await fetch(`${apiBaseUrl}/api/game/action`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        action_id: actionId,
        player_id: currentActionPlayerId.value,
        selection_source: normalizedSelectionSource,
        selection_strategy: normalizedSelectionStrategy,
        selection_mode: selectionMode
      })
    })
    const data = await response.json()

    if (!response.ok || data.status !== 'success') {
      console.error('命令发送失败:', data.error || data.message || response.statusText)
      return { submitted: false, synced: false }
    }

    const synced = await syncStateAfterActionSubmission(previousVersion)
    return { submitted: true, synced }
  } catch (error) {
    console.error('命令发送失败:', error)
    return { submitted: false, synced: false }
  }
}

async function selectAction(action) {
  if (!action || pendingActionId.value !== null) {
    return
  }

  const actionId = Number(action.id)
  if (!Number.isInteger(actionId)) {
    return
  }

  pendingActionId.value = actionId

  try {
    await submitActionAndSync(actionId, {
      selectionSource: 'manual'
    })
  } finally {
    pendingActionId.value = null
  }
}

function getHexPoints(x, y, size) {
  const points = []
  for (let i = 0; i < 6; i++) {
    const angle = (Math.PI / 3) * i - Math.PI / 6
    const px = x + size * Math.cos(angle)
    const py = y + size * Math.sin(angle)
    points.push(`${px},${py}`)
  }
  return points.join(' ')
}

function generateHexMap() {
  const svg = document.getElementById('hex-grid-svg')
  if (!svg) return

  // 完全按照 game_panel.html 的方式：清空SVG并重新创建所有层
  svg.innerHTML = ''

  const { rows, cols, hexSize, rowLetters } = MAP_CONFIG
  const horizontalSpacing = hexSize * Math.sqrt(3)
  const verticalSpacing = hexSize * 1.5

  // 计算网格总尺寸
  const gridWidth = cols * horizontalSpacing + hexSize
  const gridHeight = rows * verticalSpacing + hexSize

  // 设置SVG的viewBox
  svg.setAttribute('viewBox', `0 0 ${gridWidth} ${gridHeight}`)
  svg.setAttribute('preserveAspectRatio', 'xMidYMid meet')

  // 计算起始位置
  const startX = hexSize
  const startY = hexSize + 5

  // 创建组元素，用于整体控制
  const gridGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g')
  gridGroup.setAttribute('id', 'hex-grid-group')
  gridGroup.setAttribute('class', 'hex-grid-group')

  // 创建编号层
  const numbersLayer = document.createElementNS('http://www.w3.org/2000/svg', 'g')
  numbersLayer.setAttribute('id', 'hex-numbers')

  // 创建元素层
  const elementsLayer = document.createElementNS('http://www.w3.org/2000/svg', 'g')
  elementsLayer.setAttribute('id', 'hex-elements')
  elementsLayer.setAttribute('class', 'hex-elements')

  // 创建高亮层
  const highlightLayer = document.createElementNS('http://www.w3.org/2000/svg', 'g')
  highlightLayer.setAttribute('id', 'hex-highlight-layer')

  // 创建悬停层
  const hoverLayer = document.createElementNS('http://www.w3.org/2000/svg', 'g')
  hoverLayer.setAttribute('id', 'hex-hover-layer')

  for (let row = 0; row < rows; row++) {
    for (let col = 0; col < cols; col++) {
      const xOffset = (row % 2 === 0) ? 0 : horizontalSpacing / 2
      const centerX = startX + col * horizontalSpacing + xOffset
      const centerY = startY + row * verticalSpacing
      const rowLetter = rowLetters[row]
      const colNumber = col + 1
      const hexId = `${rowLetter}${colNumber}`

      // 创建六边形 - 与 game_panel.html 完全一致
      const hexagon = document.createElementNS('http://www.w3.org/2000/svg', 'polygon')
      hexagon.setAttribute('class', 'hexagon terrain-water')
      hexagon.setAttribute('id', `hex-${hexId}`)
      hexagon.setAttribute('points', getHexPoints(centerX, centerY, hexSize))
      hexagon.setAttribute('data-position', hexId)
      hexagon.setAttribute('data-row', row)
      hexagon.setAttribute('data-col', col)
      hexagon.setAttribute('data-terrain', '0')
      // 设置默认颜色（水域）
      hexagon.setAttribute('fill', TERRAIN_COLORS[0])
      gridGroup.appendChild(hexagon)

      // 创建编号文本
      const text = document.createElementNS('http://www.w3.org/2000/svg', 'text')
      text.setAttribute('class', 'hex-number')
      text.setAttribute('id', `text-${hexId}`)
      text.setAttribute('x', centerX)
      text.setAttribute('y', centerY - 9)
      text.textContent = hexId
      numbersLayer.appendChild(text)

      // 创建悬停叠加层
      const hoverOverlay = document.createElementNS('http://www.w3.org/2000/svg', 'polygon')
      hoverOverlay.setAttribute('class', 'hover-overlay')
      hoverOverlay.setAttribute('id', `hover-${row}-${col}`)
      hoverOverlay.setAttribute('data-row', row)
      hoverOverlay.setAttribute('data-col', col)
      hoverOverlay.setAttribute('points', getHexPoints(centerX, centerY, hexSize))
      hoverOverlay.addEventListener('mouseenter', function() {
        this.classList.add('hover-active')
        const highlight = document.getElementById(`highlight-${row}-${col}`)
        if (highlight) highlight.classList.add('hover')
      })
      hoverOverlay.addEventListener('mouseleave', function() {
        this.classList.remove('hover-active')
        const highlight = document.getElementById(`highlight-${row}-${col}`)
        if (highlight) highlight.classList.remove('hover')
      })
      hoverLayer.appendChild(hoverOverlay)

      // 创建高亮叠加层
      const highlightOverlay = document.createElementNS('http://www.w3.org/2000/svg', 'polygon')
      highlightOverlay.setAttribute('class', 'highlight-overlay')
      highlightOverlay.setAttribute('id', `highlight-${row}-${col}`)
      highlightOverlay.setAttribute('data-row', row)
      highlightOverlay.setAttribute('data-col', col)
      highlightOverlay.setAttribute('points', getHexPoints(centerX, centerY, hexSize))
      highlightLayer.appendChild(highlightOverlay)
    }
  }

  // 按照正确顺序添加所有层到SVG
  svg.appendChild(gridGroup)
  svg.appendChild(elementsLayer)
  svg.appendChild(highlightLayer)
  svg.appendChild(hoverLayer)
  svg.appendChild(numbersLayer)

  // 应用初始地形
  applyInitialTerrain()

  console.log('六边形地图生成完成')
}

// 应用初始地形 - 与 game_panel.html 完全一致
function applyInitialTerrain() {
  for (let row = 0; row < 9; row++) {
    for (let col = 0; col < 13; col++) {
      setHexTerrain(row, col, INITIAL_TERRAIN[row][col])
    }
  }
}

function setHexTerrain(row, col, terrainType) {
  const hex = document.querySelector(`.hexagon[data-row="${row}"][data-col="${col}"]`)
  if (hex && TERRAIN_COLORS[terrainType] !== undefined) {
    // 移除旧的地形类
    const terrainClasses = Object.values(TERRAIN_TYPES).map(t => `terrain-${t}`)
    hex.classList.remove(...terrainClasses)
    // 添加新的地形类和颜色 - 与 game_panel.html 保持一致
    hex.classList.add(`terrain-${TERRAIN_TYPES[terrainType]}`)
    hex.setAttribute('fill', TERRAIN_COLORS[terrainType])
    hex.setAttribute('data-terrain', terrainType)
    // 特殊处理：水域使用虚线边框
    if (terrainType === 0) {
      hex.style.strokeDasharray = '4,2'
    } else {
      hex.style.strokeDasharray = 'none'
    }
    return true
  }
  return false
}

function setHexHighlights(hexList) {
  // 清除所有现有高亮
  document.querySelectorAll('.highlight-overlay.active, .highlight-overlay.hover').forEach(el => {
    el.classList.remove('active', 'hover')
  })

  if (!hexList || hexList.length === 0) return

  hexList.forEach(coord => {
    if (!Array.isArray(coord) || coord.length !== 2) return
    const [row, col] = coord
    if (row < 0 || row > 8 || col < 0 || col > 12) return
    const highlight = document.getElementById(`highlight-${row}-${col}`)
    if (highlight) highlight.classList.add('active')
  })
}

// ========== 建筑放置功能 ==========

function placeElement(hexRow, hexCol, colorId, buildingId, mode = 'replace', renderToken = null) {
  // 计算位置ID (A1, B2等)
  const positionId = getHexPositionId(hexRow, hexCol)

  // 获取对应的六边形元素
  const hexElement = document.getElementById(`hex-${positionId}`)
  if (!hexElement) {
    console.error(`六边形 ${positionId} 不存在`)
    return false
  }

  // 获取元素层
  const elementsLayer = document.getElementById('hex-elements')
  if (!elementsLayer) {
    console.error('元素层不存在')
    return false
  }

  // 获取六边形的中心坐标
  const bbox = hexElement.getBBox()
  const centerX = bbox.x + bbox.width / 2
  const bottomY = bbox.y + bbox.height * 0.85

  // 替换模式：移除该位置的所有现有元素
  if (mode === 'replace') {
    clearPlacedElementsAt(hexRow, hexCol)
  }

  const normalizedBuildingId = Number(buildingId)
  if (!Number.isInteger(normalizedBuildingId) || normalizedBuildingId <= 0) {
    return false
  }

  const normalizedColorId = Number(colorId) || 0
  const spriteCol = SPECIAL_BUILDINGS.has(normalizedBuildingId) ? 7 : (COLOR_TO_SPRITE_COL[normalizedColorId] ?? 7)
  const spriteRow = BUILDING_TO_SPRITE_ROW[normalizedBuildingId] ?? 0

  const displayWidth = 40
  const displayHeight = 46

  if (renderToken !== null && !isLatestBuildingRender(hexRow, hexCol, renderToken)) {
    return false
  }

  // 创建 foreignObject 包裹 canvas 以绘制精灵图切片
  const foreignObject = document.createElementNS('http://www.w3.org/2000/svg', 'foreignObject')
  foreignObject.setAttribute('class', 'hex-element')
  foreignObject.setAttribute('data-position', positionId)
  foreignObject.setAttribute('data-building-id', String(normalizedBuildingId))
  foreignObject.setAttribute('x', centerX - displayWidth / 2)
  foreignObject.setAttribute('y', bottomY - displayHeight)
  foreignObject.setAttribute('width', displayWidth)
  foreignObject.setAttribute('height', displayHeight)

  const canvas = document.createElement('canvas')
  canvas.setAttribute('width', String(displayWidth))
  canvas.setAttribute('height', String(displayHeight))
  canvas.style.width = `${displayWidth}px`
  canvas.style.height = `${displayHeight}px`
  canvas.style.display = 'block'

  drawSpriteCell(canvas, spriteCol, spriteRow, displayWidth, displayHeight)

  foreignObject.appendChild(canvas)
  elementsLayer.appendChild(foreignObject)
  console.log(`已加载建筑: ${normalizedColorId}-${normalizedBuildingId}`)
  return true
}

function getCityTileIdForCell(row, col) {
  const cell = ensureMapCell(row, col)
  if (!cell.controller || cell.controller < 0) return null

  const player = players.value[cell.controller]
  if (!player) return null

  const assignments = player.city_tile_assignments || {}
  const sac = player.settlements_and_cities || {}
  const posKey = `${row},${col}`

  // 直接检查该坐标是否是已匹配的城市根节点
  if (assignments[posKey]) {
    return assignments[posKey]
  }

  // 检查该坐标在 settlements_and_cities 中的根节点是否已匹配
  if (sac[posKey]) {
    const rootKey = sac[posKey][0]
    if (assignments[rootKey]) {
      return assignments[rootKey]
    }
  }

  return null
}

function placeAnnex(hexRow, hexCol, colorId, renderToken) {
  const positionId = getHexPositionId(hexRow, hexCol)
  const hexElement = document.getElementById(`hex-${positionId}`)
  if (!hexElement) return false

  const elementsLayer = document.getElementById('hex-elements')
  if (!elementsLayer) return false

  const bbox = hexElement.getBBox()
  const centerX = bbox.x + bbox.width / 2
  const bottomY = bbox.y + bbox.height * 0.85

  const displayWidth = 35
  const displayHeight = 40

  // 右下角偏移（约45%宽度，15%高度）
  const offsetX = displayWidth * 0.45
  const offsetY = displayHeight * 0.15

  const x = centerX - displayWidth / 2 + offsetX
  const y = bottomY - displayHeight + offsetY

  if (renderToken !== null && !isLatestBuildingRender(hexRow, hexCol, renderToken)) {
    return false
  }

  const foreignObject = document.createElementNS('http://www.w3.org/2000/svg', 'foreignObject')
  foreignObject.setAttribute('class', 'hex-element hex-annex')
  foreignObject.setAttribute('data-position', positionId)
  foreignObject.setAttribute('x', x)
  foreignObject.setAttribute('y', y)
  foreignObject.setAttribute('width', displayWidth)
  foreignObject.setAttribute('height', displayHeight)

  const canvas = document.createElement('canvas')
  canvas.setAttribute('width', String(displayWidth))
  canvas.setAttribute('height', String(displayHeight))
  canvas.style.width = `${displayWidth}px`
  canvas.style.height = `${displayHeight}px`
  canvas.style.display = 'block'

  // 侧楼固定使用 col=7（特殊建筑列），row=7（第8行，BUILDING_TO_SPRITE_ROW[8]）
  drawSpriteCell(canvas, 7, BUILDING_TO_SPRITE_ROW[8], displayWidth, displayHeight)

  foreignObject.appendChild(canvas)
  elementsLayer.appendChild(foreignObject)
  return true
}

function placeCityTile(hexRow, hexCol, cityTileId, renderToken) {
  const positionId = getHexPositionId(hexRow, hexCol)
  const hexElement = document.getElementById(`hex-${positionId}`)
  if (!hexElement) return false

  const elementsLayer = document.getElementById('hex-elements')
  if (!elementsLayer) return false

  const bbox = hexElement.getBBox()
  const centerX = bbox.x + bbox.width / 2
  const bottomY = bbox.y + bbox.height * 0.85

  const displayWidth = 35
  const displayHeight = 40

  // 右上方偏移（与侧楼对称）
  const offsetX = displayWidth * 0.4
  const offsetY = -displayHeight * 0.4

  const x = centerX - displayWidth / 2 + offsetX
  const y = bottomY - displayHeight + offsetY

  if (renderToken !== null && !isLatestBuildingRender(hexRow, hexCol, renderToken)) {
    return false
  }

  const foreignObject = document.createElementNS('http://www.w3.org/2000/svg', 'foreignObject')
  foreignObject.setAttribute('class', 'hex-element hex-city-tile')
  foreignObject.setAttribute('data-position', positionId)
  foreignObject.setAttribute('x', x)
  foreignObject.setAttribute('y', y)
  foreignObject.setAttribute('width', displayWidth)
  foreignObject.setAttribute('height', displayHeight)

  const canvas = document.createElement('canvas')
  canvas.setAttribute('width', String(displayWidth))
  canvas.setAttribute('height', String(displayHeight))
  canvas.style.width = `${displayWidth}px`
  canvas.style.height = `${displayHeight}px`
  canvas.style.display = 'block'

  const colIndex = CITY_TILE_ID_TO_INDEX[cityTileId]
  if (colIndex !== undefined) {
    drawCityTileSprite(canvas, colIndex, displayWidth, displayHeight)
  }

  foreignObject.appendChild(canvas)
  elementsLayer.appendChild(foreignObject)
  return true
}

// ========== 回合信息功能 ==========

function setRoundScoring(round, x) {
  if (round < 1 || round > 6) return false
  roundStates[round].actualX = x
  roundStates[round].currentX = x
  return true
}

function RoundScoringUpdate(round) {
  if (round < 1 || round > 6) return false
  syncRoundScoringProgress(round + 1)
  return true
}

function emphasizeRound(round) {
  currentRound.value = round >= 1 && round <= 6 ? round : 0
}

function clearAllEmphasis() {
  currentRound.value = 0
}

function setFinalRoundBonus(x) {
  const finalScoringId = Number(x)
  if (!Number.isInteger(finalScoringId) || finalScoringId < 1 || finalScoringId > 4) return false
  roundStates[6].finalScoringId = finalScoringId
  return true
}

function setBonusColumns(xList) {
  if (!Array.isArray(xList)) return false
  const previousBonusByBoosterId = new Map(
    bonusColumns.value.map((bonus) => [bonus.x, bonus])
  )

  bonusColumns.value = xList.map((x) => createBonusColumnState(x, previousBonusByBoosterId.get(x)))
  return true
}

function flipSingleBonusColumn(index) {
  if (index < 0 || index >= bonusColumns.value.length) return false
  // 确保该索引存在
  if (!bonusColumns.value[index]) return false
  bonusColumns.value[index].isFlipped = !bonusColumns.value[index].isFlipped
  return true
}

function normalizeRoundBoosterCoinCount(value) {
  const normalizedValue = Number(value)
  return Number.isInteger(normalizedValue) && normalizedValue > 0 ? normalizedValue : 0
}

function setRoundBoosterCoinCounts(roundBoosterCoinCounts) {
  const normalizedCoinCountMap = new Map()

  if (roundBoosterCoinCounts && typeof roundBoosterCoinCounts === 'object') {
    Object.entries(roundBoosterCoinCounts).forEach(([boosterId, coinCount]) => {
      const normalizedBoosterId = Number(boosterId)
      if (!Number.isInteger(normalizedBoosterId) || normalizedBoosterId <= 0) {
        return
      }

      normalizedCoinCountMap.set(normalizedBoosterId, normalizeRoundBoosterCoinCount(coinCount))
    })
  }

  bonusColumns.value.forEach((bonus) => {
    bonus.coinCount = normalizedCoinCountMap.get(bonus.x) ?? 0
  })

  return true
}

function setSingleRoundBoosterCoinCount(boosterId, coinCount) {
  const normalizedBoosterId = Number(boosterId)
  if (!Number.isInteger(normalizedBoosterId) || normalizedBoosterId <= 0) {
    return false
  }

  const bonusColumn = bonusColumns.value.find((bonus) => bonus.x === normalizedBoosterId)
  if (!bonusColumn) {
    return false
  }

  bonusColumn.coinCount = normalizeRoundBoosterCoinCount(coinCount)
  return true
}

function normalizeBoosterIds(boosterIds) {
  if (!Array.isArray(boosterIds)) {
    return []
  }

  return boosterIds
    .map((boosterId) => Number(boosterId))
    .filter((boosterId) => Number.isInteger(boosterId) && boosterId > 0)
}

function getLatestBoosterId(boosterIds) {
  const normalizedBoosterIds = normalizeBoosterIds(boosterIds)
  return normalizedBoosterIds.length > 0 ? normalizedBoosterIds[normalizedBoosterIds.length - 1] : null
}

function setBonusColumnFlipByBoosterId(boosterId, isFlipped) {
  const normalizedBoosterId = Number(boosterId)
  if (!Number.isInteger(normalizedBoosterId) || normalizedBoosterId <= 0) {
    return false
  }

  const bonusColumn = bonusColumns.value.find((bonus) => bonus.x === normalizedBoosterId)
  if (!bonusColumn) {
    return false
  }

  bonusColumn.isFlipped = isFlipped
  return true
}

function applyPlayerBoosterIdsChange(player, nextBoosterIds) {
  if (!player) return false

  const previousLatestBoosterId = getLatestBoosterId(player.booster_ids)
  const normalizedNextBoosterIds = normalizeBoosterIds(nextBoosterIds)
  const nextLatestBoosterId = getLatestBoosterId(normalizedNextBoosterIds)

  player.booster_ids = [...normalizedNextBoosterIds]
  syncBonusColumnsFromPlayers()
  return previousLatestBoosterId !== nextLatestBoosterId
}

function syncBonusColumnsFromPlayers(playerStates = players.value) {
  const heldBoosterMarkMap = new Map()

  ;(Array.isArray(playerStates) ? playerStates : []).forEach((playerState) => {
    const boosterId = getLatestBoosterId(playerState?.booster_ids)
    if (boosterId === null) {
      return
    }

    const holderMarkId = normalizePlanningCardId(playerState?.planningCardId ?? playerState?.planning_card_id)
    heldBoosterMarkMap.set(boosterId, holderMarkId)
  })

  bonusColumns.value.forEach((bonus) => {
    const isHeld = heldBoosterMarkMap.has(bonus.x)
    bonus.isFlipped = isHeld
    bonus.holderMarkId = isHeld ? heldBoosterMarkMap.get(bonus.x) ?? null : null
  })
}

// ========== SSE 连接 ==========
let eventSource = null
let reconnectTimeout = null
let isComponentActive = false

// 获取全量状态并应用
/*
async function fetchFullState(retries = 10, delay = 500) {
  const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:5001'
  
  for (let i = 0; i < retries; i++) {
    try {
      const response = await fetch(`${apiBaseUrl}/api/game/state?client_version=${stateVersion.value}`)
      const result = await response.json()

      if (result.up_to_date) {
        return true
      }

      if (result.status === 'success' && result.state) {
        applyGameViewFullState(result.state)
        console.log('全量状态已加载, version:', result.version)
        return true
      }
      
      // 如果游戏还没开始，等待后重试
      if (result.status === 'error') {
        console.log(`游戏尚未启动，等待重试 (${i + 1}/${retries})...`)
        await new Promise(resolve => setTimeout(resolve, delay))
      }
    } catch (e) {
      console.error('获取全量状态失败:', e)
      await new Promise(resolve => setTimeout(resolve, delay))
    }
  }
  return false
}

// 应用全量状态到本地
*/

async function fetchFullState(retries = 10, delay = 500) {
  const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:5001'

  for (let i = 0; i < retries; i++) {
    try {
      const response = await fetch(`${apiBaseUrl}/api/game/state?client_version=${stateVersion.value}`)
      const result = await response.json()

      if (result.up_to_date) {
        return true
      }

      if (result.status === 'success' && result.state) {
        applyGameViewFullState(result.state)
        updateStateVersion(result.version)
        console.log('全量状态已加载, version:', result.version)
        return true
      }

      if (result.status === 'error') {
        console.log(`游戏尚未启动，等待重试 (${i + 1}/${retries})...`)
        await new Promise((resolve) => setTimeout(resolve, delay))
      }
    } catch (error) {
      console.error('获取全量状态失败:', error)
      await new Promise((resolve) => setTimeout(resolve, delay))
    }
  }

  return false
}

function applyFullState(state) {
  // 应用元信息
  if (state.meta) {
    applyMetaState(state.meta)
    
    // 根据玩家数量初始化玩家列表
    const numPlayers = state.meta.num_players || 3
    if (players.value.length !== numPlayers) {
      initPlayers(numPlayers)
    }
  }
  
  // 应用游戏设置
  if (state.setup) {
    // 应用轮次计分
    if (state.setup.round_scoring_order) {
      state.setup.round_scoring_order.forEach((scoringId, index) => {
        setRoundScoring(index + 1, scoringId)
      })
    }
    
    // 应用终局计分
    if (state.setup.final_scoring) {
      setFinalRoundBonus(state.setup.final_scoring)
    }
    
    // 应用助推板块
    if (state.setup.selected_round_boosters) {
      setBonusColumns(state.setup.selected_round_boosters)
    }

    if (state.setup.round_booster_coin_counts) {
      setRoundBoosterCoinCounts(state.setup.round_booster_coin_counts)
    }
  }
  
  // 应用玩家状态
  if (state.players && Array.isArray(state.players)) {
    state.players.forEach((p, idx) => {
      if (idx < players.value.length) {
        applyPlayerState(players.value[idx], p)
      }
    })

    syncBonusColumnsFromPlayers(state.players)
  }
  
  // 应用可选行动
  setAvailableActions(state.available_actions)

  setActionLogsFromHistory(state.action_history)
  setFinalScores(state.final_scores)
  
  // 应用地图状态
  if (state.map_state && state.map_state.grid) {
    state.map_state.grid.forEach((row, rowIdx) => {
      row.forEach((cell, colIdx) => {
        if (cell.terrain !== undefined) {
          setHexTerrain(rowIdx, colIdx, cell.terrain)
        }
        if (cell.building_id !== undefined && cell.building_id > 0) {
          // 获取建筑类型名称
          const buildingType = buildingIdToType[cell.building_id]
          if (buildingType) {
            // 获取控制者的规划卡ID来构建图片路径
            const controllerPlayer = state.players?.[cell.controller]
            const planningCardId = controllerPlayer?.planning_card_id || (cell.controller + 1)
            placeElement(rowIdx, colIdx, planningCardId, cell.building_id, 'replace')
          }
        }
      })
    })
  }
}

function applyGameViewFullState(state) {
  if (state.meta) {
    applyMetaState(state.meta)

    const np = state.meta.num_players || 3
    numPlayers.value = np
    if (players.value.length !== np) {
      initPlayers(np)
    }
  }

  if (state.timer_state) {
    timerStore.updateFromTimerState(state.timer_state)
    if (gameMeta.is_game_over) {
      timerStore.dispose()
    }
  }

  if (state.setup) {
    if (state.setup.round_scoring_order) {
      state.setup.round_scoring_order.forEach((scoringId, index) => {
        setRoundScoring(index + 1, scoringId)
      })
    }

    if (state.setup.final_scoring) {
      setFinalRoundBonus(state.setup.final_scoring)
    }

    if (state.setup.selected_round_boosters) {
      setBonusColumns(state.setup.selected_round_boosters)
    }

    if (state.setup.round_booster_coin_counts) {
      setRoundBoosterCoinCounts(state.setup.round_booster_coin_counts)
    }

    if (state.setup.ability_tiles_order) {
      abilityTilesOrder.value = state.setup.ability_tiles_order
    }

    if (state.setup.science_tiles_order) {
      scienceTilesOrder.value = state.setup.science_tiles_order
    }
  }

  if (state.players && Array.isArray(state.players)) {
    state.players.forEach((playerState, idx) => {
      if (idx < players.value.length) {
        applyPlayerState(players.value[idx], playerState)
      }
    })

    syncBonusColumnsFromPlayers(state.players)
  }

  applyDisplayBoardState(state.display_board)

  setAvailableActions(state.available_actions)
  setActionLogsFromHistory(state.action_history)
  setFinalScores(state.final_scores)

  if (state.map_state && state.map_state.grid) {
    resetMapState(state.map_state.grid)
    document.querySelectorAll('.hex-element').forEach((el) => el.remove())

    state.map_state.grid.forEach((row, rowIdx) => {
      row.forEach((cell, colIdx) => {
        if (cell.terrain !== undefined) {
          setHexTerrain(rowIdx, colIdx, cell.terrain)
        }
        renderBuildingForCell(rowIdx, colIdx)
      })
    })
  }
}

function connectSSE() {
  if (!isComponentActive) return

  const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:5001'
  eventSource = new EventSource(`${apiBaseUrl}/stream/game`)

  eventSource.onopen = () => {
    console.log('SSE 连接已建立')
  }

  eventSource.onmessage = (event) => {
    if (!isComponentActive) return
    if (event.data === ':heartbeat') return
    try {
      const message = JSON.parse(event.data)
      handleSSEMessage(message)
    } catch (e) {
      console.error('解析 SSE 消息失败:', e)
    }
  }

  eventSource.onerror = (error) => {
    console.error('SSE 连接错误:', error)
    // 检测连接是否已关闭（后端可能已停止）
    if (eventSource.readyState === EventSource.CLOSED) {
      console.log('后端连接已关闭，清理游戏状态')
      // 清理 localStorage 中的游戏状态
      localStorage.removeItem('gameInProgress')
      localStorage.removeItem('gameSettings')
      // 重置游戏状态
      gameStore.endGame()
      timerStore.reset()
      resetActionLogHistory()
      // 返回首页
      router.push('/')
      return
    }
    // 尝试重连
    reconnectTimeout = setTimeout(() => {
      if (isComponentActive && eventSource) {
        eventSource.close()
        connectSSE()
      }
    }, 3000)
  }
}

function handleSSEMessage(message) {
  const { type, player_id, data } = message

  switch (type) {
    case 'player_state':
      if (player_id >= 0 && player_id < players.value.length) {
        applyPlayerState(players.value[player_id], data)
      }
      break

    case 'global_status':
      // 对局状态统一由 meta 标志推导，避免被独立文案覆盖。
      break

    case 'log':
      appendActionLogEntry(player_id, data)
      break

    case 'actions':
      // 处理可选行动，统一转换为前端格式 {id, text}
      console.log('[SSE] 收到 actions 消息:', message)
      setAvailableActions(data.actions)
      isAiPlayer.value = message.is_ai_player || false
      console.log('[SSE] isAiPlayer 设置为:', isAiPlayer.value)
      break

    case 'terrain_update':
      if (data.row !== undefined && data.col !== undefined && data.terrain_type !== undefined) {
        const cell = ensureMapCell(data.row, data.col)
        cell.terrain = data.terrain_type
        setHexTerrain(data.row, data.col, data.terrain_type)
      }
      break

    case 'building_update':
      // 建筑更新处理
      if (data.hex_row !== undefined && data.hex_col !== undefined) {
        const cell = ensureMapCell(data.hex_row, data.hex_col)

        if (Object.prototype.hasOwnProperty.call(data, 'id')) {
          cell.building_id = data.id
        }

        if (Object.prototype.hasOwnProperty.call(data, 'color')) {
          cell.controller = data.color
        }

        if (Object.prototype.hasOwnProperty.call(data, 'is_neutral')) {
          cell.is_neutral = data.is_neutral
        }

        renderBuildingForCell(data.hex_row, data.hex_col)
      }
      break

    case 'highlight_hex':
      if (data.hex_list && Array.isArray(data.hex_list)) {
        setHexHighlights(data.hex_list)
      }
      break

    case 'round_scoring':
      if (data.round >= 1 && data.round <= 6) {
        setRoundScoring(data.round, data.scoring_id)
      }
      break

    case 'final_scoring':
      if (data.scoring_id >= 1 && data.scoring_id <= 4) {
        setFinalRoundBonus(data.scoring_id)
      }
      break

    case 'bonus_columns':
      if (data.bonus_ids) {
        setBonusColumns(data.bonus_ids)
      }
      break

    case 'round_scoring_update':
      // 回合计分板翻面并强调下一回合
      if (data.round >= 1 && data.round <= 6) {
        RoundScoringUpdate(data.round)
      }
      break

    case 'round_bonus_get':
    case 'round_bonus_back':
      if (data.booster_index !== undefined) {
        flipSingleBonusColumn(data.booster_index)
      }
      break

    case 'full':
      // 全量状态更新 - 来自 SSE 的初始状态
      if (message.state) {
        applyGameViewFullState(message.state)
        updateStateVersion(message.version)
        console.log('SSE 全量状态已加载, version:', message.version)
      }
      break

    case 'incremental':
      // 增量更新 - 应用变更到本地状态
      console.log('[SSE] 收到增量更新, changes:', message.changes?.length || 0)
      if (message.changes) {
        // 检查是否有 available_actions 更新
        const actionsChange = message.changes.find(c => c.path === 'available_actions')
        if (actionsChange) {
          console.log('[SSE] 发现 available_actions 更新:', actionsChange.new_value)
        }
        applyIncrementalChanges(message.changes)
        updateStateVersion(message.version)
      }
      break

    case 'game_over':
      // 游戏结束
      console.log('游戏结束:', data)
      applyMetaState({ is_game_over: true })
      setFinalScores(data?.final_scores)
      setAvailableActions([])
      timerStore.dispose()
      break

    default:
      console.log('未知消息类型:', type, data)
  }
}

// 应用增量变更到本地状态
function applyIncrementalChanges(changes) {
  const pendingBuildingRenders = new Set()

  for (const change of changes) {
    applyGameViewChange(change.path, change.new_value, change.change_type, pendingBuildingRenders)
  }

  pendingBuildingRenders.forEach((cellKey) => {
    const [row, col] = cellKey.split('-').map((value) => Number.parseInt(value, 10))
    if (Number.isInteger(row) && Number.isInteger(col)) {
      renderBuildingForCell(row, col)
    }
  })
}

function queueBuildingRender(pendingBuildingRenders, row, col) {
  pendingBuildingRenders?.add(`${row}-${col}`)
}

function shouldDeferBuildingRender(pendingBuildingRenders) {
  return pendingBuildingRenders instanceof Set
}

function triggerBuildingRender(row, col, pendingBuildingRenders = null) {
  if (shouldDeferBuildingRender(pendingBuildingRenders)) {
    queueBuildingRender(pendingBuildingRenders, row, col)
    return
  }

  renderBuildingForCell(row, col)
}

// 应用单个变更
function applyGameViewChange(path, value, changeType, pendingBuildingRenders = null) {
  if (!path) return

  const keys = path.split(/\.|\[|\]/).filter(k => k !== '')

  if (keys.length >= 2) {
    const lastKey = keys[keys.length - 1]
    if (lastKey === 'added' || lastKey === 'removed') {
      return
    }
  }

  const rootKey = keys[0]

  if (rootKey === 'available_actions') {
    setAvailableActions(value)
    return
  }

  if (rootKey === 'action_history') {
    setActionLogsFromHistory(value)
    return
  }

  if (rootKey === 'final_scores') {
    setFinalScores(changeType === 'removed' ? null : value)
    return
  }

  if (rootKey === 'players' && keys.length >= 2) {
    const playerIdx = Number.parseInt(keys[1], 10)
    if (playerIdx >= 0 && playerIdx < players.value.length) {
      applyPlayerFieldChange(players.value[playerIdx], keys.slice(2), value, changeType)

      // 如果是 settlements_and_cities 或 city_tile_assignments 变更，触发该玩家所有控制地块重渲染
      if (keys.length >= 3) {
        const fieldName = keys[2]
        if (fieldName === 'settlements_and_cities' || fieldName === 'city_tile_assignments') {
          const player = players.value[playerIdx]
          if (player?.controlled_map_ids) {
            for (const mapId of player.controlled_map_ids) {
              if (Array.isArray(mapId) && mapId.length === 2) {
                triggerBuildingRender(mapId[0], mapId[1], pendingBuildingRenders)
              }
            }
          }
        }
      }
    }
    return
  }

  if (rootKey === 'meta' && keys.length >= 2) {
    const key = keys[1]
    applyMetaState({ [key]: value })

    if (key === 'num_players' && value > 0 && players.value.length !== value) {
      initPlayers(value)
    }
    return
  }

  if (rootKey === 'timer_state' && keys.length >= 2) {
    if (!gameMeta.is_game_over) {
      timerStore.updateFromTimerState({ [keys[1]]: value })
    }
    return
  }

  if (rootKey === 'display_board') {
    if (keys.length === 1) {
      applyDisplayBoardState(changeType === 'removed' ? null : value)
      return
    }

    const displayBoardKey = keys[1]
    if (displayBoardKey === 'ability_tile_owners') {
      applyTileOwnerMapChange(abilityTileOwners, keys.slice(2), value, changeType, abilityTilesOrder.value)
    } else if (displayBoardKey === 'science_tile_owners') {
      applyTileOwnerMapChange(scienceTileOwners, keys.slice(2), value, changeType, scienceTilesOrder.value)
    } else if (displayBoardKey === 'city_tile_owners') {
      // 城市板块拥有者变更 - 触发所有玩家控制地块的重渲染
      for (let playerIdx = 0; playerIdx < players.value.length; playerIdx++) {
        const player = players.value[playerIdx]
        if (player?.controlled_map_ids) {
          for (const mapId of player.controlled_map_ids) {
            if (Array.isArray(mapId) && mapId.length === 2) {
              triggerBuildingRender(mapId[0], mapId[1], pendingBuildingRenders)
            }
          }
        }
      }
    } else if (displayBoardKey === 'science_tracks' && keys.length >= 3) {
      const trackType = keys[2]
      if (scienceTracks[trackType]) {
        if (keys.length === 3) {
          if (changeType !== 'removed' && value && typeof value === 'object') {
            scienceTracks[trackType].is_crowned = value.is_crowned ?? false
            scienceTracks[trackType].meeples = Array.isArray(value.meeples) ? [...value.meeples] : [-1, -1, -1, -1]
          }
        } else if (keys[3] === 'is_crowned') {
          scienceTracks[trackType].is_crowned = changeType === 'removed' ? false : Boolean(value)
        } else if (keys[3] === 'meeples' && keys.length >= 5) {
          const meepleIdx = parseInt(keys[4], 10)
          if (!Number.isNaN(meepleIdx) && meepleIdx >= 0 && meepleIdx < 4) {
            scienceTracks[trackType].meeples[meepleIdx] = changeType === 'removed' ? -1 : Number(value)
          }
        }
      }
    }
    return
  }

  if (rootKey === 'map_state' && keys.length >= 5 && keys[1] === 'grid') {
    const row = Number.parseInt(keys[2], 10)
    const col = Number.parseInt(keys[3], 10)
    const field = keys[4]
    const cell = ensureMapCell(row, col)

    cell[field] = value

    if (field === 'terrain') {
      setHexTerrain(row, col, value)
      return
    }

    if (field === 'building_id' || field === 'controller' || field === 'is_neutral' || field === 'has_annex') {
      triggerBuildingRender(row, col, pendingBuildingRenders)
    }
    return
  }

  if (rootKey === 'setup' && keys.length >= 2) {
    const setupKey = keys[1]
    if (setupKey === 'round_scoring_order' && Array.isArray(value)) {
      value.forEach((scoringId, index) => {
        setRoundScoring(index + 1, scoringId)
      })
    } else if (setupKey === 'final_scoring' && value > 0) {
      setFinalRoundBonus(value)
    } else if (setupKey === 'selected_round_boosters' && Array.isArray(value)) {
      setBonusColumns(value)
      syncBonusColumnsFromPlayers()
    } else if (setupKey === 'ability_tiles_order' && Array.isArray(value)) {
      abilityTilesOrder.value = value
      replaceTileOwnerMap(abilityTileOwners, abilityTileOwners, value)
    } else if (setupKey === 'science_tiles_order' && Array.isArray(value)) {
      scienceTilesOrder.value = value
      replaceTileOwnerMap(scienceTileOwners, scienceTileOwners, value)
    } else if (setupKey === 'round_booster_coin_counts') {
      if (keys.length === 2 && value && typeof value === 'object') {
        setRoundBoosterCoinCounts(value)
      } else if (keys.length >= 3) {
        setSingleRoundBoosterCoinCount(keys[2], changeType === 'removed' ? 0 : value)
      }
    }
  }
}

function applySingleChange(path, value, changeType) {
  const keys = path.split(/\.|\[|\]/).filter(k => k !== '')

  // 处理 set 类型的增量更新 (added/removed)
  if (keys.length >= 2) {
    const lastKey = keys[keys.length - 1]
    if (lastKey === 'added' || lastKey === 'removed') {
      // 暂不处理集合类型的增量更新
      return
    }
  }

  // 根据路径更新对应的本地状态
  const rootKey = keys[0]

  // 处理 available_actions - 直接替换整个列表
  if (rootKey === 'available_actions') {
    setAvailableActions(value)
    return
  }

  if (rootKey === 'action_history') {
    setActionLogsFromHistory(value)
    return
  }

  if (rootKey === 'final_scores') {
    setFinalScores(changeType === 'removed' ? null : value)
    return
  }

  if (rootKey === 'players' && keys.length >= 2) {
    // 更新玩家状态
    const playerIdx = parseInt(keys[1])
    if (playerIdx >= 0 && playerIdx < players.value.length) {
      const player = players.value[playerIdx]
      const remainingKeys = keys.slice(2)

      // 特殊处理规划卡ID更新
      if (remainingKeys.length === 1 && remainingKeys[0] === 'planning_card_id') {
        setPlayerPlanningCard(player, value)
        return
      }

      // 特殊处理派系ID更新
      if (remainingKeys.length === 1 && remainingKeys[0] === 'faction_id') {
        setPlayerFaction(player, value)
        return
      }

      // 其他字段使用普通更新
      updateNestedObject(player, remainingKeys, value)
    }
  } else if (rootKey === 'meta' && keys.length >= 2) {
    // 更新元信息
    const key = keys[1]
    if (key === 'current_player_id') {
      // 可以在这里添加当前玩家指示器的更新
    } else if (key === 'num_players') {
      // 玩家数量变化时重新初始化玩家列表
      if (value > 0 && players.value.length !== value) {
        initPlayers(value)
      }
    }
  } else if (rootKey === 'map_state' && keys.length >= 4) {
    // 更新地图状态
    if (keys[1] === 'grid') {
      const row = parseInt(keys[2])
      const col = parseInt(keys[3])
      if (keys.length >= 5) {
        const field = keys[4]
        if (field === 'terrain') {
          setHexTerrain(row, col, value)
        } else if (field === 'building_id') {
          // 建筑更新 - 需要获取controller信息来放置正确的建筑图片
          if (value > 0) {
            const buildingType = buildingIdToType[value]
            if (buildingType) {
              // 尝试从当前地图状态获取controller
              const cell = mapState.grid?.[row]?.[col]
              const controller = cell?.controller ?? 0
              const planningCardId = players.value[controller]?.planningCardId ?? (controller + 1)
              placeElement(row, col, planningCardId, value, 'replace')
            }
          }
        } else if (field === 'controller') {
          // 控制者更新 - 单独更新时可能需要重新渲染建筑
        }
      }
    }
  } else if (rootKey === 'setup' && keys.length >= 2) {
    // 更新游戏设置
    const setupKey = keys[1]
    if (setupKey === 'round_scoring_order' && Array.isArray(value)) {
      // 轮次计分顺序更新
      value.forEach((scoringId, index) => {
        setRoundScoring(index + 1, scoringId)
      })
    } else if (setupKey === 'final_scoring' && value > 0) {
      // 最终计分更新
      setFinalRoundBonus(value)
    } else if (setupKey === 'selected_round_boosters' && Array.isArray(value)) {
      // 回合助推器更新
      setBonusColumns(value)
    }
  }
}

// 递归更新嵌套对象
function updateNestedObject(obj, keys, value) {
  let current = obj
  for (let i = 0; i < keys.length - 1; i++) {
    const key = keys[i]
    if (current[key] === undefined) {
      current[key] = {}
    }
    current = current[key]
  }
  const lastKey = keys[keys.length - 1]
  current[lastKey] = value
}

// 点击外部关闭菜单
function handleDocumentClick(e) {
  const tooltipContainer = e.target.closest('.terrain-tooltip-container')
  const actionLogFilterContainer = e.target.closest('.action-log-filter')
  if (!tooltipContainer && terrainTooltipOpen.value) {
    terrainTooltipOpen.value = false
  }
  const modalContent = e.target.closest('.modal-content')
  if (!actionLogFilterContainer && !modalContent && actionLogFilterModalOpen.value) {
    actionLogFilterModalOpen.value = false
  }
}

onMounted(async () => {
  isComponentActive = true
  gameStore.loadFromStorage()
  document.addEventListener('click', handleDocumentClick)
  // 初始化地图
  generateHexMap()
  // 先获取全量状态
  await fetchFullState()
  await nextTick()
  setupPlayerCardResizeObserver()
  // setupActionContentResizeObserver() // 已停用：不再自动检测高度溢出
  setupRoundInfoResizeObserver()
  updateRoundInfoLayout()
  setupScienceAbilityResizeObserver()
  updateScienceAbilityLayout()
  // scheduleActionOverflowMeasurement({ resetExpanded: true }) // 已停用：默认全部展开
  // 建立 SSE 连接
  connectSSE()
})

onUnmounted(() => {
  isComponentActive = false
  document.removeEventListener('click', handleDocumentClick)
  clearTimeout(terrainTooltipTimeout)
  clearTimeout(reconnectTimeout)
  clearEntityPreviewTimer()
  clearEntityPreviewHideTimer()
  cancelActionOverflowMeasurement()
  if (actionContentResizeObserver) {
    actionContentResizeObserver.disconnect()
    actionContentResizeObserver = null
  }
  if (roundInfoResizeObserver) {
    roundInfoResizeObserver.disconnect()
    roundInfoResizeObserver = null
  }
  if (playerCardResizeObserver) {
    playerCardResizeObserver.disconnect()
    playerCardResizeObserver = null
  }
  if (scienceAbilityResizeObserver) {
    scienceAbilityResizeObserver.disconnect()
    scienceAbilityResizeObserver = null
  }
  cancelPlayerCardSizeUpdates()
  playerCardRefs.clear()
  if (eventSource) {
    eventSource.close()
    eventSource = null
  }
  timerStore.dispose()
})
</script>

<style scoped>
@import '../assets/variables.css';

.game-page {
  --game-page-padding: 24px 48px 36px 48px;
  --game-column-gap: 18px;
  --game-section-inset: 0px;
  --game-content-gap: 16px;
  width: 100%;
  height: calc(100vh - 56px);
  background-color: var(--bg-primary);
  color: var(--text-primary);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  padding: var(--game-page-padding);
  box-sizing: border-box;
}

.main-container {
  display: flex;
  gap: var(--game-column-gap);
  flex: 1;
  height: 100%;
  overflow: hidden;
}

/* ===== 左侧：玩家面板 ===== */
.players-monitor {
  width: 17%;
  height: 100%;
  overflow: hidden;
  background-color: #171717;
  border: 1px solid var(--border);
  border-radius: var(--border-radius);
}

.monitor-header {
  padding: 11px calc(var(--panel-padding) + 1px);
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
  border: none;
  margin-left: var(--game-section-inset);
  margin-right: var(--game-section-inset);
  margin-bottom: var(--game-section-inset);
  background-color: #171717;
}

.player-grid {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 12px 10px;
  flex: 1;
  overflow-y: auto;
  max-height: 100%;
}

.player-grid::-webkit-scrollbar {
  display: none;
}

.player-card {
  --player-header-height: 42px;
  --player-stat-icon-size: 15px;
  --player-stat-icon-box-size: 18px;
  --player-building-icon-size: 18px;
  --player-stat-gap: 4px;
  --player-stat-value-size: 0.94rem;
  --player-stat-row-height: 31px;
  background-color: var(--bg-tertiary);
  border-radius: var(--border-radius);
  border: 1px solid var(--border);
  position: relative;
  overflow: visible;
  isolation: isolate;
  display: flex;
  flex-direction: column;
  height: auto;
  min-height: 0;
  flex-shrink: 0;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.player-card-ring {
  position: absolute;
  left: 0;
  top: 0;
  z-index: 0;
  pointer-events: none;
  overflow: visible;
  shape-rendering: auto;
  transform: translateZ(0);
  backface-visibility: hidden;
}

.player-card:hover {
  border-color: var(--accent);
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.3);
}

.player-card-ring-flow-aura,
.player-card-ring-flow-soft,
.player-card-ring-flow-mid,
.player-card-ring-flow-core,
.player-card-ring-flow-bright {
  fill: none;
  vector-effect: non-scaling-stroke;
  stroke-linejoin: round;
  stroke-linecap: round;
  animation-timing-function: linear;
  animation-iteration-count: infinite;
  will-change: stroke-dashoffset;
}

.player-card-ring-flow-aura {
  stroke: rgba(0, 123, 255, 0.26);
  stroke-width: 4;
  stroke-dasharray: 40 60;
  stroke-dashoffset: 0;
  animation-name: player-card-ring-travel-aura;
  animation-duration: 12s;
  opacity: 0.26;
  filter:
    drop-shadow(0 0 3px rgba(77, 166, 255, 0.28))
    drop-shadow(0 0 6px rgba(0, 123, 255, 0.12));
}

.player-card-ring-flow-soft {
  stroke: rgba(0, 123, 255, 0.42);
  stroke-width: 3.5;
  stroke-dasharray: 33 67;
  stroke-dashoffset: -3.5;
  animation-name: player-card-ring-travel-soft;
  animation-duration: 12s;
  opacity: 0.46;
}

.player-card-ring-flow-mid {
  stroke: rgba(77, 166, 255, 0.74);
  stroke-width: 3.2;
  stroke-dasharray: 26 74;
  stroke-dashoffset: -7;
  animation-name: player-card-ring-travel-mid;
  animation-duration: 12s;
  opacity: 0.7;
}

.player-card-ring-flow-core {
  stroke: rgba(120, 197, 255, 0.92);
  stroke-width: 3;
  stroke-dasharray: 19 81;
  stroke-dashoffset: -10.5;
  animation-name: player-card-ring-travel-core;
  animation-duration: 12s;
  opacity: 0.88;
}

.player-card-ring-flow-bright {
  stroke: rgba(215, 239, 255, 0.98);
  stroke-width: 2.6;
  stroke-dasharray: 12 88;
  stroke-dashoffset: -14;
  animation-name: player-card-ring-travel-bright;
  animation-duration: 12s;
  opacity: 0.98;
}

.player-card.is-current-action-player {
  border-color: var(--border);
  box-shadow: none;
}

.player-card.is-transitioning .player-card-ring {
  contain: paint;
}

.player-card.is-transitioning .player-card-ring-flow-aura {
  filter: none;
  opacity: 0.18;
}

@keyframes player-card-ring-travel-aura {
  from {
    stroke-dashoffset: 0;
  }

  to {
    stroke-dashoffset: -100;
  }
}

@keyframes player-card-ring-travel-soft {
  from {
    stroke-dashoffset: -3.5;
  }

  to {
    stroke-dashoffset: -103.5;
  }
}

@keyframes player-card-ring-travel-mid {
  from {
    stroke-dashoffset: -7;
  }

  to {
    stroke-dashoffset: -107;
  }
}

@keyframes player-card-ring-travel-core {
  from {
    stroke-dashoffset: -10.5;
  }

  to {
    stroke-dashoffset: -110.5;
  }
}

@keyframes player-card-ring-travel-bright {
  from {
    stroke-dashoffset: -14;
  }

  to {
    stroke-dashoffset: -114;
  }
}

.player-card.collapsed {
  min-height: var(--player-header-height);
}

.player-card.collapsed .player-status {
  max-height: 0;
  opacity: 0;
}

.player-header {
  padding: 6px 12px;
  background-color: transparent;
  position: relative;
  z-index: 1;
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  user-select: none;
  transition: background-color 0.2s;
  flex-shrink: 0;
  height: var(--player-header-height);
  box-sizing: border-box;
}

.player-header:hover {
  background-color: rgba(255, 255, 255, 0.02);
}

.player-header-left {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
  flex: 1;
}

.player-header-right {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
  margin-left: auto;
}

.planning-card-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 15px;
  height: 15px;
  flex-shrink: 0;
}

.planning-card-circle {
  display: block;
  width: 13px;
  height: 13px;
  border-radius: 50%;
  background-color: transparent;
  border: 1px solid transparent;
  box-shadow: inset 0 0 0 1px rgba(10, 10, 10, 0.45);
  cursor: default;
  transition: background-color 0.3s ease, border-color 0.16s ease, box-shadow 0.16s ease;
}

.planning-card-circle.is-visible {
  border-color: rgba(255, 255, 255, 0.35);
  cursor: zoom-in;
}

.planning-card-circle.is-visible:hover,
.planning-card-circle.is-visible:focus-visible {
  outline: none;
  border-color: rgba(149, 196, 230, 0.62);
  box-shadow:
    0 0 0 3px rgba(72, 122, 168, 0.2),
    inset 0 0 0 1px rgba(255, 255, 255, 0.1);
}

.faction-badge {
  --faction-badge-height: 27px;
  --faction-badge-border: 1px;
  --faction-badge-gap: 3px;
  --faction-badge-avatar-size: calc(var(--faction-badge-height) - var(--faction-badge-border) * 2 - var(--faction-badge-gap) * 2);
  --faction-badge-text-gap: 6px;
  display: inline-grid;
  grid-template-columns: var(--faction-badge-avatar-size) auto;
  column-gap: var(--faction-badge-text-gap);
  align-items: center;
  min-width: 0;
  height: var(--faction-badge-height);
  padding: var(--faction-badge-gap) 8px var(--faction-badge-gap) var(--faction-badge-gap);
  border-radius: 999px;
  background: rgba(14, 22, 34, 0.78);
  border: var(--faction-badge-border) solid rgba(120, 160, 200, 0.28);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.05);
  box-sizing: border-box;
}

.faction-badge-avatar {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: var(--faction-badge-avatar-size);
  height: var(--faction-badge-avatar-size);
  border-radius: 50%;
  overflow: hidden;
  background: #0f1724;
  border: 1px solid rgba(120, 160, 200, 0.35);
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.08);
  box-sizing: border-box;
  cursor: zoom-in;
  flex-shrink: 0;
  transition: border-color 0.16s ease, box-shadow 0.16s ease;
}

.faction-badge-avatar:hover,
.faction-badge-avatar:focus-visible {
  outline: none;
  border-color: rgba(149, 196, 230, 0.62);
  box-shadow:
    0 0 0 3px rgba(72, 122, 168, 0.2),
    inset 0 0 0 1px rgba(255, 255, 255, 0.1);
}

.faction-badge-avatar-image {
  display: block;
  width: 100%;
  height: 100%;
  border-radius: inherit;
  background-repeat: no-repeat;
}

.faction-badge-name {
  max-width: 5em;
  overflow: hidden;
  color: var(--text-primary);
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 0.7rem;
  font-weight: 600;
  line-height: 1;
}

.palace-tile-badge {
  --palace-tile-badge-size: 22px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  position: relative;
  width: var(--palace-tile-badge-size);
  height: var(--palace-tile-badge-size);
  border-radius: 50%;
  background: rgba(18, 27, 40, 0.9);
  border: 1px solid rgba(120, 160, 200, 0.32);
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.08);
  box-sizing: border-box;
  color: #dcecfb;
  font-size: 0.62rem;
  font-weight: 700;
  line-height: 1;
  font-variant-numeric: tabular-nums;
  cursor: zoom-in;
  flex-shrink: 0;
  transition: border-color 0.16s ease, box-shadow 0.16s ease, color 0.16s ease;
}

.palace-tile-badge-value {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 0;
}

.palace-tile-badge.is-hidden-placeholder {
  visibility: hidden;
  pointer-events: none;
  cursor: default;
}

.palace-tile-badge-status {
  position: absolute;
  top: -1px;
  right: -2px;
  color: #ef4444;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  text-shadow: 0 1px 4px rgba(0, 0, 0, 0.55);
}

.palace-tile-badge-status i {
  font-size: 8px;
  line-height: 1;
}

.palace-tile-badge:hover,
.palace-tile-badge:focus-visible {
  outline: none;
  border-color: rgba(149, 196, 230, 0.62);
  box-shadow:
    0 0 0 3px rgba(72, 122, 168, 0.2),
    inset 0 0 0 1px rgba(255, 255, 255, 0.1);
  color: #ffffff;
}

.player-title {
  font-size: 0.92rem;
  font-weight: 600;
  color: var(--text-primary);
  display: flex;
  align-items: center;
  gap: 3px;
  min-width: 0;
}

.player-name {
  display: inline-flex;
  align-items: center;
  width: 3.15rem;
  white-space: nowrap;
  flex-shrink: 0;
  font-variant-numeric: tabular-nums;
}

.entity-preview {
  position: fixed;
  z-index: 1200;
  padding: 8px;
  border-radius: 16px;
  background: rgba(28, 28, 28, 0.96);
  border: 1px solid rgba(255, 255, 255, 0.12);
  box-shadow: 0 18px 36px rgba(0, 0, 0, 0.32);
  backdrop-filter: blur(10px);
  box-sizing: border-box;
}

.entity-preview-media {
  position: relative;
}

.entity-preview-image {
  position: relative;
  width: 100%;
  height: var(--entity-preview-image-height);
  border-radius: 12px;
  background-color: transparent;
  overflow: hidden;
}

.entity-preview-image.is-inactive {
  filter: saturate(0.82);
}

.entity-preview-image-layer {
  position: absolute;
  inset: 0;
  background-repeat: no-repeat;
  background-color: transparent;
}

.entity-preview-image-overlay {
  position: absolute;
  inset: 0;
  border-radius: 12px;
  background: rgba(113, 120, 132, 0.42);
  display: flex;
  align-items: center;
  justify-content: center;
}

.entity-preview-status-icon {
  color: #ef4444;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  text-shadow: 0 6px 18px rgba(0, 0, 0, 0.36);
}

.entity-preview-status-icon i {
  font-size: 4rem;
  line-height: 1;
}

.entity-preview-name {
  margin-top: 8px;
  color: var(--text-primary);
  text-align: center;
  font-size: 0.85rem;
  font-weight: 600;
  letter-spacing: 0.02em;
  line-height: 1.3;
}

.player-score {
  background-color: transparent;
  color: var(--accent);
  padding: 0;
  border: none;
  font-weight: 700;
  font-size: 1.04rem;
  flex-shrink: 0;
  line-height: 1;
  display: inline-flex;
  align-items: center;
  height: 100%;
  width: 1.6rem;
  justify-content: flex-end;
  font-variant-numeric: tabular-nums;
}

.player-timer {
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  justify-content: flex-end;
  height: 100%;
}

.player-status {
  flex: 0 0 auto;
  overflow: hidden;
  max-height: 172px;
  position: relative;
  z-index: 1;
  transition: max-height 0.28s ease, opacity 0.22s ease;
  opacity: 1;
  will-change: max-height, opacity;
}

.player-stats {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 8px 12px 10px;
  overflow: visible;
  background-color: transparent;
}

.player-stats::-webkit-scrollbar {
  width: 6px;
}

.stat-row {
  display: grid;
  grid-template-columns: repeat(var(--stat-columns), minmax(0, 1fr));
  align-items: center;
  min-height: var(--player-stat-row-height);
  position: relative;
}

.stat-row + .stat-row::before {
  content: '';
  position: absolute;
  top: -2px;
  left: 10px;
  right: 10px;
  height: 1px;
  background: linear-gradient(
    90deg,
    transparent 0%,
    rgba(255, 255, 255, 0.025) 14%,
    rgba(255, 255, 255, 0.055) 50%,
    rgba(255, 255, 255, 0.025) 86%,
    transparent 100%
  );
  transform: scaleY(0.5);
  transform-origin: center;
  pointer-events: none;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-width: 0;
  margin: 0;
  padding: 0 2px;
}

.stat-row.is-building-row .stat-content {
  gap: var(--player-stat-gap);
}

.stat-row.is-wide-row .stat-content {
  gap: var(--player-stat-gap);
}

.stat-content {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--player-stat-gap);
  width: 100%;
}

.stat-icon-wrapper {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: var(--player-stat-icon-box-size);
  height: var(--player-stat-icon-box-size);
  line-height: 1;
  flex-shrink: 0;
}

.stat-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  font-size: var(--player-stat-icon-size);
  flex-shrink: 0;
  text-align: center;
  line-height: 1;
}

.stat-icon::before {
  display: block;
  line-height: 1;
}

.stat-image {
  display: block;
  width: var(--player-building-icon-size);
  height: var(--player-building-icon-size);
  object-fit: contain;
  flex-shrink: 0;
}

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
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: var(--player-stat-icon-box-size);
  height: var(--player-stat-icon-box-size);
  flex-shrink: 0;
}

.magic-disc {
  display: block;
  width: var(--player-stat-icon-size);
  height: var(--player-stat-icon-size);
  border-radius: 50%;
  background: #e4e4e4;
  flex-shrink: 0;
}

.magic-disc-label {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  font-weight: 700;
  color: #0a0a0a;
  line-height: 1;
  font-variant-numeric: tabular-nums;
}

.stat-value {
  font-size: var(--player-stat-value-size);
  font-weight: 700;
  color: var(--text-primary);
  white-space: nowrap;
  font-variant-numeric: tabular-nums;
  line-height: 1;
}

.stat-badge {
  position: absolute;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  top: -5px;
  right: -7px;
  min-width: 13px;
  height: 13px;
  padding: 0 2px;
  border-radius: 999px;
  background: rgba(22, 28, 39, 0.96);
  border: 1px solid rgba(92, 190, 240, 0.65);
  color: #dcecfb;
  font-size: 0.54rem;
  font-weight: 700;
  line-height: 1;
  text-align: center;
  box-sizing: border-box;
}

.log-item {
  background-color: var(--bg-tertiary);
  border-left: 2px solid var(--accent);
  padding: 8px 10px;
  margin-bottom: 6px;
  border-radius: 0 10px 10px 0;
  font-family: 'Consolas', monospace;
  white-space: pre-wrap;
  word-wrap: break-word;
  transition: background-color 0.2s ease, border-color 0.2s ease;
}

.log-item[data-color='blue'] { border-left-color: #007bff; }
.log-item[data-color='orange'] { border-left-color: #f1a61b; }
.log-item[data-color='purple'] { border-left-color: #ad32ef; }
.log-item[data-color='pink'] { border-left-color: #e57ea9; }
.log-item[data-color='celeste'] { border-left-color: #82d8d0; }

.log-item:hover {
  background-color: rgba(77, 166, 255, 0.1);
}

/* ===== 中间区域：游戏区域 ===== */
.middle-section {
  background-color: #171717;
  border-radius: var(--border-radius);
  width: 40%;
  height: 100%;
  display: flex;
  flex-direction: column;
  border: 1px solid var(--border);
  overflow: hidden;
}

.middle-header {
  padding: 11px calc(var(--panel-padding) + 1px);
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
  border: none;
  margin-left: var(--game-section-inset);
  margin-right: var(--game-section-inset);
  margin-bottom: var(--game-section-inset);
  background-color: #171717;
}

.game-grid {
  display: flex;
  flex-direction: column;
  gap: var(--game-content-gap);
  padding: var(--game-content-gap);
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
  padding: 9px calc(var(--panel-padding) + 1px);
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
  border-radius: 10px;
  padding: 10px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 1000;
  min-width: 160px;
  opacity: 0;
  visibility: hidden;
  transform: translateY(-8px);
  transition: all 0.3s ease;
  margin-top: 6px;
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
  margin: 0 0 10px 0;
  font-size: 0.85rem;
  color: var(--text-primary);
  text-align: center;
  border-bottom: 1px solid var(--border);
  padding-bottom: 6px;
}

.color-ring-wrapper {
  display: flex;
  justify-content: center;
  margin-bottom: 12px;
}

.legend {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px 12px;
  justify-items: center;
  justify-content: center;
  margin: 0 auto;
  max-width: 220px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  width: 100%;
  justify-content: center;
  font-size: 0.8rem;
}

.color-box {
  width: 12px;
  height: 12px;
  border-radius: 2px;
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
  opacity: 1;
  position: relative;
  z-index: 0;
  transition: opacity 0.3s ease;
}

.game-card.collapsed .map-board-status {
  opacity: 0;
}

.map-container-full {
  width: 100%;
  max-height: 100%;
  padding: 12px 20px;
  background-color: transparent;
  overflow: hidden;
  box-sizing: border-box;
}

#hex-grid-svg {
  display: block;
  width: 100%;
  height: 100%;
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
  align-items: flex-start;
  gap: 24px;
}

.left-column {
  flex: 0 0 30%;
  width: 30%;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  align-content: start;
  min-width: 0;
}

.grid-cell {
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
  width: 100%;
  height: auto;
  aspect-ratio: 232 / 134;
  transition: all 0.3s ease;
}

.grid-cell:focus-visible,
.bonus-cell:focus-visible {
  outline: none;
  box-shadow: 0 0 0 3px rgba(72, 122, 168, 0.26);
}

.grid-cell[tabindex="0"],
.bonus-cell[tabindex="0"] {
  cursor: zoom-in;
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
  overflow: hidden;
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

.grid-cell.current-round .card-face {
  padding: 0;
  box-sizing: border-box;
}

.grid-cell.current-round .scoring-image,
.grid-cell.current-round .base-image,
.grid-cell.current-round .overlay-image {
  transform: scale(0.8);
  transform-origin: center;
}

.grid-cell.current-round .base-image,
.grid-cell.current-round .overlay-image {
  inset: 0;
}

.scoring-image,
.base-image,
.overlay-image,
.bonus-sprite-image {
  display: block;
  background-repeat: no-repeat;
  background-color: transparent;
}

.scoring-image,
.base-image,
.overlay-image {
  width: 100%;
  max-width: 100%;
  max-height: 100%;
  aspect-ratio: 232 / 134;
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
  inset: 0;
  margin: auto;
  pointer-events: none;
}

.overlay-image {
  z-index: 2;
}

.round-label {
  position: absolute;
  bottom: 2px;
  font-size: 0.62rem;
  color: #ededed;
  background: rgba(0, 0, 0, 0.5);
  padding: 1px 4px;
  border-radius: 999px;
  z-index: 30;
  pointer-events: none;
  line-height: 1.2;
  letter-spacing: -0.01em;
}

.right-column {
  flex: 1 1 auto;
  width: 70%;
  display: flex;
  gap: 8px;
  padding: 0 6px;
  min-height: 100px;
  box-sizing: border-box;
  overflow: hidden;
  min-width: 0;
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

.bonus-cell img,
.bonus-cell .bonus-sprite-image {
  width: 100%;
  height: 100%;
  box-sizing: border-box;
}

.bonus-cell .bonus-holder-mark {
  position: absolute;
  top: 15%;
  left: 47.5%;
  width: 135%;
  height: auto;
  aspect-ratio: 90 / 108;
  transform: translate(-50%, -50%);
  z-index: 6;
  pointer-events: none;
  object-fit: contain;
}

.bonus-cell .bonus-coin-badge {
  position: absolute;
  top: 4px;
  right: 4px;
  display: inline-flex;
  align-items: center;
  gap: 3px;
  padding: 3px 6px;
  border-radius: 999px;
  background: rgba(25, 32, 44, 0.92);
  border: 1px solid rgba(247, 199, 74, 0.52);
  color: #ffe08a;
  box-shadow: 0 3px 10px rgba(0, 0, 0, 0.28);
  z-index: 11;
  pointer-events: none;
  line-height: 1;
  font-variant-numeric: tabular-nums;
}

.bonus-cell .bonus-coin-badge i {
  font-size: 0.62rem;
}

.bonus-cell .bonus-coin-badge-text {
  font-size: 0.62rem;
  font-weight: 800;
  letter-spacing: -0.02em;
}

.bonus-label {
  position: absolute;
  bottom: 3px;
  left: 3px;
  width: 24px;
  height: 24px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 0.58rem;
  font-weight: 800;
  color: #f7fbff;
  background: var(--accent);
  border: 1px solid var(--accent-light);
  border-radius: 50%;
  box-shadow: 0 3px 8px rgba(0, 0, 0, 0.22);
  z-index: 10;
  pointer-events: none;
  text-align: center;
  white-space: nowrap;
  line-height: 1;
  letter-spacing: -0.03em;
  font-variant-numeric: tabular-nums;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.18);
}

/* 科学能力 */
.game-status {
  flex: 1;
  display: flex;
  overflow: hidden;
  min-height: 0;
  transition: opacity 0.3s ease;
  opacity: 1;
}

.game-card.collapsed .game-status,
.game-card.collapsed .science-ability-status {
  opacity: 0;
}

.science-ability-status {
  flex: 1;
  overflow: hidden;
  min-height: 0;
  transition: opacity 0.3s ease;
  opacity: 1;
  padding: 14px 22px;
}

.science-ability-layout {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 18px;
  min-height: 0;
}

.science-ability-left {
  flex: 0 0 auto;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  min-height: 0;
  min-width: 0;
}

.left-boards-stack {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  max-width: 100%;
  max-height: 100%;
  width: auto;
  height: auto;
}

.left-boards-stack.left-boards-stack-3 {
  aspect-ratio: 850 / 846;
}

.left-boards-stack.left-boards-stack-4 {
  aspect-ratio: 850 / 1037;
}

.left-boards-stack.left-boards-stack-5 {
  aspect-ratio: 850 / 987;
}

.science-board-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  width: 100%;
  flex: 0 0 auto;
  border-radius: 12px 12px 0 0;
}

.ability-board-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  width: 100%;
  flex: 0 0 auto;
  border-radius: 0 0 8px 8px;
}

.science-board {
  position: relative;
  background-size: contain;
  background-repeat: no-repeat;
  background-position: center;
  width: 100%;
  height: auto;
  border-radius: 12px 12px 0 0;
  overflow: hidden;
}

.science-board.science-board-3 {
  aspect-ratio: 850 / 493;
}

.science-board.science-board-3.crop-top {
  aspect-ratio: 850 / 443;
}

.science-board.science-board-4,
.science-board.science-board-5 {
  aspect-ratio: 850 / 634;
}

.science-board.science-board-5.crop-top {
  aspect-ratio: 850 / 584;
}

.science-board-inner {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  aspect-ratio: 850 / 493;
  overflow: hidden;
}

.science-board.science-board-5 .science-board-inner {
  aspect-ratio: 850 / 634;
}

.science-board.science-board-3.crop-top .science-board-inner {
  transform: translateY(calc(-100% * 50 / 493));
}

.science-board.science-board-5.crop-top .science-board-inner {
  transform: translateY(calc(-100% * 50 / 634));
}

.science-board-img {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: auto;
  display: block;
  pointer-events: none;
}

.ability-board {
  position: relative;
  background-size: contain;
  background-repeat: no-repeat;
  background-position: center;
  aspect-ratio: 534.6 / 253;
  width: 100%;
  height: auto;
  border-radius: 0 0 8px 8px;
}

.science-board-tile,
.ability-board-tile {
  position: absolute;
  background-repeat: no-repeat;
  box-sizing: border-box;
  cursor: pointer;
  box-shadow: 3px 3px 6px rgba(0, 0, 0, 0.35);
}

.science-tile-owner-mark {
  position: absolute;
  top: -28px;
  right: -18px;
  width: 48px;
  height: 56px;
  z-index: 11;
  pointer-events: none;
  object-fit: contain;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.35));
}

.ability-tile-owner-strip {
  position: absolute;
  top: -24px;
  left: -14px;
  right: 0;
  display: flex;
  align-items: flex-start;
  justify-content: flex-start;
  z-index: 11;
  pointer-events: none;
}

.ability-tile-owner-mark {
  width: 40px;
  height: 48px;
  object-fit: contain;
  flex: 0 0 auto;
  filter: drop-shadow(0 1px 3px rgba(0, 0, 0, 0.35));
}

.ability-tile-owner-mark + .ability-tile-owner-mark {
  margin-left: -29px;
}

.tile-index-badge {
  position: absolute;
  bottom: 2px;
  left: 2px;
  width: 17px;
  height: 17px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.52rem;
  font-weight: 800;
  color: #f7fbff;
  background: var(--accent);
  border: 1px solid var(--accent-light);
  border-radius: 50%;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.22);
  z-index: 10;
  pointer-events: none;
  text-align: center;
  white-space: nowrap;
  font-variant-numeric: tabular-nums;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.18);
}

.ability-board-tile .tile-index-badge {
  width: 15px;
  height: 15px;
  font-size: 0.46rem;
}

.ability-tile-remaining-badge {
  position: absolute;
  right: 2px;
  bottom: 2px;
  min-width: 20px;
  height: 16px;
  padding: 0 3px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  background: rgba(25, 32, 44, 0.92);
  border: 1px solid rgba(149, 196, 230, 0.42);
  color: #f7fbff;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.22);
  z-index: 10;
  pointer-events: none;
  font-size: 0.48rem;
  font-weight: 800;
  font-variant-numeric: tabular-nums;
  line-height: 1;
}

.cult-board-section {
  position: relative;
  flex: 0 0 auto;
  aspect-ratio: 861 / 1248;
  display: flex;
  align-items: center;
  justify-content: center;
  align-self: center;
  max-height: 100%;
  max-width: 100%;
  overflow: hidden;
}

.cult-board-image {
  width: 100%;
  height: 100%;
  object-fit: contain;
  border-radius: 8px;
  display: block;
}

.tracks-board-overlay {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.track-marker {
  position: absolute;
  width: 12%;
  height: auto;
  aspect-ratio: 67 / 80;
  transform: translate(-50%, -50%);
  transition: top 0.7s ease, left 0.7s ease;
  pointer-events: none;
}

.track-marker-fade-enter-active,
.track-marker-fade-leave-active {
  transition: top 0.7s ease, left 0.7s ease, opacity 0.7s ease;
}

.track-marker-fade-enter-from,
.track-marker-fade-leave-to {
  opacity: 0;
}

.track-marker canvas {
  width: 100%;
  height: 100%;
  display: block;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.35));
}

/* ===== 右侧：全局信息区 (21%) ===== */
.global-section {
  display: flex;
  flex-direction: column;
  gap: var(--game-column-gap);
  width: 25%;
  height: 100%;
}

.global-status {
  background-color: #171717;
  border-radius: var(--border-radius);
  padding: 14px calc(var(--panel-padding) + 2px) 12px;
  border: 1px solid var(--border);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.status-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.status-title {
  font-size: 1rem;
  color: var(--text-primary);
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  min-width: 0;
}

.status-title i {
  color: var(--accent);
}

.status-body {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  align-items: center;
  gap: 10px;
}

.status-body.has-detail-action {
  grid-template-columns: minmax(0, 1fr) auto;
}

.status-content {
  font-size: 0.98rem;
  color: var(--text-primary);
  line-height: 1.45;
  overflow: hidden;
  display: flex;
  align-items: center;
  white-space: pre-wrap;
  word-wrap: break-word;
  min-height: 34px;
  min-width: 0;
}

.status-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
}

.status-detail-btn {
  appearance: none;
  min-height: 30px;
  padding: 0 12px;
  border: 1px solid rgba(92, 190, 240, 0.34);
  border-radius: 999px;
  background: rgba(14, 22, 34, 0.82);
  color: #dcecfb;
  font-size: 0.75rem;
  font-weight: 600;
  line-height: 1;
  cursor: pointer;
  transition: border-color 0.18s ease, background-color 0.18s ease, color 0.18s ease;
}

.status-detail-btn:hover {
  border-color: var(--accent);
  background: rgba(18, 27, 40, 0.96);
  color: #ffffff;
}

.more-menu-btn {
  width: 30px;
  height: 30px;
  border: none;
  padding: 0;
  background: transparent;
  color: #ffffff;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: opacity 0.18s ease;
}

.more-menu-btn:hover {
  background: transparent;
  color: #ffffff;
  opacity: 0.74;
}

.more-menu-btn:focus-visible {
  outline: none;
  box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.24);
  border-radius: 999px;
}

/* 游戏菜单弹窗样式 */
.game-menu-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 20px 24px;
}

.menu-modal-btn {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 16px;
  width: 100%;
  padding: 16px 20px;
  border: 1px solid var(--border);
  border-radius: 12px;
  background: var(--bg-tertiary);
  color: var(--text-primary);
  cursor: pointer;
  transition: all 0.2s;
  text-align: left;
}

.menu-modal-btn:hover {
  border-color: var(--accent);
  background: var(--bg-secondary);
  transform: translateY(-2px);
}

.btn-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  flex-shrink: 0;
}

.btn-icon i {
  font-size: 1.5rem;
}

.btn-text {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.btn-text span {
  font-weight: 600;
  font-size: 1rem;
}

.btn-text small {
  font-size: 0.85rem;
  color: var(--text-secondary);
  font-weight: 400;
}

/* 所有菜单按钮悬停态统一为红色 */
.menu-modal-btn:hover {
  border-color: #ef4444;
  background: rgba(239, 68, 68, 0.1);
}

.menu-modal-btn .btn-icon i {
  color: #ef4444;
}

/* 二次确认状态样式 */
.menu-modal-btn.confirm-state {
  border-color: #ef4444;
  background: rgba(239, 68, 68, 0.15);
  animation: confirm-pulse 1s ease-in-out infinite;
}

.menu-modal-btn.confirm-state .btn-text span {
  color: #ef4444;
}

.menu-modal-btn.confirm-state .btn-text small {
  color: #f87171;
}

@keyframes confirm-pulse {
  0%, 100% {
    box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.4);
  }
  50% {
    box-shadow: 0 0 0 4px rgba(239, 68, 68, 0.2);
  }
}

.action-section {
  flex: 1;
  min-height: 0;
  position: relative;
}

.control-center-section,
.action-section,
.action-log-panel {
  background-color: #171717;
  border-radius: var(--border-radius);
  border: 1px solid var(--border);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.action-section,
.action-log-panel {
  --action-toolbar-pill-width: 96px;
  --action-toolbar-pill-height: 32px;
  --action-toolbar-pill-gap: 7px;
  --action-toolbar-pill-border: rgba(255, 255, 255, 0.08);
  --action-toolbar-pill-border-hover: rgba(255, 255, 255, 0.14);
  --action-toolbar-pill-border-active: rgba(255, 255, 255, 0.2);
  --action-toolbar-pill-bg: rgba(94, 100, 107, 0.24);
  --action-toolbar-pill-bg-hover: rgba(104, 111, 118, 0.32);
  --action-toolbar-pill-bg-active: rgba(114, 121, 128, 0.4);
  --action-toolbar-pill-text: rgba(229, 235, 242, 0.92);
}

.control-center-section {
  min-height: 90px;
}

.control-center-header {
  padding: 14px calc(var(--panel-padding) + 2px) 6px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.control-center-content {
  padding: 6px 14px 12px;
  flex: 1;
}

.control-center-toolbar {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto auto;
  gap: 8px;
}

.control-center-button {
  appearance: none;
  width: 100%;
  min-width: 0;
  min-height: 32px;
  padding: 0 10px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 9px;
  background: rgba(255, 255, 255, 0.03);
  color: var(--text-primary);
  display: inline-flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  box-sizing: border-box;
  cursor: pointer;
  transition: border-color 0.18s ease, background-color 0.18s ease, color 0.18s ease;
  font-size: 0.76rem;
  font-weight: 700;
}

.control-center-button:hover:not(:disabled) {
  border-color: var(--accent);
  background: rgba(0, 123, 255, 0.1);
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.18);
}

.control-center-button:focus-visible {
  outline: none;
  border-color: var(--accent);
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.2);
}

.control-center-button:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

.control-center-button-main {
  min-width: 0;
  flex: 1 1 auto;
  display: inline-flex;
  align-items: center;
  justify-content: flex-start;
  gap: 8px;
}

.control-center-button-label {
  color: rgba(198, 211, 224, 0.66);
  font-size: 0.7rem;
  flex-shrink: 0;
}

.control-center-button-value {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #f5f8fb;
  font-size: inherit;
  font-weight: inherit;
}

.control-center-button-arrow {
  flex-shrink: 0;
  color: rgba(198, 211, 224, 0.62);
  font-size: 0.66rem;
}

.control-center-strategy-button.is-open {
  border-color: var(--accent);
  background: rgba(0, 123, 255, 0.12);
}

.control-center-strategy-button.is-open .control-center-button-arrow {
  color: rgba(236, 242, 248, 0.86);
}

.control-center-execute-button {
  justify-content: center;
  padding: 0 14px;
}

.control-center-execute-button.has-recommendation {
  border-color: rgba(245, 158, 11, 0.72);
  color: rgba(255, 250, 240, 0.98);
}

.control-center-execute-button.has-recommendation:hover:not(:disabled) {
  border-color: rgba(245, 158, 11, 0.9);
  background: transparent;
  box-shadow: none;
}

.control-center-recommend-button {
  justify-content: center;
  gap: 6px;
  padding: 0 14px;
}

.control-center-recommend-button.is-recommended {
  border-color: rgba(245, 158, 11, 0.78);
  background: rgba(245, 158, 11, 0.14);
  color: rgba(255, 250, 240, 0.98);
  box-shadow: 0 0 0 1px rgba(245, 158, 11, 0.16);
}

.control-center-recommend-button.is-recommended:hover:not(:disabled) {
  border-color: rgba(245, 158, 11, 0.88);
  background: rgba(245, 158, 11, 0.18);
  box-shadow: 0 0 0 1px rgba(245, 158, 11, 0.2);
}

.action-section {
  --action-toolbar-pill-width: 84px;
  --action-toolbar-pill-height: 28px;
  --action-toolbar-pill-gap: 8px;
}

.action-header {
  padding: 14px calc(var(--panel-padding) + 2px) 10px;
  background: transparent;
  display: grid;
  grid-template-columns: 1fr auto;
  grid-template-rows: auto auto;
  align-items: start;
  gap: 14px 12px;
}

.action-title-group {
  grid-column: 1;
  grid-row: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
}

.action-title {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.action-title > div {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.action-title i {
  color: var(--accent);
  flex-shrink: 0;
}

.action-subtitle {
  font-size: 0.73rem;
  line-height: 1.35;
  color: rgba(198, 211, 224, 0.72);
  max-width: 100%;
  word-break: keep-all;
}

.ai-thinking-badge {
  grid-column: 2;
  grid-row: 2;
  display: flex;
  align-items: center;
  align-self: center;
  justify-content: flex-end;
  height: var(--action-toolbar-pill-height);
  gap: 6px;
  color: var(--accent);
  font-size: 1.1rem;
  font-weight: 600;
  font-family: 'Outfit', 'Poppins', 'DM Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  font-size: 1.1rem;
  font-weight: 700;
  animation: pulse 2s infinite;
  white-space: nowrap;
}

.ai-thinking-badge img {
  width: 28px;
  height: 28px;
  flex-shrink: 0;
  display: block;
}

.ai-thinking-badge span {
  line-height: var(--action-toolbar-pill-height);
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.85;
  }
}

.action-header-pills {
  grid-column: 1;
  grid-row: 2;
  display: flex;
  align-items: center;
  align-self: center;
  gap: var(--action-toolbar-pill-gap);
}

.action-header-pills .action-owner-chip,
.action-header-pills .action-mode-chip,
.action-header-pills .action-count {
  width: auto;
  min-width: var(--action-toolbar-pill-width);
}

.action-header-timer {
  grid-column: 2;
  grid-row: 1;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  height: calc(1rem + 0.73rem + 8px);
}

.action-header-timer .action-timer {
  font-family: 'SF Mono', 'Menlo', 'Monaco', 'Consolas', 'Liberation Mono', 'Courier New', monospace;
  font-size: 2.3em;
  font-weight: 700;
}

.action-header-timer .timer-circle {
  width: 56px;
  height: 56px;
}

.action-header-timer .timer-text.byo-yomi-time {
  font-size: 1.18em;
  font-weight: 700;
}

.action-header-meta,
.action-log-toolbar {
  display: grid;
  align-items: center;
  justify-content: stretch;
  gap: var(--action-toolbar-pill-gap);
  width: min(100%, calc(var(--action-toolbar-pill-width) * var(--action-toolbar-pill-count) + var(--action-toolbar-pill-gap) * (var(--action-toolbar-pill-count) - 1)));
  min-width: 0;
}

.action-header-meta {
  --action-toolbar-pill-count: 3;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  margin-left: 0;
}

.action-header-meta.has-recommendation {
  --action-toolbar-pill-count: 4;
  grid-template-columns: repeat(3, minmax(0, 1fr)) var(--action-toolbar-pill-height);
  width: min(100%, calc(var(--action-toolbar-pill-width) * 3 + var(--action-toolbar-pill-height) + var(--action-toolbar-pill-gap) * 3));
}

.action-log-toolbar {
  --action-toolbar-pill-count: 2;
  width: min(100%, calc(var(--action-log-count-width) + var(--action-toolbar-pill-width) + var(--action-toolbar-pill-gap)));
  grid-template-columns: minmax(var(--action-log-count-width), 1fr) var(--action-toolbar-pill-width);
  flex: 0 0 auto;
  margin-left: auto;
}

.action-owner-chip,
.action-mode-chip,
.action-count,
.action-recommend-chip,
.action-filter-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  min-width: 0;
  height: var(--action-toolbar-pill-height);
  padding: 0 8px;
  gap: 5px;
  border-radius: 999px;
  border: 1px solid var(--action-toolbar-pill-border);
  background: var(--action-toolbar-pill-bg);
  color: var(--action-toolbar-pill-text);
  line-height: 1;
  font-size: 0.75rem;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
  box-sizing: border-box;
  white-space: nowrap;
  transition: border-color 0.18s ease, background-color 0.18s ease, color 0.18s ease;
  overflow: hidden;
}

.action-owner-chip,
.action-mode-chip,
.action-count,
.action-recommend-chip {
  flex-shrink: 0;
}

.action-owner-dot {
  width: 11px;
  height: 11px;
  border-radius: 50%;
  flex-shrink: 0;
  box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.08);
}

.action-mode-chip {
  letter-spacing: 0.02em;
}

.action-recommend-chip {
  width: var(--action-toolbar-pill-height);
  min-width: var(--action-toolbar-pill-height);
  padding: 0;
  border-color: rgba(245, 158, 11, 0.34);
  background: rgba(245, 158, 11, 0.14);
  color: rgba(255, 240, 204, 0.96);
}

.action-recommend-chip i {
  font-size: 0.76rem;
}

.action-content {
  flex: 1;
  min-height: 0;
  padding: 0 14px 14px;
  /* 始终显示滚动条，在右侧预留空间，避免滚动条出现/消失时布局跳动 */
  overflow-y: scroll;
  background: transparent;
  display: flex;
  flex-direction: column;
  gap: 8px;
  box-sizing: border-box;
}

.action-content--measure {
  position: absolute;
  top: 0;
  left: 0;
  z-index: -1;
  height: auto;
  max-height: none;
  visibility: hidden;
  pointer-events: none;
  overflow: visible;
}

.action-content--measure .action-option-button {
  pointer-events: none;
}

.action-content--measure .action-group-body {
  max-height: none;
  opacity: 1;
  overflow: visible;
}

.action-content--measure .action-group-body-inner {
  opacity: 1;
  transform: none;
}

.action-content.ai-turn {
  opacity: 0.6;
}

.action-content.ai-turn .action-option-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.action-content::-webkit-scrollbar {
  width: 4px;
}

.action-content::-webkit-scrollbar-track {
  background: transparent;
}

.action-content::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.06);
  border-radius: 2px;
}

.action-content::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.12);
}

.action-group-card {
  position: relative;
  overflow: hidden;
  padding: 10px 11px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: var(--border-radius);
  background-color: #1f1f1f;
  display: flex;
  flex-direction: column;
  gap: 0;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.015);
  transition: border-color 0.22s ease, box-shadow 0.22s ease, background-color 0.22s ease;
  box-sizing: border-box;
  /* 关键修复：防止 flex item 被压缩，确保内容超出时出现滚动条而不是压缩卡片 */
  flex-shrink: 0;
}

.action-group-card:hover:not(.is-disabled):not(.is-submitting) {
  border-color: var(--accent);
  background-color: #222222;
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.3);
}

.action-group-card.is-disabled {
  opacity: 0.56;
}

.action-group-card.is-submitting {
  border-color: rgba(92, 190, 240, 0.72);
  box-shadow: 0 0 0 2px rgba(92, 190, 240, 0.18);
}

.action-group-card.has-recommended-option {
  border-color: rgba(245, 158, 11, 0.24);
}

.action-option-button:focus-visible {
  outline: none;
  border-color: var(--border);
  background-color: #343434;
  box-shadow: none;
}

.action-filter-btn:focus-visible,
.action-filter-option:focus-visible {
  outline: none;
  border-color: var(--accent);
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.3);
}

.action-group-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  transition: color 0.18s ease;
  border-radius: 8px;
}

.action-group-header.is-collapsible {
  cursor: pointer;
  user-select: none;
  transition: color 0.18s ease;
}

.action-group-header.is-collapsible:hover {
  background-color: transparent;
}

.action-group-header.is-collapsible:focus-visible {
  outline: none;
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.3);
}

.action-group-title {
  min-width: 0;
  color: var(--text-primary);
  font-size: 0.82rem;
  font-weight: 700;
  line-height: 1.12;
}

.action-group-header.is-collapsible:hover .action-group-title,
.action-group-header.is-expanded .action-group-title {
  color: rgba(236, 242, 248, 0.98);
}

.action-group-header-meta {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  flex-shrink: 0;
}

.action-group-count-chip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 22px;
  height: 22px;
  padding: 0 6px;
  border-radius: 999px;
  border: 1px solid rgba(92, 190, 240, 0.08);
  background: rgba(92, 190, 240, 0.1);
  color: rgba(214, 233, 248, 0.92);
  font-family: 'Consolas', monospace;
  font-size: 0.65rem;
  font-weight: 700;
  box-sizing: border-box;
}

.action-group-toggle {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 14px;
  height: 14px;
  color: rgba(198, 211, 224, 0.62);
  font-size: 0.58rem;
  line-height: 1;
  transition: transform 0.18s ease, color 0.18s ease;
}

.action-group-toggle.is-expanded {
  transform: rotate(90deg);
  color: rgba(229, 235, 242, 0.88);
}

.action-group-body {
  max-height: var(--action-group-body-height, 999px);
  opacity: 1;
  margin-top: 7px;
  overflow: hidden;
  will-change: max-height, opacity;
  transition: max-height 0.24s ease, opacity 0.18s ease, margin-top 0.24s ease;
}

.action-group-body.is-collapsed {
  max-height: 0;
  opacity: 0;
  margin-top: 0;
  pointer-events: none;
}

.action-group-body-inner {
  min-height: 0;
  overflow: hidden;
  padding-top: 9px;
  padding-bottom: 2px;
  border-top: 1px solid rgba(255, 255, 255, 0.045);
  opacity: 1;
  transform: translateY(0);
  transition: transform 0.24s ease, opacity 0.18s ease;
}

.action-group-body.is-collapsed .action-group-body-inner {
  opacity: 0;
  transform: translateY(-4px);
}

.action-group-options {
  display: flex;
  flex-wrap: wrap;
  gap: 7px;
  align-items: flex-start;
}

.action-group-options.is-coord_grid {
  gap: 6px;
}

.action-group-options.is-number_grid {
  gap: 5px;
}

.action-group-options.is-single_button,
.action-group-options.has-verbose-detail,
.action-group-options.is-fixed-grid {
  display: flex;
  flex-wrap: wrap;
}

.action-option-button {
  --action-option-accent-color: rgba(92, 190, 240, 0.85);
  appearance: none;
  min-height: 34px;
  padding: 7px 9px;
  border: 1px solid var(--border);
  border-radius: 10px;
  background-color: var(--bg-tertiary);
  color: var(--text-primary);
  text-align: left;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: border-color 0.18s ease, background-color 0.18s ease, transform 0.18s ease, box-shadow 0.18s ease;
  box-sizing: border-box;
  font: inherit;
  min-width: 46px;
  width: auto;
  max-width: 100%;
  flex: 0 0 auto;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.012);
}

.action-group-options.has-detail .action-option-button {
  flex: 0 0 auto;
}

.action-group-options.is-fixed-grid .action-option-button {
  width: auto;
}

.action-group-options.is-coord_grid .action-option-button {
  min-width: 40px;
  justify-content: center;
}

.action-group-options.is-number_grid .action-option-button {
  min-width: 38px;
  justify-content: center;
}

.action-option-button.is-compact {
  text-align: center;
  min-width: 0;
  padding: 5px 7px;
}

.action-option-button:hover:not(:disabled) {
  border-color: var(--border);
  background-color: #343434;
  box-shadow: none;
}

.action-option-button:disabled {
  cursor: wait;
}

.action-option-button.is-disabled {
  opacity: 0.56;
}

.action-option-button.is-submitting {
  border-color: rgba(92, 190, 240, 0.72);
  box-shadow: 0 0 0 1px rgba(92, 190, 240, 0.18);
}

.action-option-button.is-recommended {
  border-color: rgba(245, 158, 11, 0.78);
  background-color: rgba(245, 158, 11, 0.14);
  box-shadow: 0 0 0 1px rgba(245, 158, 11, 0.16);
}

.action-option-button.is-recommended:hover:not(:disabled) {
  border-color: rgba(245, 158, 11, 0.88);
  background-color: rgba(245, 158, 11, 0.18);
  box-shadow: 0 0 0 1px rgba(245, 158, 11, 0.2);
}

.action-option-button.is-recommended .action-option-label {
  color: rgba(255, 247, 230, 0.98);
}

.action-option-main {
  display: inline-flex;
  align-items: baseline;
  justify-content: flex-start;
  flex-wrap: wrap;
  gap: 6px;
  min-width: 0;
}

.action-option-label {
  color: var(--text-primary);
  font-size: 0.72rem;
  font-weight: 700;
  line-height: 1.08;
}

.action-option-detail {
  color: rgba(198, 211, 224, 0.72);
  font-size: 0.62rem;
  line-height: 1.2;
  white-space: normal;
  word-break: break-word;
}

.action-option-button[data-color='red'] { --action-option-accent-color: #cc2828; }
.action-option-button[data-color='green'] { --action-option-accent-color: #37af37; }
.action-option-button[data-color='blue'] { --action-option-accent-color: #35a0d5; }
.action-option-button[data-color='yellow'] { --action-option-accent-color: #e8e83d; }
.action-option-button[data-color='grey'] { --action-option-accent-color: #a1a1a1; }
.action-option-button[data-color='brown'] { --action-option-accent-color: #85491d; }
.action-option-button[data-color='black'] { --action-option-accent-color: #595959; }
.action-option-button[data-color='white'] { --action-option-accent-color: #ffffff; }

.action-log-section {
  width: 18%;
  height: 100%;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: var(--game-column-gap);
}

.action-log-panel {
  --action-log-count-width: 100px;
  --action-toolbar-pill-width: 78px;
  --action-toolbar-pill-height: 28px;
  --action-toolbar-pill-gap: 6px;
  flex: 1;
  min-height: 0;
}

.action-log-header {
  position: relative;
  padding: 14px calc(var(--panel-padding) + 2px) 10px;
  background: transparent;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  flex-wrap: nowrap;
}

.action-log-header .action-title-group {
  flex: 1 1 auto;
}

.action-log-content {
  flex: 1;
  min-height: 0;
  padding: 0 14px 14px;
  overflow-y: auto;
  background: transparent;
  display: flex;
  flex-direction: column;
  gap: 6px;
  scrollbar-width: none;
  -ms-overflow-style: none;
}

.action-log-content::-webkit-scrollbar {
  display: none;
}

.action-log-filter {
  position: relative;
  width: 100%;
  min-width: 0;
}

.action-filter-btn {
  appearance: none;
  cursor: pointer;
  position: relative;
  width: 100%;
  overflow: visible;
}

#action-count,
#action-log-count {
  font-weight: 700;
  color: #f5f8fb;
}

.action-log-count-chip {
  cursor: default;
  min-width: var(--action-log-count-width);
}

.action-filter-btn i {
  font-size: 0.76rem;
}

.action-filter-btn:hover {
  border-color: var(--action-toolbar-pill-border-hover);
  background: var(--action-toolbar-pill-bg-hover);
  color: #f3f7fb;
}

.action-filter-btn.is-active {
  border-color: var(--accent);
  background: var(--accent);
  color: #ffffff;
  box-shadow: 0 0 0 1px rgba(0, 123, 255, 0.28);
}

.action-filter-badge {
  position: absolute;
  top: -5px;
  right: -4px;
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.08);
  color: rgba(236, 241, 246, 0.9);
  font-size: 0.68rem;
  font-weight: 700;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
}

.action-filter-btn.is-active .action-filter-badge {
  background: rgba(255, 255, 255, 0.98);
  color: var(--accent);
  box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.28);
}

.action-filter-popup {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  width: 276px;
  max-width: calc(100vw - 40px);
  padding: 14px;
  border: 1px solid var(--accent);
  border-radius: 12px;
  background: var(--bg-secondary);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
  z-index: 20;
  display: flex;
  flex-direction: column;
  gap: 0;
}

.action-filter-section-title {
  margin: 0;
  color: var(--text-secondary);
  font-size: 0.78rem;
  font-weight: 500;
  line-height: 1.2;
}

.action-filter-section {
  display: flex;
  flex-direction: column;
  gap: 9px;
}

.action-filter-section + .action-filter-section {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--border);
}

.action-filter-option--sm {
  min-height: 28px;
  padding: 0 10px;
  font-size: 0.7rem;
  font-weight: 500;
}

.action-filter-search-grid {
  display: grid;
  gap: 9px;
}

.action-filter-search-field {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.action-filter-search-label,
.action-filter-stage-group-title {
  color: var(--text-secondary);
  font-size: 0.68rem;
  font-weight: 500;
  line-height: 1.2;
}

.action-filter-stage-groups {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.action-filter-stage-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.action-filter-search-input {
  width: 100%;
  min-height: 34px;
  padding: 0 12px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--bg-tertiary);
  color: var(--text-primary);
  font-size: 0.76rem;
  line-height: 1.2;
  box-sizing: border-box;
  transition: border-color 0.18s ease, box-shadow 0.18s ease;
}

.action-filter-search-input::placeholder {
  color: rgba(198, 211, 224, 0.46);
}

.action-filter-search-input:focus {
  outline: none;
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(92, 190, 240, 0.12);
}

.action-filter-options {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.action-filter-options.is-compact-rounds {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 6px;
}

.action-filter-option {
  appearance: none;
  width: auto;
  min-height: 34px;
  padding: 0 12px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--bg-tertiary);
  color: var(--text-primary);
  display: inline-flex;
  align-items: center;
  gap: 7px;
  cursor: pointer;
  transition: border-color 0.18s ease, background-color 0.18s ease, color 0.18s ease, box-shadow 0.18s ease;
  font-size: 0.76rem;
  font-weight: 600;
  line-height: 1;
  white-space: nowrap;
}

.action-filter-option.is-round-chip {
  flex: 1 1 0;
  min-width: 0;
  justify-content: center;
  padding: 0;
}

.action-filter-option:hover,
.action-filter-option.is-active {
  border-color: var(--accent);
  background: rgba(92, 190, 240, 0.14);
  color: #dcecfb;
  box-shadow: 0 0 0 2px rgba(92, 190, 240, 0.06);
}

.action-filter-player-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  flex-shrink: 0;
  box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.06);
}

.action-filter-footer-btn {
  min-width: 92px;
  min-height: 36px;
  padding: 0 14px;
  border-radius: 8px;
  font: inherit;
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
  transition: border-color 0.18s ease, background-color 0.18s ease, color 0.18s ease;
}

.action-filter-actions {
  display: flex;
  gap: 8px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--border);
}

.action-filter-footer-btn.is-ghost {
  flex: 1;
  border: 1px solid var(--border);
  background: transparent;
  color: var(--text-secondary);
}

.action-filter-footer-btn.is-ghost:hover {
  background: rgba(255, 255, 255, 0.05);
  color: var(--text-primary);
}

.action-filter-footer-btn.is-primary {
  flex: 1;
  border: 1px solid var(--accent);
  background: var(--accent);
  color: #ffffff;
}

.action-filter-footer-btn.is-primary:hover {
  background: #0069d9;
  border-color: #0069d9;
}

/* 筛选弹窗全屏布局样式 */
.action-filter-modal-body {
  padding: 20px 0;
}

.action-filter-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1.35fr) minmax(0, 1.15fr);
}

.action-filter-column {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 0 20px;
  border-right: 1px solid var(--border);
  max-height: calc(80vh - 180px);
  overflow-y: auto;
  overflow-x: hidden;
  min-width: 0;
}

.action-filter-column:last-child {
  border-right: none;
}

.action-filter-column:first-child {
  padding-left: 24px;
}

.action-filter-column:last-child {
  padding-right: 24px;
}

.action-filter-options--wrap {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  max-height: 300px;
  overflow-y: auto;
}

.action-filter-options--inline {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

/* 扩大筛选弹窗宽度 */
.action-log-filter-modal :deep(.modal-content) {
  max-width: 60vw;
}

.action-filter-modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 24px;
}

.action-log-divider {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto minmax(0, 1fr);
  align-items: center;
  gap: 10px;
  min-height: 24px;
  color: rgba(198, 211, 224, 0.72);
}

.action-log-divider-line {
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(120, 160, 200, 0.26), transparent);
}

.action-log-divider-text {
  color: rgba(198, 211, 224, 0.78);
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  white-space: nowrap;
}

/* 玩家面板分割线 - 参考 action-log-divider 样式 */
.player-pass-divider {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto minmax(0, 1fr);
  align-items: center;
  gap: 10px;
  min-height: 24px;
  color: rgba(198, 211, 224, 0.72);
  margin: 4px 0;
}

.player-pass-divider-line {
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(120, 160, 200, 0.26), transparent);
}

.player-pass-divider-text {
  color: rgba(198, 211, 224, 0.78);
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  white-space: nowrap;
}

/* 空状态提示 */
.player-empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 40px;
  padding: 8px 0;
  color: rgba(198, 211, 224, 0.42);
  font-size: 0.75rem;
  font-style: italic;
}

/* TransitionGroup 列表动画 */
.player-card-move {
  transition: transform 0.5s cubic-bezier(0.25, 0.8, 0.25, 1), opacity 0.5s cubic-bezier(0.25, 0.8, 0.25, 1);
}

.player-card-enter-active {
  transition: opacity 0.4s cubic-bezier(0.25, 0.8, 0.25, 1), transform 0.4s cubic-bezier(0.25, 0.8, 0.25, 1);
}

.player-card-leave-active {
  position: absolute;
  width: 100%;
  transition: opacity 0.4s cubic-bezier(0.25, 0.8, 0.25, 1), transform 0.4s cubic-bezier(0.25, 0.8, 0.25, 1);
}

.player-card-enter-from {
  opacity: 0;
  transform: scale(0.96);
}

.player-card-leave-to {
  opacity: 0;
  transform: scale(0.96);
}

/* 已pass玩家卡片样式 */
.player-card.is-passed {
  opacity: 0.75;
  filter: grayscale(0.15);
}

.action-log-entry {
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 7px 10px;
  background-color: var(--bg-tertiary);
  display: grid;
  grid-template-columns: auto auto minmax(0, 1fr);
  align-items: center;
  gap: 8px;
  min-height: 34px;
  box-sizing: border-box;
  transition: border-color 0.18s ease, background-color 0.18s ease;
}

.action-log-entry:hover {
  border-color: rgba(0, 123, 255, 0.42);
  background: rgba(255, 255, 255, 0.02);
}

.action-log-entry.is-system {
  border-color: rgba(121, 139, 160, 0.22);
}

.action-log-record-id {
  color: #cde8fb;
  font-family: 'Consolas', monospace;
  font-size: 0.69rem;
  font-weight: 700;
  flex-shrink: 0;
}

.action-log-player-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
  background: var(--log-player-color);
  box-shadow: var(--log-player-dot-shadow, 0 0 0 1px rgba(255, 255, 255, 0.08));
}

.action-log-text {
  color: var(--text-primary);
  font-size: 0.78rem;
  line-height: 1.35;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.action-log-description-inline {
  display: flex;
  align-items: baseline;
  gap: 0;
  min-width: 0;
  flex-wrap: nowrap;
  overflow: hidden;
}

.action-log-category-inline {
  color: #f0f4f8;
  font-size: 0.8rem;
  font-weight: 500;
  line-height: 1.3;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 100%;
  min-width: 0;
  flex: 0 0 auto;
}

.action-log-separator {
  color: rgba(198, 211, 224, 0.3);
  font-size: 0.75rem;
  line-height: 1.3;
  margin: 0 2px;
  flex-shrink: 0;
}

.action-log-subcategory-wrap {
  display: flex;
  align-items: baseline;
  gap: 0 2px;
  flex: 0 0 auto;
  min-width: 0;
  overflow: hidden;
}

.action-log-subcategory-inline {
  color: var(--text-primary);
  font-size: 0.75rem;
  line-height: 1.3;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  min-width: 0;
}

.action-log-detail-wrap {
  display: flex;
  align-items: baseline;
  gap: 0 2px;
  flex: 0 999 auto;
  min-width: 0;
  overflow: hidden;
}

.action-log-detail-inline {
  color: rgba(198, 211, 224, 0.5);
  font-size: 0.68rem;
  line-height: 1.3;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  min-width: 0;
}

.panel-empty-state {
  min-height: 112px;
  padding: 20px 16px;
  border-radius: 12px;
  color: rgba(198, 211, 224, 0.72);
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  line-height: 1.6;
}

.panel-empty-state--action,
.panel-empty-state--log {
  margin-top: 10px;
}

.final-score-modal {
  padding: 20px 24px 24px;
}

.final-score-table {
  overflow-x: auto;
}

.final-score-grid {
  min-width: 620px;
  display: grid;
  grid-template-columns: minmax(132px, 1.5fr) repeat(5, minmax(68px, 0.78fr));
  align-items: center;
  gap: 12px;
}

.final-score-header {
  padding: 0 12px 12px;
  border-bottom: 1px solid var(--border);
  color: var(--text-secondary);
  font-size: 0.76rem;
  font-weight: 600;
}

.final-score-row {
  padding: 13px 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  color: var(--text-primary);
  font-size: 0.9rem;
}

.final-score-row:last-child {
  border-bottom: none;
}

.final-score-row.is-winner {
  background: rgba(92, 190, 240, 0.08);
}

.final-score-player {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  font-weight: 600;
}

.final-score-player-dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  flex-shrink: 0;
  box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.06);
}

.final-score-total {
  color: #dcecfb;
  font-weight: 700;
}

.final-score-empty {
  min-height: 160px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(198, 211, 224, 0.72);
  text-align: center;
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

.player-stats::-webkit-scrollbar-thumb,
.action-content::-webkit-scrollbar-thumb,
.action-log-content::-webkit-scrollbar-thumb {
  background: var(--accent);
}

/* 响应式 */
@media (max-width: 1400px) {
  .main-container {
    flex-wrap: wrap;
    height: auto;
    overflow-y: auto;
    align-content: flex-start;
  }

  .players-monitor {
    width: 34%;
    min-height: 420px;
  }

  .middle-section {
    width: 64%;
    min-height: 420px;
  }

  .global-section,
  .action-log-section {
    width: calc(50% - 1px);
    min-height: 320px;
  }
}

@media (max-width: 768px) {
  .game-page {
    --game-page-padding: 18px;
    --game-column-gap: 18px;
    --game-section-inset: 0px;
    --game-content-gap: 13px;
  }

  .main-container {
    flex-direction: column;
    height: auto;
    overflow-y: auto;
  }

  .players-monitor,
  .middle-section,
  .global-section,
  .action-log-section {
    width: 100%;
    height: auto;
    min-height: 400px;
  }

  .action-header-meta {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .action-header-meta.has-recommendation {
    grid-template-columns: repeat(2, minmax(0, 1fr)) var(--action-toolbar-pill-height);
    width: min(100%, calc(var(--action-toolbar-pill-width) * 2 + var(--action-toolbar-pill-height) + var(--action-toolbar-pill-gap) * 2));
  }

  .action-header-meta,
  .action-log-toolbar {
    margin-left: 0;
  }

  .action-log-header {
    align-items: flex-start;
    flex-wrap: wrap;
  }

  .control-center-toolbar {
    grid-template-columns: minmax(0, 1fr) 60px 60px;
  }
}

</style>

<style>
/* ===== 六边形地图样式（全局，因为 SVG 元素是动态创建的） ===== */
.hexagon {
  fill: rgba(40, 40, 60, 0.7);
  stroke: rgb(219, 219, 219);
  stroke-width: 2;
  stroke-dasharray: 0;
  transition: all 0.1s ease;
  cursor: default;
  z-index: 0;
  pointer-events: none;
}

/* 水域地块使用虚线边框 */
.hexagon.terrain-water {
  stroke-dasharray: 9, 9;
  stroke-width: 1.5;
  stroke: rgba(255, 255, 255, 0.2);
}

/* 地形颜色类 */
.terrain-water { fill: transparent; }
.terrain-plains { fill: #85491D; }
.terrain-swamp { fill: #595959; }
.terrain-lake { fill: #35a0d5; }
.terrain-forest { fill: #37af37; }
.terrain-mountain { fill: #a1a1a1; }
.terrain-wasteland { fill: #cc2828; }
.terrain-desert { fill: #e8e83d; }

/* 六边形编号样式 */
.hex-number {
  font-family: Arial, sans-serif;
  font-size: 10px;
  font-weight: bold;
  fill: rgba(255, 255, 255, 0.9);
  text-anchor: middle;
  dominant-baseline: middle;
  pointer-events: none;
  user-select: none;
  text-shadow: 0 0 3px rgba(0, 0, 0, 0.85);
}

/* 高亮层基础样式 */
.highlight-overlay {
  pointer-events: none;
  stroke: transparent;
  stroke-dasharray: 0;
  stroke-width: 4;
  fill: transparent;
  transition: all 0.3s ease;
}

/* 高亮激活状态 - 紫色边框和填充 */
.highlight-overlay.active {
  stroke: #9c27b0;
  stroke-dasharray: 12, 6;
  stroke-width: 4;
  fill: rgba(156, 39, 176, 0.2);
}

/* 高亮层悬停状态 - 蓝色边框 */
.highlight-overlay.hover {
  stroke: var(--accent) !important;
  stroke-width: 4 !important;
}

.highlight-overlay.active.hover {
  stroke: var(--accent) !important;
}

/* 悬停叠加层样式 */
.hover-overlay {
  pointer-events: all;
  cursor: default;
  stroke: transparent;
  stroke-width: 4;
  transition: all 0.1s ease;
  fill: transparent;
}

.hover-overlay:hover,
.hover-overlay.hover-active {
  stroke: var(--accent);
  stroke-width: 4;
}
</style>
