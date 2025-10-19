<template>
  <div class="datasource-container">
    <!-- 页面标题和操作栏 -->
    <div class="page-header">
      <div class="header-left">
        <h2>数据源管理</h2>
        <p class="page-description">管理和配置多种数据源连接</p>
      </div>
      <div class="header-right">
        <el-button type="primary" @click="showCreateDialog" :icon="Plus">
          新建数据源
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
                <el-icon><DataBoard /></el-icon>
              </div>
              <div class="stats-info">
                <div class="stats-number">{{ stats.total_count }}</div>
                <div class="stats-label">总数据源</div>
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
                <div class="stats-number">{{ stats.active_count }}</div>
                <div class="stats-label">正常连接</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stats-card">
            <div class="stats-content">
              <div class="stats-icon error">
                <el-icon><CircleClose /></el-icon>
              </div>
              <div class="stats-info">
                <div class="stats-number">{{ stats.error_count }}</div>
                <div class="stats-label">连接异常</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stats-card">
            <div class="stats-content">
              <div class="stats-icon success-rate">
                <el-icon><TrendCharts /></el-icon>
              </div>
              <div class="stats-info">
                <div class="stats-number">{{ stats.recent_test_success_rate }}%</div>
                <div class="stats-label">测试成功率</div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 筛选和搜索 -->
    <el-card class="filter-card">
      <el-form :model="filters" inline>
        <el-form-item label="数据源类型">
          <el-select v-model="filters.type" placeholder="选择类型" clearable style="width: 150px">
            <el-option
              v-for="template in datasourceTemplates"
              :key="template.datasource_type"
              :label="getTypeLabel(template.datasource_type)"
              :value="template.datasource_type"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filters.status" placeholder="选择状态" clearable style="width: 120px">
            <el-option label="正常" value="active" />
            <el-option label="异常" value="error" />
            <el-option label="未知" value="unknown" />
          </el-select>
        </el-form-item>
        <el-form-item label="启用状态">
          <el-select v-model="filters.enabled" placeholder="选择启用状态" clearable style="width: 120px">
            <el-option label="启用" :value="true" />
            <el-option label="禁用" :value="false" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-input
            v-model="filters.search"
            placeholder="搜索数据源名称或主机"
            :prefix-icon="Search"
            style="width: 250px"
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch" :icon="Search">
            搜索
          </el-button>
          <el-button @click="handleReset" :icon="Refresh">
            重置
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 数据源列表 -->
    <el-card class="table-card">
      <template #header>
        <div class="card-header">
          <span>数据源列表</span>
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
        <div class="datasources-grid">
          <div
            v-for="datasource in datasources"
            :key="datasource.id"
            class="datasource-card"
          >
            <div class="datasource-header">
              <div class="datasource-info">
                <div class="datasource-name">
                  <el-icon class="datasource-icon">{{ getDatasourceIcon(datasource.datasource_type) }}</el-icon>
                  {{ datasource.name }}
                </div>
                <div class="datasource-host">{{ datasource.host }}:{{ datasource.port }}</div>
              </div>
              <div class="datasource-status" :class="datasource.status">
                <el-icon><Connection /></el-icon>
              </div>
            </div>

            <div class="datasource-details">
              <div class="detail-item">
                <span class="label">类型:</span>
                <el-tag :type="getTypeColor(datasource.type)" size="small">
                  {{ getTypeLabel(datasource.type) }}
                </el-tag>
              </div>
              <div class="detail-item">
                <span class="label">数据库:</span>
                <span class="value">{{ datasource.database || '-' }}</span>
              </div>
              <div class="detail-item">
                <span class="label">启用状态:</span>
                <el-tag :type="datasource.enabled ? 'success' : 'danger'" size="small">
                  {{ datasource.enabled ? '启用' : '禁用' }}
                </el-tag>
              </div>
              <div class="detail-item">
                <span class="label">最后测试:</span>
                <span class="value">{{ datasource.last_test_time || '未测试' }}</span>
              </div>
              <div class="detail-item">
                <span class="label">创建时间:</span>
                <span class="value">{{ datasource.created_at }}</span>
              </div>
            </div>

            <div class="datasource-actions">
              <el-button
                type="primary"
                size="small"
                @click="testConnection(datasource)"
                :loading="datasource.testing"
                :icon="Connection"
              >
                测试连接
              </el-button>
              <el-dropdown @command="(command) => handleDatasourceAction(command, datasource)">
                <el-button size="small" :icon="MoreFilled" />
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="edit" :icon="Edit">
                      编辑
                    </el-dropdown-item>
                    <el-dropdown-item command="delete" :icon="Delete" divided>
                      删除
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 列表视图 -->
      <div v-else class="list-view">
        <el-table
          v-loading="loading"
          :data="datasources"
          style="width: 100%"
          @selection-change="handleSelectionChange"
        >
          <el-table-column type="selection" width="55" />
          <el-table-column prop="name" label="数据源名称" min-width="200">
            <template #default="{ row }">
              <div class="datasource-name">
                <el-icon class="datasource-icon">{{ getDatasourceIcon(row.type) }}</el-icon>
                <span>{{ row.name }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="type" label="类型" width="120">
            <template #default="{ row }">
              <el-tag :type="getTypeColor(row.type)" size="small">
                {{ getTypeLabel(row.type) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="host" label="主机地址" min-width="180">
            <template #default="{ row }">
              {{ row.host }}:{{ row.port }}
            </template>
          </el-table-column>
          <el-table-column prop="database" label="数据库" width="150" />
          <el-table-column prop="status" label="连接状态" width="100">
            <template #default="{ row }">
              <el-tag :type="getStatusColor(row.status)" size="small">
                {{ getStatusLabel(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="enabled" label="启用状态" width="100">
            <template #default="{ row }">
              <el-switch
                v-model="row.enabled"
                @change="toggleEnabled(row)"
              />
            </template>
          </el-table-column>
          <el-table-column prop="last_test_time" label="最后测试时间" width="180" />
          <el-table-column prop="created_at" label="创建时间" width="180" />
          <el-table-column label="操作" width="200" fixed="right">
            <template #default="{ row }">
              <el-button
                type="primary"
                size="small"
                @click="testConnection(row)"
                :loading="row.testing"
                :icon="Connection"
              >
                测试
              </el-button>
              <el-button
                size="small"
                @click="editDatasource(row)"
                :icon="Edit"
              >
                编辑
              </el-button>
              <el-button
                type="danger"
                size="small"
                @click="deleteDatasource(row)"
                :icon="Delete"
              >
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.size"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 创建/编辑数据源对话框 -->
    <DatasourceDialog
      v-model="dialogVisible"
      :datasource="currentDatasource"
      :mode="dialogMode"
      @success="handleDialogSuccess"
    />

    <!-- 测试结果对话框 -->
    <TestResultDialog
      v-model="testDialogVisible"
      :test-result="testResult"
    />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus, Search, Refresh, DataBoard, CircleCheck, CircleClose,
  TrendCharts, Connection, Edit, Delete, Grid, List, MoreFilled
} from '@element-plus/icons-vue'
import DatasourceDialog from './components/DatasourceDialog.vue'
import TestResultDialog from './components/TestResultDialog.vue'
import { datasourceApi } from '@/api/datasourceV2'

// 响应式数据
const loading = ref(false)
const datasources = ref([])
const selectedDatasources = ref([])
const dialogVisible = ref(false)
const testDialogVisible = ref(false)
const dialogMode = ref('create')
const currentDatasource = ref(null)
const testResult = ref(null)
const viewMode = ref('grid')
const datasourceTemplates = ref([])

// 统计数据
const stats = ref({
  total_count: 0,
  active_count: 0,
  error_count: 0,
  recent_test_success_rate: 0
})

// 筛选条件
const filters = reactive({
  search: '',
  type: '',
  status: '',
  enabled: null
})

// 分页
const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

// 计算属性
const hasSelection = computed(() => selectedDatasources.value.length > 0)

// 方法
const loadDatasourceTemplates = async () => {
  try {
    const response = await datasourceApi.getDatasourceTemplates()
    datasourceTemplates.value = response
  } catch (error) {
    console.error('加载数据源模板失败:', error)
    ElMessage.error('加载数据源模板失败')
  }
}

const loadDatasources = async () => {
  try {
    loading.value = true
    const params = {
      page: pagination.page,
      size: pagination.size,
      ...filters
    }
    
    // 过滤空值
    Object.keys(params).forEach(key => {
      if (params[key] === '' || params[key] === null) {
        delete params[key]
      }
    })
    
    const response = await datasourceApi.getDatasources(params)
    // 防护代码：确保response和response.items存在
    if (response && Array.isArray(response.data.items)) {
      datasources.value = response.data.items.map(item => ({
        ...item,
        type: item.datasource_type,
        database: item.database_name,
        enabled: item.is_enabled,
        testing: false
      }))
      pagination.total = response.total || 0
    } else if (response && Array.isArray(response)) {
      // 如果API直接返回数组而不是包含items的对象
      datasources.value = response.map(item => ({
        ...item,
        type: item.datasource_type,
        database: item.database_name,
        enabled: item.is_enabled,
        testing: false
      }))
      pagination.total = response.length
    } else {
      console.warn('Unexpected API response structure:', response)
      datasources.value = []
      pagination.total = 0
    }
  } catch (error) {
    ElMessage.error('加载数据源列表失败')
    console.error('Load datasources error:', error)
  } finally {
    loading.value = false
  }
}

const loadStats = async () => {
  try {
    const response = await datasourceApi.getDatasourceStats()
    stats.value = response
  } catch (error) {
    console.error('Load stats error:', error)
  }
}

const handleSearch = () => {
  pagination.page = 1
  loadDatasources()
}

const handleReset = () => {
  Object.assign(filters, {
    search: '',
    type: '',
    status: '',
    enabled: null
  })
  handleSearch()
}

const handleSizeChange = (size) => {
  pagination.size = size
  pagination.page = 1
  loadDatasources()
}

const handleCurrentChange = (page) => {
  pagination.page = page
  loadDatasources()
}

const handleSelectionChange = (selection) => {
  selectedDatasources.value = selection
}

const showCreateDialog = () => {
  dialogMode.value = 'create'
  currentDatasource.value = null
  dialogVisible.value = true
}

const editDatasource = (row) => {
  dialogMode.value = 'edit'
  currentDatasource.value = { ...row }
  dialogVisible.value = true
}

const testConnection = async (row) => {
  try {
    row.testing = true
    const response = await datasourceApi.testDatasourceConnection(row.id, {
      timeout: 10
    })
    testResult.value = response
    testDialogVisible.value = true
    
    // 刷新列表以更新状态
    await loadDatasources()
  } catch (error) {
    ElMessage.error('测试连接失败')
    console.error('Test connection error:', error)
  } finally {
    row.testing = false
  }
}

const toggleEnabled = async (row) => {
  try {
    if (row.enabled) {
      await datasourceApi.enableDatasource(row.id)
      ElMessage.success('数据源已启用')
    } else {
      await datasourceApi.disableDatasource(row.id)
      ElMessage.success('数据源已禁用')
    }
  } catch (error) {
    // 恢复开关状态
    row.enabled = !row.enabled
    ElMessage.error('操作失败')
    console.error('Toggle enable error:', error)
  }
}

const deleteDatasource = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除数据源 "${row.name}" 吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await datasourceApi.deleteDatasource(row.id)
    ElMessage.success('删除成功')
    await loadDatasources()
    await loadStats()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
      console.error('Delete datasource error:', error)
    }
  }
}

const handleDialogSuccess = () => {
  loadDatasources()
  loadStats()
}

const handleDatasourceAction = (command, datasource) => {
  switch (command) {
    case 'edit':
      editDatasource(datasource)
      break
    case 'delete':
      deleteDatasource(datasource)
      break
    default:
      console.warn('未知操作:', command)
  }
}

// 工具方法
const getDatasourceIcon = (type) => {
  const icons = {
    mysql: 'Db',
    postgresql: 'Db',
    mongodb: 'Doc',
    redis: 'Key',
    clickhouse: 'Db',
    elasticsearch: 'Search',
    doris: 'Db',
    oracle: 'Db',
    sqlserver: 'Db'
  }
  return icons[type] || 'Db'
}

const getTypeColor = (type) => {
  const colors = {
    mysql: 'primary',
    postgresql: 'info',
    mongodb: 'success',
    redis: 'warning',
    clickhouse: 'primary',
    elasticsearch: 'info',
    doris: 'success',
    oracle: 'warning',
    sqlserver: 'primary'
  }
  return colors[type] || 'info'
}

const getTypeLabel = (type) => {
  const labels = {
    mysql: 'MySQL',
    postgresql: 'PostgreSQL',
    mongodb: 'MongoDB',
    redis: 'Redis',
    clickhouse: 'ClickHouse',
    elasticsearch: 'Elasticsearch',
    doris: 'Apache Doris',
    oracle: 'Oracle',
    sqlserver: 'SQL Server'
  }
  return labels[type] || type
}

const getStatusColor = (status) => {
  const colors = {
    active: 'success',
    error: 'danger',
    unknown: 'info'
  }
  return colors[status] || 'info'
}

const getStatusLabel = (status) => {
  const labels = {
    active: '正常',
    error: '异常',
    unknown: '未知'
  }
  return labels[status] || status
}

// 生命周期
onMounted(() => {
  loadDatasourceTemplates()
  loadDatasources()
  loadStats()
})
</script>

<style scoped>
.datasource-container {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-left h2 {
  margin: 0 0 5px 0;
  color: #303133;
}

.page-description {
  margin: 0;
  color: #909399;
  font-size: 14px;
}

.stats-cards {
  margin-bottom: 20px;
}

.stats-card {
  border: none;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.stats-content {
  display: flex;
  align-items: center;
}

.stats-icon {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 16px;
  font-size: 24px;
  color: white;
}

.stats-icon.total {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.stats-icon.active {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.stats-icon.error {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.stats-icon.success-rate {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
}

.stats-info {
  flex: 1;
}

.stats-number {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
  line-height: 1;
}

.stats-label {
  font-size: 14px;
  color: #909399;
  margin-top: 4px;
}

.filter-card {
  margin-bottom: 20px;
}

.table-card {
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.datasource-name {
  display: flex;
  align-items: center;
}

.datasource-icon {
  margin-right: 8px;
  color: #409eff;
}

.pagination-container {
  margin-top: 20px;
  text-align: right;
}

:deep(.el-table .el-table__cell) {
  padding: 12px 0;
}

:deep(.el-card__body) {
  padding: 20px;
}

/* 卡片视图样式 */
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.grid-view {
  margin-top: 20px;
}

.datasources-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 20px;
  padding: 0;
}

.datasource-card {
  background: #fff;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 20px;
  transition: all 0.3s ease;
  cursor: pointer;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.datasource-card:hover {
  border-color: #409eff;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.15);
  transform: translateY(-2px);
}

.datasource-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f0f0;
}

.datasource-info {
  flex: 1;
}

.datasource-name {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.datasource-host {
  font-size: 13px;
  color: #909399;
}

.datasource-status {
  flex-shrink: 0;
}

.datasource-details {
  margin-bottom: 16px;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  font-size: 14px;
}

.detail-item:last-child {
  margin-bottom: 0;
}

.detail-item .label {
  color: #606266;
  font-weight: 500;
  min-width: 80px;
}

.detail-item .value {
  color: #303133;
  text-align: right;
  flex: 1;
  margin-left: 12px;
}

.datasource-actions {
  display: flex;
  gap: 8px;
  padding-top: 12px;
  border-top: 1px solid #f0f0f0;
}

.datasource-actions .el-button {
  flex: 1;
}

.datasource-actions .el-dropdown {
  flex-shrink: 0;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .datasources-grid {
    grid-template-columns: 1fr;
  }
  
  .datasource-card {
    padding: 16px;
  }
  
  .datasource-actions {
    flex-direction: column;
  }
  
  .datasource-actions .el-button {
    width: 100%;
  }
}
</style>