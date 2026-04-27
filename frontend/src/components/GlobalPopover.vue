<template>
  <Teleport to="body">
    <Transition
      name="global-popover"
      @after-leave="handleAfterLeave"
    >
      <div
        v-if="visible"
        ref="popoverRef"
        class="global-popover"
        :class="`global-popover-placement-${actualPlacement}`"
        :style="popoverStyle"
        @click.stop
      >
        <div class="global-popover-content">
          <GlobalPopoverContent
            v-if="data"
            :image-container-style="data.imageContainerStyle"
            :image-layer-style="data.imageLayerStyle"
            :overlay-layer-style="data.overlayLayerStyle"
            :name="data.name"
            :inactive="data.inactive"
            :detail-title="data.detailTitle || '变更明细'"
            :aspect-ratio="data.aspectRatio"
            :placeholder-count="data.placeholderCount || 20"
            :is-switching="isSwitching"
          />
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useGlobalPopover, setPopoverElement, cleanup } from '../composables/useGlobalPopover.js'
import GlobalPopoverContent from './GlobalPopoverContent.vue'

const { visible, position, actualPlacement, data, onAfterLeave, isSwitching } = useGlobalPopover()

const popoverRef = ref(null)

const popoverStyle = computed(() => ({
  position: 'fixed',
  top: `${position.value.top}px`,
  left: `${position.value.left}px`,
  zIndex: 1000
}))

onMounted(() => {
  watch(popoverRef, (el) => {
    if (el) {
      setPopoverElement(el)
    }
  }, { immediate: true })
})

onUnmounted(() => {
  cleanup()
  setPopoverElement(null)
})

function handleAfterLeave() {
  onAfterLeave()
}
</script>

<style>
.global-popover {
  background: #2a2a2a;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
  padding: 16px;
  pointer-events: auto;
  /* GPU 加速提示 */
  will-change: transform, opacity;
  /* 确保 FLIP 动画中 width/height 计算包含 padding 和 border */
  box-sizing: border-box;
}

.global-popover-content {
  color: var(--text-primary, #fff);
}

/* 首次打开 / 关闭：淡入淡出 + 缩放 */
.global-popover-enter-active,
.global-popover-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.global-popover-enter-from,
.global-popover-leave-to {
  opacity: 0;
  transform: scale(0.95);
}
</style>
