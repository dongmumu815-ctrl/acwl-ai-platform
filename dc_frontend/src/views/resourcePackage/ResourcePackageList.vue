<template>
  <div class="resource-package-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-left">
          <h1 class="page-title">
            <el-icon><Box /></el-icon>
            资源包管理
          </h1>
          <p class="page-description">管理和配置数据查询资源包，支持SQL和Elasticsearch查询</p>
        </div>
        <div class="header-right">
          <el-button type="primary" @click="handleCreate">
            <el-icon><Plus /></el-icon>
            创建资源包
          </el-button>
          <el-button @click="refreshPackages">
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
              <el-icon><Box /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.total }}</div>
              <div class="stat-label">总资源包</div>
            </div>
          </div>
        </el-col>
        
        <el-col :xs="12" :sm="6">
          <div class="stat-card">
            <div class="stat-icon active">
              <el-icon><CircleCheck /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.active }}</div>
              <div class="stat-label">启用中</div>
            </div>
          </div>
        </el-col>
        
        <el-col :xs="12" :sm="6">
          <div class="stat-card">
            <div class="stat-icon sql">
              <el-icon><Coin /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.sqlCount }}</div>
              <div class="stat-label">SQL类型</div>
            </div>
          </div>
        </el-col>
        
        <el-col :xs="12" :sm="6">
          <div class="stat-card">
            <div class="stat-icon elasticsearch">
              <el-icon><Search /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.elasticsearchCount }}</div>
              <div class="stat-label">ES类型</div>
            </div>
          </div>
        </el-col>
      </el-row>
    </div>
    
    <!-- 筛选和搜索 -->
    <div class="filter-section">
      <el-card shadow="never">
        <el-form :model="filters" inline>
          <el-form-item label="搜索">
            <el-input
              v-model="filters.search"
              placeholder="搜索资源包名称或描述"
              clearable
              style="width: 250px"
              @input="handleSearch"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
          </el-form-item>
          
          <el-form-item label="类型">
            <el-select
              v-model="filters.type"
              placeholder="选择类型"
              clearable
              style="width: 150px"
              @change="handleFilter"
            >
              <el-option label="全部" value="" />
              <el-option label="SQL" value="sql" />
              <el-option label="Elasticsearch" value="elasticsearch" />
            </el-select>
          </el-form-item>
          
          <el-form-item label="数据源">
            <el-select
              v-model="filters.datasource_id"
              placeholder="选择数据源"
              clearable
              style="width: 150px"
              @change="handleFilter"
            >
              <el-option label="全部" value="" />
              <el-option
                v-for="ds in datasources"
                :key="ds.id"
                :label="ds.name"
                :value="ds.id"
              />
            </el-select>
          </el-form-item>
          
          <el-form-item label="状态">
            <el-select
              v-model="filters.status"
              placeholder="选择状态"
              clearable
              style="width: 120px"
              @change="handleFilter"
            >
              <el-option label="全部" value="" />
              <el-option label="启用" value="true" />
              <el-option label="禁用" value="false" />
            </el-select>
          </el-form-item>
          
          <el-form-item label="排序">
            <el-select
              v-model="filters.sortBy"
              style="width: 150px"
              @change="handleSort"
            >
              <el-option label="创建时间" value="created_at" />
              <el-option label="更新时间" value="updated_at" />
              <el-option label="名称" value="name" />
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
    
    <!-- 资源包列表 -->
    <div class="packages-list">
      <el-card shadow="never">
        <template #header>
          <div class="card-header">
            <span>资源包列表</span>
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
              v-for="pkg in paginatedPackages"
              :key="pkg.id"
              :xs="24"
              :sm="12"
              :md="8"
              :lg="6"
            >
              <div class="package-card">
                <div class="package-header">
                  <div class="package-type">
                    <el-icon class="type-icon">
                      <component :is="getTypeIcon(pkg.type)" />
                    </el-icon>
                  </div>
                  <div class="package-status">
                    <el-tag
                      :type="getStatusType(pkg.is_active)"
                      size="small"
                    >
                      {{ pkg.is_active ? '启用' : '禁用' }}
                    </el-tag>
                  </div>
                </div>
                
                <div class="package-content">
                  <h3 class="package-name">{{ pkg.name }}</h3>
                  <p class="package-description">{{ pkg.description || '暂无描述' }}</p>
                  
                  <div class="package-meta">
                    <div class="meta-item">
                      <el-icon><Calendar /></el-icon>
                      <span>{{ formatDate(pkg.created_at) }}</span>
                    </div>
                    <div class="meta-item">
                      <el-icon><Coin /></el-icon>
                      <span>{{ getDatasourceName(pkg.datasource_id) }}</span>
                    </div>
                    <div class="meta-item">
                      <el-icon><Setting /></el-icon>
                      <span>{{ pkg.template_type || '未知' }} 模板</span>
                    </div>
                  </div>
                  
                  <div class="package-tags" v-if="pkg.tags && pkg.tags.length > 0">
                    <el-tag
                      v-for="tag in pkg.tags.slice(0, 3)"
                      :key="tag.id"
                      size="small"
                      class="tag-item"
                      :color="tag.tag_color"
                    >
                      {{ tag.tag_name }}
                    </el-tag>
                    <el-tag v-if="pkg.tags.length > 3" size="small" type="info" class="tag-item">
                      +{{ pkg.tags.length - 3 }}
                    </el-tag>
                  </div>
                  
                  <!-- 模板预览 -->
                  <div class="package-preview" v-if="pkg.template_id">
                    <div class="preview-label">模板信息:</div>
                    <div class="preview-content">
                      <div class="condition-info">
                        <el-text type="primary" size="small">模板名称: {{ pkg.name }}</el-text>
                      </div>
                      <!-- <div class="condition-info" v-if="pkg.dynamic_params && Object.keys(pkg.dynamic_params).length > 0">
                        <el-text type="success" size="small">参数: {{ Object.keys(pkg.dynamic_params).length }}</el-text>
                      </div> -->
                    </div>
                  </div>
                </div>
                
                <div class="package-actions">
                  <el-button
                    size="small"
                    @click="handleView(pkg)"
                  >
                    API
                  </el-button>
                  <el-button
                    v-if="pkg.is_active"
                    type="primary"
                    size="small"
                    @click="handleQuery(pkg)"
                  >
                    查询
                  </el-button>
                  <el-dropdown trigger="click">
                    <el-button size="small" text>
                      <el-icon><MoreFilled /></el-icon>
                    </el-button>
                    <template #dropdown>
                      <el-dropdown-menu>
                        <el-dropdown-item @click="handleEdit(pkg)">
                          <el-icon><Edit /></el-icon>
                          编辑
                        </el-dropdown-item>
                        <el-dropdown-item @click="handleClone(pkg)">
                          <el-icon><CopyDocument /></el-icon>
                          克隆
                        </el-dropdown-item>
                        <el-dropdown-item
                          divided
                          @click="handleDelete(pkg)"
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
            v-loading="loading"
            :data="paginatedPackages"
            style="width: 100%"
            @sort-change="handleTableSort"
          >
            <el-table-column prop="name" label="资源包名称" min-width="200" sortable>
              <template #default="{ row }">
                <div class="package-name-cell">
                  <div class="package-type-icon">
                    <el-icon>
                      <component :is="getTypeIcon(row.type)" />
                    </el-icon>
                  </div>
                  <div class="package-info">
                    <div class="name">
                      <el-link type="primary" @click="handleView(row)">
                        {{ row.name }}
                      </el-link>
                    </div>
                    <div class="description">{{ row.description || '暂无描述' }}</div>
                  </div>
                </div>
              </template>
            </el-table-column>
            
            <el-table-column prop="type" label="类型" width="120">
              <template #default="{ row }">
                <el-tag :type="row.type === 'sql' ? 'primary' : 'success'">
                  {{ row.type === 'sql' ? 'SQL' : 'Elasticsearch' }}
                </el-tag>
              </template>
            </el-table-column>
            
            <el-table-column label="数据源" width="150">
              <template #default="{ row }">
                {{ getDatasourceName(row.datasource_id) }}
              </template>
            </el-table-column>
            
            <el-table-column label="模板信息" width="120">
              <template #default="{ row }">
                <div class="condition-info">
                  <div>
                    <el-text type="primary" size="small">{{ row.template_type || '未知' }}</el-text>
                  </div>
                  <div v-if="row.template_id">
                    <el-text type="info" size="small">ID: {{ row.template_id }}</el-text>
                  </div>
                </div>
              </template>
            </el-table-column>
            
            <el-table-column label="标签" width="200">
              <template #default="{ row }">
                <div class="package-tags" v-if="row.tags && row.tags.length > 0">
                  <el-tag
                    v-for="tag in row.tags.slice(0, 3)"
                    :key="tag.id"
                    size="small"
                    :color="tag.tag_color"
                    style="margin-right: 4px; margin-top: 4px"
                  >
                    {{ tag.tag_name }}
                  </el-tag>
                  <el-tag v-if="row.tags.length > 3" size="small" type="info" style="margin-top: 4px">
                    +{{ row.tags.length - 3 }}
                  </el-tag>
                </div>
              </template>
            </el-table-column>
            
            <el-table-column prop="is_active" label="状态" width="80">
              <template #default="{ row }">
                <el-tag :type="getStatusType(row.is_active)">
                  {{ row.is_active ? '启用' : '禁用' }}
                </el-tag>
              </template>
            </el-table-column>
            
            <el-table-column prop="created_at" label="创建时间" width="160" sortable>
              <template #default="{ row }">
                {{ formatDate(row.created_at) }}
              </template>
            </el-table-column>
            
            <el-table-column label="操作" width="240" fixed="right">
              <template #default="{ row }">
                <div class="action-buttons">
                  <el-button type="primary" size="small" @click="handleQuery(row)">
                    <el-icon><Search /></el-icon>
                    查询
                  </el-button>
                  <el-button type="warning" size="small" @click="handleEdit(row)">
                    <el-icon><Setting /></el-icon>
                    设定
                  </el-button>
                  <el-popconfirm
                    title="确定要删除这个资源包吗？"
                    @confirm="handleDelete(row)"
                  >
                    <template #reference>
                      <el-button type="danger" size="small">
                        <el-icon><Delete /></el-icon>
                        删除
                      </el-button>
                    </template>
                  </el-popconfirm>
                </div>
              </template>
            </el-table-column>
          </el-table>
        </div>
        
        <!-- 分页 -->
        <div class="pagination-wrapper">
          <el-pagination
            v-model:current-page="pagination.currentPage"
            v-model:page-size="pagination.pageSize"
            :page-sizes="[10, 20, 50, 100]"
            :total="pagination.total"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="handleSizeChange"
            @current-change="handleCurrentChange"
          />
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Box,
  Plus,
  Refresh,
  CircleCheck,
  Search,
  RefreshLeft,
  Grid,
  List,
  Calendar,
  Setting,
  MoreFilled,
  Edit,
  CopyDocument,
  Delete,
  View,
  Coin
} from '@element-plus/icons-vue'
import { resourcePackageApi, type ResourcePackage, type ResourcePackageSearchRequest } from '@/api/resourcePackage'
import { formatDate } from '@/utils/date'

