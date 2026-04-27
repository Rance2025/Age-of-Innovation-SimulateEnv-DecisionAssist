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
  const visualStyles = cssBlock('.draft-item-visual')
  const imageStyles = cssBlock('.draft-item-image')

  assert.match(rowStyles, /flex-wrap:\s*nowrap/)
  assert.match(rowStyles, /width:\s*100%/)
  assert.match(itemStyles, /flex:\s*1\s+1\s+0/)
  assert.match(itemStyles, /min-width:\s*0/)
  assert.match(visualStyles, /width:\s*100%/)
  assert.match(visualStyles, /display:\s*flex/)
  assert.match(visualStyles, /flex-direction:\s*column/)
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
  assert.match(source, /class="draft-item-visual"/)
  assert.match(source, /class="draft-item-label"/)
})

test('game cards do not cap expanded content height', () => {
  const cardStyles = cssBlock('.game-card')
  const collapsedCardStyles = cssBlock('.game-card.collapsed')

  assert.doesNotMatch(cardStyles, /max-height:\s*60%/)
  assert.match(cardStyles, /display:\s*flex/)
  assert.match(cardStyles, /flex-direction:\s*column/)
  assert.match(cardStyles, /max-height:\s*100%/)
  assert.match(cardStyles, /transition:\s*max-height\s+0\.3s\s+ease/)
  assert.match(collapsedCardStyles, /max-height:\s*50px/)
})

test('draft board items render selected-player marker hooks and unavailable state hooks', () => {
  assert.match(source, /getDraftItemClass\('planning',\s*cardId\)/)
  assert.match(source, /getDraftItemStyle\('planning',\s*cardId\)/)
  assert.match(source, /getDraftOwnerLabel\('planning',\s*cardId\)/)
  assert.match(source, /class="draft-item-corner"/)

  const itemStyles = cssBlock('.draft-item')
  const selectedStyles = cssBlock('.draft-item.is-selected')
  const unavailableStyles = cssBlock('.draft-item.is-unavailable')
  const visualStyles = cssBlock('.draft-item-visual')
  const imageStyles = cssBlock('.draft-item-image')
  const labelStyles = cssBlock('.draft-item-label')
  const unavailableVisualStyles = cssBlock('.draft-item.is-unavailable .draft-item-visual')
  const cornerStyles = cssBlock('.draft-item-corner')

  assert.match(itemStyles, /border:\s*2px\s+solid\s+transparent/)
  assert.match(itemStyles, /background:\s*transparent/)
  assert.match(itemStyles, /box-shadow:\s*none/)
  assert.match(selectedStyles, /border-color:\s*var\(--draft-owner-color\)/)
  assert.match(selectedStyles, /box-shadow:\s*0\s+0\s+0\s+2px\s+var\(--draft-owner-color\)/)
  assert.doesNotMatch(selectedStyles, /outline:/)
  assert.doesNotMatch(selectedStyles, /outline-offset:/)
  assert.doesNotMatch(selectedStyles, /0\s+3px\s+12px/)
  assert.match(unavailableStyles, /filter:\s*saturate\(0\.15\)/)
  assert.match(visualStyles, /transition:[^;]*transform\s+0\.18s\s+ease/)
  assert.match(visualStyles, /transform-origin:\s*center/)
  assert.match(visualStyles, /border-radius:\s*6px/)
  assert.match(visualStyles, /overflow:\s*hidden/)
  assert.match(imageStyles, /border-radius:\s*6px\s+6px\s+0\s+0/)
  assert.match(labelStyles, /width:\s*100%/)
  assert.match(labelStyles, /flex:\s*0\s+0\s+auto/)
  assert.match(unavailableVisualStyles, /transform:\s*scale\(0\.85\)/)
  assert.doesNotMatch(source, /\.draft-item\.is-unavailable\s+\.draft-item-image\s*\{[\s\S]*?transform:\s*scale\(0\.85\)/)
  assert.doesNotMatch(source, /\.draft-item\.is-unavailable::after\s*\{/)
  assert.doesNotMatch(unavailableStyles, /grayscale/)
  assert.doesNotMatch(unavailableStyles, /opacity:\s*0\.[0-9]+/)
  assert.doesNotMatch(unavailableStyles, /brightness/)
  assert.match(cornerStyles, /clip-path:\s*polygon/)
})
