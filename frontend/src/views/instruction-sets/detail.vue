<template>
  <div class="instruction-set-detail">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <el-button @click="handleBack" class="back-btn">
          <el-icon><ArrowLeft /></el-icon>
          返回
        </el-button>
        <div class="header-info">
          <h1 class="page-title">
            {{ instructionSet?.name || '加载中...' }}
            <el-tag v-if="instructionSet?.version" type="info" size="small">
              v{{ instructionSet.version }}
            </el-tag>
          </h1>
          <p class="page-description">{{ instructionSet?.description }}</p>
        </div>
      </div>
      <div class="header-actions">
        <PermissionButton 
          permission="instruction_set:update"
          @click="handleEdit"
        >
          <el-icon><Edit /></el-icon>
          编辑
        </PermissionButton>
        <PermissionButton 
          permission="instruction_set:test"
          type="primary" 
          @click="handleTest"
        >
          <el-icon><VideoPlay /></el-icon>
          测试
        </PermissionButton>
        <el-dropdown @command="handleDropdownCommand">
          <el-button>
            更多<el-icon class="el-icon--right"><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <PermissionWrapper permission="instruction_set:create">
                <el-dropdown-item command="copy">
                  <el-icon><CopyDocument /></el-icon>
                  复制
                </el-dropdown-item>
              </PermissionWrapper>
              <PermissionWrapper permission="instruction_set:read">
                <el-dropdown-item command="statistics">
                  <el-icon><DataAnalysis /></el-icon>
                  统计
                </el-dropdown-item>
              </PermissionWrapper>
              <PermissionWrapper permission="instruction_set:read">
                <el-dropdown-item command="export">
                  <el-icon><Download /></el-icon>
                  导出
                </el-dropdown-item>
              </PermissionWrapper>
              <PermissionWrapper permission="instruction_set:delete">
                <el-dropdown-item command="delete" divided>
                  <el-icon><Delete /></el-icon>
                  删除
                </el-dropdown-item>
              </PermissionWrapper>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <!-- 基本信息卡片 -->
    <el-row :gutter="20" class="info-section">
      <el-col :span="16">
        <el-card class="info-card">
          <template #header>
            <div class="card-header">
              <span>基本信息</span>
              <el-tag :type="getStatusType(instructionSet?.status)">{{ getStatusText(instructionSet?.status) }}</el-tag>
            </div>
          </template>
          <div v-loading="loading" class="info-content">
            <el-descriptions :column="2" border>
              <el-descriptions-item label="ID">{{ instructionSet?.id }}</el-descriptions-item>
              <el-descriptions-item label="名称">{{ instructionSet?.name }}</el-descriptions-item>
              <el-descriptions-item label="版本">{{ instructionSet?.version }}</el-descriptions-item>
              <el-descriptions-item label="状态">
                <el-tag :type="getStatusType(instructionSet?.status)">{{ getStatusText(instructionSet?.status) }}</el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="创建者">{{ instructionSet?.created_by_name || instructionSet?.created_by }}</el-descriptions-item>
              <el-descriptions-item label="创建时间">{{ formatDate(instructionSet?.created_at) }}</el-descriptions-item>
              <el-descriptions-item label="更新时间">{{ formatDate(instructionSet?.updated_at) }}</el-descriptions-item>
              <el-descriptions-item label="节点数量">{{ instructionSet?.node_count || 0 }}</el-descriptions-item>
              <el-descriptions-item label="描述" :span="2">{{ instructionSet?.description }}</el-descriptions-item>
            </el-descriptions>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="stats-card">
          <template #header>
            <span>执行统计</span>
          </template>
          <div v-loading="statsLoading" class="stats-content">
            <div class="stat-item">
              <div class="stat-number">{{ statistics?.total_executions || 0 }}</div>
              <div class="stat-label">总执行次数</div>
            </div>
            <div class="stat-item">
              <div class="stat-number">{{ statistics?.success_executions || 0 }}</div>
              <div class="stat-label">成功次数</div>
            </div>
            <div class="stat-item">
              <div class="stat-number">{{ (statistics?.average_execution_time || 0).toFixed(2) }}ms</div>
              <div class="stat-label">平均执行时间</div>
            </div>
            <div class="stat-item">
              <div class="stat-number">{{ ((statistics?.success_executions || 0) / Math.max(statistics?.total_executions || 1, 1) * 100).toFixed(1) }}%</div>
              <div class="stat-label">成功率</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 指令树结构 -->
    <el-card class="tree-card">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <span>指令树结构</span>
            <el-radio-group v-model="viewMode" size="small" class="view-mode-switch">
              <el-radio-button value="tree">树形视图</el-radio-button>
                <el-radio-button value="mindmap">思维导图</el-radio-button>
            </el-radio-group>
          </div>
          <div class="tree-actions">
            <el-button size="small" @click="handleAddNode">
              <el-icon><Plus /></el-icon>
              添加节点
            </el-button>
            <el-button size="small" @click="handleRefreshTree">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
          </div>
        </div>
      </template>
      <div v-loading="treeLoading" class="tree-content">
        <!-- 树形视图 -->
        <InstructionTree
          v-if="viewMode === 'tree' && instructionSet"
          ref="instructionTreeRef"
          :instruction-set-id="instructionSet.id"
          :tree-data="treeData"
          :loading="treeLoading"
          @node-click="handleNodeClick"
          @node-add="handleNodeAdd"
          @node-edit="handleNodeEdit"
          @node-delete="handleNodeDelete"
          @node-move="handleNodeMove"
          @tree-change="handleTreeChange"
        />
        
        <!-- 思维导图视图 -->
        <MindMapView
          v-if="viewMode === 'mindmap' && instructionSet"
          ref="mindMapRef"
          :instruction-set-id="instructionSet.id"
          :tree-data="treeData"
          :loading="treeLoading"
          @node-click="handleNodeClick"
          @node-add="handleNodeAdd"
          @node-edit="handleNodeEdit"
          @node-delete="handleNodeDelete"
          @node-move="handleNodeMove"
          @tree-change="handleTreeChange"
        />
      </div>
    </el-card>

    <!-- 编辑对话框 -->
    <el-dialog
      v-model="editDialogVisible"
      title="编辑指令集"
      width="600px"
      @close="handleEditDialogClose"
    >
      <el-form
        ref="editFormRef"
        :model="editFormData"
        :rules="editFormRules"
        label-width="100px"
      >
        <el-form-item label="名称" prop="name">
          <el-input v-model="editFormData.name" placeholder="请输入指令集名称" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="editFormData.description"
            type="textarea"
            :rows="3"
            placeholder="请输入指令集描述"
          />
        </el-form-item>
        <el-form-item label="版本" prop="version">
          <el-input v-model="editFormData.version" placeholder="例如：1.0.0" />
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-select v-model="editFormData.status" placeholder="选择状态" style="width: 100%">
            <el-option label="草稿" value="draft" />
            <el-option label="活跃" value="active" />
            <el-option label="已归档" value="archived" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="editDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleEditSubmit" :loading="editSubmitting">
            更新
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 节点配置对话框 -->
    <NodeConfigModal
      v-model="nodeConfigVisible"
      :node="currentEditNode"
      :instruction-set-id="instructionSetId"
      @submit="handleNodeConfigSubmit"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ArrowLeft,
  Edit,
  VideoPlay,
  ArrowDown,
  CopyDocument,
  DataAnalysis,
  Download,
  Delete,
  Plus,
  Refresh
} from '@element-plus/icons-vue'
import { instructionSetApi, instructionNodeApi } from '@/api/instruction-set'
import InstructionTree from '@/components/InstructionTree/index.vue'
import MindMapView from '@/components/MindMapView.vue'
import NodeConfigModal from '@/components/InstructionTree/NodeConfigModal.vue'
import type {
  InstructionSet,
  InstructionSetUpdate,
  InstructionTreeNode,
  InstructionSetStatistics
} from '@/types/instruction-set'
import { PermissionButton, PermissionWrapper } from '@/components/Permission'

