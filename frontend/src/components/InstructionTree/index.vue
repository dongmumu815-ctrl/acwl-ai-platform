<template>
  <div class="instruction-tree">
    <!-- 树头部 -->
    <div class="tree-header">
      <div class="header-left">
        <h3 class="tree-title">
          <el-icon><Share /></el-icon>
          指令树结构
        </h3>
        <el-tag v-if="treeData.length > 0" size="small" type="info">
          {{ treeData.length }} 个根节点
        </el-tag>
      </div>
      <div class="header-actions">
        <el-button 
          size="small" 
          @click="handleAddRootNode"
          :disabled="hasRootNode"
          :title="hasRootNode ? '只能有一个根节点' : '添加根节点'"
        >
          <el-icon><Plus /></el-icon>
          添加根节点
        </el-button>
        <el-button size="small" @click="handleExpandAll">
          <el-icon><Expand /></el-icon>
          展开全部
        </el-button>
        <el-button size="small" @click="handleCollapseAll">
          <el-icon><Fold /></el-icon>
          收起全部
        </el-button>
      </div>
    </div>

    <!-- 树内容 -->
    <div class="tree-content">
      <div v-if="loading" class="tree-loading">
        <el-skeleton :rows="5" animated />
      </div>
      <div v-else-if="treeData.length === 0" class="tree-empty">
        <el-empty description="暂无指令节点">
          <el-button type="primary" @click="handleAddRootNode">
            <el-icon><Plus /></el-icon>
            创建根节点
          </el-button>
        </el-empty>
      </div>
      <el-tree
        v-else
        ref="treeRef"
        :data="treeData"
        :props="treeProps"
        :expand-on-click-node="false"
        :default-expand-all="false"
        :allow-drag="allowDrag"
        :allow-drop="allowDrop"
        node-key="id"
        draggable
        @node-click="handleNodeClick"
        @node-contextmenu="handleNodeContextMenu"
        @node-drag-start="handleDragStart"
        @node-drag-end="handleDragEnd"
        @node-drop="handleNodeDrop"
      >
        <template #default="{ node, data }">
          <div class="tree-node" :class="getNodeClass(data)" @dblclick="handleEditNode(data)">
            <div class="node-content">
              <div class="node-info">
                <div class="node-icon">
                  <el-icon :color="getNodeIconColor(data.node_type)">
                    <component :is="getNodeIcon(data.node_type)" />
                  </el-icon>
                </div>
                <div class="node-details">
                  <div class="node-title">{{ data.node_number }} {{ data.title }}</div>
                  <div class="node-meta">
                    <el-tag size="small" :type="getNodeTypeTag(data.node_type)">{{ getNodeTypeText(data.node_type) }}</el-tag>
                    <el-tag v-if="data.risk_level" size="small" :type="getRiskLevelTag(data.risk_level)">{{ getRiskLevelText(data.risk_level) }}</el-tag>
                    <span class="node-order">序号: {{ data.sort_order }}</span>
                  </div>
                </div>
              </div>
              <div class="node-status">
                <el-switch
                  v-model="data.is_active"
                  size="small"
                  @change="handleStatusChange(data)"
                />
              </div>
            </div>
            <div class="node-actions" @click.stop>
              <el-button-group size="small" class="action-buttons">
                <el-button @click="handleAddChild(data)" title="添加子节点">
                  <el-icon><Plus /></el-icon>
                </el-button>
                <el-button @click="handleEditNode(data)" title="编辑节点">
                  <el-icon><Edit /></el-icon>
                </el-button>
                <el-button @click="handleCopyNode(data)" title="复制节点">
                  <el-icon><CopyDocument /></el-icon>
                </el-button>
                <el-button type="danger" @click="handleDeleteNode(data)" title="删除节点">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </el-button-group>
            </div>
          </div>
        </template>
      </el-tree>
    </div>

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
          <el-dropdown-item command="move-up">
            <el-icon><Top /></el-icon>
            上移
          </el-dropdown-item>
          <el-dropdown-item command="move-down">
            <el-icon><Bottom /></el-icon>
            下移
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
      :parent-node="currentParentNode"
      :instruction-set-id="instructionSetId"
      @submit="handleNodeConfigSubmit"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, nextTick, watch, onMounted } from 'vue'
