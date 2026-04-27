import test from 'node:test'
import assert from 'node:assert/strict'

import {
  getDraftSelectionState,
  isDraftSelectionTypeComplete
} from './draftBoardSelectionState.js'

const players = [
  { id: 0, planningCardId: 2, factionId: 4, palaceTileId: 8 },
  { id: 1, planningCardId: 3, factionId: 5, palaceTileId: 9 },
  { id: 2, planningCardId: 4, factionId: 6, palaceTileId: 10 }
]

test('getDraftSelectionState marks the player who selected a draft board item', () => {
  assert.deepEqual(getDraftSelectionState(players, 'planning', 3), {
    ownerPlayerId: 1,
    isSelected: true,
    isTypeComplete: true,
    isUnavailable: false
  })

  assert.deepEqual(getDraftSelectionState(players, 'faction', 6), {
    ownerPlayerId: 2,
    isSelected: true,
    isTypeComplete: true,
    isUnavailable: false
  })

  assert.deepEqual(getDraftSelectionState(players, 'palace', 8), {
    ownerPlayerId: 0,
    isSelected: true,
    isTypeComplete: true,
    isUnavailable: false
  })
})

test('getDraftSelectionState greys remaining items only after every player has selected that type', () => {
  assert.equal(isDraftSelectionTypeComplete(players, 'faction'), true)
  assert.equal(getDraftSelectionState(players, 'faction', 12).isUnavailable, true)

  const incompletePlayers = [
    { id: 0, factionId: 4 },
    { id: 1, factionId: null },
    { id: 2, factionId: 6 }
  ]

  assert.equal(isDraftSelectionTypeComplete(incompletePlayers, 'faction'), false)
  assert.equal(getDraftSelectionState(incompletePlayers, 'faction', 12).isUnavailable, false)
})
