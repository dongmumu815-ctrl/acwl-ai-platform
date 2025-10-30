<template>
  <div 
    class="virtual-table" 
    :class="{ 'fullscreen': isFullscreen }"
    :style="{ height: `${currentHeight}px` }"
  >
    <!-- 工具栏 -->
    <div class="table-toolbar">
      <div class="toolbar-left">
        <span class="data-count">共 {{ totalCount }} 条数据</span>
      </div>
      <div class="toolbar-right">
        <el-button 
          size="small" 
          @click="toggleFullscreen"
          :title="isFullscreen ? '退出全屏' : '全屏显示'"
        >
          <el-icon>
            <FullScreen v-if="!isFullscreen" />
            <Rank v-else />
          </el-icon>
          {{ isFullscreen ? '退出全屏' : '全屏' }}
        </el-button>
      </div>
    </div>
    
    <!-- 表头 -->
    <div class="table-header" ref="headerRef">
      <div class="table-row header-row">
        <div 
            v-for="column in columns" 
            :key="column" 
            class="table-cell header-cell"
            :style="{ width: `${columnWidth}px`, minWidth: '100px', maxWidth: '300px' }"
          >
            {{ column }}
          </div>
      </div>
    </div>
    
    <!-- 虚拟滚动容器 -->
    <div 
      class="table-body" 
      ref="containerRef" 
      @scroll="handleScroll"
      :style="{ height: `${containerHeight}px` }"
    >
      <!-- 占位元素，用于撑开滚动条 -->
      <div :style="{ height: `${totalHeight}px`, position: 'relative' }">
        <!-- 可视区域的数据行 -->
        <div 
          class="visible-rows" 
          :style="{ transform: `translateY(${offsetY}px)` }"
        >
          <div 
            v-for="(item, index) in visibleData" 
            :key="startIndex + index"
            class="table-row data-row"
            :style="{ height: `${itemHeight}px` }"
          >
            <div 
              v-for="column in columns" 
              :key="column" 
              class="table-cell data-cell"
              :style="{ width: `${columnWidth}px`, minWidth: '100px', maxWidth: '300px' }"
              :title="String(item[column] || '')"
            >
              {{ item[column] || '' }}
            </div>
          </div>
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
import { Loading, FullScreen, Rank } from '@element-plus/icons-vue'
import { ElButton, ElIcon } from 'element-plus'

const props = defineProps({
  data: {
    type: Array,
    default: () => []
  },
  columns: {
    type: Array,
    default: () => []
  },
  height: {
    type: Number,
    default: 400
  },
  itemHeight: {
    type: Number,
    default: 40
  },
  columnWidth: {
    type: Number,
    default: 150
  },
  buffer: {
    type: Number,
    default: 100
  },
  loading: {
    type: Boolean,
    default: false
  },
  totalCount: {
    type: Number,
    default: 0
  }
})

const emit = defineEmits(['load-more', 'scroll'])

const containerRef = ref(null)
const headerRef = ref(null)
const scrollTop = ref(0)
const containerHeight = ref(props.height - 80) // 减去表头高度和工具栏高度
const isLoadingMore = ref(false)
const isFullscreen = ref(false)
const originalHeight = ref(props.height)

// 计算当前高度（全屏时使用视窗高度）
const currentHeight = computed(() => {
  if (isFullscreen.value) {
    return window.innerHeight - 20 // 留一些边距
  }
  return props.height
})

/**
 * 切换全屏状态
 */
const toggleFullscreen = () => {
  isFullscreen.value = !isFullscreen.value
  
  nextTick(() => {
    updateContainerHeight()
    // 强制重新计算可视区域
    if (containerRef.value) {
      const event = { target: containerRef.value }
      handleScroll(event)
    }
  })
}

/**
 * 处理键盘事件（ESC退出全屏）
 */
const handleKeydown = (event) => {
  if (event.key === 'Escape' && isFullscreen.value) {
    toggleFullscreen()
  }
}

/**
 * 处理窗口大小变化
 */
const handleResize = () => {
  if (isFullscreen.value) {
    updateContainerHeight()
  }
}

// 计算可视区域内显示的行数
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
  const result = props.data.slice(startIndex.value, endIndex.value)
  return result
})

// 计算总高度
const totalHeight = computed(() => {
  return Math.max(props.data.length, props.totalCount) * props.itemHeight
})

// 计算偏移量
const offsetY = computed(() => {
  return startIndex.value * props.itemHeight
})

// 滚动处理
const handleScroll = (event) => {
  const target = event.target
  scrollTop.value = target.scrollTop
  
  // 同步表头滚动
  if (headerRef.value) {
    headerRef.value.scrollLeft = target.scrollLeft
  }
  
  emit('scroll', {
    scrollTop: scrollTop.value,
    scrollLeft: target.scrollLeft
  })
  
  // 检查是否需要加载更多数据
  // 当滚动到接近已加载数据的底部时，触发加载更多
  const needLoadMore = endIndex.value >= props.data.length - 50 && 
                      props.data.length < props.totalCount && 
                      !isLoadingMore.value && 
                      !props.loading
  
  if (needLoadMore) {
    console.log('VirtualTable: Triggering load-more, current data length:', props.data.length, 'total:', props.totalCount)
    isLoadingMore.value = true
    const currentDataLength = props.data.length
    emit('load-more', {
      offset: currentDataLength,
      limit: Math.min(1000, props.totalCount - currentDataLength)
    })
    // 重置加载状态将由父组件控制
    nextTick(() => {
      isLoadingMore.value = false
    })
  }
}