// 定义数据源接口
interface Datasource {
  id: number
  name: string
  type: string
  description?: string
  host: string
  port: number
  database?: string
  username: string
  is_active: boolean
  created_at: string
  updated_at: string
}

// 路由
const router = useRouter()

// 响应式数据
const loading = ref(false)
const packageList = ref<ResourcePackage[]>([])
const datasources = ref<Datasource[]>([])
const viewMode = ref('grid')

// 搜索和筛选
const filters = reactive({
  search: '',
  type: '',
  datasource_id: '',
  status: '',
  sortBy: 'created_at'
})

// 分页信息
const pagination = reactive({
  currentPage: 1,
  pageSize: 20,
  total: 0
})

// 统计数据
const stats = reactive({
  total: 0,
  active: 0,
  sqlCount: 0,
  elasticsearchCount: 0
})

// 计算属性
const getDatasourceName = computed(() => {
  return (datasourceId: number) => {
    const ds = datasources.value.find((d: Datasource) => d.id === datasourceId)
    return ds ? ds.name : '数据源'
  }
})

/**
 * 过滤后的资源包列表
 */
const filteredPackages = computed(() => {
  let result = packageList.value

  // 搜索过滤
  if (filters.search) {
    const keyword = filters.search.toLowerCase()
    result = result.filter(pkg => 
      pkg.name.toLowerCase().includes(keyword) ||
      (pkg.description && pkg.description.toLowerCase().includes(keyword))
    )
  }

  // 类型过滤
  if (filters.type) {
    result = result.filter(pkg => pkg.type === filters.type)
  }

  // 数据源过滤
  if (filters.datasource_id) {
    result = result.filter(pkg => pkg.datasource_id === Number(filters.datasource_id))
  }

  // 状态过滤
  if (filters.status) {
    const isActive = filters.status === 'true'
    result = result.filter(pkg => pkg.is_active === isActive)
  }

  // 排序
  result.sort((a, b) => {
    const field = filters.sortBy as keyof ResourcePackage
    const aValue = a[field]
    const bValue = b[field]
    
    if (typeof aValue === 'string' && typeof bValue === 'string') {
      return bValue.localeCompare(aValue) // 降序
    }
    
    return 0
  })

  return result
})

