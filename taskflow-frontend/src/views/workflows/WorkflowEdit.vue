<template>
  <div class="workflow-editor">
    <!-- 顶部工具栏 -->
    <div class="toolbar">
      <div class="toolbar-left">
        <el-button @click="goBack" size="small">
          <el-icon><ArrowLeft /></el-icon>
          返回
        </el-button>
        <el-divider direction="vertical" />
        <span class="workflow-title">编辑工作流: {{ workflowName }}</span>
      </div>
      <div class="toolbar-right">
        <el-button @click="handleSave" type="primary" size="small" :loading="saveLoading">
          <el-icon><Check /></el-icon>
          {{ saveLoading ? '保存中...' : '保存' }}
        </el-button>
        <el-button @click="handlePreview" size="small">
          <el-icon><View /></el-icon>
          预览
        </el-button>
      </div>
    </div>

    <!-- 主编辑区域 -->
    <div class="editor-main">
      <!-- 左侧节点面板 -->
      <div class="node-panel" :class="{ collapsed: !showNodePanel }">
        <div class="panel-header">
          <h3>节点库</h3>
          <el-button @click="toggleNodePanel" size="small" text>
            <el-icon><ArrowLeft v-if="showNodePanel" /><ArrowRight v-else /></el-icon>
          </el-button>
        </div>
        <div class="panel-content" v-show="showNodePanel">
          <!-- 节点分类 -->
          <div class="node-categories">
            <div 
              v-for="category in nodeCategories" 
              :key="category.key"
              class="category-item"
              :class="{ active: activeCategory === category.key }"
              @click="activeCategory = category.key"
            >
              {{ category.name }}
            </div>
          </div>
          <!-- 节点列表 -->
          <div class="node-list">
            <div 
              v-for="nodeType in filteredNodeTypes" 
              :key="nodeType.type"
              class="node-item"
              :draggable="true"
              @dragstart="handleDragStart($event, nodeType)"
              @dragend="handleDragEnd($event)"
            >
              <div class="node-name">{{ nodeType.name }}</div>
              <div class="node-desc">{{ nodeType.description }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 中间画布区域 -->
      <div class="canvas-area">
        <div class="canvas-toolbar">
          <div class="toolbar-group">
            <el-button
              type="primary"
              :loading="saveLoading"
              @click="handleSave"
              size="small"
            >
              <el-icon><Check /></el-icon>
              保存
            </el-button>
            <el-button @click="importJSON" size="small">
              <el-icon><Upload /></el-icon>
              导入
            </el-button>
            <el-button @click="exportJSON" size="small">
              <el-icon><Download /></el-icon>
              导出JSON
            </el-button>
            <el-button @click="exportImage" size="small">
              <el-icon><Picture /></el-icon>
              导出图片
            </el-button>
          </div>
          
          <el-divider direction="vertical" />
          
          <div class="toolbar-group">
            <el-button @click="handleZoomIn" size="small">
              <el-icon><ZoomIn /></el-icon>
            </el-button>
            <el-button @click="handleZoomOut" size="small">
              <el-icon><ZoomOut /></el-icon>
            </el-button>
            <el-button @click="handleZoomFit" size="small">
              <el-icon><FullScreen /></el-icon>
              适应画布
            </el-button>
            <el-button @click="resetZoom" size="small">
              <el-icon><Refresh /></el-icon>
              重置缩放
            </el-button>
          </div>
          
          <el-divider direction="vertical" />
          
          <div class="toolbar-group">
            <el-button @click="handleUndo" :disabled="!canUndo" size="small">
              <el-icon><RefreshLeft /></el-icon>
              撤销
            </el-button>
            <el-button @click="handleRedo" :disabled="!canRedo" size="small">
              <el-icon><RefreshRight /></el-icon>
              重做
            </el-button>
          </div>
          
          <el-divider direction="vertical" />
          
          <div class="toolbar-group">
            <el-button @click="handleClearAll" size="small" type="danger">
              <el-icon><Delete /></el-icon>
              清空
            </el-button>
          </div>
        </div>
        <div
          id="workflow-canvas"
          class="canvas"
          @drop="handleDrop"
          @dragover="handleDragOver"
        ></div>
      </div>

    </div>

    <!-- 右侧属性面板 - 抽屉式模态窗口 -->
    <el-drawer
      v-model="showPropertyPanel"
      title="节点属性"
      direction="rtl"
      size="400px"
      :before-close="handleClosePropertyPanel"
    >
      <template #header>
        <div class="drawer-header">
          <h3>节点属性</h3>
          <span class="node-type-badge" v-if="selectedNode">
            {{ getNodeTypeName(selectedNode.type) }}
          </span>
        </div>
      </template>
      
      <div class="drawer-content" v-if="selectedNode">
        <el-form :model="selectedNode" label-width="80px" size="small">
          <el-form-item label="节点名称">
            <el-input v-model="selectedNode.name" @change="updateNodeProperty" />
          </el-form-item>
          <el-form-item label="节点描述">
            <el-input 
              v-model="selectedNode.description" 
              type="textarea" 
              :rows="3"
              @change="updateNodeProperty"
            />
          </el-form-item>
          <el-form-item label="节点类型">
            <el-tag>{{ getNodeTypeName(selectedNode.type) }}</el-tag>
          </el-form-item>
          
          <!-- 动态配置项 -->
          <NodeConfig 
            v-model="selectedNode.config"
            :node-type="selectedNode.type"
            @change="updateNodeProperty"
          />
        </el-form>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted, markRaw } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Graph } from '@antv/x6'
