import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'

const globalPopoverSource = readFileSync('frontend/src/composables/useGlobalPopover.js', 'utf8')
const globalPopoverViewSource = readFileSync('frontend/src/components/GlobalPopover.vue', 'utf8')
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

test('global popover keeps direct scroll tracking and only animates placement flips', () => {
  assert.doesNotMatch(
    globalPopoverViewSource,
    /\.global-popover\s*\{[\s\S]*transition:\s*top\s+0\.\d+s\s+ease,\s*left\s+0\.\d+s\s+ease;/
  )
  assert.doesNotMatch(
    globalPopoverSource,
    /if \(isSwitching \|\| isPlacementAnimating\)/
  )
  assert.match(
    globalPopoverSource,
    /function animatePlacementFlip\(nextPlacement\)/
  )
  assert.match(
    globalPopoverSource,
    /if \(nextPlacement\.placement !== state\.actualPlacement\) \{\s*animatePlacementFlip\(nextPlacement\)/
  )
  assert.match(
    globalPopoverSource,
    /const firstRect = popoverEl\.getBoundingClientRect\(\)[\s\S]*applyCalculatedPlacement\(nextPlacement\)[\s\S]*const lastRect = popoverEl\.getBoundingClientRect\(\)[\s\S]*popoverEl\.style\.transition = 'none'[\s\S]*popoverEl\.style\.transform = `translate\(\$\{dx\}px, \$\{dy\}px\)`[\s\S]*requestAnimationFrame/
  )
  assert.match(
    globalPopoverSource,
    /stopPlacementAnimation\(\{\s*invalidate:\s*true,\s*preserveStyles:\s*true\s*\}\)/
  )
  assert.doesNotMatch(
    globalPopoverSource,
    /await nextTick\(\)[\s\S]*requestAnimationFrame\(\(\) => \{[\s\S]*const lastRect = popoverEl\.getBoundingClientRect\(\)/
  )
  assert.match(
    globalPopoverSource,
    /popoverEl\.style\.transition = 'transform 180ms ease'/
  )
})