/**
 * 分页后的资源包列表
 */
const paginatedPackages = computed(() => {
  const start = (pagination.currentPage - 1) * pagination.pageSize
  const end = start + pagination.pageSize
  return filteredPackages.value.slice(start, end)
})

// 方法

/**
 * 获取类型图标
 */
const getTypeIcon = (type: string) => {
  return type === 'sql' ? Coin : Search
}

/**
 * 获取状态类型
 */
const getStatusType = (isActive: boolean): 'success' | 'danger' => {
  return isActive ? 'success' : 'danger'
}

/**
 * 加载资源包列表
 */
const loadPackages = async () => {
  try {
    loading.value = true
    
    const searchParams: ResourcePackageSearchRequest = {
      keyword: filters.search || undefined,
      type: filters.type as any || undefined,
      datasource_id: filters.datasource_id ? Number(filters.datasource_id) : undefined,
      is_active: filters.status ? filters.status === 'true' : undefined,
      page: pagination.currentPage,
      size: Math.min(pagination.pageSize, 100), // 后端限制最大为100
      sort_by: 'created_at',
      sort_order: 'desc'
    }
    
    const res = await resourcePackageApi.search(searchParams)
    console.log('搜索资源包响应:', res)
    packageList.value = res.data?.items || []
    pagination.total = res.data?.total || 0 // 更新总数
    
    // 更新统计数据
    updateStats()
    
  } catch (error) {
    console.error('加载资源包列表失败:', error)
    ElMessage.error('加载资源包列表失败')
  } finally {
    loading.value = false
  }
}

