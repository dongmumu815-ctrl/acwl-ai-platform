<template>
  <div class="role-management">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">
          <el-icon><UserFilled /></el-icon>
          角色管理
        </h1>
        <p class="page-description">管理系统角色和权限分配</p>
      </div>
      <div class="header-actions">
        <el-button type="primary" @click="showCreateDialog">
          <el-icon><Plus /></el-icon>
          新建角色
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
                <el-icon><UserFilled /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-value">{{ stats.total }}</div>
                <div class="stat-label">总角色数</div>
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
                <div class="stat-label">启用角色</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-icon system">
                <el-icon><Key /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-value">{{ stats.system }}</div>
                <div class="stat-label">系统角色</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
              <div class="stat-content">
                <div class="stat-icon custom">
                  <el-icon><Setting /></el-icon>
                </div>
                <div class="stat-info">
                  <div class="stat-value">{{ stats.custom }}</div>
                  <div class="stat-label">自定义角色</div>
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
            placeholder="搜索角色名称或描述"
            style="width: 250px"
            clearable
            @input="handleFilter"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
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
            <el-option label="启用" value="active" />
            <el-option label="禁用" value="disabled" />
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

    <!-- 角色列表 -->
    <el-card class="table-card">
      <el-table
        :data="roles"
        v-loading="loading"
        stripe
        style="width: 100%"
      >
        <el-table-column prop="name" label="角色名称" min-width="150">
          <template #default="{ row }">
            <div class="role-name">
              <el-icon v-if="row.is_system" class="system-icon"><Key /></el-icon>
              {{ row.name }}
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="code" label="角色代码" width="120" />
        
        <el-table-column prop="description" label="描述" min-width="200" />
        
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status ? 'success' : 'danger'" size="small">
              {{ row.status ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              size="small"
              @click="showEditDialog(row)"
            >
              编辑
            </el-button>
            <el-button
              type="warning"
              size="small"
              @click="showPermissionsDialog(row)"
            >
              权限
            </el-button>
            <el-button
              v-if="!row.is_system"
              type="danger"
              size="small"
              @click="handleDelete(row)"
            >
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
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 创建/编辑角色对话框 -->
    <el-dialog
      v-model="roleDialogVisible"
      :title="isEditing ? '编辑角色' : '新建角色'"
      width="600px"
      :before-close="handleCloseDialog"
    >
      <el-form
        ref="roleFormRef"
        :model="roleForm"
        :rules="roleRules"
        label-width="80px"
      >
        <el-form-item label="角色名称" prop="name">
          <el-input
            v-model="roleForm.name"
            placeholder="请输入角色名称"
            :disabled="roleForm.is_system"
          />
        </el-form-item>
        
        <el-form-item label="角色代码" prop="code">
          <el-input
            v-model="roleForm.code"
            placeholder="请输入角色代码，如：admin、user"
            :disabled="roleForm.is_system"
          />
        </el-form-item>
        
        <el-form-item label="角色描述" prop="description">
          <el-input
            v-model="roleForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入角色描述"
          />
        </el-form-item>
        
        <el-form-item label="状态" prop="status">
          <el-radio-group v-model="roleForm.status">
            <el-radio :label="true">启用</el-radio>
            <el-radio :label="false">禁用</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="roleDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleSubmit" :loading="submitting">
            {{ isEditing ? '更新' : '创建' }}
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 权限配置对话框 -->
    <el-dialog
      v-model="permissionsDialogVisible"
      title="权限配置"
      width="800px"
    >
      <div class="permissions-content">
        <div class="permissions-header">
          <h3>为角色 "{{ currentRole?.name }}" 配置权限</h3>
          <el-button type="primary" size="small" @click="selectAllPermissions">
            全选
          </el-button>
          <el-button size="small" @click="clearAllPermissions">
            清空
          </el-button>
        </div>
        
        <el-tree
          ref="permissionTreeRef"
          :data="permissionTree"
          :props="treeProps"
          show-checkbox
          node-key="id"
          :default-checked-keys="selectedPermissions"
          @check="handlePermissionCheck"
        />
      </div>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="permissionsDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="savePermissions" :loading="savingPermissions">
            保存权限
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import {
  UserFilled,
  Plus,
  CircleCheck,
  Key,
  User,
  Search,
  RefreshLeft,
  Setting
} from '@element-plus/icons-vue'
import { roleApi, permissionApi, type Role, type RoleCreate, type RoleUpdate, type Permission } from '@/api/roles'

// 响应式数据
const loading = ref(false)
const submitting = ref(false)
const savingPermissions = ref(false)
const roleDialogVisible = ref(false)
const permissionsDialogVisible = ref(false)
const isEditing = ref(false)
const roleFormRef = ref<FormInstance>()
const permissionTreeRef = ref()
const currentRole = ref<any>(null)

// 统计数据
const stats = ref({
  total: 0,
  active: 0,
  system: 0,
  custom: 0
})

// 筛选条件
const filters = reactive({
  search: '',
  status: ''
})

// 分页
const pagination = reactive({
  currentPage: 1,
  pageSize: 20,
  total: 0
})

// 角色列表
const roles = ref<Role[]>([])

// 角色表单
const roleForm = reactive({
  id: 0,
  name: '',
  code: '',
  description: '',
  status: true,
  is_system: false
})

// 权限相关
const permissionTree = ref<any[]>([])
const selectedPermissions = ref<number[]>([])
const treeProps = {
  children: 'children',
  label: 'name',
  key: 'id'
}

// 表单验证规则
const roleRules: FormRules = {
  name: [
    { required: true, message: '请输入角色名称', trigger: 'blur' },
    { min: 2, max: 50, message: '角色名称长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  code: [
    { required: true, message: '请输入角色代码', trigger: 'blur' },
    { min: 2, max: 50, message: '角色代码长度在 2 到 50 个字符', trigger: 'blur' },
    { pattern: /^[a-zA-Z0-9_-]+$/, message: '角色代码只能包含字母、数字、下划线和横线', trigger: 'blur' }
  ],
  description: [
    { max: 200, message: '描述不能超过 200 个字符', trigger: 'blur' }
  ]
}

/**
 * 格式化日期
 */
const formatDate = (date: string) => {
  if (!date) return '-'
  return new Date(date).toLocaleString('zh-CN')
}

/**
 * 加载角色列表
 */
/**
 * 加载角色列表
 * - 使用后端通用响应结构 ApiResponse<RoleListResponse>
 * - 支持 status 过滤与分页
 */
const loadRoles = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.currentPage,
      size: pagination.pageSize,
      search: filters.search || undefined,
      status: filters.status === 'active' ? true : filters.status === 'disabled' ? false : undefined
    }
    
    const response = await roleApi.getRoles(params)
    roles.value = response.data.items
    pagination.total = response.data.total
    
    // 更新统计数据
    stats.value.total = response.data.total
    stats.value.active = response.data.items.filter((role: Role) => (role as any).status).length
    stats.value.system = response.data.items.filter((role: Role) => role.is_system).length
    stats.value.custom = response.data.items.filter((role: Role) => !role.is_system).length
    
  } catch (error: any) {
    console.error('加载角色列表失败:', error)
    ElMessage.error(error.response?.data?.message || '加载角色列表失败')
  } finally {
    loading.value = false
  }
}