import NodeConfig from '../../components/workflow/configs/NodeConfig.vue'
import { workflowApi } from '@/api/workflow'
import {
  ArrowLeft, Check, View, ZoomIn, ZoomOut, FullScreen,
  RefreshLeft, RefreshRight, Delete, ArrowRight, Close,
  DataBoard, Setting, Share, DocumentCopy, Upload,
  Download, Picture, Refresh
} from '@element-plus/icons-vue'

// 路由相关
const router = useRouter()
const route = useRoute()

// 响应式数据
const workflowName = ref('新建工作流')
const saveLoading = ref(false)
const showNodePanel = ref(true)
const showPropertyPanel = ref(false)
const activeCategory = ref('data')
const selectedNode = ref(null)
const canUndo = ref(false)
const canRedo = ref(false)

// X6图实例
let graph = null

/**
 * 节点分类定义
 */
const nodeCategories = ref([
  { key: 'data', name: '数据处理' },
  { key: 'ai', name: 'AI智能' },
  { key: 'control', name: '流程控制' },
  { key: 'tools', name: '工具类' }
])

/**
 * 节点类型定义
 */
const nodeTypes = ref([
  // 流程控制类 - 开始和结束节点（不在节点库中显示）
  {
    type: 'start',
    name: '开始',
    description: '工作流开始节点',
    category: 'control',
    color: '#52c41a',
    hidden: true // 标记为隐藏，不在节点库中显示
  },
  {
    type: 'end',
    name: '结束',
    description: '工作流结束节点',
    category: 'control',
    color: '#f5222d',
    hidden: true // 标记为隐藏，不在节点库中显示
  },
  // 数据处理类
  {
    type: 'sql-execute',
    name: 'SQL执行',
    description: '执行SQL查询和数据操作',
    category: 'data',
    color: '#1890ff'
  },
  // AI智能类
  {
    type: 'llm-chat',
    name: '大语言模型',
    description: '调用大语言模型进行对话和文本生成',
    category: 'ai',
    color: '#722ed1'
  },
  {
    type: 'ai-agent',
    name: 'AI智能体',
    description: '执行复杂的AI任务和决策',
    category: 'ai',
    color: '#eb2f96'
  },
  {
    type: 'text-analysis',
    name: '文本分析',
    description: '文本情感分析、关键词提取等',
    category: 'ai',
    color: '#52c41a'
  },
  {
    type: 'image-recognition',
    name: '图像识别',
    description: '图像分类、物体检测等AI视觉任务',
    category: 'ai',
    color: '#faad14'
  },
  {
    type: 'speech-processing',
    name: '语音处理',
    description: '语音识别、语音合成等处理',
    category: 'ai',
    color: '#13c2c2'
  },
  // 流程控制类
  {
    type: 'condition',
    name: '条件判断',
    description: '根据条件分支执行',
    category: 'control',
    color: '#722ed1'
  },
  {
    type: 'loop',
    name: '循环执行',
    description: '重复执行子流程',
    category: 'control',
    color: '#eb2f96'
  },
  {
    type: 'shell',
    name: 'Shell脚本',
    description: '执行Shell命令或脚本',
    category: 'control',
    color: '#13c2c2'
  },
  {
    type: 'python',
    name: 'Python脚本',
    description: '执行Python代码',
    category: 'control',
    color: '#3776ab'
  },
  {
    type: 'delay',
    name: '延时等待',
    description: '等待指定时间后继续',
    category: 'control',
    color: '#fa8c16'
  },
  // 工具类
  {
    type: 'http-request',
    name: 'HTTP请求',
    description: '发送HTTP/HTTPS请求',
    category: 'tools',
    color: '#52c41a'
  },
  {
    type: 'file-process',
    name: '文件处理',
    description: '文件读写和处理操作',
    category: 'tools',
    color: '#faad14'
  },
  {
    type: 'email-send',
    name: '邮件发送',
    description: '发送电子邮件通知',
    category: 'tools',
    color: '#1890ff'
  },
  {
    type: 'ftp-transfer',
    name: 'FTP传输',
    description: '文件FTP上传下载',
    category: 'tools',
    color: '#722ed1'
  },
  {
    type: 'database-query',
    name: '数据库查询',
    description: '执行SQL查询语句',
    category: 'tools',
    color: '#f5222d'
  }
])

