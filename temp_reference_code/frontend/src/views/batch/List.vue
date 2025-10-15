<template>
  <div class="batches-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-left">
          <h1 class="page-title">
            <el-icon><DataBoard /></el-icon>
            批次管理
          </h1>
          <p class="page-description">管理和监控数据批次处理任务</p>
        </div>
        <div class="header-right">
          <el-button type="primary" @click="showCreateDialog">
            <el-icon><Plus /></el-icon>
            创建批次
          </el-button>
          <el-button @click="loadBatches">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-section">
      <el-row :gutter="20">
        <el-col :xs="12" :sm="6">
          <div class="stat-card">
            <div class="stat-icon total">
              <el-icon><DataBoard /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ total }}</div>
              <div class="stat-label">总批次</div>
            </div>
          </div>
        </el-col>
        
        <el-col :xs="12" :sm="6">
          <div class="stat-card">
            <div class="stat-icon pending">
              <el-icon><Clock /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ getStatusCount('pending') }}</div>
              <div class="stat-label">待处理</div>
            </div>
          </div>
        </el-col>
        
        <el-col :xs="12" :sm="6">
          <div class="stat-card">
            <div class="stat-icon processing">
              <el-icon><Loading /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ getStatusCount('processing') }}</div>
              <div class="stat-label">处理中</div>
            </div>
          </div>
        </el-col>
        
        <el-col :xs="12" :sm="6">
          <div class="stat-card">
            <div class="stat-icon completed">
              <el-icon><CircleCheckFilled /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ getStatusCount('completed') }}</div>
              <div class="stat-label">已完成</div>
            </div>
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- 搜索和筛选 -->
    <div class="search-section">
      <el-row :gutter="20">
        <el-col :xs="24" :sm="12">
          <el-input
            v-model="searchQuery"
            placeholder="搜索批次名称或描述..."
            clearable
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-col>
        <el-col :xs="12" :sm="6">
          <el-select
            v-model="statusFilter"
            placeholder="筛选状态"
            clearable
          >
            <el-option label="待处理" value="pending" />
            <el-option label="处理中" value="processing" />
            <el-option label="已完成" value="completed" />
            <el-option label="失败" value="failed" />
          </el-select>
        </el-col>
      </el-row>
    </div>

    <!-- 批次列表 -->
    <div class="batches-section">
      <el-card shadow="never">
        <template #header>
          <div class="card-header">
            <span>批次列表</span>
            <div class="header-actions">
              <el-radio-group v-model="viewMode" size="small">
                <el-radio-button value="grid">
                  <el-icon><Grid /></el-icon>
                </el-radio-button>
                <el-radio-button value="list">
                  <el-icon><List /></el-icon>
                </el-radio-button>
              </el-radio-group>
            </div>
          </div>
        </template>
        
        <!-- 网格视图 -->
        <div v-if="viewMode === 'grid'" class="grid-view">
          <div class="batches-grid">
            <div
              v-for="batch in filteredBatches"
              :key="batch.id"
              class="batch-card"
              @click="viewBatchDetail(batch)"
            >
              <div class="batch-header">
                <div class="batch-info">
                  <div class="batch-name">{{ batch.batch_name || batch.name }}</div>
                  <div class="batch-id">ID: {{ batch.batch_id || batch.id }}</div>
                </div>
                <div class="batch-status" :class="batch.status">
                  <el-icon v-if="batch.status === 'completed'">
                    <CircleCheckFilled />
                  </el-icon>
                  <el-icon v-else-if="batch.status === 'processing'">
                    <Loading />
                  </el-icon>
                  <el-icon v-else>
                    <Clock />
                  </el-icon>
                  {{ getStatusText(batch.status) }}
                </div>
              </div>
              
              <div class="batch-details">
                <div class="detail-item">
                  <span class="label">描述:</span>
                  <span class="value">{{ batch.description || '无描述' }}</span>
                </div>
                <div class="detail-item">
                  <span class="label">进度:</span>
                  <span class="value">{{ batch.completed_count || 0 }}/{{ batch.total_count || 0 }}</span>
                </div>
                <div class="detail-item">
                  <span class="label">创建时间:</span>
                  <span class="value">{{ formatDate(batch.created_at) }}</span>
                </div>
              </div>
              
              <div class="batch-progress">
                <el-progress
                  :percentage="getProgress(batch)"
                  :status="getProgressStatus(batch.status)"
                  :stroke-width="6"
                />
              </div>
              
              <div class="batch-actions" @click.stop>
                <el-button
                  size="small"
                  @click="viewBatchDetail(batch)"
                >
                  <el-icon><View /></el-icon>
                  详情
                </el-button>
                <el-button
                  size="small"
                  type="primary"
                  @click="processBatch(batch)"
                  :disabled="batch.status === 'processing' || batch.status === 'completed'"
                >
                  <el-icon><VideoPlay /></el-icon>
                  处理
                </el-button>
                <el-button
                  size="small"
                  type="danger"
                  @click="deleteBatch(batch)"
                  :disabled="batch.status === 'processing'"
                >
                  <el-icon><Delete /></el-icon>
                  删除
                </el-button>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 列表视图 -->
        <div v-else class="list-view">
          <el-table
            :data="filteredBatches"
            style="width: 100%"
            v-loading="loading"
            :scroll-x="true"
          >
            <el-table-column prop="id" label="ID" width="80" />
            <el-table-column prop="batch_name" label="批次名称" width="200">
              <template #default="{ row }">
                <div class="batch-name-cell">
                  <div class="batch-info">
                    <div class="name">{{ row.batch_name || row.name }}</div>
                    <div class="id">ID: {{ row.batch_id || row.id }}</div>
                  </div>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="description" label="描述" width="250" show-overflow-tooltip />
            <el-table-column prop="status" label="状态" width="120">
              <template #default="{ row }">
                <el-tag :type="getStatusTagType(row.status)" size="small">
                  {{ getStatusText(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="total_count" label="总数据量" width="100" />
            <el-table-column prop="completed_count" label="已处理" width="100" />
            <el-table-column label="进度" width="150">
              <template #default="{ row }">
                <el-progress
                  :percentage="getProgress(row)"
                  :status="getProgressStatus(row.status)"
                  :stroke-width="8"
                />
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="创建时间" width="180">
              <template #default="{ row }">
                {{ formatDate(row.created_at) }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="200" fixed="right">
              <template #default="{ row }">
                <el-button size="small" @click="viewBatchDetail(row)">
                  <el-icon><View /></el-icon>
                  详情
                </el-button>
                <el-button
                  size="small"
                  type="primary"
                  @click="processBatch(row)"
                  :disabled="row.status === 'processing' || row.status === 'completed'"
                >
                  <el-icon><VideoPlay /></el-icon>
                  处理
                </el-button>
                <el-button
                  size="small"
                  type="danger"
                  @click="deleteBatch(row)"
                  :disabled="row.status === 'processing'"
                >
                  <el-icon><Delete /></el-icon>
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
        
        <!-- 分页 -->
        <div class="pagination-wrapper">
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
      </el-card>
    </div>
    
    <!-- 创建批次对话框 -->
    <el-dialog
      v-model="createDialogVisible"
      title="创建批次"
      width="600px"
      @close="resetCreateForm"
    >
      <el-form
        ref="createFormRef"
        :model="createForm"
        :rules="createRules"
        label-width="100px"
      >
        <el-form-item label="批次名称" prop="name">
          <el-input
            v-model="createForm.name"
            placeholder="请输入批次名称"
          />
        </el-form-item>
        
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="createForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入批次描述"
          />
        </el-form-item>
        
        <el-form-item label="处理配置" prop="config">
          <el-input
            v-model="createForm.config"
            type="textarea"
            :rows="5"
            placeholder="请输入JSON格式的处理配置"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="createDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="createBatch" :loading="creating">
            {{ creating ? '创建中...' : '创建' }}
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/utils/api'
import dayjs from 'dayjs'
import {
  Plus,
  Refresh,
  Search,
  DataBoard,
  Clock,
  Loading,
  CircleCheckFilled,
  View,
  VideoPlay,
  Delete,
  Grid,
  List
} from '@element-plus/icons-vue'

const router = useRouter()

// 响应式数据
const loading = ref(false)
const creating = ref(false)
const batches = ref([])
const searchQuery = ref('')
const statusFilter = ref('')
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const viewMode = ref('grid')

// 创建对话框
const createDialogVisible = ref(false)
const createFormRef = ref()

// 创建表单
const createForm = reactive({
  name: '',
  description: '',
  config: '{}'
})

// 表单验证规则
const createRules = {
  name: [
    { required: true, message: '请输入批次名称', trigger: 'blur' }
  ],
  description: [
    { required: true, message: '请输入批次描述', trigger: 'blur' }
  ],
  config: [
    { required: true, message: '请输入处理配置', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        try {
          JSON.parse(value)
          callback()
        } catch (error) {
          callback(new Error('请输入有效的JSON格式'))
        }
      },
      trigger: 'blur'
    }
  ]
}

// 计算属性
const filteredBatches = computed(() => {
  let result = batches.value
  
  // 按搜索关键词过滤
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(batch => 
      batch.name.toLowerCase().includes(query) ||
      batch.description.toLowerCase().includes(query)
    )
  }
  
  // 按状态过滤
  if (statusFilter.value) {
    result = result.filter(batch => batch.status === statusFilter.value)
  }
  
  return result
})

// 获取状态标签类型
const getStatusTagType = (status) => {
  const typeMap = {
    'pending': 'info',
    'processing': 'warning',
    'completed': 'success',
    'failed': 'danger'
  }
  return typeMap[status] || 'default'
}

// 获取状态文本
const getStatusText = (status) => {
  const textMap = {
    'pending': '待处理',
    'processing': '处理中',
    'completed': '已完成',
    'failed': '失败'
  }
  return textMap[status] || status
}

// 获取进度百分比
const getProgress = (batch) => {
  if (!batch.total_count || batch.total_count === 0) return 0
  return Math.round((batch.completed_count / batch.total_count) * 100)
}

// 获取进度条状态
const getProgressStatus = (status) => {
  if (status === 'completed') return 'success'
  if (status === 'failed') return 'exception'
  return null
}

// 格式化日期
const formatDate = (dateString) => {
  return dayjs(dateString).format('YYYY-MM-DD HH:mm:ss')
}

// 获取指定状态的批次数量
const getStatusCount = (status) => {
  return batches.value.filter(batch => batch.status === status).length
}

// 加载批次列表
const loadBatches = async () => {
  // 防止重复请求
  if (loading.value) {
    console.log('[loadBatches] Request blocked - already loading')
    return
  }
  
  console.log('[loadBatches] Starting batch request at:', new Date().toISOString())
  loading.value = true
  try {
    const params = {
      page: currentPage.value,
      size: pageSize.value
    }
    
    // 添加状态过滤
    if (statusFilter.value) {
      params.status_filter = statusFilter.value
    }
    
    // 使用管理员批次API
    const response = await api.get('/admin/batches', { params })
    
    if (response.data && response.data.data) {
      const responseData = response.data.data
      batches.value = responseData.items || []
      total.value = responseData.pagination?.total || 0
    } else {
      batches.value = []
      total.value = 0
    }
  } catch (error) {
    console.error('加载批次列表失败:', error)
    ElMessage.error('加载批次列表失败')
    batches.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

// 分页处理
const handleSizeChange = (val) => {
  pageSize.value = val
  currentPage.value = 1
  loadBatches()
}

const handleCurrentChange = (val) => {
  currentPage.value = val
  loadBatches()
}

// 显示创建对话框
const showCreateDialog = () => {
  createDialogVisible.value = true
}

// 重置创建表单
const resetCreateForm = () => {
  if (createFormRef.value) {
    createFormRef.value.resetFields()
  }
  Object.assign(createForm, {
    name: '',
    description: '',
    config: '{}'
  })
}

// 创建批次
const createBatch = async () => {
  if (!createFormRef.value) return
  
  try {
    const valid = await createFormRef.value.validate()
    if (!valid) return
    
    creating.value = true
    
    const data = {
      batch_name: createForm.name,
      description: createForm.description,
      expected_count: parseInt(createForm.config) || 0
    }
    
    await api.post('/batch', data)
    ElMessage.success('批次创建成功')
    
    createDialogVisible.value = false
    loadBatches()
  } catch (error) {
    console.error('创建批次失败:', error)
    ElMessage.error('创建批次失败')
  } finally {
    creating.value = false
  }
}

// 查看批次详情
const viewBatchDetail = (batch) => {
  router.push(`/batches/${batch.batch_id}`)
}

// 处理批次
const processBatch = async (batch) => {
  try {
    await ElMessageBox.confirm(`确定要开始处理批次 "${batch.batch_name || batch.name}" 吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await api.post(`/batch/${batch.batch_id}/process`)
    ElMessage.success('批次处理已开始')
    loadBatches()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('处理批次失败:', error)
      ElMessage.error('处理批次失败')
    }
  }
}

// 删除批次
const deleteBatch = async (batch) => {
  try {
    await ElMessageBox.confirm(`确定要删除批次 "${batch.name}" 吗？此操作不可恢复！`, '警告', {
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
      type: 'error'
    })
    
    await api.delete(`/admin/batches/${batch.id}`)
    ElMessage.success('批次删除成功')
    loadBatches()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除批次失败:', error)
      ElMessage.error('删除批次失败')
    }
  }
}

// 组件挂载时加载数据
onMounted(() => {
  console.log('[Batch List.vue] onMounted called at:', new Date().toISOString())
  loadBatches()
})
</script>

<style scoped>
.batches-page {
  padding: 20px;
}

.page-header {
  margin-bottom: 24px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.page-title {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
  color: #1f2937;
  display: flex;
  align-items: center;
  gap: 8px;
}

.page-description {
  margin: 4px 0 0 0;
  color: #6b7280;
  font-size: 14px;
}

.header-right {
  display: flex;
  gap: 12px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.grid-view {
  margin-bottom: 24px;
}

.batches-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 20px;
  margin-bottom: 24px;
}

.batch-card {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.batch-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  border-color: #3b82f6;
}

.batch-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.batch-name {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 4px;
}

.batch-id {
  font-size: 12px;
  color: #6b7280;
  font-family: 'Monaco', 'Menlo', monospace;
}

.batch-status {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  font-weight: 500;
  padding: 4px 8px;
  border-radius: 6px;
  white-space: nowrap;
}

.batch-status.pending {
  background: #fef3c7;
  color: #d97706;
}

.batch-status.processing {
  background: #dbeafe;
  color: #2563eb;
}

.batch-status.completed {
  background: #d1fae5;
  color: #059669;
}

.batch-status.failed {
  background: #fee2e2;
  color: #dc2626;
}

.batch-details {
  margin-bottom: 16px;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 14px;
}

.detail-item .label {
  color: #6b7280;
  font-weight: 500;
}

.detail-item .value {
  color: #1f2937;
  font-weight: 400;
  text-align: right;
  max-width: 60%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.batch-progress {
  margin-bottom: 16px;
}

.batch-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

.list-view {
  margin-bottom: 24px;
  width: 100%;
  overflow-x: auto;
}

.list-view .el-table {
  min-width: 1200px;
}

.list-view :deep(.el-scrollbar__view) {
  width: 100% !important;
  min-width: 1200px;
}

.list-view :deep(.el-table__body-wrapper) {
  overflow-x: auto;
}

.stats-section {
  margin-bottom: 24px;
}

.stat-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  display: flex;
  align-items: center;
  gap: 16px;
  transition: all 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: white;
}

.stat-icon.total {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.stat-icon.pending {
  background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
}

.stat-icon.processing {
  background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
}

.stat-icon.completed {
  background: linear-gradient(135deg, #4ade80 0%, #22c55e 100%);
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #1f2937;
  line-height: 1;
}

.stat-label {
  font-size: 14px;
  color: #6b7280;
  margin-top: 4px;
}

.search-section {
  margin-bottom: 24px;
}

.batches-section {
  margin-bottom: 24px;
}

.batch-name-cell {
  display: flex;
  align-items: center;
}

.batch-name-cell .batch-info .name {
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 2px;
}

.batch-name-cell .batch-info .id {
  font-size: 12px;
  color: #6b7280;
  font-family: 'Monaco', 'Menlo', monospace;
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 24px;
}

@media (max-width: 768px) {
  .batches-page {
    padding: 12px;
  }
  
  .page-title {
    font-size: 20px;
  }
  
  .header-content {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }
  
  .stat-card {
    padding: 16px;
  }
  
  .stat-value {
    font-size: 24px;
  }
  
  .batches-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }
  
  .batch-card {
    padding: 16px;
  }
  
  .batch-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  
  .batch-actions {
    flex-wrap: wrap;
    gap: 6px;
  }
  
  .batch-actions .el-button {
    flex: 1;
    min-width: 80px;
  }
}

.list-view {
  margin-bottom: 24px;
}

.batch-name-cell {
  display: flex;
  align-items: center;
}

.batch-name-cell .batch-info {
  display: flex;
  flex-direction: column;
}

.batch-name-cell .name {
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 2px;
}

.batch-name-cell .id {
  font-size: 12px;
  color: #6b7280;
  font-family: 'Monaco', 'Menlo', monospace;
}

@media (max-width: 1200px) {
  .batches-grid {
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  }
}

@media (max-width: 992px) {
  .batches-grid {
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  }
}
</style>