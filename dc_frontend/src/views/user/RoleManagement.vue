<template>
  <div class="role-management-container">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1 class="page-title">
        <el-icon><UserFilled /></el-icon>
        角色管理
      </h1>
      <p class="page-description">管理系统角色和权限配置</p>
    </div>

    <!-- 操作栏 -->
    <div class="action-bar">
      <div class="action-left">
        <el-button type="primary" @click="addRole">
          <el-icon><Plus /></el-icon>
          新增角色
        </el-button>
        <el-button @click="refreshRoles">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
      
      <div class="action-right">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索角色..."
          style="width: 200px"
          clearable
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
      </div>
    </div>

    <!-- 角色列表 -->
    <div class="roles-content">
      <el-table
        :data="filteredRoles"
        v-loading="loading"
        stripe
        style="width: 100%"
      >
        <el-table-column prop="name" label="角色名称" min-width="150">
          <template #default="{ row }">
            <div class="role-name">
              <el-icon class="role-icon"><UserFilled /></el-icon>
              <span>{{ row.name }}</span>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="code" label="角色代码" width="120" />
        
        <el-table-column prop="description" label="描述" min-width="200" />
        
        <el-table-column prop="userCount" label="用户数量" width="100">
          <template #default="{ row }">
            <el-tag type="info">{{ row.userCount }}</el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === '启用' ? 'success' : 'danger'">
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="createdAt" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.createdAt) }}
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="250" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              size="small"
              @click="editRole(row)"
            >
              编辑
            </el-button>
            <el-button
              type="info"
              size="small"
              @click="managePermissions(row)"
            >
              权限
            </el-button>
            <el-button
              :type="row.status === '启用' ? 'warning' : 'success'"
              size="small"
              @click="toggleStatus(row)"
            >
              {{ row.status === '启用' ? '禁用' : '启用' }}
            </el-button>
            <el-button
              type="danger"
              size="small"
              @click="deleteRole(row)"
              :disabled="row.userCount > 0"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 分页 -->
    <div class="pagination-container">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50, 100]"
        :total="totalRoles"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>

    <!-- 新增/编辑角色对话框 -->
    <el-dialog
      v-model="roleDialogVisible"
      :title="isEdit ? '编辑角色' : '新增角色'"
      width="500px"
    >
      <el-form :model="roleForm" :rules="roleRules" ref="roleFormRef" label-width="100px">
        <el-form-item label="角色名称" prop="name">
          <el-input v-model="roleForm.name" placeholder="请输入角色名称" />
        </el-form-item>
        
        <el-form-item label="角色代码" prop="code">
          <el-input v-model="roleForm.code" placeholder="请输入角色代码" :disabled="isEdit" />
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
            <el-radio label="启用">启用</el-radio>
            <el-radio label="禁用">禁用</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="roleDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveRole">保存</el-button>
      </template>
    </el-dialog>

    <!-- 权限管理对话框 -->
    <el-dialog
      v-model="permissionDialogVisible"
      title="权限管理"
      width="600px"
    >
      <div class="permission-content">
        <div class="permission-header">
          <h4>为角色 "{{ currentRole?.name }}" 分配权限</h4>
        </div>
        
        <el-tree
          ref="permissionTreeRef"
          :data="permissionTree"
          :props="treeProps"
          show-checkbox
          node-key="id"
          :default-checked-keys="checkedPermissions"
          @check="handlePermissionCheck"
        />
      </div>
      
      <template #footer>
        <el-button @click="permissionDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="savePermissions">保存权限</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { getRoles, createRole, updateRole, deleteRole } from '@/api/user'

// 响应式数据
const loading = ref(false)
const searchKeyword = ref('')
const currentPage = ref(1)
const pageSize = ref(20)
const totalRoles = ref(0)
const roleDialogVisible = ref(false)
const permissionDialogVisible = ref(false)
const isEdit = ref(false)
const currentRole = ref<any>(null)
const checkedPermissions = ref<string[]>([])

// 表单引用
const roleFormRef = ref<FormInstance>()
const permissionTreeRef = ref()