/**
 * 过滤后的节点类型（排除隐藏节点）
 */
const filteredNodeTypes = computed(() => {
  return nodeTypes.value.filter(node => node.category === activeCategory.value && !node.hidden)
})

/**
 * 初始化X6图编辑器
 */
const initGraph = () => {
  const container = document.getElementById('workflow-canvas')
  if (!container) return

  graph = new Graph({
    container: container,
    width: container.clientWidth,
    height: container.clientHeight,
    // 网格配置
    grid: {
      visible: true,
      type: 'doubleMesh',
      args: [
        { color: '#f0f0f0', thickness: 1 },
        { color: '#e0e0e0', thickness: 1, factor: 4 }
      ]
    },
    // 背景配置
    background: { 
      color: '#fafafa' 
    },
    // 平移配置
    panning: { 
      enabled: true,
      eventTypes: ['leftMouseDown', 'mouseWheel']
    },
    // 鼠标滚轮缩放
    mousewheel: {
      enabled: true,
      modifiers: 'ctrl',
      factor: 1.1,
      maxScale: 3,
      minScale: 0.3
    },
    // 连接配置
    connecting: {
      router: {
        name: 'manhattan',
        args: {
          padding: 1
        }
      },
      connector: {
        name: 'rounded',
        args: {
          radius: 8,
          offset: 20
        }
      },
      router: {
        name: 'manhattan',
        args: {
          padding: 20,
          step: 20
        }
      },
      anchor: 'center',
      connectionPoint: 'boundary',
      allowBlank: false,
      allowLoop: false,
      allowNode: false,
      allowEdge: false,
      snap: {
        radius: 20
      },
      createEdge() {
        return graph.createEdge({
          shape: 'edge',
          attrs: {
            line: {
              stroke: '#1890ff',
              strokeWidth: 2,
              targetMarker: {
                name: 'classic',
                size: 10,
                offset: -2
              }
            }
          },
          connector: {
            name: 'rounded',
            args: {
              radius: 8,
              offset: 15
            }
          },
          router: {
            name: 'manhattan',
            args: {
              padding: 25,
              step: 20,
              endDirections: ['top', 'bottom', 'left', 'right'],
              startDirections: ['top', 'bottom', 'left', 'right']
            }
          },
          zIndex: 0
        })
      },
      validateConnection({ targetMagnet }) {
        return !!targetMagnet
      }
    },
    // 选择配置
    selecting: {
      enabled: true,
      rubberband: true,
      movable: true,
      showNodeSelectionBox: true,
      showEdgeSelectionBox: true
    },
    // 对齐线
    snapline: {
      enabled: true,
      sharp: true
    },
    // 键盘快捷键
    keyboard: {
      enabled: true,
      global: true
    },
    // 剪贴板
    clipboard: {
      enabled: true
    },
    // 历史记录
    history: {
      enabled: true,
      beforeAddCommand: (event, args) => {
        if (args.key === 'tools') {
          return false
        }
      }
    },
    // 缩放配置
    scaling: {
      min: 0.3,
      max: 3
    }
  })

  // 注册自定义节点
  registerCustomNodes()
  
  // 绑定事件
  bindGraphEvents()
  
  // 启用键盘快捷键
  bindKeyboardShortcuts()
  
  // 创建默认的开始和结束节点
  createDefaultNodes()
}

/**
 * 注册自定义节点
 */
