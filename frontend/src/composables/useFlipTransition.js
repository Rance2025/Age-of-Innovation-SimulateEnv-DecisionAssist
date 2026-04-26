/**
 * 通用 FLIP（First / Last / Invert / Play）动画工具
 * 支持位置 + 尺寸的平滑 GPU 加速过渡
 */

import { nextTick } from 'vue'

/**
 * 执行 FLIP 动画
 * @param {HTMLElement} element - 目标元素
 * @param {Function} prepareCallback - 准备回调：修改数据 / DOM 后返回新位置计算函数
 * @param {Object} options
 * @param {number} options.duration - 动画时长(ms)，默认 300
 * @param {string} options.easing - 缓动函数，默认 'ease'
 * @param {string} options.overflow - 过渡期间 overflow 值，默认 'hidden'
 * @returns {Promise<{cancelled: boolean}>} - 动画完成或取消时 resolve
 */
export async function animateFlip(
  element,
  prepareCallback,
  options = {}
) {
  const {
    duration = 300,
    easing = 'ease',
    overflow = 'hidden'
  } = options

  // 1. First：记录旧状态
  const firstRect = element.getBoundingClientRect()
  const firstWidth = element.offsetWidth
  const firstHeight = element.offsetHeight

  // 2. 执行准备回调（修改数据 / 计算新位置）
  const computeNewPosition = prepareCallback()

  // 3. 等待 Vue DOM 更新完成
  await nextTick()

  // 应用新位置
  if (computeNewPosition) {
    computeNewPosition()
  }

  // 4. 等待 position 等 DOM 更新应用到元素
  await nextTick()

  // 5. 在单个 rAF 中完成 Last + Invert + Play
  // 关键：避免浏览器在两帧之间偷看到中间状态
  return new Promise((resolve) => {
    requestAnimationFrame(() => {
      // Last：记录新状态
      const lastRect = element.getBoundingClientRect()
      const lastWidth = element.offsetWidth
      const lastHeight = element.offsetHeight

      // 计算差值
      const dx = firstRect.left - lastRect.left
      const dy = firstRect.top - lastRect.top

      const hasChange =
        Math.abs(dx) > 0.5 ||
        Math.abs(dy) > 0.5 ||
        Math.abs(firstWidth - lastWidth) > 0.5 ||
        Math.abs(firstHeight - lastHeight) > 0.5

      if (!hasChange) {
        resolve({ cancelled: false })
        return
      }

      // 6. Invert：瞬间拉回到旧位置和旧尺寸
      const originalTransition = element.style.transition
      const originalTransform = element.style.transform
      const originalWidth = element.style.width
      const originalHeight = element.style.height
      const originalOverflow = element.style.overflow

      element.style.transition = 'none'
      element.style.transform = `translate(${dx}px, ${dy}px)`
      element.style.width = `${firstWidth}px`
      element.style.height = `${firstHeight}px`
      element.style.overflow = overflow

      // 强制重排
      void element.offsetHeight

      // 7. Play：触发过渡
      element.style.transition = `transform ${duration}ms ${easing}, width ${duration}ms ${easing}, height ${duration}ms ${easing}`
      element.style.transform = ''
      element.style.width = `${lastWidth}px`
      element.style.height = `${lastHeight}px`

      // 8. 等待 transitionend
      let resolved = false

      const onTransitionEnd = (e) => {
        if (e.target !== element) return
        if (!['transform', 'width', 'height'].includes(e.propertyName)) return

        resolved = true
        cleanup()
        resolve({ cancelled: false })
      }

      const cancel = () => {
        if (resolved) return
        cleanup()
        resolve({ cancelled: true })
      }

      const cleanup = () => {
        element.removeEventListener('transitionend', onTransitionEnd)
        element.style.transition = originalTransition
        element.style.transform = originalTransform
        element.style.width = originalWidth
        element.style.height = originalHeight
        element.style.overflow = originalOverflow
      }

      element.addEventListener('transitionend', onTransitionEnd)

      // 安全超时：若 transitionend 未触发（如元素被移除），自动清理
      const timeoutId = setTimeout(() => {
        if (!resolved) cancel()
      }, duration + 50)

      // 暴露 cancel 函数
      element._flipCancel = () => {
        clearTimeout(timeoutId)
        cancel()
      }
    })
  })
}

/**
 * 取消元素上正在进行的 FLIP 动画
 */
export function cancelFlip(element) {
  if (element && element._flipCancel) {
    element._flipCancel()
    element._flipCancel = null
  }
}
