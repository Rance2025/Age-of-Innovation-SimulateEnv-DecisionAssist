const DRAFT_SELECTION_FIELD_BY_TYPE = {
  planning: 'planningCardId',
  faction: 'factionId',
  palace: 'palaceTileId'
}

function normalizeDraftBoardId(value) {
  const normalized = Number(value)
  return Number.isInteger(normalized) && normalized > 0 ? normalized : null
}

export function getDraftSelectionOwnerPlayerId(players, type, boardId) {
  const fieldName = DRAFT_SELECTION_FIELD_BY_TYPE[type]
  const normalizedBoardId = normalizeDraftBoardId(boardId)
  if (!fieldName || normalizedBoardId === null || !Array.isArray(players)) {
    return null
  }

  const owner = players.find((player) => normalizeDraftBoardId(player?.[fieldName]) === normalizedBoardId)
  const ownerPlayerId = Number(owner?.id)
  return Number.isInteger(ownerPlayerId) && ownerPlayerId >= 0 ? ownerPlayerId : null
}

export function isDraftSelectionTypeComplete(players, type) {
  const fieldName = DRAFT_SELECTION_FIELD_BY_TYPE[type]
  if (!fieldName || !Array.isArray(players) || players.length === 0) {
    return false
  }

  return players.every((player) => normalizeDraftBoardId(player?.[fieldName]) !== null)
}

export function getDraftSelectionState(players, type, boardId) {
  const ownerPlayerId = getDraftSelectionOwnerPlayerId(players, type, boardId)
  const isTypeComplete = isDraftSelectionTypeComplete(players, type)
  const isSelected = ownerPlayerId !== null

  return {
    ownerPlayerId,
    isSelected,
    isTypeComplete,
    isUnavailable: isTypeComplete && !isSelected
  }
}
