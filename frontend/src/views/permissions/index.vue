<template>
  <div class="permission-management">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">
          <el-icon><Key /></el-icon>
          权限管理
        </h1>
        <p class="page-description">管理系统权限和访问控制</p>
      </div>
      <div class="header-actions">
        <el-button type="primary" @click="showCreateDialog">
          <el-icon><Plus /></el-icon>
          新建权限
        </el-button>
        <el-button @click="expandAll">
          <el-icon><ArrowDown /></el-icon>
          展开全部
        </el-button>
        <el-button @click="collapseAll">
          <el-icon><ArrowRight /></el-icon>
          收起全部
        </el-button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-cards">
      <el-row :gutter="20">
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-icon">
                <el-icon><Key /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-value">{{ stats.total }}</div>
                <div class="stat-label">总权限数</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-icon module">
                <el-icon><Grid /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-value">{{ stats.modules }}</div>
                <div class="stat-label">权限模块</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-icon active">
                <el-icon><CircleCheck /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-value">{{ stats.active }}</div>
                <div class="stat-label">启用权限</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-icon roles">
                <el-icon><UserFilled /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-value">{{ stats.roles }}</div>
                <div class="stat-label">关联角色</div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 筛选和搜索 -->
    <el-card class="filter-card">
      <el-form :model="filters" inline>
        <el-form-item label="搜索">
          <el-input
            v-model="filters.search"
            placeholder="搜索权限名称或描述"
            style="width: 250px"
            clearable
            @input="handleFilter"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-form-item>
        
        <el-form-item label="模块">
          <el-select
            v-model="filters.module"
            placeholder="选择模块"
            clearable
            style="width: 150px"
            @change="handleFilter"
          >
            <el-option label="全部" value="" />
            <el-option label="系统管理" value="system" />
            <el-option label="用户管理" value="user" />
            <el-option label="模型管理" value="model" />
            <el-option label="部署管理" value="deployment" />
            <el-option label="数据管理" value="data" />
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
            <el-option label="启用" :value="true" />
            <el-option label="禁用" :value="false" />
          </el-select>
        </el-form-item>
        
        <el-form-item>
          <el-button @click="resetFilters">
            <el-icon><RefreshLeft /></el-icon>
            重置
          </el-button>
          <el-button type="primary" @click="handleFilter">
            <el-icon><Search /></el-icon>
            搜索
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 权限树 -->
    <el-card class="tree-card">
      <div class="tree-header">
        <h3>权限树结构</h3>
        <div class="tree-actions">
          <el-button size="small" @click="refreshTree">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </div>
      
      <el-tree
        ref="permissionTreeRef"
        :data="permissionTree"
        :props="treeProps"
        node-key="id"
        :default-expand-all="false"
        :expand-on-click-node="false"
        v-loading="treeLoading"
      >
        <template #default="{ node, data }">
          <div class="tree-node">
            <div class="node-content">
              <el-icon v-if="data.type === 'module'" class="module-icon">
                <Grid />
              </el-icon>
              <el-icon v-else class="permission-icon">
                <Key />
              </el-icon>
              <span class="node-label">{{ data.name }}</span>
              <el-tag
                v-if="data.code"
                size="small"
                type="info"
                class="permission-code"
              >
                {{ data.code }}
              </el-tag>
              <el-tag
                :type="data.is_active ? 'success' : 'danger'"
                size="small"
                class="status-tag"
              >
                {{ data.is_active ? '启用' : '禁用' }}
              </el-tag>
            </div>
            
            <div class="node-actions">
              <el-button
                v-if="data.type === 'module'"
                type="primary"
                size="small"
                @click.stop="showCreatePermissionDialog(data)"
              >
                添加权限
              </el-button>
              <el-button
                type="warning"
                size="small"
                @click.stop="showEditDialog(data)"
              >
                编辑
              </el-button>
              <el-button
                v-if="!data.is_system"
                type="danger"
                size="small"
                @click.stop="handleDelete(data)"
              >
                删除
              </el-button>
            </div>
          </div>
        </template>
      </el-tree>
    </el-card>

    <!-- 创建/编辑权限对话框 -->
    <el-dialog
      v-model="permissionDialogVisible"
      :title="dialogTitle"
      width="600px"
      :before-close="handleCloseDialog"
    >
      <el-form
        ref="permissionFormRef"
        :model="permissionForm"
        :rules="permissionRules"
        label-width="100px"
      >
        <el-form-item label="权限类型" prop="type">
          <el-radio-group v-model="permissionForm.type" :disabled="isEditing">
            <el-radio label="module">权限模块</el-radio>
            <el-radio label="permission">具体权限</el-radio>
          </el-radio-group>
        </el-form-item>
        
        <el-form-item
          v-if="permissionForm.type === 'permission'"
          label="所属模块"
          prop="parent_id"
        >
          <el-select
            v-model="permissionForm.parent_id"
            placeholder="选择所属模块"
            style="width: 100%"
            :disabled="isEditing"
          >
            <el-option
              v-for="module in moduleOptions"
              :key="module.id"
              :label="module.name"
              :value="module.id"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="权限名称" prop="name">
          <el-input
            v-model="permissionForm.name"
            placeholder="请输入权限名称"
          />
        </el-form-item>
        
        <el-form-item
          v-if="permissionForm.type === 'permission'"
          label="权限代码"
          prop="code"
        >
          <el-input
            v-model="permissionForm.code"
            placeholder="例如：user:create"
            :disabled="isEditing"
          />
        </el-form-item>
        
        <el-form-item label="权限描述" prop="description">
          <el-input
            v-model="permissionForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入权限描述"
          />
        </el-form-item>
        
        <el-form-item label="状态" prop="is_active">
          <el-radio-group v-model="permissionForm.is_active">
            <el-radio :label="true">启用</el-radio>
            <el-radio :label="false">禁用</el-radio>
          </el-radio-group>
        </el-form-item>
        
        <el-form-item label="排序" prop="sort">
          <el-input-number
            v-model="permissionForm.sort"
            :min="0"
            :max="999"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="permissionDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleSubmit" :loading="submitting">
            {{ isEditing ? '更新' : '创建' }}
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import {
  Key,
  Plus,
  ArrowDown,
  ArrowRight,
  Grid,
  CircleCheck,
  UserFilled,
  Search,
  RefreshLeft,
  Refresh
} from '@element-plus/icons-vue'
import { permissionApi, type Permission } from '@/api/roles'

