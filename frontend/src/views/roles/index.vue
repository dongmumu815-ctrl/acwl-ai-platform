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
      @opened="onPermissionsDialogOpened"
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
          :key="treeRenderKey"
          :data="permissionTree"
          :props="treeProps"
          show-checkbox
          default-expand-all
          :render-after-expand="false"
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
import { ref, reactive, onMounted, nextTick } from 'vue'
import { watch } from 'vue'
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
// 树渲染key：用于强制重新渲染以触发 default-checked-keys
const treeRenderKey = ref(0)
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
// 角色已有权限的代码（如 agent:read），用于兜底按code勾选
const selectedPermissionCodes = ref<string[]>([])
// 调试开关：打印更详细的权限相关日志
const DEBUG_PERMISSION = true
const logPerm = (...args: any[]) => { if (DEBUG_PERMISSION) console.log('[角色权限]', ...args) }
const treeProps = {
  children: 'children',
  label: 'name',
  key: 'id'
}

/**
 * 平台与模块映射关系
 * 用于在前端对后端返回的模块进行平台分组，实现与权限页一致的“AI中台/数据中台/其他”结构。
 */
const PLATFORM_MODULE_MAP: Record<'AI中台' | '数据中台', string[]> = {
  AI中台: [
    'agent',
    'model',
    'instruction_set',
    'deployment',
    'training',
    'system',
    'user',
    'role',
    'permission',
    'dataset',
    'datasource',
    'project'
  ],
  数据中台: [
    'data'
  ]
}

/**
 * 根据模块及其权限码推断所属平台
 * 推断策略：
 * 1) 若模块下存在权限码以 `data:` 开头，则归“数据中台”
 * 2) 若模块下存在权限码以 `ai:` 开头，则归“AI中台”
 * 3) 否则，按模块名在 AI/数据中台清单中匹配，仍无法匹配则归“其他”
 * @param mod 模块名
 * @param children 模块下权限节点列表
 * @returns 平台名字：'AI中台'|'数据中台'|'其他'
 */
function getPlatformForModule(mod: string, children?: any[]): 'AI中台' | '数据中台' | '其他' {
  const codes = Array.isArray(children) ? children.map((p:any) => p?.code).filter((c:string) => typeof c === 'string') : []
  const parts = codes.map((c:string) => (c.includes(':') ? c.split(':')[0] : c)).filter(Boolean)
  const hasDataPrefix = codes.some((c:string) => c.startsWith('data:')) || parts.includes('data')
  const hasAiPrefix = codes.some((c:string) => c.startsWith('ai:')) || parts.includes('ai')
  if (hasDataPrefix) return '数据中台'
  if (hasAiPrefix) return 'AI中台'
  if (parts.some(p => PLATFORM_MODULE_MAP['AI中台'].includes(p))) return 'AI中台'
  if (PLATFORM_MODULE_MAP['AI中台'].includes(mod)) return 'AI中台'
  if (PLATFORM_MODULE_MAP['数据中台'].includes(mod)) return '数据中台'
  return '其他'
}

/**
 * 按数据中台左侧菜单对模块内权限分组
 * 输入：模块(data)的原始权限子节点列表；输出：插入“分组”中间层后的树
 * 分组依据权限的 `resource` 字段，未匹配到的归入“其他”分组
 * @param children 扁平的权限子节点
 * @returns 插入分组后的子树
 */
