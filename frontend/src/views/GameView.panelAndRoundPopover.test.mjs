import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'

const gameViewSource = readFileSync('frontend/src/views/GameView.vue', 'utf8')
const globalPopoverSource = readFileSync('frontend/src/components/GlobalPopover.vue', 'utf8')
const globalPopoverContentSource = readFileSync('frontend/src/components/GlobalPopoverContent.vue', 'utf8')

function escapeRegExp(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

function cssBlock(source, selector) {
  const match = source.match(new RegExp(`${escapeRegExp(selector)}\\s*\\{([\\s\\S]*?)\\}`, 'm'))
  assert.ok(match, `Missing CSS block for ${selector}`)
  return match[1]
}

test('inactive palace styling belongs to the popover preview, not the player panel badge', () => {
  assert.doesNotMatch(gameViewSource, /\.palace-tile-badge\.is-inactive\s*\{/)
  assert.doesNotMatch(gameViewSource, /\.palace-tile-badge\.is-inactive \.palace-tile-badge-value\s*\{/)
  assert.doesNotMatch(gameViewSource, /\.palace-tile-badge\.is-inactive \.palace-tile-badge-status\s*\{/)

  const inactiveImageStyles = cssBlock(globalPopoverContentSource, '.entity-preview-image.is-inactive')
  const inactiveOverlayStyles = cssBlock(globalPopoverContentSource, '.entity-preview-image-overlay')
  const inactiveIconStyles = cssBlock(globalPopoverContentSource, '.entity-preview-status-icon i')

  assert.match(globalPopoverContentSource, /v-if="inactive"/)
  assert.match(globalPopoverContentSource, /class="entity-preview-image-overlay"/)
  assert.match(globalPopoverContentSource, /class="entity-preview-status-icon"/)
  assert.match(inactiveImageStyles, /filter:\s*saturate\(0\.68\)/)
  assert.match(inactiveOverlayStyles, /inset:\s*0/)
  assert.match(inactiveOverlayStyles, /background:\s*rgba\(113,\s*120,\s*132,\s*0\.42\)/)
  assert.match(inactiveOverlayStyles, /justify-content:\s*center/)
  assert.match(inactiveIconStyles, /font-size:\s*4rem/)
})

test('round 6 popover passes final scoring overlay layer and popover content renders it', () => {
  assert.match(gameViewSource, /overlayLayerStyle:\s*getRoundPopoverOverlayStyle\(roundNumber,\s*roundState\)/)
  assert.match(gameViewSource, /function getRoundPopoverOverlayStyle\(roundNumber,\s*roundState\)/)
  assert.match(gameViewSource, /getFinalScoringOverlaySpriteStyleByBackendId\(roundState\.finalScoringId\)/)

  assert.match(globalPopoverSource, /:overlay-layer-style="data\.overlayLayerStyle"/)
  assert.match(globalPopoverContentSource, /overlayLayerStyle:\s*Object/)
  assert.match(globalPopoverContentSource, /v-if="overlayLayerStyle"/)
  assert.match(globalPopoverContentSource, /class="entity-preview-image-layer entity-preview-image-overlay-layer"/)
})