// 角色数据
const roles = ref([
  {
    id: 1,
    name: '超级管理员',
    code: 'super_admin',
    description: '拥有系统所有权限',
    userCount: 2,
    status: '启用',
    createdAt: '2024-01-15 10:30:00'
  },
  {
    id: 2,
    name: '数据管理员',
    code: 'data_admin',
    description: '负责数据管理和维护',
    userCount: 5,
    status: '启用',
    createdAt: '2024-01-14 15:20:00'
  },
  {
    id: 3,
    name: '普通用户',
    code: 'user',
    description: '基础数据查看权限',
    userCount: 25,
    status: '启用',
    createdAt: '2024-01-13 09:15:00'
  },
  {
    id: 4,
    name: '访客',
    code: 'guest',
    description: '只读权限',
    userCount: 0,
    status: '禁用',
    createdAt: '2024-01-12 14:45:00'
  }
])

// 角色表单
const roleForm = ref({
  name: '',
  code: '',
  description: '',
  status: '启用'
})

// 表单验证规则
const roleRules: FormRules = {
  name: [
    { required: true, message: '请输入角色名称', trigger: 'blur' },
    { min: 2, max: 20, message: '长度在 2 到 20 个字符', trigger: 'blur' }
  ],
  code: [
    { required: true, message: '请输入角色代码', trigger: 'blur' },
    { pattern: /^[a-zA-Z_][a-zA-Z0-9_]*$/, message: '只能包含字母、数字和下划线，且以字母或下划线开头', trigger: 'blur' }
  ],
  description: [
    { max: 200, message: '描述不能超过200个字符', trigger: 'blur' }
  ]
}

// 权限树数据
const permissionTree = ref([
  {
    id: 'dashboard',
    label: '仪表盘',
    children: [
      { id: 'dashboard.view', label: '查看仪表盘' }
    ]
  },
  {
    id: 'data',
    label: '数据管理',
    children: [
      { id: 'data.view', label: '查看数据' },
      { id: 'data.create', label: '创建数据' },
      { id: 'data.edit', label: '编辑数据' },
      { id: 'data.delete', label: '删除数据' },
      { id: 'data.export', label: '导出数据' }
    ]
  },
  {
    id: 'user',
    label: '用户管理',
    children: [
      { id: 'user.view', label: '查看用户' },
      { id: 'user.create', label: '创建用户' },
      { id: 'user.edit', label: '编辑用户' },
      { id: 'user.delete', label: '删除用户' }
    ]
  },
  {
    id: 'role',
    label: '角色管理',
    children: [
      { id: 'role.view', label: '查看角色' },
      { id: 'role.create', label: '创建角色' },
      { id: 'role.edit', label: '编辑角色' },
      { id: 'role.delete', label: '删除角色' },
      { id: 'role.permission', label: '分配权限' }
    ]
  },
  {
    id: 'system',
    label: '系统设置',
    children: [
      { id: 'system.config', label: '系统配置' },
      { id: 'system.log', label: '系统日志' },
      { id: 'system.backup', label: '数据备份' }
    ]
  }
])

// 树形控件属性
const treeProps = {
  children: 'children',
  label: 'label'
}

/**
 * 过滤后的角色列表
 */
const filteredRoles = computed(() => {
  if (!searchKeyword.value) {
    return roles.value
  }
  return roles.value.filter(role => 
    role.name.toLowerCase().includes(searchKeyword.value.toLowerCase()) ||
    role.code.toLowerCase().includes(searchKeyword.value.toLowerCase())
  )
})

/**
 * 格式化日期
 */
const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleString('zh-CN')
}

/**
 * 新增角色
 */
const addRole = () => {
  isEdit.value = false
  roleForm.value = {
    name: '',
    code: '',
    description: '',
    status: '启用'
  }
  roleDialogVisible.value = true
}

/**
 * 编辑角色
 */
const editRole = (role: any) => {
  isEdit.value = true
  roleForm.value = { ...role }
  roleDialogVisible.value = true
}

/**
 * 保存角色
 */
const saveRole = () => {
  roleFormRef.value?.validate((valid) => {
    if (valid) {
      if (isEdit.value) {
        // 更新角色
        const index = roles.value.findIndex(r => r.id === roleForm.value.id)
        if (index > -1) {
          Object.assign(roles.value[index], roleForm.value)
          ElMessage.success('角色更新成功')
        }
      } else {
        // 新增角色
        const newRole = {
          ...roleForm.value,
          id: Date.now(),
          userCount: 0,
          createdAt: new Date().toLocaleString('zh-CN')
        }
        roles.value.unshift(newRole)
        ElMessage.success('角色创建成功')
      }
      roleDialogVisible.value = false
    }
  })
}

