<template>
  <div class="resource-list">
    <div class="page-header">
      <h1>数据资源管理</h1>
      <p>管理和查看所有数据资源</p>
    </div>

    <div class="toolbar">
      <el-row :gutter="16" justify="space-between">
        <el-col :span="16">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索资源名称或描述"
            clearable
            @input="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-col>
        <el-col :span="8" style="text-align: right">
          <el-button type="primary" @click="handleCreate">
            <el-icon><Plus /></el-icon>
            创建资源
          </el-button>
        </el-col>
      </el-row>
    </div>

    <div class="filter-bar">
      <el-row :gutter="16">
        <el-col :span="6">
          <el-select v-model="filters.resourceType" placeholder="资源类型" clearable>
            <el-option label="Doris表" value="doris_table" />
            <el-option label="Elasticsearch索引" value="elasticsearch_index" />
          </el-select>
        </el-col>
        <el-col :span="6">
          <el-select v-model="filters.status" placeholder="状态" clearable>
            <el-option label="活跃" value="active" />
            <el-option label="非活跃" value="inactive" />
            <el-option label="已归档" value="archived" />
            <el-option label="错误" value="error" />
          </el-select>
        </el-col>
        <el-col :span="6">
          <el-select v-model="filters.categoryId" placeholder="分类" clearable>
            <el-option label="业务数据" :value="1" />
            <el-option label="日志数据" :value="2" />
            <el-option label="监控数据" :value="3" />
          </el-select>
        </el-col>
        <el-col :span="6">
          <el-button @click="handleFilter">筛选</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-col>
      </el-row>
    </div>

    <div class="resource-table">
      <el-table
        v-loading="loading"
        :data="resourceList"
        stripe
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="name" label="资源名称" min-width="150">
          <template #default="{ row }">
            <el-link type="primary" @click="handleDetail(row.id)">
              {{ row.display_name || row.name }}
            </el-link>
          </template>
        </el-table-column>
        <el-table-column prop="resource_type" label="类型" width="120">
          <template #default="{ row }">
            <el-tag :type="getResourceTypeTag(row.resource_type)">
              {{ getResourceTypeLabel(row.resource_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusTag(row.status)">
              {{ getStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="category.name" label="分类" width="120" />
        <el-table-column prop="row_count" label="数据量" width="100">
          <template #default="{ row }">
            {{ formatNumber(row.row_count) }}
          </template>
        </el-table-column>
        <el-table-column prop="access_count" label="访问次数" width="100" />
        <el-table-column prop="created_at" label="创建时间" width="160">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="handleQuery(row.id)">查询</el-button>
            <el-button size="small" @click="handleEdit(row.id)">编辑</el-button>
            <el-button size="small" type="danger" @click="handleDelete(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <div class="pagination">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        :total="pagination.total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Plus } from '@element-plus/icons-vue'
import type { DataResource, DataResourceListQuery } from '@/types/data-resource'

/**
 * 路由实例
 */
const router = useRouter()

/**
 * 响应式数据
 */
const loading = ref(false)
const searchKeyword = ref('')
const resourceList = ref<DataResource[]>([])
const selectedResources = ref<DataResource[]>([])

/**
 * 筛选条件
 */
const filters = reactive({
  resourceType: '',
  status: '',
  categoryId: null as number | null
})

/**
 * 分页配置
 */
const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

/**
 * 获取资源列表
 */
const fetchResourceList = async () => {
  loading.value = true
  try {
    // TODO: 调用API获取数据
    // const response = await dataResourceApi.getList(query)
    // resourceList.value = response.data.items
    // pagination.total = response.data.total
    
    // 模拟数据
    resourceList.value = [
      {
        id: 1,
        name: 'user_behavior',
        display_name: '用户行为数据',
        description: '用户行为分析数据表',
        resource_type: 'doris_table',
        status: 'active',
        category_id: 1,
        category: { id: 1, name: '业务数据' },
        tags: [],
        connection_config: { host: 'localhost', port: 9030 },
        table_name: 'user_behavior',
        fields: [],
        row_count: 1000000,
        access_count: 150,
        created_by: 1,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
        is_public: true,
        favorite_count: 5
      }
    ]
    pagination.total = 1
  } catch (error) {
    ElMessage.error('获取资源列表失败')
  } finally {
    loading.value = false
  }
}

/**
 * 搜索处理
 */
const handleSearch = () => {
  pagination.page = 1
  fetchResourceList()
}

/**
 * 筛选处理
 */
const handleFilter = () => {
  pagination.page = 1
  fetchResourceList()
}

/**
 * 重置筛选
 */
const handleReset = () => {
  filters.resourceType = ''
  filters.status = ''
  filters.categoryId = null
  searchKeyword.value = ''
  pagination.page = 1
  fetchResourceList()
}

/**
 * 选择变化处理
 */
const handleSelectionChange = (selection: DataResource[]) => {
  selectedResources.value = selection
}

/**
 * 分页大小变化
 */
const handleSizeChange = (size: number) => {
  pagination.pageSize = size
  pagination.page = 1
  fetchResourceList()
}

/**
 * 当前页变化
 */
const handleCurrentChange = (page: number) => {
  pagination.page = page
  fetchResourceList()
}

/**
 * 创建资源
 */
const handleCreate = () => {
  router.push('/data-resources/create')
}

/**
 * 查看详情
 */
const handleDetail = (id: number) => {
  router.push(`/data-resources/detail/${id}`)
}

/**
 * 数据查询
 */
const handleQuery = (id: number) => {
  router.push(`/data-resources/query/${id}`)
}

/**
 * 编辑资源
 */
const handleEdit = (id: number) => {
  router.push(`/data-resources/edit/${id}`)
}

/**
 * 删除资源
 */
const handleDelete = async (id: number) => {
  try {
    await ElMessageBox.confirm('确定要删除这个资源吗？', '确认删除', {
      type: 'warning'
    })
    
    // TODO: 调用删除API
    // await dataResourceApi.delete(id)
    
    ElMessage.success('删除成功')
    fetchResourceList()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

/**
 * 获取资源类型标签
 */
const getResourceTypeTag = (type: string) => {
  const tagMap: Record<string, string> = {
    doris_table: 'primary',
    elasticsearch_index: 'success'
  }
  return tagMap[type] || 'info'
}

/**
 * 获取资源类型标签文本
 */
const getResourceTypeLabel = (type: string) => {
  const labelMap: Record<string, string> = {
    doris_table: 'Doris表',
    elasticsearch_index: 'ES索引'
  }
  return labelMap[type] || type
}

/**
 * 获取状态标签
 */
const getStatusTag = (status: string) => {
  const tagMap: Record<string, string> = {
    active: 'success',
    inactive: 'warning',
    archived: 'info',
    error: 'danger'
  }
  return tagMap[status] || 'info'
}

/**
 * 获取状态标签文本
 */
const getStatusLabel = (status: string) => {
  const labelMap: Record<string, string> = {
    active: '活跃',
    inactive: '非活跃',
    archived: '已归档',
    error: '错误'
  }
  return labelMap[status] || status
}

/**
 * 格式化数字
 */
const formatNumber = (num: number | undefined) => {
  if (!num) return '-'
  return num.toLocaleString()
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
  fetchResourceList()
})
</script>

<style scoped>
.resource-list {
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

.toolbar {
  margin-bottom: 16px;
}

.filter-bar {
  margin-bottom: 20px;
  padding: 16px;
  background: #f5f5f5;
  border-radius: 4px;
}

.resource-table {
  margin-bottom: 20px;
}

.pagination {
  display: flex;
  justify-content: center;
}
</style>