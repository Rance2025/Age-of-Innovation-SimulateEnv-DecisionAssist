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

test('final score modal uses ranked score rows, right-aligned numeric columns, and a direct exit action', () => {
  assert.match(source, /<div class="final-score-grid final-score-header">[\s\S]*?<span>名次<\/span>[\s\S]*?<span>玩家<\/span>[\s\S]*?<span>ID\/策略<\/span>/)
  assert.match(source, /v-for="entry in finalScoreRows"/)
  assert.match(source, /class="final-score-rank"/)
  assert.match(source, /class="final-score-identity"/)
  assert.match(source, /function formatScoreValue\(value\)\s*\{\s*return value \?\? '--'\s*\}/)
  assert.match(source, /class="final-score-exit-btn"[\s\S]*?@click="handleFinalScoreExit"/)
  assert.match(source, /async function handleFinalScoreExit\(\)\s*\{[\s\S]*await leaveCurrentGame\(\)/)
  assert.match(source, /async function leaveCurrentGame\(\)\s*\{[\s\S]*await stopBackendGame\(\)[\s\S]*cleanupEndedGameSession\(\)/)
  assert.match(source, /async function handleEndGame\(\)\s*\{[\s\S]*await leaveCurrentGame\(\)/)
  assert.doesNotMatch(source, /\.final-score-row\.is-winner/)

  const gridStyles = cssBlock('.final-score-grid')
  const headerStyles = cssBlock('.final-score-header')
  const rowStyles = cssBlock('.final-score-row')
  const rankStyles = cssBlock('.final-score-rank')
  const rankIconStyles = cssBlock('.final-score-rank-icon')
  const actionsStyles = cssBlock('.final-score-actions')
  const exitButtonStyles = cssBlock('.final-score-exit-btn')

  assert.match(gridStyles, /grid-template-columns:\s*56px\s+84px\s+minmax\(156px,\s*1\.7fr\)\s+repeat\(5,\s*minmax\(68px,\s*0\.78fr\)\)/)
  assert.match(headerStyles, /padding:\s*0\s+20px\s+12px\s+12px/)
  assert.match(rowStyles, /padding:\s*13px\s+20px\s+13px\s+12px/)
  assert.match(rankStyles, /justify-content:\s*center/)
  assert.match(rankIconStyles, /display:\s*block/)
  assert.doesNotMatch(rankIconStyles, /translateX/)
  assert.match(source, /\.final-score-header\s*>\s*span:first-child,\s*\.final-score-row\s*>\s*span:first-child\s*\{[\s\S]*justify-self:\s*center[\s\S]*text-align:\s*center[\s\S]*transform:\s*translateX\(-8px\)/)
  assert.match(source, /\.final-score-header\s*>\s*span:nth-child\(n \+ 4\),\s*\.final-score-row\s*>\s*span:nth-child\(n \+ 4\)\s*\{[\s\S]*text-align:\s*right/)
  assert.match(actionsStyles, /display:\s*flex/)
  assert.match(actionsStyles, /justify-content:\s*flex-end/)
  assert.match(exitButtonStyles, /border:\s*1px solid rgba\(239,\s*68,\s*68,\s*0\.28\)/)
})