/**
 * 管理权限
 */
const managePermissions = (role: any) => {
  currentRole.value = role
  // 模拟获取角色权限
  checkedPermissions.value = role.code === 'super_admin' 
    ? ['dashboard.view', 'data.view', 'data.create', 'data.edit', 'data.delete', 'data.export', 'user.view', 'user.create', 'user.edit', 'user.delete', 'role.view', 'role.create', 'role.edit', 'role.delete', 'role.permission', 'system.config', 'system.log', 'system.backup']
    : role.code === 'data_admin'
    ? ['dashboard.view', 'data.view', 'data.create', 'data.edit', 'data.export']
    : ['dashboard.view', 'data.view']
  
  permissionDialogVisible.value = true
}

/**
 * 处理权限选择
 */
const handlePermissionCheck = (data: any, checked: any) => {
  // 处理权限选择逻辑
}

/**
 * 保存权限
 */
const savePermissions = () => {
  const checkedKeys = permissionTreeRef.value.getCheckedKeys()
  const halfCheckedKeys = permissionTreeRef.value.getHalfCheckedKeys()
  const allCheckedKeys = [...checkedKeys, ...halfCheckedKeys]
  
  ElMessage.success(`已为角色 "${currentRole.value?.name}" 分配 ${allCheckedKeys.length} 个权限`)
  permissionDialogVisible.value = false
}

/**
 * 切换状态
 */
const toggleStatus = (role: any) => {
  const newStatus = role.status === '启用' ? '禁用' : '启用'
  ElMessageBox.confirm(
    `确定要${newStatus}角色 "${role.name}" 吗？`,
    '确认操作',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(() => {
    role.status = newStatus
    ElMessage.success(`角色已${newStatus}`)
  }).catch(() => {
    // 用户取消操作
  })
}

/**
 * 删除角色
 */
const deleteRole = (role: any) => {
  if (role.userCount > 0) {
    ElMessage.warning('该角色下还有用户，无法删除')
    return
  }
  
  ElMessageBox.confirm(
    `确定要删除角色 "${role.name}" 吗？`,
    '确认删除',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(() => {
    const index = roles.value.findIndex(r => r.id === role.id)
    if (index > -1) {
      roles.value.splice(index, 1)
      ElMessage.success('角色删除成功')
    }
  }).catch(() => {
    // 用户取消删除
  })
}

/**
 * 刷新角色列表
 */
const refreshRoles = () => {
  loading.value = true
  // 模拟刷新
  setTimeout(() => {
    loading.value = false
    ElMessage.success('角色列表已刷新')
  }, 1000)
}

/**
 * 处理页面大小变化
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
 * 组件挂载时加载数据
 */
onMounted(() => {
  totalRoles.value = roles.value.length
})
</script>

<style lang="scss" scoped>
.role-management-container {
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
  border: 1px solid var(--el-border-color-light);
  
  .action-left {
    display: flex;
    gap: 12px;
  }
}

.roles-content {
  background: var(--el-bg-color);
  border-radius: 8px;
  border: 1px solid var(--el-border-color-light);
  overflow: hidden;
  
  .role-name {
    display: flex;
    align-items: center;
    
    .role-icon {
      margin-right: 8px;
      color: var(--el-color-primary);
    }
  }
}

.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 20px;
  padding: 16px;
  background: var(--el-bg-color);
  border-radius: 8px;
  border: 1px solid var(--el-border-color-light);
}

.permission-content {
  .permission-header {
    margin-bottom: 16px;
    padding-bottom: 12px;
    border-bottom: 1px solid var(--el-border-color-light);
    
    h4 {
      margin: 0;
      color: var(--el-text-color-primary);
    }
  }
}

// 响应式设计
@media (max-width: 768px) {
  .role-management-container {
    padding: 16px;
  }
  
  .action-bar {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
    
    .action-left {
      justify-content: center;
    }
    
    .action-right {
      display: flex;
      justify-content: center;
    }
  }
}
</style>