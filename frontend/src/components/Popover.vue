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
      calculatePosition(triggerRef.value, popoverRef.value, props.placement, props.offset)
    })
  })
}

function hide() {
  visible.value = false
  emit('hide')
}

function handleClickOutside(event) {
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
  hide
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
      calculatePosition(triggerRef.value, popoverRef.value, props.placement, props.offset)
    }
    resizeHandler = () => {
      calculatePosition(triggerRef.value, popoverRef.value, props.placement, props.offset)
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
</style>