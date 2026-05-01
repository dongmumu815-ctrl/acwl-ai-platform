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
        <el-button type="danger" @click="scanAndRemoveDataPlatformPermissions">
          <el-icon><Delete /></el-icon>
          扫描并移除数据中台权限
        </el-button>
        <el-button type="danger" @click="deleteAllDataPlatformPermissionDefinitions">
          <el-icon><Delete /></el-icon>
          删除数据中台权限定义
        </el-button>
        <el-button type="danger" @click="rebuildPermissionsFromDcMenu">
          <el-icon><Refresh /></el-icon>
          清空并按数据中台菜单重建
        </el-button>
        <el-button type="warning" @click="syncPermissionsFromConstants">
          <el-icon><Refresh /></el-icon>
          同步权限常量
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

        <el-form-item label="平台">
          <el-select
            v-model="filters.platform"
            placeholder="选择平台"
            clearable
            style="width: 150px"
            @change="handleFilter"
          >
            <el-option label="全部" value="" />
            <el-option label="AI中台" value="AI中台" />
            <el-option label="数据中台" value="数据中台" />
            <el-option label="其他" value="其他" />
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
              <el-icon v-if="data.type === 'platform'" class="platform-icon">
                <OfficeBuilding />
              </el-icon>
              <el-icon v-else-if="data.type === 'module'" class="module-icon">
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

        <el-form-item
          v-if="permissionForm.type === 'permission'"
          label="资源标识"
          prop="resource"
        >
          <el-input
            v-model="permissionForm.resource"
            placeholder="可选。用于区分资源，如某个数据集"
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
  Refresh,
  OfficeBuilding,
  Delete
} from '@element-plus/icons-vue'
import { permissionApi, roleApi, type Permission } from '@/api/roles'
import { PERMISSIONS } from '@/utils/permission'

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
  // 新增平台筛选：'' | 'AI中台' | '数据中台' | '其他'
  platform: '' as '' | 'AI中台' | '数据中台' | '其他',
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
  // 资源标识（后端字段 resource），用于进一步区分权限归属
  resource: '',
  sort: 0,
  is_system: false
})

// 树形组件属性
const treeProps = {
  children: 'children',
  label: 'name',
  key: 'id'
}

/**
 * 平台与模块映射关系
 * 用于在前端对后端返回的模块进行平台分组，以最小改动实现“AI中台/数据中台”两级结构。
 */
const PLATFORM_MODULE_MAP: Record<'AI中台' | '数据中台', string[]> = {
  AI中台: [
    // 前端（AI中台）路由中涉及的功能模块
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
    // 数据中台路由中涉及的功能模块（以 data 前缀聚合）
    'data',
    'governance'
  ]
}

/**
 * 根据模块及其权限码推断所属平台
 * 规则来源：
 * - AI中台功能来自 `frontend/src/router/index.ts`
 * - 数据中台功能来自 `dc_frontend/src/router/index.ts`
 * 推断策略：
 * 1) 若模块下存在权限码以 `data:` 开头，则归为“数据中台”
 * 2) 若模块下存在权限码以 `ai:` 开头，则归为“AI中台”
 * 3) 否则，按模块名在 AI/数据中台清单中匹配
 * 4) 仍无法匹配则归为“其他”（避免误归到 AI）
 * @param mod 模块名（后端返回的 module 字段）
 * @param children 模块下权限节点列表，用于观察权限码前缀
 * @returns 平台名字：'AI中台'|'数据中台'|'其他'
 */
function getPlatformForModule(mod: string, children?: any[]): 'AI中台' | '数据中台' | '其他' {
  const codes = Array.isArray(children) ? children.map((p:any) => p?.code).filter((c:string) => typeof c === 'string') : []
  const parts = codes.map((c:string) => (c.includes(':') ? c.split(':')[0] : c)).filter(Boolean)
  const hasDataPrefix = codes.some((c:string) => c.startsWith('data:')) || parts.includes('data')
  const hasAiPrefix = codes.some((c:string) => c.startsWith('ai:')) || parts.includes('ai')
  if (hasDataPrefix) return '数据中台'
  if (hasAiPrefix) return 'AI中台'
  // 若权限码的模块段命中 AI 中台清单，则归 AI
  if (parts.some(p => PLATFORM_MODULE_MAP['AI中台'].includes(p))) return 'AI中台'
  // 兜底：使用模块名匹配（后端可能返回英文模块名）
  if (PLATFORM_MODULE_MAP['AI中台'].includes(mod)) return 'AI中台'
  if (PLATFORM_MODULE_MAP['数据中台'].includes(mod)) return '数据中台'
  return '其他'
}