import { ElTree, ElMessage, ElMessageBox } from 'element-plus'
import {
  Share,
  Plus,
  Expand,
  Fold,
  Edit,
  CopyDocument,
  Delete,
  Top,
  Bottom,
  Setting,
  QuestionFilled,
  VideoPlay,
  Connection
} from '@element-plus/icons-vue'
import { instructionNodeApi } from '@/api/instruction-set'
import NodeConfigModal from './NodeConfigModal.vue'
import type {
  InstructionTreeNode,
  InstructionNode,
  InstructionNodeCreate,
  InstructionNodeUpdate,
  NodeType,
  RiskLevel
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
const treeRef = ref<InstanceType<typeof ElTree>>()
const contextMenuRef = ref()
const configModalVisible = ref(false)
const currentNode = ref<InstructionTreeNode | null>(null)
const currentParentNode = ref<InstructionTreeNode | null>(null)
const contextMenuNode = ref<InstructionTreeNode | null>(null)

// 计算属性
/**
 * 是否已有根节点
 */
const hasRootNode = computed(() => {
  return props.treeData && props.treeData.length > 0
})

// 树配置
const treeProps = {
  children: 'children',
  label: 'title'
}

/**
 * 获取节点图标
 */
const getNodeIcon = (nodeType: NodeType) => {
  const iconMap = {
    CONDITION: QuestionFilled,
    ACTION: VideoPlay,
    BRANCH: Connection
  }
  return iconMap[nodeType] || Setting
}

/**
 * 获取节点图标颜色
 */
const getNodeIconColor = (nodeType: NodeType) => {
  const colorMap = {
    CONDITION: '#409eff',
    ACTION: '#67c23a',
    BRANCH: '#e6a23c'
  }
  return colorMap[nodeType] || '#909399'
}

/**
 * 获取节点类型标签
 */
const getNodeTypeTag = (nodeType: NodeType) => {
  const tagMap = {
    CONDITION: 'primary',
    ACTION: 'success',
    BRANCH: 'warning'
  }
  return tagMap[nodeType] || 'info'
}

/**
 * 获取节点类型文本
 */
const getNodeTypeText = (nodeType: NodeType) => {
  const textMap = {
    CONDITION: '条件',
    ACTION: '动作',
    BRANCH: '分支'
  }
  return textMap[nodeType] || nodeType
}

/**
 * 获取风险等级标签类型
 */
const getRiskLevelTag = (riskLevel: string) => {
  const tagMap = {
    'critical': 'danger',
    'high': 'danger',
    'medium': 'warning',
    'low': 'info',
    'safe': 'success'
  }
  return tagMap[riskLevel] || 'info'
}

/**
 * 获取风险等级中文文本
 */
const getRiskLevelText = (riskLevel: string) => {
  const textMap = {
    'critical': '严重',
    'high': '高风险',
    'medium': '中风险',
    'low': '低风险',
    'safe': '安全'
  }
  return textMap[riskLevel] || riskLevel
}

/**
 * 获取节点样式类
 */
const getNodeClass = (node: InstructionTreeNode) => {
  return {
    'node-active': node.is_active,
    'node-inactive': !node.is_active,
    [`node-${node.node_type}`]: true
  }
}

/**
 * 是否允许拖拽
 */
const allowDrag = (draggingNode: any) => {
  return true // 允许所有节点拖拽
}

/**
 * 是否允许放置
 */
const allowDrop = (draggingNode: any, dropNode: any, type: string) => {
  // 不允许拖拽到自己的子节点中
  if (type === 'inner') {
    return dropNode.data.node_type === 'BRANCH' // 只有分支节点可以作为容器
  }
  return true
}

/**
 * 节点点击处理
 */
const handleNodeClick = (data: InstructionTreeNode) => {
  emit('nodeClick', data)
}

/**
 * 节点右键菜单
 */
const handleNodeContextMenu = (event: MouseEvent, data: InstructionTreeNode) => {
  event.preventDefault()
  contextMenuNode.value = data
  // 这里可以显示右键菜单，但Element Plus的dropdown组件不太适合这种场景
  // 可以考虑使用第三方库或自定义实现
}

/**
 * 右键菜单命令处理
 */
const handleContextMenuCommand = (command: string) => {
  if (!contextMenuNode.value) return
  
  switch (command) {
    case 'add-child':
      handleAddChild(contextMenuNode.value)
      break
    case 'edit':
      handleEditNode(contextMenuNode.value)
      break
    case 'copy':
      handleCopyNode(contextMenuNode.value)
      break
    case 'move-up':
      handleMoveUp(contextMenuNode.value)
      break
    case 'move-down':
      handleMoveDown(contextMenuNode.value)
      break
    case 'delete':
      handleDeleteNode(contextMenuNode.value)
      break
  }
  contextMenuNode.value = null
}

/**
 * 添加根节点
 */
const handleAddRootNode = () => {
  // 检查是否已有根节点
  if (hasRootNode.value) {
    ElMessage.warning('只能有一个根节点，请在现有根节点下添加子节点')
    return
  }
  currentNode.value = null
  currentParentNode.value = null
  configModalVisible.value = true
}

/**
 * 添加子节点
 */
const handleAddChild = (parentNode: InstructionTreeNode) => {
  // 对于添加子节点，currentNode应该为null，表示创建新节点
  // 父节点信息通过parentNode传递给模态框
  currentNode.value = null
  currentParentNode.value = parentNode
  configModalVisible.value = true
}

/**
 * 编辑节点
 */
const handleEditNode = (node: InstructionTreeNode) => {
  // 对于编辑节点，currentNode为要编辑的节点，parentNode应该为null
  currentNode.value = node
  currentParentNode.value = null
  configModalVisible.value = true
}

/**
 * 复制节点
 */
const handleCopyNode = async (node: InstructionTreeNode) => {
  try {
    const copyData: InstructionNodeCreate = {
      title: `${node.title} - 副本`,
      node_type: node.node_type,
      parent_id: node.parent_id,
      sort_order: node.sort_order + 1,
      is_active: false,
      config: {} // 需要从原节点获取配置
    }
    
    const response = await instructionNodeApi.createInstructionNode(props.instructionSetId, copyData)
    if (response.success) {
      ElMessage.success('复制成功')
      emit('treeChange')
    }
  } catch (error) {
    console.error('复制节点失败:', error)
    ElMessage.error('复制节点失败')
  }
}

/**
 * 删除节点
 */
const handleDeleteNode = async (node: InstructionTreeNode) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除节点 "${node.title}" 吗？此操作将同时删除所有子节点。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const response = await instructionNodeApi.deleteInstructionNode(node.id)
    if (response.success) {
      ElMessage.success('删除成功')
      emit('treeChange')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除节点失败:', error)
      ElMessage.error('删除节点失败')
    }
  }
}

