import { defineStore } from 'pinia'
import { ref, reactive, computed } from 'vue'

/**
 * 游戏状态管理 Store
 *
 * 基于 game_state_frontend_mapping.md 设计文档实现
 * 支持：
 * 1. 全量状态获取（页面刷新后恢复）
 * 2. 增量更新（通过 SSE 实时推送）
 * 3. 状态版本管理
 */

// ============ 类型定义（与后端对应） ============

// 游戏元信息
const createDefaultMeta = () => ({
  round: 0,
  num_players: 3,
  current_player_id: -1,
  action_type: '',
  is_game_over: false,
  setup_choice_is_completed: false,
  setup_build_is_completed: false
})

// 资源
const createDefaultResources = () => ({
  money: 0,
  ore: 0,
  bank_book: 0,
  law_book: 0,
  engineering_book: 0,
  medical_book: 0,
  meeples: 0,
  all_meeples: 7,
  all_bridges: 3
})

// 魔力
const createDefaultMagics = () => ({
  zone1: 5,
  zone2: 7,
  zone3: 0
})

// 建筑
const createDefaultBuildings = () => ({
  workshop: 9,
  guild: 4,
  palace: 1,
  school: 3,
  university: 1,
  tower: 0,
  monument: 0,
  annex: 0,
  neutral_workshop: 0,
  neutral_guild: 0,
  neutral_palace: 0,
  neutral_school: 0,
  neutral_university: 0
})

// 科技轨
const createDefaultTracks = () => ({
  bank: 0,
  law: 0,
  engineering: 0,
  medical: 0
})

// 玩家状态
const createDefaultPlayer = (playerId) => ({
  player_id: playerId,
  planning_card_id: 0,
  faction_id: 0,
  palace_tile_id: 0,
  is_got_palace: false,
  resources: createDefaultResources(),
  magics: createDefaultMagics(),
  buildings: createDefaultBuildings(),
  tracks: createDefaultTracks(),
  tracks_over_7_amount: 0,
  navigation_level: 0,
  shovel_level: 3,
  temp_navigation: false,
  controlled_map_ids: [],
  adjacent_map_ids: [],
  reachable_map_ids: [],
  citys_amount: 0,
  settlements_and_cities: {},
  city_tile_assignments: {},
  booster_ids: [],
  ability_tile_ids: [],
  science_tile_ids: [],
  boardscore: 20,
  trackscore: 0,
  chainscore: 0,
  resourcescore: 0,
  main_action_is_done: false,
  ispass: false
})

// 地图单元格
const createDefaultMapCell = () => ({
  terrain: 0,
  controller: -1,
  building_id: 0,
  is_neutral: false,
  has_annex: false
})

// 游戏设置
const createDefaultSetup = () => ({
  selected_planning_cards: [],
  selected_factions: [],
  selected_palace_tiles: [],
  selected_round_boosters: [],
  round_booster_coin_counts: {},
  round_scoring_order: [],
  final_scoring: 0,
  ability_tiles_order: [],
  science_tiles_order: [],
  selected_book_actions: [],
  init_player_order: [],
  current_global_books: {
    bank_book: 12,
    law_book: 12,
    engineering_book: 12,
    medical_book: 12
  }
})

// 展示板状态
const createDefaultDisplayBoard = () => ({
    science_tracks: {
    bank: { is_crowned: false, meeples: [-1, -1, -1, -1] },
    law: { is_crowned: false, meeples: [-1, -1, -1, -1] },
    engineering: { is_crowned: false, meeples: [-1, -1, -1, -1] },
    medical: { is_crowned: false, meeples: [-1, -1, -1, -1] }
  },
  ability_tile_owners: {},
  science_tile_owners: {},
  city_tile_owners: {}
})

