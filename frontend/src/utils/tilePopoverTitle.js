const TERRAIN_ID_TO_LABEL = Object.freeze({
  0: '水域',
  1: '平原',
  2: '沼泽',
  3: '湖泊',
  4: '森林',
  5: '山脉',
  6: '荒地',
  7: '沙漠'
})

const TERRAIN_KEY_TO_LABEL = Object.freeze({
  water: '水域',
  plains: '平原',
  swamp: '沼泽',
  lake: '湖泊',
  forest: '森林',
  mountain: '山脉',
  wasteland: '荒地',
  desert: '沙漠'
})

const BUILDING_ID_TO_LABEL = Object.freeze({
  1: '车间',
  2: '工会',
  3: '宫殿',
  4: '学校',
  5: '大学',
  6: '塔楼',
  7: '纪念碑'
})

const CITY_TILE_ID_TO_LABEL = Object.freeze({
  1: '两书城',
  2: '四轨城',
  3: '两铲城',
  4: '八转城',
  5: '三矿城',
  6: '米宝城',
  7: '六钱城'
})

function resolveTerrainLabel(terrain) {
  if (terrain === null || terrain === undefined) return ''

  const normalizedTerrainId = Number(terrain)
  if (Number.isInteger(normalizedTerrainId) && Object.prototype.hasOwnProperty.call(TERRAIN_ID_TO_LABEL, normalizedTerrainId)) {
    return TERRAIN_ID_TO_LABEL[normalizedTerrainId]
  }

  const normalizedTerrainKey = String(terrain).trim().toLowerCase()
  return TERRAIN_KEY_TO_LABEL[normalizedTerrainKey] || ''
}

function resolveBuildingLabel(buildingId) {
  const normalizedBuildingId = Number(buildingId)
  if (!Number.isInteger(normalizedBuildingId)) return ''
  return BUILDING_ID_TO_LABEL[normalizedBuildingId] || ''
}

function resolveCityTileLabel(cityTileId) {
  const normalizedCityTileId = Number(cityTileId)
  if (!Number.isInteger(normalizedCityTileId)) return ''
  return CITY_TILE_ID_TO_LABEL[normalizedCityTileId] || ''
}

export function buildTilePopoverTitle({
  position,
  terrain,
  buildingId = 0,
  hasAnnex = false,
  cityTileId = null
}) {
  const normalizedPosition = typeof position === 'string' ? position.trim() : ''
  const terrainLabel = resolveTerrainLabel(terrain)
  const buildingLabel = resolveBuildingLabel(buildingId)
  const cityTileLabel = resolveCityTileLabel(cityTileId)
  const titleParts = []

  if (normalizedPosition) {
    titleParts.push(`${normalizedPosition}地块`)
  }

  if (terrainLabel) {
    titleParts.push(terrainLabel)
  }

  if (buildingLabel) {
    titleParts.push(buildingLabel)
  }

  if (hasAnnex) {
    titleParts.push('侧楼')
  }

  if (cityTileLabel) {
    titleParts.push(cityTileLabel)
  }

  return titleParts.join(' · ')
}
