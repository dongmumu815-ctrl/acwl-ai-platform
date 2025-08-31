<template>
  <div class="model-service-configs">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-left">
          <h1 class="page-title">
            <el-icon><Setting /></el-icon>
            模型服务配置
          </h1>
          <p class="page-description">管理各种AI服务提供商的接口配置</p>
        </div>
        <div class="header-right">
          <el-button type="primary" @click="showCreateDialog">
            <el-icon><Plus /></el-icon>
            新增配置
          </el-button>
          <el-button @click="refreshData">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-cards">
      <el-row :gutter="20">
        <el-col :xs="12" :sm="6">
          <div class="stat-card">
            <div class="stat-icon total">
              <el-icon><Setting /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats?.total_count || 0 }}</div>
              <div class="stat-label">总配置数</div>
            </div>
          </div>
        </el-col>
        
        <el-col :xs="12" :sm="6">
          <div class="stat-card">
            <div class="stat-icon active">
              <el-icon><Connection /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats?.active_count || 0 }}</div>
              <div class="stat-label">已激活</div>
            </div>
          </div>
        </el-col>
        
        <el-col :xs="12" :sm="6">
          <div class="stat-card">
            <div class="stat-icon inactive">
              <el-icon><Document /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats?.inactive_count || 0 }}</div>
              <div class="stat-label">未激活</div>
            </div>
          </div>
        </el-col>
        
        <el-col :xs="12" :sm="6">
          <div class="stat-card">
            <div class="stat-icon provider">
              <el-icon><Calendar /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ Object.keys(stats?.provider_stats || {}).length }}</div>
              <div class="stat-label">提供商数</div>
            </div>
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- 筛选和搜索 -->
    <div class="filter-section">
      <el-card shadow="never">
        <el-form :model="searchForm" inline>
          <el-form-item label="搜索">
            <el-input
              v-model="searchForm.search"
              placeholder="搜索配置名称或描述"
              clearable
              style="width: 250px"
              @input="handleSearch"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
          </el-form-item>
          
          <el-form-item label="提供商">
            <el-select
              v-model="searchForm.provider"
              placeholder="选择服务提供商"
              clearable
              style="width: 150px"
              @change="handleSearch"
            >
              <el-option label="全部" value="" />
              <el-option
                v-for="provider in providers"
                :key="provider.value"
                :label="provider.label"
                :value="provider.value"
              />
            </el-select>
          </el-form-item>
          
          <el-form-item label="状态">
            <el-select
              v-model="searchForm.is_active"
              placeholder="选择状态"
              clearable
              style="width: 120px"
              @change="handleSearch"
            >
              <el-option label="全部" value="" />
              <el-option label="已激活" :value="true" />
              <el-option label="未激活" :value="false" />
            </el-select>
          </el-form-item>
          
          <el-form-item label="排序">
            <el-select
              v-model="sortConfig.prop"
              style="width: 150px"
              @change="handleSearch"
            >
              <el-option label="创建时间" value="created_at" />
              <el-option label="更新时间" value="updated_at" />
              <el-option label="配置名称" value="name" />
            </el-select>
          </el-form-item>
          
          <el-form-item>
            <el-button @click="resetFilters">
              <el-icon><RefreshLeft /></el-icon>
              重置
            </el-button>
          </el-form-item>
        </el-form>
      </el-card>
    </div>

    <!-- 配置列表 -->
    <div class="configs-list">
      <el-card shadow="never">
        <template #header>
          <div class="card-header">
            <span>配置列表</span>
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
          <el-row :gutter="20">
            <el-col
              v-for="config in configs"
              :key="config.id"
              :xs="24"
              :sm="12"
              :md="8"
              :lg="6"
            >
              <div class="config-card">
                <div class="config-header">
                  <div class="config-avatar">
                    <el-icon><Setting /></el-icon>
                  </div>
                  <div class="config-status">
                    <el-tag
                      :type="config.is_active ? 'success' : 'info'"
                      size="small"
                    >
                      {{ config.is_active ? '已激活' : '未激活' }}
                    </el-tag>
                    <el-tag v-if="config.is_default" type="warning" size="small">
                      默认
                    </el-tag>
                  </div>
                </div>
                
                <div class="config-content">
                  <h3 class="config-name">{{ config.name }}</h3>
                  <p class="config-description">{{ config.display_name }}</p>
                  
                  <div class="config-meta">
                    <div class="meta-item">
                      <el-icon><Calendar /></el-icon>
                      <span>{{ formatDateTime(config.created_at) }}</span>
                    </div>
                    <div class="meta-item">
                      <el-icon><Connection /></el-icon>
                      <span>{{ getProviderDisplayName(config.provider) }}</span>
                    </div>
                    <div class="meta-item">
                      <el-icon><Document /></el-icon>
                      <span>{{ config.model_name }}</span>
                    </div>
                  </div>
                  
                  <div class="config-tags">
                    <el-tag
                      :type="getProviderTagType(config.provider)"
                      size="small"
                      class="tag-item"
                    >
                      {{ getProviderDisplayName(config.provider) }}
                    </el-tag>
                    <el-tag
                      v-if="config.max_tokens"
                      size="small"
                      class="tag-item"
                      type="info"
                    >
                      {{ config.max_tokens }} tokens
                    </el-tag>
                  </div>
                </div>
                
                <div class="config-actions">
                  <el-button
                    size="small"
                    @click="testConfig(config)"
                    :loading="config.testLoading"
                  >
                    测试
                  </el-button>
                  <el-button
                    type="primary"
                    size="small"
                    @click="editConfig(config)"
                  >
                    编辑
                  </el-button>
                  <el-dropdown trigger="click">
                    <el-button size="small" text>
                      <el-icon><MoreFilled /></el-icon>
                    </el-button>
                    <template #dropdown>
                      <el-dropdown-menu>
                        <el-dropdown-item @click="editConfig(config)">
                          <el-icon><Edit /></el-icon>
                          编辑
                        </el-dropdown-item>
                        <el-dropdown-item @click="cloneConfig(config)">
                          <el-icon><CopyDocument /></el-icon>
                          克隆
                        </el-dropdown-item>
                        <el-dropdown-item
                          divided
                          @click="deleteConfig(config)"
                        >
                          <el-icon><Delete /></el-icon>
                          删除
                        </el-dropdown-item>
                      </el-dropdown-menu>
                    </template>
                  </el-dropdown>
                </div>
              </div>
            </el-col>
          </el-row>
        </div>
        
        <!-- 列表视图 -->
        <div v-else class="list-view">
          <el-table
            :data="configs"
            v-loading="loading"
            style="width: 100%"
            @sort-change="handleSortChange"
          >
            <el-table-column prop="name" label="配置名称" sortable="custom">
              <template #default="{ row }">
                <div class="config-name-cell">
                  <div class="config-avatar-small">
                    <el-icon><Setting /></el-icon>
                  </div>
                  <div class="config-info">
                    <div class="name">{{ row.name }}</div>
                    <div class="description">{{ row.display_name }}</div>
                  </div>
                </div>
              </template>
            </el-table-column>
            
            <el-table-column prop="provider" label="服务提供商" width="120">
              <template #default="{ row }">
                <el-tag :type="getProviderTagType(row.provider)" size="small">
                  {{ getProviderDisplayName(row.provider) }}
                </el-tag>
              </template>
            </el-table-column>
            
            <el-table-column prop="model_name" label="模型名称" width="150" show-overflow-tooltip />
            
            <el-table-column prop="api_endpoint" label="API端点" min-width="200" show-overflow-tooltip />
            
            <el-table-column prop="max_tokens" label="最大Token" width="100" align="center" />
            
            <el-table-column prop="temperature" label="温度" width="80" align="center" />
            
            <el-table-column prop="is_active" label="状态" width="100" align="center">
              <template #default="{ row }">
                <div class="status-cell">
                  <el-tag
                    :type="row.is_active ? 'success' : 'info'"
                    size="small"
                  >
                    {{ row.is_active ? '已激活' : '未激活' }}
                  </el-tag>
                  <el-tag v-if="row.is_default" type="warning" size="small">
                    默认
                  </el-tag>
                </div>
              </template>
            </el-table-column>
            
            <el-table-column prop="created_at" label="创建时间" width="150" sortable="custom">
              <template #default="{ row }">
                {{ formatDateTime(row.created_at) }}
              </template>
            </el-table-column>
            
            <el-table-column label="操作" width="200" fixed="right">
              <template #default="{ row }">
                <el-button size="small" @click="testConfig(row)" :loading="row.testLoading">
                  测试
                </el-button>
                <el-button
                  type="primary"
                  size="small"
                  @click="editConfig(row)"
                >
                  编辑
                </el-button>
                <el-dropdown trigger="click">
                  <el-button size="small" text>
                    <el-icon><MoreFilled /></el-icon>
                  </el-button>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item @click="editConfig(row)">
                        <el-icon><Edit /></el-icon>
                        编辑
                      </el-dropdown-item>
                      <el-dropdown-item @click="cloneConfig(row)">
                        <el-icon><CopyDocument /></el-icon>
                        克隆
                      </el-dropdown-item>
                      <el-dropdown-item
                        divided
                        @click="deleteConfig(row)"
                      >
                        <el-icon><Delete /></el-icon>
                        删除
                      </el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </template>
            </el-table-column>
          </el-table>
        </div>
        
        <!-- 分页 -->
        <div class="pagination-wrapper">
          <el-pagination
            v-model:current-page="pagination.page"
            v-model:page-size="pagination.size"
            :page-sizes="[10, 20, 50, 100]"
            :total="pagination.total"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="handleSizeChange"
            @current-change="handlePageChange"
          />
        </div>
      </el-card>
    </div>

    <!-- 创建/编辑对话框 -->
    <ModelServiceConfigDialog
      v-model="dialogVisible"
      :config="currentConfig"
      :providers="providers"
      :existing-configs="configs"
      @success="handleDialogSuccess"
    />

    <!-- 测试结果对话框 -->
    <TestResultDialog
      v-model="testDialogVisible"
      :result="testResult"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Plus, 
  Refresh, 
  Search,
  RefreshLeft,
  Setting,
  Calendar,
  Connection,
  Document,
  Grid,
  List,
  MoreFilled,
  Edit,
  Delete,
  CopyDocument
} from '@element-plus/icons-vue'
import { modelServiceConfigApi } from '@/api/model-service-configs'
import ModelServiceConfigDialog from './components/ModelServiceConfigDialog.vue'
import TestResultDialog from './components/TestResultDialog.vue'
import { formatDateTime } from '@/utils/date'

