<template>
  <div ref="triggerRef" class="popover-trigger" @click="handleTriggerClick">
    <slot />
  </div>
  
  <Teleport to="body">
    <Transition name="popover">
      <div
        v-if="visible"
        ref="popoverRef"
        class="popover"
        :class="`popover-placement-${actualPlacement}`"
        :style="popoverStyle"
        @click.stop
      >
        <div class="popover-content">
          <slot name="content" />
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, watch, nextTick, onUnmounted, computed } from 'vue'
import { usePopoverPosition } from '../composables/usePopoverPosition.js'

const props = defineProps({
  placement: {
    type: String,
    default: 'auto',
    validator: (value) => ['auto', 'top', 'bottom', 'left', 'right'].includes(value)
  },
  offset: {
    type: Number,
    default: 16
  },
  width: {
    type: [String, Number],
    default: 'auto'
  },
  clickOutsideExclude: {
    type: [String, Function],
    default: ''
  }

})

const emit = defineEmits(['show', 'hide'])

const visible = ref(false)
const triggerRef = ref(null)
const popoverRef = ref(null)

const { position, actualPlacement, calculatePosition } = usePopoverPosition()

const popoverStyle = computed(() => {
  const style = {
    position: 'fixed',
    top: `${position.value.top}px`,
    left: `${position.value.left}px`,
    zIndex: 1000
  }
  
  if (props.width !== 'auto') {
    style.width = typeof props.width === 'number' ? `${props.width}px` : props.width
  }
  
  return style
})

function handleTriggerClick(event) {
  event.stopPropagation()
  
  if (visible.value) {
    hide()
  } else {
    document.dispatchEvent(new CustomEvent('popover:close-all'))
    show()
  }
}

function show() {
  visible.value = true
  emit('show')
  
  nextTick(() => {
    // 使用 requestAnimationFrame 确保浏览器完成布局计算（包括图片、flex 布局等）
    // 此时 Vue Transition 的 enter-from（opacity: 0）仍在生效，用户不会看到定位过程
    requestAnimationFrame(() => {
      const el = popoverRef.value
      // show() 期间临时禁用位置transition，避免从上一次关闭位置"飞"到新位置
      el?.classList.remove('has-position-transition')
      
      calculatePosition(triggerRef.value, popoverRef.value, props.placement, props.offset)
      
      // 强制浏览器同步重排，确保新位置已应用且不触发过渡
      el?.offsetHeight
      
      requestAnimationFrame(() => {
        // 进入动画开始后，恢复位置transition（供 updatePosition() 平滑位移使用）
        el?.classList.add('has-position-transition')
      })
    })
  })
}

function hide() {
  // 关闭时移除位置transition，下次show时重新添加
  popoverRef.value?.classList.remove('has-position-transition')
  visible.value = false
  emit('hide')
}

function updatePosition() {
  if (!visible.value) return
  nextTick(() => {
    requestAnimationFrame(() => {
      calculatePosition(triggerRef.value, popoverRef.value, props.placement, props.offset)
    })
  })
}

function handleClickOutside(event) {
  // 新增：检查是否被排除（用于地块弹窗排除 SVG overlay 点击）
  if (props.clickOutsideExclude) {
    if (typeof props.clickOutsideExclude === 'string') {
      if (event.target.matches?.(props.clickOutsideExclude)) return
      if (event.target.closest?.(props.clickOutsideExclude)) return
    } else if (typeof props.clickOutsideExclude === 'function') {
      if (props.clickOutsideExclude(event.target)) return
    }
  }
  
  if (visible.value && popoverRef.value && !popoverRef.value.contains(event.target) && 
      triggerRef.value && !triggerRef.value.contains(event.target)) {
    hide()
  }
}

function handleCloseAll() {
  if (visible.value) {
    hide()
  }
}

defineExpose({
  show,
  hide,
  updatePosition
})

let scrollHandler = null
let resizeHandler = null

watch(visible, (isVisible) => {
  if (isVisible) {
    document.addEventListener('click', handleClickOutside, true)
    document.addEventListener('popover:close-all', handleCloseAll)
    
    scrollHandler = (event) => {
      // 忽略来自 popover 内部的滚动事件，避免内部滚动触发位置重计算
      if (event.target && popoverRef.value && popoverRef.value.contains(event.target)) {
        return
      }
      // 滚动时临时禁用位置transition，避免不跟手的"飘"动画
      const el = popoverRef.value
      el?.classList.remove('has-position-transition')
      calculatePosition(triggerRef.value, popoverRef.value, props.placement, props.offset)
      // 关键：等 Vue 把新位置写到 DOM 后再恢复 transition
      nextTick(() => {
        el?.offsetHeight // 强制重排，锁定新位置
        el?.classList.add('has-position-transition')
      })
    }
    resizeHandler = () => {
      // resize时临时禁用位置transition，避免不跟手的"飘"动画
      const el = popoverRef.value
      el?.classList.remove('has-position-transition')
      calculatePosition(triggerRef.value, popoverRef.value, props.placement, props.offset)
      // 关键：等 Vue 把新位置写到 DOM 后再恢复 transition
      nextTick(() => {
        el?.offsetHeight // 强制重排，锁定新位置
        el?.classList.add('has-position-transition')
      })
    }
    
    window.addEventListener('scroll', scrollHandler, true)
    window.addEventListener('resize', resizeHandler)
  } else {
    document.removeEventListener('click', handleClickOutside, true)
    document.removeEventListener('popover:close-all', handleCloseAll)
    
    if (scrollHandler) {
      window.removeEventListener('scroll', scrollHandler, true)
      scrollHandler = null
    }
    if (resizeHandler) {
      window.removeEventListener('resize', resizeHandler)
      resizeHandler = null
    }
  }
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside, true)
  document.removeEventListener('popover:close-all', handleCloseAll)
  if (scrollHandler) {
    window.removeEventListener('scroll', scrollHandler, true)
  }
  if (resizeHandler) {
    window.removeEventListener('resize', resizeHandler)
  }
})
</script>

<style scoped>
.popover {
  background: #2a2a2a;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
  padding: 16px;
  pointer-events: auto;
}

.popover-content {
  color: var(--text-primary, #fff);
}

/* 过渡动画 */
.popover-enter-active,
.popover-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.popover-enter-from,
.popover-leave-to {
  opacity: 0;
  transform: scale(0.95);
}

.popover-trigger {
  display: contents;
}

/* 位置平滑过渡：仅在updatePosition切换时启用，首次show时不应有 */
.popover.has-position-transition {
  transition: opacity 0.2s ease, transform 0.2s ease, top 0.3s ease, left 0.3s ease;
}
</style>