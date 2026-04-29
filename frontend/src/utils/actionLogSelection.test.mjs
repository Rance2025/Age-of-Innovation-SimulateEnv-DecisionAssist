import assert from 'node:assert/strict'

import {
  ACTION_LOG_SELECTION_MODE_OPTIONS,
  buildStrategyExecutePendingSelection,
  resolveControlCenterExecuteSelectionMode,
  resolveActionSelectionMode,
} from './actionLogSelection.js'

const optionIds = ACTION_LOG_SELECTION_MODE_OPTIONS.map((option) => option.id)
const strategyExecuteOption = ACTION_LOG_SELECTION_MODE_OPTIONS.find((option) => option.id === 'strategy_execute')

assert.deepEqual(optionIds, [
  'player_choice',
  'accepted',
  'rejected',
  'strategy_execute',
  'ai_agent',
  'timeout_agent',
])
assert.equal(strategyExecuteOption?.label, '直接执行')

assert.deepEqual(buildStrategyExecutePendingSelection({
  action_id: 12,
}), {
  actionId: 12,
  selectionMode: 'strategy_execute',
})

assert.equal(buildStrategyExecutePendingSelection({
  action_id: null,
}), null)

assert.equal(resolveControlCenterExecuteSelectionMode({
  hasRecommendedAction: true,
}), 'accepted')

assert.equal(resolveControlCenterExecuteSelectionMode({
  hasRecommendedAction: false,
}), 'strategy_execute')

assert.equal(resolveActionSelectionMode({
  actionId: 12,
  recommendedActionId: null,
  isStrategyExecute: false,
}), 'player_choice')

assert.equal(resolveActionSelectionMode({
  actionId: 12,
  recommendedActionId: 12,
  isStrategyExecute: false,
}), 'accepted')

assert.equal(resolveActionSelectionMode({
  actionId: 12,
  recommendedActionId: 18,
  isStrategyExecute: false,
}), 'rejected')

assert.equal(resolveActionSelectionMode({
  actionId: 12,
  recommendedActionId: 12,
  isStrategyExecute: true,
}), 'strategy_execute')

console.log('actionLogSelection tests passed')