// 响应式数据
const loading = ref(false)
const configs = ref([])
const providers = ref([])
const stats = ref(null)
const dialogVisible = ref(false)
const testDialogVisible = ref(false)
const currentConfig = ref(null)
const testResult = ref(null)
const viewMode = ref('grid')

// 搜索表单
const searchForm = reactive({
  search: '',
  provider: '',
  is_active: null
})

// 分页
const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

// 排序
const sortConfig = reactive({
  prop: 'created_at',
  order: 'desc'
})

/**
 * 获取配置列表
 */
const fetchConfigs = async () => {
  try {
    loading.value = true
    const params = {
      page: pagination.page,
      size: pagination.size,
      search: searchForm.search || undefined,
      provider: searchForm.provider || undefined,
      is_active: searchForm.is_active
    }
    
    const response = await modelServiceConfigApi.getConfigs(params)
    configs.value = response.items.map(config => ({
      ...config,
      statusLoading: false,
      testLoading: false
    }))
    pagination.total = response.total
  } catch (error) {
    ElMessage.error('获取配置列表失败')
    console.error('获取配置列表失败:', error)
  } finally {
    loading.value = false
  }
}

/**
 * 获取统计信息
 */
const fetchStats = async () => {
  try {
    stats.value = await modelServiceConfigApi.getStats()
  } catch (error) {
    console.error('获取统计信息失败:', error)
  }
}