// 响应式数据
const treeLoading = ref(false)
const submitting = ref(false)
const permissionDialogVisible = ref(false)
const isEditing = ref(false)
const isCreatingPermission = ref(false)
const permissionFormRef = ref<FormInstance>()
const permissionTreeRef = ref()
const currentParentModule = ref<any>(null)

// 统计数据
const stats = reactive({
  total: 0,
  modules: 0,
  active: 0,
  roles: 0
})

// 筛选条件
const filters = reactive({
  search: '',
  module: '',
  status: '' as boolean | ''
})

// 权限树数据
const permissionTree = ref<any[]>([])

// 权限表单
const permissionForm = reactive({
  id: 0,
  name: '',
  code: '',
  description: '',
  type: 'module',
  parent_id: null as number | null,
  is_active: true,
  sort: 0,
  is_system: false
})

// 树形组件属性
const treeProps = {
  children: 'children',
  label: 'name',
  key: 'id'
}

// 对话框标题
const dialogTitle = computed(() => {
  if (isCreatingPermission.value) {
    return '添加权限'
  }
  return isEditing.value ? '编辑权限' : '新建权限模块'
})

// 模块选项
const moduleOptions = computed(() => {
  return permissionTree.value.filter(item => item.type === 'module')
})

// 表单验证规则
const permissionRules: FormRules = {
  type: [
    { required: true, message: '请选择权限类型', trigger: 'change' }
  ],
  name: [
    { required: true, message: '请输入权限名称', trigger: 'blur' },
    { min: 2, max: 50, message: '权限名称长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  code: [
    { required: true, message: '请输入权限代码', trigger: 'blur' },
    { pattern: /^[a-z]+:[a-z]+$/, message: '权限代码格式为：模块:操作', trigger: 'blur' }
  ],
  parent_id: [
    { required: true, message: '请选择所属模块', trigger: 'change' }
  ],
  description: [
    { max: 200, message: '描述不能超过 200 个字符', trigger: 'blur' }
  ]
}

/**
 * 加载权限树
 */
const loadPermissionTree = async () => {
  treeLoading.value = true
  try {
    const response = await permissionApi.getPermissionTree()
    // 后端返回 ResponseModel，data: { modules: Array<{ module: string; permissions: PermissionTreeNode[] }> }
    const modules = (response as any)?.data?.modules || []
    // 统一转换为 el-tree 可用的节点结构
    permissionTree.value = modules.map((mod: any) => ({
      id: `module:${mod.module}`,
      name: mod.module,
      type: 'module',
      is_active: true,
      is_system: false,
      children: (mod.permissions || []).map((perm: any) => ({
        id: perm.id,
        name: perm.name,
        code: perm.code,
        type: 'permission',
        is_active: perm.status,
        is_system: perm.is_system
      }))
    }))
    
    // 计算统计数据
    updateStats()
  } catch (error: any) {
    console.error('加载权限数据失败:', error)
    ElMessage.error(error.response?.data?.message || '加载权限数据失败')
  } finally {
    treeLoading.value = false
  }
}

/**
 * 更新统计数据
 */
const updateStats = () => {
  let totalPermissions = 0
  let activePermissions = 0
  let moduleCount = 0
  
  const countNodes = (nodes: any[]) => {
    nodes.forEach(node => {
      if (node.type === 'module') {
        moduleCount++
      } else {
        totalPermissions++
        if (node.is_active) {
          activePermissions++
        }
      }
      
      if (node.children) {
        countNodes(node.children)
      }
    })
  }
  
  countNodes(permissionTree.value)
  
  stats.total = totalPermissions
  stats.modules = moduleCount
  stats.active = activePermissions
  stats.roles = 0 // 需要额外API获取关联角色数
}

/**
 * 展开全部
 */
const expandAll = () => {
  const allKeys: string[] = []
  const collectKeys = (nodes: any[]) => {
    nodes.forEach(node => {
      allKeys.push(node.id)
      if (node.children) {
        collectKeys(node.children)
      }
    })
  }
  collectKeys(permissionTree.value)
  
  allKeys.forEach(key => {
    permissionTreeRef.value?.store.nodesMap[key]?.expand()
  })
}

/**
 * 收起全部
 */
const collapseAll = () => {
  const allKeys: string[] = []
  const collectKeys = (nodes: any[]) => {
    nodes.forEach(node => {
      allKeys.push(node.id)
      if (node.children) {
        collectKeys(node.children)
      }
    })
  }
  collectKeys(permissionTree.value)
  
  allKeys.forEach(key => {
    permissionTreeRef.value?.store.nodesMap[key]?.collapse()
  })
}

/**
 * 刷新权限树
 */
const refreshTree = () => {
  loadPermissionTree()
}

/**
 * 显示创建对话框
 */
const showCreateDialog = () => {
  isEditing.value = false
  isCreatingPermission.value = false
  Object.assign(permissionForm, {
    id: 0,
    name: '',
    code: '',
    description: '',
    type: 'module',
    parent_id: null,
    is_active: true,
    sort: 0,
    is_system: false
  })
  permissionDialogVisible.value = true
}

/**
 * 显示创建权限对话框
 */
const showCreatePermissionDialog = (module: any) => {
  isEditing.value = false
  isCreatingPermission.value = true
  currentParentModule.value = module
  Object.assign(permissionForm, {
    id: 0,
    name: '',
    code: '',
    description: '',
    type: 'permission',
    parent_id: module.id,
    is_active: true,
    sort: 0,
    is_system: false
  })
  permissionDialogVisible.value = true
}

/**
 * 显示编辑对话框
 */
const showEditDialog = (data: any) => {
  isEditing.value = true
  isCreatingPermission.value = false
  Object.assign(permissionForm, { ...data })
  permissionDialogVisible.value = true
}

/**
 * 处理筛选
 */
const handleFilter = () => {
  // 实际项目中这里会调用API进行筛选
  loadPermissionTree()
}

/**
 * 重置筛选条件
 */
const resetFilters = () => {
  filters.search = ''
  filters.module = ''
  filters.status = ''
  handleFilter()
}

/**
 * 关闭对话框
 */
const handleCloseDialog = () => {
  permissionFormRef.value?.resetFields()
  permissionDialogVisible.value = false
}

/**
 * 提交表单
 */
const handleSubmit = async () => {
  if (!permissionFormRef.value) return
  
  try {
    await permissionFormRef.value.validate()
    submitting.value = true
    
    if (isEditing.value) {
      // 更新权限
      await permissionApi.updatePermission(permissionForm.id, {
        name: permissionForm.name,
        code: permissionForm.code,
        description: permissionForm.description,
        is_active: permissionForm.is_active,
        sort: permissionForm.sort
      })
      ElMessage.success('权限更新成功')
    } else {
      // 创建权限
      await permissionApi.createPermission({
        name: permissionForm.name,
        code: permissionForm.code,
        description: permissionForm.description,
        type: permissionForm.type,
        parent_id: permissionForm.parent_id,
        is_active: permissionForm.is_active,
        sort: permissionForm.sort
      })
      ElMessage.success('权限创建成功')
    }
    
    permissionDialogVisible.value = false
    loadPermissionTree()
  } catch (error: any) {
    console.error('操作失败:', error)
    ElMessage.error(error.response?.data?.message || '操作失败')
  } finally {
    submitting.value = false
  }
}

/**
 * 删除权限
 */
const handleDelete = async (data: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除${data.type === 'module' ? '模块' : '权限'} "${data.name}" 吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await permissionApi.deletePermission(data.id)
    ElMessage.success('删除成功')
    loadPermissionTree()
  } catch (error: any) {
    if (error.response) {
      console.error('删除失败:', error)
      ElMessage.error(error.response?.data?.message || '删除失败')
    }
    // 用户取消删除时不显示错误
  }
}

