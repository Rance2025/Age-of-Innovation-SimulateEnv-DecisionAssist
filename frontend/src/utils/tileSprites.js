const ROUND_SCORING_SPRITE_URL = '/assets/images/round_scoring_tiles.png'
const ROUND_BOOSTER_SPRITE_URL = '/assets/images/round_boosters.png'

const ROUND_SCORING_TILE_POSITIONS = Object.freeze([
  0, 6.25, 12.5, 18.75, 25, 31.25, 37.5, 43.75,
  50, 56.25, 62.5, 68.75, 75, 81.25, 87.5, 93.75, 100
])

const ROUND_SCORING_FRONT_INDEX_BY_BACKEND_ID = Object.freeze([2, 11, 1, 8, 9, 6, 10, 3, 4, 5, 7, 0])
const FINAL_SCORING_RELATIVE_INDEX_BY_BACKEND_ID = Object.freeze([3, 0, 2, 1])
const FINAL_SCORING_SELECTION_POSITIONS = Object.freeze([75.7576, 81.8182, 87.8788, 93.9394])
const ROUND_BOOSTER_TILE_POSITIONS = Object.freeze([0, 11.1111, 22.2222, 33.3333, 44.4444, 55.5556, 66.6667, 77.7778, 88.8889, 100])
const ROUND_BOOSTER_INDEX_BY_BACKEND_ID = Object.freeze([0, 4, 5, 1, 2, 9, 8, 3, 6, 7])

const ROUND_SCORING_BACKGROUND_SIZE = `${(3978 / 232) * 100}% 100%`
const FINAL_SCORING_SELECTION_BACKGROUND_SIZE = '3400% 100%'
const ROUND_BOOSTER_BACKGROUND_SIZE = `${(1500 / 148) * 100}% 200%`

function normalizeId(value, min, max) {
  const normalizedValue = Number(value)
  if (!Number.isInteger(normalizedValue) || normalizedValue < min || normalizedValue > max) {
    return null
  }

  return normalizedValue
}

function buildSpriteStyle(backgroundImage, backgroundSize, backgroundPositionX, backgroundPositionY = '0%') {
  return {
    backgroundImage: `url(${backgroundImage})`,
    backgroundRepeat: 'no-repeat',
    backgroundSize,
    backgroundPositionX: `${backgroundPositionX}%`,
    backgroundPositionY
  }
}

function getFinalScoringSpriteIndexByBackendId(backendId) {
  const normalizedBackendId = normalizeId(backendId, 1, 4)
  if (normalizedBackendId === null) {
    return null
  }

  return 12 + FINAL_SCORING_RELATIVE_INDEX_BY_BACKEND_ID[normalizedBackendId - 1]
}

export function getRoundScoringSpriteStyleByBackendId(backendId) {
  const normalizedBackendId = normalizeId(backendId, 1, 12)
  if (normalizedBackendId === null) {
    return {}
  }

  const spriteIndex = ROUND_SCORING_FRONT_INDEX_BY_BACKEND_ID[normalizedBackendId - 1]
  return buildSpriteStyle(
    ROUND_SCORING_SPRITE_URL,
    ROUND_SCORING_BACKGROUND_SIZE,
    ROUND_SCORING_TILE_POSITIONS[spriteIndex]
  )
}

export function getRoundScoringBackSpriteStyle() {
  return buildSpriteStyle(
    ROUND_SCORING_SPRITE_URL,
    ROUND_SCORING_BACKGROUND_SIZE,
    ROUND_SCORING_TILE_POSITIONS[16]
  )
}

export function getFinalScoringOverlaySpriteStyleByBackendId(backendId) {
  const spriteIndex = getFinalScoringSpriteIndexByBackendId(backendId)
  if (spriteIndex === null) {
    return {}
  }

  return buildSpriteStyle(
    ROUND_SCORING_SPRITE_URL,
    ROUND_SCORING_BACKGROUND_SIZE,
    ROUND_SCORING_TILE_POSITIONS[spriteIndex]
  )
}

export function getFinalScoringSelectionSpriteStyleByBackendId(backendId) {
  const normalizedBackendId = normalizeId(backendId, 1, 4)
  if (normalizedBackendId === null) {
    return {}
  }

  const spriteIndex = FINAL_SCORING_RELATIVE_INDEX_BY_BACKEND_ID[normalizedBackendId - 1]
  return buildSpriteStyle(
    ROUND_SCORING_SPRITE_URL,
    FINAL_SCORING_SELECTION_BACKGROUND_SIZE,
    FINAL_SCORING_SELECTION_POSITIONS[spriteIndex]
  )
}

export function getRoundBoosterFrontSpriteStyleByBackendId(backendId) {
  const normalizedBackendId = normalizeId(backendId, 1, 10)
  if (normalizedBackendId === null) {
    return {}
  }

  const spriteIndex = ROUND_BOOSTER_INDEX_BY_BACKEND_ID[normalizedBackendId - 1]
  return buildSpriteStyle(
    ROUND_BOOSTER_SPRITE_URL,
    ROUND_BOOSTER_BACKGROUND_SIZE,
    ROUND_BOOSTER_TILE_POSITIONS[spriteIndex],
    '0%'
  )
}

export function getRoundBoosterBackSpriteStyleByBackendId(backendId) {
  const normalizedBackendId = normalizeId(backendId, 1, 10)
  if (normalizedBackendId === null) {
    return {}
  }

  const spriteIndex = ROUND_BOOSTER_INDEX_BY_BACKEND_ID[normalizedBackendId - 1]
  return buildSpriteStyle(
    ROUND_BOOSTER_SPRITE_URL,
    ROUND_BOOSTER_BACKGROUND_SIZE,
    ROUND_BOOSTER_TILE_POSITIONS[spriteIndex],
    '100%'
  )
}