const registerCustomNodes = () => {
  // 先尝试清理可能存在的旧注册
  try {
    Graph.unregisterNode('workflow-node')
    console.log('Cleaned up existing workflow-node registration')
  } catch (e) {
    // 节点不存在，这是正常的
    console.log('No existing workflow-node to clean up')
  }
  
  // 现在安全地注册新节点
  console.log('Registering workflow-node...')
  
  Graph.registerNode('workflow-node', {
    inherit: 'rect',
    width: 180,
    height: 56,
    attrs: {
      body: {
        strokeWidth: 2,
        stroke: '#d9d9d9',
        fill: '#ffffff',
        rx: 8,
        ry: 8,
        filter: {
          name: 'dropShadow',
          args: {
            dx: 0,
            dy: 2,
            blur: 4,
            color: 'rgba(0,0,0,0.1)'
          }
        }
      },
      text: {
        fontSize: 13,
        fill: '#262626',
        fontWeight: 500,
        textAnchor: 'middle',
        textVerticalAnchor: 'middle',
        textWrap: {
          width: 160,
          height: 40,
          ellipsis: true
        }
      }
    },
    ports: {
      groups: {
        top: {
          position: 'top',
          attrs: {
            circle: {
              r: 5,
              magnet: true,
              stroke: '#1890ff',
              strokeWidth: 2,
              fill: '#ffffff',
              style: {
                visibility: 'hidden'
              }
            }
          }
        },
        bottom: {
          position: 'bottom',
          attrs: {
            circle: {
              r: 5,
              magnet: true,
              stroke: '#1890ff',
              strokeWidth: 2,
              fill: '#ffffff',
              style: {
                visibility: 'hidden'
              }
            }
          }
        }
      },
      items: [
        { group: 'top' },
        { group: 'bottom' }
      ]
    }
  })
}

/**
 * 绑定图事件
 */
const bindGraphEvents = () => {
  // 节点选择事件
  graph.on('node:click', ({ node }) => {
    selectedNode.value = {
      id: node.id,
      name: node.attr('text/text'),
      type: node.getData()?.type || 'unknown',
      description: node.getData()?.description || '',
      config: node.getData()?.config || {}
    }
    showPropertyPanel.value = true
  })

  // 画布点击事件
  graph.on('blank:click', () => {
    selectedNode.value = null
    showPropertyPanel.value = false
  })

  // 历史记录事件
  graph.on('history:change', () => {
    canUndo.value = graph.canUndo()
    canRedo.value = graph.canRedo()
  })

  // 节点悬停事件 - 显示连接点
  graph.on('node:mouseenter', ({ node }) => {
    const ports = node.getPorts()
    ports.forEach(port => {
      node.portProp(port.id, 'attrs/circle/style/visibility', 'visible')
    })
  })

  // 节点离开事件 - 隐藏连接点
  graph.on('node:mouseleave', ({ node }) => {
    const ports = node.getPorts()
    ports.forEach(port => {
      node.portProp(port.id, 'attrs/circle/style/visibility', 'hidden')
    })
  })

  // 边选择事件
  graph.on('edge:click', ({ edge }) => {
    selectedNode.value = null
  })

  // 节点移动事件
  graph.on('node:moved', ({ node }) => {
    // 可以在这里添加节点移动后的处理逻辑
  })

  // 连接创建事件
  graph.on('edge:connected', ({ edge }) => {
    console.log('连接已创建:', edge.id)
  })
}

/**
 * 绑定键盘快捷键
 */
const bindKeyboardShortcuts = () => {
  if (!graph) {
    console.warn('Graph not initialized')
    return
  }
  
  // 检查graph是否有bindKey方法
  if (typeof graph.bindKey !== 'function') {
    console.warn('Graph.bindKey method not available, skipping keyboard shortcuts')
    return
  }
  
  try {
    // 撤销 Ctrl+Z
    graph.bindKey(['ctrl+z', 'cmd+z'], () => {
      if (graph.canUndo()) {
        graph.undo()
      }
      return false
    })

  // 重做 Ctrl+Y
  graph.bindKey(['ctrl+y', 'cmd+y'], () => {
    if (graph.canRedo()) {
      graph.redo()
    }
    return false
  })

  // 删除 Delete/Backspace
  graph.bindKey(['del', 'backspace'], () => {
    const cells = graph.getSelectedCells()
    if (cells.length) {
      graph.removeCells(cells)
    }
    return false
  })

  // 全选 Ctrl+A
  graph.bindKey(['ctrl+a', 'cmd+a'], () => {
    const nodes = graph.getNodes()
    if (nodes.length) {
      graph.select(nodes)
    }
    return false
  })

  // 复制 Ctrl+C
  graph.bindKey(['ctrl+c', 'cmd+c'], () => {
    const cells = graph.getSelectedCells()
    if (cells.length) {
      graph.copy(cells)
    }
    return false
  })

  // 粘贴 Ctrl+V
  graph.bindKey(['ctrl+v', 'cmd+v'], () => {
    if (!graph.isClipboardEmpty()) {
      const cells = graph.paste({ offset: 32 })
      graph.cleanSelection()
      graph.select(cells)
    }
    return false
  })

  // 缩放到适合 Ctrl+0
  graph.bindKey(['ctrl+0', 'cmd+0'], () => {
    graph.zoomToFit({ padding: 20 })
    return false
  })

  // 放大 Ctrl+=
  graph.bindKey(['ctrl+=', 'cmd+='], () => {
    graph.zoom(0.1)
    return false
  })

  // 缩小 Ctrl+-
  graph.bindKey(['ctrl+-', 'cmd+-'], () => {
    graph.zoom(-0.1)
    return false
  })
  
  } catch (error) {
    console.warn('Failed to bind keyboard shortcuts:', error)
  }
}

