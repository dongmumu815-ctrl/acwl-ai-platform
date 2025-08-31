<template>
  <div class="mindmap-container">
    <!-- 工具栏 -->
    <div class="mindmap-toolbar">
      <div class="toolbar-left">
        <h3 class="mindmap-title">
          <el-icon><Share /></el-icon>
          指令思维导图
        </h3>
        <el-tag v-if="nodeCount > 0" size="small" type="info">
          {{ nodeCount }} 个节点
        </el-tag>
      </div>
      <div class="toolbar-actions">
        <el-button size="small" @click="handleAddRootNode">
          <el-icon><Plus /></el-icon>
          添加根节点
        </el-button>
        <el-button size="small" @click="handleZoomIn">
          <el-icon><ZoomIn /></el-icon>
          放大
        </el-button>
        <el-button size="small" @click="handleZoomOut">
          <el-icon><ZoomOut /></el-icon>
          缩小
        </el-button>
        <el-button size="small" @click="handleFitContent">
          <el-icon><FullScreen /></el-icon>
          适应画布
        </el-button>
        <el-button size="small" @click="handleToggleFullscreen">
          <el-icon><Expand /></el-icon>
          {{ isFullscreen ? '退出全屏' : '全屏' }}
        </el-button>
        <el-dropdown @command="handleFormatLayout">
          <el-button size="small"  @click="() => handleFormatLayout('tree')">
            <el-icon><MagicStick /></el-icon>
            格式化布局
            <el-icon class="el-icon--right"><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item @click="() => handleFormatLayout('compact')">
                <el-icon><Grid /></el-icon>
                紧凑布局
              </el-dropdown-item>
              <el-dropdown-item @click="() => handleFormatLayout('tree')">
                 <el-icon><MagicStick /></el-icon>
                 经典树形
               </el-dropdown-item>
              <el-dropdown-item @click="() => handleFormatLayout('radial')">
                 <el-icon><Compass /></el-icon>
                 垂直树形布局
               </el-dropdown-item>
              <el-dropdown-item @click="() => handleFormatLayout('mindmap')">
                <el-icon><Connection /></el-icon>
                思维导图式
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <!-- 思维导图画布 -->
    <div ref="containerRef" class="mindmap-canvas" />

    <!-- 右键菜单 -->
    <el-dropdown
      ref="contextMenuRef"
      trigger="contextmenu"
      :teleported="false"
      @command="handleContextMenuCommand"
    >
      <span></span>
      <template #dropdown>
        <el-dropdown-menu>
          <el-dropdown-item command="add-child">
            <el-icon><Plus /></el-icon>
            添加子节点
          </el-dropdown-item>
          <el-dropdown-item command="edit">
            <el-icon><Edit /></el-icon>
            编辑节点
          </el-dropdown-item>
          <el-dropdown-item command="copy">
            <el-icon><CopyDocument /></el-icon>
            复制节点
          </el-dropdown-item>
          <el-dropdown-item command="delete" divided>
            <el-icon><Delete /></el-icon>
            删除节点
          </el-dropdown-item>
        </el-dropdown-menu>
      </template>
    </el-dropdown>

    <!-- 节点配置对话框 -->
    <NodeConfigModal
      v-model="configModalVisible"
      :node="currentNode"
      :parent-node="parentNode"
      :instruction-set-id="instructionSetId"
      @submit="handleNodeConfigSubmit"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, nextTick, watch, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Share,
  Plus,
  ZoomIn,
  ZoomOut,
  FullScreen,
  Expand,
  Edit,
  CopyDocument,
  Delete,
  QuestionFilled,
  VideoPlay,
  Connection,
  MagicStick,
  ArrowDown,
  Grid,
  Compass
} from '@element-plus/icons-vue'
import { Graph, Cell, Node, Path } from '@antv/x6'
import { Selection } from '@antv/x6-plugin-selection'
import { Keyboard } from '@antv/x6-plugin-keyboard'
import Hierarchy from '@antv/hierarchy'
import { instructionNodeApi } from '@/api/instruction-set'
import NodeConfigModal from './InstructionTree/NodeConfigModal.vue'
import type {
  InstructionTreeNode,
  InstructionNode,
  InstructionNodeCreate,
  InstructionNodeUpdate,
  NodeType
} from '@/types/instruction-set'

