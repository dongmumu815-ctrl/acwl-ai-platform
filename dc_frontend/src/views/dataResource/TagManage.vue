<template>
  <div class="tag-manage-container">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1 class="page-title">
        <el-icon><PriceTag /></el-icon>
        标签管理
      </h1>
      <p class="page-description">管理数据资源的标签体系</p>
    </div>

    <!-- 操作栏 -->
    <div class="action-bar">
      <div class="left-actions">
        <el-button type="primary" @click="showCreateDialog">
          <el-icon><Plus /></el-icon>
          新建标签
        </el-button>
        <el-button @click="batchDelete" :disabled="selectedTags.length === 0">
          <el-icon><Delete /></el-icon>
          批量删除
        </el-button>
        <el-button @click="exportTags">
          <el-icon><Download /></el-icon>
          导出标签
        </el-button>
      </div>
      
      <div class="right-actions">
        <el-select
          v-model="filterStatus"
          placeholder="状态筛选"
          style="width: 120px"
          clearable
          @change="handleFilter"
        >
          <el-option label="启用" value="active" />
          <el-option label="禁用" value="disabled" />
        </el-select>
        
        <el-select
          v-model="filterCategory"
          placeholder="分类筛选"
          style="width: 150px"
          clearable
          @change="handleFilter"
        >
          <el-option
            v-for="category in tagCategories"
            :key="category.value"
            :label="category.label"
            :value="category.value"
          />
        </el-select>
        
        <el-input
          v-model="searchKeyword"
          placeholder="搜索标签名称"
          style="width: 250px"
          clearable
          @input="handleSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        
        <el-button @click="refreshTags">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <!-- 标签统计 -->
    <div class="stats-section">
      <el-row :gutter="20">
        <el-col :span="6">
          <el-card class="stats-card">
            <div class="stats-content">
              <div class="stats-icon">
                <el-icon color="#409EFF"><PriceTag /></el-icon>
              </div>
              <div class="stats-info">
                <div class="stats-number">{{ totalTags }}</div>
                <div class="stats-label">总标签数</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stats-card">
            <div class="stats-content">
              <div class="stats-icon">
                <el-icon color="#67C23A"><CircleCheck /></el-icon>
              </div>
              <div class="stats-info">
                <div class="stats-number">{{ activeTags }}</div>
                <div class="stats-label">启用标签</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stats-card">
            <div class="stats-content">
              <div class="stats-icon">
                <el-icon color="#E6A23C"><Warning /></el-icon>
              </div>
              <div class="stats-info">
                <div class="stats-number">{{ disabledTags }}</div>
                <div class="stats-label">禁用标签</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stats-card">
            <div class="stats-content">
              <div class="stats-icon">
                <el-icon color="#F56C6C"><Link /></el-icon>
              </div>
              <div class="stats-info">
                <div class="stats-number">{{ usedTags }}</div>
                <div class="stats-label">已使用标签</div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 标签列表 -->
    <div class="tag-list-section">
      <el-card>
        <template #header>
          <div class="card-header">
            <span>标签列表</span>
            <div class="header-actions">
              <el-button size="small" @click="toggleView">
                <el-icon><Grid /></el-icon>
                {{ viewMode === 'table' ? '卡片视图' : '表格视图' }}
              </el-button>
            </div>
          </div>
        </template>
        
        <!-- 表格视图 -->
        <div v-if="viewMode === 'table'" class="table-view">
          <el-table
            :data="filteredTags"
            stripe
            border
            style="width: 100%"
            @selection-change="handleSelectionChange"
            v-loading="loading"
          >
            <el-table-column type="selection" width="55" />
            
            <el-table-column prop="name" label="标签名称" min-width="150">
              <template #default="{ row }">
                <div class="tag-name-cell">
                  <el-tag
                    :color="row.color"
                    :style="{ color: getTextColor(row.color) }"
                    size="small"
                  >
                    {{ row.name }}
                  </el-tag>
                </div>
              </template>
            </el-table-column>
            
            <el-table-column prop="category" label="分类" width="120">
              <template #default="{ row }">
                <el-tag type="info" size="small">
                  {{ getCategoryLabel(row.category) }}
                </el-tag>
              </template>
            </el-table-column>
            
            <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
            
            <el-table-column prop="usageCount" label="使用次数" width="100" sortable>
              <template #default="{ row }">
                <el-link
                  type="primary"
                  @click="viewTagUsage(row)"
                  :disabled="row.usageCount === 0"
                >
                  {{ row.usageCount }}
                </el-link>
              </template>
            </el-table-column>
            
            <el-table-column prop="status" label="状态" width="80">
              <template #default="{ row }">
                <el-tag :type="row.status === 'active' ? 'success' : 'danger'" size="small">
                  {{ row.status === 'active' ? '启用' : '禁用' }}
                </el-tag>
              </template>
            </el-table-column>
            
            <el-table-column prop="createdAt" label="创建时间" width="180">
              <template #default="{ row }">
                {{ formatDate(row.createdAt) }}
              </template>
            </el-table-column>
            
            <el-table-column label="操作" width="200" fixed="right">
              <template #default="{ row }">
                <el-button size="small" type="primary" link @click="showEditDialog(row)">
                  <el-icon><Edit /></el-icon>
                  编辑
                </el-button>
                <el-button
                  size="small"
                  :type="row.status === 'active' ? 'warning' : 'success'"
                  link
                  @click="toggleTagStatus(row)"
                >
                  <el-icon><Switch /></el-icon>
                  {{ row.status === 'active' ? '禁用' : '启用' }}
                </el-button>
                <el-button
                  size="small"
                  type="danger"
                  link
                  @click="deleteTag(row)"
                  :disabled="row.usageCount > 0"
                >
                  <el-icon><Delete /></el-icon>
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>
          
          <!-- 分页 -->
          <div class="pagination-wrapper">
            <el-pagination
              v-model:current-page="currentPage"
              v-model:page-size="pageSize"
              :page-sizes="[10, 20, 50, 100]"
              :total="totalCount"
              layout="total, sizes, prev, pager, next, jumper"
              @size-change="handleSizeChange"
              @current-change="handleCurrentChange"
            />
          </div>
        </div>
        
        <!-- 卡片视图 -->
        <div v-else class="card-view">
          <div class="tag-cards">
            <div
              v-for="tag in filteredTags"
              :key="tag.id"
              class="tag-card"
              :class="{ selected: selectedTags.includes(tag) }"
              @click="toggleTagSelection(tag)"
            >
              <div class="tag-card-header">
                <el-tag
                  :color="tag.color"
                  :style="{ color: getTextColor(tag.color) }"
                  size="large"
                >
                  {{ tag.name }}
                </el-tag>
                <el-dropdown @command="handleTagCommand">
                  <el-button size="small" type="primary" link>
                    <el-icon><MoreFilled /></el-icon>
                  </el-button>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item :command="{ action: 'edit', data: tag }">
                        <el-icon><Edit /></el-icon>
                        编辑
                      </el-dropdown-item>
                      <el-dropdown-item :command="{ action: 'toggle', data: tag }">
                        <el-icon><Switch /></el-icon>
                        {{ tag.status === 'active' ? '禁用' : '启用' }}
                      </el-dropdown-item>
                      <el-dropdown-item
                        :command="{ action: 'delete', data: tag }"
                        divided
                        :disabled="tag.usageCount > 0"
                      >
                        <el-icon><Delete /></el-icon>
                        删除
                      </el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </div>
              
              <div class="tag-card-content">
                <div class="tag-info">
                  <div class="tag-category">
                    <el-tag type="info" size="small">
                      {{ getCategoryLabel(tag.category) }}
                    </el-tag>
                  </div>
                  <div class="tag-description">
                    {{ tag.description || '暂无描述' }}
                  </div>
                </div>
                
                <div class="tag-stats">
                  <div class="stat-item">
                    <span class="stat-label">使用次数:</span>
                    <span class="stat-value">{{ tag.usageCount }}</span>
                  </div>
                  <div class="stat-item">
                    <span class="stat-label">状态:</span>
                    <el-tag :type="tag.status === 'active' ? 'success' : 'danger'" size="small">
                      {{ tag.status === 'active' ? '启用' : '禁用' }}
                    </el-tag>
                  </div>
                </div>
                
                <div class="tag-meta">
                  <span class="create-time">{{ formatDate(tag.createdAt) }}</span>
                </div>
              </div>
            </div>
          </div>
          
          <div v-if="filteredTags.length === 0" class="empty-cards">
            <el-empty description="暂无标签数据">
              <el-button type="primary" @click="showCreateDialog">
                创建第一个标签
              </el-button>
            </el-empty>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 创建/编辑标签对话框 -->
    <el-dialog
      v-model="tagDialogVisible"
      :title="isEditMode ? '编辑标签' : '新建标签'"
      width="500px"
      @close="resetTagForm"
    >
      <el-form
        ref="tagFormRef"
        :model="tagForm"
        :rules="tagRules"
        label-width="80px"
      >
        <el-form-item label="标签名称" prop="name">
          <el-input
            v-model="tagForm.name"
            placeholder="请输入标签名称"
            maxlength="20"
            show-word-limit
          />
        </el-form-item>
        
        <el-form-item label="标签分类" prop="category">
          <el-select
            v-model="tagForm.category"
            placeholder="请选择标签分类"
            style="width: 100%"
          >
            <el-option
              v-for="category in tagCategories"
              :key="category.value"
              :label="category.label"
              :value="category.value"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="标签颜色" prop="color">
          <div class="color-selector">
            <el-color-picker
              v-model="tagForm.color"
              :predefine="colorPresets"
              show-alpha
            />
            <div class="color-preview">
              <el-tag
                :color="tagForm.color"
                :style="{ color: getTextColor(tagForm.color) }"
                size="large"
              >
                {{ tagForm.name || '预览' }}
              </el-tag>
            </div>
          </div>
        </el-form-item>
        
        <el-form-item label="状态" prop="status">
          <el-radio-group v-model="tagForm.status">
            <el-radio value="active">启用</el-radio>
            <el-radio value="disabled">禁用</el-radio>
          </el-radio-group>
        </el-form-item>
        
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="tagForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入标签描述"
            maxlength="100"
            show-word-limit
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="tagDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitTagForm" :loading="submitting">
            {{ isEditMode ? '更新' : '创建' }}
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 标签使用详情对话框 -->
    <el-dialog
      v-model="usageDialogVisible"
      title="标签使用详情"
      width="800px"
    >
      <div class="usage-content" v-if="currentTag">
        <div class="usage-header">
          <el-tag
            :color="currentTag.color"
            :style="{ color: getTextColor(currentTag.color) }"
            size="large"
          >
            {{ currentTag.name }}
          </el-tag>
          <span class="usage-count">共被 {{ currentTag.usageCount }} 个资源使用</span>
        </div>
        
        <el-table
          :data="tagUsageList"
          stripe
          style="width: 100%"
          max-height="400"
        >
          <el-table-column prop="resourceName" label="资源名称" min-width="200" />
          <el-table-column prop="resourceType" label="资源类型" width="120">
            <template #default="{ row }">
              <el-tag type="info" size="small">
                {{ getResourceTypeLabel(row.resourceType) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="categoryName" label="所属分类" width="150" />
          <el-table-column prop="createdAt" label="关联时间" width="180">
            <template #default="{ row }">
              {{ formatDate(row.createdAt) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="100">
            <template #default="{ row }">
              <el-button size="small" type="primary" link @click="viewResource(row)">
                查看
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRouter } from 'vue-router'

// 路由
const router = useRouter()

// 响应式数据
const tagFormRef = ref()
const loading = ref(false)
const submitting = ref(false)
const tagDialogVisible = ref(false)
const usageDialogVisible = ref(false)
const isEditMode = ref(false)
const viewMode = ref('table') // table | card
const searchKeyword = ref('')
const filterStatus = ref('')
const filterCategory = ref('')
const currentPage = ref(1)
const pageSize = ref(20)
const totalCount = ref(0)
const selectedTags = ref([])
const currentTag = ref(null)

// 标签表单
const tagForm = reactive({
  id: '',
  name: '',
  category: '',
  color: '#409EFF',
  status: 'active',
  description: ''
})

// 表单验证规则
const tagRules = {
  name: [
    { required: true, message: '请输入标签名称', trigger: 'blur' },
    { min: 2, max: 20, message: '长度在 2 到 20 个字符', trigger: 'blur' }
  ],
  category: [
    { required: true, message: '请选择标签分类', trigger: 'change' }
  ],
  color: [
    { required: true, message: '请选择标签颜色', trigger: 'change' }
  ]
}

// 标签分类
const tagCategories = [
  { label: '数据类型', value: 'data_type' },
  { label: '业务领域', value: 'business' },
  { label: '技术栈', value: 'technology' },
  { label: '重要程度', value: 'priority' },
  { label: '访问权限', value: 'permission' },
  { label: '数据质量', value: 'quality' },
  { label: '更新频率', value: 'frequency' },
  { label: '其他', value: 'other' }
]

// 颜色预设
const colorPresets = [
  '#409EFF', '#67C23A', '#E6A23C', '#F56C6C',
  '#909399', '#C71585', '#FF6347', '#32CD32',
  '#1E90FF', '#FF69B4', '#8A2BE2', '#00CED1',
  '#FFD700', '#FF4500', '#9370DB', '#20B2AA'
]

// 标签数据
const tags = ref([
  {
    id: 1,
    name: '用户数据',
    category: 'data_type',
    color: '#409EFF',
    status: 'active',
    description: '包含用户基本信息的数据',
    usageCount: 15,
    createdAt: '2024-01-15 10:30:00'
  },
  {
    id: 2,
    name: '订单数据',
    category: 'data_type',
    color: '#67C23A',
    status: 'active',
    description: '电商订单相关数据',
    usageCount: 12,
    createdAt: '2024-01-15 11:00:00'
  },
  {
    id: 3,
    name: '高优先级',
    category: 'priority',
    color: '#F56C6C',
    status: 'active',
    description: '重要程度较高的数据资源',
    usageCount: 8,
    createdAt: '2024-01-15 11:30:00'
  },
  {
    id: 4,
    name: 'MySQL',
    category: 'technology',
    color: '#E6A23C',
    status: 'active',
    description: 'MySQL数据库相关资源',
    usageCount: 20,
    createdAt: '2024-01-15 12:00:00'
  },
  {
    id: 5,
    name: '财务数据',
    category: 'business',
    color: '#909399',
    status: 'active',
    description: '财务相关的业务数据',
    usageCount: 6,
    createdAt: '2024-01-15 12:30:00'
  },
  {
    id: 6,
    name: '实时数据',
    category: 'frequency',
    color: '#FF6347',
    status: 'active',
    description: '需要实时更新的数据',
    usageCount: 10,
    createdAt: '2024-01-15 13:00:00'
  },
  {
    id: 7,
    name: '已废弃',
    category: 'other',
    color: '#C0C4CC',
    status: 'disabled',
    description: '已废弃不再使用的标签',
    usageCount: 0,
    createdAt: '2024-01-15 13:30:00'
  },
  {
    id: 8,
    name: '机密数据',
    category: 'permission',
    color: '#8A2BE2',
    status: 'active',
    description: '需要特殊权限访问的数据',
    usageCount: 3,
    createdAt: '2024-01-15 14:00:00'
  }
])

// 标签使用详情数据
const tagUsageList = ref([])

/**
 * 计算属性
 */
const totalTags = computed(() => tags.value.length)
const activeTags = computed(() => tags.value.filter(tag => tag.status === 'active').length)
const disabledTags = computed(() => tags.value.filter(tag => tag.status === 'disabled').length)
const usedTags = computed(() => tags.value.filter(tag => tag.usageCount > 0).length)

const filteredTags = computed(() => {
  let result = tags.value
  
  // 状态筛选
  if (filterStatus.value) {
    result = result.filter(tag => tag.status === filterStatus.value)
  }
  
  // 分类筛选
  if (filterCategory.value) {
    result = result.filter(tag => tag.category === filterCategory.value)
  }
  
  // 关键词搜索
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    result = result.filter(tag => 
      tag.name.toLowerCase().includes(keyword) ||
      tag.description.toLowerCase().includes(keyword)
    )
  }
  
  totalCount.value = result.length
  
  // 分页
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return result.slice(start, end)
})

/**
 * 获取分类标签
 */
const getCategoryLabel = (category: string) => {
  const categoryItem = tagCategories.find(item => item.value === category)
  return categoryItem ? categoryItem.label : category
}

/**
 * 获取资源类型标签
 */
const getResourceTypeLabel = (type: string) => {
  const typeMap: Record<string, string> = {
    database: '数据库',
    api: 'API',
    file: '文件',
    cache: '缓存'
  }
  return typeMap[type] || type
}

/**
 * 根据背景色获取文字颜色
 */
const getTextColor = (backgroundColor: string) => {
  // 简单的颜色对比度计算
  const color = backgroundColor.replace('#', '')
  const r = parseInt(color.substr(0, 2), 16)
  const g = parseInt(color.substr(2, 2), 16)
  const b = parseInt(color.substr(4, 2), 16)
  const brightness = (r * 299 + g * 587 + b * 114) / 1000
  return brightness > 128 ? '#000000' : '#FFFFFF'
}

/**
 * 格式化日期
 */
const formatDate = (dateStr: string) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}

/**
 * 切换视图模式
 */
const toggleView = () => {
  viewMode.value = viewMode.value === 'table' ? 'card' : 'table'
}

/**
 * 处理筛选
 */
const handleFilter = () => {
  currentPage.value = 1
}

/**
 * 处理搜索
 */
const handleSearch = () => {
  currentPage.value = 1
}

/**
 * 刷新标签
 */
const refreshTags = () => {
  loading.value = true
  // 模拟刷新
  setTimeout(() => {
    loading.value = false
    ElMessage.success('标签数据已刷新')
  }, 1000)
}

/**
 * 处理选择变化
 */
const handleSelectionChange = (selection: any[]) => {
  selectedTags.value = selection
}

/**
 * 切换标签选择（卡片视图）
 */
const toggleTagSelection = (tag: any) => {
  console.log('=== 标签选择调试信息 ===');
  console.log('点击的标签:', tag);
  console.log('标签ID:', tag.id);
  console.log('标签名称:', tag.name);
  console.log('当前已选标签:', selectedTags.value);
  console.log('========================');
  
  const index = selectedTags.value.findIndex(item => item.id === tag.id)
  if (index > -1) {
    selectedTags.value.splice(index, 1)
  } else {
    selectedTags.value.push(tag)
  }
}

/**
 * 处理分页大小变化
 */
const handleSizeChange = (size: number) => {
  pageSize.value = size
  currentPage.value = 1
}

/**
 * 处理当前页变化
 */
const handleCurrentChange = (page: number) => {
  currentPage.value = page
}

/**
 * 显示创建对话框
 */
const showCreateDialog = () => {
  console.log('=== 创建标签调试信息 ===');
  console.log('当前路由:', route.path);
  console.log('用户权限:', userStore.userPermissions);
  console.log('准备打开创建标签对话框');
  console.log('========================');
  
  isEditMode.value = false
  resetTagForm()
  tagDialogVisible.value = true
}

/**
 * 显示编辑对话框
 */
const showEditDialog = (tag: any) => {
  console.log('=== 编辑标签调试信息 ===');
  console.log('要编辑的标签:', tag);
  console.log('标签ID:', tag.id);
  console.log('标签名称:', tag.name);
  console.log('标签分类:', tag.category);
  console.log('当前路由:', route.path);
  console.log('用户权限:', userStore.userPermissions);
  console.log('准备打开编辑标签对话框');
  console.log('========================');
  
  isEditMode.value = true
  
  Object.assign(tagForm, {
    id: tag.id,
    name: tag.name,
    category: tag.category,
    color: tag.color,
    status: tag.status,
    description: tag.description
  })
  
  tagDialogVisible.value = true
}

/**
 * 重置表单
 */
const resetTagForm = () => {
  Object.assign(tagForm, {
    id: '',
    name: '',
    category: '',
    color: '#409EFF',
    status: 'active',
    description: ''
  })
  
  tagFormRef.value?.clearValidate()
}

/**
 * 提交表单
 */
const submitTagForm = () => {
  tagFormRef.value?.validate((valid: boolean) => {
    if (!valid) return
    
    submitting.value = true
    
    // 模拟提交
    setTimeout(() => {
      if (isEditMode.value) {
        ElMessage.success('标签更新成功')
      } else {
        ElMessage.success('标签创建成功')
      }
      
      tagDialogVisible.value = false
      submitting.value = false
      
      // 这里应该刷新标签数据
      refreshTags()
    }, 1000)
  })
}

/**
 * 处理标签命令（卡片视图）
 */
const handleTagCommand = (command: any) => {
  const { action, data } = command
  
  switch (action) {
    case 'edit':
      showEditDialog(data)
      break
    case 'toggle':
      toggleTagStatus(data)
      break
    case 'delete':
      deleteTag(data)
      break
  }
}

/**
 * 切换标签状态
 */
const toggleTagStatus = (tag: any) => {
  const newStatus = tag.status === 'active' ? 'disabled' : 'active'
  const action = newStatus === 'active' ? '启用' : '禁用'
  
  ElMessageBox.confirm(
    `确定要${action}标签 "${tag.name}" 吗？`,
    '确认操作',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(() => {
    // 模拟状态切换
    tag.status = newStatus
    ElMessage.success(`已${action}标签 "${tag.name}"`)
  }).catch(() => {
    // 取消操作
  })
}

/**
 * 删除标签
 */
const deleteTag = (tag: any) => {
  if (tag.usageCount > 0) {
    ElMessage.warning('该标签正在被使用，无法删除')
    return
  }
  
  ElMessageBox.confirm(
    `确定要删除标签 "${tag.name}" 吗？此操作不可恢复。`,
    '确认删除',
    {
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
      type: 'error'
    }
  ).then(() => {
    ElMessage.success(`已删除标签 "${tag.name}"`)
    // 这里应该刷新标签数据
    refreshTags()
  }).catch(() => {
    // 取消删除
  })
}

/**
 * 批量删除
 */
const batchDelete = () => {
  const canDeleteTags = selectedTags.value.filter(tag => tag.usageCount === 0)
  
  if (canDeleteTags.length === 0) {
    ElMessage.warning('所选标签都在使用中，无法删除')
    return
  }
  
  if (canDeleteTags.length < selectedTags.value.length) {
    ElMessage.warning(`只能删除 ${canDeleteTags.length} 个未使用的标签`)
  }
  
  ElMessageBox.confirm(
    `确定要删除选中的 ${canDeleteTags.length} 个标签吗？此操作不可恢复。`,
    '确认批量删除',
    {
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
      type: 'error'
    }
  ).then(() => {
    ElMessage.success(`已删除 ${canDeleteTags.length} 个标签`)
    selectedTags.value = []
    // 这里应该刷新标签数据
    refreshTags()
  }).catch(() => {
    // 取消删除
  })
}

/**
 * 导出标签
 */
const exportTags = () => {
  ElMessage.success('导出功能开发中...')
}

/**
 * 查看标签使用情况
 */
const viewTagUsage = (tag: any) => {
  currentTag.value = tag
  
  // 模拟加载使用详情
  tagUsageList.value = [
    {
      id: 1,
      resourceName: '用户基础信息表',
      resourceType: 'database',
      categoryName: '数据库资源',
      createdAt: '2024-01-15 10:30:00'
    },
    {
      id: 2,
      resourceName: '用户行为分析API',
      resourceType: 'api',
      categoryName: 'API接口',
      createdAt: '2024-01-15 11:00:00'
    },
    {
      id: 3,
      resourceName: '用户画像数据',
      resourceType: 'file',
      categoryName: '文件资源',
      createdAt: '2024-01-15 11:30:00'
    }
  ]
  
  usageDialogVisible.value = true
}

/**
 * 查看资源
 */
const viewResource = (resource: any) => {
  router.push({
    name: 'ResourceDetail',
    params: { id: resource.id }
  })
}

/**
 * 组件挂载时初始化
 */
onMounted(() => {
  // 初始化数据
  totalCount.value = tags.value.length
})
</script>

<style lang="scss" scoped>
.tag-manage-container {
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

.action-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 16px;
  background: var(--el-bg-color);
  border-radius: 8px;
  border: 1px solid var(--el-border-color-lighter);
  
  .left-actions,
  .right-actions {
    display: flex;
    gap: 12px;
    align-items: center;
  }
}

.stats-section {
  margin-bottom: 20px;
  
  .stats-card {
    .stats-content {
      display: flex;
      align-items: center;
      gap: 16px;
      
      .stats-icon {
        font-size: 32px;
      }
      
      .stats-info {
        .stats-number {
          font-size: 24px;
          font-weight: 600;
          color: var(--el-text-color-primary);
          line-height: 1;
        }
        
        .stats-label {
          font-size: 14px;
          color: var(--el-text-color-secondary);
          margin-top: 4px;
        }
      }
    }
  }
}

.tag-list-section {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .table-view {
    .tag-name-cell {
      display: flex;
      align-items: center;
    }
    
    .pagination-wrapper {
      margin-top: 20px;
      text-align: center;
    }
  }
  
  .card-view {
    .tag-cards {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
      gap: 16px;
      
      .tag-card {
        border: 1px solid var(--el-border-color-lighter);
        border-radius: 8px;
        padding: 16px;
        background: var(--el-bg-color);
        cursor: pointer;
        transition: all 0.2s;
        
        &:hover {
          border-color: var(--el-color-primary);
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }
        
        &.selected {
          border-color: var(--el-color-primary);
          background: var(--el-color-primary-light-9);
        }
        
        .tag-card-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 12px;
        }
        
        .tag-card-content {
          .tag-info {
            margin-bottom: 12px;
            
            .tag-category {
              margin-bottom: 8px;
            }
            
            .tag-description {
              font-size: 14px;
              color: var(--el-text-color-secondary);
              line-height: 1.4;
            }
          }
          
          .tag-stats {
            display: flex;
            justify-content: space-between;
            margin-bottom: 12px;
            
            .stat-item {
              display: flex;
              align-items: center;
              gap: 4px;
              font-size: 12px;
              
              .stat-label {
                color: var(--el-text-color-secondary);
              }
              
              .stat-value {
                font-weight: 600;
                color: var(--el-text-color-primary);
              }
            }
          }
          
          .tag-meta {
            .create-time {
              font-size: 12px;
              color: var(--el-text-color-placeholder);
            }
          }
        }
      }
    }
    
    .empty-cards {
      padding: 60px 0;
      text-align: center;
    }
  }
}

.color-selector {
  display: flex;
  align-items: center;
  gap: 16px;
  
  .color-preview {
    display: flex;
    align-items: center;
  }
}

.usage-content {
  .usage-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 20px;
    
    .usage-count {
      font-size: 14px;
      color: var(--el-text-color-secondary);
    }
  }
}

.dialog-footer {
  text-align: right;
}

// 响应式设计
@media (max-width: 1200px) {
  .action-bar {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
    
    .left-actions,
    .right-actions {
      justify-content: center;
      flex-wrap: wrap;
    }
  }
  
  .stats-section {
    .el-col {
      margin-bottom: 16px;
    }
  }
  
  .tag-cards {
    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)) !important;
  }
}

@media (max-width: 768px) {
  .tag-manage-container {
    padding: 16px;
  }
  
  .action-bar {
    .left-actions,
    .right-actions {
      gap: 8px;
    }
    
    .el-input,
    .el-select {
      width: 100% !important;
    }
  }
  
  .stats-section {
    .el-col {
      span: 12 !important;
    }
  }
  
  .tag-cards {
    grid-template-columns: 1fr !important;
  }
  
  .table-view {
    .el-table {
      font-size: 12px;
    }
  }
}
</style>