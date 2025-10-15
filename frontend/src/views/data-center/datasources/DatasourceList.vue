<template>
  <div class="datasource-list">
    <div class="page-header">
      <h1>数据源管理</h1>
      <p>管理系统中的数据源连接</p>
    </div>

    <div class="content-container">
      <!-- 搜索和操作栏 -->
      <div class="toolbar">
        <div class="search-section">
          <el-input
            v-model="searchQuery"
            placeholder="搜索数据源名称或描述"
            style="width: 300px;"
            clearable
            @input="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
          
          <el-select
            v-model="typeFilter"
            placeholder="数据源类型"
            style="width: 150px; margin-left: 12px;"
            clearable
            @change="handleSearch"
          >
            <el-option label="全部" value="" />
            <el-option label="MySQL" value="mysql" />
            <el-option label="Doris" value="doris" />
            <el-option label="Elasticsearch" value="elasticsearch" />
            <el-option label="ClickHouse" value="clickhouse" />
          </el-select>
          
          <el-select
            v-model="statusFilter"
            placeholder="连接状态"
            style="width: 120px; margin-left: 12px;"
            clearable
            @change="handleSearch"
          >
            <el-option label="全部" value="" />
            <el-option label="正常" value="connected" />
            <el-option label="断开" value="disconnected" />
            <el-option label="错误" value="error" />
          </el-select>
        </div>
        
        <div class="action-section">
          <el-button type="primary" @click="handleCreate">
            <el-icon><Plus /></el-icon>
            新增数据源
          </el-button>
          <el-button @click="handleBatchTest" :disabled="!selectedDatasources.length">
            <el-icon><Connection /></el-icon>
            批量测试
          </el-button>
          <el-button @click="handleRefresh">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </div>

      <!-- 数据源列表 -->
      <el-card class="datasource-list-card">
        <el-table
          ref="datasourceTableRef"
          :data="filteredDatasources"
          stripe
          border
          v-loading="loading"
          @selection-change="handleSelectionChange"
          style="width: 100%"
        >
          <el-table-column type="selection" width="55" />
          
          <el-table-column prop="name" label="数据源名称" min-width="150">
            <template #default="{ row }">
              <div class="datasource-name">
                <el-icon class="datasource-icon">
                  <Database />
                </el-icon>
                <span>{{ row.name }}</span>
              </div>
            </template>
          </el-table-column>
          
          <el-table-column prop="display_name" label="显示名称" min-width="150" />
          
          <el-table-column prop="type" label="数据源类型" width="120">
            <template #default="{ row }">
              <el-tag :type="getTypeTagType(row.type)">
                {{ getTypeDisplayName(row.type) }}
              </el-tag>
            </template>
          </el-table-column>
          
          <el-table-column prop="host" label="主机地址" min-width="150" />
          
          <el-table-column prop="port" label="端口" width="80" />
          
          <el-table-column prop="database" label="数据库" min-width="120" />
          
          <el-table-column prop="connection_status" label="连接状态" width="100">
            <template #default="{ row }">
              <el-tag :type="getStatusTagType(row.connection_status)">
                {{ getStatusDisplayName(row.connection_status) }}
              </el-tag>
            </template>
          </el-table-column>
          
          <el-table-column prop="last_test_time" label="最后测试时间" width="180">
            <template #default="{ row }">
              {{ row.last_test_time ? formatDate(row.last_test_time) : '-' }}
            </template>
          </el-table-column>
          
          <el-table-column prop="created_at" label="创建时间" width="180">
            <template #default="{ row }">
              {{ formatDate(row.created_at) }}
            </template>
          </el-table-column>
          
          <el-table-column label="操作" width="250" fixed="right">
            <template #default="{ row }">
              <el-button type="text" size="small" @click="handleTest(row)">
                <el-icon><Connection /></el-icon>
                测试连接
              </el-button>
              <el-button type="text" size="small" @click="handleView(row)">
                <el-icon><View /></el-icon>
                查看
              </el-button>
              <el-button type="text" size="small" @click="handleEdit(row)">
                <el-icon><Edit /></el-icon>
                编辑
              </el-button>
              <el-button
                type="text"
                size="small"
                @click="handleDelete(row)"
                style="color: #f56c6c;"
              >
                <el-icon><Delete /></el-icon>
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
        
        <!-- 分页 -->
        <div class="pagination-container">
          <el-pagination
            v-model:current-page="pagination.page"
            v-model:page-size="pagination.size"
            :total="pagination.total"
            :page-sizes="[10, 20, 50, 100]"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="handleSizeChange"
            @current-change="handlePageChange"
          />
        </div>
      </el-card>
    </div>

    <!-- 测试连接对话框 -->
    <el-dialog
      v-model="testDialogVisible"
      title="测试连接"
      width="500px"
    >
      <div v-if="testResult" class="test-result">
        <div class="result-header">
          <el-icon :class="testResult.success ? 'success-icon' : 'error-icon'">
            <CircleCheck v-if="testResult.success" />
            <CircleClose v-else />
          </el-icon>
          <span :class="testResult.success ? 'success-text' : 'error-text'">
            {{ testResult.success ? '连接成功' : '连接失败' }}
          </span>
        </div>
        
        <div class="result-details">
          <el-descriptions :column="1" border>
            <el-descriptions-item label="响应时间">
              {{ testResult.response_time }}ms
            </el-descriptions-item>
            <el-descriptions-item label="测试时间">
              {{ formatDate(testResult.test_time) }}
            </el-descriptions-item>
            <el-descriptions-item label="详细信息" v-if="testResult.message">
              {{ testResult.message }}
            </el-descriptions-item>
            <el-descriptions-item label="错误信息" v-if="testResult.error">
              <el-text type="danger">{{ testResult.error }}</el-text>
            </el-descriptions-item>
          </el-descriptions>
        </div>
      </div>
      
      <div v-else-if="testing" class="testing-status">
        <el-icon class="loading-icon"><Loading /></el-icon>
        <span>正在测试连接...</span>
      </div>
      
      <template #footer>
        <el-button @click="testDialogVisible = false">关闭</el-button>
        <el-button
          type="primary"
          @click="handleRetestConnection"
          :loading="testing"
          v-if="currentTestDatasource"
        >
          重新测试
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Search,
  Plus,
  Edit,
  Delete,
  Refresh,
  View,
  Connection,
  Database,
  CircleCheck,
  CircleClose,
  Loading
} from '@element-plus/icons-vue'
import type { Datasource, DatasourceTestResult } from '@/types/datasource'

