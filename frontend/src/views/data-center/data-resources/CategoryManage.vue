<template>
  <div class="category-manage">
    <div class="page-header">
      <h1>资源分类管理</h1>
      <p>管理数据资源的分类信息</p>
    </div>

    <div class="content-container">
      <el-row :gutter="20">
        <el-col :span="8">
          <!-- 分类树 -->
          <el-card title="分类树" class="category-tree-card">
            <template #header>
              <div class="card-header">
                <span>分类树</span>
                <el-button type="primary" size="small" @click="handleAddCategory">
                  <el-icon><Plus /></el-icon>
                  新增分类
                </el-button>
              </div>
            </template>
            
            <el-tree
              ref="categoryTreeRef"
              :data="categoryTree"
              :props="treeProps"
              node-key="id"
              :expand-on-click-node="false"
              :highlight-current="true"
              @node-click="handleNodeClick"
              class="category-tree"
            >
              <template #default="{ node, data }">
                <div class="tree-node">
                  <div class="node-content">
                    <el-icon class="node-icon">
                      <Folder v-if="data.children && data.children.length > 0" />
                      <FolderOpened v-else />
                    </el-icon>
                    <span class="node-label">{{ data.name }}</span>
                    <span class="node-count">({{ data.resource_count || 0 }})</span>
                  </div>
                  <div class="node-actions">
                    <el-button
                      type="text"
                      size="small"
                      @click.stop="handleAddSubCategory(data)"
                    >
                      <el-icon><Plus /></el-icon>
                    </el-button>
                    <el-button
                      type="text"
                      size="small"
                      @click.stop="handleEditCategory(data)"
                    >
                      <el-icon><Edit /></el-icon>
                    </el-button>
                    <el-button
                      type="text"
                      size="small"
                      @click.stop="handleDeleteCategory(data)"
                      :disabled="data.resource_count > 0"
                    >
                      <el-icon><Delete /></el-icon>
                    </el-button>
                  </div>
                </div>
              </template>
            </el-tree>
          </el-card>
        </el-col>

        <el-col :span="16">
          <!-- 分类详情 -->
          <el-card title="分类详情" class="category-detail-card">
            <div v-if="!selectedCategory" class="empty-selection">
              <el-empty description="请选择一个分类查看详情" />
            </div>
            
            <div v-else class="category-detail">
              <el-form
                ref="categoryFormRef"
                :model="categoryForm"
                :rules="categoryRules"
                label-width="100px"
                class="category-form"
              >
                <el-form-item label="分类名称" prop="name">
                  <el-input
                    v-model="categoryForm.name"
                    placeholder="请输入分类名称"
                    :disabled="!isEditing"
                  />
                </el-form-item>
                
                <el-form-item label="显示名称" prop="display_name">
                  <el-input
                    v-model="categoryForm.display_name"
                    placeholder="请输入显示名称"
                    :disabled="!isEditing"
                  />
                </el-form-item>
                
                <el-form-item label="分类描述" prop="description">
                  <el-input
                    v-model="categoryForm.description"
                    type="textarea"
                    :rows="3"
                    placeholder="请输入分类描述"
                    :disabled="!isEditing"
                  />
                </el-form-item>
                
                <el-form-item label="父级分类" prop="parent_id">
                  <el-tree-select
                    v-model="categoryForm.parent_id"
                    :data="categoryTree"
                    :props="treeProps"
                    placeholder="请选择父级分类"
                    :disabled="!isEditing"
                    clearable
                    check-strictly
                  />
                </el-form-item>
                
                <el-form-item label="排序权重" prop="sort_order">
                  <el-input-number
                    v-model="categoryForm.sort_order"
                    :min="0"
                    :max="999"
                    :disabled="!isEditing"
                  />
                </el-form-item>
                
                <el-form-item label="是否启用" prop="is_active">
                  <el-switch
                    v-model="categoryForm.is_active"
                    :disabled="!isEditing"
                  />
                </el-form-item>
                
                <el-form-item label="创建时间" v-if="selectedCategory.id">
                  <el-input
                    :value="formatDate(selectedCategory.created_at)"
                    disabled
                  />
                </el-form-item>
                
                <el-form-item label="更新时间" v-if="selectedCategory.id">
                  <el-input
                    :value="formatDate(selectedCategory.updated_at)"
                    disabled
                  />
                </el-form-item>
              </el-form>
              
              <div class="form-actions">
                <template v-if="!isEditing">
                  <el-button @click="handleEdit">编辑</el-button>
                  <el-button
                    type="danger"
                    @click="handleDelete"
                    :disabled="selectedCategory.resource_count > 0"
                  >
                    删除
                  </el-button>
                </template>
                <template v-else>
                  <el-button type="primary" @click="handleSave" :loading="saving">
                    保存
                  </el-button>
                  <el-button @click="handleCancel">取消</el-button>
                </template>
              </div>
            </div>
          </el-card>
          
          <!-- 分类下的资源列表 -->
          <el-card title="分类资源" class="category-resources-card" style="margin-top: 20px;">
            <div v-if="!selectedCategory" class="empty-selection">
              <el-empty description="请选择一个分类查看资源" />
            </div>
            
            <div v-else class="category-resources">
              <div class="resources-header">
                <span>共 {{ categoryResources.length }} 个资源</span>
                <el-button size="small" @click="handleRefreshResources">
                  <el-icon><Refresh /></el-icon>
                  刷新
                </el-button>
              </div>
              
              <el-table
                :data="categoryResources"
                stripe
                style="width: 100%"
                v-loading="loadingResources"
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
                <el-table-column label="操作" width="120">
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
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 新增/编辑分类对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="500px"
      @close="handleDialogClose"
    >
      <el-form
        ref="dialogFormRef"
        :model="dialogForm"
        :rules="categoryRules"
        label-width="100px"
      >
        <el-form-item label="分类名称" prop="name">
          <el-input v-model="dialogForm.name" placeholder="请输入分类名称" />
        </el-form-item>
        
        <el-form-item label="显示名称" prop="display_name">
          <el-input v-model="dialogForm.display_name" placeholder="请输入显示名称" />
        </el-form-item>
        
        <el-form-item label="分类描述" prop="description">
          <el-input
            v-model="dialogForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入分类描述"
          />
        </el-form-item>
        
        <el-form-item label="父级分类" prop="parent_id">
          <el-tree-select
            v-model="dialogForm.parent_id"
            :data="categoryTree"
            :props="treeProps"
            placeholder="请选择父级分类"
            clearable
            check-strictly
          />
        </el-form-item>
        
        <el-form-item label="排序权重" prop="sort_order">
          <el-input-number
            v-model="dialogForm.sort_order"
            :min="0"
            :max="999"
          />
        </el-form-item>
        
        <el-form-item label="是否启用" prop="is_active">
          <el-switch v-model="dialogForm.is_active" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleDialogSave" :loading="saving">
          保存
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus,
  Edit,
  Delete,
  Folder,
  FolderOpened,
  Refresh
} from '@element-plus/icons-vue'
import type { DataResourceCategory, DataResource } from '@/types/data-resource'