/**
 * 获取支持的提供商列表
 */
const fetchProviders = async () => {
  try {
    providers.value = await modelServiceConfigApi.getProviders()
  } catch (error) {
    console.error('获取提供商列表失败:', error)
  }
}

/**
 * 刷新数据
 */
const refreshData = async () => {
  await Promise.all([
    fetchConfigs(),
    fetchStats(),
    fetchProviders()
  ])
}

/**
 * 重置筛选条件
 */
const resetFilters = () => {
  searchForm.search = ''
  searchForm.provider = ''
  searchForm.is_active = null
  sortConfig.prop = 'created_at'
  sortConfig.order = 'desc'
  pagination.page = 1
  fetchConfigs()
}

/**
 * 搜索处理
 */
const handleSearch = () => {
  pagination.page = 1
  fetchConfigs()
}

/**
 * 分页大小变化
 */
const handleSizeChange = (size: number) => {
  pagination.size = size
  pagination.page = 1
  fetchConfigs()
}

/**
 * 页码变化
 */
const handlePageChange = (page: number) => {
  pagination.page = page
  fetchConfigs()
}

/**
 * 排序变化
 */
const handleSortChange = ({ prop, order }) => {
  sortConfig.prop = prop
  sortConfig.order = order
  fetchConfigs()
}

