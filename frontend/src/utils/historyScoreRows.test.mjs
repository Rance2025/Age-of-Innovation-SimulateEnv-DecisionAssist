import assert from 'node:assert/strict'

import { getStrategyLabel } from '../constants/strategies.js'
import { buildHistoryScoreRows } from './historyScoreRows.js'

const interruptedRows = buildHistoryScoreRows({
  players: [
    { player_id: 0, player_type: 'human', player_input_id: 'alpha', strategy_name: '' },
    { player_id: 1, player_type: 'ai', player_input_id: '', strategy_name: 'random_pure' },
    { player_id: 2, player_type: 'human', player_input_id: 'gamma', strategy_name: '' },
  ],
  finalScores: null,
})

assert.deepEqual(
  interruptedRows.map((row) => ({
    player_id: row.player_id,
    player_label: row.player_label,
    identity_text: row.identity_text,
    identity_icon: row.identity_icon,
    identity_is_ai: row.identity_is_ai,
    rank_index: row.rank_index,
    rank_icon_class: row.rank_icon_class,
    rank_tone: row.rank_tone,
    total: row.total,
  })),
  [
    {
      player_id: 0,
      player_label: '1',
      identity_text: 'alpha',
      identity_icon: '',
      identity_is_ai: false,
      rank_index: null,
      rank_icon_class: '',
      rank_tone: '',
      total: null,
    },
    {
      player_id: 1,
      player_label: '2',
      identity_text: getStrategyLabel('random_pure'),
      identity_icon: 'fas fa-robot',
      identity_is_ai: true,
      rank_index: null,
      rank_icon_class: '',
      rank_tone: '',
      total: null,
    },
    {
      player_id: 2,
      player_label: '3',
      identity_text: 'gamma',
      identity_icon: '',
      identity_is_ai: false,
      rank_index: null,
      rank_icon_class: '',
      rank_tone: '',
      total: null,
    },
  ]
)

const rankedRows = buildHistoryScoreRows({
  players: [
    { type: 'ai', strategy_id: 'random_fast_action' },
    { type: 'human', player_input_id: 'beta' },
    { type: 'human', player_input_id: 'alpha' },
    { type: 'human', player_input_id: 'delta' },
  ],
  finalScores: {
    3: { total: 88, board: 26, chain: 18, track: 24, resource: 20 },
    1: { total: 101, board: 28, chain: 21, track: 25, resource: 27 },
    0: { total: 109, board: 31, chain: 20, track: 29, resource: 29 },
    2: { total: 96, board: 27, chain: 19, track: 23, resource: 27 },
  },
})

assert.deepEqual(
  rankedRows.map((row) => ({
    player_id: row.player_id,
    player_label: row.player_label,
    identity_text: row.identity_text,
    identity_icon: row.identity_icon,
    rank_index: row.rank_index,
    rank_icon_class: row.rank_icon_class,
    rank_tone: row.rank_tone,
    total: row.total,
  })),
  [
    {
      player_id: 0,
      player_label: '1',
      identity_text: getStrategyLabel('random_fast_action'),
      identity_icon: 'fas fa-robot',
      rank_index: 1,
      rank_icon_class: 'fas fa-medal',
      rank_tone: 'gold',
      total: 109,
    },
    {
      player_id: 1,
      player_label: '2',
      identity_text: 'beta',
      identity_icon: '',
      rank_index: 2,
      rank_icon_class: 'fas fa-medal',
      rank_tone: 'silver',
      total: 101,
    },
    {
      player_id: 2,
      player_label: '3',
      identity_text: 'alpha',
      identity_icon: '',
      rank_index: 3,
      rank_icon_class: 'fas fa-medal',
      rank_tone: 'bronze',
      total: 96,
    },
    {
      player_id: 3,
      player_label: '4',
      identity_text: 'delta',
      identity_icon: '',
      rank_index: 4,
      rank_icon_class: '',
      rank_tone: '',
      total: 88,
    },
  ]
)

console.log('historyScoreRows tests passed')
