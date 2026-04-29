import assert from 'node:assert/strict'
import { createPinia, setActivePinia } from 'pinia'

import { useTimerStore } from './timer.js'

setActivePinia(createPinia())
const timerStore = useTimerStore()

timerStore.updateFromTimerState({
  main_time_limit: 300000,
})

assert.equal(timerStore.getActionLogRemainingPercentage(300000), 100)
assert.equal(timerStore.getActionLogRemainingPercentage(150000), 50)
assert.equal(timerStore.getActionLogRemainingPercentage(60000), 20)

console.log('timer store tests passed')