/**
 * 创建节点
 */
const createNode = (nodeType, x, y) => {
  const nodeConfig = nodeTypes.value.find(type => type.type === nodeType.type)
  if (!nodeConfig) return null

  const node = graph.addNode({
    shape: 'workflow-node',
    x: x - 90, // 居中对齐
    y: y - 28,
    attrs: {
      body: {
        fill: nodeConfig.color + '20',
        stroke: nodeConfig.color
      },
      text: {
        text: nodeConfig.name
      }
    },
    data: {
      type: nodeType.type,
      name: nodeConfig.name,
      description: nodeConfig.description,
      config: getDefaultConfig(nodeType.type),
      category: nodeConfig.category
    }
  })

  return node
}

/**
 * 获取默认配置
 */
const getDefaultConfig = (nodeType) => {
  const baseConfig = {
    inputParams: [],
    outputParams: [],
    workerGroup: 'default',
    environment: 'production',
    timeout: 300,
    retryCount: 0
  }

  switch (nodeType) {
    // 数据处理类
    case 'sql-execute':
      return { ...baseConfig, dbType: 'mysql', connectionString: '', sqlScript: '', queryType: 'select', outputTable: '' }
    // AI智能类
    case 'llm-chat':
      return { ...baseConfig, modelName: 'gpt-3.5-turbo', apiKey: '', prompt: '', temperature: 0.7, maxTokens: 1000 }
    case 'ai-agent':
      return { ...baseConfig, agentType: 'general', instructions: '', tools: [], maxIterations: 10 }
    case 'text-analysis':
      return { ...baseConfig, analysisType: 'sentiment', inputText: '', language: 'zh-CN', outputFormat: 'json' }
    case 'image-recognition':
      return { ...baseConfig, modelType: 'classification', imagePath: '', confidence: 0.8, outputFormat: 'json' }
    case 'speech-processing':
      return { ...baseConfig, operation: 'speech-to-text', audioPath: '', language: 'zh-CN', outputFormat: 'text' }
    // 流程控制类
    case 'condition':
      return { ...baseConfig, conditionExpression: '', trueAction: '', falseAction: '' }
    case 'loop':
      return { ...baseConfig, loopType: 'for', loopCondition: '', maxIterations: 100 }
    case 'shell':
      return { ...baseConfig, script: '', scriptPath: '', arguments: [] }
    case 'python':
      return { ...baseConfig, script: '', scriptPath: '', pythonPath: 'python', requirements: [] }
    case 'delay':
      return { ...baseConfig, delayTime: 60, delayUnit: 'seconds' }
    case 'http-request':
      return { ...baseConfig, url: '', method: 'GET', headers: {}, body: '', timeout: 30 }
    case 'file-process':
      return { ...baseConfig, operation: 'read', filePath: '', encoding: 'utf-8' }
    case 'email-send':
      return { ...baseConfig, smtpServer: '', port: 587, username: '', password: '', to: '', subject: '', body: '' }
    case 'ftp-transfer':
      return { ...baseConfig, ftpServer: '', port: 21, username: '', password: '', operation: 'upload', localPath: '', remotePath: '' }
    case 'database-query':
      return { ...baseConfig, dbType: 'mysql', connectionString: '', query: '', queryType: 'select' }
    case 'start':
      return { ...baseConfig, description: '工作流开始节点' }
    case 'end':
      return { ...baseConfig, description: '工作流结束节点' }
    default:
      return baseConfig
  }
}

/**
 * 创建默认的开始和结束节点
 */
const createDefaultNodes = () => {
  if (!graph) {
    console.warn('Graph not initialized')
    return
  }

  // 获取画布尺寸
  const canvasRect = graph.container.getBoundingClientRect()
  const centerX = canvasRect.width / 2
  const startY = 100
  const endY = 300

  // 创建开始节点
  const startNodeType = { type: 'start' }
  const startNode = createNode(startNodeType, centerX, startY)
  
  // 创建结束节点
  const endNodeType = { type: 'end' }
  const endNode = createNode(endNodeType, centerX, endY)

  console.log('默认节点已创建:', { startNode: startNode?.id, endNode: endNode?.id })
}

/**
 * 拖拽开始
 */
const handleDragStart = (event, nodeType) => {
  event.dataTransfer.setData('application/x-node-type', JSON.stringify(nodeType))
  event.dataTransfer.effectAllowed = 'copy'
  
  // 添加拖拽样式
  event.target.style.opacity = '0.5'
}

