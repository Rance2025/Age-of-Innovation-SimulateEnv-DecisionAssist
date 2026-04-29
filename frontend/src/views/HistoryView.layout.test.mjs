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

{
  const pageStyles = cssBlock('.history-page')
  const containerStyles = cssBlock('.history-container')
  const bodyStyles = cssBlock('.history-body')
  const scrollAreaStyles = cssBlock('.games-scroll-area')
  const listStyles = cssBlock('.games-list')
  const paginationStyles = cssBlock('.pagination')
  const hoverStyles = cssBlock('.game-card:hover')
  const cardStyles = cssBlock('.game-card')
  const moveStyles = cssBlock('.history-list-move')
  const leaveToStyles = cssBlock('.history-list-leave-to')
  const pendingDeleteStyles = cssBlock('.game-card.is-pending-delete')

  assert.match(pageStyles, /height:\s*calc\(100vh\s*-\s*56px\)/)
  assert.match(pageStyles, /overflow:\s*hidden/)
  assert.doesNotMatch(pageStyles, /padding-top:\s*56px/)

  assert.match(containerStyles, /height:\s*100%/)
  assert.match(containerStyles, /display:\s*flex/)
  assert.match(containerStyles, /flex-direction:\s*column/)
  assert.match(containerStyles, /overflow:\s*hidden/)
  assert.match(containerStyles, /padding:\s*44px\s+24px\s+24px/)

  assert.match(bodyStyles, /flex:\s*1/)
  assert.match(bodyStyles, /min-height:\s*0/)
  assert.match(bodyStyles, /display:\s*flex/)
  assert.match(bodyStyles, /flex-direction:\s*column/)
  assert.match(bodyStyles, /overflow:\s*hidden/)

  assert.match(scrollAreaStyles, /flex:\s*1/)
  assert.match(scrollAreaStyles, /min-height:\s*0/)
  assert.match(scrollAreaStyles, /overflow-y:\s*auto/)

  assert.match(listStyles, /padding-bottom:\s*24px/)
  assert.match(listStyles, /position:\s*relative/)
  assert.match(paginationStyles, /flex-shrink:\s*0/)
  assert.match(paginationStyles, /margin-top:\s*24px/)
  assert.match(paginationStyles, /padding-top:\s*20px/)
  assert.doesNotMatch(cardStyles, /transition:\s*all/)
  assert.doesNotMatch(hoverStyles, /transform:/)
  assert.doesNotMatch(pendingDeleteStyles, /opacity:/)
  assert.match(moveStyles, /transition:\s*transform/)
  assert.match(source, /\.history-list-enter-active,\s*\.history-list-leave-active\s*\{[\s\S]*transition:/)
  assert.match(source, /\.history-list-leave-active\s*\{[\s\S]*position:\s*absolute/)
  assert.match(source, /\.history-list-leave-active\s*\{[\s\S]*pointer-events:\s*none/)
  assert.match(source, /\.history-list-leave-active\s*\{[\s\S]*z-index:\s*3/)
  assert.match(source, /\.history-list-leave-active\s*\{[\s\S]*transform-origin:\s*center\s+center/)
  assert.match(leaveToStyles, /transform:\s*scale\(/)
  assert.doesNotMatch(leaveToStyles, /translateY/)
}

assert.match(source, /<TransitionGroup[\s\S]*name="history-list"[\s\S]*tag="div"[\s\S]*class="games-list"/)
assert.match(source, /@before-leave="pinLeavingGameCard"/)
assert.match(source, /:class="\{\s*'is-confirming':\s*pendingDeleteGameId === game\.id\s*\}"/)
assert.match(source, /pendingDeleteGameId === game\.id \? '再次点击确认删除' : '删除'/)
assert.match(source, /pendingDeleteGameId === game\.id \? 'fas fa-check' : 'fas fa-trash'/)
assert.match(source, /const\s+GAME_LIST_TRANSITION_MS\s*=\s*320/)
assert.match(source, /const\s+wasLastGameOnPage\s*=\s*games\.value\.length\s*===\s*1\s*&&\s*pagination\.value\.page\s*>\s*1/)
assert.match(source, /const\s+pendingDeleteGameId\s*=\s*ref\(null\)/)
assert.match(source, /function\s+clearPendingDelete\(\)\s*\{\s*pendingDeleteGameId\.value\s*=\s*null\s*\}/)
assert.match(source, /function\s+pinLeavingGameCard\(el\)\s*\{/)
assert.match(source, /el\.style\.left\s*=\s*`\$\{el\.offsetLeft\}px`/)
assert.match(source, /el\.style\.top\s*=\s*`\$\{el\.offsetTop\}px`/)
assert.match(source, /el\.style\.width\s*=\s*`\$\{el\.offsetWidth\}px`/)
assert.match(source, /el\.style\.height\s*=\s*`\$\{el\.offsetHeight\}px`/)
assert.match(source, /async\s+function\s+waitForGameListTransition\(\)\s*\{/)
assert.match(source, /await\s+waitForGameListTransition\(\)/)
assert.doesNotMatch(source, /confirm\(/)
assert.match(source, /if\s*\(\s*pendingDeleteGameId\.value !== id\s*\)\s*\{\s*pendingDeleteGameId\.value\s*=\s*id\s*return\s*\}/)
assert.match(source, /games\.value\s*=\s*games\.value\.filter\(\(game\)\s*=>\s*game\.id !== id\)/)
assert.match(source, /games\.length\s*===\s*0\s*&&\s*deletingGameIds\.length\s*===\s*0/)
assert.match(source, /if\s*\(\s*wasLastGameOnPage\s*\)\s*\{\s*pagination\.value\.page\s*-=\s*1/)
assert.match(source, /await\s+loadGames\(\)/)
assert.match(source, /const\s+deleteButton\s*=\s*e\.target\.closest\('\.delete-btn'\)/)
assert.match(source, /if\s*\(!deleteButton && pendingDeleteGameId\.value !== null\)\s*\{\s*clearPendingDelete\(\)\s*\}/)
assert.doesNotMatch(source, /gameCardElements/)
assert.doesNotMatch(source, /gamesListRef/)
assert.doesNotMatch(source, /createLeavingGameCardClone/)
assert.doesNotMatch(source, /animateLeavingClone/)
assert.doesNotMatch(source, /\.game-card\.is-leaving/)

console.log('HistoryView layout tests passed')