/**
 * 上移节点
 */
const handleMoveUp = async (node: InstructionTreeNode) => {
  if (node.sort_order <= 1) {
    ElMessage.warning('已经是第一个节点')
    return
  }
  
  try {
    const updateData: InstructionNodeUpdate = {
      sort_order: node.sort_order - 1
    }
    const response = await instructionNodeApi.updateInstructionNode(node.id, updateData)
    if (response.success) {
      ElMessage.success('移动成功')
      emit('treeChange')
    }
  } catch (error) {
    console.error('移动节点失败:', error)
    ElMessage.error('移动节点失败')
  }
}

/**
 * 下移节点
 */
const handleMoveDown = async (node: InstructionTreeNode) => {
  try {
    const updateData: InstructionNodeUpdate = {
      sort_order: node.sort_order + 1
    }
    const response = await instructionNodeApi.updateInstructionNode(node.id, updateData)
    if (response.success) {
      ElMessage.success('移动成功')
      emit('treeChange')
    }
  } catch (error) {
    console.error('移动节点失败:', error)
    ElMessage.error('移动节点失败')
  }
}

/**
 * 状态变更处理
 */
const handleStatusChange = async (node: InstructionTreeNode) => {
  try {
    const updateData: InstructionNodeUpdate = {
      is_active: node.is_active
    }
    const response = await instructionNodeApi.updateInstructionNode(node.id, updateData)
    if (response.success) {
      ElMessage.success('状态更新成功')
      emit('treeChange')
    } else {
      // 如果更新失败，恢复原状态
      node.is_active = !node.is_active
    }
  } catch (error) {
    console.error('更新状态失败:', error)
    ElMessage.error('更新状态失败')
    // 恢复原状态
    node.is_active = !node.is_active
  }
}