// Props
interface Props {
  instructionSetId: number
  treeData: InstructionTreeNode[]
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  loading: false
})

// Emits
const emit = defineEmits<{
  nodeClick: [node: InstructionTreeNode]
  nodeAdd: [parentNode: InstructionTreeNode | null]
  nodeEdit: [node: InstructionTreeNode]
  nodeDelete: [node: InstructionTreeNode]
  nodeMove: [node: InstructionTreeNode, newParent: InstructionTreeNode | null, newIndex: number]
  treeChange: []
}>()

// 响应式数据
const containerRef = ref<HTMLElement>()
const contextMenuRef = ref()
const configModalVisible = ref(false)
const currentNode = ref<InstructionTreeNode | null>(null)
const parentNode = ref<InstructionTreeNode | null>(null)
const contextMenuNode = ref<InstructionTreeNode | null>(null)
const graph = ref<Graph>()
const isFullscreen = ref(false)

// 计算属性
const nodeCount = computed(() => {
  const countNodes = (nodes: InstructionTreeNode[]): number => {
    return nodes.reduce((count, node) => {
      return count + 1 + (node.children ? countNodes(node.children) : 0)
    }, 0)
  }
  return countNodes(props.treeData)
})

/**
 * 检查是否已存在根节点
 */
const hasRootNode = computed(() => {
  return props.treeData && props.treeData.length > 0
})

/**
 * 注册自定义节点类型
 */
const registerCustomNodes = () => {
  // 注册指令节点
  Graph.registerNode(
    'instruction-node',
    {
      inherit: 'rect',
      markup: [
        {
          tagName: 'rect',
          selector: 'body',
        },
        {
          tagName: 'text',
          selector: 'label',
        },
        {
          tagName: 'text',
          selector: 'description',
        },
      ],
      attrs: {
        body: {
          rx: 12,
          ry: 12,
          stroke: '#5F95FF',
          fill: '#EFF4FF',
          strokeWidth: 2,
          filter: {
            name: 'dropShadow',
            args: {
              dx: 2,
              dy: 2,
              blur: 4,
              color: 'rgba(0,0,0,0.1)',
            },
          },
        },
        label: {
          fontSize: 16,
          fill: '#262626',
          fontWeight: 'bold',
          textAnchor: 'middle',
          textVerticalAnchor: 'middle',
          refX: '50%',
          refY: '40%',
          textWrap: {
            width: -20,
            height: -10,
            ellipsis: true,
          },
        },

        description: {
          fontSize: 11,
          fill: '#666',
          textAnchor: 'middle',
          textVerticalAnchor: 'middle',
          refX: '50%',
          refY: '70%',
          textWrap: {
            width: -20,
            height: -10,
            ellipsis: true,
          },
        },
      },
    },
    true,
  )

  // 注册连接器
  Graph.registerConnector(
    'mindmap',
    (sourcePoint, targetPoint, routerPoints, options) => {
      const midX = sourcePoint.x + 20
      const midY = sourcePoint.y
      const ctrX = (targetPoint.x - midX) / 5 + midX
      const ctrY = targetPoint.y
      const pathData = `
        M ${sourcePoint.x} ${sourcePoint.y}
        L ${midX} ${midY}
        Q ${ctrX} ${ctrY} ${targetPoint.x} ${targetPoint.y}
      `
      return options.raw ? Path.parse(pathData) : pathData
    },
    true,
  )

  // 注册边
  Graph.registerEdge(
    'mindmap-edge',
    {
      inherit: 'edge',
      connector: {
        name: 'mindmap',
      },
      attrs: {
        line: {
          targetMarker: '',
          stroke: '#A2B1C3',
          strokeWidth: 2,
        },
      },
      zIndex: 0,
    },
    true,
  )
}