/**
 * 加载权限树
 */
/**
 * 加载权限树
 * - 将后端 modules 列表转换为 el-tree 所需结构
 */
const loadPermissionTree = async () => {
  try {
    const response = await permissionApi.getPermissionTree()
    const modules = (response as any)?.data?.modules || []
    permissionTree.value = modules.map((mod: any) => ({
      id: `module:${mod.module}`,
      name: mod.module,
      children: (mod.permissions || []).map((perm: any) => ({
        id: perm.id,
        name: perm.name,
        code: perm.code
      }))
    }))
  } catch (error: any) {
    console.error('加载权限数据失败:', error)
    ElMessage.error(error.response?.data?.message || '加载权限数据失败')
  }
}

/**
 * 显示创建对话框
 */
/**
 * 显示创建角色对话框
 */
const showCreateDialog = () => {
  isEditing.value = false
  Object.assign(roleForm, {
    id: 0,
    name: '',
    code: '',
    description: '',
    status: true,
    is_system: false
  })
  roleDialogVisible.value = true
}

/**
 * 显示编辑对话框
 */
const showEditDialog = (role: any) => {
  isEditing.value = true
  Object.assign(roleForm, { ...role })
  roleDialogVisible.value = true
}

/**
 * 显示权限配置对话框
 */
/**
 * 显示权限配置对话框
 * - 加载权限树并初始化已选权限
 */
const showPermissionsDialog = async (role: Role) => {
  currentRole.value = role
  await loadPermissionTree()
  
  try {
    // 加载角色已有权限
    const response = await roleApi.getRolePermissions(role.id)
    const perms = (response as any)?.data?.permissions || []
    selectedPermissions.value = perms.map((p: any) => p.id)
  } catch (error: any) {
    console.error('加载角色权限失败:', error)
    selectedPermissions.value = []
  }
  
  permissionsDialogVisible.value = true
}