function groupDcModulePermissionsByMenu(children: any[]): any[] {
  const categories = [
    { key: 'overview', label: '数据中心概览', match: (r: string | null) => r === 'overview' || r === 'dashboard' },
    { key: 'resource', label: '数据资源管理', match: (r: string | null) => r === 'resource' },
    { key: 'datasource', label: '数据源管理', match: (r: string | null) => r === 'datasource' },
    { key: 'resource_center', label: '资源中心管理', match: (r: string | null) => r === 'resource_center' },
    { key: 'api', label: 'API接口管理', match: (r: string | null) => r === 'api' || r === 'customer' },
    { key: 'logs', label: '日志管理', match: (r: string | null) => r === 'logs' || r === 'logs:user_operation' || r === 'logs:data_upload' }
  ]

  const grouped: any[] = []
  for (const cat of categories) {
    const catChildren = children.filter((c:any) => cat.match(c.resource || null))
    if (catChildren.length === 0) continue
    grouped.push({
      id: `category:${cat.key}`,
      name: cat.label,
      type: 'category',
      is_active: true,
      is_system: true,
      children: catChildren
    })
  }

  const matchedIds = new Set(grouped.flatMap(g => g.children.map((c: any) => c.id)))
  const others = children.filter((c:any) => !matchedIds.has(c.id))
  if (others.length > 0) {
    grouped.push({
      id: 'category:others',
      name: '其他',
      type: 'category',
      is_active: true,
      is_system: true,
      children: others
    })
  }

  grouped.forEach(g => {
    g.children.sort((a: any, b: any) => (a.sort_order ?? 0) - (b.sort_order ?? 0))
  })
  return grouped
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
 * 构建与权限页一致的树结构：平台→模块→（数据中台：分组）→权限
 */
const loadPermissionTree = async () => {
  try {
    const response = await permissionApi.getPermissionTree()
    const modules = (response as any)?.data?.modules || []
    const moduleNodes = modules.map((mod: any) => ({
      id: `module:${mod.module}`,
      name: mod.module,
      type: 'module',
      is_active: true,
      is_system: false,
      children: (mod.permissions || []).map((perm: any) => ({
        id: perm.id,
        name: perm.name,
        code: perm.code,
        resource: perm.resource,
        action: perm.action,
        type: 'permission',
        is_active: (perm as any).status,
        is_system: (perm as any).is_system
      }))
    }))

    moduleNodes.forEach((m) => {
      if (m.name === 'data') {
        m.children = groupDcModulePermissionsByMenu(m.children)
      }
    })

    const aiModules: any[] = []
    const dcModules: any[] = []
    const otherModules: any[] = []
    moduleNodes.forEach((m) => {
      const pf = getPlatformForModule(m.name, m.children)
      if (pf === 'AI中台') aiModules.push(m)
      else if (pf === '数据中台') dcModules.push(m)
      else otherModules.push(m)
    })

    const groupedTree: any[] = [
      {
        id: 'platform:ai',
        name: 'AI中台',
        type: 'platform',
        is_active: true,
        is_system: true,
        children: aiModules
      },
      {
        id: 'platform:dc',
        name: '数据中台',
        type: 'platform',
        is_active: true,
        is_system: true,
        children: dcModules
      }
    ]
    if (otherModules.length > 0) {
      groupedTree.push({
        id: 'platform:other',
        name: '其他',
        type: 'platform',
        is_active: true,
        is_system: true,
        children: otherModules
      })
    }

    permissionTree.value = groupedTree

    logPerm('加载权限树（平台分组）', {
      aiModules: aiModules.length,
      dcModules: dcModules.length,
      otherModules: otherModules.length
    })
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
 * - 加载权限树并初始化已选权限
 * - 注意：Element Plus 的 `default-checked-keys` 仅在初次渲染生效，
 *   为确保异步加载后能正确勾选，需要在对话框渲染完成后主动 setCheckedKeys。
 */
/**
 * 解析角色权限接口响应，兼容不同数据结构，返回权限数组。
 * 支持：
 * - resp.data.permissions
 * - resp.data.data.permissions
 * - resp.data.role.permissions
 * - resp.permissions
 */
const extractPermissionsFromRoleResponse = (resp: any): any[] => {
  try {
    const d = resp?.data
    if (Array.isArray(d?.permissions)) return d.permissions
    if (Array.isArray(d?.data?.permissions)) return d.data.permissions
    if (Array.isArray(d?.role?.permissions)) return d.role.permissions
    if (Array.isArray(resp?.permissions)) return resp.permissions
    // 兜底：尝试从常见字段中寻找包含 id/code 的数组
    const candidates: any[] = [d, d?.data, d?.role, resp]
    for (const obj of candidates) {
      if (obj && typeof obj === 'object') {
        for (const k of Object.keys(obj)) {
          const v = obj[k]
          if (Array.isArray(v) && v.length > 0 && typeof v[0] === 'object' && ('id' in v[0] || 'code' in v[0])) {
            return v
          }
        }
      }
    }
  } catch (e) {
    // ignore
  }
  return []
}

const showPermissionsDialog = async (role: Role) => {
  currentRole.value = role
  // 先加载权限树数据
  await loadPermissionTree()

  try {
    // 加载角色已有权限
    const response = await roleApi.getRolePermissions(role.id)
    // 兼容多种返回结构
    const perms = extractPermissionsFromRoleResponse(response)
    logPerm('角色权限响应结构', {
      topLevelKeys: Object.keys((response as any) || {}),
      dataKeys: Object.keys(((response as any)?.data) || {})
    })
    // 强制转换为数字，避免后端返回字符串ID导致无法匹配
    selectedPermissions.value = (perms as any[])
      .map((p: any) => Number(p.id))
      .filter((id: number) => Number.isFinite(id))
    // 保存权限代码（如 agent:read），用于兜底匹配
    selectedPermissionCodes.value = (perms as any[])
      .map((p: any) => String(p.code))
      .filter((code: string) => !!code)
    logPerm('角色权限加载成功', {
      role: { id: role.id, name: role.name, code: role.code },
      permsCount: perms.length,
      selectedIdsSample: selectedPermissions.value.slice(0, 10),
      selectedCodesSample: selectedPermissionCodes.value.slice(0, 10)
    })
  } catch (error: any) {
    console.error('加载角色权限失败:', error)
    selectedPermissions.value = []
    selectedPermissionCodes.value = []
  }

  // 变更渲染key，确保初次渲染应用 default-checked-keys
  treeRenderKey.value++
  // 打开对话框并在下一次 DOM 更新后设置勾选项
  permissionsDialogVisible.value = true
  await nextTick()
  logPerm('初次渲染后设置勾选（ID）', selectedPermissions.value)
  permissionTreeRef.value?.setCheckedKeys(selectedPermissions.value)
}

/**
 * 权限对话框打开回调
 * - 在对话框完全打开（动画完成）后调用，确保树组件已渲染
 * - 再次设置勾选项，提升稳定性
 */
/**
 * 在权限对话框完全打开时，应用默认勾选。
 * 目的：确保 Tree 实例与子节点已渲染，再调用 setCheckedKeys。
 */
const onPermissionsDialogOpened = () => {
  try {
    logPerm('权限弹窗已打开，尝试设置勾选（ID）', selectedPermissions.value.slice(0, 10))
    // 在对话框完全打开后设置勾选项
    permissionTreeRef.value?.setCheckedKeys(selectedPermissions.value)
  } catch (e) {
    // 兜底处理：稍后再试一次，避免极端情况下 ref 未就绪
    setTimeout(() => {
      logPerm('权限弹窗已打开（延时兜底），再次设置勾选（ID）', selectedPermissions.value.slice(0, 10))
      permissionTreeRef.value?.setCheckedKeys(selectedPermissions.value)
    }, 0)
  }
}

/**
 * 应用选中权限到树
 * - 在任意相关数据变化时调用，确保 UI 与数据一致
 */
/**
 * 将后端返回的 selectedPermissions 应用到权限树。
 * 细节：同时尝试数字与字符串形式的 ID，以兼容内部 key 处理。
 */
/**
 * 收集权限树的所有叶子节点（权限项）。
 * 返回叶子节点的原始 data 对象，包含 id、code、name。
 */
const collectLeafNodes = (): Array<{ id: number | string; code?: string; name?: string }> => {
  const leaves: Array<{ id: number | string; code?: string; name?: string }> = []
  const walk = (nodes: any[]) => {
    if (!Array.isArray(nodes)) return
    for (const n of nodes) {
      if (Array.isArray(n.children) && n.children.length > 0) {
        walk(n.children)
      } else {
        leaves.push(n)
      }
    }
  }
  walk(permissionTree.value || [])
  return leaves
}

/**
 * 兜底：按权限 code 强制勾选（逐个 setChecked）。
 * 用途：当按 ID 设置失败时，尝试按 code 匹配叶子节点勾选。
 */
const forceCheckByCodes = (codes: string[]) => {
  const leaves = collectLeafNodes()
  const matched = leaves.filter(n => codes.includes(String(n.code)))
  logPerm('按 code 兜底勾选', { tryCodesSample: codes.slice(0, 10), matchedCount: matched.length })
  for (const n of matched) {
    try {
      permissionTreeRef.value?.setChecked(n as any, true, false)
    } catch (e) {
      // 忽略单个节点勾选错误
    }
  }
}

const applySelectedPermissionsToTree = async () => {
  if (!permissionsDialogVisible.value) return
  await nextTick()
  try {
    logPerm('应用选中权限到树（开始）', {
      selectedIdsCount: selectedPermissions.value.length,
      selectedIdsSample: selectedPermissions.value.slice(0, 10)
    })
    // 尝试以数字ID设置
    permissionTreeRef.value?.setCheckedKeys(selectedPermissions.value)
    // 兼容某些情况下内部将 key 统一为字符串的实现，追加一次字符串ID设置
    const stringKeys = (selectedPermissions.value || []).map((id: number) => String(id))
    permissionTreeRef.value?.setCheckedKeys(stringKeys as any)
    const checkedNow = permissionTreeRef.value?.getCheckedKeys(false) || []
    logPerm('应用选中权限到树（完成）', { checkedCount: checkedNow.length, checkedSample: (checkedNow as any[]).slice(0, 10) })
    // 如果按 ID 设置失败（无勾选），尝试按 code 逐个强制勾选
    if ((selectedPermissions.value?.length || 0) > 0 && (checkedNow?.length || 0) === 0 && (selectedPermissionCodes.value?.length || 0) > 0) {
      forceCheckByCodes(selectedPermissionCodes.value)
      const checkedAfterCode = permissionTreeRef.value?.getCheckedKeys(false) || []
      logPerm('兜底后勾选情况', { checkedCount: checkedAfterCode.length, checkedSample: (checkedAfterCode as any[]).slice(0, 10) })
    }
  } catch (e) {
    setTimeout(() => {
      permissionTreeRef.value?.setCheckedKeys(selectedPermissions.value)
      const stringKeys = (selectedPermissions.value || []).map((id: number) => String(id))
      permissionTreeRef.value?.setCheckedKeys(stringKeys as any)
      const checkedNow = permissionTreeRef.value?.getCheckedKeys(false) || []
      logPerm('异常兜底（延时）后的勾选情况', { checkedCount: checkedNow.length, checkedSample: (checkedNow as any[]).slice(0, 10) })
      if ((selectedPermissions.value?.length || 0) > 0 && (checkedNow?.length || 0) === 0 && (selectedPermissionCodes.value?.length || 0) > 0) {
        forceCheckByCodes(selectedPermissionCodes.value)
        const checkedAfterCode = permissionTreeRef.value?.getCheckedKeys(false) || []
        logPerm('延时后按 code 兜底勾选情况', { checkedCount: checkedAfterCode.length, checkedSample: (checkedAfterCode as any[]).slice(0, 10) })
      }
    }, 0)
  }
}

// 监听对话框可见性、树数据与选中权限变化，动态应用选中项
watch(permissionsDialogVisible, (visible) => {
  if (visible) {
    applySelectedPermissionsToTree()
  }
})

watch(permissionTree, () => {
  applySelectedPermissionsToTree()
})

watch(selectedPermissions, () => {
  applySelectedPermissionsToTree()
})

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
    logPerm('保存权限提交', {
      roleId: currentRole.value.id,
      permissionIdsCount: permissionIds.length,
      permissionIdsSample: permissionIds.slice(0, 10)
    })
    
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