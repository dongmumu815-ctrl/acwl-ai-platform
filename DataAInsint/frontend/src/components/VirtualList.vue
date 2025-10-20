<template>
  <div class="virtual-list" ref="containerRef" @scroll="handleScroll">
    <!-- 占位元素，用于撑开滚动条 -->
    <div :style="{ height: `${totalHeight}px`, position: 'relative' }">
      <!-- 可视区域的列表项 -->
      <div 
        class="visible-items" 
        :style="{ transform: `translateY(${offsetY}px)` }"
      >
        <div 
          v-for="(item, index) in visibleData" 
          :key="getItemKey(item, startIndex + index)"
          class="list-item"
          :style="{ height: `${itemHeight}px` }"
          @click="handleItemClick(item, startIndex + index)"
        >
          <slot :item="item" :index="startIndex + index">
            <!-- 默认插槽内容 -->
            <div class="default-item">{{ item }}</div>
          </slot>
        </div>
      </div>
    </div>
    
    <!-- 加载状态 -->
    <div v-if="loading" class="loading-indicator">
      <el-icon class="is-loading"><Loading /></el-icon>
      正在加载...
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { Loading } from '@element-plus/icons-vue'

/**
 * 虚拟滚动列表组件
 * 用于优化大量数据的列表渲染性能
 */
const props = defineProps({
  // 列表数据
  data: {
    type: Array,
    default: () => []
  },
  // 每个列表项的高度
  itemHeight: {
    type: Number,
    default: 50
  },
  // 容器高度
  height: {
    type: Number,
    default: 400
  },
  // 缓冲区大小（在可视区域外额外渲染的项目数量）
  buffer: {
    type: Number,
    default: 10
  },
  // 加载状态
  loading: {
    type: Boolean,
    default: false
  },
  // 获取项目唯一键的函数
  itemKey: {
    type: [String, Function],
    default: null
  },
  // 总数据量（用于无限滚动）
  totalCount: {
    type: Number,
    default: 0
  }
})

const emit = defineEmits(['item-click', 'load-more', 'scroll'])

const containerRef = ref(null)
const scrollTop = ref(0)
const containerHeight = ref(props.height)
const isLoadingMore = ref(false)

// 计算可视区域内显示的项目数
const visibleCount = computed(() => {
  return Math.ceil(containerHeight.value / props.itemHeight)
})

// 计算缓冲区大小
const bufferCount = computed(() => {
  return Math.min(props.buffer, Math.floor(visibleCount.value / 2))
})

// 计算开始索引
const startIndex = computed(() => {
  const index = Math.floor(scrollTop.value / props.itemHeight) - bufferCount.value
  return Math.max(0, index)
})

// 计算结束索引
const endIndex = computed(() => {
  const index = startIndex.value + visibleCount.value + bufferCount.value * 2
  return Math.min(props.data.length, index)
})

// 计算可视区域内的数据
const visibleData = computed(() => {
  return props.data.slice(startIndex.value, endIndex.value)
})

// 计算总高度
const totalHeight = computed(() => {
  return Math.max(props.data.length, props.totalCount) * props.itemHeight
})

// 计算偏移量
const offsetY = computed(() => {
  return startIndex.value * props.itemHeight
})

/**
 * 获取项目的唯一键
 * @param {*} item 列表项数据
 * @param {number} index 索引
 * @returns {string|number} 唯一键
 */
const getItemKey = (item, index) => {
  if (typeof props.itemKey === 'function') {
    return props.itemKey(item, index)
  } else if (typeof props.itemKey === 'string') {
    return item[props.itemKey]
  } else {
    return index
  }
}

/**
 * 处理项目点击事件
 * @param {*} item 被点击的项目
 * @param {number} index 项目索引
 */
const handleItemClick = (item, index) => {
  emit('item-click', item, index)
}

/**
 * 处理滚动事件
 * @param {Event} event 滚动事件
 */
const handleScroll = (event) => {
  const target = event.target
  scrollTop.value = target.scrollTop
  
  emit('scroll', {
    scrollTop: scrollTop.value,
    scrollLeft: target.scrollLeft
  })
  
  // 检查是否需要加载更多数据
  const needLoadMore = endIndex.value >= props.data.length - 10 && 
                      props.data.length < props.totalCount && 
                      !isLoadingMore.value && 
                      !props.loading
  
  if (needLoadMore) {
    isLoadingMore.value = true
    const currentDataLength = props.data.length
    emit('load-more', {
      offset: currentDataLength,
      limit: Math.min(100, props.totalCount - currentDataLength)
    })
    // 重置加载状态
    nextTick(() => {
      isLoadingMore.value = false
    })
  }
}

/**
 * 更新容器高度
 */
const updateContainerHeight = () => {
  if (containerRef.value) {
    const rect = containerRef.value.getBoundingClientRect()
    containerHeight.value = rect.height
  }
}

/**
 * 滚动到指定索引
 * @param {number} index 目标索引
 */
const scrollToIndex = (index) => {
  if (containerRef.value) {
    const targetScrollTop = index * props.itemHeight
    containerRef.value.scrollTop = targetScrollTop
  }
}

/**
 * 滚动到顶部
 */
const scrollToTop = () => {
  scrollToIndex(0)
}

/**
 * 滚动到底部
 */
const scrollToBottom = () => {
  if (containerRef.value) {
    containerRef.value.scrollTop = totalHeight.value
  }
}

// 监听数据变化，重置滚动位置
watch(() => props.data.length, (newLength, oldLength) => {
  // 如果是新数据加载（长度从0变为有值），滚动到顶部
  if (oldLength === 0 && newLength > 0) {
    nextTick(() => {
      scrollToTop()
    })
  }
})

// 监听窗口大小变化
const handleResize = () => {
  updateContainerHeight()
}

onMounted(() => {
  updateContainerHeight()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})

// 暴露方法给父组件
defineExpose({
  scrollToIndex,
  scrollToTop,
  scrollToBottom
})
</script>

<style scoped>
.virtual-list {
  height: 100%;
  overflow-y: auto;
  position: relative;
  background-color: #fff;
}

.visible-items {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
}

.list-item {
  display: flex;
  align-items: center;
  width: 100%;
  box-sizing: border-box;
}

.default-item {
  padding: 12px 16px;
  width: 100%;
  border-bottom: 1px solid #ebeef5;
  display: flex;
  align-items: center;
}

.loading-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  color: #909399;
  background-color: #f5f7fa;
  border-top: 1px solid #dcdfe6;
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 5;
}

.loading-indicator .el-icon {
  margin-right: 8px;
}

.is-loading {
  animation: rotating 2s linear infinite;
}

@keyframes rotating {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

/* 滚动条样式 */
.virtual-list::-webkit-scrollbar {
  width: 6px;
}

.virtual-list::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.virtual-list::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.virtual-list::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}
</style>