/**
 * 路由实例
 */
const router = useRouter()

/**
 * 响应式数据
 */
const datasources = ref<Datasource[]>([])
const selectedDatasources = ref<Datasource[]>([])
const loading = ref(false)
const testing = ref(false)
const testDialogVisible = ref(false)
const testResult = ref<DatasourceTestResult | null>(null)
const currentTestDatasource = ref<Datasource | null>(null)
const searchQuery = ref('')
const typeFilter = ref('')
const statusFilter = ref('')

/**
 * 分页数据
 */
const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

/**
 * 过滤后的数据源列表
 */
const filteredDatasources = computed(() => {
  let result = datasources.value
  
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(ds =>
      ds.name.toLowerCase().includes(query) ||
      ds.display_name?.toLowerCase().includes(query) ||
      ds.description?.toLowerCase().includes(query)
    )
  }
  
  if (typeFilter.value) {
    result = result.filter(ds => ds.type === typeFilter.value)
  }
  
  if (statusFilter.value) {
    result = result.filter(ds => ds.connection_status === statusFilter.value)
  }
  
  return result
})

/**
 * 获取数据源列表
 */
const fetchDatasources = async () => {
  loading.value = true
  
  try {
    // TODO: 调用API获取数据源列表
    // const response = await datasourceApi.getList({
    //   page: pagination.page,
    //   size: pagination.size,
    //   search: searchQuery.value,
    //   type: typeFilter.value,
    //   status: statusFilter.value
    // })
    // datasources.value = response.data.items
    // pagination.total = response.data.total
    
    // 模拟数据
    datasources.value = [
      {
        id: 1,
        name: 'main_mysql',
        display_name: '主数据库',
        description: '主要的MySQL数据库',
        type: 'mysql',
        host: 'localhost',
        port: 3306,
        database: 'acwl_ai',
        username: 'root',
        password: '******',
        connection_status: 'connected',
        last_test_time: '2024-01-01T10:00:00Z',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
        created_by: 1,
        is_active: true
      },
      {
        id: 2,
        name: 'analytics_doris',
        display_name: '分析数据库',
        description: 'Doris分析数据库',
        type: 'doris',
        host: 'doris-cluster',
        port: 9030,
        database: 'analytics',
        username: 'admin',
        password: '******',
        connection_status: 'connected',
        last_test_time: '2024-01-01T09:30:00Z',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
        created_by: 1,
        is_active: true
      },
      {
        id: 3,
        name: 'search_es',
        display_name: '搜索引擎',
        description: 'Elasticsearch搜索引擎',
        type: 'elasticsearch',
        host: 'es-cluster',
        port: 9200,
        database: '',
        username: 'elastic',
        password: '******',
        connection_status: 'error',
        last_test_time: '2024-01-01T08:00:00Z',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
        created_by: 1,
        is_active: true
      }
    ]
    pagination.total = datasources.value.length
  } catch (error) {
    ElMessage.error('获取数据源列表失败')
  } finally {
    loading.value = false
  }
}

/**
 * 处理搜索
 */
const handleSearch = () => {
  pagination.page = 1
  fetchDatasources()
}

/**
 * 处理新增
 */
const handleCreate = () => {
  router.push('/datasources/create')
}

/**
 * 处理查看
 */
const handleView = (datasource: Datasource) => {
  router.push(`/datasources/detail/${datasource.id}`)
}

/**
 * 处理编辑
 */
