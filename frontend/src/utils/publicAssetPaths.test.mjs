import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'

test('GameView uses public URLs for image assets moved under public/assets', () => {
  const source = readFileSync('frontend/src/views/GameView.vue', 'utf8')

  assert.equal(source.includes('../../assets/images/'), false)
})
