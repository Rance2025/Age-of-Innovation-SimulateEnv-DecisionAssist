import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useNavigationStore = defineStore('navigation', () => {
  // 记录从哪个页面跳转到历史页面
  const historySource = ref('Home')

  function setHistorySource(source) {
    historySource.value = source
  }

  function getHistorySource() {
    return historySource.value
  }

  return {
    historySource,
    setHistorySource,
    getHistorySource
  }
})
