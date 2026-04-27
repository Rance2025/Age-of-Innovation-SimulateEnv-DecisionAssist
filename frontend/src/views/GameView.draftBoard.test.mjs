import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'

const source = readFileSync('frontend/src/views/GameView.vue', 'utf8')

function escapeRegExp(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

function cssBlock(selector) {
  const match = source.match(new RegExp(`${escapeRegExp(selector)}\\s*\\{([\\s\\S]*?)\\}`, 'm'))
  assert.ok(match, `Missing CSS block for ${selector}`)
  return match[1]
}

test('draft board rows keep all selected images on one line and fill the row width', () => {
  const rowStyles = cssBlock('.draft-section-items')
  const itemStyles = cssBlock('.draft-item')
  const imageStyles = cssBlock('.draft-item-image')

  assert.match(rowStyles, /flex-wrap:\s*nowrap/)
  assert.match(rowStyles, /width:\s*100%/)
  assert.match(itemStyles, /flex:\s*1\s+1\s+0/)
  assert.match(itemStyles, /min-width:\s*0/)
  assert.match(imageStyles, /width:\s*100%/)
  assert.match(imageStyles, /height:\s*auto/)
  assert.match(imageStyles, /aspect-ratio:\s*var\(--draft-item-aspect-ratio\)/)
})

test('draft board collapse keeps content in flow so max-height can animate both directions', () => {
  const statusStyles = cssBlock('.draft-board-status')
  const collapsedStyles = cssBlock('.game-card.collapsed .draft-board-status')

  assert.match(statusStyles, /transition:\s*opacity\s+0\.3s\s+ease/)
  assert.doesNotMatch(collapsedStyles, /display:\s*none/)
  assert.match(collapsedStyles, /opacity:\s*0/)
})

test('draft board renders name labels for planning cards and factions plus number labels for palace tiles', () => {
  assert.match(source, /\{\{\s*planningCardIdToName\[cardId\]\s*\|\|\s*`规划卡 \$\{cardId\}`\s*\}\}/)
  assert.match(source, /\{\{\s*factionIdToName\[factionId\]\s*\|\|\s*`派系 \$\{factionId\}`\s*\}\}/)
  assert.match(source, /\{\{\s*palaceId\s*\}\}/)
  assert.match(source, /class="draft-item-label"/)
})