/**
 * 显示创建对话框
 */
const showCreateDialog = () => {
  currentConfig.value = null
  dialogVisible.value = true
}

/**
 * 编辑配置
 */
const editConfig = (config) => {
  currentConfig.value = { ...config }
  dialogVisible.value = true
}

/**
 * 对话框成功回调
 */
const handleDialogSuccess = () => {
  dialogVisible.value = false
  refreshData()
}

/**
 * 切换状态
 */
const toggleStatus = async (config) => {
  try {
    config.statusLoading = true
    await modelServiceConfigApi.toggleStatus(config.id, config.is_active)
    ElMessage.success('状态更新成功')
    await fetchStats() // 更新统计信息
  } catch (error) {
    // 恢复原状态
    config.is_active = !config.is_active
    ElMessage.error('状态更新失败')
    console.error('状态更新失败:', error)
  } finally {
    config.statusLoading = false
  }
}

/**
 * 测试配置
 */
const testConfig = async (config) => {
  try {
    config.testLoading = true
    testResult.value = await modelServiceConfigApi.testConfig({
      config_id: config.id,
      test_message: 'Hello, this is a test message.'
    })
    testDialogVisible.value = true
  } catch (error) {
    ElMessage.error('测试失败')
    console.error('测试失败:', error)
  } finally {
    config.testLoading = false
  }
}

/**
 * 克隆配置
 */