/**
 * 展开全部
 */
const handleExpandAll = () => {
  if (treeRef.value) {
    // 尝试使用 store 方式展开所有节点
    try {
      if (treeRef.value.store && treeRef.value.store._getAllNodes) {
        const allNodes = treeRef.value.store._getAllNodes()
        allNodes.forEach((node: any) => {
          node.expanded = true
        })
      } else if (typeof treeRef.value.setExpandedKeys === 'function') {
        // 收集所有节点的key
        const getAllNodeKeys = (nodes: InstructionTreeNode[]): (string | number)[] => {
          let keys: (string | number)[] = []
          nodes.forEach(node => {
            keys.push(node.id)
            if (node.children && node.children.length > 0) {
              keys = keys.concat(getAllNodeKeys(node.children))
            }
          })
          return keys
        }
        
        const allKeys = getAllNodeKeys(props.treeData)
        treeRef.value.setExpandedKeys(allKeys)
      }
    } catch (error) {
      console.error('Error expanding nodes:', error)
    }
  }
}

/**
 * 收起全部
 */
const handleCollapseAll = () => {
  if (treeRef.value) {
    // 尝试使用 store 方式收起所有节点
    try {
      if (treeRef.value.store && treeRef.value.store._getAllNodes) {
        const allNodes = treeRef.value.store._getAllNodes()
        allNodes.forEach((node: any) => {
          node.expanded = false
        })
      } else if (typeof treeRef.value.setExpandedKeys === 'function') {
        // 设置空数组来收起所有节点
        treeRef.value.setExpandedKeys([])
      }
    } catch (error) {
      console.error('Error collapsing nodes:', error)
    }
  }
}

/**
 * 拖拽开始
 */
const handleDragStart = (node: any, event: DragEvent) => {
  console.log('拖拽开始:', node.data)
}

/**
 * 拖拽结束
 */
const handleDragEnd = (draggingNode: any, dropNode: any, dropType: string, event: DragEvent) => {
  console.log('拖拽结束:', draggingNode.data, dropNode?.data, dropType)
}

/**
 * 节点放置
 */
const handleNodeDrop = (draggingNode: any, dropNode: any, dropType: string, event: DragEvent) => {
  console.log('节点放置:', draggingNode.data, dropNode?.data, dropType)
  
  // 这里需要调用API更新节点的父级和排序
  const dragData = draggingNode.data as InstructionTreeNode
  const dropData = dropNode?.data as InstructionTreeNode
  
  let newParentId: number | null = null
  let newSortOrder = 1
  
  if (dropType === 'inner') {
    // 放置到节点内部，成为子节点
    newParentId = dropData.id
    newSortOrder = (dropData.children?.length || 0) + 1
  } else if (dropType === 'before' || dropType === 'after') {
    // 放置到节点前后，成为同级节点
    newParentId = dropData.parent_id || null
    newSortOrder = dropType === 'before' ? dropData.sort_order : dropData.sort_order + 1
  }
  
  emit('nodeMove', dragData, dropData, newSortOrder)
}

/**
 * 节点配置提交
 */
const handleNodeConfigSubmit = () => {
  configModalVisible.value = false
  emit('treeChange')
}

/**
 * 自动创建默认根节点
 */
const createDefaultRootNode = async () => {
  try {
    const defaultNodeData: InstructionNodeCreate = {
      instruction_set_id: props.instructionSetId,
      title: '默认根节点',
      description: '这是一个默认创建的根节点，您可以编辑或删除它',
      node_type: 'CONDITION',
      parent_id: null,
      sort_order: 1,
      is_active: true,
      config: {
        condition: '',
        true_action: '',
        false_action: ''
      }
    }
    
    const response = await instructionNodeApi.createInstructionNode(props.instructionSetId, defaultNodeData)
    if (response.success) {
      ElMessage.success('已自动创建默认根节点')
      emit('treeChange')
    }
  } catch (error) {
    console.error('创建默认根节点失败:', error)
    // 不显示错误消息，因为这是自动操作
  }
}

