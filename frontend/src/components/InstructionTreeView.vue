<template>
  <div class="instruction-tree-view">
    <!-- 工具栏 -->
    <div class="tree-toolbar">
      <div class="toolbar-left">
        <el-button size="small" type="primary" @click="handleAddRoot">
          <el-icon><Plus /></el-icon>
          新增根节点
        </el-button>
        <el-button size="small" @click="expandAll">
          <el-icon><ArrowDown /></el-icon>
          展开全部
        </el-button>
        <el-button size="small" @click="collapseAll">
          <el-icon><ArrowUp /></el-icon>
          收起全部
        </el-button>
      </div>
      <div class="toolbar-right">
        <el-input
          v-model="searchText"
          placeholder="搜索节点..."
          size="small"
          style="width: 200px"
          clearable
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
      </div>
    </div>

    <!-- 树形结构 -->
    <div class="tree-container">
      <el-tree
        ref="treeRef"
        :data="treeData"
        :props="treeProps"
        :filter-node-method="filterNode"
        :expand-on-click-node="false"
        :default-expand-all="false"
        node-key="id"
        draggable
        @node-drop="handleNodeDrop"
        class="instruction-tree"
      >
        <template #default="{ node, data }">
          <div class="tree-node">
            <div class="node-card">
              <!-- 节点主要内容 -->
              <div class="node-main">
                <!-- 节点图标和标题 -->
                <div class="node-header">
                  <div class="node-icon-wrapper">
                    <el-icon class="node-icon" :class="getNodeIconClass(data)">
                      <component :is="getNodeIcon(data)" />
                    </el-icon>
                  </div>
                  <div class="node-title-wrapper">
                    <div class="node-title">{{ data.name }}</div>
                    <div class="node-meta">
                      <el-tag
                        v-if="data.status"
                        :type="getStatusType(data.status)"
                        size="small"
                        class="status-tag"
                      >
                        {{ getStatusText(data.status) }}
                      </el-tag>
                      <el-tag
                        v-if="data.type"
                        type="info"
                        size="small"
                        class="type-tag"
                      >
                        {{ getTypeText(data.type) }}
                      </el-tag>
                    </div>
                  </div>
                </div>
                
                <!-- 节点描述 -->
                <div class="node-description" v-if="data.description">
                  {{ data.description }}
                </div>
                
                <!-- 节点额外信息 -->
                <div class="node-extra" v-if="data.version || data.originalData">
                  <span v-if="data.version" class="version-info">
                    版本: {{ data.version }}
                  </span>
                  <span v-if="data.originalData && data.originalData.created_at" class="date-info">
                    创建: {{ formatDate(data.originalData.created_at) }}
                  </span>
                </div>
              </div>
              
              <!-- 节点操作 -->
              <div class="node-actions">
                <el-button
                  size="small"
                  type="text"
                  @click="handleAddChild(data)"
                  title="添加子节点"
                  class="action-btn"
                >
                  <el-icon><Plus /></el-icon>
                </el-button>
                <el-button
                  size="small"
                  type="text"
                  @click="handleEdit(data)"
                  title="编辑"
                  class="action-btn"
                >
                  <el-icon><Edit /></el-icon>
                </el-button>
                <el-button
                  size="small"
                  type="text"
                  @click="handleDelete(data)"
                  title="删除"
                  class="action-btn delete-btn"
                >
                  <el-icon><Delete /></el-icon>
                </el-button>
              </div>
            </div>
          </div>
        </template>
      </el-tree>
    </div>

    <!-- 空状态 -->
    <div v-if="!treeData.length" class="empty-state">
      <el-empty description="暂无指令集数据">
        <el-button type="primary" @click="handleAddRoot">
          创建第一个指令集
        </el-button>
      </el-empty>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'
import { ElTree, ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus,
  ArrowDown,
  ArrowUp,
  Search,
  Edit,
  Delete,
  Folder,
  Document,
  Setting
} from '@element-plus/icons-vue'
import type { InstructionSet, InstructionNode, InstructionTreeNode } from '@/types/instruction-set'

// Props
interface Props {
  data: InstructionSet[]
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  loading: false
})

