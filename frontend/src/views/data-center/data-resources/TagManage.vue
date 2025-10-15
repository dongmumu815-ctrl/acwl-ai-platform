<template>
  <div class="tag-manage">
    <div class="page-header">
      <h1>标签管理</h1>
      <p>管理数据资源的标签信息</p>
    </div>

    <div class="content-container">
      <!-- 搜索和操作栏 -->
      <div class="toolbar">
        <div class="search-section">
          <el-input
            v-model="searchQuery"
            placeholder="搜索标签名称或描述"
            style="width: 300px;"
            clearable
            @input="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
          
          <el-select
            v-model="statusFilter"
            placeholder="状态筛选"
            style="width: 120px; margin-left: 12px;"
            clearable
            @change="handleSearch"
          >
            <el-option label="全部" value="" />
            <el-option label="启用" value="active" />
            <el-option label="禁用" value="inactive" />
          </el-select>
        </div>
        
        <div class="action-section">
          <el-button type="primary" @click="handleCreate">
            <el-icon><Plus /></el-icon>
            新增标签
          </el-button>
          <el-button @click="handleBatchDelete" :disabled="!selectedTags.length">
            <el-icon><Delete /></el-icon>
            批量删除
          </el-button>
          <el-button @click="handleRefresh">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </div>

      <!-- 标签列表 -->
      <el-card class="tag-list-card">
        <el-table
          ref="tagTableRef"
          :data="filteredTags"
          stripe
          border
          v-loading="loading"
          @selection-change="handleSelectionChange"
          style="width: 100%"
        >
          <el-table-column type="selection" width="55" />
          
          <el-table-column prop="name" label="标签名称" min-width="150">
            <template #default="{ row }">
              <el-tag
                :color="row.color"
                :style="{ color: getTextColor(row.color) }"
                class="tag-preview"
              >
                {{ row.name }}
              </el-tag>
            </template>
          </el-table-column>
          
          <el-table-column prop="display_name" label="显示名称" min-width="150" />
          
          <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
          
          <el-table-column prop="color" label="颜色" width="100">
            <template #default="{ row }">
              <div class="color-preview" :style="{ backgroundColor: row.color }"></div>
            </template>
          </el-table-column>
          
          <el-table-column prop="resource_count" label="使用次数" width="100" align="center" />
          
          <el-table-column prop="is_active" label="状态" width="100">
            <template #default="{ row }">
              <el-switch
                v-model="row.is_active"
                @change="handleStatusChange(row)"
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
              <el-button type="text" size="small" @click="handleEdit(row)">
                <el-icon><Edit /></el-icon>
                编辑
              </el-button>
              <el-button type="text" size="small" @click="handleViewResources(row)">
                <el-icon><View /></el-icon>
                查看资源
              </el-button>
              <el-button
                type="text"
                size="small"
                @click="handleDelete(row)"
                :disabled="row.resource_count > 0"
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

    <!-- 新增/编辑标签对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="500px"
      @close="handleDialogClose"
    >
      <el-form
        ref="tagFormRef"
        :model="tagForm"
        :rules="tagRules"
        label-width="100px"
      >
        <el-form-item label="标签名称" prop="name">
          <el-input v-model="tagForm.name" placeholder="请输入标签名称" />
        </el-form-item>
        
        <el-form-item label="显示名称" prop="display_name">
          <el-input v-model="tagForm.display_name" placeholder="请输入显示名称" />
        </el-form-item>
        
        <el-form-item label="标签描述" prop="description">
          <el-input
            v-model="tagForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入标签描述"
          />
        </el-form-item>
        
        <el-form-item label="标签颜色" prop="color">
          <div class="color-picker-container">
            <el-color-picker
              v-model="tagForm.color"
              :predefine="predefineColors"
              show-alpha
            />
            <el-tag
              :color="tagForm.color"
              :style="{ color: getTextColor(tagForm.color), marginLeft: '12px' }"
              class="tag-preview"
            >
              {{ tagForm.name || '标签预览' }}
            </el-tag>
          </div>
        </el-form-item>
        
        <el-form-item label="是否启用" prop="is_active">
          <el-switch v-model="tagForm.is_active" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSave" :loading="saving">
          保存
        </el-button>
      </template>
    </el-dialog>

    <!-- 标签资源对话框 -->
    <el-dialog
      v-model="resourceDialogVisible"
      :title="'标签 ' + (currentTag?.display_name || '') + ' 的资源列表'"
      width="800px"
    >
      <el-table
        :data="tagResources"
        stripe
        v-loading="loadingResources"
        style="width: 100%"
      >
        <el-table-column prop="name" label="资源名称" min-width="150" />
        <el-table-column prop="display_name" label="显示名称" min-width="150" />
        <el-table-column prop="resource_type" label="资源类型" width="120" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-button
              type="text"
              size="small"
              @click="handleViewResource(row)"
            >
              查看
            </el-button>
          </template>
        </el-table-column>
      </el-table>
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
  View
} from '@element-plus/icons-vue'
import type { DataResourceTag, DataResource } from '@/types/data-resource'

