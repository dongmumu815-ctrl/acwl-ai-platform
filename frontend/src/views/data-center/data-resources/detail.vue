<template>
  <div class="resource-detail-container">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="header-left">
        <el-button @click="handleBack" text>
          <el-icon><ArrowLeft /></el-icon>
          返回列表
        </el-button>
        <h1 class="page-title">
          <el-icon><View /></el-icon>
          资源详情
        </h1>
      </div>
      <div class="header-actions">
        <el-button @click="handleEdit">
          <el-icon><Edit /></el-icon>
          编辑
        </el-button>
        <el-button type="danger" @click="handleDelete">
          <el-icon><Delete /></el-icon>
          删除
        </el-button>
      </div>
    </div>

    <el-row :gutter="24">
      <!-- 主要内容 -->
      <el-col :span="16">
        <!-- 基本信息 -->
        <el-card class="info-card">
          <template #header>
            <div class="card-header">
              <span>基本信息</span>
              <el-tag :type="getStatusTagType(resourceData.status)">
                {{ getStatusLabel(resourceData.status) }}
              </el-tag>
            </div>
          </template>
          
          <div class="resource-info">
            <div class="resource-title">
              <el-icon class="resource-icon" :size="32">
                <component :is="getResourceIcon(resourceData.type)" />
              </el-icon>
              <div>
                <h2>{{ resourceData.name }}</h2>
                <div class="resource-meta">
                  <el-tag :type="getTypeTagType(resourceData.type)">
                    {{ getTypeLabel(resourceData.type) }}
                  </el-tag>
                  <span class="meta-item">
                    <el-icon><User /></el-icon>
                    {{ resourceData.author }}
                  </span>
                  <span class="meta-item">
                    <el-icon><Calendar /></el-icon>
                    {{ resourceData.publishDate }}
                  </span>
                </div>
              </div>
            </div>
            
            <div class="resource-description">
              <h4>资源描述</h4>
              <p>{{ resourceData.description }}</p>
            </div>
            
            <div class="resource-keywords" v-if="resourceData.keywords.length">
              <h4>关键词</h4>
              <el-tag
                v-for="keyword in resourceData.keywords"
                :key="keyword"
                style="margin-right: 8px; margin-bottom: 8px;"
              >
                {{ keyword }}
              </el-tag>
            </div>
          </div>
        </el-card>

        <!-- 文件信息 -->
        <el-card class="file-card">
          <template #header>
            <span>文件信息</span>
          </template>
          
          <div class="file-info">
            <div class="file-item" v-for="file in resourceData.files" :key="file.id">
              <div class="file-icon">
                <el-icon :size="24">
                  <component :is="getFileIcon(file.type)" />
                </el-icon>
              </div>
              <div class="file-details">
                <div class="file-name">{{ file.name }}</div>
                <div class="file-meta">
                  <span>{{ formatSize(file.size) }}</span>
                  <span>{{ file.type }}</span>
                  <span>上传时间：{{ file.uploadTime }}</span>
                </div>
              </div>
              <div class="file-actions">
                <el-button size="small" @click="handlePreviewFile(file)">
                  <el-icon><View /></el-icon>
                  预览
                </el-button>
                <el-button size="small" type="primary" @click="handleDownloadFile(file)">
                  <el-icon><Download /></el-icon>
                  下载
                </el-button>
              </div>
            </div>
          </div>
        </el-card>

        <!-- 元数据 -->
        <el-card class="metadata-card">
          <template #header>
            <span>元数据</span>
          </template>
          
          <el-descriptions :column="2" border>
            <el-descriptions-item label="作者">{{ resourceData.author }}</el-descriptions-item>
            <el-descriptions-item label="出版社/机构">{{ resourceData.publisher }}</el-descriptions-item>
            <el-descriptions-item label="出版日期">{{ resourceData.publishDate }}</el-descriptions-item>
            <el-descriptions-item label="版本号">{{ resourceData.version }}</el-descriptions-item>
            <el-descriptions-item label="语言">{{ getLanguageLabel(resourceData.language) }}</el-descriptions-item>
            <el-descriptions-item label="文件格式">{{ resourceData.format }}</el-descriptions-item>
            <el-descriptions-item label="文件大小">{{ formatSize(resourceData.totalSize) }}</el-descriptions-item>
            <el-descriptions-item label="创建时间">{{ resourceData.createdAt }}</el-descriptions-item>
            <el-descriptions-item label="更新时间">{{ resourceData.updatedAt }}</el-descriptions-item>
            <el-descriptions-item label="创建者">{{ resourceData.creator }}</el-descriptions-item>
          </el-descriptions>
        </el-card>

        <!-- 访问记录 -->
        <el-card class="access-card">
          <template #header>
            <div class="card-header">
              <span>访问记录</span>
              <el-button size="small" @click="refreshAccessLog">
                <el-icon><Refresh /></el-icon>
                刷新
              </el-button>
            </div>
          </template>
          
          <el-table :data="accessLog" style="width: 100%">
            <el-table-column prop="user" label="用户" width="120" />
            <el-table-column prop="action" label="操作" width="100">
              <template #default="{ row }">
                <el-tag :type="getActionTagType(row.action)" size="small">
                  {{ getActionLabel(row.action) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="ip" label="IP地址" width="140" />
            <el-table-column prop="userAgent" label="用户代理" min-width="200" show-overflow-tooltip />
            <el-table-column prop="time" label="时间" width="180" />
          </el-table>
        </el-card>
      </el-col>

      <!-- 侧边栏 -->
      <el-col :span="8">
        <!-- 统计信息 -->
        <el-card class="stats-card">
          <template #header>
            <span>统计信息</span>
          </template>
          
          <div class="stats-grid">
            <div class="stat-item">
              <div class="stat-value">{{ resourceData.views }}</div>
              <div class="stat-label">
                <el-icon><View /></el-icon>
                总访问量
              </div>
            </div>
            <div class="stat-item">
              <div class="stat-value">{{ resourceData.downloads }}</div>
              <div class="stat-label">
                <el-icon><Download /></el-icon>
                总下载量
              </div>
            </div>
            <div class="stat-item">
              <div class="stat-value">{{ resourceData.likes }}</div>
              <div class="stat-label">
                <el-icon><Star /></el-icon>
                点赞数
              </div>
            </div>
            <div class="stat-item">
              <div class="stat-value">{{ resourceData.shares }}</div>
              <div class="stat-label">
                <el-icon><Share /></el-icon>
                分享数
              </div>
            </div>
          </div>
        </el-card>

        <!-- 分类和标签 -->
        <el-card class="category-card">
          <template #header>
            <span>分类和标签</span>
          </template>
          
          <div class="category-info">
            <div class="category-item">
              <h4>所属分类</h4>
              <el-breadcrumb separator="/">
                <el-breadcrumb-item v-for="cat in resourceData.categoryPath" :key="cat">
                  {{ cat }}
                </el-breadcrumb-item>
              </el-breadcrumb>
            </div>
            
            <div class="tags-item" v-if="resourceData.tags.length">
              <h4>标签</h4>
              <el-tag
                v-for="tag in resourceData.tags"
                :key="tag"
                style="margin-right: 8px; margin-bottom: 8px;"
                effect="plain"
              >
                {{ tag }}
              </el-tag>
            </div>
          </div>
        </el-card>

        <!-- 访问控制 -->
        <el-card class="access-control-card">
          <template #header>
            <span>访问控制</span>
          </template>
          
          <div class="access-control-info">
            <div class="control-item">
              <span class="control-label">访问权限：</span>
              <el-tag :type="getAccessLevelTagType(resourceData.accessLevel)">
                {{ getAccessLevelLabel(resourceData.accessLevel) }}
              </el-tag>
            </div>
            
            <div class="control-item">
              <span class="control-label">下载权限：</span>
              <el-tag :type="resourceData.downloadPermission ? 'success' : 'danger'">
                {{ resourceData.downloadPermission ? '允许下载' : '禁止下载' }}
              </el-tag>
            </div>
            
            <div class="control-item" v-if="resourceData.authorizedUsers.length">
              <span class="control-label">授权用户：</span>
              <div class="authorized-users">
                <el-tag
                  v-for="user in resourceData.authorizedUsers"
                  :key="user"
                  size="small"
                  style="margin-right: 4px; margin-bottom: 4px;"
                >
                  {{ user }}
                </el-tag>
              </div>
            </div>
          </div>
        </el-card>

        <!-- 相关资源 -->
        <el-card class="related-card">
          <template #header>
            <span>相关资源</span>
          </template>
          
          <div class="related-resources">
            <div
              v-for="related in relatedResources"
              :key="related.id"
              class="related-item"
              @click="handleViewRelated(related)"
            >
              <div class="related-icon">
                <el-icon>
                  <component :is="getResourceIcon(related.type)" />
                </el-icon>
              </div>
              <div class="related-info">
                <div class="related-name">{{ related.name }}</div>
                <div class="related-meta">
                  <el-tag :type="getTypeTagType(related.type)" size="small">
                    {{ getTypeLabel(related.type) }}
                  </el-tag>
                </div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ArrowLeft,
  View,
  Edit,
  Delete,
  User,
  Calendar,
  Download,
  Refresh,
  Star,
  Share,
  Document,
  Notebook,
  Files,
  Reading,
  Collection,
  Folder
} from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()

// 响应式数据
const loading = ref(false)

// 资源数据
const resourceData = reactive({
  id: 1,
  name: '机器学习基础教程',
  type: 'textbook',
  description: '这是一本全面介绍机器学习基础理论和实践的教程，涵盖了监督学习、无监督学习、强化学习等核心内容。本书适合初学者和有一定基础的读者，通过丰富的案例和实践项目，帮助读者深入理解机器学习的原理和应用。',
  keywords: ['机器学习', '人工智能', '数据科学', '算法', '深度学习'],
  author: '张教授',
  publisher: '清华大学出版社',
  publishDate: '2024-01-15',
  version: 'v2.1',
  language: 'zh',
  format: 'PDF',
  totalSize: 15728640,
  status: 'published',
  views: 1547,
  downloads: 284,
  likes: 89,
  shares: 23,
  categoryPath: ['计算机科学', '人工智能', '机器学习'],
  tags: ['教程', '基础', '实践'],
  accessLevel: 'public',
  downloadPermission: true,
  authorizedUsers: [],
  createdAt: '2024-01-15 10:30:00',
  updatedAt: '2024-01-20 14:20:00',
  creator: '管理员',
  files: [
    {
      id: 1,
      name: '机器学习基础教程.pdf',
      type: 'application/pdf',
      size: 15728640,
      uploadTime: '2024-01-15 10:30:00'
    }
  ]
})

// 访问记录
const accessLog = ref([
  {
    user: '张三',
    action: 'view',
    ip: '192.168.1.100',
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    time: '2024-01-20 15:30:00'
  },
  {
    user: '李四',
    action: 'download',
    ip: '192.168.1.101',
    userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    time: '2024-01-20 14:20:00'
  },
  {
    user: '王五',
    action: 'view',
    ip: '192.168.1.102',
    userAgent: 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
    time: '2024-01-20 13:10:00'
  }
])

// 相关资源
const relatedResources = ref([
  {
    id: 2,
    name: '深度学习实战',
    type: 'book'
  },
  {
    id: 3,
    name: '机器学习算法详解',
    type: 'paper'
  },
  {
    id: 4,
    name: 'Python机器学习库',
    type: 'textbook'
  }
])

/**
 * 获取资源图标
 * @param type 资源类型
 * @returns 图标组件名
 */
const getResourceIcon = (type: string) => {
  const iconMap: Record<string, string> = {
    book: 'Reading',
    article: 'Document',
    conference: 'Files',
    paper: 'Notebook',
    textbook: 'Collection'
  }
  return iconMap[type] || 'Document'
}

/**
 * 获取文件图标
 * @param type 文件类型
 * @returns 图标组件名
 */
const getFileIcon = (type: string) => {
  if (type.includes('pdf')) return 'Document'
  if (type.includes('word')) return 'Notebook'
  if (type.includes('excel')) return 'Files'
  return 'Folder'
}

/**
 * 获取类型标签样式
 * @param type 资源类型
 * @returns 标签样式
 */
const getTypeTagType = (type: string) => {
  const typeMap: Record<string, string> = {
    book: 'primary',
    article: 'success',
    conference: 'warning',
    paper: 'info',
    textbook: 'danger'
  }
  return typeMap[type] || 'info'
}

/**
 * 获取类型标签文本
 * @param type 资源类型
 * @returns 标签文本
 */
const getTypeLabel = (type: string) => {
  const typeMap: Record<string, string> = {
    book: '图书',
    article: '期刊文章',
    conference: '会议录',
    paper: '学术论文',
    textbook: '教材'
  }
  return typeMap[type] || type
}

/**
 * 获取状态标签样式
 * @param status 状态
 * @returns 标签样式
 */
const getStatusTagType = (status: string) => {
  const statusMap: Record<string, string> = {
    published: 'success',
    draft: 'warning',
    offline: 'danger'
  }
  return statusMap[status] || 'info'
}

/**
 * 获取状态标签文本
 * @param status 状态
 * @returns 标签文本
 */
const getStatusLabel = (status: string) => {
  const statusMap: Record<string, string> = {
    published: '已发布',
    draft: '草稿',
    offline: '已下线'
  }
  return statusMap[status] || status
}

/**
 * 获取语言标签
 * @param language 语言代码
 * @returns 语言标签
 */
const getLanguageLabel = (language: string) => {
  const languageMap: Record<string, string> = {
    zh: '中文',
    en: '英文',
    ja: '日文',
    other: '其他'
  }
  return languageMap[language] || language
}

/**
 * 获取访问级别标签样式
 * @param level 访问级别
 * @returns 标签样式
 */
const getAccessLevelTagType = (level: string) => {
  const levelMap: Record<string, string> = {
    public: 'success',
    internal: 'warning',
    private: 'danger'
  }
  return levelMap[level] || 'info'
}

/**
 * 获取访问级别标签文本
 * @param level 访问级别
 * @returns 标签文本
 */
const getAccessLevelLabel = (level: string) => {
  const levelMap: Record<string, string> = {
    public: '公开',
    internal: '内部',
    private: '私有'
  }
  return levelMap[level] || level
}

/**
 * 获取操作标签样式
 * @param action 操作类型
 * @returns 标签样式
 */
const getActionTagType = (action: string) => {
  const actionMap: Record<string, string> = {
    view: 'info',
    download: 'success',
    edit: 'warning',
    delete: 'danger'
  }
  return actionMap[action] || 'info'
}

/**
 * 获取操作标签文本
 * @param action 操作类型
 * @returns 标签文本
 */
const getActionLabel = (action: string) => {
  const actionMap: Record<string, string> = {
    view: '查看',
    download: '下载',
    edit: '编辑',
    delete: '删除'
  }
  return actionMap[action] || action
}

/**
 * 格式化文件大小
 * @param bytes 字节数
 * @returns 格式化后的大小字符串
 */
const formatSize = (bytes: number) => {
  const units = ['B', 'KB', 'MB', 'GB']
  let size = bytes
  let unitIndex = 0
  
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024
    unitIndex++
  }
  
  return `${size.toFixed(1)}${units[unitIndex]}`
}