const cloneConfig = async (config) => {
  try {
    // 确认克隆操作
    await ElMessageBox.confirm(
      `确定要克隆配置 "${config.display_name || config.name}" 吗？\n克隆后将创建一个新的配置副本，您可以修改其参数。`,
      '确认克隆',
      {
        confirmButtonText: '确定克隆',
        cancelButtonText: '取消',
        type: 'info',
        dangerouslyUseHTMLString: false
      }
    )
    
    // 生成唯一的克隆名称
    const generateCloneName = (originalName) => {
      const existingNames = configs.value.map(c => c.name)
      
      // 优先尝试添加数字后缀的方式
      let cloneName = `${originalName}_2`
      let counter = 2
      
      // 如果名称已存在，递增数字后缀
      while (existingNames.includes(cloneName)) {
        counter++
        cloneName = `${originalName}_${counter}`
      }
      
      return cloneName
    }
    
    // 深度复制配置对象，排除不需要的字段
    const clonedConfig = {
      ...JSON.parse(JSON.stringify(config)),
      // 清除ID相关字段
      id: undefined,
      // 生成新的配置名称
      name: generateCloneName(config.name),
      // 生成新的显示名称，保持与配置名称一致
      display_name: generateCloneName(config.name),
      // 克隆的配置默认不是默认配置
      is_default: false,
      // 克隆的配置默认激活
      is_active: true,
      // 保持原有描述或生成简洁描述
      description: config.description || `基于 ${config.name} 的配置`,
      // 清除时间戳字段
      created_at: undefined,
      updated_at: undefined,
      created_by: undefined,
      updated_by: undefined
    }
    
    // 直接保存克隆的配置
    await modelServiceConfigApi.createConfig(clonedConfig)
    ElMessage.success('配置克隆成功')
    
    // 刷新配置列表
    await refreshData()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('克隆配置失败:', error)
      ElMessage.error('克隆配置失败，请稍后重试')
    }
  }
}

/**
 * 删除配置
 */
const deleteConfig = async (config) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除配置 "${config.name}" 吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await modelServiceConfigApi.deleteConfig(config.id)
    ElMessage.success('删除成功')
    await refreshData()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
      console.error('删除失败:', error)
    }
  }
}

/**
 * 获取提供商标签类型
 */
const getProviderTagType = (provider: string) => {
  const typeMap = {
    openai: 'primary',
    azure: 'success',
    anthropic: 'warning',
    google: 'danger',
    baidu: 'info',
    alibaba: 'success',
    tencent: 'primary',
    local: 'info',
    claude: 'success',
    qwen: 'warning',
    doubao: 'info',
    gemini: 'danger',
    ollama: '',
    vllm: '',
    custom: 'info'
  }
  return typeMap[provider] || 'info'
}

/**
 * 获取提供商显示名称
 */
const getProviderDisplayName = (provider: string) => {
  const nameMap = {
    openai: 'OpenAI',
    azure: 'Azure OpenAI',
    anthropic: 'Anthropic',
    google: 'Google',
    baidu: '百度',
    alibaba: '阿里云',
    tencent: '腾讯云',
    local: '本地部署',
    claude: 'Claude',
    qwen: '通义千问',
    doubao: '豆包',
    gemini: 'Gemini',
    ollama: 'Ollama',
    vllm: 'vLLM',
    custom: '自定义'
  }
  const provider_obj = providers.value.find(p => p.value === provider)
  return provider_obj?.label || nameMap[provider] || provider
}

/**
 * 获取状态标签类型
 */
const getStatusTagType = (isActive: boolean) => {
  return isActive ? 'success' : 'info'
}

/**
 * 获取状态显示文本
 */
const getStatusText = (isActive: boolean) => {
  return isActive ? '已激活' : '未激活'
}

// 组件挂载时获取数据
onMounted(() => {
  refreshData()
})
</script>

<style scoped>
.model-service-configs {
  padding: 20px;
  background-color: #f5f7fa;
  min-height: calc(100vh - 60px);
}

/* 页面头部 */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 0 4px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.page-icon {
  width: 32px;
  height: 32px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 16px;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.page-description {
  font-size: 14px;
  color: #6b7280;
  margin: 0;
}

.header-right {
  display: flex;
  gap: 12px;
}

/* 筛选卡片 */
.filter-section {
  margin-bottom: 20px;
  
  :deep(.el-card__body) {
    padding: 16px 20px;
  }
}



/* 统计卡片 */
.stats-cards {
  margin-bottom: 24px;
}

.stat-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 16px;
  height: 100px;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  color: white;
  flex-shrink: 0;
}