/**
 * 路由实例
 */
const router = useRouter()

/**
 * 响应式数据
 */
const tags = ref<DataResourceTag[]>([])
const selectedTags = ref<DataResourceTag[]>([])
const tagResources = ref<DataResource[]>([])
const currentTag = ref<DataResourceTag | null>(null)
const loading = ref(false)
const saving = ref(false)
const loadingResources = ref(false)
const dialogVisible = ref(false)
const resourceDialogVisible = ref(false)
const searchQuery = ref('')
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
 * 表单数据
 */
const tagForm = reactive<Partial<DataResourceTag>>({
  name: '',
  display_name: '',
  description: '',
  color: '#409EFF',
  is_active: true
})

/**
 * 预定义颜色
 */
const predefineColors = [
  '#409EFF',
  '#67C23A',
  '#E6A23C',
  '#F56C6C',
  '#909399',
  '#E4E7ED',
  '#F2F6FC',
  '#FFFFFF'
]

/**
 * 表单验证规则
 */
const tagRules = {
  name: [
    { required: true, message: '请输入标签名称', trigger: 'blur' },
    { min: 2, max: 20, message: '长度在 2 到 20 个字符', trigger: 'blur' }
  ],
  display_name: [
    { required: true, message: '请输入显示名称', trigger: 'blur' },
    { min: 2, max: 50, message: '长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  color: [
    { required: true, message: '请选择标签颜色', trigger: 'change' }
  ]
}

/**
 * 对话框标题
 */
const dialogTitle = computed(() => {
  return tagForm.id ? '编辑标签' : '新增标签'
})

/**
 * 过滤后的标签列表
 */
const filteredTags = computed(() => {
  let result = tags.value
  
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(tag =>
      tag.name.toLowerCase().includes(query) ||
      tag.display_name?.toLowerCase().includes(query) ||
      tag.description?.toLowerCase().includes(query)
    )
  }
  
  if (statusFilter.value) {
    result = result.filter(tag => {
      if (statusFilter.value === 'active') return tag.is_active
      if (statusFilter.value === 'inactive') return !tag.is_active
      return true
    })
  }
  
  return result
})

/**
 * 获取标签列表
 */
const fetchTags = async () => {
  loading.value = true
  
  try {
    // TODO: 调用API获取标签列表
    // const response = await dataResourceApi.getTags({
    //   page: pagination.page,
    //   size: pagination.size,
    //   search: searchQuery.value,
    //   status: statusFilter.value
    // })
    // tags.value = response.data.items
    // pagination.total = response.data.total
    
    // 模拟数据
    tags.value = [
      {
        id: 1,
        name: 'production',
        display_name: '生产环境',
        description: '生产环境数据',
        color: '#F56C6C',
        is_active: true,
        resource_count: 15,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z'
      },
      {
        id: 2,
        name: 'test',
        display_name: '测试环境',
        description: '测试环境数据',
        color: '#E6A23C',
        is_active: true,
        resource_count: 8,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z'
      },
      {
        id: 3,
        name: 'sensitive',
        display_name: '敏感数据',
        description: '包含敏感信息的数据',
        color: '#909399',
        is_active: true,
        resource_count: 3,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z'
      }
    ]
    pagination.total = tags.value.length
  } catch (error) {
    ElMessage.error('获取标签列表失败')
  } finally {
    loading.value = false
  }
}

/**
 * 获取标签关联的资源
 */
const fetchTagResources = async (tagId: number) => {
  loadingResources.value = true
  
  try {
    // TODO: 调用API获取标签资源
    // const response = await dataResourceApi.getResourcesByTag(tagId)
    // tagResources.value = response.data
    
    // 模拟数据
    tagResources.value = [
      {
        id: 1,
        name: 'user_behavior',
        display_name: '用户行为数据',
        description: '用户行为分析数据表',
        resource_type: 'doris_table',
        status: 'active',
        category_id: 1,
        tags: [],
        connection_config: {},
        table_name: 'user_behavior',
        fields: [],
        created_by: 1,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
        is_public: true,
        access_count: 0,
        favorite_count: 0
      }
    ]
  } catch (error) {
    ElMessage.error('获取标签资源失败')
  } finally {
    loadingResources.value = false
  }
}

/**
 * 处理搜索
 */
const handleSearch = () => {
  pagination.page = 1
  fetchTags()
}

/**
 * 处理新增
 */
const handleCreate = () => {
  Object.assign(tagForm, {
    name: '',
    display_name: '',
    description: '',
    color: '#409EFF',
    is_active: true
  })
  dialogVisible.value = true
}