const route = useRoute()
const router = useRouter()

// 响应式数据
const loading = ref(false)
const treeLoading = ref(false)
const statsLoading = ref(false)
const editSubmitting = ref(false)
const editDialogVisible = ref(false)
const nodeConfigVisible = ref(false)
const currentEditNode = ref<InstructionTreeNode | null>(null)
const instructionSet = ref<InstructionSet | null>(null)
const treeData = ref<InstructionTreeNode[]>([])
const statistics = ref<InstructionSetStatistics | null>(null)
const instructionTreeRef = ref()
const mindMapRef = ref()

// 编辑表单数据
const editFormData = reactive<InstructionSetUpdate & { id?: number }>({
  name: '',
  description: '',
  version: '',
  status: 'draft'
})

// 编辑表单验证规则
const editFormRules = {
  name: [
    { required: true, message: '请输入指令集名称', trigger: 'blur' },
    { min: 2, max: 100, message: '名称长度在 2 到 100 个字符', trigger: 'blur' }
  ],
  description: [
    { required: true, message: '请输入指令集描述', trigger: 'blur' },
    { max: 500, message: '描述不能超过 500 个字符', trigger: 'blur' }
  ],
  version: [
    { required: true, message: '请输入版本号', trigger: 'blur' }
  ],
  status: [
    { required: true, message: '请选择状态', trigger: 'change' }
  ]
}

