<template>
  <div class="resource-detail-container" v-loading="loading">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <el-button @click="goBack" class="back-button">
          <el-icon><ArrowLeft /></el-icon>
          返回
        </el-button>
        <div class="title-section">
          <h1 class="page-title">
            <el-icon class="resource-icon" :style="{ color: getTypeColor(resource.resource_type) }">
              <component :is="getTypeIcon(resource.resource_type)" />
            </el-icon>
            {{ resource.display_name || resource.name }}
          </h1>
          <div class="title-meta">
            <el-tag :type="getTypeTagType(resource.resource_type)">{{ getTypeLabel(resource.resource_type) }}</el-tag>
            <el-tag :type="getStatusTagType(resource.status)">{{ getStatusLabel(resource.status) }}</el-tag>
            <span class="meta-text">创建于 {{ formatDate(resource.created_at) }}</span>
          </div>
        </div>
      </div>
      
      <div class="header-actions">
        <el-button @click="downloadResource">
          <el-icon><Download /></el-icon>
          下载
        </el-button>
        <el-button @click="shareResource">
          <el-icon><Share /></el-icon>
          分享
        </el-button>
        <el-button type="primary" @click="editResource">
          <el-icon><Edit /></el-icon>
          编辑
        </el-button>
        <el-dropdown trigger="click">
          <el-button>
            更多<el-icon class="el-icon--right"><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item @click="copyResource">
                <el-icon><CopyDocument /></el-icon>复制链接
              </el-dropdown-item>
              <el-dropdown-item @click="exportResource">
                <el-icon><Upload /></el-icon>导出
              </el-dropdown-item>
              <el-dropdown-item divided @click="deleteResource">
                <el-icon><Delete /></el-icon>删除
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <!-- 主要内容区域 -->
    <div class="content-area">
      <!-- 左侧详情信息 -->
      <div class="detail-panel">
        <!-- 基本信息 -->
        <div class="info-card">
          <h3 class="card-title">
            <el-icon><InfoFilled /></el-icon>
            基本信息
          </h3>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="资源名称">
              {{ resource.display_name || resource.name }}
            </el-descriptions-item>
            <el-descriptions-item label="资源类型">
              <el-tag :type="getTypeTagType(resource.resource_type)">{{ getTypeLabel(resource.resource_type) }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="文件大小">
              {{ getResourceSize() }}
            </el-descriptions-item>
            <el-descriptions-item label="记录数">
              <span v-if="getRecordCount() !== null">{{ formatNumber(getRecordCount()) }}</span>
              <span v-else class="text-placeholder">-</span>
            </el-descriptions-item>
            <el-descriptions-item label="状态">
              <el-tag :type="getStatusTagType(resource.status)">{{ getStatusLabel(resource.status) }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="所有者">
              <div class="owner-info">
                <el-avatar :size="24" :src="getCreatorInfo().avatar">
                  {{ getCreatorInfo().full_name.charAt(0) }}
                </el-avatar>
                <span>{{ getCreatorInfo().full_name }}</span>
              </div>
            </el-descriptions-item>
            <el-descriptions-item label="创建时间">
              {{ formatDate(resource.created_at) }}
            </el-descriptions-item>
            <el-descriptions-item label="最后修改">
              {{ formatDate(resource.updated_at) }}
            </el-descriptions-item>
            <el-descriptions-item label="最后访问">
              {{ resource.last_accessed_at ? formatDate(resource.last_accessed_at) : '从未访问' }}
            </el-descriptions-item>
            <el-descriptions-item label="访问次数">
              {{ getAccessCount() }} 次
            </el-descriptions-item>
            <el-descriptions-item label="数据源" v-if="resource.datasource">
              <div class="datasource-info">
                <el-tag size="small">{{ resource.datasource.name }}</el-tag>
                <span class="datasource-desc">{{ resource.datasource.description }}</span>
              </div>
            </el-descriptions-item>
            <el-descriptions-item label="索引名称" v-if="resource.index_name">
              <el-tag type="info" size="small">{{ resource.index_name }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="描述" span="2">
              {{ resource.description || '暂无描述' }}
            </el-descriptions-item>
          </el-descriptions>
        </div>

        <!-- 数据预览 -->
        <div class="info-card" v-if="resource.resource_type === 'elasticsearch_index' || resource.resource_type === 'DORIS_TABLE'">
          <h3 class="card-title">
            <el-icon><View /></el-icon>
            数据预览
            <el-button size="small" @click="refreshPreview" class="refresh-btn">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
          </h3>
          
          <div class="preview-content" v-loading="previewLoading">
            <el-table
              :data="previewData"
              stripe
              style="width: 100%"
              max-height="400"
            >
              <el-table-column
                v-for="column in previewColumns"
                :key="column.prop"
                :prop="column.prop"
                :label="column.label"
                :width="column.width"
                show-overflow-tooltip
              />
            </el-table>
            
            <div class="preview-footer" v-if="previewData.length > 0">
              <span class="preview-info">
                显示前 {{ previewData.length }} 条记录，共 {{ getRecordCount() || 0 }} 条
              </span>
              <el-button size="small" @click="viewFullData">
                查看完整数据
              </el-button>
            </div>
          </div>
        </div>

        <!-- 权限信息 -->
        <div class="info-card">
          <h3 class="card-title">
            <el-icon><Lock /></el-icon>
            权限信息
          </h3>
          
          <div class="permission-content">
            <div class="permission-item">
              <span class="permission-label">访问权限：</span>
              <el-tag :type="permissions.read ? 'success' : 'danger'">
                {{ permissions.read ? '可读' : '不可读' }}
              </el-tag>
            </div>
            
            <div class="permission-item">
              <span class="permission-label">下载权限：</span>
              <el-tag :type="permissions.download ? 'success' : 'danger'">
                {{ permissions.download ? '可下载' : '不可下载' }}
              </el-tag>
            </div>
            
            <div class="permission-item">
              <span class="permission-label">编辑权限：</span>
              <el-tag :type="permissions.edit ? 'success' : 'danger'">
                {{ permissions.edit ? '可编辑' : '不可编辑' }}
              </el-tag>
            </div>
            
            <div class="permission-item">
              <span class="permission-label">删除权限：</span>
              <el-tag :type="permissions.delete ? 'success' : 'danger'">
                {{ permissions.delete ? '可删除' : '不可删除' }}
              </el-tag>
            </div>
            
            <div class="permission-item">
              <span class="permission-label">公开状态：</span>
              <el-tag :type="resource.is_public ? 'success' : 'warning'">
                {{ resource.is_public ? '公开' : '私有' }}
              </el-tag>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 右侧统计和活动 -->
      <div class="sidebar-panel">
        <!-- 访问统计 -->
        <div class="info-card">
          <h3 class="card-title">
            <el-icon><TrendCharts /></el-icon>
            访问统计
          </h3>
          
          <div class="stats-content">
            <div class="stat-item">
              <div class="stat-value">{{ getAccessCount() }}</div>
              <div class="stat-label">总访问次数</div>
            </div>
            
            <div class="stat-item">
              <div class="stat-value">{{ getQueryCount() }}</div>
              <div class="stat-label">查询次数</div>
            </div>
            
            <div class="stat-item">
              <div class="stat-value">{{ getTagCount() }}</div>
              <div class="stat-label">标签数量</div>
            </div>
          </div>
          
          <!-- 访问趋势图 -->
          <div class="chart-container" ref="accessChartRef"></div>
        </div>
        
        <!-- 最近活动 -->
        <div class="info-card">
          <h3 class="card-title">
            <el-icon><Clock /></el-icon>
            最近活动
          </h3>
          
          <div class="activity-list">
            <div
              v-for="activity in recentActivities"
              :key="activity.id"
              class="activity-item"
            >
              <div class="activity-icon">
                <el-icon :style="{ color: getActivityColor(activity.type) }">
                  <component :is="getActivityIcon(activity.type)" />
                </el-icon>
              </div>
              <div class="activity-content">
                <div class="activity-text">{{ activity.description }}</div>
                <div class="activity-time">{{ formatRelativeTime(activity.createdAt) }}</div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 相关资源 -->
        <div class="info-card">
          <h3 class="card-title">
            <el-icon><Connection /></el-icon>
            相关资源
          </h3>
          
          <div class="related-resources">
            <div
              v-for="relatedResource in relatedResources"
              :key="relatedResource.id"
              class="related-item"
              @click="viewRelatedResource(relatedResource)"
            >
              <el-icon class="related-icon" :style="{ color: getTypeColor(relatedResource.type) }">
                <component :is="getTypeIcon(relatedResource.type)" />
              </el-icon>
              <div class="related-content">
                <div class="related-name">{{ relatedResource.name }}</div>
                <div class="related-desc">{{ relatedResource.description }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import * as echarts from 'echarts'
import { dataResourceApi } from '@/api/dataResource'
import type { DataResource } from '@/types/dataResource'

// 路由相关
const router = useRouter()
const route = useRoute()

// 响应式数据
const loading = ref(false)
const previewLoading = ref(false)
const accessChartRef = ref<HTMLElement>()
let accessChart: any = null

// 资源详情数据 - 根据实际API响应结构初始化
const resource = ref<any>({
  id: null,
  name: '',
  display_name: '',
  description: '',
  resource_type: '',
  status: '',
  category: null,
  category_id: null,
  tags: null,
  tag_list: null,
  database_name: null,
  table_name: null,
  index_name: null,
  schema_info: null,
  datasource: null,
  datasource_id: null,
  is_public: false,
  is_favorited: null,
  view_count: 0,
  query_count: 0,
  created_at: '',
  updated_at: '',
  created_by: null,
  updated_by: null,
  last_accessed_at: null,
  user_permission: null
})

// 权限信息
const permissions = ref({
  read: true,
  download: false,
  edit: false,
  delete: false
})

// 数据预览
const previewColumns = ref([
  { prop: 'id', label: 'ID', width: 80 },
  { prop: 'userId', label: '用户ID', width: 100 },
  { prop: 'action', label: '操作', width: 120 },
  { prop: 'page', label: '页面', width: 150 },
  { prop: 'timestamp', label: '时间戳', width: 180 }
])

const previewData = ref([
  {
    id: 1,
    userId: 'U001',
    action: '页面访问',
    page: '/dashboard',
    timestamp: '2024-01-15 14:30:00'
  },
  {
    id: 2,
    userId: 'U002',
    action: '按钮点击',
    page: '/user/profile',
    timestamp: '2024-01-15 14:29:45'
  },
  {
    id: 3,
    userId: 'U003',
    action: '表单提交',
    page: '/settings',
    timestamp: '2024-01-15 14:29:30'
  },
  {
    id: 4,
    userId: 'U001',
    action: '文件下载',
    page: '/resources',
    timestamp: '2024-01-15 14:29:15'
  },
  {
    id: 5,
    userId: 'U004',
    action: '搜索查询',
    page: '/search',
    timestamp: '2024-01-15 14:29:00'
  }
])

// 最近活动
const recentActivities = ref([
  {
    id: 1,
    type: 'access',
    description: '张三访问了该资源',
    createdAt: '2024-01-15 14:30:00'
  },
  {
    id: 2,
    type: 'download',
    description: '李四下载了该资源',
    createdAt: '2024-01-15 13:45:00'
  },
  {
    id: 3,
    type: 'share',
    description: '王五分享了该资源',
    createdAt: '2024-01-15 12:20:00'
  },
  {
    id: 4,
    type: 'edit',
    description: '张三编辑了资源信息',
    createdAt: '2024-01-15 10:15:00'
  }
])

// 相关资源
const relatedResources = ref([
  {
    id: 2,
    name: '用户画像数据',
    description: '基于行为数据生成的用户画像',
    type: 'database'
  },
  {
    id: 3,
    name: '行为分析报表',
    description: '用户行为数据分析报告',
    type: 'report'
  },
  {
    id: 4,
    name: '数据清洗脚本',
    description: '用于清洗行为数据的脚本文件',
    type: 'file'
  }
])

/**
 * 获取类型图标
 */
const getTypeIcon = (type: string) => {
  const iconMap: Record<string, string> = {
    DORIS_TABLE: 'DataBoard',
    ELASTICSEARCH_INDEX: 'Search',
    elasticsearch_index: 'Search',
    database: 'Coin',
    file: 'Document',
    api: 'Connection',
    report: 'DataAnalysis'
  }
  return iconMap[type] || 'Document'
}

/**
 * 获取类型颜色
 */
const getTypeColor = (type: string) => {
  const colorMap: Record<string, string> = {
    DORIS_TABLE: '#409EFF',
    ELASTICSEARCH_INDEX: '#67C23A',
    elasticsearch_index: '#67C23A',
    database: '#409EFF',
    file: '#67C23A',
    api: '#E6A23C',
    report: '#F56C6C'
  }
  return colorMap[type] || '#909399'
}

/**
 * 获取类型标签类型
 */
const getTypeTagType = (type: string) => {
  const tagMap: Record<string, string> = {
    DORIS_TABLE: 'primary',
    ELASTICSEARCH_INDEX: 'success',
    elasticsearch_index: 'success',
    database: 'primary',
    file: 'success',
    api: 'warning',
    report: 'danger'
  }
  return tagMap[type] || 'info'
}

/**
 * 获取类型标签文本
 */
const getTypeLabel = (type: string) => {
  const labelMap: Record<string, string> = {
    DORIS_TABLE: 'Doris表',
    ELASTICSEARCH_INDEX: 'ES索引',
    elasticsearch_index: 'ES索引',
    database: '数据库',
    file: '文件',
    api: 'API',
    report: '报表'
  }
  return labelMap[type] || type
}

/**
 * 获取状态标签类型
 */
const getStatusTagType = (status: string) => {
  const tagMap: Record<string, string> = {
    ACTIVE: 'success',
    INACTIVE: 'warning',
    ARCHIVED: 'info',
    ERROR: 'danger'
  }
  return tagMap[status] || 'info'
}

/**
 * 获取状态标签文本
 */
const getStatusLabel = (status: string) => {
  const labelMap: Record<string, string> = {
    ACTIVE: '正常',
    INACTIVE: '停用',
    ARCHIVED: '归档',
    ERROR: '错误'
  }
  return labelMap[status] || status
}

/**
 * 获取活动图标
 */
const getActivityIcon = (type: string) => {
  const iconMap: Record<string, string> = {
    access: 'View',
    download: 'Download',
    share: 'Share',
    edit: 'Edit'
  }
  return iconMap[type] || 'InfoFilled'
}

/**
 * 获取活动颜色
 */
const getActivityColor = (type: string) => {
  const colorMap: Record<string, string> = {
    access: '#409EFF',
    download: '#67C23A',
    share: '#E6A23C',
    edit: '#F56C6C'
  }
  return colorMap[type] || '#909399'
}

/**
 * 格式化文件大小
 */
const formatSize = (bytes: number | null) => {
  if (bytes === null) return '-'
  if (bytes === 0) return '0 B'
  
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

/**
 * 格式化数字
 */
const formatNumber = (num: number) => {
  return num.toLocaleString()
}

/**
 * 格式化日期
 */
const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleString('zh-CN')
}

/**
 * 格式化相对时间
 */
const formatRelativeTime = (dateStr: string) => {
  const now = new Date()
  const date = new Date(dateStr)
  const diff = now.getTime() - date.getTime()
  
  const minutes = Math.floor(diff / (1000 * 60))
  const hours = Math.floor(diff / (1000 * 60 * 60))
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  
  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  if (hours < 24) return `${hours}小时前`
  if (days < 7) return `${days}天前`
  
  return formatDate(dateStr)
}

/**
 * 返回上一页
 */
const goBack = () => {
  router.back()
}

/**
 * 下载资源
 */
const downloadResource = () => {
  if (!resource.value.permissions.download) {
    ElMessage.warning('您没有下载权限')
    return
  }
  ElMessage.success(`开始下载: ${resource.value.display_name || resource.value.name}`)
}

/**
 * 分享资源
 */
const shareResource = () => {
  ElMessage.info(`分享资源: ${resource.value.name}`)
}

/**
 * 编辑资源
 */
const editResource = () => {
  if (!resource.value.permissions.edit) {
    ElMessage.warning('您没有编辑权限')
    return
  }
  ElMessage.info(`编辑资源: ${resource.value.name}`)
}

/**
 * 复制资源链接
 */
const copyResource = () => {
  ElMessage.success(`已复制资源链接: ${resource.value.name}`)
}

/**
 * 导出资源
 */
const exportResource = () => {
  ElMessage.info(`导出资源: ${resource.value.name}`)
}

/**
 * 删除资源
 */
const deleteResource = () => {
  if (!resource.value.permissions.delete) {
    ElMessage.warning('您没有删除权限')
    return
  }
  
  ElMessageBox.confirm(
    `确定要删除资源 "${resource.value.name}" 吗？`,
    '确认删除',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(() => {
    ElMessage.success('资源删除成功')
    router.push('/data-center/resources')
  }).catch(() => {
    // 用户取消删除
  })
}

/**
 * 刷新预览数据
 */
const refreshPreview = () => {
  previewLoading.value = true
  
  // 模拟刷新
  setTimeout(() => {
    previewLoading.value = false
    ElMessage.success('预览数据已刷新')
  }, 1000)
}

/**
 * 查看完整数据
 */
const viewFullData = () => {
  // 跳转到数据查看页面或打开数据查看对话框
  ElMessage.info('功能开发中，敬请期待')
}

/**
 * 查看相关资源
 */
const viewRelatedResource = (relatedResource: any) => {
  router.push(`/data-resources/detail/${relatedResource.id}`)
}

/**
 * 获取创建者信息
 */
const getCreatorInfo = () => {
  // 由于API返回的是created_by（用户ID），这里需要根据实际情况处理
  // 可能需要额外的API调用来获取用户详细信息
  if (resource.value.created_by) {
    return {
      id: resource.value.created_by,
      username: `用户${resource.value.created_by}`,
      full_name: `用户${resource.value.created_by}`,
      avatar: null
    }
  }
  return {
    id: null,
    username: '未知用户',
    full_name: '未知用户',
    avatar: null
  }
}

/**
 * 获取文件大小显示
 */
const getResourceSize = () => {
  // API中没有直接的size字段，可能需要根据resource_type来处理
  if (resource.value.schema_info && resource.value.schema_info.row_count) {
    return `约 ${formatNumber(resource.value.schema_info.row_count)} 条记录`
  }
  return '未知大小'
}

/**
 * 获取记录数
 */
const getRecordCount = () => {
  if (resource.value.schema_info && resource.value.schema_info.row_count) {
    return resource.value.schema_info.row_count
  }
  return null
}

/**
 * 获取访问次数
 */
const getAccessCount = () => {
  return resource.value.view_count || 0
}

/**
 * 获取查询次数
 */
const getQueryCount = () => {
  return resource.value.query_count || 0
}

/**
 * 获取标签数量
 */
const getTagCount = () => {
  if (resource.value.tags && Array.isArray(resource.value.tags)) {
    return resource.value.tags.length
  }
  if (resource.value.tag_list && Array.isArray(resource.value.tag_list)) {
    return resource.value.tag_list.length
  }
  return 0
}

/**
 * 加载资源详情数据
 */
const loadResourceDetail = async () => {
  const resourceId = route.params.id as string
  if (!resourceId) {
    ElMessage.error('资源ID不能为空')
    router.push('/data-resources/list')
    return
  }

  loading.value = true
  try {
    console.log('正在加载资源详情，ID:', resourceId)
    const response = await dataResourceApi.getResourceDetail(Number(resourceId))
    
    // 检查响应是否为标准 ApiResponse 结构
    let resourceData = null
    if (response && response.success && response.data) {
      resourceData = response.data
    } else {
      throw new Error('无法获取资源数据')
    }
    
    if (resourceData) {
      // 直接使用API返回的数据结构
      resource.value = resourceData
      console.log('资源详情加载成功:', resourceData)
      
      // 设置权限信息
      permissions.value = {
        read: true,
        download: resource.value.is_public || false,
        edit: false, // 根据user_permission字段设置
        delete: false // 根据user_permission字段设置
      }
      
      // 如果有用户权限信息，更新权限设置
      if (resource.value.user_permission) {
        permissions.value = {
          ...permissions.value,
          ...resource.value.user_permission
        }
      }
      
      // 加载预览数据（如果是支持的类型）
      if (resource.value.resource_type === 'elasticsearch_index' || 
          resource.value.resource_type === 'DORIS_TABLE') {
        await loadPreviewData()
      }
    } else {
      throw new Error('无法获取资源数据')
    }
  } catch (error) {
    console.error('加载资源详情失败:', error)
    ElMessage.error(`加载资源详情失败: ${error.message || '请稍后重试'}`)
    // 可以选择返回列表页面或显示错误页面
    // router.push('/data-resources/list')
  } finally {
    loading.value = false
  }
}

/**
 * 加载预览数据
 */
const loadPreviewData = async () => {
  if (!resource.value.id) return
  
  previewLoading.value = true
  try {
    // 这里可以调用预览数据的API
    // const previewResponse = await dataResourceApi.getResourcePreview(resource.value.id)
    // previewData.value = previewResponse.data.rows
    // previewColumns.value = previewResponse.data.columns
    
    // 暂时使用模拟数据
    console.log('加载预览数据...')
    setTimeout(() => {
      previewLoading.value = false
    }, 1000)
  } catch (error) {
    console.error('加载预览数据失败:', error)
    ElMessage.warning('预览数据加载失败')
    previewLoading.value = false
  }
}

/**
 * 初始化访问趋势图
 */
const initAccessChart = () => {
  if (!accessChartRef.value) return
  
  accessChart = echarts.init(accessChartRef.value)
  
  const option = {
    title: {
      text: '最近7天访问趋势',
      textStyle: {
        fontSize: 14,
        fontWeight: 'normal'
      }
    },
    tooltip: {
      trigger: 'axis'
    },
    xAxis: {
      type: 'category',
      data: ['1/9', '1/10', '1/11', '1/12', '1/13', '1/14', '1/15']
    },
    yAxis: {
      type: 'value'
    },
    series: [
      {
        name: '访问次数',
        type: 'line',
        smooth: true,
        data: [12, 19, 15, 22, 18, 25, 20],
        itemStyle: {
          color: '#409EFF'
        },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(64, 158, 255, 0.3)' },
              { offset: 1, color: 'rgba(64, 158, 255, 0.1)' }
            ]
          }
        }
      }
    ],
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    }
  }
  
  accessChart.setOption(option)
}

/**
 * 组件挂载时初始化
 */
onMounted(async () => {
  console.log('ResourceDetail组件挂载，路由参数:', route.params)
  
  // 加载资源详情
  await loadResourceDetail()
  
  // 初始化图表
  setTimeout(() => {
    initAccessChart()
  }, 100)
  
  // 监听窗口大小变化
  window.addEventListener('resize', () => {
    accessChart?.resize()
  })
})

/**
 * 组件卸载时清理
 */
onUnmounted(() => {
  accessChart?.dispose()
  window.removeEventListener('resize', () => {
    accessChart?.resize()
  })
})
</script>

<style lang="scss" scoped>
.resource-detail-container {
  padding: 20px;
  background: var(--el-bg-color-page);
  min-height: 100vh;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  
  .header-left {
    display: flex;
    align-items: flex-start;
    gap: 16px;
    
    .back-button {
      margin-top: 8px;
    }
    
    .title-section {
      .page-title {
        display: flex;
        align-items: center;
        font-size: 28px;
        font-weight: 600;
        color: var(--el-text-color-primary);
        margin: 0 0 8px 0;
        
        .resource-icon {
          margin-right: 12px;
          font-size: 32px;
        }
      }
      
      .title-meta {
        display: flex;
        align-items: center;
        gap: 12px;
        
        .meta-text {
          color: var(--el-text-color-secondary);
          font-size: 14px;
        }
      }
    }
  }
  
  .header-actions {
    display: flex;
    gap: 12px;
    margin-top: 8px;
  }
}

.content-area {
  display: flex;
  gap: 20px;
}

.detail-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.sidebar-panel {
  flex: 0 0 320px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.info-card {
  background: var(--el-bg-color);
  border-radius: 8px;
  border: 1px solid var(--el-border-color-light);
  overflow: hidden;
  
  .card-title {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px 20px;
    margin: 0;
    font-size: 16px;
    font-weight: 600;
    color: var(--el-text-color-primary);
    border-bottom: 1px solid var(--el-border-color-lighter);
    background: var(--el-bg-color-page);
    
    .el-icon {
      margin-right: 8px;
      color: var(--el-color-primary);
    }
    
    .refresh-btn {
      margin-left: auto;
    }
  }
}

.owner-info {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .datasource-info {
    display: flex;
    align-items: center;
    gap: 8px;
    
    .datasource-desc {
      color: var(--el-text-color-regular);
      font-size: 12px;
    }
  }

.text-placeholder {
  color: var(--el-text-color-placeholder);
}

.preview-content {
  padding: 20px;
  
  .preview-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 16px;
    padding-top: 16px;
    border-top: 1px solid var(--el-border-color-lighter);
    
    .preview-info {
      color: var(--el-text-color-secondary);
      font-size: 14px;
    }
  }
}

.permission-content {
  padding: 20px;
  
  .permission-item {
    display: flex;
    align-items: center;
    margin-bottom: 12px;
    
    &:last-child {
      margin-bottom: 0;
    }
    
    .permission-label {
      width: 80px;
      color: var(--el-text-color-regular);
      font-size: 14px;
    }
  }
}

.stats-content {
  display: flex;
  justify-content: space-around;
  padding: 20px;
  
  .stat-item {
    text-align: center;
    
    .stat-value {
      font-size: 24px;
      font-weight: 600;
      color: var(--el-color-primary);
      margin-bottom: 4px;
    }
    
    .stat-label {
      font-size: 12px;
      color: var(--el-text-color-secondary);
    }
  }
}

.chart-container {
  height: 200px;
  padding: 0 20px 20px;
}

.activity-list {
  padding: 20px;
  max-height: 300px;
  overflow-y: auto;
  
  .activity-item {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    margin-bottom: 16px;
    
    &:last-child {
      margin-bottom: 0;
    }
    
    .activity-icon {
      flex: 0 0 24px;
      height: 24px;
      display: flex;
      align-items: center;
      justify-content: center;
      margin-top: 2px;
    }
    
    .activity-content {
      flex: 1;
      
      .activity-text {
        color: var(--el-text-color-primary);
        font-size: 14px;
        margin-bottom: 2px;
      }
      
      .activity-time {
        color: var(--el-text-color-secondary);
        font-size: 12px;
      }
    }
  }
}

.related-resources {
  padding: 20px;
  
  .related-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.2s;
    margin-bottom: 8px;
    
    &:last-child {
      margin-bottom: 0;
    }
    
    &:hover {
      background: var(--el-bg-color-page);
      transform: translateY(-1px);
    }
    
    .related-icon {
      flex: 0 0 20px;
      font-size: 20px;
    }
    
    .related-content {
      flex: 1;
      
      .related-name {
        color: var(--el-text-color-primary);
        font-size: 14px;
        font-weight: 500;
        margin-bottom: 2px;
      }
      
      .related-desc {
        color: var(--el-text-color-secondary);
        font-size: 12px;
        line-height: 1.4;
      }
    }
  }
}

// 响应式设计
@media (max-width: 1200px) {
  .content-area {
    flex-direction: column;
  }
  
  .sidebar-panel {
    flex: none;
  }
}

@media (max-width: 768px) {
  .resource-detail-container {
    padding: 16px;
  }
  
  .page-header {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
    
    .header-left {
      flex-direction: column;
      gap: 12px;
      
      .back-button {
        align-self: flex-start;
        margin-top: 0;
      }
    }
    
    .header-actions {
      justify-content: center;
      flex-wrap: wrap;
      margin-top: 0;
    }
  }
  
  .stats-content {
    flex-direction: column;
    gap: 16px;
    
    .stat-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      text-align: left;
      
      .stat-value {
        margin-bottom: 0;
      }
    }
  }
}
</style>