// 对话框标题
const dialogTitle = computed(() => {
  if (isCreatingPermission.value) {
    return '添加权限'
  }
  return isEditing.value ? '编辑权限' : '新建权限模块'
})

// 模块选项
/**
 * 模块选项（支持平台分组后的嵌套结构）
 * 在创建具体权限时为“所属模块”下拉提供数据来源。
 */
const moduleOptions = computed(() => {
  const mods: any[] = []
  const walk = (nodes: any[]) => {
    nodes.forEach(n => {
      if (n.type === 'module') mods.push(n)
      if (n.children && n.children.length) walk(n.children)
    })
  }
  walk(permissionTree.value)
  return mods
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
    // 支持两到四段格式，例如：user:read、data:resource:view、data:user:profile:view
    { pattern: /^[a-z][a-z0-9_-]*(?::[a-z][a-z0-9_-]*){1,3}$/,
      message: '权限代码格式为：模块:操作 / 模块:资源:操作 / 模块:资源子级:操作', trigger: 'blur' }
  ],
  parent_id: [
    { required: true, message: '请选择所属模块', trigger: 'change' }
  ],
  resource: [
    { min: 0, max: 100, message: '资源标识长度不能超过100', trigger: 'blur' }
  ],
  description: [
    { max: 200, message: '描述不能超过 200 个字符', trigger: 'blur' }
  ]
}

/**
 * 加载权限树
 */
/**
 * 加载权限树
 * - 从后端拉取模块与权限
 * - 前端按平台（AI中台/数据中台）聚合为两级树结构
 *   归类规则：若模块任何子权限码以 `data:` 开头，则归“数据中台”，否则归“AI中台”
 * - 应用平台筛选（如选择了 filters.platform，仅渲染对应平台节点）
 */
const loadPermissionTree = async () => {
  treeLoading.value = true
  try {
    const response = await permissionApi.getPermissionTree()
    // 后端返回 ResponseModel，data: { modules: Array<{ module: string; permissions: PermissionTreeNode[] }> }
    const modules = (response as any)?.data?.modules || []
    // 统一转换为 el-tree 可用的节点结构（先构建模块节点）
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
        is_active: perm.status,
        is_system: perm.is_system
      }))
    }))

    // 将“数据中台”模块按左侧菜单分组为三级结构：模块→分组→权限
    moduleNodes.forEach((m) => {
      if (m.name === 'data') {
        m.children = groupDcModulePermissionsByMenu(m.children)
      }
    })

    // 前端分组为平台节点
    const aiModules: any[] = []
    const dcModules: any[] = []
    const otherModules: any[] = []
    moduleNodes.forEach((m) => {
      const pf = getPlatformForModule(m.name, m.children)
      if (pf === 'AI中台') aiModules.push(m)
      else if (pf === '数据中台') dcModules.push(m)
      else otherModules.push(m)
    })

    let groupedTree: any[] = [
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

    // 应用平台筛选（仅渲染选择的平台）
    if (filters.platform) {
      permissionTree.value = groupedTree.filter(n => n.name === filters.platform)
    } else {
      permissionTree.value = groupedTree
    }
    
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
 * 按数据中台左侧菜单对模块内权限分组
 * 输入为原始的权限节点列表（扁平：module→permissions），输出为带“分组”中间层的树：
 * 模块(data) → 分组（如：数据中心概览、数据资源管理） → 权限项（如：仪表盘、资源列表）
 * 分组匹配基于 permission.resource，必要时使用静态映射补充父子关系。
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
    const catChildren = children.filter(c => cat.match(c.resource || null))
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

  // 未匹配到分类的权限，放入“其他”分类，避免遗漏
  const matchedIds = new Set(grouped.flatMap(g => g.children.map((c: any) => c.id)))
  const others = children.filter(c => !matchedIds.has(c.id))
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

  // 分类内按已有排序字段排序；无则保持原序
  grouped.forEach(g => {
    g.children.sort((a: any, b: any) => (a.sort_order ?? 0) - (b.sort_order ?? 0))
  })
  return grouped
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
    resource: '',
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
    resource: '',
    sort: 0,
    is_system: false
  })
  permissionDialogVisible.value = true
}

/**
 * 显示编辑对话框
 */
/**
 * 显示编辑对话框
 * 仅支持编辑具体权限节点，模块节点为聚合显示不可编辑
 */
