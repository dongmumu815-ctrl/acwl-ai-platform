<template>
  <div class="resource-package-container">
    <!-- 页面标题 -->
    <div class="page-header">
      <h2>资源包管理</h2>
      <p class="page-description">管理和配置数据查询资源包，支持SQL和Elasticsearch查询</p>
    </div>

    <!-- 搜索和操作区域 -->
    <div class="search-section">
      <el-card>
        <el-form :model="searchForm" inline>
          <el-form-item label="关键词">
            <el-input
              v-model="searchForm.keyword"
              placeholder="搜索资源包名称或描述"
              clearable
              style="width: 200px"
            />
          </el-form-item>
          <el-form-item label="类型">
            <el-select v-model="searchForm.type" placeholder="选择类型" clearable style="width: 120px">
              <el-option label="SQL" value="sql" />
              <el-option label="Elasticsearch" value="elasticsearch" />
            </el-select>
          </el-form-item>
          <el-form-item label="数据源">
            <el-select v-model="searchForm.datasource_id" placeholder="选择数据源" clearable style="width: 150px">
              <el-option
                v-for="ds in datasources"
                :key="ds.id"
                :label="ds.name"
                :value="ds.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="状态">
            <el-select v-model="searchForm.is_active" placeholder="选择状态" clearable style="width: 100px">
              <el-option label="启用" :value="true" />
              <el-option label="禁用" :value="false" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleSearch" :loading="loading">
              <el-icon><Search /></el-icon>
              搜索
            </el-button>
            <el-button @click="handleReset">
              <el-icon><Refresh /></el-icon>
              重置
            </el-button>
            <el-button type="success" @click="handleCreate">
              <el-icon><Plus /></el-icon>
              创建资源包
            </el-button>
          </el-form-item>
        </el-form>
      </el-card>
    </div>

    <!-- 资源包列表 -->
    <div class="table-section">
      <el-card>
        <el-table
          v-loading="loading"
          :data="packageList"
          stripe
          style="width: 100%"
        >
          <el-table-column prop="name" label="资源包名称" min-width="150">
            <template #default="{ row }">
              <div class="package-name">
                <el-link type="primary" @click="handleView(row)">
                  {{ row.name }}
                </el-link>
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
              </div>
            </template>
          </el-table-column>
          
          <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
          
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
          
          <el-table-column label="查询条件" width="120">
            <template #default="{ row }">
              <div class="condition-info">
                <div v-if="row.locked_conditions.length > 0">
                  <el-text type="danger" size="small">锁定: {{ row.locked_conditions.length }}</el-text>
                </div>
                <div v-if="row.dynamic_conditions.length > 0">
                  <el-text type="primary" size="small">动态: {{ row.dynamic_conditions.length }}</el-text>
                </div>
              </div>
            </template>
          </el-table-column>
          
          <el-table-column prop="is_active" label="状态" width="80">
            <template #default="{ row }">
              <el-tag :type="row.is_active ? 'success' : 'danger'">
                {{ row.is_active ? '启用' : '禁用' }}
              </el-tag>
            </template>
          </el-table-column>
          
          <el-table-column prop="created_at" label="创建时间" width="160">
            <template #default="{ row }">
              {{ formatDate(row.created_at) }}
            </template>
          </el-table-column>
          
          <el-table-column label="操作" width="200" fixed="right">
            <template #default="{ row }">
              <el-button type="primary" size="small" @click="handleQuery(row)">
                <el-icon><Search /></el-icon>
                查询
              </el-button>
              <el-button type="warning" size="small" @click="handleEdit(row)">
                <el-icon><Edit /></el-icon>
                编辑
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
            </template>
          </el-table-column>
        </el-table>
        
        <!-- 分页 -->
        <div class="pagination-section">
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
    </div>

    <!-- 创建/编辑对话框 -->
    <ResourcePackageForm
      v-model:visible="formVisible"
      :package-data="currentPackage"
      :is-edit="isEdit"
      @success="handleFormSuccess"
    />

    <!-- 查询对话框 -->
    <ResourcePackageQuery
      v-model:visible="queryVisible"
      :package-data="currentPackage"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Refresh, Plus, Edit, Delete } from '@element-plus/icons-vue'
