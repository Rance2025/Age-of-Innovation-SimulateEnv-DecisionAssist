import test from 'node:test'
import assert from 'node:assert/strict'

import {
  createDraftSetupState,
  applyDraftSetupState,
  applyDraftSetupChange
} from './draftSetupState.js'

test('applyDraftSetupState copies selected setup tile arrays from full state', () => {
  const draftSetup = createDraftSetupState()
  const setup = {
    selected_planning_cards: [1, 3, 4],
    selected_factions: [2, 6, 9],
    selected_palace_tiles: [5, 8, 12]
  }

  applyDraftSetupState(draftSetup, setup)
  setup.selected_planning_cards.push(7)

  assert.deepEqual(draftSetup.selectedPlanningCards, [1, 3, 4])
  assert.deepEqual(draftSetup.selectedFactions, [2, 6, 9])
  assert.deepEqual(draftSetup.selectedPalaceTiles, [5, 8, 12])
})

test('applyDraftSetupChange replaces and updates draft setup tile lists', () => {
  const draftSetup = createDraftSetupState()

  applyDraftSetupChange(draftSetup, ['selected_factions'], [1, 4, 7], 'modified')
  applyDraftSetupChange(draftSetup, ['selected_factions', '1'], 5, 'modified')
  applyDraftSetupChange(draftSetup, ['selected_factions', '2'], null, 'removed')

  assert.deepEqual(draftSetup.selectedFactions, [1, 5])
})
