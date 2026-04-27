<template>
  <div class="entity-popover-content" :class="layoutClass">
    <!-- 图片区域 -->
    <div v-if="imageLayerStyle" ref="imageSectionRef" class="popover-image-section">
      <div class="entity-preview-media">
        <div
          class="entity-preview-image"
          :class="{ 'is-inactive': inactive }"
          :style="imageContainerStyle"
        >
          <div class="entity-preview-image-layer" :style="imageLayerStyle"></div>
          <div
            v-if="overlayLayerStyle"
            class="entity-preview-image-layer entity-preview-image-overlay-layer"
            :style="overlayLayerStyle"
          ></div>
          <div v-if="inactive" class="entity-preview-inactive-mark" aria-hidden="true">
            <i class="fas fa-ban"></i>
          </div>
        </div>
      </div>
      <div v-if="name" class="entity-preview-name">{{ name }}</div>
    </div>

    <!-- 明细区域 -->
    <div
      ref="detailSectionRef"
      class="popover-detail-section"
      :class="{ 'full-width': !imageLayerStyle }"
      :style="detailSectionStyle"
    >
      <div class="detail-header">{{ detailTitle }}</div>
      <div class="detail-list">
        <div v-for="i in props.placeholderCount" :key="i" class="detail-item">
          <span class="detail-dot"></span>
          <span class="detail-text">占位明细条目 {{ i }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, onMounted, onUnmounted, nextTick, watch } from 'vue'

const props = defineProps({
  imageContainerStyle: Object,
  imageLayerStyle: Object,
  overlayLayerStyle: Object,
  name: String,
  inactive: Boolean,
  detailTitle: { type: String, default: '变更明细' },
  aspectRatio: String,
  placeholderCount: { type: Number, default: 20 },
  isSwitching: { type: Boolean, default: false }
})

const imageSectionRef = ref(null)
const detailSectionRef = ref(null)
const tallDetailMaxHeight = ref('280px')
let resizeObserver = null

const layoutClass = computed(() => {
  if (!props.imageLayerStyle) return 'layout-detail-only'
  if (!props.aspectRatio) return 'layout-wide'
  const [w, h] = props.aspectRatio.split('/').map(Number)
  return (w / h) < 1.0 ? 'layout-tall' : 'layout-wide'
})

const detailSectionStyle = computed(() => {
  if (layoutClass.value === 'layout-tall') {
    return { maxHeight: tallDetailMaxHeight.value }
  }
  return {}
})

function syncTallDetailHeight() {
  if (layoutClass.value === 'layout-tall' && imageSectionRef.value) {
    const height = imageSectionRef.value.getBoundingClientRect().height
    tallDetailMaxHeight.value = `${height}px`
  }
}

onMounted(() => {
  nextTick(() => {
    syncTallDetailHeight()
    if (imageSectionRef.value && typeof ResizeObserver !== 'undefined') {
      resizeObserver = new ResizeObserver(() => syncTallDetailHeight())
      resizeObserver.observe(imageSectionRef.value)
    }
  })
})

onUnmounted(() => {
  if (resizeObserver) {
    resizeObserver.disconnect()
    resizeObserver = null
  }
})

watch(() => [props.imageLayerStyle, props.name, props.aspectRatio], () => {
  nextTick(() => syncTallDetailHeight())
}, { flush: 'post' })

// FLIP 切换动画期间暂停 ResizeObserver，避免尺寸竞争
watch(() => props.isSwitching, (switching) => {
  if (switching) {
    if (resizeObserver) {
      resizeObserver.disconnect()
    }
  } else {
    nextTick(() => {
      syncTallDetailHeight()
      if (imageSectionRef.value && typeof ResizeObserver !== 'undefined') {
        resizeObserver = new ResizeObserver(() => syncTallDetailHeight())
        resizeObserver.observe(imageSectionRef.value)
      }
    })
  }
})
</script>

<style scoped>
.entity-popover-content {
  display: flex;
  gap: 16px;
}

/* 瘦高：左右布局 */
.entity-popover-content.layout-tall {
  flex-direction: row;
  align-items: flex-start;
  gap: 24px;
}

.layout-tall .popover-image-section {
  flex-shrink: 0;
}

.layout-tall .popover-detail-section {
  min-width: 200px;
}

/* 长宽：上下布局 */
.entity-popover-content.layout-wide {
  flex-direction: column;
}

.layout-wide .popover-image-section {
  align-self: center;
}

.layout-wide .popover-detail-section {
  max-height: 280px;
}

/* 纯明细 */
.entity-popover-content.layout-detail-only {
  flex-direction: column;
}

.layout-detail-only .popover-detail-section {
  min-width: 200px;
  max-height: 280px;
}

/* 图片 */
.entity-preview-media {
  position: relative;
}

.entity-preview-image {
  position: relative;
  width: var(--preview-width, auto);
  max-width: 100%;
  height: auto;
  aspect-ratio: var(--preview-aspect-ratio, auto);
  border-radius: 12px;
  overflow: hidden;
}

.entity-preview-image.is-inactive .entity-preview-image-layer {
  filter: grayscale(1);
}

.entity-preview-image-layer {
  position: absolute;
  inset: 0;
  background-repeat: no-repeat;
  background-position: center;
  background-size: contain;
}

.entity-preview-image-overlay-layer {
  z-index: 2;
}

.entity-preview-inactive-mark {
  position: absolute;
  inset: 0;
  z-index: 3;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #ef4444;
  font-size: 2.6rem;
  line-height: 1;
  text-shadow: 0 2px 8px rgba(0, 0, 0, 0.68);
  pointer-events: none;
}

.entity-preview-name {
  margin-top: 8px;
  text-align: center;
  font-size: 0.875rem;
  color: #fff;
  font-weight: 500;
}

/* 明细区域 */
.popover-detail-section {
  display: flex;
  flex-direction: column;
  min-width: 200px;
}

.detail-header {
  flex-shrink: 0;
  font-size: 0.875rem;
  font-weight: 600;
  color: #fff;
  margin-bottom: 8px;
  padding-bottom: 6px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.detail-list {
  flex: 1;
  overflow-y: auto;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.detail-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 0;
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.7);
}

.detail-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.4);
  flex-shrink: 0;
}

.detail-list::-webkit-scrollbar {
  width: 4px;
}

.detail-list::-webkit-scrollbar-track {
  background: transparent;
}

.detail-list::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 2px;
}
</style>
