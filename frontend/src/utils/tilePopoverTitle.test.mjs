import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'

let buildTilePopoverTitle

try {
  ({ buildTilePopoverTitle } = await import('./tilePopoverTitle.js'))
} catch {
  buildTilePopoverTitle = undefined
}

const gameViewSource = readFileSync('frontend/src/views/GameView.vue', 'utf8')

test('buildTilePopoverTitle exists and formats the required Chinese title parts', () => {
  assert.equal(typeof buildTilePopoverTitle, 'function')

  assert.equal(
    buildTilePopoverTitle({
      position: 'A1',
      terrain: 4,
      buildingId: 3,
      hasAnnex: true,
      cityTileId: 1
    }),
    'A1地块 · 森林 · 宫殿 · 侧楼 · 两书城'
  )

  assert.equal(
    buildTilePopoverTitle({
      position: 'C7',
      terrain: '6',
      buildingId: 0,
      hasAnnex: false,
      cityTileId: null
    }),
    'C7地块 · 荒地'
  )

  assert.equal(
    buildTilePopoverTitle({
      position: 'H12',
      terrain: 'lake',
      buildingId: 7,
      hasAnnex: false,
      cityTileId: 6
    }),
    'H12地块 · 湖泊 · 纪念碑 · 米宝城'
  )
})

test('GameView uses the tile popover title builder instead of hardcoded English terrain text', () => {
  assert.match(gameViewSource, /import\s+\{\s*buildTilePopoverTitle\s*\}\s+from\s+'..\/utils\/tilePopoverTitle\.js'/)
  assert.match(gameViewSource, /title:\s*buildTilePopoverTitle\(\s*\{/)
  assert.doesNotMatch(gameViewSource, /title:\s*`\$\{position\}\s+地块\s+·\s+\$\{terrainName\}`/)
})
