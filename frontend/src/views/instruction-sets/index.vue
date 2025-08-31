<template>
  <div class="instruction-sets-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">
          <el-icon><Setting /></el-icon>
          指令集管理
        </h1>
        <p class="page-description">管理和维护树状结构的指令集，用于内容审核和自动化处理</p>
      </div>
      <div class="header-actions">
        <el-button type="primary" @click="handleCreate">
          <el-icon><Plus /></el-icon>
          创建指令集
        </el-button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-cards">
      <el-row :gutter="20">
        <el-col :span="6">
          <el-card class="stats-card">
            <div class="stats-content">
              <div class="stats-icon total">
                <el-icon><Document /></el-icon>
              </div>
              <div class="stats-info">
                <div class="stats-number">{{ statistics.total }}</div>
                <div class="stats-label">总指令集</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stats-card">
            <div class="stats-content">
              <div class="stats-icon active">
                <el-icon><CircleCheck /></el-icon>
              </div>
              <div class="stats-info">
                <div class="stats-number">{{ statistics.active }}</div>
                <div class="stats-label">活跃指令集</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stats-card">
            <div class="stats-content">
              <div class="stats-icon draft">
                <el-icon><Edit /></el-icon>
              </div>
              <div class="stats-info">
                <div class="stats-number">{{ statistics.draft }}</div>
                <div class="stats-label">草稿状态</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stats-card">
            <div class="stats-content">
              <div class="stats-icon executions">
                <el-icon><DataAnalysis /></el-icon>
              </div>
              <div class="stats-info">
                <div class="stats-number">{{ statistics.executions }}</div>
                <div class="stats-label">总执行次数</div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 搜索和筛选 -->
    <el-card class="filter-card">
      <el-form :model="queryParams" inline>
        <el-form-item label="搜索">
          <el-input
            v-model="queryParams.search"
            placeholder="搜索指令集名称或描述"
            clearable
            style="width: 300px"
            @keyup.enter="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="queryParams.status" placeholder="选择状态" clearable style="width: 150px">
            <el-option label="草稿" :value="InstructionSetStatus.DRAFT" />
            <el-option label="活跃" :value="InstructionSetStatus.ACTIVE" />
            <el-option label="未激活" :value="InstructionSetStatus.INACTIVE" />
          </el-select>
        </el-form-item>
        <el-form-item label="创建者">
          <el-select v-model="queryParams.created_by" placeholder="选择创建者" clearable style="width: 150px">
            <el-option
              v-for="user in users"
              :key="user.id"
              :label="user.username"
              :value="user.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">
            <el-icon><Search /></el-icon>
            搜索
          </el-button>
          <el-button @click="handleReset">
            <el-icon><Refresh /></el-icon>
            重置
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 指令集列表 -->
    <el-card class="table-card">
      <template #header>
        <div class="table-header">
          <span>指令集列表</span>
          <div class="table-actions">
            <!-- 视图切换 -->
            <el-radio-group v-model="viewMode" size="small" @change="handleViewModeChange">
              <el-radio-button value="grid">
                <el-icon><Grid /></el-icon>
              </el-radio-button>
              <el-radio-button value="list">
                <el-icon><List /></el-icon>
              </el-radio-button>
            </el-radio-group>
            <el-button size="small" @click="handleRefresh">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
          </div>
        </div>
      </template>

      <!-- 网格视图 -->
      <div v-if="viewMode === 'grid'" class="grid-view">
        <div class="instruction-sets-grid">
          <div
            v-for="instructionSet in instructionSets"
            :key="instructionSet.id"
            class="instruction-set-card"
            @click="handleViewDetail(instructionSet)"
          >
            <div class="instruction-set-header">
              <div class="instruction-set-info">
                <div class="instruction-set-name">{{ instructionSet.name }}</div>
                <div class="instruction-set-version" v-if="instructionSet.version">v{{ instructionSet.version }}</div>
              </div>
              <div class="instruction-set-status" :class="instructionSet.status">
                <el-tag :type="getStatusType(instructionSet.status)">{{ getStatusText(instructionSet.status) }}</el-tag>
              </div>
            </div>
            
            <div class="instruction-set-description">
              {{ instructionSet.description || '暂无描述' }}
            </div>
            
            <div class="instruction-set-details">
              <div class="detail-item">
                <span class="label">节点数:</span>
                <span class="value">{{ instructionSet.node_count || 0 }}</span>
              </div>
              <div class="detail-item">
                <span class="label">执行次数:</span>
                <span class="value">{{ instructionSet.execution_count || 0 }}</span>
              </div>
              <div class="detail-item">
                <span class="label">创建时间:</span>
                <span class="value">{{ formatDate(instructionSet.created_at) }}</span>
              </div>
            </div>
            
            <div class="instruction-set-actions" @click.stop>
              <el-button size="small" @click="handleViewDetail(instructionSet)">
                <el-icon><View /></el-icon>
                详情
              </el-button>
              <el-button size="small" type="primary" @click="handleEdit(instructionSet)">
                <el-icon><Edit /></el-icon>
                编辑
              </el-button>
              <el-dropdown @command="(command) => handleDropdownCommand(command, instructionSet)">
                <el-button size="small">
                  <el-icon><ArrowDown /></el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="test">
                      <el-icon><VideoPlay /></el-icon>
                      测试
                    </el-dropdown-item>
                    <el-dropdown-item command="copy">
                      <el-icon><CopyDocument /></el-icon>
                      复制
                    </el-dropdown-item>
                    <el-dropdown-item command="statistics">
                      <el-icon><DataAnalysis /></el-icon>
                      统计
                    </el-dropdown-item>
                    <el-dropdown-item command="export">
                      <el-icon><Download /></el-icon>
                      导出
                    </el-dropdown-item>
                    <el-dropdown-item command="delete" divided>
                      <el-icon><Delete /></el-icon>
                      删除
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </div>
        </div>

        <!-- 分页 -->
        <div class="pagination-container">
          <el-pagination
            v-model:current-page="queryParams.page"
            v-model:page-size="queryParams.size"
            :total="total"
            :page-sizes="[10, 20, 50, 100]"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="handleSizeChange"
            @current-change="handleCurrentChange"
          />
        </div>
      </div>

      <!-- 列表视图 -->
      <div v-else class="list-view">
        <el-table
          v-loading="loading"
          :data="instructionSets"
          style="width: 100%"
        >
          <el-table-column prop="name" label="指令集名称" sortable>
            <template #default="{ row }">
              <div class="instruction-set-name-cell">
                <div class="instruction-set-info">
                  <div class="name">{{ row.name }}</div>
                  <div class="version" v-if="row.version">v{{ row.version }}</div>
                </div>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="description" label="描述" min-width="300" show-overflow-tooltip />
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="getStatusType(row.status)">{{ getStatusText(row.status) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="node_count" label="节点数" width="100" />
          <el-table-column prop="execution_count" label="执行次数" width="120" />
          <el-table-column prop="created_at" label="创建时间" width="180">
            <template #default="{ row }">
              {{ formatDate(row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="300" fixed="right">
            <template #default="{ row }">
              <el-button size="small" @click="handleViewDetail(row)">
                <el-icon><View /></el-icon>
                详情
              </el-button>
              <el-button size="small" type="primary" @click="handleEdit(row)">
                <el-icon><Edit /></el-icon>
                编辑
              </el-button>
              <el-button size="small" type="success" @click="handleTest(row)">
                <el-icon><VideoPlay /></el-icon>
                测试
              </el-button>
              <el-dropdown @command="(command) => handleDropdownCommand(command, row)">
                <el-button size="small">
                  更多<el-icon class="el-icon--right"><ArrowDown /></el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="copy">
                      <el-icon><CopyDocument /></el-icon>
                      复制
                    </el-dropdown-item>
                    <el-dropdown-item command="statistics">
                      <el-icon><DataAnalysis /></el-icon>
                      统计
                    </el-dropdown-item>
                    <el-dropdown-item command="export">
                      <el-icon><Download /></el-icon>
                      导出
                    </el-dropdown-item>
                    <el-dropdown-item command="delete" divided>
                      <el-icon><Delete /></el-icon>
                      删除
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </template>
          </el-table-column>
        </el-table>
         
         <!-- 分页 -->
         <div class="pagination-container">
           <el-pagination
             v-model:current-page="currentPage"
             v-model:page-size="pageSize"
             :page-sizes="[10, 20, 50, 100]"
             :total="total"
             layout="total, sizes, prev, pager, next, jumper"
             @size-change="handleSizeChange"
             @current-change="handleCurrentChange"
           />
         </div>
        </div>
      </el-card>

    <!-- 创建/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="600px"
      @close="handleDialogClose"
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="100px"
      >
        <el-form-item label="名称" prop="name">
          <el-input v-model="formData.name" placeholder="请输入指令集名称" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="formData.description"
            type="textarea"
            :rows="3"
            placeholder="请输入指令集描述"
          />
        </el-form-item>
        <el-form-item label="版本" prop="version">
          <el-input v-model="formData.version" placeholder="例如：1.0.0" />
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-select v-model="formData.status" placeholder="选择状态" style="width: 100%">
            <el-option label="草稿" :value="InstructionSetStatus.DRAFT" />
            <el-option label="活跃" :value="InstructionSetStatus.ACTIVE" />
            <el-option label="未激活" :value="InstructionSetStatus.INACTIVE" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleSubmit" :loading="submitting">
            {{ isEdit ? '更新' : '创建' }}
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Setting,
  Plus,
  Document,
  CircleCheck,
  Edit,
  DataAnalysis,
  Search,
  Refresh,
  View,
  VideoPlay,
  ArrowDown,
  CopyDocument,
  Download,
  Delete,
  Grid,
  List
} from '@element-plus/icons-vue'
import { instructionSetApi } from '@/api/instruction-set'
import type { InstructionSet, InstructionSetCreate, InstructionSetUpdate, InstructionNode } from '@/types/instruction-set'
import { InstructionSetStatus } from '@/types/instruction-set'


const router = useRouter()

// 响应式数据
const loading = ref(false)
const submitting = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const instructionSets = ref<InstructionSet[]>([])

const users = ref<any[]>([])
const total = ref(0)
const viewMode = ref('grid')

// 统计数据
const statistics = reactive({
  total: 0,
  active: 0,
  draft: 0,
  executions: 0
})

// 查询参数
const queryParams = reactive({
  page: 1,
  size: 20,
  search: '',
  status: '',
  created_by: null as number | null
})

// 表单数据
const formData = reactive<InstructionSetCreate & { id?: number }>({
  name: '',
  description: '',
  version: '1.0.0',
  status: InstructionSetStatus.DRAFT
})

// 表单验证规则
const formRules = {
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

const formRef = ref()

// 计算属性
const dialogTitle = computed(() => isEdit.value ? '编辑指令集' : '创建指令集')

/**
 * 获取状态类型
 */
const getStatusType = (status: string) => {
  const typeMap: Record<string, string> = {
    DRAFT: 'info',
    ACTIVE: 'success',
    INACTIVE: 'warning',
    ARCHIVED: 'danger'
  }
  return typeMap[status] || 'info'
}

/**
 * 获取状态文本
 */
const getStatusText = (status: string) => {
  const textMap: Record<string, string> = {
    DRAFT: '草稿',
    ACTIVE: '活跃',
    INACTIVE: '未激活',
    ARCHIVED: '已归档'
  }
  return textMap[status] || status
}

/**
 * 格式化日期
 */
const formatDate = (date: string) => {
  return new Date(date).toLocaleString('zh-CN')
}

/**
 * 加载指令集列表
 */
const loadInstructionSets = async () => {
  try {
    loading.value = true
    const params = {
      skip: (queryParams.page - 1) * queryParams.size,
      limit: queryParams.size,
      search: queryParams.search || undefined,
      status: queryParams.status || undefined,
      created_by: queryParams.created_by || undefined
    }
    
    const response = await instructionSetApi.getInstructionSets(params)
    console.log("==================")
    console.log(response)
    if (response.success) {
      instructionSets.value = response.data
      total.value = response.total
      
      // 更新统计数据
      updateStatistics()
    }
  } catch (error) {
    console.error('加载指令集列表失败:', error)
    ElMessage.error('加载指令集列表失败')
  } finally {
    loading.value = false
  }
}

/**
 * 更新统计数据
 */
const updateStatistics = () => {
  statistics.total = instructionSets.value.length
  statistics.active = instructionSets.value.filter(item => item.status === InstructionSetStatus.ACTIVE).length
  statistics.draft = instructionSets.value.filter(item => item.status === InstructionSetStatus.DRAFT).length
  statistics.executions = instructionSets.value.reduce((sum, item) => sum + (item.execution_count || 0), 0)
}

/**
 * 搜索
 */
const handleSearch = () => {
  queryParams.page = 1
  loadInstructionSets()
}

/**
 * 重置搜索
 */
const handleReset = () => {
  queryParams.search = ''
  queryParams.status = ''
  queryParams.created_by = null
  queryParams.page = 1
  loadInstructionSets()
}

/**
 * 刷新
 */
const handleRefresh = () => {
  loadInstructionSets()
}

/**
 * 分页大小改变
 */
const handleSizeChange = (size: number) => {
  queryParams.size = size
  queryParams.page = 1
  loadInstructionSets()
}

/**
 * 当前页改变
 */
const handleCurrentChange = (page: number) => {
  queryParams.page = page
  loadInstructionSets()
}

/**
 * 创建指令集
 */
const handleCreate = () => {
  isEdit.value = false
  Object.assign(formData, {
    name: '',
    description: '',
    version: '1.0.0',
    status: InstructionSetStatus.DRAFT
  })
  dialogVisible.value = true
}

/**
 * 编辑指令集
 */
const handleEdit = (row: InstructionSet) => {
  isEdit.value = true
  Object.assign(formData, {
    id: row.id,
    name: row.name,
    description: row.description,
    version: row.version,
    status: row.status
  })
  dialogVisible.value = true
}

/**
 * 查看详情
 */
const handleViewDetail = (row: InstructionSet) => {
  router.push(`/instruction-sets/${row.id}`)
}

/**
 * 测试指令集
 */
const handleTest = (row: InstructionSet) => {
  router.push(`/instruction-sets/${row.id}/test`)
}

/**
 * 下拉菜单命令处理
 */
const handleDropdownCommand = async (command: string, row: InstructionSet) => {
  switch (command) {
    case 'copy':
      await handleCopy(row)
      break
    case 'statistics':
      router.push(`/instruction-sets/${row.id}/statistics`)
      break
    case 'export':
      await handleExport(row)
      break
    case 'delete':
      await handleDelete(row)
      break
  }
}

/**
 * 复制指令集
 */
const handleCopy = async (row: InstructionSet) => {
  try {
    const copyData: InstructionSetCreate = {
      name: `${row.name} - 副本`,
      description: row.description,
      version: '1.0.0',
      status: InstructionSetStatus.DRAFT
    }
    
    const response = await instructionSetApi.createInstructionSet(copyData)
    if (response.success) {
      ElMessage.success('复制成功')
      loadInstructionSets()
    }
  } catch (error) {
    console.error('复制失败:', error)
    ElMessage.error('复制失败')
  }
}

/**
 * 导出指令集
 */
const handleExport = async (row: InstructionSet) => {
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
const handleDelete = async (row: InstructionSet) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除指令集 "${row.name}" 吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const response = await instructionSetApi.deleteInstructionSet(row.id)
    if (response.success) {
      ElMessage.success('删除成功')
      loadInstructionSets()
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

/**
 * 提交表单
 */
const handleSubmit = async () => {
  try {
    await formRef.value?.validate()
    submitting.value = true
    
    if (isEdit.value && formData.id) {
      const updateData: InstructionSetUpdate = {
        name: formData.name,
        description: formData.description,
        version: formData.version,
        status: formData.status
      }
      const response = await instructionSetApi.updateInstructionSet(formData.id, updateData)
      if (response.success) {
        ElMessage.success('更新成功')
        dialogVisible.value = false
        loadInstructionSets()
      }
    } else {
      const createData: InstructionSetCreate = {
        name: formData.name,
        description: formData.description,
        version: formData.version,
        status: formData.status
      }
      const response = await instructionSetApi.createInstructionSet(createData)
      if (response.success) {
        ElMessage.success('创建成功')
        dialogVisible.value = false
        loadInstructionSets()
      }
    }
  } catch (error) {
    console.error('提交失败:', error)
    ElMessage.error('提交失败')
  } finally {
    submitting.value = false
  }
}

/**
 * 对话框关闭处理
 */
const handleDialogClose = () => {
  formRef.value?.resetFields()
}

/**
 * 加载树形数据
 */


/**
 * 视图模式切换处理
 */
const handleViewModeChange = (mode: string) => {
  viewMode.value = mode
  loadInstructionSets()
}



// 组件挂载时加载数据
onMounted(() => {
  loadInstructionSets()
})
</script>

<style scoped>
.instruction-sets-container {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
}

.header-content {
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
  margin-left: 20px;
}

.stats-cards {
  margin-bottom: 20px;
}

.stats-card {
  border: none;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.stats-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stats-icon {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: white;
}

.stats-icon.total {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.stats-icon.active {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.stats-icon.draft {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.stats-icon.executions {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
}

.stats-info {
  flex: 1;
}

.stats-number {
  font-size: 24px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  line-height: 1;
}

.stats-label {
  font-size: 14px;
  color: var(--el-text-color-regular);
  margin-top: 4px;
}

.filter-card {
  margin-bottom: 20px;
}

.table-card {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.table-actions {
  display: flex;
  gap: 8px;
}

.name-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.name-text {
  font-weight: 500;
}

.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.tree-card {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.tree-container {
  min-height: 400px;
}

.tree-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 400px;
  color: var(--el-text-color-placeholder);
  font-size: 16px;
}

.view-switcher {
  margin-right: 16px;
}

/* 网格视图样式 */
.grid-view {
  padding: 0;
}

.instruction-sets-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
  margin-bottom: 20px;
}

.instruction-set-card {
  background: white;
  border: 1px solid var(--el-border-color-light);
  border-radius: 8px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.instruction-set-card:hover {
  border-color: var(--el-color-primary);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  transform: translateY(-2px);
}

.instruction-set-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.instruction-set-info {
  flex: 1;
}

.instruction-set-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  margin-bottom: 4px;
  line-height: 1.4;
}

.instruction-set-version {
  font-size: 12px;
  color: var(--el-text-color-regular);
  background: var(--el-fill-color-light);
  padding: 2px 6px;
  border-radius: 4px;
  display: inline-block;
}

.instruction-set-status {
  margin-left: 12px;
}

.instruction-set-description {
  color: var(--el-text-color-regular);
  font-size: 14px;
  line-height: 1.5;
  margin-bottom: 16px;
  min-height: 42px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.instruction-set-details {
  margin-bottom: 16px;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  font-size: 13px;
}

.detail-item:last-child {
  margin-bottom: 0;
}

.detail-item .label {
  color: var(--el-text-color-regular);
  font-weight: 500;
}

.detail-item .value {
  color: var(--el-text-color-primary);
  font-weight: 600;
}

.instruction-set-actions {
  display: flex;
  gap: 8px;
  padding-top: 12px;
  border-top: 1px solid var(--el-border-color-lighter);
}

.instruction-set-actions .el-button {
  flex: 1;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    gap: 16px;
  }
  
  .header-actions {
    margin-left: 0;
    align-self: stretch;
  }
  
  .stats-cards .el-col {
    margin-bottom: 16px;
  }
}
</style>