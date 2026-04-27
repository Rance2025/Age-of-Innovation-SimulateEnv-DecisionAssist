import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'

const globalPopoverSource = readFileSync('frontend/src/composables/useGlobalPopover.js', 'utf8')
const gameViewSource = readFileSync('frontend/src/views/GameView.vue', 'utf8')
const playerTimerSource = readFileSync('frontend/src/components/PlayerTimer.vue', 'utf8')

test('stop-propagating outside controls close the global popover without changing switch clicks', () => {
  assert.match(playerTimerSource, /@click\.stop="toggleMode"/)
  assert.match(gameViewSource, /@click\.stop="openActionLogFilterModal"/)
  assert.match(playerTimerSource, /const globalPopover = useGlobalPopover\(\)/)
  assert.match(playerTimerSource, /globalPopover\.close\(\)/)
  assert.match(gameViewSource, /function openActionLogFilterModal\(\)\s*\{\s*globalPopover\.close\(\)/)
  assert.match(
    globalPopoverSource,
    /document\.addEventListener\('click',\s*clickOutsideHandler,\s*false\)/
  )
  assert.match(
    globalPopoverSource,
    /document\.removeEventListener\('click',\s*clickOutsideHandler,\s*false\)/
  )
})
