<template>
  <div class="datasource-detail">
    <div class="page-header">
      <div class="header-left">
        <el-button @click="handleBack" text>
          <el-icon><ArrowLeft /></el-icon>
          返回列表
        </el-button>
        <h1>{{ datasource?.display_name || '数据源详情' }}</h1>
        <el-tag :type="getStatusTagType(datasource?.connection_status)">
          {{ getStatusDisplayName(datasource?.connection_status) }}
        </el-tag>
      </div>
      <div class="header-actions">
        <el-button @click="handleTest" :loading="testing">
          <el-icon><Connection /></el-icon>
          测试连接
        </el-button>
        <el-button @click="handleEdit">
          <el-icon><Edit /></el-icon>
          编辑
        </el-button>
        <el-button type="danger" @click="handleDelete">
          <el-icon><Delete /></el-icon>
          删除
        </el-button>
      </div>
    </div>

    <div class="content-container" v-loading="loading">
      <el-row :gutter="20">
        <!-- 基本信息 -->
        <el-col :span="16">
          <el-card class="info-card">
            <template #header>
              <div class="card-header">
                <span>基本信息</span>
              </div>
            </template>
            
            <el-descriptions :column="2" border>
              <el-descriptions-item label="数据源名称">
                {{ datasource?.name }}
              </el-descriptions-item>
              <el-descriptions-item label="显示名称">
                {{ datasource?.display_name }}
              </el-descriptions-item>
              <el-descriptions-item label="数据源类型">
                <el-tag :type="getTypeTagType(datasource?.type)">
                  {{ getTypeDisplayName(datasource?.type) }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="启用状态">
                <el-tag :type="datasource?.is_active ? 'success' : 'info'">
                  {{ datasource?.is_active ? '已启用' : '已禁用' }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="描述信息" :span="2">
                {{ datasource?.description || '-' }}
              </el-descriptions-item>
              <el-descriptions-item label="创建时间">
                {{ datasource?.created_at ? formatDate(datasource.created_at) : '-' }}
              </el-descriptions-item>
              <el-descriptions-item label="更新时间">
                {{ datasource?.updated_at ? formatDate(datasource.updated_at) : '-' }}
              </el-descriptions-item>
            </el-descriptions>
          </el-card>

          <!-- 连接配置 -->
          <el-card class="info-card">
            <template #header>
              <div class="card-header">
                <span>连接配置</span>
              </div>
            </template>
            
            <el-descriptions :column="2" border>
              <el-descriptions-item label="主机地址">
                {{ datasource?.host }}
              </el-descriptions-item>
              <el-descriptions-item label="端口">
                {{ datasource?.port }}
              </el-descriptions-item>
              <el-descriptions-item label="数据库">
                {{ datasource?.database || '-' }}
              </el-descriptions-item>
              <el-descriptions-item label="用户名">
                {{ datasource?.username }}
              </el-descriptions-item>
              <el-descriptions-item label="连接超时">
                {{ datasource?.connection_timeout || 30 }}秒
              </el-descriptions-item>
              <el-descriptions-item label="查询超时">
                {{ datasource?.query_timeout || 300 }}秒
              </el-descriptions-item>
              <el-descriptions-item label="最大连接数">
                {{ datasource?.max_connections || 10 }}
              </el-descriptions-item>
              <el-descriptions-item label="SSL启用">
                <el-tag :type="datasource?.ssl_enabled ? 'success' : 'info'">
                  {{ datasource?.ssl_enabled ? '已启用' : '未启用' }}
                </el-tag>
              </el-descriptions-item>
            </el-descriptions>
          </el-card>

          <!-- 连接历史 -->
          <el-card class="info-card">
            <template #header>
              <div class="card-header">
                <span>连接历史</span>
                <el-button size="small" @click="fetchConnectionHistory">
                  <el-icon><Refresh /></el-icon>
                  刷新
                </el-button>
              </div>
            </template>
            
            <el-table
              :data="connectionHistory"
              stripe
              v-loading="historyLoading"
              style="width: 100%"
            >
              <el-table-column prop="test_time" label="测试时间" width="180">
                <template #default="{ row }">
                  {{ formatDate(row.test_time) }}
                </template>
              </el-table-column>
              
              <el-table-column prop="success" label="结果" width="100">
                <template #default="{ row }">
                  <el-tag :type="row.success ? 'success' : 'danger'">
                    {{ row.success ? '成功' : '失败' }}
                  </el-tag>
                </template>
              </el-table-column>
              
              <el-table-column prop="response_time" label="响应时间" width="120">
                <template #default="{ row }">
                  {{ row.response_time }}ms
                </template>
              </el-table-column>
              
              <el-table-column prop="message" label="详细信息" min-width="200">
                <template #default="{ row }">
                  <span v-if="row.success">{{ row.message }}</span>
                  <el-text v-else type="danger">{{ row.error || row.message }}</el-text>
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </el-col>

        <!-- 侧边栏 -->
        <el-col :span="8">
          <!-- 连接状态 -->
          <el-card class="status-card">
            <template #header>
              <div class="card-header">
                <span>连接状态</span>
              </div>
            </template>
            
            <div class="status-content">
              <div class="status-indicator">
                <el-icon
                  :class="getStatusIconClass(datasource?.connection_status)"
                  size="32"
                >
                  <CircleCheck v-if="datasource?.connection_status === 'connected'" />
                  <CircleClose v-else-if="datasource?.connection_status === 'error'" />
                  <Warning v-else />
                </el-icon>
                <span class="status-text">
                  {{ getStatusDisplayName(datasource?.connection_status) }}
                </span>
              </div>
              
              <div class="status-details">
                <div class="detail-item">
                  <span class="label">最后测试时间：</span>
                  <span class="value">
                    {{ datasource?.last_test_time ? formatDate(datasource.last_test_time) : '未测试' }}
                  </span>
                </div>
              </div>
            </div>
          </el-card>

          <!-- 统计信息 -->
          <el-card class="stats-card">
            <template #header>
              <div class="card-header">
                <span>使用统计</span>
              </div>
            </template>
            
            <div class="stats-content">
              <div class="stat-item">
                <div class="stat-value">{{ stats.total_queries }}</div>
                <div class="stat-label">总查询次数</div>
              </div>
              <div class="stat-item">
                <div class="stat-value">{{ stats.success_rate }}%</div>
                <div class="stat-label">成功率</div>
              </div>
              <div class="stat-item">
                <div class="stat-value">{{ stats.avg_response_time }}ms</div>
                <div class="stat-label">平均响应时间</div>
              </div>
              <div class="stat-item">
                <div class="stat-value">{{ stats.last_7_days_queries }}</div>
                <div class="stat-label">近7天查询</div>
              </div>
            </div>
          </el-card>

          <!-- 相关资源 -->
          <el-card class="resources-card">
            <template #header>
              <div class="card-header">
                <span>相关资源</span>
                <el-button size="small" text @click="viewAllResources">
                  查看全部
                </el-button>
              </div>
            </template>
            
            <div class="resources-list">
              <div
                v-for="resource in relatedResources"
                :key="resource.id"
                class="resource-item"
                @click="viewResource(resource)"
              >
                <el-icon class="resource-icon"><Document /></el-icon>
                <div class="resource-info">
                  <div class="resource-name">{{ resource.display_name }}</div>
                  <div class="resource-type">{{ resource.resource_type }}</div>
                </div>
              </div>
              
              <div v-if="relatedResources.length === 0" class="empty-resources">
                暂无相关资源
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 测试连接对话框 -->
    <el-dialog
      v-model="testDialogVisible"
      title="测试连接结果"
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
        <el-button type="primary" @click="handleTest" :loading="testing">
          重新测试
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ArrowLeft,
  Edit,
  Delete,
  Connection,
  Refresh,
  CircleCheck,
  CircleClose,
  Warning,
  Document,
  Loading
} from '@element-plus/icons-vue'
import type { Datasource, DatasourceTestResult } from '@/types/datasource'

/**
 * 路由实例
 */
const router = useRouter()
const route = useRoute()

/**
 * 响应式数据
 */
const datasource = ref<Datasource | null>(null)
const connectionHistory = ref<DatasourceTestResult[]>([])
const relatedResources = ref<any[]>([])
const testResult = ref<DatasourceTestResult | null>(null)
const loading = ref(false)
const historyLoading = ref(false)
const testing = ref(false)
const testDialogVisible = ref(false)

/**
 * 统计信息
 */
const stats = reactive({
  total_queries: 0,
  success_rate: 0,
  avg_response_time: 0,
  last_7_days_queries: 0
})

/**
 * 获取数据源详情
 */
const fetchDatasourceDetail = async () => {
  loading.value = true
  
  try {
    const id = route.params.id as string
    
    // TODO: 调用API获取数据源详情
    // const response = await datasourceApi.getDetail(id)
    // datasource.value = response.data
    
    // 模拟数据
    datasource.value = {
      id: parseInt(id),
      name: 'main_mysql',
      display_name: '主数据库',
      description: '主要的MySQL数据库，存储核心业务数据',
      type: 'mysql',
      host: 'localhost',
      port: 3306,
      database: 'acwl_ai',
      username: 'root',
      password: '******',
      connection_status: 'connected',
      connection_timeout: 30,
      query_timeout: 300,
      max_connections: 10,
      ssl_enabled: false,
      last_test_time: '2024-01-01T10:00:00Z',
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
      created_by: 1,
      is_active: true
    }
    
    // 获取统计信息
    await fetchStats()
    
    // 获取相关资源
    await fetchRelatedResources()
  } catch (error) {
    ElMessage.error('获取数据源详情失败')
    router.push('/datasources')
  } finally {
    loading.value = false
  }
}

/**
 * 获取连接历史
 */
const fetchConnectionHistory = async () => {
  historyLoading.value = true
  
  try {
    // TODO: 调用API获取连接历史
    // const response = await datasourceApi.getConnectionHistory(datasource.value!.id!)
    // connectionHistory.value = response.data
    
    // 模拟数据
    connectionHistory.value = [
      {
        success: true,
        response_time: 120,
        test_time: '2024-01-01T10:00:00Z',
        message: '连接正常'
      },
      {
        success: true,
        response_time: 95,
        test_time: '2024-01-01T09:30:00Z',
        message: '连接正常'
      },
      {
        success: false,
        response_time: 0,
        test_time: '2024-01-01T09:00:00Z',
        message: '连接失败',
        error: '连接超时'
      }
    ]
  } catch (error) {
    ElMessage.error('获取连接历史失败')
  } finally {
    historyLoading.value = false
  }
}

/**
 * 获取统计信息
 */
const fetchStats = async () => {
  try {
    // TODO: 调用API获取统计信息
    // const response = await datasourceApi.getStats(datasource.value!.id!)
    // Object.assign(stats, response.data)
    
    // 模拟数据
    Object.assign(stats, {
      total_queries: 1250,
      success_rate: 98.5,
      avg_response_time: 125,
      last_7_days_queries: 89
    })
  } catch (error) {
    console.error('获取统计信息失败:', error)
  }
}

/**
 * 获取相关资源
 */
const fetchRelatedResources = async () => {
  try {
    // TODO: 调用API获取相关资源
    // const response = await datasourceApi.getRelatedResources(datasource.value!.id!)
    // relatedResources.value = response.data
    
    // 模拟数据
    relatedResources.value = [
      {
        id: 1,
        display_name: '用户表',
        resource_type: 'table'
      },
      {
        id: 2,
        display_name: '订单表',
        resource_type: 'table'
      },
      {
        id: 3,
        display_name: '产品表',
        resource_type: 'table'
      }
    ]
  } catch (error) {
    console.error('获取相关资源失败:', error)
  }
}

/**
 * 处理返回
 */
const handleBack = () => {
  router.push('/datasources')
}

/**
 * 处理编辑
 */
const handleEdit = () => {
  router.push(`/datasources/edit/${datasource.value!.id}`)
}

/**
 * 处理删除
 */
const handleDelete = async () => {
  try {
    await ElMessageBox.confirm(
      `确定要删除数据源 "${datasource.value!.display_name}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    // TODO: 调用删除API
    // await datasourceApi.delete(datasource.value!.id!)
    
    ElMessage.success('删除成功')
    router.push('/datasources')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

/**
 * 处理测试连接
 */
const handleTest = async () => {
  testing.value = true
  testResult.value = null
  testDialogVisible.value = true
  
  try {
    // TODO: 调用测试连接API
    // const response = await datasourceApi.testConnection(datasource.value!.id!)
    // testResult.value = response.data
    
    // 模拟测试结果
    await new Promise(resolve => setTimeout(resolve, 2000))
    const success = Math.random() > 0.2 // 80%成功率
    testResult.value = {
      success,
      response_time: Math.floor(Math.random() * 500) + 50,
      test_time: new Date().toISOString(),
      message: success ? '连接正常' : '连接失败',
      error: success ? undefined : '无法连接到数据库服务器'
    }
    
    // 更新数据源状态
    if (datasource.value) {
      datasource.value.connection_status = success ? 'connected' : 'error'
      datasource.value.last_test_time = testResult.value.test_time
    }
    
    // 刷新连接历史
    fetchConnectionHistory()
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
 * 查看所有资源
 */
const viewAllResources = () => {
  router.push(`/data-resources?datasource_id=${datasource.value!.id}`)
}

/**
 * 查看资源详情
 */
const viewResource = (resource: any) => {
  router.push(`/data-resources/detail/${resource.id}`)
}

/**
 * 获取类型标签类型
 */
const getTypeTagType = (type?: string) => {
  const typeMap: Record<string, string> = {
    mysql: 'primary',
    doris: 'success',
    elasticsearch: 'warning',
    clickhouse: 'info'
  }
  return typeMap[type || ''] || 'info'
}

/**
 * 获取类型显示名称
 */
const getTypeDisplayName = (type?: string) => {
  const typeMap: Record<string, string> = {
    mysql: 'MySQL',
    doris: 'Doris',
    elasticsearch: 'Elasticsearch',
    clickhouse: 'ClickHouse'
  }
  return typeMap[type || ''] || type
}

/**
 * 获取状态标签类型
 */
const getStatusTagType = (status?: string) => {
  const statusMap: Record<string, string> = {
    connected: 'success',
    disconnected: 'info',
    error: 'danger'
  }
  return statusMap[status || ''] || 'info'
}

/**
 * 获取状态显示名称
 */
const getStatusDisplayName = (status?: string) => {
  const statusMap: Record<string, string> = {
    connected: '已连接',
    disconnected: '未连接',
    error: '连接错误'
  }
  return statusMap[status || ''] || status
}

/**
 * 获取状态图标类名
 */
const getStatusIconClass = (status?: string) => {
  const statusMap: Record<string, string> = {
    connected: 'success-icon',
    disconnected: 'warning-icon',
    error: 'error-icon'
  }
  return statusMap[status || ''] || 'warning-icon'
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
  fetchDatasourceDetail()
  fetchConnectionHistory()
})
</script>

<style scoped>
.datasource-detail {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-left h1 {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.content-container {
  min-height: 600px;
}

.info-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
}

.status-card {
  margin-bottom: 20px;
}

.status-content {
  text-align: center;
}

.status-indicator {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 20px;
}

.status-text {
  margin-top: 8px;
  font-size: 16px;
  font-weight: 600;
}

.success-icon {
  color: #67c23a;
}

.error-icon {
  color: #f56c6c;
}

.warning-icon {
  color: #e6a23c;
}

.status-details {
  text-align: left;
}

.detail-item {
  margin-bottom: 8px;
}

.label {
  color: #666;
  font-size: 14px;
}

.value {
  font-size: 14px;
}

.stats-card {
  margin-bottom: 20px;
}

.stats-content {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.stat-item {
  text-align: center;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: #409eff;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 12px;
  color: #666;
}

.resources-card {
  margin-bottom: 20px;
}

.resources-list {
  max-height: 300px;
  overflow-y: auto;
}

.resource-item {
  display: flex;
  align-items: center;
  padding: 8px;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.resource-item:hover {
  background-color: #f5f5f5;
}

.resource-icon {
  margin-right: 8px;
  color: #409eff;
}

.resource-info {
  flex: 1;
}

.resource-name {
  font-size: 14px;
  font-weight: 500;
}

.resource-type {
  font-size: 12px;
  color: #666;
}

.empty-resources {
  text-align: center;
  color: #999;
  padding: 20px;
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