/**
 * 路由实例
 */
const router = useRouter()

/**
 * 响应式数据
 */
const categoryTree = ref<DataResourceCategory[]>([])
const selectedCategory = ref<DataResourceCategory | null>(null)
const categoryResources = ref<DataResource[]>([])
const isEditing = ref(false)
const saving = ref(false)
const loadingResources = ref(false)
const dialogVisible = ref(false)

/**
 * 表单数据
 */
const categoryForm = reactive<Partial<DataResourceCategory>>({
  name: '',
  display_name: '',
  description: '',
  parent_id: null,
  sort_order: 0,
  is_active: true
})

const dialogForm = reactive<Partial<DataResourceCategory>>({
  name: '',
  display_name: '',
  description: '',
  parent_id: null,
  sort_order: 0,
  is_active: true
})

/**
 * 树形组件配置
 */
const treeProps = {
  children: 'children',
  label: 'name',
  value: 'id'
}

/**
 * 表单验证规则
 */
const categoryRules = {
  name: [
    { required: true, message: '请输入分类名称', trigger: 'blur' },
    { min: 2, max: 50, message: '长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  display_name: [
    { required: true, message: '请输入显示名称', trigger: 'blur' },
    { min: 2, max: 100, message: '长度在 2 到 100 个字符', trigger: 'blur' }
  ]
}

/**
 * 对话框标题
 */
const dialogTitle = computed(() => {
  return dialogForm.id ? '编辑分类' : '新增分类'
})

/**
 * 获取分类树数据
 */
const fetchCategoryTree = async () => {
  try {
    // TODO: 调用API获取分类树
    // const response = await dataResourceApi.getCategoryTree()
    // categoryTree.value = response.data
    
    // 模拟数据
    categoryTree.value = [
      {
        id: 1,
        name: 'database',
        display_name: '数据库',
        description: '数据库相关资源',
        parent_id: null,
        sort_order: 1,
        is_active: true,
        resource_count: 5,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
        children: [
          {
            id: 2,
            name: 'mysql',
            display_name: 'MySQL',
            description: 'MySQL数据库',
            parent_id: 1,
            sort_order: 1,
            is_active: true,
            resource_count: 3,
            created_at: '2024-01-01T00:00:00Z',
            updated_at: '2024-01-01T00:00:00Z'
          },
          {
            id: 3,
            name: 'doris',
            display_name: 'Apache Doris',
            description: 'Doris数据库',
            parent_id: 1,
            sort_order: 2,
            is_active: true,
            resource_count: 2,
            created_at: '2024-01-01T00:00:00Z',
            updated_at: '2024-01-01T00:00:00Z'
          }
        ]
      },
      {
        id: 4,
        name: 'file',
        display_name: '文件',
        description: '文件相关资源',
        parent_id: null,
        sort_order: 2,
        is_active: true,
        resource_count: 2,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z'
      }
    ]
  } catch (error) {
    ElMessage.error('获取分类树失败')
  }
}

/**
 * 获取分类下的资源列表
 */
const fetchCategoryResources = async (categoryId: number) => {
  loadingResources.value = true
  
  try {
    // TODO: 调用API获取分类资源
    // const response = await dataResourceApi.getResourcesByCategory(categoryId)
    // categoryResources.value = response.data
    
    // 模拟数据
    categoryResources.value = [
      {
        id: 1,
        name: 'user_behavior',
        display_name: '用户行为数据',
        description: '用户行为分析数据表',
        resource_type: 'doris_table',
        status: 'active',
        category_id: categoryId,
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
    ElMessage.error('获取分类资源失败')
  } finally {
    loadingResources.value = false
  }
}

/**
 * 处理节点点击
 */
const handleNodeClick = (data: DataResourceCategory) => {
  selectedCategory.value = data
  Object.assign(categoryForm, data)
  isEditing.value = false
  
  fetchCategoryResources(data.id!)
}

/**
 * 处理新增分类
 */
const handleAddCategory = () => {
  Object.assign(dialogForm, {
    name: '',
    display_name: '',
    description: '',
    parent_id: null,
    sort_order: 0,
    is_active: true
  })
  dialogVisible.value = true
}

/**
 * 处理新增子分类
 */
const handleAddSubCategory = (parent: DataResourceCategory) => {
  Object.assign(dialogForm, {
    name: '',
    display_name: '',
    description: '',
    parent_id: parent.id,
    sort_order: 0,
    is_active: true
  })
  dialogVisible.value = true
}

/**
 * 处理编辑分类
 */
const handleEditCategory = (data: DataResourceCategory) => {
  Object.assign(dialogForm, data)
  dialogVisible.value = true
}

/**
 * 处理删除分类
 */
const handleDeleteCategory = async (data: DataResourceCategory) => {
  if (data.resource_count && data.resource_count > 0) {
    ElMessage.warning('该分类下还有资源，无法删除')
    return
  }
  
  try {
    await ElMessageBox.confirm(
      `确定要删除分类 "${data.display_name}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    // TODO: 调用删除API
    // await dataResourceApi.deleteCategory(data.id!)
    
    ElMessage.success('删除成功')
    fetchCategoryTree()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

/**
 * 处理编辑
 */
const handleEdit = () => {
  isEditing.value = true
}

/**
 * 处理保存
 */
const handleSave = async () => {
  saving.value = true
  
  try {
    // TODO: 调用更新API
    // await dataResourceApi.updateCategory(selectedCategory.value!.id!, categoryForm)
    
    ElMessage.success('保存成功')
    isEditing.value = false
    fetchCategoryTree()
  } catch (error) {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

/**
 * 处理取消
 */
const handleCancel = () => {
  Object.assign(categoryForm, selectedCategory.value)
  isEditing.value = false
}

/**
 * 处理删除
 */
const handleDelete = async () => {
  if (!selectedCategory.value) return
  
  await handleDeleteCategory(selectedCategory.value)
  selectedCategory.value = null
}

/**
 * 处理对话框保存
 */
const handleDialogSave = async () => {
  saving.value = true
  
  try {
    if (dialogForm.id) {
      // TODO: 调用更新API
      // await dataResourceApi.updateCategory(dialogForm.id, dialogForm)
    } else {
      // TODO: 调用创建API
      // await dataResourceApi.createCategory(dialogForm)
    }
    
    ElMessage.success('保存成功')
    dialogVisible.value = false
    fetchCategoryTree()
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
  Object.assign(dialogForm, {
    name: '',
    display_name: '',
    description: '',
    parent_id: null,
    sort_order: 0,
    is_active: true
  })
}

/**
 * 处理刷新资源
 */
const handleRefreshResources = () => {
  if (selectedCategory.value) {
    fetchCategoryResources(selectedCategory.value.id!)
  }
}

/**
 * 处理查看资源
 */
const handleViewResource = (resource: DataResource) => {
  router.push(`/data-resources/detail/${resource.id}`)
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
  fetchCategoryTree()
})
</script>

<style scoped>
.category-manage {
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

.category-tree-card,
.category-detail-card,
.category-resources-card {
  height: fit-content;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.category-tree {
  max-height: 500px;
  overflow-y: auto;
}

.tree-node {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  padding-right: 8px;
}

.node-content {
  display: flex;
  align-items: center;
  flex: 1;
}

.node-icon {
  margin-right: 8px;
  color: #409eff;
}

.node-label {
  margin-right: 8px;
}

.node-count {
  color: #999;
  font-size: 12px;
}

.node-actions {
  display: none;
}

.tree-node:hover .node-actions {
  display: flex;
}

.empty-selection {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 200px;
}

.category-detail {
  padding: 20px;
}

.category-form {
  margin-bottom: 20px;
}

.form-actions {
  text-align: right;
  padding-top: 20px;
  border-top: 1px solid #eee;
}

.resources-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #eee;
}
</style>