/**
 * 拖拽结束
 */
const handleDragEnd = (event) => {
  event.target.style.opacity = '1'
}

/**
 * 拖拽悬停
 */
const handleDragOver = (event) => {
  event.preventDefault()
  event.dataTransfer.dropEffect = 'copy'
}

/**
 * 拖拽放置
 */
const handleDrop = (event) => {
  event.preventDefault()
  const nodeTypeData = event.dataTransfer.getData('application/x-node-type')
  if (!nodeTypeData) return

  const nodeType = JSON.parse(nodeTypeData)
  const rect = event.currentTarget.getBoundingClientRect()
  const x = event.clientX - rect.left
  const y = event.clientY - rect.top

  // 转换为图坐标
  const point = graph.clientToLocal({ x, y })
  createNode(nodeType, point.x, point.y)
}

/**
 * 工具栏操作
 */
const handleZoomIn = () => {
    if (graph) {
      graph.zoom(0.1)
    }
  }
  
  const handleZoomOut = () => {
    if (graph) {
      graph.zoom(-0.1)
    }
  }
  
  const handleZoomFit = () => {
    if (graph) {
      graph.zoomToFit({ padding: 20, maxScale: 1 })
    }
  }
  
  const handleUndo = () => {
    if (graph && graph.canUndo()) {
      graph.undo()
    }
  }
  
  const handleRedo = () => {
    if (graph && graph.canRedo()) {
      graph.redo()
    }
  }
