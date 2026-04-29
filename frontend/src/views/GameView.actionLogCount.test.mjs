import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'

const source = readFileSync('frontend/src/views/GameView.vue', 'utf8')

test('action log count pill excludes divider entries from filtered and total counts', () => {
  assert.match(
    source,
    /<span id="action-log-count">\{\{\s*filteredActionLogEntryCount\s*\}\}<\/span>\s*\/\s*\{\{\s*renderedActionLogEntryCount\s*\}\}\s*条/
  )

  assert.match(
    source,
    /const renderedActionLogEntryCount = computed\(\(\) => renderedActionLogs\.value\.filter\(\(entry\) => entry\.kind !== 'divider'\)\.length\)/
  )

  assert.match(
    source,
    /const filteredActionLogEntryCount = computed\(\(\) => filteredActionLogs\.value\.filter\(\(entry\) => entry\.kind !== 'divider'\)\.length\)/
  )
})