/**
 * 处理筛选
 */
const handleFilter = () => {
  // 实际项目中这里会调用API进行筛选
  loadRoles()
}

/**
 * 重置筛选条件
 */
const resetFilters = () => {
  filters.search = ''
  filters.status = ''
  handleFilter()
}

/**
 * 处理分页大小变化
 */
const handleSizeChange = (size: number) => {
  pagination.pageSize = size
  loadRoles()
}

/**
 * 处理页码变化
 */
const handleCurrentChange = (page: number) => {
  pagination.currentPage = page
  loadRoles()
}

/**
 * 关闭对话框
 */
const handleCloseDialog = () => {
  roleFormRef.value?.resetFields()
  roleDialogVisible.value = false
}

/**
 * 提交表单
 */
/**
 * 提交角色表单
 * - 创建/更新均提交 status 字段
 */
const handleSubmit = async () => {
  if (!roleFormRef.value) return
  
  try {
    await roleFormRef.value.validate()
    submitting.value = true
    
    if (isEditing.value) {
      // 更新角色
      const updateData: RoleUpdate = {
        name: roleForm.name,
        description: roleForm.description,
        status: roleForm.status,
        code: roleForm.code
      }
      await roleApi.updateRole(roleForm.id, updateData)
      ElMessage.success('角色更新成功')
    } else {
      // 创建角色
      const createData: RoleCreate = {
        name: roleForm.name,
        code: roleForm.code,
        description: roleForm.description,
        status: roleForm.status
      }
      await roleApi.createRole(createData)
      ElMessage.success('角色创建成功')
    }
    
    roleDialogVisible.value = false
    loadRoles()
  } catch (error: any) {
    console.error('操作失败:', error)
    ElMessage.error(error.response?.data?.message || '操作失败')
  } finally {
    submitting.value = false
  }
}

/**
 * 删除角色
 */
const handleDelete = async (role: Role) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除角色 "${role.name}" 吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await roleApi.deleteRole(role.id)
    ElMessage.success('角色删除成功')
    loadRoles()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('删除角色失败:', error)
      ElMessage.error(error.response?.data?.message || '删除角色失败')
    }
  }
}

/**
 * 全选权限
 */
const selectAllPermissions = () => {
  const allKeys: string[] = []
  const collectKeys = (nodes: any[]) => {
    nodes.forEach(node => {
      if (node.children) {
        collectKeys(node.children)
      } else {
        allKeys.push(node.id)
      }
    })
  }
  collectKeys(permissionTree.value)
  permissionTreeRef.value?.setCheckedKeys(allKeys)
}

/**
 * 清空权限
 */
const clearAllPermissions = () => {
  permissionTreeRef.value?.setCheckedKeys([])
}

/**
 * 处理权限选择
 */
const handlePermissionCheck = () => {
  // 权限选择逻辑
}

/**
 * 保存权限
 */
const savePermissions = async () => {
  if (!currentRole.value) return
  
  try {
    savingPermissions.value = true
    
    // 仅提交叶子节点（具体权限）的 ID，过滤非数字键（模块键形如 "module:xxx"）
    const checkedLeafKeys = permissionTreeRef.value?.getCheckedKeys(true) || []
    const permissionIds = (checkedLeafKeys as Array<string | number>).filter(k => typeof k === 'number') as number[]
    
    await roleApi.assignPermissions(currentRole.value.id, permissionIds)
    
    ElMessage.success('权限配置保存成功')
    permissionsDialogVisible.value = false
    loadRoles()
  } catch (error: any) {
    console.error('保存权限失败:', error)
    ElMessage.error(error.response?.data?.message || '保存权限失败')
  } finally {
    savingPermissions.value = false
  }
}

// 初始化
onMounted(() => {
  loadRoles()
})
</script>

<style scoped>
.role-management {
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

.stat-icon.active {
  background: #e7f7ff;
  color: #1890ff;
}

.stat-icon.admin {
  background: #fff7e6;
  color: #fa8c16;
}

.stat-icon.users {
  background: #f6ffed;
  color: #52c41a;
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

.table-card {
  margin-bottom: 20px;
}

.role-name {
  display: flex;
  align-items: center;
  gap: 8px;
}

.system-icon {
  color: #fa8c16;
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

.permissions-content {
  max-height: 400px;
  overflow-y: auto;
}

.permissions-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #ebeef5;
}

.permissions-header h3 {
  margin: 0;
  font-size: 16px;
  color: #303133;
}
</style>