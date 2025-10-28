<template>
  <div class="user-list">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">用户管理</h1>
        <p class="page-description">管理系统用户账户、角色和权限</p>
      </div>
      <div class="header-right">
        <el-button type="primary" @click="handleCreate">
          <el-icon><Plus /></el-icon>
          新建用户
        </el-button>
      </div>
    </div>

    <!-- 搜索和筛选 -->
    <div class="search-section">
      <el-card>
        <el-form :model="searchForm" inline>
          <el-form-item label="搜索">
            <el-input
              v-model="searchForm.search"
              placeholder="用户名、邮箱、姓名"
              clearable
              style="width: 200px"
              @keyup.enter="handleSearch"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
          </el-form-item>
          <el-form-item label="部门">
            <el-select
              v-model="searchForm.department"
              placeholder="选择部门"
              clearable
              style="width: 150px"
            >
              <el-option
                v-for="dept in departments"
                :key="dept"
                :label="dept"
                :value="dept"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="状态">
            <el-select
              v-model="searchForm.is_active"
              placeholder="选择状态"
              clearable
              style="width: 120px"
            >
              <el-option label="启用" :value="true" />
              <el-option label="禁用" :value="false" />
            </el-select>
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

    <!-- 工具栏 -->
    <div class="toolbar">
      <div class="toolbar-left">
        <el-button
          type="danger"
          :disabled="selectedUsers.length === 0"
          @click="handleBatchDelete"
        >
          <el-icon><Delete /></el-icon>
          批量删除
        </el-button>
        <el-button @click="handleExport">
          <el-icon><Download /></el-icon>
          导出
        </el-button>
        <el-button @click="handleImport">
          <el-icon><Upload /></el-icon>
          导入
        </el-button>
      </div>
      <div class="toolbar-right">
        <el-button-group>
          <el-button
            :type="viewMode === 'table' ? 'primary' : 'default'"
            @click="viewMode = 'table'"
          >
            <el-icon><List /></el-icon>
          </el-button>
          <el-button
            :type="viewMode === 'card' ? 'primary' : 'default'"
            @click="viewMode = 'card'"
          >
            <el-icon><Grid /></el-icon>
          </el-button>
        </el-button-group>
        <el-button @click="loadUsers">
          <el-icon><Refresh /></el-icon>
        </el-button>
      </div>
    </div>

    <!-- 数据表格 -->
    <div v-if="viewMode === 'table'" class="table-section">
      <el-card>
        <el-table
          v-loading="loading"
          :data="users"
          @selection-change="handleSelectionChange"
          stripe
          style="width: 100%"
        >
          <el-table-column type="selection" width="55" />
          <el-table-column prop="avatar" label="头像" width="80">
            <template #default="{ row }">
              <el-avatar
                :src="row.avatar"
                :alt="row.full_name"
                size="small"
              >
                {{ row.full_name?.charAt(0) }}
              </el-avatar>
            </template>
          </el-table-column>
          <el-table-column prop="username" label="用户名" min-width="120" />
          <el-table-column prop="full_name" label="姓名" min-width="120" />
          <el-table-column prop="email" label="邮箱" min-width="180" />
          <el-table-column prop="department" label="部门" min-width="120" />
          <el-table-column prop="position" label="职位" min-width="120" />
          <el-table-column prop="is_active" label="状态" width="80">
            <template #default="{ row }">
              <el-tag :type="row.is_active ? 'success' : 'danger'">
                {{ row.is_active ? '启用' : '禁用' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="last_login" label="最后登录" width="160">
            <template #default="{ row }">
              {{ formatDateTime(row.last_login) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="200" fixed="right">
            <template #default="{ row }">
              <el-button
                type="primary"
                size="small"
                @click="handleView(row)"
              >
                查看
              </el-button>
              <el-button
                type="warning"
                size="small"
                @click="handleEdit(row)"
              >
                编辑
              </el-button>
              <el-popconfirm
                title="确定要删除这个用户吗？"
                @confirm="handleDelete(row)"
              >
                <template #reference>
                  <el-button type="danger" size="small">
                    删除
                  </el-button>
                </template>
              </el-popconfirm>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>

    <!-- 卡片视图 -->
    <div v-else class="card-section">
      <div class="user-cards">
        <div
          v-for="user in users"
          :key="user.id"
          class="user-card"
          @click="handleView(user)"
        >
          <el-card shadow="hover">
            <div class="card-header">
              <el-avatar
                :src="user.avatar"
                :alt="user.full_name"
                size="large"
              >
                {{ user.full_name?.charAt(0) }}
              </el-avatar>
              <div class="user-info">
                <h3>{{ user.full_name }}</h3>
                <p>{{ user.username }}</p>
              </div>
              <el-tag :type="user.is_active ? 'success' : 'danger'">
                {{ user.is_active ? '启用' : '禁用' }}
              </el-tag>
            </div>
            <div class="card-content">
              <div class="info-item">
                <span class="label">邮箱：</span>
                <span class="value">{{ user.email }}</span>
              </div>
              <div class="info-item">
                <span class="label">部门：</span>
                <span class="value">{{ user.department || '-' }}</span>
              </div>
              <div class="info-item">
                <span class="label">职位：</span>
                <span class="value">{{ user.position || '-' }}</span>
              </div>
              <div class="info-item">
                <span class="label">最后登录：</span>
                <span class="value">{{ formatDateTime(user.last_login) }}</span>
              </div>
            </div>
            <div class="card-actions">
              <el-button size="small" @click.stop="handleEdit(user)">
                编辑
              </el-button>
              <el-popconfirm
                title="确定要删除这个用户吗？"
                @confirm="handleDelete(user)"
              >
                <template #reference>
                  <el-button type="danger" size="small" @click.stop>
                    删除
                  </el-button>
                </template>
              </el-popconfirm>
            </div>
          </el-card>
        </div>
      </div>
    </div>

    <!-- 分页 -->
    <div class="pagination-section">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.page_size"
        :total="pagination.total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>

    <!-- 用户详情对话框 -->
    <el-dialog
      v-model="detailDialogVisible"
      title="用户详情"
      width="800px"
    >
      <UserDetail
        v-if="selectedUser"
        :user="selectedUser"
        @close="detailDialogVisible = false"
      />
    </el-dialog>

    <!-- 导入对话框 -->
    <el-dialog
      v-model="importDialogVisible"
      title="导入用户"
      width="600px"
    >
      <UserImport
        @success="handleImportSuccess"
        @close="importDialogVisible = false"
      />
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus,
  Search,
  Refresh,
  Delete,
  Download,
  Upload,
  List,
  Grid
} from '@element-plus/icons-vue'
import type { User, UserListQuery } from '@/types/user'
import { getUsers, deleteUser, batchDeleteUsers, exportUsers, toggleUser } from '@/api/user'
import { formatDateTime } from '@/utils/format'
import UserDetail from './components/UserDetail.vue'
import UserImport from './components/UserImport.vue'

const router = useRouter()

// 响应式数据
const loading = ref(false)
const users = ref<User[]>([])
const selectedUsers = ref<User[]>([])
const selectedUser = ref<User | null>(null)
const viewMode = ref<'table' | 'card'>('table')
const detailDialogVisible = ref(false)
const importDialogVisible = ref(false)

// 搜索表单
const searchForm = reactive<UserListQuery>({
  search: '',
  department: '',
  is_active: undefined,
  sort_by: 'created_at',
  sort_order: 'desc'
})

// 分页数据
const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})

// 部门列表
const departments = ref<string[]>([
  '技术部',
  '产品部',
  '运营部',
  '市场部',
  '人事部',
  '财务部'
])

/**
 * 加载用户列表
 */
const loadUsers = async () => {
  try {
    loading.value = true
    const params = {
      ...searchForm,
      page: pagination.page,
      size: pagination.page_size  // 修正参数名
    }
    const response = await getUsers(params)  // 使用正确的API函数
    users.value = response.data.items || response.data.users || []
    pagination.total = response.data.total || 0
  } catch (error) {
    console.error('加载用户列表失败:', error)
    ElMessage.error('加载用户列表失败')
  } finally {
    loading.value = false
  }
}

/**
 * 处理搜索
 */
const handleSearch = () => {
  pagination.page = 1
  loadUsers()
}

/**
 * 处理重置
 */
const handleReset = () => {
  Object.assign(searchForm, {
    search: '',
    department: '',
    is_active: undefined,
    sort_by: 'created_at',
    sort_order: 'desc'
  })
  pagination.page = 1
  loadUsers()
}

/**
 * 处理选择变化
 */
const handleSelectionChange = (selection: User[]) => {
  selectedUsers.value = selection
}

/**
 * 处理页面大小变化
 */
const handleSizeChange = (size: number) => {
  pagination.page_size = size
  pagination.page = 1
  loadUsers()
}

/**
 * 处理当前页变化
 */
const handleCurrentChange = (page: number) => {
  pagination.page = page
  loadUsers()
}

/**
 * 处理新建用户
 */
const handleCreate = () => {
  router.push('/user/create')
}

/**
 * 处理查看用户
 */
const handleView = (user: User) => {
  selectedUser.value = user
  detailDialogVisible.value = true
}

/**
 * 处理编辑用户
 */
const handleEdit = (user: User) => {
  router.push(`/user/edit/${user.id}`)
}

/**
 * 处理删除用户
 */
const handleDelete = async (user: User) => {
  try {
    await deleteUser(user.id.toString())
    ElMessage.success('删除用户成功')
    loadUsers()
  } catch (error) {
    console.error('删除用户失败:', error)
    ElMessage.error('删除用户失败')
  }
}

/**
 * 处理批量删除
 */
const handleBatchDelete = async () => {
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedUsers.value.length} 个用户吗？`,
      '批量删除',
      {
        type: 'warning'
      }
    )
    
    const userIds = selectedUsers.value.map(user => user.id)
    await batchDeleteUsers(userIds)
    ElMessage.success('批量删除成功')
    selectedUsers.value = []
    loadUsers()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('批量删除失败')
    }
  }
}

/**
 * 处理导出
 */
const handleExport = async () => {
  try {
    const params = {
      ...searchForm,
      export_all: true
    }
    await exportUsers(params)
    ElMessage.success('导出成功')
  } catch (error) {
    ElMessage.error('导出失败')
  }
}

/**
 * 处理导入
 */
const handleImport = () => {
  importDialogVisible.value = true
}

/**
 * 处理导入成功
 */
const handleImportSuccess = () => {
  importDialogVisible.value = false
  loadUsers()
}

// 组件挂载时加载数据
onMounted(() => {
  loadUsers()
})
</script>

<style lang="scss" scoped>
@use "@/styles/variables.scss" as *;

.user-list {
  padding: $spacing-lg;
  background-color: var(--el-bg-color-page);
  min-height: 100vh;

  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: $spacing-lg;

    .header-left {
      .page-title {
        margin: 0 0 $spacing-xs 0;
        font-size: $font-size-xl;
        font-weight: 600;
        color: var(--el-text-color-primary);
      }

      .page-description {
        margin: 0;
        color: var(--el-text-color-regular);
        font-size: $font-size-sm;
      }
    }
  }

  .search-section {
    margin-bottom: $spacing-lg;
  }

  .toolbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: $spacing-lg;

    .toolbar-left {
      display: flex;
      gap: $spacing-sm;
    }

    .toolbar-right {
      display: flex;
      gap: $spacing-sm;
      align-items: center;
    }
  }

  .table-section {
    margin-bottom: $spacing-lg;
  }

  .card-section {
    margin-bottom: $spacing-lg;

    .user-cards {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
      gap: $spacing-lg;

      .user-card {
        cursor: pointer;
        transition: transform 0.2s;

        &:hover {
          transform: translateY(-2px);
        }

        .card-header {
          display: flex;
          align-items: center;
          gap: $spacing-md;
          margin-bottom: $spacing-md;

          .user-info {
            flex: 1;

            h3 {
              margin: 0 0 $spacing-xs 0;
              font-size: $font-size-md;
              font-weight: 600;
              color: var(--el-text-color-primary);
            }

            p {
              margin: 0;
              font-size: $font-size-sm;
              color: var(--el-text-color-regular);
            }
          }
        }

        .card-content {
          margin-bottom: $spacing-md;

          .info-item {
            display: flex;
            margin-bottom: $spacing-xs;

            .label {
              width: 80px;
              font-size: $font-size-sm;
              color: var(--el-text-color-regular);
            }

            .value {
              flex: 1;
              font-size: $font-size-sm;
              color: var(--el-text-color-primary);
            }
          }
        }

        .card-actions {
          display: flex;
          gap: $spacing-sm;
          justify-content: flex-end;
        }
      }
    }
  }

  .pagination-section {
    display: flex;
    justify-content: center;
    margin-top: $spacing-lg;
  }
}

// 响应式设计
@media (max-width: 768px) {
  .user-list {
    padding: $spacing-md;

    .page-header {
      flex-direction: column;
      gap: $spacing-md;
    }

    .toolbar {
      flex-direction: column;
      gap: $spacing-md;
      align-items: stretch;

      .toolbar-left,
      .toolbar-right {
        justify-content: center;
      }
    }

    .user-cards {
      grid-template-columns: 1fr;
    }
  }
}

// 暗色主题适配
@media (prefers-color-scheme: dark) {
  .user-list {
    background-color: var(--el-bg-color-page);
  }
}
</style>