// 初始化
onMounted(() => {
  loadPermissionTree()
})
</script>

<style scoped>
.permission-management {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 8px 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.page-description {
  color: #606266;
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.stats-cards {
  margin-bottom: 20px;
}

.stat-card {
  height: 100px;
}

.stat-content {
  display: flex;
  align-items: center;
  height: 100%;
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 16px;
  background: #f0f2f5;
  color: #606266;
  font-size: 24px;
}

.stat-icon.module {
  background: #e7f7ff;
  color: #1890ff;
}

.stat-icon.active {
  background: #f6ffed;
  color: #52c41a;
}

.stat-icon.roles {
  background: #fff7e6;
  color: #fa8c16;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
  line-height: 1;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 4px;
}

.filter-card {
  margin-bottom: 20px;
}

.tree-card {
  margin-bottom: 20px;
}

.tree-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #ebeef5;
}

.tree-header h3 {
  margin: 0;
  font-size: 16px;
  color: #303133;
}

.tree-actions {
  display: flex;
  gap: 8px;
}

.tree-node {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  padding: 4px 0;
}

.node-content {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
}

.module-icon {
  color: #1890ff;
}

.permission-icon {
  color: #52c41a;
}

.node-label {
  font-weight: 500;
  color: #303133;
}

.permission-code {
  margin-left: 8px;
}

.status-tag {
  margin-left: 8px;
}

.node-actions {
  display: flex;
  gap: 8px;
  opacity: 0;
  transition: opacity 0.2s;
}

.tree-node:hover .node-actions {
  opacity: 1;
}
</style>