const handleClearAll = () => {
  ElMessageBox.confirm(
    '确定要清空画布吗？此操作不可撤销。',
    '确认清空',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(() => {
    graph.clearCells()
    selectedNode.value = null
    ElMessage.success('画布已清空')
  }).catch(() => {
    // 用户取消
  })
}

/**
 * 验证工作流
 */
const validateWorkflow = (graphData) => {
  const nodes = graphData.cells.filter(cell => cell.shape === 'workflow-node')
  const edges = graphData.cells.filter(cell => cell.shape === 'edge')
  
  // 检查是否有孤立节点（除了起始节点）
  const connectedNodes = new Set()
  edges.forEach(edge => {
    connectedNodes.add(edge.source.cell)
    connectedNodes.add(edge.target.cell)
  })
  
  const isolatedNodes = nodes.filter(node => 
    !connectedNodes.has(node.id) && 
    node.data?.type !== 'data-input'
  )
  
  if (isolatedNodes.length > 0) {
    return {
      valid: false,
      message: `存在孤立节点: ${isolatedNodes.map(n => n.data?.name).join(', ')}`
    }
  }
  
  // 检查是否有循环依赖
  const hasCycle = detectCycle(nodes, edges)
  if (hasCycle) {
    return {
      valid: false,
      message: '工作流中存在循环依赖'
    }
  }
  
  return { valid: true }
}

/**
 * 检测循环依赖
 */
const detectCycle = (nodes, edges) => {
  const graph = new Map()
  const visited = new Set()
  const recStack = new Set()
  
  // 构建邻接表
  nodes.forEach(node => graph.set(node.id, []))
  edges.forEach(edge => {
    const source = edge.source.cell
    const target = edge.target.cell
    if (graph.has(source)) {
      graph.get(source).push(target)
    }
  })
  
  // DFS检测循环
  const dfs = (nodeId) => {
    visited.add(nodeId)
    recStack.add(nodeId)
    
    const neighbors = graph.get(nodeId) || []
    for (const neighbor of neighbors) {
      if (!visited.has(neighbor)) {
        if (dfs(neighbor)) return true
      } else if (recStack.has(neighbor)) {
        return true
      }
    }
    
    recStack.delete(nodeId)
    return false
  }
  
  for (const nodeId of graph.keys()) {
    if (!visited.has(nodeId)) {
      if (dfs(nodeId)) return true
    }
  }
  
  return false
}

/**
 * 缩放到适合
 */
const zoomToFit = () => {
  graph.zoomToFit({ padding: 20, maxScale: 1 })
}

/**
 * 重置缩放
 */
const resetZoom = () => {
  graph.zoomTo(1)
  graph.centerContent()
}

/**
 * 导出为图片
 */
const exportImage = () => {
  graph.toPNG((dataUri) => {
    const link = document.createElement('a')
    link.download = `${workflowName.value || 'workflow'}.png`
    link.href = dataUri
    link.click()
  }, {
    backgroundColor: '#ffffff',
    padding: 20
  })
}

/**
 * 导出为JSON
 */
const exportJSON = () => {
  const graphData = graph.toJSON()
  const workflowData = {
    name: workflowName.value,
    description: '',
    graph: graphData,
    exportedAt: new Date().toISOString()
  }
  
  const blob = new Blob([JSON.stringify(workflowData, null, 2)], {
    type: 'application/json'
  })
  
  const link = document.createElement('a')
  link.download = `${workflowName.value || 'workflow'}.json`
  link.href = URL.createObjectURL(blob)
  link.click()
  
  URL.revokeObjectURL(link.href)
}

/**
 * 导入JSON
 */
const importJSON = () => {
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = '.json'
  
  input.onchange = (event) => {
    const file = event.target.files[0]
    if (!file) return
    
    const reader = new FileReader()
    reader.onload = (e) => {
      try {
        const workflowData = JSON.parse(e.target.result)
        
        if (workflowData.graph) {
          graph.fromJSON(workflowData.graph)
          workflowName.value = workflowData.name || ''
          ElMessage.success('工作流导入成功')
        } else {
          ElMessage.error('无效的工作流文件')
        }
      } catch (error) {
        console.error('导入失败:', error)
        ElMessage.error('文件格式错误')
      }
    }
    
    reader.readAsText(file)
  }
  
  input.click()
}

/**
 * 面板操作
 */
const toggleNodePanel = () => {
  showNodePanel.value = !showNodePanel.value
}

const handleClosePropertyPanel = () => {
  showPropertyPanel.value = false
  selectedNode.value = null
}

/**
 * 节点属性更新
 */
const updateNodeProperty = (key, value) => {
  if (!selectedNode.value || !graph) return
  
  if (key) {
    selectedNode.value[key] = value
  }
  
  const node = graph.getCellById(selectedNode.value.id)
  if (node) {
    node.attr('text/text', selectedNode.value.name)
    node.setData({
      ...node.getData(),
      name: selectedNode.value.name,
      description: selectedNode.value.description,
      config: selectedNode.value.config
    })
  }
}

/**
 * 获取节点类型名称
 */
const getNodeTypeName = (type) => {
  const nodeType = nodeTypes.value.find(node => node.type === type)
  return nodeType ? nodeType.name : type
}

/**
 * 获取配置组件
 */
const getConfigComponent = (type) => {
  return NodeConfig
}

/**
 * 页面操作
 */
const goBack = () => {
  router.push('/workflows')
}

const handleSave = async () => {
  if (!workflowName.value.trim()) {
    ElMessage.warning('请输入工作流名称')
    return
  }

  const nodes = graph.getNodes()
  if (nodes.length === 0) {
    ElMessage.warning('工作流中至少需要一个节点')
    return
  }

  saveLoading.value = true
  try {
    // 获取图形数据
    const graphData = graph.toJSON()
    
    // 验证工作流完整性
    const validation = validateWorkflow(graphData)
    if (!validation.valid) {
      ElMessage.warning(`工作流验证失败: ${validation.message}`)
      saveLoading.value = false
      return
    }
    
    // 构建保存数据
    const workflowData = {
      name: workflowName.value,
      description: '',
      workflow_config: {
        graph: graphData
      },
      nodes: graphData.cells.filter(cell => cell.shape === 'workflow-node'),
      connections: graphData.cells.filter(cell => cell.shape === 'edge')
    }

    // 获取工作流ID，判断是创建还是更新
    const workflowId = route.params.id
    let response
    
    if (workflowId && workflowId !== 'new') {
      // 更新现有工作流
      response = await workflowApi.updateWorkflow(workflowId, workflowData)
      ElMessage.success('工作流更新成功')
    } else {
      // 创建新工作流
      response = await workflowApi.createWorkflow(workflowData)
      ElMessage.success('工作流创建成功')
      
      // 创建成功后跳转到编辑页面
      if (response.data && response.data.id) {
        router.replace(`/workflows/edit/${response.data.id}`)
      }
    }
    
    console.log('保存工作流成功:', response.data)
  } catch (error) {
    console.error('保存失败:', error)
    const errorMessage = error.response?.data?.detail || error.message || '保存失败'
    ElMessage.error(errorMessage)
  } finally {
    saveLoading.value = false
  }
}

const handlePreview = () => {
  const graphData = graph.toJSON()
  console.log('预览工作流:', graphData)
  ElMessage.info('预览功能开发中')
}

/**
 * 加载工作流数据
 */
const loadWorkflowData = async (workflowId) => {
  try {
    // 响应拦截器已经返回了data部分，所以response就是工作流对象
    const workflow = await workflowApi.getWorkflowDetail(workflowId)
    
    // 设置工作流名称
    if (workflow && workflow.name) {
      workflowName.value = workflow.name
    }
    
    // 如果有图形数据，加载到编辑器中
    if (workflow && workflow.workflow_config && workflow.workflow_config.graph) {
      // 延迟加载图形数据，确保图编辑器已初始化
      setTimeout(() => {
        if (graph) {
          graph.fromJSON(workflow.workflow_config.graph)
        }
      }, 200)
    }
    
    console.log('工作流数据加载成功:', workflow)
  } catch (error) {
    console.error('加载工作流数据失败:', error)
    const errorMessage = error.response?.data?.detail || error.message || '加载工作流数据失败'
    ElMessage.error(errorMessage)
  }
}

/**
 * 生命周期
 */
onMounted(async () => {
  // 获取工作流ID
  const workflowId = route.params.id
  
  // 初始化图编辑器
  setTimeout(() => {
    initGraph()
  }, 100)
  
  // 如果是编辑现有工作流，加载数据
  if (workflowId && workflowId !== 'new') {
    await loadWorkflowData(workflowId)
  }
})

onUnmounted(() => {
  // 清理注册的自定义节点
  try {
    Graph.unregisterNode('workflow-node')
    console.log('workflow-node unregistered on component unmount')
  } catch (e) {
    console.warn('Failed to unregister workflow-node:', e)
  }
  
  // 销毁图实例
  if (graph) {
    graph.dispose()
  }
})
</script>

<style scoped>
.workflow-editor {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f5f5f5;
  overflow-x: auto;
  min-width: 100%;
}

/* 工具栏样式 */
.toolbar {
  height: 56px;
  background: #fff;
  border-bottom: 1px solid #e8e8e8;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.workflow-title {
  font-size: 16px;
  font-weight: 500;
  color: #262626;
}

/* 主编辑区域 */
.editor-main {
  flex: 1;
  display: flex;
  overflow: hidden;
  min-width: 1200px;
}

/* 左侧节点面板 */
.node-panel {
  width: 280px;
  background: #fff;
  border-right: 1px solid #e8e8e8;
  display: flex;
  flex-direction: column;
  transition: all 0.3s;
}

.node-panel.collapsed {
  width: 48px;
}

.node-panel .panel-header {
  height: 48px;
  padding: 0 16px;
  border-bottom: 1px solid #e8e8e8;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.node-panel .panel-header h3 {
  margin: 0;
  font-size: 14px;
  font-weight: 500;
}

.node-categories {
  padding: 12px;
  border-bottom: 1px solid #e8e8e8;
}

.category-item {
  padding: 8px 12px;
  margin-bottom: 4px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s;
}

.category-item:hover {
  background: #f0f0f0;
}

.category-item.active {
  background: #e6f7ff;
  color: #1890ff;
}

.node-list {
  flex: 1;
  padding: 12px;
  overflow-y: auto;
}

.node-item {
  padding: 12px;
  margin-bottom: 8px;
  background: #fafafa;
  border: 1px solid #e8e8e8;
  border-radius: 6px;
  cursor: grab;
  transition: all 0.2s;
}

.node-item:hover {
  background: #f0f0f0;
  border-color: #1890ff;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(24,144,255,0.15);
}

.node-item:active {
  cursor: grabbing;
}

.node-name {
  font-size: 13px;
  font-weight: 500;
  color: #262626;
  margin-bottom: 4px;
}

.node-desc {
  font-size: 11px;
  color: #8c8c8c;
  line-height: 1.4;
}

/* 画布区域 */
.canvas-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 600px;
}

