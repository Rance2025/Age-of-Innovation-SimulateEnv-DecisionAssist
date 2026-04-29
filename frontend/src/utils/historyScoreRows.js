import { getStrategyLabel } from '../constants/strategies.js'

function normalizePlayerId(playerId, fallbackPlayerId = null) {
  const normalized = Number(playerId)
  if (!Number.isInteger(normalized) || normalized < 0) {
    return Number.isInteger(fallbackPlayerId) && fallbackPlayerId >= 0 ? fallbackPlayerId : null
  }

  return normalized
}

function normalizePlayerType(player = {}) {
  const playerType = typeof player.player_type === 'string'
    ? player.player_type.trim()
    : (typeof player.type === 'string' ? player.type.trim() : '')

  return playerType || 'human'
}

function resolvePlayerInputId(player = {}, playerType = normalizePlayerType(player)) {
  const playerInputId = typeof player.player_input_id === 'string' ? player.player_input_id.trim() : ''
  if (playerInputId) {
    return playerInputId
  }

  const args = typeof player.args === 'string' ? player.args.trim() : ''
  return playerType === 'human' ? args : ''
}

function resolveStrategyId(player = {}, playerType = normalizePlayerType(player)) {
  const strategyName = typeof player.strategy_name === 'string' ? player.strategy_name.trim() : ''
  if (strategyName) {
    return strategyName
  }

  const strategyId = typeof player.strategy_id === 'string' ? player.strategy_id.trim() : ''
  if (strategyId) {
    return strategyId
  }

  const args = typeof player.args === 'string' ? player.args.trim() : ''
  return playerType === 'ai' ? args : ''
}

function normalizeScoreValue(value) {
  if (value === null || value === undefined || value === '') {
    return null
  }

  const normalized = Number(value)
  return Number.isFinite(normalized) ? normalized : null
}

function resolveStrategyText(strategyName) {
  if (!strategyName) {
    return '--'
  }

  const strategyLabel = getStrategyLabel(strategyName)
  return strategyLabel === '未知策略' ? strategyName : strategyLabel
}

function createBaseRow(playerId, player = {}) {
  const playerType = normalizePlayerType(player)
  const playerInputId = resolvePlayerInputId(player, playerType)
  const strategyId = resolveStrategyId(player, playerType)
  const isAiPlayer = playerType === 'ai'

  return {
    player_id: playerId,
    player_label: String(playerId + 1),
    rank_index: null,
    rank_icon_class: '',
    rank_tone: '',
    identity_text: isAiPlayer ? resolveStrategyText(strategyId) : (playerInputId || '--'),
    identity_icon: isAiPlayer ? 'fas fa-robot' : '',
    identity_is_ai: isAiPlayer,
    total: null,
    board: null,
    chain: null,
    track: null,
    resource: null,
  }
}

function hasRankedTotal(row) {
  return Number.isFinite(row?.total)
}

function compareScoreRows(left, right) {
  const leftHasTotal = hasRankedTotal(left)
  const rightHasTotal = hasRankedTotal(right)

  if (leftHasTotal && rightHasTotal && left.total !== right.total) {
    return right.total - left.total
  }

  if (leftHasTotal !== rightHasTotal) {
    return leftHasTotal ? -1 : 1
  }

  return left.player_id - right.player_id
}

function resolveRankTone(rankIndex) {
  if (rankIndex === 1) return 'gold'
  if (rankIndex === 2) return 'silver'
  if (rankIndex === 3) return 'bronze'
  return ''
}

export function buildHistoryScoreRows({ players, finalScores } = {}) {
  const rowsByPlayerId = new Map()

  if (Array.isArray(players)) {
    for (const [playerIndex, player] of players.entries()) {
      if (!player || typeof player !== 'object') {
        continue
      }

      const playerId = normalizePlayerId(player.player_id, playerIndex)
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

      row.total = normalizeScoreValue(scores.total)
      row.board = normalizeScoreValue(scores.board)
      row.chain = normalizeScoreValue(scores.chain)
      row.track = normalizeScoreValue(scores.track)
      row.resource = normalizeScoreValue(scores.resource)

      rowsByPlayerId.set(playerId, row)
    }
  }

  const sortedRows = Array.from(rowsByPlayerId.values()).sort(compareScoreRows)
  let rankedPosition = 0

  return sortedRows.map((row) => {
    if (!hasRankedTotal(row)) {
      return row
    }

    rankedPosition += 1
    const rankTone = resolveRankTone(rankedPosition)

    return {
      ...row,
      rank_index: rankedPosition,
      rank_icon_class: rankTone ? 'fas fa-medal' : '',
      rank_tone: rankTone,
    }
  })
}
