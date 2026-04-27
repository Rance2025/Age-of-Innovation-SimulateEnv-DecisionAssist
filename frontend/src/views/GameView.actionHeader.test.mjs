import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'

const source = readFileSync('frontend/src/views/GameView.vue', 'utf8')

test('available action header count pill keeps the 0.9.5.20 text wrapper', () => {
  assert.match(
    source,
    /<div class="action-count">共\s*<span id="action-count">\{\{\s*actionCount\s*\}\}<\/span>\s*项<\/div>/
  )
})