.stat-icon.total {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.stat-icon.active {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.stat-icon.inactive {
  background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
}

.stat-icon.provider {
  background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
  color: #333;
}

.stat-content {
  flex: 1;
  text-align: left;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: #1f2937;
  margin-bottom: 4px;
  line-height: 1;
}

.stat-label {
  font-size: 14px;
  color: #6b7280;
  font-weight: 500;
}

/* 配置列表卡片 */
.configs-list .el-card {
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 网格视图 */
.grid-view {
  padding: 20px;
}

.config-card {
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 20px;
  background: white;
  transition: all 0.3s ease;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.config-card:hover {
  border-color: #3b82f6;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15);
  transform: translateY(-2px);
}

.config-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.config-avatar {
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 20px;
  flex-shrink: 0;
}

.config-status {
  display: flex;
  flex-direction: column;
  gap: 4px;
  align-items: flex-end;
}

.config-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.config-name {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 4px 0;
  word-break: break-word;
}

.config-description {
  font-size: 14px;
  color: #6b7280;
  margin: 0;
  word-break: break-word;
}

.config-meta {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #6b7280;
}

.config-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 8px;
}

.tag-item {
  margin-right: 0 !important;
}

.config-actions {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #f3f4f6;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}

/* 列表视图 */
.list-view {
  padding: 0;
}

.config-name-cell {
  display: flex;
  align-items: center;
  gap: 12px;
}

.config-avatar-small {
  width: 32px;
  height: 32px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 14px;
  flex-shrink: 0;
}

.config-info {
  flex: 1;
  min-width: 0;
}

.config-info .name {
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
  word-break: break-word;
}

.config-info .description {
  font-size: 12px;
  color: #6b7280;
  margin: 2px 0 0 0;
  word-break: break-word;
}

.status-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
  align-items: center;
}

/* 分页 */
.pagination-wrapper {
  display: flex;
  justify-content: center;
  padding: 20px;
  background: white;
  border-top: 1px solid #e5e7eb;
}

/* Element Plus 样式覆盖 */
:deep(.el-table) {
  border-radius: 0;
}

:deep(.el-table th) {
  background-color: #fafafa;
  color: #606266;
  font-weight: 600;
}

:deep(.el-table td) {
  padding: 12px 0;
}

:deep(.el-button + .el-button) {
  margin-left: 8px;
}

:deep(.el-card__body) {
  padding: 0;
}

:deep(.el-card__header) {
  padding: 16px 20px;
  border-bottom: 1px solid #e5e7eb;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .model-service-configs {
    padding: 16px;
  }
  
  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }
  
  .header-content {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }
  
  .header-right {
    width: 100%;
    justify-content: flex-end;
  }
  
  .filter-form {
    flex-direction: column;
    align-items: stretch;
  }
  
  .filter-actions {
    margin-left: 0;
    justify-content: flex-end;
  }
  
  .card-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  
  .header-actions {
    align-self: flex-end;
  }
  
  .config-card {
    padding: 16px;
  }
  
  .config-header {
    gap: 8px;
  }
  
  .config-avatar {
    width: 40px;
    height: 40px;
    font-size: 16px;
  }
  
  .config-actions {
    flex-wrap: wrap;
  }
  
  .stats-cards :deep(.el-col) {
    margin-bottom: 16px;
  }
}

/* 暗色主题支持 */
@media (prefers-color-scheme: dark) {
  .model-service-configs {
    background-color: #111827;
  }
  
  .page-title {
    color: #f9fafb;
  }
  
  .page-description {
    color: #9ca3af;
  }
  
  .config-card {
    background: #1f2937;
    border-color: #374151;
  }
  
  .config-card:hover {
    border-color: #60a5fa;
    box-shadow: 0 4px 12px rgba(96, 165, 250, 0.25);
  }
  
  .config-name {
    color: #f9fafb;
  }
  
  .config-description {
    color: #9ca3af;
  }
  
  .config-actions {
    border-top-color: #374151;
  }
  
  .config-info .name {
    color: #f9fafb;
  }
  
  .config-info .description {
    color: #9ca3af;
  }
}
</style>