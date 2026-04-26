import { reactive, computed, nextTick } from 'vue'
import { animateFlip, cancelFlip } from './useFlipTransition.js'

// ==================== 状态 ====================

const state = reactive({
  visible: false,
  status: 'closed', // 'closed' | 'opening' | 'open' | 'switching' | 'closing'
  currentTriggerId: null,
  position: { top: -9999, left: -9999 },
  actualPlacement: 'bottom',
  data: null,
  config: null
})

const viewportPadding = 12

// ==================== 模块级私有变量 ====================

let popoverEl = null
let scrollHandler = null
let resizeHandler = null
let keydownHandler = null
let clickOutsideHandler = null

// 切换动画状态
let isSwitching = false
let pendingSwitchConfig = null
let pendingUpdatePosition = false

// ==================== 导出 API ====================

export function useGlobalPopover() {
  return {
    // 状态（只读）
    visible: computed(() => state.visible),
    status: computed(() => state.status),
    currentTriggerId: computed(() => state.currentTriggerId),
    position: computed(() => state.position),
    actualPlacement: computed(() => state.actualPlacement),
    data: computed(() => state.data),
    config: computed(() => state.config),
    isSwitching: computed(() => state.status === 'switching'),

    // 方法
    open,
    close,
    updatePosition,
    onAfterLeave,
    cleanup,
    setPopoverElement
  }
}

export function setPopoverElement(el) {
  popoverEl = el
  if (!el) {
    cleanup()
  }
}

/**
 * 完全清理：关闭弹窗、移除事件、重置状态
 */
export function cleanup() {
  // 取消可能正在进行的 FLIP 动画
  if (popoverEl) {
    cancelFlip(popoverEl)
  }

  unbindEvents()
  isSwitching = false
  pendingSwitchConfig = null
  pendingUpdatePosition = false

  // 重置状态
  state.visible = false
  state.status = 'closed'
  state.currentTriggerId = null
  state.data = null
  state.config = null
  state.position = { top: -9999, left: -9999 }
  state.actualPlacement = 'bottom'
}

// ==================== 打开 / 切换 / 关闭 ====================

function open(config) {
  if (!config || !config.id || !config.triggerEl) return

  // Toggle：点击同一元素则关闭
  if (state.currentTriggerId === config.id && state.visible && state.status !== 'closing') {
    close()
    return
  }

  const isSwitch = state.visible && state.currentTriggerId !== config.id

  if (isSwitch) {
    // 正在切换中：排队等待当前动画完成
    if (isSwitching) {
      pendingSwitchConfig = config
      return
    }
    performSwitch(config)
  } else {
    performOpen(config)
  }
}

function performOpen(config) {
  state.status = 'opening'
  state.currentTriggerId = config.id
  state.data = config.data
  state.config = config
  state.visible = true

  nextTick(() => {
    requestAnimationFrame(() => {
      // 计算初始位置（避免从左上角闪现）
      calculatePosition(config.triggerEl, config.placement, config.offset)

      // 再次 rAF 确保位置已应用，然后标记为完全打开
      requestAnimationFrame(() => {
        if (state.status === 'opening') {
          state.status = 'open'
        }
        bindEvents(config)
      })
    })
  })
}

async function performSwitch(config) {
  if (!popoverEl) return

  isSwitching = true
  state.status = 'switching'

  // 重新绑定事件（排除条件可能不同）
  unbindEvents()
  bindEvents(config)

  try {
    await animateFlip(
      popoverEl,
      () => {
        // 更新数据与位置（同步执行，FLIP 会自动等待 DOM 更新）
        state.data = config.data
        state.currentTriggerId = config.id
        state.config = config

        // 返回位置计算函数，在 DOM 更新后执行
        return () => {
          calculatePosition(config.triggerEl, config.placement, config.offset)
        }
      },
      {
        duration: 300,
        easing: 'ease',
        overflow: 'hidden'
      }
    )
  } catch (err) {
    // 动画被中断（如元素被移除），静默处理
  } finally {
    isSwitching = false

    if (state.status === 'switching') {
      state.status = 'open'
    }

    // 处理挂起的切换
    if (pendingSwitchConfig) {
      const next = pendingSwitchConfig
      pendingSwitchConfig = null
      performSwitch(next)
      return
    }

    // 处理挂起的位置更新
    if (pendingUpdatePosition) {
      pendingUpdatePosition = false
      updatePosition()
    }
  }
}

function close() {
  if (!state.visible || state.status === 'closing') return

  // 取消挂起的切换
  pendingSwitchConfig = null

  // 如果正在切换，取消 FLIP 动画并清理样式
  if (isSwitching && popoverEl) {
    cancelFlip(popoverEl)
    isSwitching = false
  }

  state.status = 'closing'
  unbindEvents()

  // 立即触发 leave 动画（Vue Transition 接管）
  state.visible = false
}