/**
 * 处理返回
 */
const handleBack = () => {
  router.back()
}

/**
 * 处理编辑
 */
const handleEdit = () => {
  router.push(`/data-center/data-resources/edit/${resourceData.id}`)
}

/**
 * 处理删除
 */
const handleDelete = () => {
  ElMessageBox.confirm(
    `确定要删除资源 "${resourceData.name}" 吗？`,
    '删除确认',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(() => {
    ElMessage.success('删除成功')
    router.push('/data-center/data-resources')
  }).catch(() => {
    ElMessage.info('已取消删除')
  })
}

/**
 * 处理文件预览
 * @param file 文件对象
 */
const handlePreviewFile = (file: any) => {
  ElMessage.info('文件预览功能开发中...')
}

/**
 * 处理文件下载
 * @param file 文件对象
 */
const handleDownloadFile = (file: any) => {
  ElMessage.success(`开始下载 ${file.name}`)
}

/**
 * 刷新访问记录
 */
const refreshAccessLog = () => {
  ElMessage.success('访问记录已刷新')
}

/**
 * 查看相关资源
 * @param resource 相关资源
 */
const handleViewRelated = (resource: any) => {
  router.push(`/data-center/data-resources/detail/${resource.id}`)
}

/**
 * 组件挂载时初始化
 */
onMounted(() => {
  const resourceId = route.params.id
  console.log('查看资源详情:', resourceId)
  // 这里可以根据 resourceId 加载具体的资源数据
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
  align-items: center;
  margin-bottom: 24px;
  
  .header-left {
    display: flex;
    align-items: center;
    gap: 16px;
  }
  
  .page-title {
    display: flex;
    align-items: center;
    font-size: 24px;
    font-weight: 600;
    color: var(--el-text-color-primary);
    margin: 0;
    
    .el-icon {
      margin-right: 8px;
      color: var(--el-color-primary);
    }
  }
  
  .header-actions {
    display: flex;
    gap: 8px;
  }
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.info-card {
  margin-bottom: 24px;
  
  .resource-info {
    .resource-title {
      display: flex;
      align-items: flex-start;
      margin-bottom: 24px;
      
      .resource-icon {
        margin-right: 16px;
        color: var(--el-color-primary);
        margin-top: 4px;
      }
      
      h2 {
        font-size: 24px;
        font-weight: 600;
        margin: 0 0 8px 0;
        color: var(--el-text-color-primary);
      }
      
      .resource-meta {
        display: flex;
        align-items: center;
        gap: 16px;
        
        .meta-item {
          display: flex;
          align-items: center;
          font-size: 14px;
          color: var(--el-text-color-secondary);
          
          .el-icon {
            margin-right: 4px;
          }
        }
      }
    }
    
    .resource-description,
    .resource-keywords {
      margin-bottom: 24px;
      
      h4 {
        font-size: 16px;
        font-weight: 600;
        margin: 0 0 12px 0;
        color: var(--el-text-color-primary);
      }
      
      p {
        line-height: 1.6;
        color: var(--el-text-color-regular);
        margin: 0;
      }
    }
  }
}

.file-card {
  margin-bottom: 24px;
  
  .file-info {
    .file-item {
      display: flex;
      align-items: center;
      padding: 16px;
      border: 1px solid var(--el-border-color-lighter);
      border-radius: 8px;
      margin-bottom: 12px;
      
      &:last-child {
        margin-bottom: 0;
      }
      
      .file-icon {
        margin-right: 16px;
        color: var(--el-color-primary);
      }
      
      .file-details {
        flex: 1;
        
        .file-name {
          font-size: 16px;
          font-weight: 500;
          color: var(--el-text-color-primary);
          margin-bottom: 4px;
        }
        
        .file-meta {
          font-size: 12px;
          color: var(--el-text-color-secondary);
          
          span {
            margin-right: 16px;
          }
        }
      }
      
      .file-actions {
        display: flex;
        gap: 8px;
      }
    }
  }
}

.metadata-card,
.access-card {
  margin-bottom: 24px;
}

.stats-card {
  margin-bottom: 24px;
  
  .stats-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
    
    .stat-item {
      text-align: center;
      padding: 16px;
      background: var(--el-bg-color-page);
      border-radius: 8px;
      
      .stat-value {
        font-size: 24px;
        font-weight: 600;
        color: var(--el-color-primary);
        margin-bottom: 8px;
      }
      
      .stat-label {
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 12px;
        color: var(--el-text-color-secondary);
        
        .el-icon {
          margin-right: 4px;
        }
      }
    }
  }
}

.category-card {
  margin-bottom: 24px;
  
  .category-info {
    .category-item,
    .tags-item {
      margin-bottom: 16px;
      
      &:last-child {
        margin-bottom: 0;
      }
      
      h4 {
        font-size: 14px;
        font-weight: 600;
        margin: 0 0 8px 0;
        color: var(--el-text-color-primary);
      }
    }
  }
}

.access-control-card {
  margin-bottom: 24px;
  
  .access-control-info {
    .control-item {
      display: flex;
      align-items: flex-start;
      margin-bottom: 12px;
      
      &:last-child {
        margin-bottom: 0;
      }
      
      .control-label {
        font-size: 14px;
        color: var(--el-text-color-secondary);
        margin-right: 8px;
        min-width: 80px;
      }
      
      .authorized-users {
        flex: 1;
      }
    }
  }
}

.related-card {
  .related-resources {
    .related-item {
      display: flex;
      align-items: center;
      padding: 12px;
      border-radius: 8px;
      cursor: pointer;
      transition: background-color 0.3s;
      
      &:hover {
        background: var(--el-bg-color-page);
      }
      
      .related-icon {
        margin-right: 12px;
        color: var(--el-color-primary);
      }
      
      .related-info {
        flex: 1;
        
        .related-name {
          font-size: 14px;
          font-weight: 500;
          color: var(--el-text-color-primary);
          margin-bottom: 4px;
        }
        
        .related-meta {
          font-size: 12px;
        }
      }
    }
  }
}

// 响应式设计
@media (max-width: 768px) {
  .resource-detail-container {
    padding: 16px;
  }
  
  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }
  
  .stats-grid {
    grid-template-columns: 1fr !important;
  }
  
  .file-item {
    flex-direction: column;
    align-items: flex-start !important;
    
    .file-actions {
      margin-top: 12px;
      width: 100%;
      justify-content: flex-end;
    }
  }
}
</style>