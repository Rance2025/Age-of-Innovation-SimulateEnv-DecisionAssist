import { ref, computed } from 'vue'

export function usePopoverPosition() {
  const position = ref({ top: 0, left: 0 })
  const actualPlacement = ref('bottom')

  const viewportPadding = 12

  function calculatePosition(triggerEl, popoverEl, preferredPlacement = 'auto', offset = 8) {
    if (!triggerEl || !popoverEl) return

    // 如果 triggerEl 是 display: contents，使用其第一个子元素
    let actualTriggerEl = triggerEl
    const triggerStyle = window.getComputedStyle(triggerEl)
    if (triggerStyle.display === 'contents' && triggerEl.firstElementChild) {
      actualTriggerEl = triggerEl.firstElementChild
    }

    const triggerRect = actualTriggerEl.getBoundingClientRect()
    // 使用 offsetWidth/offsetHeight 获取实际布局尺寸，不受 CSS transform（如 Vue Transition 的 scale）影响
    const popoverWidth = popoverEl.offsetWidth
    const popoverHeight = popoverEl.offsetHeight
    const viewportWidth = window.innerWidth
    const viewportHeight = window.innerHeight

    const placements = preferredPlacement === 'auto' 
      ? ['bottom', 'top', 'right', 'left'] 
      : [preferredPlacement]

    for (const placement of placements) {
      let top = 0
      let left = 0

      switch (placement) {
        case 'bottom':
          top = triggerRect.bottom + offset
          left = triggerRect.left + (triggerRect.width - popoverWidth) / 2
          break
        case 'top':
          top = triggerRect.top - popoverHeight - offset
          left = triggerRect.left + (triggerRect.width - popoverWidth) / 2
          break
        case 'right':
          top = triggerRect.top + (triggerRect.height - popoverHeight) / 2
          left = triggerRect.right + offset
          break
        case 'left':
          top = triggerRect.top + (triggerRect.height - popoverHeight) / 2
          left = triggerRect.left - popoverWidth - offset
          break
      }

      // 检查是否超出视口
      const fitsHorizontally = left >= viewportPadding && 
        left + popoverWidth <= viewportWidth - viewportPadding
      const fitsVertically = top >= viewportPadding && 
        top + popoverHeight <= viewportHeight - viewportPadding

      if (fitsHorizontally && fitsVertically) {
        position.value = { top, left }
        actualPlacement.value = placement
        return
      }
    }

    // 如果都不合适，使用 bottom 并限制在视口内
    let top = triggerRect.bottom + offset
    let left = triggerRect.left + (triggerRect.width - popoverWidth) / 2
    
    top = Math.max(viewportPadding, Math.min(top, viewportHeight - popoverHeight - viewportPadding))
    left = Math.max(viewportPadding, Math.min(left, viewportWidth - popoverWidth - viewportPadding))
    
    position.value = { top, left }
    actualPlacement.value = 'bottom'
  }

  return {
    position: computed(() => position.value),
    actualPlacement: computed(() => actualPlacement.value),
    calculatePosition
  }
}