/**
 * 初始化图形
 */
const initGraph = () => {
  if (!containerRef.value) return

  registerCustomNodes()

  graph.value = new Graph({
    container: containerRef.value,
    background: {
      color: '#f8f9fa',
    },
    grid: {
      visible: true,
      type: 'doubleMesh',
      args: [
        {
          color: '#eee',
          thickness: 1,
        },
        {
          color: '#ddd',
          thickness: 1,
          factor: 4,
        },
      ],
    },
    connecting: {
      connectionPoint: 'anchor',
    },
    selecting: {
      enabled: true,
      multiple: true,
      rubberband: true,
      movable: true,
      showNodeSelectionBox: true,
    },
    keyboard: {
      enabled: true,
    },
  })

  // 添加插件
  graph.value.use(new Selection())
  graph.value.use(new Keyboard())

  // 绑定事件
  bindEvents()
}

// 画布拖拽相关状态
const isDragging = ref(false)
const dragStart = ref({ x: 0, y: 0 })

/**
 * 绑定事件
 */
const bindEvents = () => {
  if (!graph.value) return

  // 节点点击事件
  graph.value.on('node:click', ({ node }) => {
    const nodeData = node.getData() as InstructionTreeNode
    emit('nodeClick', nodeData)
  })

  // 节点双击事件
  graph.value.on('node:dblclick', ({ node }) => {
    const nodeData = node.getData() as InstructionTreeNode
    handleEditNode(nodeData)
  })

  // 节点右键事件
  graph.value.on('node:contextmenu', ({ node, e }) => {
    const nodeData = node.getData() as InstructionTreeNode
    contextMenuNode.value = nodeData
    // 显示右键菜单
    nextTick(() => {
      if (contextMenuRef.value) {
        contextMenuRef.value.handleOpen()
      }
    })
  })

  // 画布拖拽事件
  // 鼠标按下事件（在空白区域）
  graph.value.on('blank:mousedown', ({ e }) => {
    isDragging.value = true
    dragStart.value = { x: e.clientX, y: e.clientY }
    // 改变鼠标样式
    if (containerRef.value) {
      containerRef.value.style.cursor = 'grabbing'
    }
  })

  // 鼠标移动事件
  graph.value.on('blank:mousemove', ({ e }) => {
    if (!isDragging.value) return
    
    const deltaX = e.clientX - dragStart.value.x
    const deltaY = e.clientY - dragStart.value.y
    
    // 使用相对偏移而不是绝对位置
    graph.value?.translateBy(deltaX, deltaY)
    
    // 更新起始位置为当前位置，避免累积偏移
    dragStart.value = { x: e.clientX, y: e.clientY }
  })

  // 鼠标释放事件
  graph.value.on('blank:mouseup', () => {
    isDragging.value = false
    // 恢复鼠标样式
    if (containerRef.value) {
      containerRef.value.style.cursor = 'default'
    }
  })

  // 鼠标离开画布事件
  graph.value.on('blank:mouseleave', () => {
    isDragging.value = false
    // 恢复鼠标样式
    if (containerRef.value) {
      containerRef.value.style.cursor = 'default'
    }
  })

  // 键盘事件
  graph.value.bindKey('delete', () => {
    const selectedCells = graph.value?.getSelectedCells()
    if (selectedCells && selectedCells.length > 0) {
      selectedCells.forEach(cell => {
        if (cell.isNode()) {
          const nodeData = cell.getData() as InstructionTreeNode
          handleDeleteNode(nodeData)
        }
      })
    }
  })
}

/**
 * 渲染思维导图
 */