import { resourcePackageApi, type ResourcePackage, type ResourcePackageSearchRequest } from '@/api/resourcePackage'
import { datasourceApi, type Datasource } from '@/api/datasource'
import ResourcePackageForm from './components/ResourcePackageForm.vue'
import ResourcePackageQuery from './components/ResourcePackageQuery.vue'
import { formatDate } from '@/utils/date'

// 响应式数据
const loading = ref(false)
const packageList = ref<ResourcePackage[]>([])
const datasources = ref<Datasource[]>([])
const formVisible = ref(false)
const queryVisible = ref(false)
const isEdit = ref(false)
const currentPackage = ref<ResourcePackage | null>(null)

// 搜索表单
const searchForm = reactive({
  keyword: '',
  type: '',
  datasource_id: '',
  is_active: '',
})

// 分页信息
const pagination = reactive({
  page: 1,
  size: 20,
  total: 0,
  pages: 0
})

// 计算属性
const getDatasourceName = computed(() => {
  return (datasourceId: number) => {
    const ds = datasources.value.find(d => d.id === datasourceId)
    return ds ? ds.name : '未知数据源'
  }
})

// 方法
const loadPackages = async () => {
  try {
    loading.value = true
    
    const searchParams: ResourcePackageSearchRequest = {
      keyword: searchForm.keyword || undefined,
      type: searchForm.type as any || undefined,
      datasource_id: searchForm.datasource_id ? Number(searchForm.datasource_id) : undefined,
      is_active: searchForm.is_active !== '' ? searchForm.is_active : undefined,
      page: pagination.page,
      size: pagination.size,
      sort_by: 'created_at',
      sort_order: 'desc'
    }
    
    const response = await resourcePackageApi.search(searchParams)
    
    packageList.value = response.items
    pagination.total = response.total
    pagination.pages = response.pages
    
  } catch (error) {
    console.error('加载资源包列表失败:', error)
    ElMessage.error('加载资源包列表失败')
  } finally {
    loading.value = false
  }
}

const loadDatasources = async () => {
  try {
    const response = await datasourceApi.getDataSourceList()
    datasources.value = response.data?.items || []
  } catch (error) {
    console.error('加载数据源列表失败:', error)
  }
}

const handleSearch = () => {
  pagination.page = 1
  loadPackages()
}

const handleReset = () => {
  Object.assign(searchForm, {
    keyword: '',
    type: '',
    datasource_id: '',
    is_active: ''
  })
  pagination.page = 1
  loadPackages()
}

const handleCreate = () => {
  currentPackage.value = null
  isEdit.value = false
  formVisible.value = true
}

const handleEdit = (row: ResourcePackage) => {
  currentPackage.value = row
  isEdit.value = true
  formVisible.value = true
}

const handleView = (row: ResourcePackage) => {
  // 可以跳转到详情页面或打开详情对话框
  console.log('查看资源包:', row)
}

const handleQuery = (row: ResourcePackage) => {
  currentPackage.value = row
  queryVisible.value = true
}

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

const handleFormSuccess = () => {
  formVisible.value = false
  loadPackages()
}

const handleSizeChange = (size: number) => {
  pagination.size = size
  pagination.page = 1
  loadPackages()
}

const handleCurrentChange = (page: number) => {
  pagination.page = page
  loadPackages()
}

// 生命周期
onMounted(() => {
  loadDatasources()
  loadPackages()
})
</script>

<style scoped>
.resource-package-container {
  padding: 20px;
}

.page-header {
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0 0 8px 0;
  color: #303133;
  font-size: 24px;
  font-weight: 600;
}

.page-description {
  margin: 0;
  color: #606266;
  font-size: 14px;
}

.search-section {
  margin-bottom: 20px;
}

.table-section {
  margin-bottom: 20px;
}

.package-name {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.package-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.condition-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.pagination-section {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

:deep(.el-table .el-table__cell) {
  padding: 12px 0;
}

:deep(.el-card__body) {
  padding: 20px;
}

:deep(.el-form--inline .el-form-item) {
  margin-right: 16px;
  margin-bottom: 16px;
}
</style>