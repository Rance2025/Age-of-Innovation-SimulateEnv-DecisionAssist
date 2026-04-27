const DRAFT_SETUP_FIELD_MAP = {
  selected_planning_cards: 'selectedPlanningCards',
  selected_factions: 'selectedFactions',
  selected_palace_tiles: 'selectedPalaceTiles'
}

export function createDraftSetupState() {
  return {
    selectedPlanningCards: [],
    selectedFactions: [],
    selectedPalaceTiles: []
  }
}

export function applyDraftSetupState(target, setup = {}) {
  Object.entries(DRAFT_SETUP_FIELD_MAP).forEach(([backendKey, frontendKey]) => {
    target[frontendKey] = Array.isArray(setup[backendKey])
      ? [...setup[backendKey]]
      : []
  })
}

export function applyDraftSetupChange(target, setupKeys, value, changeType = 'modified') {
  if (!Array.isArray(setupKeys) || setupKeys.length === 0) {
    return false
  }

  const frontendKey = DRAFT_SETUP_FIELD_MAP[setupKeys[0]]
  if (!frontendKey) {
    return false
  }

  if (setupKeys.length === 1) {
    target[frontendKey] = changeType === 'removed'
      ? []
      : Array.isArray(value) ? [...value] : []
    return true
  }

  const index = Number.parseInt(setupKeys[1], 10)
  if (!Number.isInteger(index) || index < 0) {
    return true
  }

  if (!Array.isArray(target[frontendKey])) {
    target[frontendKey] = []
  }

  if (changeType === 'removed') {
    target[frontendKey].splice(index, 1)
  } else {
    target[frontendKey][index] = value
  }

  return true
}