// Emits
const emit = defineEmits<{
  addRoot: []
  addChild: [parent: InstructionSet | InstructionNode]
  edit: [item: InstructionSet | InstructionNode]
  delete: [item: InstructionSet | InstructionNode]
  move: [dragNode: any, dropNode: any, dropType: string]
}>()

// 响应式数据
const treeRef = ref<InstanceType<typeof ElTree>>()
const searchText = ref('')
const treeData = ref<any[]>([])

// 树形配置
const treeProps = {
  children: 'children',
  label: 'name'
}

/**
 * 监听数据变化，转换为树形结构
 */
watch(
  () => props.data,
  (newData) => {
    treeData.value = convertToTreeData(newData)
  },
  { immediate: true }
)

/**
 * 监听搜索文本变化
 */
watch(searchText, (val) => {
  treeRef.value?.filter(val)
})

/**
 * 将扁平数据转换为树形结构
 */
const convertToTreeData = (data: InstructionSet[]): any[] => {
  return data.map(instructionSet => ({
    id: `set_${instructionSet.id}`,
    name: instructionSet.name,
    description: instructionSet.description,
    status: instructionSet.status,
    type: 'instruction_set',
    version: instructionSet.version,
    originalData: instructionSet,
    children: instructionSet.nodes?.map(node => convertNodeToTreeNode(node)) || []
  }))
}

/**
 * 将节点转换为树形节点
 */
const convertNodeToTreeNode = (node: InstructionNode): any => {
  return {
    id: `node_${node.id}`,
    name: node.name,
    description: node.description,
    type: node.type,
    originalData: node,
    children: node.children?.map(child => convertNodeToTreeNode(child)) || []
  }
}

/**
 * 获取节点图标
 */
const getNodeIcon = (data: any) => {
  if (data.type === 'instruction_set') {
    return Folder
  }
  if (data.type === 'condition') {
    return Setting
  }
  return Document
}

/**
 * 获取节点图标样式类
 */
const getNodeIconClass = (data: any) => {
  return {
    'instruction-set-icon': data.type === 'instruction_set',
    'condition-icon': data.type === 'condition',
    'action-icon': data.type === 'action'
  }
}

/**
 * 格式化日期
 */
const formatDate = (dateString: string) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  })
}

/**
 * 获取状态类型
 */
const getStatusType = (status: string) => {
  const typeMap: Record<string, string> = {
    DRAFT: 'info',
    PUBLISHED: 'success',
    ARCHIVED: 'warning'
  }
  return typeMap[status] || 'info'
}

/**
 * 获取状态文本
 */
const getStatusText = (status: string) => {
  const textMap: Record<string, string> = {
    DRAFT: '草稿',
    PUBLISHED: '已发布',
    ARCHIVED: '已归档'
  }
  return textMap[status] || status
}

/**
 * 获取类型文本
 */
const getTypeText = (type: string) => {
  const textMap: Record<string, string> = {
    instruction_set: '指令集',
    condition: '条件',
    action: '动作'
  }
  return textMap[type] || type
}

/**
 * 过滤节点
 */
const filterNode = (value: string, data: any) => {
  if (!value) return true
  return data.name.toLowerCase().includes(value.toLowerCase()) ||
         (data.description && data.description.toLowerCase().includes(value.toLowerCase()))
}

/**
 * 展开全部
 */
const expandAll = () => {
  const keys = getAllNodeKeys(treeData.value)
  treeRef.value?.setExpandedKeys(keys)
}

/**
 * 收起全部
 */
const collapseAll = () => {
  treeRef.value?.setExpandedKeys([])
}

/**
 * 获取所有节点的key
 */
const getAllNodeKeys = (nodes: any[]): string[] => {
  const keys: string[] = []
  const traverse = (nodeList: any[]) => {
    nodeList.forEach(node => {
      keys.push(node.id)
      if (node.children && node.children.length > 0) {
        traverse(node.children)
      }
    })
  }
  traverse(nodes)
  return keys
}

/**
 * 处理添加根节点
 */
const handleAddRoot = () => {
  emit('addRoot')
}

