import assert from 'node:assert/strict'

import { GAME_MODE_OPTIONS, getGameModeIcon, getGameModeName } from './gameModeMeta.js'

assert.deepEqual(
  GAME_MODE_OPTIONS.map((mode) => mode.value),
  ['standard', 'quick', 'custom'],
)

assert.equal(getGameModeIcon('standard'), 'fas fa-chess')
assert.equal(getGameModeIcon('quick'), 'fas fa-bolt')
assert.equal(getGameModeIcon('custom'), 'fas fa-cogs')
assert.equal(getGameModeIcon('unknown'), 'fas fa-gamepad')

assert.equal(getGameModeName('standard'), '标准模式')
assert.equal(getGameModeName('quick'), '快速模式')
assert.equal(getGameModeName('custom'), '自定义')
assert.equal(getGameModeName('unknown'), 'unknown')

console.log('gameModeMeta tests passed')