const renderMindMap = () => {
  if (!graph.value) return
  if (!props.treeData || props.treeData.length === 0) {
    // 清空画布
    graph.value.resetCells([])
    return
  }

  // 转换数据格式
  const mindMapData = convertToMindMapData(props.treeData[0])
  
  // 使用层次布局
  const result = Hierarchy.mindmap(mindMapData, {
    direction: 'H',
    getHeight: () => 100,
    getWidth: () => 180,
    getHGap: () => 120,
    getVGap: () => 60,
    getSide: () => 'right',
  })

  const cells: Cell[] = []
  
  // 遍历生成节点和边
  const traverse = (hierarchyItem: any) => {
    if (hierarchyItem) {
      const { data, children } = hierarchyItem
      
      // 创建节点
      cells.push(
        graph.value!.createNode({
          id: data.id.toString(),
          shape: 'instruction-node',
          x: hierarchyItem.x,
          y: hierarchyItem.y,
          width: 180,
          height: 100,
          label: data.title,
          data: data,
          attrs: {
            body: {
              fill: getNodeColor(data.node_type),
              stroke: getNodeBorderColor(data.node_type),
            },

            description: {
              text: data.description || '暂无描述',
            },
          },
        }),
      )

      // 创建边
      if (children) {
        children.forEach((item: any) => {
          cells.push(
            graph.value!.createEdge({
              shape: 'mindmap-edge',
              source: {
                cell: hierarchyItem.id.toString(),
                anchor: {
                  name: 'right',
                },
              },
              target: {
                cell: item.id.toString(),
                anchor: {
                  name: 'left',
                },
              },
            }),
          )
          traverse(item)
        })
      }
    }
  }

  traverse(result)
  graph.value.resetCells(cells)
  graph.value.centerContent()
}

/**
 * 转换数据格式
 */
const convertToMindMapData = (node: InstructionTreeNode): any => {
  return {
    id: node.id,
    title: node.title,
    node_type: node.node_type,
    description: node.description,
    width: 180,
    height: 100,
    children: node.children ? node.children.map(convertToMindMapData) : undefined,
  }
}

/**
 * 获取节点颜色
 */
const getNodeColor = (nodeType: NodeType): string => {
  const colorMap = {
    CONDITION: '#EFF4FF',
    ACTION: '#F0F9FF',
    BRANCH: '#FFF7ED',
  }
  return colorMap[nodeType] || '#F5F5F5'
}

/**
 * 获取节点边框颜色
 */
const getNodeBorderColor = (nodeType: NodeType): string => {
  const colorMap = {
    CONDITION: '#5F95FF',
    ACTION: '#67C23A',
    BRANCH: '#E6A23C',
  }
  return colorMap[nodeType] || '#DCDFE6'
}

/**
 * 获取节点类型文本
 */
const getNodeTypeText = (nodeType: NodeType): string => {
  const textMap = {
    CONDITION: '条件',
    ACTION: '动作',
    BRANCH: '分支',
  }
  return textMap[nodeType] || '未知'
}

/**
 * 处理工具栏操作
 */
const handleAddRootNode = () => {
  // 检查是否已存在根节点
  if (hasRootNode.value) {
    ElMessage.warning('已存在根节点，不能重复添加')
    return
  }
  
  // 添加根节点：currentNode和parentNode都为null
  currentNode.value = null
  parentNode.value = null
  configModalVisible.value = true
}

const handleZoomIn = () => {
  graph.value?.zoom(0.1)
}

const handleZoomOut = () => {
  graph.value?.zoom(-0.1)
}

const handleFitContent = () => {
  graph.value?.centerContent()
  graph.value?.zoomToFit({ padding: 20 })
}

/**
 * 格式化布局 - 根据选择的风格自动重新排列节点位置
 * @param layoutType 布局类型：compact(紧凑), tree(经典树形), radial(放射状), mindmap(思维导图式)
 */