const showEditDialog = (data: any) => {
  if (data.type === 'module' || data.type === 'platform') {
    ElMessage.warning('该节点为聚合显示，不支持直接编辑')
    return
  }
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
/**
 * 重置筛选条件
 */
const resetFilters = () => {
  filters.search = ''
  filters.module = ''
  filters.platform = ''
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
/**
 * 提交表单
 * - 解析 code 支持两到四段：module[:resource[...]]:action
 * - 创建/更新时：module 取首段，action 取末段，resource 为中间段合并（若存在）
 */
const handleSubmit = async () => {
  if (!permissionFormRef.value) return
  
  try {
    await permissionFormRef.value.validate()
    submitting.value = true
    
    if (isEditing.value) {
      // 更新权限
      // 从 code 拆分 module/resource/action，支持分级权限码
      const parts = (permissionForm.code || '').split(':')
      const mod = parts[0]
      const act = parts[parts.length - 1]
      const res = parts.length > 2 ? parts.slice(1, -1).join(':') : ''
      await permissionApi.updatePermission(permissionForm.id, {
        name: permissionForm.name,
        code: permissionForm.code,
        description: permissionForm.description,
        module: mod,
        action: act,
        resource: permissionForm.resource || res,
        status: permissionForm.is_active,
        sort_order: permissionForm.sort
      })
      ElMessage.success('权限更新成功')
    } else {
      // 创建权限
      const parts = (permissionForm.code || '').split(':')
      const mod = parts[0]
      const act = parts[parts.length - 1]
      const res = parts.length > 2 ? parts.slice(1, -1).join(':') : ''
      await permissionApi.createPermission({
        name: permissionForm.name,
        code: permissionForm.code,
        description: permissionForm.description,
        module: mod,
        resource: permissionForm.resource || res,
        action: act,
        status: permissionForm.is_active,
        sort_order: permissionForm.sort
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
/**
 * 删除权限
 * - 限制：模块节点为聚合展示，不能删除
 */
const handleDelete = async (data: any) => {
  if (data.type === 'module' || data.type === 'platform') {
    ElMessage.warning('该节点为聚合显示，不能直接删除')
    return
  }
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

/**
 * 根据模块与动作生成默认权限名称
 * @param module 模块标识（如：user、model、datasource）
 * @param action 动作标识（如：read、create、update、delete）
 * @returns 默认的中文权限名称，例如："数据源:读取"
 */
/**
 * 根据权限代码生成默认中文名称（支持两段或三段）
 * @param moduleOrCode 模块或完整权限代码（形如：user:read 或 data:resource:view）
 * @param action 可选动作（仅当传入两段时使用）
 * @returns 例如："数据源:查看"、"资源:查询"
 */
/**
 * 根据权限代码生成默认中文名称（支持两到四段代码）
 * 示例：
 * - 两段：data:view -> 数据:查看
 * - 三段：data:resource:view -> 资源:查看
 * - 四段：data:user:profile:view -> 用户资料:查看
 * @param moduleOrCode 模块或完整权限代码
 * @param action 可选动作（仅当传入两段时使用）
 */
function getDefaultPermissionName(moduleOrCode: string, action?: string): string {
  const actionMap: Record<string, string> = {
    read: '读取',
    view: '查看',
    query: '查询',
    create: '创建',
    update: '更新',
    edit: '编辑',
    delete: '删除',
    export: '导出',
    save: '保存',
    deploy: '部署',
    monitor: '监控',
    test: '测试'
  }
  const moduleMap: Record<string, string> = {
    user: '用户',
    role: '角色',
    permission: '权限',
    model: '模型',
    dataset: '数据集',
    project: '项目',
    system: '系统',
    instruction_set: '指令集',
    datasource: '数据源',
    agent: '智能体',
    training: '微调',
    data: '数据',
    ai: 'AI'
  }
  // 支持资源与子级的中文映射（包含常见组合）
  const resourceLabelMap: Record<string, string> = {
    resource: '资源',
    resource_center: '资源中心',
    resource_package: '资源包',
    datasource: '数据源',
    elasticsearch: 'Elasticsearch',
    api: 'API',
    customer: '平台',
    overview: '概览',
    dashboard: '仪表盘',
    'user:profile': '用户资料',
    'logs:user_operation': '用户操作日志',
    'logs:data_upload': '数据上传日志'
  }

  const code = action ? `${moduleOrCode}:${action}` : moduleOrCode
  const parts = code.split(':')
  if (parts.length >= 3) {
    const act = parts[parts.length - 1]
    const mid = parts.slice(1, -1).join(':')
    const label = resourceLabelMap[mid] || resourceLabelMap[parts[1]] || moduleMap[parts[1]] || mid
    return `${label}:${actionMap[act] || act}`
  }
  const [mod, act] = parts
  return `${moduleMap[mod] || mod}:${actionMap[act] || act}`
}

/**
 * 同步前端权限常量到数据库
 *
 * 实现步骤：
 * 1) 全量拉取现有权限（列表接口：skip/limit），避免树结构遗漏导致重复创建
 * 2) 对比前端 PERMISSIONS 常量，计算缺失代码集合
 * 3) 优先尝试批量创建；如遇 400（重复或名称冲突），降级为逐条创建并忽略已存在项
 * 4) 创建成功后刷新权限树，以便页面展示最新结果
 */
const syncPermissionsFromConstants = async () => {
  try {
    treeLoading.value = true
    // 1) 通过列表接口全量获取已有权限，避免树结构遗漏
    const listResp = await permissionApi.getPermissions({ skip: 0, limit: 1000 })
    const listData = (listResp as any)?.data || {}
    const items: Array<{ code: string }> = listData.items || []
    const existingCodes = new Set<string>(items.filter(it => !!it.code).map(it => it.code))

    // 兜底：再合并一次树结构中的代码（如果已加载过）
    if (permissionTree.value && permissionTree.value.length > 0) {
      permissionTree.value.forEach((mod: any) => {
        (mod.children || []).forEach((perm: any) => {
          if (perm.code) existingCodes.add(perm.code)
        })
      })
    } else {
      // 若未加载过树，则补一次加载，提升完整性
      await loadPermissionTree()
      permissionTree.value.forEach((mod: any) => {
        (mod.children || []).forEach((perm: any) => {
          if (perm.code) existingCodes.add(perm.code)
        })
      })
    }

    // 2.1 前端（AI中台）常量中的所有权限代码
    const constantCodes: string[] = Object.values(PERMISSIONS)

    // 2.2 解析 dc_frontend 路由中的权限代码（数据中台）
    // 注意：在开源版本中，数据中台路由文件路径需要由部署者自行配置
    const dcRouterPaths: string[] = []
    let dcText: string | null = null
    for (const p of dcRouterPaths) {
      dcText = await loadExternalRouterText(p)
      if (dcText) break
    }
    const dcCodes = dcText ? extractPermissionCodesFromRouterText(dcText) : []

    // 合并两侧代码并去重
    const unionCodes = Array.from(new Set<string>([...constantCodes, ...dcCodes]))
    const missingCodes = unionCodes.filter(code => !existingCodes.has(code))

    if (missingCodes.length === 0) {
      ElMessage.success('权限常量已与数据库一致，无需同步')
      return
    }

    // 构造批量创建的权限数据
    const payloads = missingCodes.map(code => {
      const parts = code.split(':')
      const module = parts[0]
      const action = parts[parts.length - 1]
      const resource = parts.length > 2 ? parts.slice(1, -1).join(':') : null
      return {
        name: getDefaultPermissionName(code),
        code,
        description: `同步自前端常量/路由 ${code}`,
        module,
        resource,
        action,
        status: true,
        sort_order: 0
      }
    })

    // 3) 执行批量创建
    try {
      await permissionApi.batchCreatePermissions(payloads)
      ElMessage.success(`已同步 ${missingCodes.length} 个权限`)
    } catch (batchError: any) {
      // 批量创建失败（可能因为部分代码/名称已存在），降级为逐条创建
      const batchDetail = batchError?.response?.data?.detail || batchError?.response?.data?.message
      console.warn('批量创建失败，降级单条创建:', batchDetail)

      let successCount = 0
      for (const p of payloads) {
        // 跳过已存在代码（双重保险）
        if (existingCodes.has(p.code)) continue
        try {
          await permissionApi.createPermission(p)
          successCount++
        } catch (singleError: any) {
          const detail = singleError?.response?.data?.detail || singleError?.response?.data?.message || ''
          // 如果是名称已存在，尝试调整名称后重试一次
          if (typeof detail === 'string' && detail.includes('名称已存在')) {
            const adjusted = { ...p, name: `${p.name}（常量）` }
            try {
              await permissionApi.createPermission(adjusted)
              successCount++
            } catch (retryErr) {
              console.warn(`创建权限失败（重试后）: ${p.code}`, retryErr)
            }
          } else {
            // 其他错误忽略，保留日志
            console.warn(`创建权限失败: ${p.code}`, singleError)
          }
        }
      }

      if (successCount > 0) {
        ElMessage.success(`已同步 ${successCount} 个权限（逐条创建）`)
      } else {
        ElMessage.info('没有可创建的缺失权限或全部创建失败')
      }
    }

    // 4) 刷新权限树
    await loadPermissionTree()
  } catch (error: any) {
    console.error('同步权限失败:', error)
    ElMessage.error(error.response?.data?.message || '同步权限失败')
  } finally {
    treeLoading.value = false
  }
}

/**
 * 加载外部路由文件文本内容（通过 Vite 的 /@fs 机制）
 * @param absPath Windows 绝对路径，如 C:/project/frontend/src/router/index.ts
 */
async function loadExternalRouterText(absPath: string): Promise<string | null> {
  const normalized = absPath.replace(/\\/g, '/').replace(/^\//, '')
  // 使用 ?raw 强制以纯文本返回，避免 Vite 对 TS 文件做导入解析
  const url = `/@fs/${normalized}?raw`
  try {
    const resp = await fetch(url)
    if (!resp.ok) return null
    const text = await resp.text()
    return text
  } catch (e) {
    console.warn('读取外部路由失败:', absPath, e)
    return null
  }
}

/**
 * 从路由源码中提取权限代码
 * 支持：
 * - 单个字段：meta.permission
 * - 数组字段：meta.permissionsAny / meta.permissionsAll
 * - 任意常量字符串中出现的 ai:/data: 前缀权限码
 * 代码段支持两到四段，例如 data:resource:view、data:user:profile:view
 */
function extractPermissionCodesFromRouterText(text: string): string[] {
  const codes = new Set<string>()
  // 匹配 'data:resource:view' 或 "ai:model:read" 等（允许中划线与最多四段）
  const codeRegex = /["']((?:data|ai):[a-z][a-z0-9_-]*(?::[a-z][a-z0-9_-]*){1,3})["']/g
  let m: RegExpExecArray | null
  while ((m = codeRegex.exec(text)) !== null) {
    codes.add(m[1])
  }
  return Array.from(codes)
}

/**
 * 从数据中台路由文本中提取“菜单项（title）与权限码（code）”的映射
 * 规则：
 * - 仅处理 `meta` 区块；忽略含有 `hideInMenu: true` 的项
 * - 在 `meta` 文本块中抽取 `title: 'xxx'` 与出现的权限码（permission/permissionsAny/permissionsAll）
 * - 一个区块可能包含多个权限码（Any/All），为简单起见分别生成多条映射，均使用同一个 title
 */
function extractMenuItemsFromDcMenuText(text: string): Array<{ code: string; title: string | null }> {
  const items: Array<{ code: string; title: string | null }> = []
  const metaBlockRegex = /meta\s*:\s*\{([\s\S]*?)\}/g
  let m: RegExpExecArray | null
  while ((m = metaBlockRegex.exec(text)) !== null) {
    const block = m[1]
    // 跳过隐藏项
    if (/hideInMenu\s*:\s*true/.test(block)) continue
    // 提取 title
    const tMatch = /title\s*:\s*["']([\s\S]*?)["']/.exec(block)
    const title = tMatch ? tMatch[1].trim() : null
    // 提取权限码
    const codes = extractPermissionCodesFromRouterText(block)
    codes.forEach(code => items.push({ code, title }))
  }
  return items
}

/**
 * 从 AI 中台（frontend 路由）文本中提取菜单项的权限代码与标题
 * - 支持 PERMISSIONS 常量映射到字符串权限码
 * - 过滤 hidden/hideInMenu 项
 */
function extractMenuItemsFromAiRouterText(text: string): Array<{ code: string; title: string | null }> {
  const items: Array<{ code: string; title: string | null }> = []
  const seen = new Set<string>()
  const metaBlockRegex = /meta\s*:\s*\{([\s\S]*?)\}/g
  let m: RegExpExecArray | null
  while ((m = metaBlockRegex.exec(text)) !== null) {
    const block = m[1]
    if (/hideInMenu\s*:\s*true/.test(block) || /hidden\s*:\s*true/.test(block)) continue
    const tMatch = /title\s*:\s*['"]([\s\S]*?)['"]/.exec(block)
    const title = tMatch ? tMatch[1].trim() : null

    // 单个权限
    const permToken = block.match(/permission\s*:\s*([^,\n]+)/)
    const singlePerms: string[] = []
    if (permToken) {
      const token = permToken[1].trim()
      const constMatch = token.match(/PERMISSIONS\.(\w+)/)
      if (constMatch && PERMISSIONS[constMatch[1] as keyof typeof PERMISSIONS]) {
        singlePerms.push(PERMISSIONS[constMatch[1] as keyof typeof PERMISSIONS])
      } else {
        const strMatch = token.match(/['"]([\w:-]+)['"]/)
        if (strMatch) singlePerms.push(strMatch[1])
      }
    }

    // 多个权限
    const multiBlocks = block.match(/permissions\s*:\s*\[([\s\S]*?)\]|requireAllPermissions\s*:\s*\[([\s\S]*?)\]/g) || []
    const multiPerms: string[] = []
    for (const mb of multiBlocks) {
      const constTokens = mb.match(/PERMISSIONS\.(\w+)/g) || []
      for (const t of constTokens) {
        const key = t.split('.')[1]
        const val = PERMISSIONS[key as keyof typeof PERMISSIONS]
        if (val) multiPerms.push(val)
      }
      const strTokens = mb.match(/['"]([\w:-]+)['"]/g) || []
      for (const st of strTokens) {
        const v = st.replace(/['"]/g, '')
        multiPerms.push(v)
      }
    }

    const allCodes = [...singlePerms, ...multiPerms]
    for (const code of allCodes) {
      if (!seen.has(code)) {
        seen.add(code)
        items.push({ code, title })
      }
    }
  }
  return items
}

// 初始化
onMounted(() => {
  loadPermissionTree()
})

/**
 * 扫描拥有“数据中台”权限的角色与用户，并移除角色的 data:* 权限
 * 步骤：
 * 1) 拉取所有角色；逐个查询其权限列表，筛选 code 以 `data:` 开头的权限
 * 2) 查询这些角色对应的用户列表，统计受影响用户
 * 3) 弹窗确认后，批量移除各角色的上述权限映射
 * 4) 操作完成后刷新权限树
 */
const scanAndRemoveDataPlatformPermissions = async () => {
  treeLoading.value = true
  try {
    // 拉取所有角色
    const rolesResp = await roleApi.getRoles({ size: 1000 })
    const rolesList = (rolesResp as any)?.data?.items || []
    const targetRoles: Array<{ role: any; permissionIds: number[]; users: any[] }> = []

    // 逐角色扫描 data:* 权限与关联用户
    for (const role of rolesList) {
      const permsResp = await roleApi.getRolePermissions(role.id)
      const roleWithPerms = (permsResp as any)?.data || {}
      const dataPerms = (roleWithPerms.permissions || []).filter((p: any) => typeof p.code === 'string' && p.code.startsWith('data:'))
      if (dataPerms.length === 0) continue

      const userResp = await roleApi.getRoleUsers(role.id)
      const users = (userResp as any)?.data || []
      targetRoles.push({ role, permissionIds: dataPerms.map((p: any) => p.id), users })
    }

    if (targetRoles.length === 0) {
      ElMessage.success('没有角色拥有数据中台权限，无需删除')
      return
    }

    const totalUsers = targetRoles.reduce((acc, r) => acc + (r.users?.length || 0), 0)
    const totalMappings = targetRoles.reduce((acc, r) => acc + (r.permissionIds?.length || 0), 0)

    // 生成摘要文本：列出前若干个角色与用户
    const previewLines: string[] = []
    targetRoles.slice(0, 5).forEach(r => {
      const userNames = (r.users || []).slice(0, 5).map((u: any) => u.username || u.email || `#${u.id}`)
      previewLines.push(`角色 ${r.role.name}（${r.role.code}） -> 权限数 ${r.permissionIds.length}，用户：${userNames.join(', ')}${(r.users?.length || 0) > 5 ? ' 等' : ''}`)
    })
    const summary = `将在 ${targetRoles.length} 个角色中移除共 ${totalMappings} 个数据中台权限映射，影响约 ${totalUsers} 名用户。\n\n示例：\n${previewLines.join('\n')}`

    await ElMessageBox.confirm(summary, '确认删除数据中台权限', { type: 'warning', confirmButtonText: '执行删除', cancelButtonText: '取消' })

    // 执行批量删除
    let successOps = 0
    for (const r of targetRoles) {
      if (!r.permissionIds || r.permissionIds.length === 0) continue
      try {
        await roleApi.removePermissions(r.role.id, r.permissionIds)
        successOps++
      } catch (e: any) {
        console.warn('批量移除失败，尝试逐条：', r.role?.code)
        // 降级逐条删除
        for (const pid of r.permissionIds) {
          try { await roleApi.removePermission(r.role.id, pid) } catch { /* 忽略 */ }
        }
      }
    }

    ElMessage.success(`已处理 ${successOps} 个角色的数据中台权限移除`)
    await loadPermissionTree()
  } catch (error: any) {
    if (!error?.message?.includes('cancel')) {
      console.error('扫描并移除失败:', error)
      ElMessage.error(error.response?.data?.message || '扫描并移除失败')
    }
  } finally {
    treeLoading.value = false
  }
}

/**
 * 删除所有“数据中台”权限定义（code 以 data: 开头）
 * 安全流程：
 * 1) 扫描所有角色，先移除其持有的 data:* 权限映射，避免外键约束或后端校验失败
 * 2) 拉取所有权限定义，筛选 code 以 data: 开头的项，二次确认后逐条删除
 * 3) 完成后刷新权限树并提示结果
 */
const deleteAllDataPlatformPermissionDefinitions = async () => {
  treeLoading.value = true
  try {
    // 第一步：移除角色上的 data:* 权限映射
    const rolesResp = await roleApi.getRoles({ size: 1000 })
    const rolesList = (rolesResp as any)?.data?.items || []
    let affectedRoles = 0
    for (const role of rolesList) {
      const permsResp = await roleApi.getRolePermissions(role.id)
      const roleWithPerms = (permsResp as any)?.data || {}
      const dataPerms = (roleWithPerms.permissions || []).filter((p: any) => typeof p.code === 'string' && p.code.startsWith('data:'))
      if (dataPerms.length === 0) continue
      try {
        await roleApi.removePermissions(role.id, dataPerms.map((p: any) => p.id))
        affectedRoles++
      } catch (e: any) {
        // 降级逐条删除
        for (const p of dataPerms) {
          try { await roleApi.removePermission(role.id, p.id) } catch {}
        }
        affectedRoles++
      }
    }

    // 第二步：删除权限定义
    // 全量拉取权限（分页累加）
    const allPerms: Permission[] = []
    let skip = 0
    const limit = 200
    while (true) {
      const listResp = await permissionApi.getPermissions({ skip, limit })
      const items = (listResp as any)?.data?.items || []
      allPerms.push(...items)
      if (items.length < limit) break
      skip += limit
    }
    const dataPermDefs = allPerms.filter(p => typeof p.code === 'string' && p.code.startsWith('data:'))

    if (dataPermDefs.length === 0) {
      ElMessage.success('没有可删除的数据中台权限定义')
      await loadPermissionTree()
      return
    }

    const preview = dataPermDefs.slice(0, 6).map(p => `${p.code}（#${p.id}）`).join('\n')
    await ElMessageBox.confirm(`将删除 ${dataPermDefs.length} 条数据中台权限定义。\n示例：\n${preview}`, '确认删除权限定义', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消'
    })

    let success = 0
    for (const p of dataPermDefs) {
      try {
        await permissionApi.deletePermission(p.id)
        success++
      } catch (e: any) {
        console.warn('删除权限失败：', p.code, e?.message)
      }
    }

    ElMessage.success(`已移除 ${affectedRoles} 个角色的映射，并删除 ${success}/${dataPermDefs.length} 条权限定义`)
    await loadPermissionTree()
  } catch (error: any) {
    if (!error?.message?.includes('cancel')) {
      console.error('删除数据中台权限定义失败:', error)
      ElMessage.error(error.response?.data?.message || '删除数据中台权限定义失败')
    }
  } finally {
    treeLoading.value = false
  }
}

/**
 * 按数据中台左侧树形菜单重建权限
 * 实现思路：
 * 1) 确认并删除当前所有“非系统”权限，避免历史结构干扰
 * 2) 读取 dc_frontend 路由源码文本，解析其中的 meta 区块
 * 3) 过滤掉 meta.hideInMenu === true 的菜单项，仅保留左侧菜单可见项
 * 4) 从可见项的 meta 中提取权限码（支持 permission、permissionsAny、permissionsAll），生成批量创建数据
 * 5) 批量创建后刷新权限树
 */
const rebuildPermissionsFromDcMenu = async () => {
  try {
    await ElMessageBox.confirm(
      '此操作将删除当前所有非系统权限，并按数据中台菜单重新生成。是否继续？',
      '重建权限',
      { type: 'warning' }
    )

    treeLoading.value = true
    // 1) 删除现有非系统权限
    const listResp = await permissionApi.getPermissions({ skip: 0, limit: 2000 })
    const items: Permission[] = ((listResp as any)?.data?.items || []) as Permission[]
    let deletedCount = 0
    for (const p of items) {
      // 仅删除非系统权限，保留 is_system
      if (!p.is_system) {
        try {
          await permissionApi.deletePermission(p.id)
          deletedCount++
        } catch (delErr: any) {
          // 可能因外键/角色关联导致删除失败，记录并继续
          console.warn('删除权限失败（忽略继续）:', p.code, delErr?.response?.data || delErr)
        }
      }
    }

    // 2) 读取 AI 中台与数据中台路由文本
    // 注意：在开源版本中，路由文件路径需要由部署者自行配置
    const aiRouterPaths: string[] = []
    const dcRouterPaths: string[] = []
    let aiText: string | null = null
    let dcText: string | null = null
    for (const p of aiRouterPaths) {
      aiText = await loadExternalRouterText(p)
      if (aiText) break
    }
    for (const p of dcRouterPaths) {
      dcText = await loadExternalRouterText(p)
      if (dcText) break
    }
    if (!aiText && !dcText) {
      ElMessage.warning('未配置路由文件路径，将使用默认权限数据')
    }

    // 3) 从菜单可见项提取权限项（title+code），优先 AI 中台
    const aiMenuItems = aiText ? extractMenuItemsFromAiRouterText(aiText) : []
    const dcMenuItems = dcText ? extractMenuItemsFromDcMenuText(dcText) : []
    const mergedMap = new Map<string, string | null>()
    for (const it of aiMenuItems) {
      if (!mergedMap.has(it.code)) mergedMap.set(it.code, it.title)
    }
    for (const it of dcMenuItems) {
      if (!mergedMap.has(it.code)) mergedMap.set(it.code, it.title)
    }
    const menuItems = Array.from(mergedMap.entries()).map(([code, title]) => ({ code, title }))
    if (menuItems.length === 0) {
      ElMessage.warning('未从菜单提取到任何权限码')
    }

    // 4) 构造批量创建的权限数据
    const payloads = menuItems.map(({ code, title }) => {
      const parts = code.split(':')
      const module = parts[0]
      const action = parts[parts.length - 1]
      const resource = parts.length > 2 ? parts.slice(1, -1).join(':') : null
      return {
        name: title || getDefaultPermissionName(code),
        code,
        description: `按菜单重建：${code}`,
        module,
        resource,
        action,
        status: true,
        sort_order: 0
      }
    })

    if (payloads.length > 0) {
      try {
        await permissionApi.batchCreatePermissions(payloads)
        ElMessage.success(`已重建 ${payloads.length} 个权限（删除 ${deletedCount} 个）`)
      } catch (batchErr: any) {
        console.warn('批量重建失败，降级逐条创建', batchErr?.response?.data || batchErr)
        let success = 0
        for (const p of payloads) {
          try {
            await permissionApi.createPermission(p)
            success++
          } catch (singleErr: any) {
            console.warn('单条创建失败（忽略继续）:', p.code, singleErr?.response?.data || singleErr)
          }
        }
        ElMessage.success(`已重建 ${success} 个权限（删除 ${deletedCount} 个）`)
      }
    } else {
      ElMessage.info('没有可重建的权限代码')
    }

    // 5) 刷新权限树
    await loadPermissionTree()
  } catch (error: any) {
    if (!error?.message?.includes('cancel')) {
      console.error('重建权限失败:', error)
      ElMessage.error(error.response?.data?.message || '重建权限失败')
    }
  } finally {
    treeLoading.value = false
  }
}

/**
 * 仅从数据中台左侧菜单可见项提取权限码
 * 解析策略：
 * - 基于正则抽取所有 meta 区块文本（meta: { ... }）
 * - 过滤掉包含 `hideInMenu: true` 的区块（隐藏项不作为菜单权限）
 * - 在可见区块中抽取 permission/permissionsAny/permissionsAll 中出现的权限码
 * - 权限码匹配支持两到四段：`data:resource:view`、`data:user:profile:view` 等
 * @param text 路由源码纯文本
 * @returns 唯一的权限码列表
 */
function extractPermissionCodesFromDcMenuText(text: string): string[] {
  const codes = new Set<string>()
  // 抽取 meta 块：宽松匹配花括号内内容
  const metaBlockRegex = /meta\s*:\s*\{([\s\S]*?)\}/g
  let m: RegExpExecArray | null
  while ((m = metaBlockRegex.exec(text)) !== null) {
    const block = m[1]
    // 过滤隐藏菜单项
    const hideMatch = /hideInMenu\s*:\s*true/.test(block)
    if (hideMatch) continue
    // 在块内抽取权限码
    const innerCodes = extractPermissionCodesFromRouterText(block)
    innerCodes.forEach(c => codes.add(c))
  }
  return Array.from(codes)
}
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

.platform-icon {
  color: #fa8c16;
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