const handleEdit = (datasource: Datasource) => {
  router.push(`/datasources/edit/${datasource.id}`)
}

/**
 * 处理删除
 */
const handleDelete = async (datasource: Datasource) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除数据源 "${datasource.display_name}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    // TODO: 调用删除API
    // await datasourceApi.delete(datasource.id!)
    
    ElMessage.success('删除成功')
    fetchDatasources()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

/**
 * 处理测试连接
 */
const handleTest = async (datasource: Datasource) => {
  currentTestDatasource.value = datasource
  testResult.value = null
  testDialogVisible.value = true
  testing.value = true
  
  try {
    // TODO: 调用测试连接API
    // const response = await datasourceApi.testConnection(datasource.id!)
    // testResult.value = response.data
    
    // 模拟测试结果
    await new Promise(resolve => setTimeout(resolve, 2000))
    testResult.value = {
      success: datasource.connection_status === 'connected',
      response_time: Math.floor(Math.random() * 500) + 50,
      test_time: new Date().toISOString(),
      message: datasource.connection_status === 'connected' ? '连接正常' : '连接超时',
      error: datasource.connection_status === 'connected' ? undefined : '无法连接到数据库服务器'
    }
  } catch (error) {
    testResult.value = {
      success: false,
      response_time: 0,
      test_time: new Date().toISOString(),
      message: '测试失败',
      error: '网络错误或服务器不可达'
    }
  } finally {
    testing.value = false
  }
}

/**
 * 处理重新测试连接
 */
const handleRetestConnection = () => {
  if (currentTestDatasource.value) {
    handleTest(currentTestDatasource.value)
  }
}

/**
 * 处理批量测试
 */
const handleBatchTest = async () => {
  if (selectedDatasources.value.length === 0) {
    ElMessage.warning('请选择要测试的数据源')
    return
  }
  
  ElMessage.info('批量测试功能开发中...')
}

/**
 * 处理刷新
 */
const handleRefresh = () => {
  fetchDatasources()
}

/**
 * 处理选择变更
 */
const handleSelectionChange = (selection: Datasource[]) => {
  selectedDatasources.value = selection
}

/**
 * 处理页面大小变更
 */
const handleSizeChange = (size: number) => {
  pagination.size = size
  pagination.page = 1
  fetchDatasources()
}

/**
 * 处理页面变更
 */
const handlePageChange = (page: number) => {
  pagination.page = page
  fetchDatasources()
}

/**
 * 获取类型标签类型
 */
const getTypeTagType = (type: string) => {
  const typeMap: Record<string, string> = {
    mysql: 'primary',
    doris: 'success',
    elasticsearch: 'warning',
    clickhouse: 'info'
  }
  return typeMap[type] || 'info'
}

/**
 * 获取类型显示名称
 */
const getTypeDisplayName = (type: string) => {
  const typeMap: Record<string, string> = {
    mysql: 'MySQL',
    doris: 'Doris',
    elasticsearch: 'Elasticsearch',
    clickhouse: 'ClickHouse'
  }
  return typeMap[type] || type
}

/**
 * 获取状态标签类型
 */
const getStatusTagType = (status: string) => {
  const statusMap: Record<string, string> = {
    connected: 'success',
    disconnected: 'info',
    error: 'danger'
  }
  return statusMap[status] || 'info'
}

/**
 * 获取状态显示名称
 */
const getStatusDisplayName = (status: string) => {
  const statusMap: Record<string, string> = {
    connected: '已连接',
    disconnected: '未连接',
    error: '连接错误'
  }
  return statusMap[status] || status
}

/**
 * 格式化日期
 */
const formatDate = (date: string) => {
  return new Date(date).toLocaleString()
}

/**
 * 组件挂载时获取数据
 */
onMounted(() => {
  fetchDatasources()
})
</script>

<style scoped>
.datasource-list {
  padding: 20px;
}

.page-header {
  margin-bottom: 20px;
}

.page-header h1 {
  margin: 0 0 8px 0;
  font-size: 24px;
  font-weight: 600;
}

.page-header p {
  margin: 0;
  color: #666;
}

.content-container {
  min-height: 600px;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 16px;
  background: #f5f5f5;
  border-radius: 4px;
}

.search-section {
  display: flex;
  align-items: center;
}

.action-section {
  display: flex;
  gap: 8px;
}

.datasource-list-card {
  margin-bottom: 20px;
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
  display: flex;
  justify-content: center;
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #eee;
}

.test-result {
  padding: 20px;
}

.result-header {
  display: flex;
  align-items: center;
  margin-bottom: 20px;
  font-size: 16px;
  font-weight: 600;
}

.success-icon {
  color: #67c23a;
  margin-right: 8px;
}

.error-icon {
  color: #f56c6c;
  margin-right: 8px;
}

.success-text {
  color: #67c23a;
}

.error-text {
  color: #f56c6c;
}

.testing-status {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
  font-size: 16px;
}

.loading-icon {
  margin-right: 8px;
  animation: rotate 2s linear infinite;
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style>