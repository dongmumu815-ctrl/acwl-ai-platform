<template>
  <div class="instruction-set-tree">
    <!-- 工具栏 -->
    <div class="tree-toolbar">
      <el-button type="primary" @click="handleAdd" :icon="Plus">
        新增指令集
      </el-button>
      <el-button @click="expandAll" :icon="Expand">
        展开全部
      </el-button>
      <el-button @click="collapseAll" :icon="Fold">
        收起全部
      </el-button>
      <el-input
        v-model="searchText"
        placeholder="搜索指令集..."
        style="width: 300px; margin-left: 10px"
        :prefix-icon="Search"
        clearable
      />
    </div>

    <!-- 树形结构 -->
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
      @node-click="handleNodeClick"
      class="instruction-tree"
    >
      <template #default="{ node, data }">
        <div class="tree-node">
          <div class="node-content">
            <!-- 图标 -->
            <el-icon class="node-icon" :class="getNodeIconClass(data)">
              <component :is="getNodeIcon(data)" />
            </el-icon>
            
            <!-- 标题和描述 -->
            <div class="node-info">
              <div class="node-title">{{ data.name || data.title }}</div>
              <div class="node-description" v-if="data.description">
                {{ data.description }}
              </div>
            </div>
            
            <!-- 状态标签 -->
            <el-tag
              v-if="data.status"
              :type="getStatusType(data.status)"
              size="small"
              class="node-status"
            >
              {{ getStatusText(data.status) }}
            </el-tag>
            
            <!-- 节点类型标签 -->
            <el-tag
              v-if="data.node_type"
              :type="getNodeTypeColor(data.node_type)"
              size="small"
              class="node-type"
            >
              {{ getNodeTypeText(data.node_type) }}
            </el-tag>
          </div>
          
          <!-- 操作按钮 -->
          <div class="node-actions">
            <el-button
              v-if="data.type === 'instruction_set'"
              type="text"
              size="small"
              @click.stop="handleAddNode(data)"
              :icon="Plus"
            >
              添加节点
            </el-button>
            <el-button
              type="text"
              size="small"
              @click.stop="handleEdit(data)"
              :icon="Edit"
            >
              编辑
            </el-button>
            <el-button
              type="text"
              size="small"
              @click.stop="handleDelete(data)"
              :icon="Delete"
              class="delete-btn"
            >
              删除
            </el-button>
          </div>
        </div>
      </template>
    </el-tree>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { ElTree, ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus,
  Edit,
  Delete,
  Search,
  Expand,
  Fold,
  Document,
  Folder,
  Setting,
  Connection
} from '@element-plus/icons-vue'
import { instructionSetApi, instructionNodeApi } from '@/api/instruction-set'
import type {
  InstructionSet,
  InstructionNode,
  InstructionTreeNode,
  InstructionSetStatus,
  NodeType
} from '@/types/instruction-set'

// Props
interface Props {
  refreshTrigger?: number
}

const props = withDefaults(defineProps<Props>(), {
  refreshTrigger: 0
})

// Emits
const emit = defineEmits<{
  add: []
  edit: [data: InstructionSet | InstructionNode]
  delete: [data: InstructionSet | InstructionNode]
  nodeClick: [data: InstructionSet | InstructionNode]
}>()

// 响应式数据
const treeRef = ref<InstanceType<typeof ElTree>>()
const searchText = ref('')
const treeData = ref<any[]>([])
const loading = ref(false)

// 树形配置
const treeProps = {
  children: 'children',
  label: 'name'
}

/**
 * 获取节点图标
 */
const getNodeIcon = (data: any) => {
  if (data.type === 'instruction_set') {
    return Folder
  }
  
  switch (data.node_type) {
    case 'CONDITION':
      return Setting
    case 'ACTION':
      return Connection
    case 'BRANCH':
      return Document
    default:
      return Document
  }
}

/**
 * 获取节点图标样式类
 */
const getNodeIconClass = (data: any) => {
  if (data.type === 'instruction_set') {
    return 'instruction-set-icon'
  }
  return 'instruction-node-icon'
}

/**
 * 获取状态类型
 */
const getStatusType = (status: InstructionSetStatus) => {
  switch (status) {
    case 'ACTIVE':
      return 'success'
    case 'DRAFT':
      return 'info'
    case 'INACTIVE':
      return 'warning'
    case 'ARCHIVED':
      return 'danger'
    default:
      return 'info'
  }
}

/**
 * 获取状态文本
 */
const getStatusText = (status: InstructionSetStatus) => {
  switch (status) {
    case 'ACTIVE':
      return '激活'
    case 'DRAFT':
      return '草稿'
    case 'INACTIVE':
      return '未激活'
    case 'ARCHIVED':
      return '已归档'
    default:
      return status
  }
}

/**
 * 获取节点类型颜色
 */
const getNodeTypeColor = (nodeType: NodeType) => {
  switch (nodeType) {
    case 'CONDITION':
      return 'warning'
    case 'ACTION':
      return 'success'
    case 'BRANCH':
      return 'primary'
    default:
      return 'info'
  }
}

/**
 * 获取节点类型文本
 */
const getNodeTypeText = (nodeType: NodeType) => {
  switch (nodeType) {
    case 'CONDITION':
      return '条件'
    case 'ACTION':
      return '动作'
    case 'BRANCH':
      return '分支'
    default:
      return nodeType
  }
}

/**
 * 过滤节点
 */
