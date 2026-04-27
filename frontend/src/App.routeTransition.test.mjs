import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'

const source = readFileSync('frontend/src/App.vue', 'utf8')

test('router transition keeps a stable element child around async route components', () => {
  assert.match(source, /<transition\s+name="page"\s+mode="out-in">/)
  assert.match(source, /<div\s+class="route-page"\s+:key="route\.path">/)
  assert.match(source, /<component\s+:is="Component"\s*\/>/)
  assert.match(source, /\.route-page\s*\{/)
})