/**
 * 处理添加子节点
 */
const handleAddChild = (data: any) => {
  emit('addChild', data.originalData)
}

/**
 * 处理编辑
 */
const handleEdit = (data: any) => {
  emit('edit', data.originalData)
}

/**
 * 处理删除
 */
const handleDelete = async (data: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除 "${data.name}" 吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    emit('delete', data.originalData)
  } catch {
    // 用户取消删除
  }
}

/**
 * 处理节点拖拽
 */
const handleNodeDrop = (dragNode: any, dropNode: any, dropType: string) => {
  emit('move', dragNode.data.originalData, dropNode.data.originalData, dropType)
}
</script>

<style scoped>
.instruction-tree-view {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.tree-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 0;
  border-bottom: 1px solid var(--el-border-color-light);
  margin-bottom: 16px;
}

.toolbar-left {
  display: flex;
  gap: 8px;
}

.tree-container {
  flex: 1;
  overflow: auto;
}

.instruction-tree {
  background: transparent;
}

.tree-node {
  width: 100%;
  padding: 4px 0;
}

.node-card {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  background: var(--el-bg-color-page);
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 8px;
  padding: 12px 16px;
  margin: 2px 0;
  transition: all 0.2s ease;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
}

.node-card:hover {
  border-color: var(--el-color-primary-light-7);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  transform: translateY(-1px);
}

.node-main {
  flex: 1;
  min-width: 0;
}

.node-header {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 8px;
}

.node-icon-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 6px;
  background: var(--el-fill-color-light);
  flex-shrink: 0;
}

.node-icon {
  font-size: 16px;
}

.instruction-set-icon {
  color: var(--el-color-primary);
}

.condition-icon {
  color: var(--el-color-warning);
}

.action-icon {
  color: var(--el-color-success);
}

.node-title-wrapper {
  flex: 1;
  min-width: 0;
}

.node-title {
  font-weight: 600;
  font-size: 14px;
  color: var(--el-text-color-primary);
  line-height: 1.4;
  margin-bottom: 4px;
  word-break: break-word;
}

.node-meta {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.status-tag {
  font-size: 11px;
  height: 20px;
  line-height: 18px;
}

.type-tag {
  font-size: 11px;
  height: 20px;
  line-height: 18px;
}

.node-description {
  font-size: 13px;
  color: var(--el-text-color-regular);
  line-height: 1.5;
  margin-bottom: 8px;
  word-break: break-word;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.node-extra {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
  flex-wrap: wrap;
}

.version-info,
.date-info {
  display: flex;
  align-items: center;
  gap: 4px;
}

.node-actions {
  display: flex;
  flex-direction: column;
  gap: 4px;
  opacity: 0;
  transition: opacity 0.2s ease;
  margin-left: 12px;
  flex-shrink: 0;
}

.node-card:hover .node-actions {
  opacity: 1;
}

.action-btn {
  width: 28px;
  height: 28px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--el-text-color-regular);
  transition: all 0.2s ease;
}

.action-btn:hover {
  background-color: var(--el-fill-color);
  color: var(--el-color-primary);
}

.delete-btn {
  color: var(--el-color-danger);
}

.delete-btn:hover {
  background-color: var(--el-color-danger-light-9);
  color: var(--el-color-danger);
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 300px;
}

/* 自定义树形组件样式 */
:deep(.el-tree-node__content) {
  height: auto;
  padding: 0;
  background: transparent !important;
}

:deep(.el-tree-node__content:hover) {
  background: transparent !important;
}

:deep(.el-tree-node__expand-icon) {
  color: var(--el-text-color-secondary);
  margin-right: 8px;
  width: 16px;
  height: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 2px;
  transition: all 0.2s ease;
}

:deep(.el-tree-node__expand-icon:hover) {
  background-color: var(--el-fill-color-light);
  color: var(--el-color-primary);
}

:deep(.el-tree-node__expand-icon.expanded) {
  transform: rotate(90deg);
}

:deep(.el-tree-node) {
  margin-bottom: 4px;
}

:deep(.el-tree-node__children) {
  padding-left: 24px;
  margin-top: 4px;
}
</style>