/**
 * 处理编辑
 */
const handleEdit = (tag: DataResourceTag) => {
  Object.assign(tagForm, tag)
  dialogVisible.value = true
}

/**
 * 处理删除
 */
const handleDelete = async (tag: DataResourceTag) => {
  if (tag.resource_count && tag.resource_count > 0) {
    ElMessage.warning('该标签还在使用中，无法删除')
    return
  }
  
  try {
    await ElMessageBox.confirm(
      `确定要删除标签 "${tag.display_name}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    // TODO: 调用删除API
    // await dataResourceApi.deleteTag(tag.id!)
    
    ElMessage.success('删除成功')
    fetchTags()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

/**
 * 处理批量删除
 */
const handleBatchDelete = async () => {
  const canDeleteTags = selectedTags.value.filter(tag => !tag.resource_count || tag.resource_count === 0)
  
  if (canDeleteTags.length === 0) {
    ElMessage.warning('选中的标签都在使用中，无法删除')
    return
  }
  
  if (canDeleteTags.length < selectedTags.value.length) {
    ElMessage.warning(`只能删除 ${canDeleteTags.length} 个标签，其余标签正在使用中`)
  }
  
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${canDeleteTags.length} 个标签吗？`,
      '确认批量删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    // TODO: 调用批量删除API
    // await dataResourceApi.batchDeleteTags(canDeleteTags.map(tag => tag.id!))
    
    ElMessage.success('批量删除成功')
    fetchTags()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('批量删除失败')
    }
  }
}

/**
 * 处理状态变更
 */
const handleStatusChange = async (tag: DataResourceTag) => {
  try {
    // TODO: 调用更新状态API
    // await dataResourceApi.updateTagStatus(tag.id!, tag.is_active)
    
    ElMessage.success('状态更新成功')
  } catch (error) {
    ElMessage.error('状态更新失败')
    tag.is_active = !tag.is_active // 回滚状态
  }
}

/**
 * 处理查看资源
 */
const handleViewResources = (tag: DataResourceTag) => {
  currentTag.value = tag
  fetchTagResources(tag.id!)
  resourceDialogVisible.value = true
}

/**
 * 处理查看单个资源
 */
const handleViewResource = (resource: DataResource) => {
  router.push(`/data-resources/detail/${resource.id}`)
}

/**
 * 处理刷新
 */
const handleRefresh = () => {
  fetchTags()
}

/**
 * 处理选择变更
 */
const handleSelectionChange = (selection: DataResourceTag[]) => {
  selectedTags.value = selection
}

/**
 * 处理页面大小变更
 */
const handleSizeChange = (size: number) => {
  pagination.size = size
  pagination.page = 1
  fetchTags()
}

/**
 * 处理页面变更
 */
const handlePageChange = (page: number) => {
  pagination.page = page
  fetchTags()
}

/**
 * 处理保存
 */
const handleSave = async () => {
  saving.value = true
  
  try {
    if (tagForm.id) {
      // TODO: 调用更新API
      // await dataResourceApi.updateTag(tagForm.id, tagForm)
    } else {
      // TODO: 调用创建API
      // await dataResourceApi.createTag(tagForm)
    }
    
    ElMessage.success('保存成功')
    dialogVisible.value = false
    fetchTags()
  } catch (error) {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

/**
 * 处理对话框关闭
 */
const handleDialogClose = () => {
  Object.assign(tagForm, {
    name: '',
    display_name: '',
    description: '',
    color: '#409EFF',
    is_active: true
  })
}

/**
 * 获取文本颜色
 */
const getTextColor = (backgroundColor: string) => {
  // 简单的颜色对比度计算
  const hex = backgroundColor.replace('#', '')
  const r = parseInt(hex.substr(0, 2), 16)
  const g = parseInt(hex.substr(2, 2), 16)
  const b = parseInt(hex.substr(4, 2), 16)
  const brightness = (r * 299 + g * 587 + b * 114) / 1000
  return brightness > 128 ? '#000000' : '#FFFFFF'
}

/**
 * 获取状态类型
 */
const getStatusType = (status: string) => {
  const statusMap: Record<string, string> = {
    active: 'success',
    inactive: 'info',
    error: 'danger'
  }
  return statusMap[status] || 'info'
}

/**
 * 获取状态文本
 */
const getStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    active: '正常',
    inactive: '停用',
    error: '错误'
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
  fetchTags()
})
</script>

<style scoped>
.tag-manage {
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

.tag-list-card {
  margin-bottom: 20px;
}

.tag-preview {
  border: none;
  font-weight: 500;
}

.color-preview {
  width: 20px;
  height: 20px;
  border-radius: 4px;
  border: 1px solid #ddd;
  margin: 0 auto;
}

.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #eee;
}

.color-picker-container {
  display: flex;
  align-items: center;
}
</style>