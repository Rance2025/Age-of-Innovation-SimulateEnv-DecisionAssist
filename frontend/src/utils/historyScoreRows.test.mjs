import assert from 'node:assert/strict'

import { buildHistoryScoreRows } from './historyScoreRows.js'

const interruptedRows = buildHistoryScoreRows({
  players: [
    { player_id: 0, player_type: 'human', player_input_id: 'alpha', strategy_name: '' },
    { player_id: 1, player_type: 'ai', player_input_id: '', strategy_name: 'random_pure' },
    { player_id: 2, player_type: 'human', player_input_id: 'gamma', strategy_name: '' },
  ],
  finalScores: null,
})

assert.deepEqual(interruptedRows, [
  {
    player_id: 0,
    player_label: '1',
    identity_text: 'alpha',
    identity_icon: '',
    identity_is_ai: false,
    total: null,
    board: null,
    chain: null,
    track: null,
    resource: null,
  },
  {
    player_id: 1,
    player_label: '2',
    identity_text: '随机 · 完全',
    identity_icon: 'fas fa-robot',
    identity_is_ai: true,
    total: null,
    board: null,
    chain: null,
    track: null,
    resource: null,
  },
  {
    player_id: 2,
    player_label: '3',
    identity_text: 'gamma',
    identity_icon: '',
    identity_is_ai: false,
    total: null,
    board: null,
    chain: null,
    track: null,
    resource: null,
  },
])

const finishedRows = buildHistoryScoreRows({
  players: [
    { player_id: 2, player_type: 'human', player_input_id: 'charlie', strategy_name: '' },
    { player_id: 0, player_type: 'human', player_input_id: 'alpha', strategy_name: '' },
  ],
  finalScores: {
    0: { total: 120, board: 40, chain: 20, track: 35, resource: 25 },
    2: { total: 115, board: 38, chain: 18, track: 34, resource: 25 },
  },
})

assert.deepEqual(finishedRows, [
  {
    player_id: 0,
    player_label: '1',
    identity_text: 'alpha',
    identity_icon: '',
    identity_is_ai: false,
    total: 120,
    board: 40,
    chain: 20,
    track: 35,
    resource: 25,
  },
  {
    player_id: 2,
    player_label: '3',
    identity_text: 'charlie',
    identity_icon: '',
    identity_is_ai: false,
    total: 115,
    board: 38,
    chain: 18,
    track: 34,
    resource: 25,
  },
])

console.log('historyScoreRows tests passed')
