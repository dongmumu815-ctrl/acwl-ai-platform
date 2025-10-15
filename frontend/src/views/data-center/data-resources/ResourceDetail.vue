<template>
  <div class="resource-detail">
    <div class="page-header">
      <el-button @click="handleBack" style="margin-right: 16px;">
        <el-icon><ArrowLeft /></el-icon>
        返回
      </el-button>
      <div>
        <h1>{{ resource?.display_name || resource?.name }}</h1>
        <p>{{ resource?.description }}</p>
      </div>
    </div>

    <div v-loading="loading" class="detail-content">
      <el-row :gutter="20">
        <el-col :span="16">
          <!-- 基本信息 -->
          <el-card title="基本信息" class="info-card">
            <el-descriptions :column="2" border>
              <el-descriptions-item label="资源名称">
                {{ resource?.name }}
              </el-descriptions-item>
              <el-descriptions-item label="显示名称">
                {{ resource?.display_name }}
              </el-descriptions-item>
              <el-descriptions-item label="资源类型">
                <el-tag :type="getResourceTypeTag(resource?.resource_type)">
                  {{ getResourceTypeLabel(resource?.resource_type) }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="状态">
                <el-tag :type="getStatusTag(resource?.status)">
                  {{ getStatusLabel(resource?.status) }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="分类">
                {{ resource?.category?.name }}
              </el-descriptions-item>
              <el-descriptions-item label="是否公开">
                <el-tag :type="resource?.is_public ? 'success' : 'info'">
                  {{ resource?.is_public ? '是' : '否' }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="表名">
                {{ resource?.table_name }}
              </el-descriptions-item>
              <el-descriptions-item label="模式名">
                {{ resource?.schema_name || '-' }}
              </el-descriptions-item>
              <el-descriptions-item label="数据量">
                {{ formatNumber(resource?.row_count) }}
              </el-descriptions-item>
              <el-descriptions-item label="存储大小">
                {{ formatSize(resource?.size_mb) }}
              </el-descriptions-item>
              <el-descriptions-item label="访问次数">
                {{ resource?.access_count }}
              </el-descriptions-item>
              <el-descriptions-item label="收藏次数">
                {{ resource?.favorite_count }}
              </el-descriptions-item>
              <el-descriptions-item label="创建时间">
                {{ formatDate(resource?.created_at) }}
              </el-descriptions-item>
              <el-descriptions-item label="更新时间">
                {{ formatDate(resource?.updated_at) }}
              </el-descriptions-item>
            </el-descriptions>
          </el-card>

          <!-- 连接配置 -->
          <el-card title="连接配置" class="info-card">
            <el-descriptions :column="2" border>
              <el-descriptions-item label="主机地址">
                {{ resource?.connection_config?.host }}
              </el-descriptions-item>
              <el-descriptions-item label="端口">
                {{ resource?.connection_config?.port }}
              </el-descriptions-item>
              <el-descriptions-item label="数据库">
                {{ resource?.connection_config?.database || '-' }}
              </el-descriptions-item>
              <el-descriptions-item label="用户名">
                {{ resource?.connection_config?.username }}
              </el-descriptions-item>
            </el-descriptions>
          </el-card>

          <!-- 字段信息 -->
          <el-card title="字段信息" class="info-card">
            <el-table :data="resource?.fields" stripe>
              <el-table-column prop="name" label="字段名" />
              <el-table-column prop="type" label="类型" />
              <el-table-column prop="description" label="描述" />
              <el-table-column prop="is_nullable" label="可空">
                <template #default="{ row }">
                  <el-tag :type="row.is_nullable ? 'warning' : 'success'">
                    {{ row.is_nullable ? '是' : '否' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="is_primary_key" label="主键">
                <template #default="{ row }">
                  <el-tag v-if="row.is_primary_key" type="danger">是</el-tag>
                  <span v-else>-</span>
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </el-col>

        <el-col :span="8">
          <!-- 操作面板 -->
          <el-card title="操作" class="action-card">
            <div class="action-buttons">
              <el-button type="primary" @click="handleQuery">
                <el-icon><Search /></el-icon>
                数据查询
              </el-button>
              <el-button @click="handleEdit">
                <el-icon><Edit /></el-icon>
                编辑资源
              </el-button>
              <el-button @click="handleFavorite">
                <el-icon><Star /></el-icon>
                {{ resource?.is_favorited ? '取消收藏' : '收藏' }}
              </el-button>
              <el-button type="warning" @click="handleSync">
                <el-icon><Refresh /></el-icon>
                同步字段
              </el-button>
              <el-button type="danger" @click="handleDelete">
                <el-icon><Delete /></el-icon>
                删除资源
              </el-button>
            </div>
          </el-card>

          <!-- 标签 -->
          <el-card title="标签" class="tag-card">
            <div class="tags">
              <el-tag
                v-for="tag in resource?.tags"
                :key="tag.id"
                :color="tag.color"
                style="margin: 4px;"
              >
                {{ tag.name }}
              </el-tag>
              <el-tag v-if="!resource?.tags?.length" type="info">暂无标签</el-tag>
            </div>
          </el-card>

          <!-- 统计信息 -->
          <el-card title="统计信息" class="stats-card">
            <div class="stats">
              <div class="stat-item">
                <div class="stat-value">{{ resource?.access_count || 0 }}</div>
                <div class="stat-label">总访问次数</div>
              </div>
              <div class="stat-item">
                <div class="stat-value">{{ resource?.favorite_count || 0 }}</div>
                <div class="stat-label">收藏次数</div>
              </div>
              <div class="stat-item">
                <div class="stat-value">{{ formatNumber(resource?.row_count) }}</div>
                <div class="stat-label">数据行数</div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, Search, Edit, Star, Refresh, Delete } from '@element-plus/icons-vue'
import type { DataResource } from '@/types/data-resource'

/**
 * 路由实例
 */
const route = useRoute()
const router = useRouter()

/**
 * 响应式数据
 */
const loading = ref(false)
const resource = ref<DataResource | null>(null)

/**
 * 获取资源详情
 */
const fetchResourceDetail = async () => {
  const id = route.params.id as string
  loading.value = true
  
  try {
    // TODO: 调用API获取详情
    // const response = await dataResourceApi.getDetail(Number(id))
    // resource.value = response.data
    
    // 模拟数据
    resource.value = {
      id: Number(id),
      name: 'user_behavior',
      display_name: '用户行为数据',
      description: '用户行为分析数据表，包含用户的各种操作记录',
      resource_type: 'doris_table',
      status: 'active',
      category_id: 1,
      category: { id: 1, name: '业务数据' },
      tags: [
        { id: 1, name: '用户数据', color: '#409EFF' },
        { id: 2, name: '行为分析', color: '#67C23A' }
      ],
      connection_config: {
        host: 'localhost',
        port: 9030,
        database: 'analytics',
        username: 'admin'
      },
      table_name: 'user_behavior',
      schema_name: 'public',
      fields: [
        {
          name: 'user_id',
          type: 'BIGINT',
          description: '用户ID',
          is_nullable: false,
          is_primary_key: true,
          is_index: true
        },
        {
          name: 'action_type',
          type: 'VARCHAR(50)',
          description: '操作类型',
          is_nullable: false,
          is_primary_key: false,
          is_index: true
        },
        {
          name: 'timestamp',
          type: 'DATETIME',
          description: '操作时间',
          is_nullable: false,
          is_primary_key: false,
          is_index: true
        }
      ],
      row_count: 1000000,
      size_mb: 256,
      access_count: 150,
      favorite_count: 5,
      is_favorited: false,
      created_by: 1,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
      is_public: true
    }
  } catch (error) {
    ElMessage.error('获取资源详情失败')
  } finally {
    loading.value = false
  }
}

/**
 * 返回上一页
 */
const handleBack = () => {
  router.back()
}

/**
 * 数据查询
 */
const handleQuery = () => {
  router.push(`/data-resources/query/${resource.value?.id}`)
}

/**
 * 编辑资源
 */
const handleEdit = () => {
  router.push(`/data-resources/edit/${resource.value?.id}`)
}

/**
 * 收藏/取消收藏
 */
const handleFavorite = async () => {
  try {
    // TODO: 调用收藏API
    // await dataResourceApi.toggleFavorite(resource.value!.id)
    
    if (resource.value) {
      resource.value.is_favorited = !resource.value.is_favorited
      resource.value.favorite_count += resource.value.is_favorited ? 1 : -1
    }
    
    ElMessage.success(resource.value?.is_favorited ? '收藏成功' : '取消收藏成功')
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

/**
 * 同步字段
 */
const handleSync = async () => {
  try {
    await ElMessageBox.confirm('确定要同步字段信息吗？', '确认同步', {
      type: 'warning'
    })
    
    // TODO: 调用同步API
    // await dataResourceApi.syncFields(resource.value!.id)
    
    ElMessage.success('同步成功')
    fetchResourceDetail()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('同步失败')
    }
  }
}

/**
 * 删除资源
 */
const handleDelete = async () => {
  try {
    await ElMessageBox.confirm('确定要删除这个资源吗？删除后无法恢复！', '确认删除', {
      type: 'warning'
    })
    
    // TODO: 调用删除API
    // await dataResourceApi.delete(resource.value!.id)
    
    ElMessage.success('删除成功')
    router.push('/data-resources/list')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

/**
 * 获取资源类型标签
 */
const getResourceTypeTag = (type?: string) => {
  const tagMap: Record<string, string> = {
    doris_table: 'primary',
    elasticsearch_index: 'success'
  }
  return tagMap[type || ''] || 'info'
}

/**
 * 获取资源类型标签文本
 */
const getResourceTypeLabel = (type?: string) => {
  const labelMap: Record<string, string> = {
    doris_table: 'Doris表',
    elasticsearch_index: 'ES索引'
  }
  return labelMap[type || ''] || type
}

/**
 * 获取状态标签
 */
const getStatusTag = (status?: string) => {
  const tagMap: Record<string, string> = {
    active: 'success',
    inactive: 'warning',
    archived: 'info',
    error: 'danger'
  }
  return tagMap[status || ''] || 'info'
}

/**
 * 获取状态标签文本
 */
const getStatusLabel = (status?: string) => {
  const labelMap: Record<string, string> = {
    active: '活跃',
    inactive: '非活跃',
    archived: '已归档',
    error: '错误'
  }
  return labelMap[status || ''] || status
}

/**
 * 格式化数字
 */
const formatNumber = (num?: number) => {
  if (!num) return '-'
  return num.toLocaleString()
}

/**
 * 格式化大小
 */
const formatSize = (sizeMb?: number) => {
  if (!sizeMb) return '-'
  if (sizeMb < 1024) return `${sizeMb} MB`
  return `${(sizeMb / 1024).toFixed(2)} GB`
}

/**
 * 格式化日期
 */
const formatDate = (date?: string) => {
  if (!date) return '-'
  return new Date(date).toLocaleString()
}

/**
 * 组件挂载时获取数据
 */
onMounted(() => {
  fetchResourceDetail()
})
</script>

<style scoped>
.resource-detail {
  padding: 20px;
}

.page-header {
  display: flex;
  align-items: flex-start;
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

.detail-content {
  min-height: 400px;
}

.info-card,
.action-card,
.tag-card,
.stats-card {
  margin-bottom: 20px;
}

.action-buttons {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.action-buttons .el-button {
  justify-content: flex-start;
}

.tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.stats {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.stat-item {
  text-align: center;
  padding: 12px;
  background: #f5f5f5;
  border-radius: 4px;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: #409EFF;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 12px;
  color: #666;
}
</style>