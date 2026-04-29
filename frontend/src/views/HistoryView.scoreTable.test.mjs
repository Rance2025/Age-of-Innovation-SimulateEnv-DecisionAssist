import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'

const source = readFileSync('frontend/src/views/HistoryView.vue', 'utf8')

function escapeRegExp(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

function cssBlock(selector) {
  const match = source.match(new RegExp(`${escapeRegExp(selector)}\\s*\\{([\\s\\S]*?)\\}`, 'm'))
  assert.ok(match, `Missing CSS block for ${selector}`)
  return match[1]
}

test('history score table shows ranked rows with medal icons and right-aligned numeric columns', () => {
  assert.match(source, /<div class="score-header">[\s\S]*?<span>名次<\/span>[\s\S]*?<span>玩家<\/span>[\s\S]*?<span>ID\/策略<\/span>/)
  assert.match(source, /class="score-rank"/)
  assert.match(source, /:class="\[pr\.rank_icon_class,\s*`is-\$\{pr\.rank_tone\}`\]"/)

  const rowStyles = cssBlock('.score-header,\n.score-row')
  const rankStyles = cssBlock('.score-rank')
  const rankIconStyles = cssBlock('.score-rank-icon')
  const goldStyles = cssBlock('.score-rank-icon.is-gold')
  const silverStyles = cssBlock('.score-rank-icon.is-silver')
  const bronzeStyles = cssBlock('.score-rank-icon.is-bronze')

  assert.match(rowStyles, /grid-template-columns:\s*0\.7fr\s+0\.9fr\s+2\.08fr\s+repeat\(5,\s*minmax\(0,\s*0\.88fr\)\)/)
  assert.match(rankStyles, /justify-content:\s*center/)
  assert.match(rankIconStyles, /display:\s*block/)
  assert.doesNotMatch(rankIconStyles, /translateX/)
  assert.match(source, /\.score-header\s*>\s*span:first-child,\s*\.score-row\s*>\s*span:first-child\s*\{[\s\S]*justify-self:\s*center[\s\S]*text-align:\s*center[\s\S]*transform:\s*translateX\(-8px\)/)
  assert.match(source, /\.score-row\s*>\s*span:nth-child\(n \+ 4\),\s*\.score-header\s*>\s*span:nth-child\(n \+ 4\)\s*\{[\s\S]*text-align:\s*right/)
  assert.match(goldStyles, /color:\s*#f5c451/)
  assert.match(silverStyles, /color:\s*#c2ccd6/)
  assert.match(bronzeStyles, /color:\s*#c9895a/)
})
