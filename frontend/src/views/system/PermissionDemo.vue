<template>
  <div class="permission-demo">
    <el-card class="demo-card">
      <template #header>
        <div class="card-header">
          <span>权限系统演示</span>
          <el-button type="primary" @click="refreshPermissions">
            刷新权限
          </el-button>
        </div>
      </template>

      <!-- 用户信息 -->
      <el-row :gutter="20" class="user-info">
        <el-col :span="12">
          <el-descriptions title="当前用户信息" :column="1" border>
            <el-descriptions-item label="用户名">
              {{ userStore.user?.username || '未登录' }}
            </el-descriptions-item>
            <el-descriptions-item label="角色">
              {{ userStore.roles.join(', ') || '无角色' }}
            </el-descriptions-item>
            <el-descriptions-item label="权限数量">
              {{ userStore.permissions.length }}
            </el-descriptions-item>
            <el-descriptions-item label="是否管理员">
              {{ isAdmin ? '是' : '否' }}
            </el-descriptions-item>
          </el-descriptions>
        </el-col>
        <el-col :span="12">
          <el-descriptions title="缓存统计" :column="1" border>
            <el-descriptions-item label="缓存大小">
              {{ cacheStats.size }}
            </el-descriptions-item>
            <el-descriptions-item label="命中次数">
              {{ cacheStats.hitCount }}
            </el-descriptions-item>
            <el-descriptions-item label="未命中次数">
              {{ cacheStats.missCount }}
            </el-descriptions-item>
            <el-descriptions-item label="命中率">
              {{ (cacheStats.hitRate * 100).toFixed(2) }}%
            </el-descriptions-item>
          </el-descriptions>
        </el-col>
      </el-row>

      <!-- 权限指令演示 -->
      <el-divider content-position="left">权限指令演示</el-divider>
      <div class="directive-demo">
        <el-space wrap>
          <el-button v-permission="'model:read'" type="primary">
            模型查看（需要model:read权限）
          </el-button>
          <el-button v-permission="['model:create', 'model:update']" type="success">
            模型编辑（需要model:create或model:update权限）
          </el-button>
          <el-button v-permission-all="['model:read', 'model:delete']" type="danger">
            模型删除（需要model:read和model:delete权限）
          </el-button>
          <el-button v-role="'admin'" type="warning">
            管理员功能（需要admin角色）
          </el-button>
        </el-space>
      </div>

      <!-- 权限组件演示 -->
      <el-divider content-position="left">权限组件演示</el-divider>
      <div class="component-demo">
        <el-row :gutter="20">
          <el-col :span="8">
            <PermissionWrapper permission="model:create">
              <el-card>
                <h4>创建模型卡片</h4>
                <p>只有拥有model:create权限的用户才能看到此卡片</p>
              </el-card>
            </PermissionWrapper>
          </el-col>
          <el-col :span="8">
            <PermissionWrapper 
              :permissions="['dataset:read', 'dataset:create']" 
              mode="any"
              fallback="show"
              fallback-text="数据集权限不足"
            >
              <el-card>
                <h4>数据集管理卡片</h4>
                <p>需要数据集相关权限</p>
              </el-card>
            </PermissionWrapper>
          </el-col>
          <el-col :span="8">
            <PermissionWrapper role="admin" fallback="show">
              <el-card>
                <h4>管理员专用卡片</h4>
                <p>只有管理员才能看到此卡片</p>
              </el-card>
              <template #fallback>
                <el-card class="fallback-card">
                  <h4>权限不足</h4>
                  <p>您需要管理员权限才能访问此功能</p>
                </el-card>
              </template>
            </PermissionWrapper>
          </el-col>
        </el-row>
      </div>

      <!-- 权限按钮演示 -->
      <el-divider content-position="left">权限按钮演示</el-divider>
      <div class="button-demo">
        <el-space wrap>
          <PermissionButton 
            permission="model:create" 
            type="primary"
            @click="handleCreateModel"
          >
            创建模型
          </PermissionButton>
          <PermissionButton 
            :permissions="['model:update', 'model:delete']" 
            mode="any"
            type="warning"
            behavior="disable"
            @click="handleEditModel"
            @no-permission="handleNoPermission"
          >
            编辑模型
          </PermissionButton>
          <PermissionButton 
            role="admin" 
            type="danger"
            @click="handleAdminAction"
          >
            管理员操作
          </PermissionButton>
        </el-space>
      </div>

      <!-- 权限表格演示 -->
      <el-divider content-position="left">权限表格演示</el-divider>
      <div class="table-demo">
        <PermissionTable 
          :data="tableData" 
          :actions="tableActions"
          @action-click="handleTableAction"
        >
          <el-table-column prop="name" label="名称" />
          <el-table-column prop="type" label="类型" />
          <el-table-column prop="status" label="状态" />
        </PermissionTable>
      </div>

      <!-- 缓存控制 -->
      <el-divider content-position="left">缓存控制</el-divider>
      <div class="cache-control">
        <el-space>
          <el-button @click="clearUserCache">清除用户缓存</el-button>
          <el-button @click="clearAllCache">清除所有缓存</el-button>
          <el-button @click="updateCacheConfig">更新缓存配置</el-button>
        </el-space>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'