export const useGameStateStore = defineStore('gameState', () => {
  // ========== 核心状态 ==========

  // 游戏元信息
  const meta = reactive(createDefaultMeta())

  // 游戏设置
  const setup = reactive(createDefaultSetup())

  // 玩家状态数组
  const players = ref([])

  // 地图状态
  const mapState = reactive({
    width: 13,
    height: 9,
    grid: [],
    bridges: {}
  })

  // 展示板状态
  const displayBoard = reactive(createDefaultDisplayBoard())

  // 可选行动列表
  const availableActions = ref([])

  // 当前行动玩家是否为 AI
  const isAiPlayer = ref(false)

  // 最终得分
  const finalScores = ref(null)

  // 版本和连接状态
  const version = ref(0)
  const isConnected = ref(false)
  const clientId = ref('')
  const gameId = ref('')

  // SSE 连接对象
  let eventSource = null
  let reconnectTimeout = null
  let isComponentActive = false

  // ========== 计算属性 ==========

  // 当前行动玩家
  const currentPlayer = computed(() => {
    if (meta.current_player_id < 0 || meta.current_player_id >= players.value.length) {
      return null
    }
    return players.value[meta.current_player_id]
  })

  // 游戏是否进行中
  const isGameActive = computed(() => {
    return meta.current_player_id >= 0 && !meta.is_game_over
  })

  // 获取特定玩家
  const getPlayer = (playerId) => {
    return players.value.find(p => p.player_id === playerId) || null
  }

  // ========== 状态初始化 ==========

  /**
   * 初始化游戏状态
   */
  function initGameState(numPlayers = 3) {
    // 初始化玩家
    players.value = Array.from({ length: numPlayers }, (_, i) =>
      createDefaultPlayer(i)
    )

    // 初始化地图网格
    mapState.grid = Array.from({ length: 9 }, () =>
      Array.from({ length: 13 }, () => createDefaultMapCell())
    )

    // 重置其他状态
    Object.assign(meta, createDefaultMeta())
    Object.assign(setup, createDefaultSetup())
    Object.assign(displayBoard, createDefaultDisplayBoard())
    availableActions.value = []
    finalScores.value = null
    version.value = 0
  }

  // ========== SSE 连接管理 ==========

  /**
   * 初始化游戏连接
   * 流程：1. GET全量状态 -> 2. 建立SSE连接 -> 3. 接收增量更新
   */
  async function init(gameIdParam) {
    gameId.value = gameIdParam
    isComponentActive = true

    // 步骤1：获取全量状态
    await fetchFullState()

    // 步骤2：建立SSE连接（接收后续增量更新）
    connectSSE()
  }

  /**
   * 获取全量状态（HTTP GET）
   * 用于页面刷新后恢复状态
   */
  async function fetchFullState() {
    try {
      const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:5001'
      const response = await fetch(`${apiBaseUrl}/api/game/state?client_version=${version.value}`)
      const data = await response.json()

      if (data.status === 'error') {
        throw new Error(data.message || 'Failed to fetch game state')
      }

      if (data.up_to_date) {
        console.log('[GameState] State is up to date')
        return
      }

      // 应用全量状态
      const stateData = data.data || data.state
      if (stateData) {
        applyFullState(stateData)
        console.log('[GameState] Full state loaded, version:', version.value)
      }
    } catch (error) {
      console.error('[GameState] Failed to fetch full state:', error)
      throw error
    }
  }

  /**
   * 建立 SSE 连接（仅用于增量更新）
   */
  function connectSSE() {
    if (!isComponentActive) return

    const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:5001'
    const url = `${apiBaseUrl}/stream/game`

    eventSource = new EventSource(url)

    eventSource.onopen = () => {
      isConnected.value = true
      console.log('[GameState] SSE connected')
    }

    eventSource.onmessage = (event) => {
      if (!isComponentActive) return
      if (event.data === ':heartbeat') return

      try {
        const message = JSON.parse(event.data)
        handleSSEMessage(message)
      } catch (e) {
        console.error('[GameState] Failed to parse SSE message:', e)
      }
    }

    eventSource.onerror = async (error) => {
      console.error('[GameState] SSE error:', error)
      isConnected.value = false

      // 检测连接是否已关闭（后端可能已停止）
      if (eventSource.readyState === EventSource.CLOSED) {
        console.log('[GameState] Backend connection closed, cleaning up')
        // 清理 localStorage 中的游戏状态
        localStorage.removeItem('gameInProgress')
        localStorage.removeItem('gameSettings')
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

  /**
   * 处理 SSE 消息
   */
  function handleSSEMessage(message) {
    const { type, player_id, data } = message

    switch (type) {
      case 'connected':
        clientId.value = message.client_id || clientId.value
        break

      case 'full':
        // 全量更新
        if (data.state) {
          applyFullState(data.state)
          version.value = message.version || version.value
        }
        break

      case 'incremental':
        // 增量更新
        if (message.changes) {
          applyChanges(message.changes)
          version.value = message.version || version.value
        }
        break

      // 兼容旧版消息格式
      case 'player_state':
        if (player_id >= 0 && player_id < players.value.length) {
          Object.assign(players.value[player_id], data)
        }
        break

      case 'actions':
        availableActions.value = (data.actions || []).map((action, idx) => ({
          action_id: action.action_id || action.id || idx,
          description: action.description || action.text || ''
        }))
        isAiPlayer.value = message.is_ai_player || false
        break

      case 'global_status':
        // 可以在这里处理全局状态更新
        break

      case 'terrain_update':
        if (data.row !== undefined && data.col !== undefined && data.terrain_type !== undefined) {
          if (mapState.grid[data.row] && mapState.grid[data.row][data.col]) {
            mapState.grid[data.row][data.col].terrain = data.terrain_type
          }
        }
        break

      case 'building_update':
        if (data.hex_row !== undefined && data.hex_col !== undefined) {
          if (mapState.grid[data.hex_row] && mapState.grid[data.hex_row][data.hex_col]) {
            const cell = mapState.grid[data.hex_row][data.hex_col]
            cell.building_id = data.id || cell.building_id
            cell.controller = data.color !== undefined ? data.color : cell.controller
          }
        }
        break

      case 'highlight_hex':
        // 高亮处理
        break

      default:
        console.log('[GameState] Unknown message type:', type, data)
    }
  }

  /**
   * 应用全量状态
   */
  function applyFullState(state) {
    // 应用元信息
    if (state.meta) {
      Object.assign(meta, state.meta)
    }

    // 应用游戏设置
    if (state.setup) {
      Object.assign(setup, state.setup)
    }

    // 应用玩家状态
    if (state.players && Array.isArray(state.players)) {
      players.value = state.players.map(p => ({
        ...createDefaultPlayer(p.player_id || 0),
        ...p
      }))
    }

    // 应用地图状态
    if (state.map_state) {
      Object.assign(mapState, state.map_state)
      // 确保网格结构正确
      if (!mapState.grid || mapState.grid.length === 0) {
        mapState.grid = Array.from({ length: 9 }, () =>
          Array.from({ length: 13 }, () => createDefaultMapCell())
        )
      }
    }

    // 应用展示板状态
    if (state.display_board) {
      Object.assign(displayBoard, state.display_board)
    }

    // 应用可选行动
    if (state.available_actions) {
      availableActions.value = state.available_actions
    }

    // 应用最终得分
    if (state.final_scores) {
      finalScores.value = state.final_scores
    }

    // 应用版本号
    if (state.version !== undefined) {
      version.value = state.version
    }
  }

  /**
   * 应用增量变更列表
   */
  function applyChanges(changes) {
    for (const change of changes) {
      applySingleChange(change.path, change.new_value, change.change_type)
    }
  }

  /**
   * 应用单个变更
   *
   * 路径示例：
   * - "meta.round"
   * - "players[0].resources.money"
   * - "map_state.grid[3][5].building_id"
   * - "players[0].controlled_map_ids.added"
   * - "players[0].reachable_map_ids.removed"
   */
  function applySingleChange(path, value, changeType) {
    const keys = path.split(/\.|\[|\]/).filter(k => k !== '')

    // 特殊处理 available_actions - 直接替换整个列表
    if (keys[0] === 'available_actions') {
      if (Array.isArray(value)) {
        availableActions.value = value.map((action, idx) => ({
          action_id: action.action_id || action.id || idx,
          description: action.description || action.text || ''
        }))
      } else {
        availableActions.value = []
      }
      return
    }

    // 处理 set 类型的增量更新 (added/removed)
    if (keys.length >= 2) {
      const lastKey = keys[keys.length - 1]
      const parentPath = keys.slice(0, -1)

      if (lastKey === 'added' || lastKey === 'removed') {
        const parent = getValueByPath(parentPath)
        if (parent && Array.isArray(parent)) {
          if (lastKey === 'added' && Array.isArray(value)) {
            // 添加新元素
            for (const item of value) {
              const exists = parent.some(p => JSON.stringify(p) === JSON.stringify(item))
              if (!exists) {
                parent.push(item)
              }
            }
          } else if (lastKey === 'removed' && Array.isArray(value)) {
            // 移除元素
            for (const item of value) {
              const idx = parent.findIndex(p => JSON.stringify(p) === JSON.stringify(item))
              if (idx >= 0) {
                parent.splice(idx, 1)
              }
            }
          }
          return
        }
      }
    }

    // 普通字段更新
    if (changeType === 'removed') {
      deleteValueByPath(keys)
    } else {
      setValueByPath(keys, value)
    }
  }

  /**
   * 根据路径获取值
   */
  function getValueByPath(keys) {
    let current = getRootObject(keys[0])

    for (let i = 1; i < keys.length; i++) {
      const key = keys[i]
      if (current === null || current === undefined) {
        return undefined
      }

      if (Array.isArray(current)) {
        const index = parseInt(key)
        current = current[index]
      } else {
        current = current[key]
      }
    }

    return current
  }

  /**
   * 根据路径设置值
   */
  function setValueByPath(keys, value) {
    let current = getRootObject(keys[0])

    for (let i = 1; i < keys.length - 1; i++) {
      const key = keys[i]
      const nextKey = keys[i + 1]

      if (Array.isArray(current)) {
        const index = parseInt(key)
        if (current[index] === undefined) {
          current[index] = /^\d+$/.test(nextKey) ? [] : {}
        }
        current = current[index]
      } else {
        if (current[key] === undefined) {
          current[key] = /^\d+$/.test(nextKey) ? [] : {}
        }
        current = current[key]
      }
    }

    const lastKey = keys[keys.length - 1]
    if (Array.isArray(current)) {
      current[parseInt(lastKey)] = value
    } else {
      current[lastKey] = value
    }
  }

  /**
   * 根据路径删除值
   */
  function deleteValueByPath(keys) {
    let current = getRootObject(keys[0])

    for (let i = 1; i < keys.length - 1; i++) {
      const key = keys[i]
      if (Array.isArray(current)) {
        current = current[parseInt(key)]
      } else {
        current = current[key]
      }
      if (current === undefined) return
    }

    const lastKey = keys[keys.length - 1]
    if (Array.isArray(current)) {
      current.splice(parseInt(lastKey), 1)
    } else {
      delete current[lastKey]
    }
  }

  /**
   * 获取根对象
   */
  function getRootObject(key) {
    switch (key) {
      case 'meta': return meta
      case 'setup': return setup
      case 'players': return players.value
      case 'map_state': return mapState
      case 'display_board': return displayBoard
      case 'available_actions': return availableActions.value
      case 'final_scores': return finalScores.value
      default: return {}
    }
  }

  /**
   * 断开连接
   */
  function disconnect() {
    isComponentActive = false
    if (eventSource) {
      eventSource.close()
      eventSource = null
    }
    if (reconnectTimeout) {
      clearTimeout(reconnectTimeout)
      reconnectTimeout = null
    }
    isConnected.value = false
  }

  /**
   * 提交玩家行动
   */
  async function submitAction(actionId) {
    try {
      const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:5001'
      const response = await fetch(`${apiBaseUrl}/api/game/action`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          action_id: actionId,
          player_id: meta.current_player_id
        })
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      return await response.json()
    } catch (error) {
      console.error('[GameState] Failed to submit action:', error)
      throw error
    }
  }

  return {
    // 状态
    meta,
    setup,
    players,
    mapState,
    displayBoard,
    availableActions,
    isAiPlayer,
    finalScores,
    version,
    isConnected,
    clientId,
    gameId,

    // 计算属性
    currentPlayer,
    isGameActive,
    getPlayer,

    // 方法
    init,
    initGameState,
    fetchFullState,
    connectSSE,
    disconnect,
    submitAction,
    applyFullState,
    applyChanges
  }
})