const editFormRef = ref()
const viewMode = ref('tree')

// 计算属性
const instructionSetId = computed(() => {
  return parseInt(route.params.id as string)
})

/**
 * 获取状态类型
 */
const getStatusType = (status?: string) => {
  const typeMap: Record<string, string> = {
    draft: 'info',
    active: 'success',
    archived: 'warning'
  }
  return typeMap[status || ''] || 'info'
}

/**
 * 获取状态文本
 */
const getStatusText = (status?: string) => {
  const textMap: Record<string, string> = {
    draft: '草稿',
    active: '活跃',
    archived: '已归档'
  }
  return textMap[status || ''] || status || ''
}

/**
 * 格式化日期
 */
const formatDate = (date?: string) => {
  return date ? new Date(date).toLocaleString('zh-CN') : '-'
}

/**
 * 加载指令集详情
 */
const loadInstructionSet = async () => {
  try {
    loading.value = true
    const response = await instructionSetApi.getInstructionSet(instructionSetId.value)
    // 后端直接返回InstructionSet对象，不是ApiResponse格式
    console.log('加载指令集详情:', response)
    instructionSet.value = response.data
  } catch (error) {
    console.error('加载指令集详情失败:', error)
    ElMessage.error('加载指令集详情失败')
  } finally {
    loading.value = false
  }
}

/**
 * 加载指令树
 */
const loadInstructionTree = async () => {
  try {
    treeLoading.value = true
    const response = await instructionNodeApi.getInstructionTree(instructionSetId.value)
    // 后端直接返回数组，不是包装在ApiResponse中
    if (Array.isArray(response)) {
      treeData.value = response
    } else if (response.success) {
      treeData.value = response.data
    } else {
      treeData.value = []
    }
  } catch (error) {
    console.error('加载指令树失败:', error)
    ElMessage.error('加载指令树失败')
    treeData.value = []
  } finally {
    treeLoading.value = false
  }
}

/**
 * 加载统计信息
 */
const loadStatistics = async () => {
  try {
    statsLoading.value = true
    const response = await instructionSetApi.getInstructionSetStatistics(instructionSetId.value)
    if (response) {
      statistics.value = response
    }
  } catch (error) {
    console.error('加载统计信息失败:', error)
    // 统计信息加载失败不显示错误，因为不是核心功能
  } finally {
    statsLoading.value = false
  }
}

/**
 * 返回上一页
 */
const handleBack = () => {
  router.back()
}

/**
 * 编辑指令集
 */
const handleEdit = () => {
  if (!instructionSet.value) return
  
  Object.assign(editFormData, {
    id: instructionSet.value.id,
    name: instructionSet.value.name,
    description: instructionSet.value.description,
    version: instructionSet.value.version,
    status: instructionSet.value.status
  })
  editDialogVisible.value = true
}

/**
 * 测试指令集
 */
const handleTest = () => {
  router.push(`/instruction-sets/${instructionSetId.value}/test`)
}

/**
 * 下拉菜单命令处理
 */
const handleDropdownCommand = async (command: string) => {
  switch (command) {
    case 'copy':
      await handleCopy()
      break
    case 'statistics':
      router.push(`/instruction-sets/${instructionSetId.value}/statistics`)
      break
    case 'export':
      await handleExport()
      break
    case 'delete':
      await handleDelete()
      break
  }
}

/**
 * 复制指令集
 */
const handleCopy = async () => {
  if (!instructionSet.value) return
  
  try {
    const copyData = {
      name: `${instructionSet.value.name} - 副本`,
      description: instructionSet.value.description,
      version: '1.0.0',
      status: 'draft' as const
    }
    
    const response = await instructionSetApi.createInstructionSet(copyData)
    if (response.success) {
      ElMessage.success('复制成功')
      router.push(`/instruction-sets/${response.data.id}`)
    }
  } catch (error) {
    console.error('复制失败:', error)
    ElMessage.error('复制失败')
  }
}

/**
 * 导出指令集
 */
const handleExport = async () => {
  try {
    // 这里实现导出逻辑
    ElMessage.info('导出功能开发中')
  } catch (error) {
    console.error('导出失败:', error)
    ElMessage.error('导出失败')
  }
}

/**
 * 删除指令集
 */