const handleFormatLayout = (layoutType: string) => {
  if (!graph.value || !props.treeData.length) {
    ElMessage.warning('暂无节点数据，无法格式化布局')
    return
  }

  try {
    // 获取所有节点
    const nodes = graph.value.getNodes()
    if (nodes.length === 0) {
      ElMessage.warning('画布中没有节点')
      return
    }

    let hierarchyData: any
    let layoutName = ''

    // 根据布局类型选择不同的算法和配置
    switch (layoutType) {
      case 'compact':
        // 紧凑布局 - 节点间距较小
        hierarchyData = Hierarchy.compactBox(convertToMindMapData(props.treeData[0]), {
          direction: 'LR',
          getId: (d: any) => d.id,
          getHeight: () => 100,
          getWidth: () => 180,
          getVGap: () => 20,
          getHGap: () => 100,
        })
        layoutName = '紧凑布局'
        break

      case 'tree':
        // 经典树形布局 - 标准间距
        hierarchyData = Hierarchy.compactBox(convertToMindMapData(props.treeData[0]), {
          direction: 'LR',
          getId: (d: any) => d.id,
          getHeight: () => 100,
          getWidth: () => 180,
          getVGap: () => 30,
          getHGap: () => 140,
        })
        layoutName = '经典树形'
        break

      case 'radial':
        // 放射状布局 - 使用紧凑布局的垂直方向模拟放射效果
        hierarchyData = Hierarchy.compactBox(convertToMindMapData(props.treeData[0]), {
          direction: 'TB', // 从上到下，模拟放射状
          getId: (d: any) => d.id,
          getHeight: () => 100,
          getWidth: () => 180,
          getVGap: () => 50,
          getHGap: () => 120,
        })
        layoutName = '垂直树形布局'
        break

      case 'mindmap':
        // 思维导图式布局 - 宽松间距
        hierarchyData = Hierarchy.compactBox(convertToMindMapData(props.treeData[0]), {
          direction: 'LR',
          getId: (d: any) => d.id,
          getHeight: () => 100,
          getWidth: () => 180,
          getVGap: () => 40,
          getHGap: () => 160,
        })
        layoutName = '思维导图式'
        break

      default:
        hierarchyData = Hierarchy.compactBox(convertToMindMapData(props.treeData[0]), {
          direction: 'LR',
          getId: (d: any) => d.id,
          getHeight: () => 100,
          getWidth: () => 180,
          getVGap: () => 20,
          getHGap: () => 100,
        })
        layoutName = '默认布局'
    }

    // 递归更新节点位置
    const updateNodePosition = (hierarchyNode: any) => {
      const node = graph.value?.getCellById(hierarchyNode.id)
      if (node && node.isNode()) {
        // 计算位置偏移
        const x = hierarchyNode.x - 90
        const y = hierarchyNode.y - 50

        // 平滑移动到新位置
        node.position(x, y, {
          transition: {
            duration: 500,
            timing: 'ease-in-out'
          }
        })
      }

      // 递归处理子节点
      if (hierarchyNode.children) {
        hierarchyNode.children.forEach(updateNodePosition)
      }
    }

    updateNodePosition(hierarchyData)

    // 格式化完成后适应画布
    setTimeout(() => {
      handleFitContent()
    }, 600)

    ElMessage.success(`${layoutName}格式化完成`)
  } catch (error) {
    console.error('格式化布局失败:', error)
    ElMessage.error('格式化布局失败，请重试')
  }
}

/**
 * 切换全屏模式
 */
const handleToggleFullscreen = () => {
  const container = containerRef.value?.closest('.mindmap-container') as HTMLElement
  if (!container) return

  if (!isFullscreen.value) {
    // 进入全屏
    if (container.requestFullscreen) {
      container.requestFullscreen()
    } else if ((container as any).webkitRequestFullscreen) {
      (container as any).webkitRequestFullscreen()
    } else if ((container as any).msRequestFullscreen) {
      (container as any).msRequestFullscreen()
    }
  } else {
    // 退出全屏
    if (document.exitFullscreen) {
      document.exitFullscreen()
    } else if ((document as any).webkitExitFullscreen) {
      (document as any).webkitExitFullscreen()
    } else if ((document as any).msExitFullscreen) {
      (document as any).msExitFullscreen()
    }
  }
}

/**
 * 处理节点操作
 */
const handleEditNode = (node: InstructionTreeNode) => {
  // 编辑节点：currentNode为要编辑的节点，parentNode为null
  currentNode.value = node
  parentNode.value = null
  configModalVisible.value = true
}