const filterNode = (value: string, data: any) => {
  if (!value) return true
  const name = data.name || data.title || ''
  const description = data.description || ''
  return name.includes(value) || description.includes(value)
}

/**
 * 加载树形数据
 */
const loadTreeData = async () => {
  try {
    loading.value = true
    
    // 获取指令集列表
    const response = await instructionSetApi.getInstructionSets({ limit: 1000 })
    
    if (response.success) {
      const instructionSets = response.data
      
      // 为每个指令集加载其节点树
      const treeNodes = await Promise.all(
        instructionSets.map(async (set) => {
          try {
            const treeResponse = await instructionNodeApi.getInstructionTree(set.id)
            
            return {
              ...set,
              type: 'instruction_set',
              children: treeResponse.success ? treeResponse.data : []
            }
          } catch (error) {
            console.error(`加载指令集 ${set.id} 的节点树失败:`, error)
            return {
              ...set,
              type: 'instruction_set',
              children: []
            }
          }
        })
      )
      
      treeData.value = treeNodes
    }
  } catch (error) {
    console.error('加载树形数据失败:', error)
    ElMessage.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

/**
 * 展开全部
 */
const expandAll = () => {
  treeRef.value?.setExpandedKeys(getAllNodeKeys(treeData.value))
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
      keys.push(node.id.toString())
      if (node.children && node.children.length > 0) {
        traverse(node.children)
      }
    })
  }
  
  traverse(nodes)
  return keys
}

/**
 * 处理节点拖拽
 */
const handleNodeDrop = async (draggingNode: any, dropNode: any, dropType: string) => {
  try {
    const dragData = draggingNode.data
    const dropData = dropNode.data
    
    // 只允许节点在同一指令集内移动
    if (dragData.type !== 'instruction_set' && dropData.type !== 'instruction_set') {
      if (dragData.instruction_set_id !== dropData.instruction_set_id) {
        ElMessage.warning('不能跨指令集移动节点')
        await loadTreeData() // 重新加载数据恢复原状
        return
      }
      
      // 调用移动API
      const newParentId = dropType === 'inner' ? dropData.id : dropData.parent_id
      await instructionNodeApi.moveInstructionNode(dragData.id, newParentId)
      
      ElMessage.success('节点移动成功')
    } else {
      ElMessage.warning('不支持此类型的拖拽操作')
      await loadTreeData() // 重新加载数据恢复原状
    }
  } catch (error) {
    console.error('移动节点失败:', error)
    ElMessage.error('移动节点失败')
    await loadTreeData() // 重新加载数据恢复原状
  }
}

/**
 * 处理节点点击
 */
const handleNodeClick = (data: any) => {
  emit('nodeClick', data)
}

/**
 * 处理添加
 */
const handleAdd = () => {
  emit('add')
}

/**
 * 处理添加节点
 */
const handleAddNode = (data: InstructionSet) => {
  // 这里可以打开添加节点的对话框
  console.log('添加节点到指令集:', data.id)
}

/**
 * 处理编辑
 */
const handleEdit = (data: any) => {
  emit('edit', data)
}

/**
 * 处理删除
 */
const handleDelete = async (data: any) => {
  try {
    const confirmText = data.type === 'instruction_set' 
      ? `确定要删除指令集 "${data.name}" 吗？这将同时删除其所有节点。`
      : `确定要删除节点 "${data.title}" 吗？`
    
    await ElMessageBox.confirm(confirmText, '确认删除', {
      type: 'warning'
    })
    
    if (data.type === 'instruction_set') {
      await instructionSetApi.deleteInstructionSet(data.id)
    } else {
      await instructionNodeApi.deleteInstructionNode(data.id)
    }
    
    ElMessage.success('删除成功')
    await loadTreeData()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

// 监听搜索文本变化
watch(searchText, (val) => {
  treeRef.value?.filter(val)
})

// 监听刷新触发器
watch(() => props.refreshTrigger, () => {
  loadTreeData()
})

// 组件挂载时加载数据
onMounted(() => {
  loadTreeData()
})

// 暴露方法
defineExpose({
  refresh: loadTreeData
})
</script>

<style scoped>
.instruction-set-tree {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.tree-toolbar {
  padding: 16px;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  align-items: center;
  gap: 8px;
}

.instruction-tree {
  flex: 1;
  padding: 16px;
  overflow: auto;
}

.tree-node {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding: 4px 8px;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.tree-node:hover {
  background-color: #f5f7fa;
}

.node-content {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
}

.node-icon {
  font-size: 16px;
}

.instruction-set-icon {
  color: #409eff;
}

.instruction-node-icon {
  color: #67c23a;
}

.node-info {
  flex: 1;
  min-width: 0;
}

.node-title {
  font-weight: 500;
  color: #303133;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.node-description {
  font-size: 12px;
  color: #909399;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-top: 2px;
}

.node-status,
.node-type {
  margin-left: 8px;
}

.node-actions {
  display: flex;
  gap: 4px;
  opacity: 0;
  transition: opacity 0.2s;
}

.tree-node:hover .node-actions {
  opacity: 1;
}

.delete-btn {
  color: #f56c6c;
}

.delete-btn:hover {
  color: #f56c6c;
  background-color: #fef0f0;
}

:deep(.el-tree-node__content) {
  height: auto;
  min-height: 40px;
  padding: 4px 0;
}

:deep(.el-tree-node__expand-icon) {
  color: #c0c4cc;
}

:deep(.el-tree-node__expand-icon.expanded) {
  color: #409eff;
}
</style>