import { usePermission } from '@/composables/usePermission'
import { usePermissionCache } from '@/utils/permissionCache'

/**
 * 权限系统演示页面
 * 展示各种权限控制功能的使用方法
 */

const userStore = useUserStore()
const { isAdmin, refreshPermissions } = usePermission()
const { stats: cacheStats, clearUserCache: clearCache, clearAllCache: clearAll, updateCacheConfig } = usePermissionCache()

// 表格数据
const tableData = ref([
  { id: 1, name: '模型A', type: 'LLM', status: '运行中' },
  { id: 2, name: '模型B', type: 'CV', status: '停止' },
  { id: 3, name: '模型C', type: 'NLP', status: '训练中' }
])

// 表格操作配置
const tableActions = ref([
  {
    key: 'view',
    label: '查看',
    permission: 'model:read',
    buttonProps: { type: 'primary', size: 'small' },
    handler: (row: any) => {
      ElMessage.success(`查看模型: ${row.name}`)
    }
  },
  {
    key: 'edit',
    label: '编辑',
    permission: 'model:update',
    buttonProps: { type: 'warning', size: 'small' },
    handler: (row: any) => {
      ElMessage.success(`编辑模型: ${row.name}`)
    }
  },
  {
    key: 'delete',
    label: '删除',
    permission: 'model:delete',
    buttonProps: { type: 'danger', size: 'small' },
    handler: (row: any) => {
      ElMessage.warning(`删除模型: ${row.name}`)
    }
  },
  {
    key: 'deploy',
    label: '部署',
    permissions: ['model:deploy', 'model:update'],
    mode: 'any',
    buttonProps: { type: 'success', size: 'small' },
    show: (row: any) => row.status !== '运行中',
    handler: (row: any) => {
      ElMessage.success(`部署模型: ${row.name}`)
    }
  }
])

// 事件处理函数
const handleCreateModel = () => {
  ElMessage.success('创建模型操作')
}

const handleEditModel = () => {
  ElMessage.success('编辑模型操作')
}

const handleAdminAction = () => {
  ElMessage.success('管理员操作')
}

const handleNoPermission = () => {
  ElMessage.warning('权限不足，无法执行操作')
}

const handleTableAction = (action: any, row: any) => {
  console.log('表格操作:', action.key, row)
}

const clearUserCache = () => {
  const userId = userStore.user?.id?.toString() || 'anonymous'
  clearCache(userId)
  ElMessage.success('用户缓存已清除')
}

const clearAllCache = () => {
  clearAll()
  ElMessage.success('所有缓存已清除')
}

const updateCacheConfig = () => {
  updateCacheConfig({
    defaultTTL: 10 * 60 * 1000, // 10分钟
    maxSize: 500
  })
  ElMessage.success('缓存配置已更新')
}
</script>

<style scoped>
.permission-demo {
  padding: 20px;
}

.demo-card {
  max-width: 1200px;
  margin: 0 auto;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.user-info {
  margin-bottom: 20px;
}

.directive-demo,
.component-demo,
.button-demo,
.table-demo,
.cache-control {
  margin: 20px 0;
}

.fallback-card {
  background-color: var(--el-fill-color-light);
  border: 1px dashed var(--el-border-color);
}

.fallback-card h4 {
  color: var(--el-text-color-placeholder);
}
</style>