/**
 * 加载数据源列表
 */
const loadDatasources = async () => {
  try {
    // 模拟数据源API调用
    // const response = await datasourceApi.getDataSourceList()
    // datasources.value = response.data?.items || []
    
    // 临时使用模拟数据
    datasources.value = [
      { id: 1, name: 'MySQL主库', type: 'mysql', host: 'localhost', port: 3306, username: 'root', is_active: true, created_at: '2024-01-01', updated_at: '2024-01-01' },
      { id: 2, name: 'Elasticsearch集群', type: 'elasticsearch', host: 'localhost', port: 9200, username: 'elastic', is_active: true, created_at: '2024-01-01', updated_at: '2024-01-01' }
    ]
  } catch (error) {
    console.error('加载数据源列表失败:', error)
  }
}

/**
 * 更新统计数据
 */
const updateStats = () => {
  stats.total = packageList.value.length
  stats.active = packageList.value.filter(pkg => pkg.is_active).length
  stats.sqlCount = packageList.value.filter(pkg => pkg.type === 'sql').length
  stats.elasticsearchCount = packageList.value.filter(pkg => pkg.type === 'elasticsearch').length
}

/**
 * 刷新资源包列表
 */
const refreshPackages = () => {
  loadPackages()
}

/**
 * 搜索处理
 */