/**
 * Vue Transition leave 动画完成后调用
 */
function onAfterLeave() {
  if (state.status === 'closing') {
    state.status = 'closed'
  }
}

// ==================== 位置更新 ====================

function updatePosition() {
  if (!state.visible || !state.config) return

  // 切换动画中：延迟到动画结束后执行
  if (isSwitching) {
    pendingUpdatePosition = true
    return
  }

  nextTick(() => {
    requestAnimationFrame(() => {
      calculatePosition(state.config.triggerEl, state.config.placement, state.config.offset)
    })
  })
}

// ==================== 定位计算（保持原有逻辑）====================

function calculatePosition(triggerEl, preferredPlacement = 'auto', offset = 16) {
  if (!triggerEl || !popoverEl) return

  // 处理 display: contents 的 trigger
  let actualTrigger = triggerEl
  const style = window.getComputedStyle(triggerEl)
  if (style.display === 'contents' && triggerEl.firstElementChild) {
    actualTrigger = triggerEl.firstElementChild
  }

  const triggerRect = actualTrigger.getBoundingClientRect()

  // 防御：trigger 已不在视口/DOM 中
  if (triggerRect.width === 0 && triggerRect.height === 0) return

  const popoverWidth = popoverEl.offsetWidth
  const popoverHeight = popoverEl.offsetHeight

  const placements = preferredPlacement === 'auto'
    ? ['bottom', 'top', 'right', 'left']
    : [preferredPlacement]

  // 遍历候选方向，找到不超出视口的
  for (const placement of placements) {
    const { top, left } = computePosition(placement, triggerRect, popoverWidth, popoverHeight, offset)
    if (isInViewport(top, left, popoverWidth, popoverHeight, viewportPadding)) {
      state.position = { top, left }
      state.actualPlacement = placement
      return
    }
  }

  // 回退：bottom 并限制在视口内
  fallbackToBottom(triggerRect, popoverWidth, popoverHeight, offset, viewportPadding)
}

function computePosition(placement, triggerRect, popoverWidth, popoverHeight, offset) {
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

  return { top, left }
}

function isInViewport(top, left, width, height, padding) {
  const viewportWidth = window.innerWidth
  const viewportHeight = window.innerHeight

  const fitsHorizontally = left >= padding && left + width <= viewportWidth - padding
  const fitsVertically = top >= padding && top + height <= viewportHeight - padding

  return fitsHorizontally && fitsVertically
}

function fallbackToBottom(triggerRect, popoverWidth, popoverHeight, offset, padding) {
  let top = triggerRect.bottom + offset
  let left = triggerRect.left + (triggerRect.width - popoverWidth) / 2

  const viewportWidth = window.innerWidth
  const viewportHeight = window.innerHeight

  top = Math.max(padding, Math.min(top, viewportHeight - popoverHeight - padding))
  left = Math.max(padding, Math.min(left, viewportWidth - popoverWidth - padding))

  state.position = { top, left }
  state.actualPlacement = 'bottom'
}

// ==================== 事件绑定 ====================

function bindEvents(config) {
  unbindEvents()

  const clickOutsideExclude = config?.clickOutsideExclude

  scrollHandler = (event) => {
    // 忽略来自 popover 内部的滚动事件
    if (event.target && popoverEl && popoverEl.contains(event.target)) {
      return
    }
    updatePosition()
  }

  resizeHandler = () => {
    updatePosition()
  }

  keydownHandler = (event) => {
    if (event.key === 'Escape') {
      close()
    }
  }

  clickOutsideHandler = (event) => {
    // 检查是否被排除
    if (clickOutsideExclude) {
      if (typeof clickOutsideExclude === 'string') {
        if (event.target.matches?.(clickOutsideExclude)) return
        if (event.target.closest?.(clickOutsideExclude)) return
      } else if (typeof clickOutsideExclude === 'function') {
        if (clickOutsideExclude(event.target)) return
      }
    }

    if (popoverEl && !popoverEl.contains(event.target) &&
        config?.triggerEl && !config.triggerEl.contains(event.target)) {
      close()
    }
  }

  document.addEventListener('click', clickOutsideHandler, false)
  window.addEventListener('scroll', scrollHandler, true)
  window.addEventListener('resize', resizeHandler)
  document.addEventListener('keydown', keydownHandler)
}

function unbindEvents() {
  if (clickOutsideHandler) {
    document.removeEventListener('click', clickOutsideHandler, false)
    clickOutsideHandler = null
  }

  if (scrollHandler) {
    window.removeEventListener('scroll', scrollHandler, true)
    scrollHandler = null
  }

  if (resizeHandler) {
    window.removeEventListener('resize', resizeHandler)
    resizeHandler = null
  }

  if (keydownHandler) {
    document.removeEventListener('keydown', keydownHandler)
    keydownHandler = null
  }
}