// 监听treeData变化，当为空时自动创建默认根节点
watch(() => props.treeData, (newData) => {
  // 只有在没有任何节点且不在加载状态时才自动创建根节点
  if (newData && newData.length === 0 && props.instructionSetId && !props.loading) {
    // 延迟一下确保组件完全加载
    setTimeout(() => {
      // 再次检查确保没有根节点
      if (!hasRootNode.value) {
        createDefaultRootNode()
      }
    }, 1000)
  }
}, { immediate: true })

// 暴露方法给父组件
defineExpose({
  handleAddRootNode
})
</script>

<style scoped>
.instruction-tree {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.tree-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 0;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.tree-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.header-actions {
  display: flex;
  gap: 8px;
}

.tree-content {
  flex: 1;
  padding: 16px 0;
  overflow: auto;
}

.tree-loading {
  padding: 20px;
}

.tree-empty {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 300px;
}

.tree-node {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  padding: 8px 12px;
  border-radius: 6px;
  transition: all 0.2s;
}

.tree-node:hover {
  background-color: var(--el-fill-color-light);
}

.node-content {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
}

.node-info {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
}

.node-icon {
  width: 32px;
  height: 32px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--el-fill-color-lighter);
  font-size: 16px;
}

.node-details {
  flex: 1;
}

.node-title {
  font-weight: 500;
  color: var(--el-text-color-primary);
  margin-bottom: 4px;
}

.node-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--el-text-color-regular);
  flex-wrap: wrap;
}

.node-meta .el-tag {
  margin-right: 4px;
}

.node-order {
  font-size: 11px;
  color: var(--el-text-color-placeholder);
}

.node-status {
  margin-right: 12px;
}

.node-actions {
  opacity: 0;
  transition: all 0.2s ease-in-out;
  transform: translateX(8px);
}

.action-buttons {
  background: var(--el-bg-color-overlay);
  border-radius: 6px;
  padding: 4px;
  box-shadow: var(--el-box-shadow-light);
}

.tree-node:hover .node-actions {
  opacity: 1;
  transform: translateX(0);
}

/* 节点状态样式 */
.node-inactive {
  opacity: 0.6;
}

.node-inactive .node-title {
  color: var(--el-text-color-placeholder);
}

/* 节点类型样式 */
.node-CONDITION .node-icon {
  background-color: rgba(64, 158, 255, 0.1);
  color: #409eff;
}

.node-ACTION .node-icon {
  background-color: rgba(103, 194, 58, 0.1);
  color: #67c23a;
}

.node-BRANCH .node-icon {
  background-color: rgba(230, 162, 60, 0.1);
  color: #e6a23c;
}

/* el-tree-node 高度修复 */
:deep(.el-tree-node) {
  min-height: 64px;
  margin-bottom: 4px;
}

:deep(.el-tree-node__content) {
  min-height: 64px;
  padding: 12px 8px;
  display: flex;
  align-items: center;
  border-radius: 6px;
  transition: all 0.2s ease;
}

:deep(.el-tree-node__content:hover) {
  background-color: var(--el-fill-color-light);
}

:deep(.el-tree-node__expand-icon) {
  padding: 8px;
  margin-right: 4px;
}

:deep(.el-tree-node.is-expanded > .el-tree-node__content) {
  background-color: var(--el-fill-color-lighter);
}

:deep(.el-tree-node.is-current > .el-tree-node__content) {
  background-color: var(--el-color-primary-light-9);
  border: 1px solid var(--el-color-primary-light-7);
}

:deep(.el-tree-node.is-focusable.is-current > .el-tree-node__content) {
  background-color: var(--el-color-primary-light-8);
}

/* 拖拽样式 */
.el-tree-node.is-dragging {
  opacity: 0.5;
}

.el-tree-node.is-drop-inner {
  background-color: var(--el-color-primary-light-9);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .tree-header {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }
  
  .header-actions {
    justify-content: center;
  }
  
  .node-actions {
    opacity: 1; /* 在移动设备上始终显示操作按钮 */
  }
}
</style>