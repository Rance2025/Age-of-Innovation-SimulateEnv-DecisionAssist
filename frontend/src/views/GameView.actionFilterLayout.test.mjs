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

test('action log filter modal assigns scroll ownership to the stacked right column sections', () => {
  assert.match(
    source,
    /<div class=\"action-filter-column action-filter-column--stacked\">[\s\S]*?按行动大类筛选/
  )

  const modalBodyStyles = cssBlock('.action-filter-modal-body')
  const rowStyles = cssBlock('.action-filter-row')
  const columnStyles = cssBlock('.action-filter-column')
  const wrapStyles = cssBlock('.action-filter-options--wrap')
  const stackedColumnStyles = cssBlock('.action-filter-column--stacked')
  const stackedSectionStyles = cssBlock('.action-filter-column--stacked .action-filter-section')
  const stackedWrapStyles = cssBlock('.action-filter-column--stacked .action-filter-options--wrap')

  assert.match(modalBodyStyles, /display:\s*flex/)
  assert.match(modalBodyStyles, /flex:\s*1/)
  assert.match(modalBodyStyles, /min-height:\s*0/)
  assert.match(modalBodyStyles, /overflow:\s*hidden/)

  assert.match(rowStyles, /flex:\s*1/)
  assert.match(rowStyles, /min-height:\s*0/)

  assert.doesNotMatch(columnStyles, /max-height:/)

  assert.doesNotMatch(wrapStyles, /max-height:/)
  assert.doesNotMatch(wrapStyles, /overflow-y:\s*auto/)

  assert.match(stackedColumnStyles, /overflow:\s*hidden/)
  assert.match(stackedSectionStyles, /flex:\s*1\s+1\s+0/)
  assert.match(stackedSectionStyles, /min-height:\s*0/)
  assert.match(stackedWrapStyles, /flex:\s*1\s+1\s+auto/)
  assert.match(stackedWrapStyles, /min-height:\s*0/)
  assert.match(stackedWrapStyles, /overflow-y:\s*auto/)
})