const handleSearch = () => {
  pagination.currentPage = 1
  loadPackages() // 重新加载数据
}

/**
 * 筛选处理
 */
const handleFilter = () => {
  pagination.currentPage = 1
  loadPackages() // 重新加载数据
}

/**
 * 排序处理
 */
const handleSort = () => {
  pagination.currentPage = 1
  loadPackages() // 重新加载数据
}

/**
 * 重置筛选条件
 */
const resetFilters = () => {
  Object.assign(filters, {
    search: '',
    type: '',
    datasource_id: '',
    status: '',
    sortBy: 'created_at'
  })
  pagination.currentPage = 1
  loadPackages() // 重新加载数据
}

/**
 * 表格排序处理
 */
const handleTableSort = ({ prop, order }: { prop: string; order: string }) => {
  filters.sortBy = prop
  // 这里可以根据 order 调整排序方向
}

/**
 * 创建资源包
 */
const handleCreate = () => {
  // 跳转到创建页面或打开创建对话框
  router.push('/data-resources/packages/create')
}

/**
 * 编辑资源包 - 跳转到数据查询页面
 */
const handleEdit = (row: ResourcePackage) => {
  // 构建查询页面的URL参数
  const queryParams: Record<string, any> = {
    datasourceType: row.type === 'sql' ? 'mysql' : 'elasticsearch',
    templateId: row.template_id,
    templateType: row.template_type
  }
  
  // 跳转到资源包查询页面
  router.push({
    path: `/resource-packages/query/${row.id}`,
    query: queryParams
  })
}

/**
 * 查看资源包详情
 */
const handleView = (row: ResourcePackage) => {
  // 可以跳转到详情页面或打开详情对话框
  ElMessage.info('正在努力开发中...')
  console.log('查看资源包:', row)
}

/**
 * 跳转到资源包查询页面
 */
const handleQuery = (row: ResourcePackage) => {
  router.push(`/data-resources/packages/${row.id}/query`)
}

/**
 * 克隆资源包
 */
const handleClone = (row: ResourcePackage) => {
  ElMessage.info('克隆功能开发中...')
}

/**
 * 删除资源包
 */
const handleDelete = async (row: ResourcePackage) => {
  try {
    await resourcePackageApi.delete(row.id)
    ElMessage.success('删除成功')
    loadPackages()
  } catch (error) {
    console.error('删除失败:', error)
    ElMessage.error('删除失败')
  }
}

/**
 * 分页大小变化处理
 */
const handleSizeChange = (size: number) => {
  pagination.pageSize = size
  pagination.currentPage = 1
  loadPackages() // 重新加载数据
}

/**
 * 当前页变化处理
 */
const handleCurrentChange = (page: number) => {
  pagination.currentPage = page
  loadPackages() // 重新加载数据
}

// 生命周期
onMounted(() => {
  loadDatasources()
  loadPackages()
})
</script>

<style scoped>
.resource-package-page {
  padding: 20px;
  background-color: #f5f7fa;
  min-height: 100vh;
}