const handleDeleteNode = async (node: InstructionTreeNode) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除节点 "${node.title}" 吗？此操作将同时删除其所有子节点。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )

    await instructionNodeApi.deleteInstructionNode(node.id)
    ElMessage.success('节点删除成功')
    emit('treeChange')
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '删除节点失败')
    }
  }
}

/**
 * 处理右键菜单
 */
const handleContextMenuCommand = (command: string) => {
  if (!contextMenuNode.value) return

  switch (command) {
    case 'add-child':
      // 添加子节点：currentNode为null，parentNode为右键点击的节点
      currentNode.value = null
      parentNode.value = contextMenuNode.value
      configModalVisible.value = true
      break
    case 'edit':
      handleEditNode(contextMenuNode.value)
      break
    case 'copy':
      // TODO: 实现复制功能
      ElMessage.info('复制功能开发中')
      break
    case 'delete':
      handleDeleteNode(contextMenuNode.value)
      break
  }
}

/**
 * 处理节点配置提交
 */
const handleNodeConfigSubmit = () => {
  configModalVisible.value = false
  currentNode.value = null
  parentNode.value = null
  emit('treeChange')
}

// 监听数据变化
watch(
  () => props.treeData,
  () => {
    nextTick(() => {
      renderMindMap()
    })
  },
  { deep: true }
)

// 组件挂载
onMounted(() => {
  nextTick(() => {
    initGraph()
    renderMindMap()
  })

  // 监听全屏状态变化
  const handleFullscreenChange = () => {
    isFullscreen.value = !!(document.fullscreenElement || 
                           (document as any).webkitFullscreenElement || 
                           (document as any).msFullscreenElement)
  }

  document.addEventListener('fullscreenchange', handleFullscreenChange)
  document.addEventListener('webkitfullscreenchange', handleFullscreenChange)
  document.addEventListener('msfullscreenchange', handleFullscreenChange)
})

// 组件卸载
onUnmounted(() => {
  if (graph.value) {
    graph.value.dispose()
  }

  // 移除全屏事件监听
  const handleFullscreenChange = () => {
    isFullscreen.value = !!(document.fullscreenElement || 
                           (document as any).webkitFullscreenElement || 
                           (document as any).msFullscreenElement)
  }

  document.removeEventListener('fullscreenchange', handleFullscreenChange)
  document.removeEventListener('webkitfullscreenchange', handleFullscreenChange)
  document.removeEventListener('msfullscreenchange', handleFullscreenChange)
})

// 暴露方法给父组件
defineExpose({
  handleAddRootNode,
  renderMindMap,
})
</script>

<style scoped>
.mindmap-container {
  height: 65vh;
  display: flex;
  flex-direction: column;
  background: #f8f9fa;
  position: relative;
}

.mindmap-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: white;
  border-bottom: 1px solid var(--el-border-color-lighter);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.mindmap-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.toolbar-actions {
  display: flex;
  gap: 8px;
}

.mindmap-canvas {
  flex: 1;
  width: 100%;
  height: 100%;
  min-height: calc(65vh - 80px);
  position: relative;
  cursor: grab;
}

.mindmap-canvas:active {
  cursor: grabbing;
}

/* 全屏模式样式 */
.mindmap-container:fullscreen {
  height: 100vh;
  width: 100vw;
}

.mindmap-container:fullscreen .mindmap-canvas {
  min-height: calc(100vh - 80px);
}

/* WebKit 全屏样式 */
.mindmap-container:-webkit-full-screen {
  height: 100vh;
  width: 100vw;
}

.mindmap-container:-webkit-full-screen .mindmap-canvas {
  min-height: calc(100vh - 80px);
}

/* MS 全屏样式 */
.mindmap-container:-ms-fullscreen {
  height: 100vh;
  width: 100vw;
}

.mindmap-container:-ms-fullscreen .mindmap-canvas {
  min-height: calc(100vh - 80px);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .mindmap-toolbar {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }
  
  .toolbar-actions {
    justify-content: center;
  }
}
</style>