export const ACTION_LOG_SELECTION_MODE_OPTIONS = Object.freeze([
  { id: 'player_choice', label: '玩家选择' },
  { id: 'accepted', label: '采纳推荐' },
  { id: 'rejected', label: '拒绝推荐' },
  { id: 'strategy_execute', label: '直接执行' },
  { id: 'ai_agent', label: 'AI代理' },
  { id: 'timeout_agent', label: '超时代理' },
])

const ACTION_LOG_SELECTION_MODE_IDS = new Set(
  ACTION_LOG_SELECTION_MODE_OPTIONS.map((option) => option.id)
)

function normalizeActionId(actionId) {
  if (actionId === null || actionId === undefined || actionId === '') {
    return null
  }
  const normalized = Number(actionId)
  return Number.isInteger(normalized) ? normalized : null
}

export function resolveActionSelectionMode({
  actionId,
  recommendedActionId = null,
  isStrategyExecute = false,
} = {}) {
  if (isStrategyExecute) {
    return 'strategy_execute'
  }

  const normalizedActionId = normalizeActionId(actionId)
  const normalizedRecommendedActionId = normalizeActionId(recommendedActionId)

  if (normalizedActionId === null || normalizedRecommendedActionId === null) {
    return 'player_choice'
  }

  return normalizedActionId === normalizedRecommendedActionId
    ? 'accepted'
    : 'rejected'
}

export function normalizeActionHistorySelectionMode(selectionMode) {
  if (typeof selectionMode !== 'string') {
    return 'player_choice'
  }

  const normalizedMode = selectionMode.trim()
  return ACTION_LOG_SELECTION_MODE_IDS.has(normalizedMode)
    ? normalizedMode
    : 'player_choice'
}

export function normalizeActionHistoryStrategyName(strategyName) {
  return typeof strategyName === 'string' ? strategyName.trim() : ''
}

export function resolveControlCenterExecuteSelectionMode({
  hasRecommendedAction = false,
} = {}) {
  return hasRecommendedAction ? 'accepted' : 'strategy_execute'
}

export function buildStrategyExecutePendingSelection(payload) {
  const actionId = normalizeActionId(payload?.action_id)
  if (actionId === null) {
    return null
  }

  return {
    actionId,
    selectionMode: 'strategy_execute',
  }
}
