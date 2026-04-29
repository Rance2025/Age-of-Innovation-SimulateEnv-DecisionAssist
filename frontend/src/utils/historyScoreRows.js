import { getStrategyLabel } from '../constants/strategies.js'

function normalizePlayerId(playerId) {
  const normalized = Number(playerId)
  if (!Number.isInteger(normalized) || normalized < 0) {
    return null
  }

  return normalized
}

function resolveStrategyText(strategyName) {
  if (!strategyName) {
    return '--'
  }

  const strategyLabel = getStrategyLabel(strategyName)
  return strategyLabel === '未知策略' ? strategyName : strategyLabel
}

function createBaseRow(playerId, player = {}) {
  const playerType = typeof player.player_type === 'string' ? player.player_type.trim() : 'human'
  const playerInputId = typeof player.player_input_id === 'string' ? player.player_input_id.trim() : ''
  const strategyName = typeof player.strategy_name === 'string' ? player.strategy_name.trim() : ''
  const isAiPlayer = playerType === 'ai'

  return {
    player_id: playerId,
    player_label: String(playerId + 1),
    identity_text: isAiPlayer ? resolveStrategyText(strategyName) : (playerInputId || '--'),
    identity_icon: isAiPlayer ? 'fas fa-robot' : '',
    identity_is_ai: isAiPlayer,
    total: null,
    board: null,
    chain: null,
    track: null,
    resource: null,
  }
}

export function buildHistoryScoreRows({ players, finalScores } = {}) {
  const rowsByPlayerId = new Map()

  if (Array.isArray(players)) {
    for (const player of players) {
      if (!player || typeof player !== 'object') {
        continue
      }

      const playerId = normalizePlayerId(player.player_id)
      if (playerId === null) {
        continue
      }

      rowsByPlayerId.set(playerId, createBaseRow(playerId, player))
    }
  }

  if (finalScores && typeof finalScores === 'object') {
    for (const [playerIdKey, scoreEntry] of Object.entries(finalScores)) {
      const playerId = normalizePlayerId(playerIdKey)
      if (playerId === null) {
        continue
      }

      const row = rowsByPlayerId.get(playerId) || createBaseRow(playerId)
      const scores = scoreEntry && typeof scoreEntry === 'object' ? scoreEntry : {}

      row.total = scores.total ?? null
      row.board = scores.board ?? null
      row.chain = scores.chain ?? null
      row.track = scores.track ?? null
      row.resource = scores.resource ?? null

      rowsByPlayerId.set(playerId, row)
    }
  }

  return Array.from(rowsByPlayerId.values()).sort((left, right) => left.player_id - right.player_id)
}