const handleDelete = async () => {
  if (!instructionSet.value) return
  
  try {
    await ElMessageBox.confirm(
      `确定要删除指令集 "${instructionSet.value.name}" 吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const response = await instructionSetApi.deleteInstructionSet(instructionSet.value.id)
    if (response.success) {
      ElMessage.success('删除成功')
      router.push('/instruction-sets')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

/**
 * 添加节点
 */
/**
 * 添加节点处理
 */
const handleAddNode = async () => {
  // 等待下一个tick确保组件已经渲染
  await nextTick()
  
  if (viewMode.value === 'tree') {
    if (instructionTreeRef.value && typeof instructionTreeRef.value.handleAddRootNode === 'function') {
      instructionTreeRef.value.handleAddRootNode()
    } else {
      ElMessage.info('组件正在加载中，请稍后再试')
    }
  } else if (viewMode.value === 'mindmap') {
    if (mindMapRef.value && typeof mindMapRef.value.handleAddRootNode === 'function') {
      mindMapRef.value.handleAddRootNode()
    } else {
      ElMessage.info('组件正在加载中，请稍后再试')
    }
  }
}

/**
 * 刷新树结构
 */
const handleRefreshTree = () => {
  loadInstructionTree()
}

/**
 * 节点点击处理
 */
const handleNodeClick = (node: InstructionTreeNode) => {
  console.log('节点点击:', node)
}

/**
 * 节点添加处理
 */
const handleNodeAdd = (parentNode?: InstructionTreeNode) => {
  currentEditNode.value = parentNode || null
  nodeConfigVisible.value = true
}

/**
 * 节点编辑处理
 */
const handleNodeEdit = (node: InstructionTreeNode) => {
  currentEditNode.value = node
  nodeConfigVisible.value = true
}

/**
 * 节点删除处理
 */
const handleNodeDelete = (node: InstructionTreeNode) => {
  console.log('删除节点:', node)
  // 这里实现删除节点的逻辑
}

/**
 * 节点移动处理
 */
const handleNodeMove = (node: InstructionTreeNode, newParent: InstructionTreeNode | null, newIndex: number) => {
  console.log('移动节点:', node, newParent, newIndex)
  // 这里实现移动节点的逻辑
}

/**
 * 树结构变化处理
 */
const handleTreeChange = () => {
  // 树结构发生变化时，重新加载相关数据
  loadInstructionTree()
  loadInstructionSet()
  loadStatistics()
}

/**
 * 节点配置提交处理
 */
const handleNodeConfigSubmit = () => {
  nodeConfigVisible.value = false
  currentEditNode.value = null
  handleTreeChange()
}

/**
 * 编辑提交
 */
const handleEditSubmit = async () => {
  try {
    await editFormRef.value?.validate()
    editSubmitting.value = true
    
    if (editFormData.id) {
      const updateData: InstructionSetUpdate = {
        name: editFormData.name,
        description: editFormData.description,
        version: editFormData.version,
        status: editFormData.status
      }
      const response = await instructionSetApi.updateInstructionSet(editFormData.id, updateData)
      if (response.success) {
        ElMessage.success('更新成功')
        editDialogVisible.value = false
        loadInstructionSet()
      }
    }
  } catch (error) {
    console.error('更新失败:', error)
    ElMessage.error('更新失败')
  } finally {
    editSubmitting.value = false
  }
}

/**
 * 编辑对话框关闭处理
 */
const handleEditDialogClose = () => {
  editFormRef.value?.resetFields()
}

// 组件挂载时加载数据
onMounted(() => {
  loadInstructionSet()
  loadInstructionTree()
  loadStatistics()
})
</script>

<style scoped>
.instruction-set-detail {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
}

.header-left {
  display: flex;
  align-items: flex-start;
  gap: 16px;
}

.back-btn {
  margin-top: 4px;
}

.header-info {
  flex: 1;
}

.page-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 8px 0;
  font-size: 24px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.page-description {
  margin: 0;
  color: var(--el-text-color-regular);
  font-size: 14px;
}

.header-actions {
  display: flex;
  gap: 8px;
  margin-left: 20px;
}

.info-section {
  margin-bottom: 20px;
}

.info-card,
.stats-card,
.tree-card {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.view-mode-switch {
  margin-left: 16px;
}

.tree-actions {
  display: flex;
  gap: 8px;
}

.info-content {
  min-height: 200px;
}

.stats-content {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.stat-item {
  text-align: center;
  padding: 16px;
  background: var(--el-fill-color-lighter);
  border-radius: 8px;
}

.stat-number {
  font-size: 24px;
  font-weight: 600;
  color: var(--el-color-primary);
  line-height: 1;
}

.stat-label {
  font-size: 12px;
  color: var(--el-text-color-regular);
  margin-top: 4px;
}

.tree-content {
  min-height: 400px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    gap: 16px;
  }
  
  .header-left {
    flex-direction: column;
    gap: 8px;
  }
  
  .header-actions {
    margin-left: 0;
    align-self: stretch;
  }
  
  .info-section .el-col {
    margin-bottom: 16px;
  }
  
  .stats-content {
    grid-template-columns: 1fr;
  }
}
</style>