.canvas-toolbar {
  height: 48px;
  background: #fff;
  border-bottom: 1px solid #e8e8e8;
  display: flex;
  align-items: center;
  padding: 0 16px;
  gap: 12px;
}

.toolbar-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.canvas {
  flex: 1;
  background: #f8f9fa;
  min-height: 400px;
}

/* 抽屉式属性面板样式 */
.drawer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}

.drawer-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

.node-type-badge {
  background: #e6f7ff;
  color: #1890ff;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.drawer-content {
  padding: 0;
}

.drawer-content .el-form {
  padding: 0;
}

/* 抽屉内的配置组件样式优化 */
:deep(.el-drawer__body) {
  padding: 20px;
  background: #f8f9fa;
}

:deep(.el-drawer__header) {
  margin-bottom: 0;
  padding: 20px 20px 16px;
  border-bottom: 1px solid #e8e8e8;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .node-panel {
    width: 240px;
  }
}

@media (max-width: 768px) {
  .editor-main {
    min-width: 800px;
  }
  
  .node-panel {
    width: 200px;
  }
  
  .node-panel.collapsed {
    width: 0;
  }
  
  .canvas-area {
    min-width: 400px;
  }
  
  /* 移动端抽屉样式调整 */
  :deep(.el-drawer) {
    width: 90% !important;
    max-width: 350px;
  }
}
</style>