// 监听容器高度变化
const updateContainerHeight = () => {
  // 计算table-body的可用高度：总高度减去表头高度和工具栏高度
  const headerHeight = headerRef.value ? headerRef.value.offsetHeight : 40
  const toolbarHeight = 40 // 工具栏高度
  const totalUsedHeight = headerHeight + toolbarHeight
  
  if (isFullscreen.value) {
    containerHeight.value = window.innerHeight - totalUsedHeight - 20 // 全屏时减去边距
  } else {
    containerHeight.value = props.height - totalUsedHeight
  }
}

// 滚动到指定位置
const scrollToIndex = (index) => {
  if (containerRef.value) {
    const targetScrollTop = index * props.itemHeight
    containerRef.value.scrollTop = targetScrollTop
  }
}

// 滚动到顶部
const scrollToTop = () => {
  scrollToIndex(0)
}

// 滚动到底部
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
      // 先更新容器高度，再滚动到顶部
      updateContainerHeight()
      scrollToTop()
    })
  }
  // 如果数据长度发生变化，强制更新容器
  if (newLength !== oldLength) {
    nextTick(() => {
      updateContainerHeight()
      // 强制重新计算可视区域
      if (containerRef.value) {
        const event = { target: containerRef.value }
        handleScroll(event)
      }
    })
  }
})

// 监听数据变化，确保容器高度正确更新
watch(() => props.data, (newData, oldData) => {
  nextTick(() => {
    updateContainerHeight()
    // 如果数据完全替换（引用不同），强制重新计算可视区域
    if (newData !== oldData && containerRef.value) {
      const event = { target: containerRef.value }
      handleScroll(event)
    }
  })
}, { deep: true })

// 监听columns变化，重新计算布局
watch(() => props.columns, () => {
  nextTick(() => {
    updateContainerHeight()
  })
})

onMounted(() => {
  updateContainerHeight()
  // 添加键盘和窗口事件监听
  document.addEventListener('keydown', handleKeydown)
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  // 清理事件监听器
  document.removeEventListener('keydown', handleKeydown)
  window.removeEventListener('resize', handleResize)
})

// 强制更新容器高度和重新渲染
const forceUpdate = () => {
  updateContainerHeight()
  // 强制重新计算可视区域
  if (containerRef.value) {
    const event = { target: containerRef.value }
    handleScroll(event)
  }
}

// 暴露方法给父组件
defineExpose({
  scrollToIndex,
  scrollToTop,
  scrollToBottom,
  forceUpdate,
  updateContainerHeight
})
</script>

<style scoped>
.virtual-table {
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  overflow: hidden;
  position: relative;
  background: white;
}

/* 全屏模式样式 */
.virtual-table.fullscreen {
  position: fixed;
  top: 10px;
  left: 10px;
  right: 10px;
  bottom: 10px;
  z-index: 9999;
  border-radius: 8px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
  background: white;
}

/* 工具栏样式 */
.table-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: #f5f7fa;
  border-bottom: 1px solid #dcdfe6;
  height: 40px;
  box-sizing: border-box;
}

.toolbar-left {
  display: flex;
  align-items: center;
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.data-count {
  font-size: 12px;
  color: #606266;
  font-weight: 500;
}

.table-header {
  background-color: #f5f7fa;
  border-bottom: 1px solid #dcdfe6;
  position: sticky;
  top: 0;
  z-index: 10;
}

.table-body {
  overflow-y: auto;
  position: relative;
}

.visible-rows {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
}

.table-row {
  display: flex;
  border-bottom: 1px solid #ebeef5;
  min-height: 40px;
  align-items: center;
}

.table-row.header-row {
  background-color: #f5f7fa;
  font-weight: 600;
  color: #909399;
}

.table-row.data-row:nth-child(even) {
  background-color: #fafafa;
}

.table-row.data-row:hover {
  background-color: #f5f7fa;
}

.table-cell {
  padding: 8px 12px;
  border-right: 1px solid #ebeef5;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
  min-width: 100px;
  display: flex;
  align-items: center;
}

.table-cell:last-child {
  border-right: none;
}

.table-cell.header-cell {
  background-color: #f5f7fa;
  font-weight: 600;
  color: #909399;
}

.table-cell.data-cell {
  color: #606266;
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
.virtual-table::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

.virtual-table::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

.virtual-table::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 4px;
}

.virtual-table::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

.virtual-table::-webkit-scrollbar-corner {
  background: #f1f1f1;
}
</style>