/* 页面头部 */
.page-header {
  margin-bottom: 24px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.header-left {
  flex: 1;
}

.page-title {
  margin: 0 0 8px 0;
  color: #303133;
  font-size: 28px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 12px;
}

.page-description {
  margin: 0;
  color: #606266;
  font-size: 14px;
  line-height: 1.5;
}

.header-right {
  display: flex;
  gap: 12px;
}

/* 统计卡片 */
.stats-cards {
  margin-bottom: 24px;
}

.stat-card {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
  border: 1px solid #ebeef5;
  display: flex;
  align-items: center;
  gap: 16px;
  transition: all 0.3s ease;
}

.stat-card:hover {
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  transform: translateY(-2px);
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

.stat-icon.active {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.stat-icon.sql {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.stat-icon.elasticsearch {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
  color: #303133;
  line-height: 1;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  font-weight: 500;
}

/* 筛选区域 */
.filter-section {
  margin-bottom: 24px;
}

/* 资源包列表 */
.packages-list {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
  color: #303133;
}

.header-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

/* 网格视图 */
.grid-view {
  margin-top: 20px;
}

.package-card {
  background: white;
  border-radius: 12px;
  border: 1px solid #ebeef5;
  overflow: hidden;
  transition: all 0.3s ease;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.package-card:hover {
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
  transform: translateY(-4px);
  border-color: #409eff;
}

.package-header {
  padding: 16px 20px 0;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.package-type {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 18px;
}

.package-content {
  padding: 16px 20px;
  flex: 1;
  display: flex;
  flex-direction: column;
}

.package-name {
  margin: 0 0 8px 0;
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.package-description {
  margin: 0 0 16px 0;
  color: #606266;
  font-size: 14px;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  flex: 1;
}

.package-meta {
  margin-bottom: 16px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 8px;
  font-size: 13px;
  color: #909399;
}

.meta-item:last-child {
  margin-bottom: 0;
}

.package-tags {
  margin-bottom: 16px;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.tag-item {
  border: none;
  font-size: 12px;
}

.package-preview {
  margin-bottom: 16px;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

.preview-label {
  font-size: 12px;
  color: #6c757d;
  margin-bottom: 8px;
  font-weight: 500;
}

.preview-content {
  display: flex;
  gap: 12px;
}

.condition-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.package-actions {
  padding: 0 20px 20px;
  display: flex;
  gap: 8px;
  align-items: center;
}

/* 列表视图 */
.list-view {
  margin-top: 20px;
}

.package-name-cell {
  display: flex;
  align-items: center;
  gap: 12px;
}

.package-type-icon {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 14px;
}

.package-info {
  flex: 1;
}

.package-info .name {
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}

.package-info .description {
  font-size: 13px;
  color: #909399;
  line-height: 1.4;
}

.action-buttons {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: nowrap;
}

.action-buttons .el-button {
  margin: 0;
}

/* 分页 */
.pagination-wrapper {
  margin-top: 24px;
  display: flex;
  justify-content: center;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .resource-package-page {
    padding: 16px;
  }
  
  .header-content {
    flex-direction: column;
    gap: 16px;
  }
  
  .header-right {
    width: 100%;
    justify-content: flex-start;
  }
  
  .page-title {
    font-size: 24px;
  }
  
  .stat-card {
    padding: 16px;
  }
  
  .stat-value {
    font-size: 24px;
  }
}

/* Element Plus 样式覆盖 */
:deep(.el-card__body) {
  padding: 24px;
}

:deep(.el-form--inline .el-form-item) {
  margin-right: 16px;
  margin-bottom: 16px;
}

:deep(.el-table .el-table__cell) {
  padding: 12px 0;
}

:deep(.el-tag) {
  border: none;
  font-weight: 500;
}

:deep(.el-button--small) {
  padding: 6px 12px;
  font-size: 12px;
}

:deep(.el-radio-group .el-radio-button__inner) {
  padding: 8px 12px;
}
</style>