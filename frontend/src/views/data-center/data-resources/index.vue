<template>
  <div class="data-resources-container">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1 class="page-title">
        <el-icon><DataBoard /></el-icon>
        数据资源管理
      </h1>
      <p class="page-description">管理和查看所有数据资源</p>
    </div>

    <!-- 搜索和筛选 -->
    <div class="search-section">
      <el-card>
        <el-form :model="searchForm" inline>
          <el-form-item label="资源名称">
            <el-input
              v-model="searchForm.name"
              placeholder="请输入资源名称"
              clearable
              style="width: 200px"
            />
          </el-form-item>
          <el-form-item label="资源类型">
            <el-select
              v-model="searchForm.type"
              placeholder="请选择资源类型"
              clearable
              style="width: 150px"
            >
              <el-option
                v-for="type in resourceTypes"
                :key="type.value"
                :label="type.label"
                :value="type.value"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="状态">
            <el-select
              v-model="searchForm.status"
              placeholder="请选择状态"
              clearable
              style="width: 120px"
            >
              <el-option label="已发布" value="published" />
              <el-option label="草稿" value="draft" />
              <el-option label="已下线" value="offline" />
            </el-select>
          </el-form-item>
          <el-form-item label="创建时间">
            <el-date-picker
              v-model="searchForm.dateRange"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              format="YYYY-MM-DD"
              value-format="YYYY-MM-DD"
            />
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
    </div>

    <!-- 操作栏 -->
    <div class="action-bar">
      <div class="left-actions">
        <el-button type="primary" @click="handleCreate">
          <el-icon><Plus /></el-icon>
          新增资源
        </el-button>
        <el-button @click="handleBatchImport">
          <el-icon><Upload /></el-icon>
          批量导入
        </el-button>
        <el-button @click="handleBatchExport" :disabled="!selectedResources.length">
          <el-icon><Download /></el-icon>
          批量导出
        </el-button>
        <el-button 
          type="danger" 
          @click="handleBatchDelete" 
          :disabled="!selectedResources.length"
        >
          <el-icon><Delete /></el-icon>
          批量删除
        </el-button>
      </div>
      <div class="right-actions">
        <el-button-group>
          <el-button 
            :type="viewMode === 'table' ? 'primary' : ''" 
            @click="viewMode = 'table'"
          >
            <el-icon><List /></el-icon>
          </el-button>
          <el-button 
            :type="viewMode === 'grid' ? 'primary' : ''" 
            @click="viewMode = 'grid'"
          >
            <el-icon><Grid /></el-icon>
          </el-button>
        </el-button-group>
      </div>
    </div>

    <!-- 数据表格 -->
    <div class="table-section" v-if="viewMode === 'table'">
      <el-card>
        <el-table
          v-loading="loading"
          :data="tableData"
          @selection-change="handleSelectionChange"
          stripe
          style="width: 100%"
        >
          <el-table-column type="selection" width="55" />
          <el-table-column prop="id" label="ID" width="80" />
          <el-table-column prop="name" label="资源名称" min-width="200">
            <template #default="{ row }">
              <div class="resource-name">
                <el-icon class="resource-icon">
                  <component :is="getResourceIcon(row.type)" />
                </el-icon>
                <span>{{ row.name }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="type" label="类型" width="120">
            <template #default="{ row }">
              <el-tag :type="getTypeTagType(row.type)">{{ getTypeLabel(row.type) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="size" label="大小" width="100">
            <template #default="{ row }">
              {{ formatSize(row.size) }}
            </template>
          </el-table-column>
          <el-table-column prop="views" label="访问量" width="100" />
          <el-table-column prop="downloads" label="下载量" width="100" />
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="getStatusTagType(row.status)">{{ getStatusLabel(row.status) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="createdAt" label="创建时间" width="180" />
          <el-table-column label="操作" width="200" fixed="right">
            <template #default="{ row }">
              <el-button size="small" @click="handleView(row)">
                <el-icon><View /></el-icon>
                查看
              </el-button>
              <el-button size="small" type="primary" @click="handleEdit(row)">
                <el-icon><Edit /></el-icon>
                编辑
              </el-button>
              <el-button size="small" type="danger" @click="handleDelete(row)">
                <el-icon><Delete /></el-icon>
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>

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

    <!-- 网格视图 -->
    <div class="grid-section" v-if="viewMode === 'grid'">
      <el-row :gutter="20">
        <el-col :span="6" v-for="item in tableData" :key="item.id">
          <el-card class="resource-card" @click="handleView(item)">
            <div class="card-header">
              <el-checkbox 
                v-model="item.selected" 
                @change="handleCardSelection(item)"
                @click.stop
              />
              <el-dropdown @click.stop>
                <el-icon><MoreFilled /></el-icon>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item @click="handleView(item)">查看</el-dropdown-item>
                    <el-dropdown-item @click="handleEdit(item)">编辑</el-dropdown-item>
                    <el-dropdown-item @click="handleDelete(item)" divided>删除</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
            <div class="card-content">
              <div class="resource-icon-large">
                <el-icon :size="48">
                  <component :is="getResourceIcon(item.type)" />
                </el-icon>
              </div>
              <div class="resource-info">
                <h4 class="resource-title">{{ item.name }}</h4>
                <p class="resource-meta">
                  <el-tag :type="getTypeTagType(item.type)" size="small">{{ getTypeLabel(item.type) }}</el-tag>
                  <span class="size">{{ formatSize(item.size) }}</span>
                </p>
                <div class="resource-stats">
                  <span><el-icon><View /></el-icon> {{ item.views }}</span>
                  <span><el-icon><Download /></el-icon> {{ item.downloads }}</span>
                </div>
              </div>
            </div>
            <div class="card-footer">
              <el-tag :type="getStatusTagType(item.status)" size="small">{{ getStatusLabel(item.status) }}</el-tag>
              <span class="create-time">{{ item.createdAt }}</span>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  DataBoard,
  Search,
  Refresh,
  Plus,
  Upload,
  Download,
  Delete,
  List,
  Grid,
  View,
  Edit,
  MoreFilled,
  Document,
  Notebook,
  Files,
  Reading,
  Collection
} from '@element-plus/icons-vue'

const router = useRouter()

// 响应式数据
const loading = ref(false)
const viewMode = ref<'table' | 'grid'>('table')
const selectedResources = ref<any[]>([])

// 搜索表单
const searchForm = reactive({
  name: '',
  type: '',
  status: '',
  dateRange: null as [string, string] | null
})

// 分页数据
const pagination = reactive({
  currentPage: 1,
  pageSize: 20,
  total: 0
})

// 资源类型选项
const resourceTypes = ref([
  { label: '图书', value: 'book' },
  { label: '期刊文章', value: 'article' },
  { label: '会议录', value: 'conference' },
  { label: '学术论文', value: 'paper' },
  { label: '教材', value: 'textbook' }
])

// 表格数据
const tableData = ref([
  {
    id: 1,
    name: '机器学习基础教程',
    type: 'textbook',
    size: 15728640, // 15MB
    views: 1547,
    downloads: 284,
    status: 'published',
    createdAt: '2024-01-15 10:30:00',
    selected: false
  },
  {
    id: 2,
    name: '深度学习论文集',
    type: 'paper',
    size: 52428800, // 50MB
    views: 2456,
    downloads: 456,
    status: 'published',
    createdAt: '2024-01-14 14:20:00',
    selected: false
  },
  {
    id: 3,
    name: '数据科学期刊2024',
    type: 'article',
    size: 31457280, // 30MB
    views: 987,
    downloads: 123,
    status: 'draft',
    createdAt: '2024-01-13 09:15:00',
    selected: false
  },
  {
    id: 4,
    name: 'AI会议录2024',
    type: 'conference',
    size: 104857600, // 100MB
    views: 765,
    downloads: 87,
    status: 'published',
    createdAt: '2024-01-12 16:45:00',
    selected: false
  },
  {
    id: 5,
    name: '计算机视觉图书',
    type: 'book',
    size: 83886080, // 80MB
    views: 654,
    downloads: 76,
    status: 'offline',
    createdAt: '2024-01-11 11:30:00',
    selected: false
  }
])

/**
 * 获取资源图标
 * @param type 资源类型
 * @returns 图标组件名
 */
const getResourceIcon = (type: string) => {
  const iconMap: Record<string, string> = {
    book: 'Reading',
    article: 'Document',
    conference: 'Files',
    paper: 'Notebook',
    textbook: 'Collection'
  }
  return iconMap[type] || 'Document'
}

/**
 * 获取类型标签样式
 * @param type 资源类型
 * @returns 标签样式
 */
const getTypeTagType = (type: string) => {
  const typeMap: Record<string, string> = {
    book: 'primary',
    article: 'success',
    conference: 'warning',
    paper: 'info',
    textbook: 'danger'
  }
  return typeMap[type] || 'info'
}

/**
 * 获取类型标签文本
 * @param type 资源类型
 * @returns 标签文本
 */
const getTypeLabel = (type: string) => {
  const typeMap: Record<string, string> = {
    book: '图书',
    article: '期刊文章',
    conference: '会议录',
    paper: '学术论文',
    textbook: '教材'
  }
  return typeMap[type] || type
}

/**
 * 获取状态标签样式
 * @param status 状态
 * @returns 标签样式
 */
const getStatusTagType = (status: string) => {
  const statusMap: Record<string, string> = {
    published: 'success',
    draft: 'warning',
    offline: 'danger'
  }
  return statusMap[status] || 'info'
}

/**
 * 获取状态标签文本
 * @param status 状态
 * @returns 标签文本
 */
const getStatusLabel = (status: string) => {
  const statusMap: Record<string, string> = {
    published: '已发布',
    draft: '草稿',
    offline: '已下线'
  }
  return statusMap[status] || status
}

/**
 * 格式化文件大小
 * @param bytes 字节数
 * @returns 格式化后的大小字符串
 */
const formatSize = (bytes: number) => {
  const units = ['B', 'KB', 'MB', 'GB']
  let size = bytes
  let unitIndex = 0
  
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024
    unitIndex++
  }
  
  return `${size.toFixed(1)}${units[unitIndex]}`
}

/**
 * 处理搜索
 */
const handleSearch = () => {
  loading.value = true
  // 模拟搜索
  setTimeout(() => {
    loading.value = false
    ElMessage.success('搜索完成')
  }, 1000)
}

/**
 * 处理重置
 */
const handleReset = () => {
  Object.assign(searchForm, {
    name: '',
    type: '',
    status: '',
    dateRange: null
  })
  handleSearch()
}

/**
 * 处理新增
 */
const handleCreate = () => {
  router.push('/data-center/data-resources/create')
}

/**
 * 处理批量导入
 */
const handleBatchImport = () => {
  ElMessage.info('批量导入功能开发中...')
}

/**
 * 处理批量导出
 */
const handleBatchExport = () => {
  ElMessage.info('批量导出功能开发中...')
}

/**
 * 处理批量删除
 */
const handleBatchDelete = () => {
  ElMessageBox.confirm(
    `确定要删除选中的 ${selectedResources.value.length} 个资源吗？`,
    '批量删除',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(() => {
    ElMessage.success('删除成功')
    selectedResources.value = []
  }).catch(() => {
    ElMessage.info('已取消删除')
  })
}

/**
 * 处理查看
 * @param row 行数据
 */
const handleView = (row: any) => {
  router.push(`/data-center/data-resources/detail/${row.id}`)
}

/**
 * 处理编辑
 * @param row 行数据
 */
const handleEdit = (row: any) => {
  router.push(`/data-center/data-resources/edit/${row.id}`)
}

/**
 * 处理删除
 * @param row 行数据
 */
const handleDelete = (row: any) => {
  ElMessageBox.confirm(
    `确定要删除资源 "${row.name}" 吗？`,
    '删除确认',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(() => {
    ElMessage.success('删除成功')
  }).catch(() => {
    ElMessage.info('已取消删除')
  })
}

/**
 * 处理选择变化
 * @param selection 选中的行
 */
const handleSelectionChange = (selection: any[]) => {
  selectedResources.value = selection
}

/**
 * 处理卡片选择
 * @param item 卡片数据
 */
const handleCardSelection = (item: any) => {
  if (item.selected) {
    selectedResources.value.push(item)
  } else {
    const index = selectedResources.value.findIndex(r => r.id === item.id)
    if (index > -1) {
      selectedResources.value.splice(index, 1)
    }
  }
}

/**
 * 处理页面大小变化
 * @param size 页面大小
 */
const handleSizeChange = (size: number) => {
  pagination.pageSize = size
  handleSearch()
}

/**
 * 处理当前页变化
 * @param page 当前页
 */
const handleCurrentChange = (page: number) => {
  pagination.currentPage = page
  handleSearch()
}

/**
 * 组件挂载时初始化
 */
onMounted(() => {
  pagination.total = tableData.value.length
  console.log('数据资源管理页面初始化完成')
})
</script>

<style lang="scss" scoped>
.data-resources-container {
  padding: 20px;
  background: var(--el-bg-color-page);
  min-height: 100vh;
}

.page-header {
  margin-bottom: 24px;
  
  .page-title {
    display: flex;
    align-items: center;
    font-size: 24px;
    font-weight: 600;
    color: var(--el-text-color-primary);
    margin: 0 0 8px 0;
    
    .el-icon {
      margin-right: 8px;
      color: var(--el-color-primary);
    }
  }
  
  .page-description {
    color: var(--el-text-color-secondary);
    margin: 0;
  }
}

.search-section {
  margin-bottom: 16px;
}

.action-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  
  .left-actions {
    display: flex;
    gap: 8px;
  }
}

.table-section {
  .resource-name {
    display: flex;
    align-items: center;
    
    .resource-icon {
      margin-right: 8px;
      color: var(--el-color-primary);
    }
  }
  
  .pagination-wrapper {
    display: flex;
    justify-content: center;
    margin-top: 20px;
  }
}

.grid-section {
  .resource-card {
    cursor: pointer;
    transition: all 0.3s;
    
    &:hover {
      transform: translateY(-2px);
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    }
    
    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 16px;
    }
    
    .card-content {
      text-align: center;
      margin-bottom: 16px;
      
      .resource-icon-large {
        margin-bottom: 12px;
        color: var(--el-color-primary);
      }
      
      .resource-title {
        font-size: 16px;
        font-weight: 500;
        margin: 0 0 8px 0;
        color: var(--el-text-color-primary);
      }
      
      .resource-meta {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
        
        .size {
          font-size: 12px;
          color: var(--el-text-color-secondary);
        }
      }
      
      .resource-stats {
        display: flex;
        justify-content: space-around;
        font-size: 12px;
        color: var(--el-text-color-secondary);
        
        span {
          display: flex;
          align-items: center;
          
          .el-icon {
            margin-right: 4px;
          }
        }
      }
    }
    
    .card-footer {
      display: flex;
      justify-content: space-between;
      align-items: center;
      
      .create-time {
        font-size: 12px;
        color: var(--el-text-color-secondary);
      }
    }
  }
}

// 响应式设计
@media (max-width: 768px) {
  .data-resources-container {
    padding: 16px;
  }
  
  .action-bar {
    flex-direction: column;
    gap: 16px;
    align-items: flex-start;
  }
  
  .grid-section {
    :deep(.el-col) {
      margin-bottom: 16px;
    }
  }
}
</style>