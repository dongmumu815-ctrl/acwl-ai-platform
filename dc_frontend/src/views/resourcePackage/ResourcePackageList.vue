<template>
  <div class="resource-package-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-left">
          <h1 class="page-title">
            <el-icon>
              <Box />
            </el-icon>
            资源包管理
            <span class="page-description">管理和配置数据查询资源包，支持SQL和Elasticsearch查询</span>
          </h1>
        </div>
        <div class="header-right">
          <el-button type="primary" @click="handleCreate">
            <el-icon>
              <Plus />
            </el-icon>
            创建资源包
          </el-button>
          <el-button @click="refreshPackages">
            <el-icon>
              <Refresh />
            </el-icon>
            刷新
          </el-button>
        </div>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-cards">
      <el-row :gutter="20">
        <el-col :xs="12" :sm="6">
          <div class="stat-card">
            <div class="stat-icon total">
              <el-icon>
                <Box />
              </el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.total }}</div>
              <div class="stat-label">总资源包</div>
            </div>
          </div>
        </el-col>

        <el-col :xs="12" :sm="6">
          <div class="stat-card">
            <div class="stat-icon active">
              <el-icon>
                <CircleCheck />
              </el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.active }}</div>
              <div class="stat-label">启用中</div>
            </div>
          </div>
        </el-col>

        <el-col :xs="12" :sm="6">
          <div class="stat-card">
            <div class="stat-icon sql">
              <el-icon>
                <Coin />
              </el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.sqlCount }}</div>
              <div class="stat-label">SQL类型</div>
            </div>
          </div>
        </el-col>

        <el-col :xs="12" :sm="6">
          <div class="stat-card">
            <div class="stat-icon elasticsearch">
              <el-icon>
                <Search />
              </el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.elasticsearchCount }}</div>
              <div class="stat-label">ES类型</div>
            </div>
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- 筛选和搜索 -->
    <div class="filter-section">
      <el-card shadow="never">
        <el-form :model="filters" inline>
          <el-form-item label="搜索">
            <el-input v-model="filters.search" placeholder="搜索资源包名称或描述" clearable style="width: 250px"
              @input="handleSearch">
              <template #prefix>
                <el-icon>
                  <Search />
                </el-icon>
              </template>
            </el-input>
          </el-form-item>

          <el-form-item label="类型">
            <el-select v-model="filters.type" placeholder="选择类型" clearable style="width: 150px" @change="handleFilter">
              <el-option label="全部" value="" />
              <el-option label="SQL" value="sql" />
              <el-option label="Elasticsearch" value="elasticsearch" />
            </el-select>
          </el-form-item>

          <el-form-item label="数据源">
            <el-select v-model="filters.datasource_id" placeholder="选择数据源" clearable style="width: 150px"
              @change="handleFilter">
              <el-option label="全部" value="" />
              <el-option v-for="ds in datasources" :key="ds.id" :label="ds.name" :value="ds.id" />
            </el-select>
          </el-form-item>

          <el-form-item label="状态">
            <el-select v-model="filters.status" placeholder="选择状态" clearable style="width: 120px"
              @change="handleFilter">
              <el-option label="全部" value="" />
              <el-option label="启用" value="true" />
              <el-option label="禁用" value="false" />
            </el-select>
          </el-form-item>

          <el-form-item label="排序">
            <el-select v-model="filters.sortBy" style="width: 150px" @change="handleSort">
              <el-option label="创建时间" value="created_at" />
              <el-option label="更新时间" value="updated_at" />
              <el-option label="名称" value="name" />
            </el-select>
          </el-form-item>

          <el-form-item>
            <el-button @click="resetFilters">
              <el-icon>
                <RefreshLeft />
              </el-icon>
              重置
            </el-button>
          </el-form-item>
        </el-form>
      </el-card>
    </div>

    <!-- 资源包列表 -->
    <div class="packages-list">
      <el-card shadow="never">
        <template #header>
          <div class="card-header">
            <span>资源包列表</span>
            <div class="header-actions">
              <el-radio-group v-model="viewMode" size="small">
                <el-radio-button value="grid">
                  <el-icon>
                    <Grid />
                  </el-icon>
                </el-radio-button>
                <el-radio-button value="list">
                  <el-icon>
                    <List />
                  </el-icon>
                </el-radio-button>
              </el-radio-group>
            </div>
          </div>
        </template>

        <!-- 网格视图 -->
        <div v-if="viewMode === 'grid'" class="grid-view">
          <el-row :gutter="20">
            <el-col v-for="pkg in paginatedPackages" :key="pkg.id" :xs="24" :sm="12" :md="8" :lg="6">
              <div class="package-card">
                <div class="package-header">
                  <div class="package-type">
                    <el-icon class="type-icon">
                      <component :is="getTypeIcon(pkg.type)" />
                    </el-icon>
                  </div>
                  <div class="package-status">
                    <el-tag :type="getStatusType(pkg.is_active)" size="small">
                      {{ pkg.is_active ? '启用' : '禁用' }}
                    </el-tag>
                  </div>
                </div>

                <div class="package-content">
                  <h3 class="package-name">{{ pkg.name }}</h3>
                  <p class="package-description">{{ pkg.description || '暂无描述' }}</p>

                  <div class="package-meta">
                    <div class="meta-item">
                      <el-icon>
                        <Calendar />
                      </el-icon>
                      <span>{{ formatDate(pkg.created_at) }}</span>
                    </div>
                    <div class="meta-item">
                      <el-icon>
                        <Coin />
                      </el-icon>
                      <span>{{ getDatasourceName(pkg.datasource_id) }}</span>
                    </div>
                    <div class="meta-item">
                      <el-icon>
                        <Setting />
                      </el-icon>
                      <span>{{ pkg.template_type || '未知' }} 模板</span>
                    </div>
                  </div>

                  <div class="package-tags" v-if="pkg.tags && pkg.tags.length > 0">
                    <el-tag v-for="tag in pkg.tags.slice(0, 3)" :key="tag.id" size="small" class="tag-item"
                      :color="tag.tag_color">
                      {{ tag.tag_name }}
                    </el-tag>
                    <el-tag v-if="pkg.tags.length > 3" size="small" type="info" class="tag-item">
                      +{{ pkg.tags.length - 3 }}
                    </el-tag>
                  </div>

                  <!-- 模板预览 -->
                  <div class="package-preview" v-if="pkg.template_id">
                    <div class="preview-label">模板信息:</div>
                    <div class="preview-content">
                      <div class="condition-info">
                        <el-text type="primary" size="small">模板名称: {{ pkg.name }}</el-text>
                      </div>
                      <!-- <div class="condition-info" v-if="pkg.dynamic_params && Object.keys(pkg.dynamic_params).length > 0">
                        <el-text type="success" size="small">参数: {{ Object.keys(pkg.dynamic_params).length }}</el-text>
                      </div> -->
                    </div>
                  </div>
                </div>

                <div class="package-actions">
                  
                  <el-tooltip v-if="!pkg.is_active" content="资源包已禁用，无法查询" placement="top">
                    <span>
                      <el-button type="primary" size="small" @click="handleQuery(pkg)" :disabled="!pkg.is_active">
                        查询
                      </el-button>
                    </span>
                  </el-tooltip>
                  <el-button v-else type="primary" size="small" @click="handleQuery(pkg)">
                    查询
                  </el-button>
                  <el-button type="warning" size="small" @click="handleQuerySetting(pkg)">
                    查询设定
                  </el-button>
                  <el-button type="success" size="small" :loading="downloadLoading" @click="openDownloadDialog(pkg)">
                    下载资源包
                  </el-button>
                  <el-dropdown trigger="click">
                    
                    <el-button size="small" >
                      <el-icon>
                        <MoreFilled />
                      </el-icon>
                      更多
                    </el-button>
                    <template #dropdown>
                      <el-dropdown-menu>
                        <el-dropdown-item  @click="showApiEndpoint(pkg)">
                          <el-icon>
                            <Link />
                          </el-icon>
                          API
                        </el-dropdown-item>
                        <el-dropdown-item divided @click="handleEdit(pkg)">
                          <el-icon>
                            <Edit />
                          </el-icon>
                          编辑
                        </el-dropdown-item>
                        <el-dropdown-item divided @click="handleDelete(pkg)">
                          <el-icon>
                            <Delete />
                          </el-icon>
                          删除
                        </el-dropdown-item>
                      </el-dropdown-menu>
                    </template>
                  </el-dropdown>
                </div>
              </div>
            </el-col>
          </el-row>
        </div>

        <!-- 列表视图 -->
        <div v-else class="list-view">
          <el-table v-loading="loading" :data="paginatedPackages" style="width: 100%" border
            @header-dragend="handleColumnResize" @sort-change="handleTableSort">
            <el-table-column prop="name" column-key="name" label="资源包名称" :width="getColumnWidth('name', 200)" sortable>
              <template #default="{ row }">
                <div class="package-name-cell">
                  <div class="package-type-icon">
                    <el-icon>
                      <component :is="getTypeIcon(row.type)" />
                    </el-icon>
                  </div>
                  <div class="package-info">
                    <div class="name">
                      <el-link type="primary" @click="handleView(row)">
                        {{ row.name }}
                      </el-link>
                    </div>
                    <div class="description">{{ row.description || '暂无描述' }}</div>
                  </div>
                </div>
              </template>
            </el-table-column>

            <el-table-column prop="type" column-key="type" label="类型" :width="getColumnWidth('type', 120)">
              <template #default="{ row }">
                <el-tag :type="row.type === 'sql' ? 'primary' : 'success'">
                  {{ row.type === 'sql' ? 'SQL' : 'Elasticsearch' }}
                </el-tag>
              </template>
            </el-table-column>

            <el-table-column column-key="datasource" label="数据源" :width="getColumnWidth('datasource', 150)">
              <template #default="{ row }">
                {{ getDatasourceName(row.datasource_id) }}
              </template>
            </el-table-column>

            <el-table-column column-key="template" label="模板信息" :width="getColumnWidth('template', 120)">
              <template #default="{ row }">
                <div class="condition-info">
                  <div>
                    <el-text type="primary" size="small">{{ row.template_type || '未知' }}</el-text>
                  </div>
                  <div v-if="row.template_id">
                    <el-text type="info" size="small">ID: {{ row.template_id }}</el-text>
                  </div>
                </div>
              </template>
            </el-table-column>

            <el-table-column column-key="tags" label="标签" :width="getColumnWidth('tags', 200)">
              <template #default="{ row }">
                <div class="package-tags" v-if="row.tags && row.tags.length > 0">
                  <el-tag v-for="tag in row.tags.slice(0, 3)" :key="tag.id" size="small" :color="tag.tag_color"
                    style="margin-right: 4px; margin-top: 4px">
                    {{ tag.tag_name }}
                  </el-tag>
                  <el-tag v-if="row.tags.length > 3" size="small" type="info" style="margin-top: 4px">
                    +{{ row.tags.length - 3 }}
                  </el-tag>
                </div>
              </template>
            </el-table-column>

            <el-table-column prop="is_active" column-key="status" label="状态" :width="getColumnWidth('status', 80)">
              <template #default="{ row }">
                <el-tag :type="getStatusType(row.is_active)">
                  {{ row.is_active ? '启用' : '禁用' }}
                </el-tag>
              </template>
            </el-table-column>

            <el-table-column prop="created_at" column-key="created_at" label="创建时间"
              :width="getColumnWidth('created_at', 160)" sortable>
              <template #default="{ row }">
                {{ formatDate(row.created_at) }}
              </template>
            </el-table-column>

            <el-table-column column-key="actions" label="操作" :width="getColumnWidth('actions', 240)" fixed="right">
              <template #default="{ row }">
                <div class="action-buttons">
                  <el-button type="primary" size="small" @click="handleQuery(row)">
                    <el-icon>
                      <Search />
                    </el-icon>
                    查询
                  </el-button>
                  <el-button type="warning" size="small" @click="handleQuerySetting(row)">
                    <el-icon>
                      <Setting />
                    </el-icon>
                    查询设定
                  </el-button>
                  <el-button type="success" size="small" :loading="downloadLoading" @click="openDownloadDialog(row)">
                    下载资源包
                  </el-button>
                  <el-dropdown trigger="click">
                    <el-button size="small">
                      更多<el-icon class="el-icon--right">
                        <ArrowDown />
                      </el-icon>
                    </el-button>
                    <template #dropdown>
                      <el-dropdown-menu>
                        <el-dropdown-item @click="showApiEndpoint(row)">
                          <el-icon>
                            <View />
                          </el-icon>API
                        </el-dropdown-item>
                        <el-dropdown-item @click="handleEdit(row)">
                          <el-icon>
                            <Edit />
                          </el-icon>编辑
                        </el-dropdown-item>
                        <el-dropdown-item divided @click="handleDelete(row)" :disabled="row.is_lock === '1'">
                          <el-tooltip v-if="row.is_lock === '1'" content="该资源包已锁定，不可删除" placement="top">
                            <span>
                              <el-icon>
                                <Delete />
                              </el-icon>删除
                            </span>
                          </el-tooltip>
                          <span v-else>
                            <el-icon>
                              <Delete />
                            </el-icon>删除
                          </span>
                        </el-dropdown-item>
                      </el-dropdown-menu>
                    </template>
                  </el-dropdown>
                </div>
              </template>
            </el-table-column>
          </el-table>
        </div>

        <!-- 分页 -->
        <div class="pagination-wrapper">
          <el-pagination v-model:current-page="pagination.currentPage" v-model:page-size="pagination.pageSize"
            :page-sizes="[10, 20, 50, 100]" :total="pagination.total" layout="total, sizes, prev, pager, next, jumper"
            @size-change="handleSizeChange" @current-change="handleCurrentChange" />
        </div>
      </el-card>
    </div>

    <!-- 创建资源包 -->
    <ResourcePackageForm v-model:visible="createDialogVisible" :isEdit="false" @success="onCreateSuccess" />

    <!-- 编辑资源包基本信息 -->
    <ResourcePackageForm v-model:visible="editDialogVisible" :packageData="selectedPackage as any" :isEdit="true"
      @success="onEditSuccess" />

    <!-- 查询设定：根据资源包类型加载对应查询构建器 -->
    <el-drawer v-model="querySettingVisible" title="查询设定" size="80%">
      <!-- <p>test{{ initialSchema }}{{ initialTableName }}</p> -->
      <template v-if="querySettingPackage && querySettingPackage.type === 'sql'">
        <SQLQueryBuilder ref="sqlQueryBuilderRef" :sqlResources="sqlResources" :hasQueryPermission="hasQueryPermission"
          :hasExportPermission="hasExportPermission" :hasSavePermission="hasSavePermission"
          :initialDatasourceId="querySettingPackage.datasource_id"
          :initialResourceId="querySettingPackage.resource_id || null" :initialSchema="initialSchema"
          :initialTableName="initialTableName" :isInResourcePackage="true" :resourcePackageId="querySettingPackage.id"
          :resourcePackageName="querySettingPackage.name" @execute-query="onSQLQueryExecute"
          @save-query="onSQLQuerySave" @update-query="onSQLQueryUpdate" @export-results="onSQLResultsExport" />
      </template>
      <template v-else-if="querySettingPackage && querySettingPackage.type === 'elasticsearch'">
        <ESQueryBuilder ref="esQueryBuilderRef" :es-datasources="esDatasources"
          :initial-datasource-id="String(querySettingPackage.datasource_id)" :initial-indices="initialIndices"
          :data-resource-id="querySettingPackage.resource_id || null" :has-es-query-permission="hasESQueryPermission"
          :has-export-permission="hasExportPermission" :has-save-permission="hasSavePermission"
          :isInResourcePackage="true" :resourcePackageId="querySettingPackage.id"
          :resourcePackageName="querySettingPackage.name" @execute-query="onESQueryExecute" @save-query="onESQuerySave"
          @export-results="onESResultsExport" @datasources-loaded="onESDatasourcesLoaded" />
      </template>
    </el-drawer>

    <!-- API端点弹窗 -->
    <el-dialog v-model="apiDialogVisible" title="API端点" width="600px">
      <p>资源包接口：<code>{{ apiEndpoint }}</code></p>
      <div style="margin-top: 12px;">
        <el-button type="primary" @click="copyApiEndpoint">
          复制端点
        </el-button>
      </div>
      <template #footer>
        <el-button @click="apiDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 下载资源包弹窗 -->
    <el-dialog v-model="downloadDialogVisible" title="下载资源包" width="520px">
      <div class="download-info">
        <div class="info-row">
          <span class="label">最新生成时间：</span>
          <span class="value">{{ formatTime(downloadDialogData?.excel_time) || '暂无' }}</span>
        </div>
        <div class="info-row">
          <span class="label">最新下载时间：</span>
          <span class="value">{{ formatTime(downloadDialogData?.download_time) || '暂无' }}</span>
        </div>
        <!-- 历史文件选择 -->
        <div class="info-row">
          <span class="label">历史文件：</span>
          <el-select v-model="selectedFileId" placeholder="选择历史Excel" filterable style="width: 260px"
            :loading="historyLoading">
            <el-option v-for="f in historyFiles" :key="f.id" :label="formatHistoryLabel(f)" :value="f.id" />
          </el-select>
          <el-button size="small" type="success" :disabled="!selectedFileId" :loading="historyDownloadLoading"
            @click="handleDownloadHistory">下载资源包</el-button>
        </div>
      </div>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="downloadDialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="generateLoading" @click="handleGenerateExcel">
            生成资源包
          </el-button>
          <el-button type="success" :disabled="!downloadDialogData?.download_url" :loading="latestDownloadLoading"
            @click="handleDownloadLatest">
            下载最新资源包
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Box,
  Plus,
  Refresh,
  CircleCheck,
  Search,
  RefreshLeft,
  Grid,
  List,
  Calendar,
  Setting,
  ArrowDown,
  MoreFilled,
  Edit,
  CopyDocument,
  Download,
  Delete,
  View,
  Coin
} from '@element-plus/icons-vue'
import { resourcePackageApi, type ResourcePackage, type ResourcePackageSearchRequest, type ResourcePackageFile } from '@/api/resourcePackage'
import { dataResourceApi } from '@/api/dataResource'
import { templateApi } from '@/api/template'
import { saveSQLTemplate, updateSQLTemplate, executeSQLQuery } from '@/api/sqlQuery'
import { formatDate } from '@/utils/date'
import SQLQueryBuilder from '@/components/SQLQueryBuilder.vue'
import ESQueryBuilder from '@/components/ESQueryBuilder.vue'
import ResourcePackageForm from '@/views/resourcePackage/components/ResourcePackageForm.vue'

// 定义数据源接口
interface Datasource {
  id: number
  name: string
  type: string
  description?: string
  host: string
  port: number
  database?: string
  username: string
  is_active: boolean
  created_at: string
  updated_at: string
}

// 路由和用户状态管理
const router = useRouter()
const userStore = useUserStore()

// 响应式数据
const loading = ref(false)
const downloadLoading = ref(false)
const packageList = ref<ResourcePackage[]>([])
const datasources = ref<Datasource[]>([])
const esDatasources = ref([])
const currentDataResource = ref<any>(null)
const viewMode = ref('grid')
// SQL资源列表
const sqlResources = ref<any[]>([])

// 编辑对话框与查询设定抽屉、API端点
const editDialogVisible = ref(false)
const createDialogVisible = ref(false)
const selectedPackage = ref<ResourcePackage | null>(null)
const querySettingVisible = ref(false)
const querySettingPackage = ref<ResourcePackage | null>(null)
const apiDialogVisible = ref(false)
const apiEndpoint = ref('')

// 搜索和筛选
const filters = reactive({
  search: '',
  type: '',
  datasource_id: '',
  status: '',
  sortBy: 'created_at'
})

// 分页信息
const pagination = reactive({
  currentPage: 1,
  pageSize: 20,
  total: 0
})

// 统计数据
const stats = reactive({
  total: 0,
  active: 0,
  sqlCount: 0,
  elasticsearchCount: 0
})

// 计算属性
const getDatasourceName = computed(() => {
  return (datasourceId: number) => {
    const ds = datasources.value.find((d: Datasource) => d.id === datasourceId)
    return ds ? ds.name : '数据源'
  }
})

// 权限控制
const hasESQueryPermission = computed(() => {
  return userStore.hasPermission('data:elasticsearch:query') || userStore.hasRole('admin')
})

const hasExportPermission = computed(() => {
  return userStore.hasPermission('data:resource:export') || userStore.hasRole('admin')
})

const hasSavePermission = computed(() => {
  return userStore.hasPermission('data:resource:save') || userStore.hasRole('admin')
})

const hasQueryPermission = computed(() => {
  return userStore.hasPermission('data:resource:query') || userStore.hasRole('admin')
})

/**
 * 计算属性：获取初始索引列表
 * 从当前数据资源的详情中获取索引信息
 */
const initialIndices = computed(() => {
  if (!currentDataResource.value) {
    return []
  }

  // 如果数据资源有 indices 字段，直接返回
  if (currentDataResource.value.indices && Array.isArray(currentDataResource.value.indices)) {
    return currentDataResource.value.indices
  }

  // 如果数据资源有 table_name 或 index_name，返回对应的名称
  if (currentDataResource.value.table_name) {
    return [currentDataResource.value.table_name]
  }

  if (currentDataResource.value.index_name) {
    return [currentDataResource.value.index_name]
  }

  return []
})

// SQL 初始 Schema 与表名（从当前数据资源详情推断）
const initialSchema = computed(() => {
  const dr = currentDataResource.value as any
  // 兼容多种字段来源：schema_name（部分类型）、database_name（后端返回的数据库名）、connection_config.database（旧结构）
  return (
    (dr?.schema_name as string) ||
    (dr?.database_name as string) ||
    (dr?.connection_config?.database as string) ||
    ''
  )
})

const initialTableName = computed(() => {
  return (currentDataResource.value?.table_name as string) || (currentDataResource.value?.tableName as string) || ''
})

// 组件引用
const esQueryBuilderRef = ref(null)
const sqlQueryBuilderRef = ref(null)

// 列宽拖拽与持久化
const COLUMN_WIDTHS_STORAGE_KEY = 'resourcePackageTableColumnWidths'
const columnWidths = ref<Record<string, number>>({})

function loadColumnWidths() {
  try {
    const saved = localStorage.getItem(COLUMN_WIDTHS_STORAGE_KEY)
    if (saved) {
      const parsed = JSON.parse(saved)
      if (parsed && typeof parsed === 'object') {
        columnWidths.value = parsed
      }
    }
  } catch (e) {
    console.warn('加载列宽失败:', e)
  }
}

function saveColumnWidths() {
  try {
    localStorage.setItem(COLUMN_WIDTHS_STORAGE_KEY, JSON.stringify(columnWidths.value))
  } catch (e) {
    console.warn('保存列宽失败:', e)
  }
}

function getColumnWidth(key: string, defaultWidth: number) {
  const val = columnWidths.value[key]
  return typeof val === 'number' && val > 0 ? val : defaultWidth
}

function handleColumnResize(newWidth: number, oldWidth: number, column: any) {
  const key = column?.columnKey || column?.property || column?.label
  if (key) {
    columnWidths.value[key] = newWidth
    saveColumnWidths()
  }
}

onMounted(() => {
  loadColumnWidths()
  loadSQLResources()
})

/**
 * 过滤后的资源包列表
 */
const filteredPackages = computed(() => {
  let result = packageList.value

  // 搜索过滤
  if (filters.search) {
    const keyword = filters.search.toLowerCase()
    result = result.filter(pkg =>
      pkg.name.toLowerCase().includes(keyword) ||
      (pkg.description && pkg.description.toLowerCase().includes(keyword))
    )
  }

  // 类型过滤
  if (filters.type) {
    result = result.filter(pkg => pkg.type === filters.type)
  }

  // 数据源过滤
  if (filters.datasource_id) {
    result = result.filter(pkg => pkg.datasource_id === Number(filters.datasource_id))
  }

  // 状态过滤
  if (filters.status) {
    const isActive = filters.status === 'true'
    result = result.filter(pkg => pkg.is_active === isActive)
  }

  // 排序
  result.sort((a, b) => {
    const field = filters.sortBy as keyof ResourcePackage
    const aValue = a[field]
    const bValue = b[field]

    if (typeof aValue === 'string' && typeof bValue === 'string') {
      return bValue.localeCompare(aValue) // 降序
    }

    return 0
  })

  return result
})

/**
 * 分页后的资源包列表
 */
const paginatedPackages = computed(() => {
  const start = (pagination.currentPage - 1) * pagination.pageSize
  const end = start + pagination.pageSize
  return filteredPackages.value.slice(start, end)
})

// 方法

/**
 * 获取类型图标
 */
const getTypeIcon = (type: string) => {
  return type === 'sql' ? Coin : Search
}

/**
 * 获取状态类型
 */
const getStatusType = (isActive: boolean): 'success' | 'danger' => {
  return isActive ? 'success' : 'danger'
}

/**
 * 加载资源包列表
 */
const loadPackages = async () => {
  try {
    loading.value = true

    const searchParams: ResourcePackageSearchRequest = {
      keyword: filters.search || undefined,
      type: filters.type as any || undefined,
      datasource_id: filters.datasource_id ? Number(filters.datasource_id) : undefined,
      is_active: filters.status ? filters.status === 'true' : undefined,
      page: pagination.currentPage,
      size: Math.min(pagination.pageSize, 100), // 后端限制最大为100
      sort_by: 'created_at',
      sort_order: 'desc'
    }

    const res = await resourcePackageApi.search(searchParams)
    console.log('搜索资源包响应:', res)
    packageList.value = res.data?.items || []
    pagination.total = res.data?.total || 0 // 更新总数

    // 更新统计数据
    updateStats()

  } catch (error) {
    console.error('加载资源包列表失败:', error)
    ElMessage.error('加载资源包列表失败')
  } finally {
    loading.value = false
  }
}

// 复制API端点
const copyApiEndpoint = async () => {
  try {
    await navigator.clipboard.writeText(apiEndpoint.value)
    ElMessage.success('已复制API端点')
  } catch (e) {
    ElMessage.error('复制失败')
  }
}

// 查看详情（当前行为：打开编辑弹窗）
const handleView = (row: ResourcePackage) => {
  handleEdit(row)
}

/**
 * 加载数据源列表
 */
const loadDatasources = async () => {
  try {
    // 模拟数据源API调用
    // const response = await datasourceApi.getDataSourceList()
    // datasources.value = response.data?.items || []

    // 临时使用模拟数据
    datasources.value = [
      { id: 1, name: 'MySQL主库', type: 'mysql', host: 'localhost', port: 3306, username: 'root', is_active: true, created_at: '2024-01-01', updated_at: '2024-01-01' },
      { id: 2, name: 'Elasticsearch集群', type: 'elasticsearch', host: 'localhost', port: 9200, username: 'elastic', is_active: true, created_at: '2024-01-01', updated_at: '2024-01-01' }
    ]
  } catch (error) {
    console.error('加载数据源列表失败:', error)
  }
}

/**
 * 加载可用于SQL查询的数据资源列表
 */
const loadSQLResources = async () => {
  try {
    const response: any = await dataResourceApi.getResourceList({ page: 1, page_size: 1000 })
    // 兼容不同返回结构
    const items = response?.data?.items || response?.items || response?.data?.list || []
    sqlResources.value = items
  } catch (error) {
    console.error('加载数据资源失败:', error)
    ElMessage.error('加载数据资源失败')
  }
}

/**
 * 更新统计数据
 */
const updateStats = () => {
  // 总数使用后端返回的 total（全量数据总数）
  stats.total = pagination.total
  stats.active = packageList.value.filter(pkg => pkg.is_active).length
  stats.sqlCount = packageList.value.filter(pkg => pkg.type === 'sql').length
  stats.elasticsearchCount = packageList.value.filter(pkg => pkg.type === 'elasticsearch').length
}

/**
 * 刷新资源包列表
 */
const refreshPackages = () => {
  loadPackages()
}

/**
 * 搜索处理
 */
const handleSearch = () => {
  pagination.currentPage = 1
  loadPackages() // 重新加载数据
}

/**
 * 筛选处理
 */
const handleFilter = () => {
  pagination.currentPage = 1
  loadPackages() // 重新加载数据
}

/**
 * 排序处理
 */
const handleSort = () => {
  pagination.currentPage = 1
  loadPackages() // 重新加载数据
}

/**
 * 重置筛选条件
 */
const resetFilters = () => {
  Object.assign(filters, {
    search: '',
    type: '',
    datasource_id: '',
    status: '',
    sortBy: 'created_at'
  })
  pagination.currentPage = 1
  loadPackages() // 重新加载数据
}

/**
 * 表格排序处理
 */
const handleTableSort = ({ prop, order }: { prop: string; order: string }) => {
  filters.sortBy = prop
  // 这里可以根据 order 调整排序方向
}

/**
 * 创建资源包
 */
const handleCreate = () => {
  createDialogVisible.value = true
}

/**
 * 编辑资源包 - 跳转到数据查询页面
 */
const handleEdit = (row: ResourcePackage) => {
  selectedPackage.value = row
  editDialogVisible.value = true
}

/**
 * 查询设定（打开查询构建器）
 */
const handleQuerySetting = async (row: ResourcePackage) => {
  querySettingPackage.value = row

  // 如果资源包有关联的数据资源ID，获取数据资源详情
  if (row.resource_id) {
    await fetchDataResourceDetail(row.resource_id)
  }

  querySettingVisible.value = true
}

/**
 * 查看资源包详情
 */
const buildApiEndpoint = (row: ResourcePackage) => `/api/v1/resource-packages/${row.id}`

const showApiEndpoint = (row: ResourcePackage) => {
  apiEndpoint.value = buildApiEndpoint(row)
  apiDialogVisible.value = true
}

// 下载相关状态与方法
const downloadDialogVisible = ref(false)
const downloadPackage = ref<ResourcePackage | null>(null)
const downloadDialogData = ref<{ excel_time?: string; download_time?: string; download_url?: string } | null>(null)
const historyFiles = ref<ResourcePackageFile[]>([])
const selectedFileId = ref<number | null>(null)
const historyLoading = ref(false)
const latestDownloadLoading = ref(false)
const historyDownloadLoading = ref(false)
const generateLoading = ref(false)
// 下载弹窗的模板兜底数据：ES模板的_source与indices
const downloadTemplateSourceFields = ref<string[]>([])
const downloadTemplateIndices = ref<string[]>([])

function formatTime(time?: string) {
  if (!time) return '-'
  const d = new Date(time)
  if (isNaN(d.getTime())) return time
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}:${String(d.getSeconds()).padStart(2, '0')}`
}

function formatHistoryLabel(f: ResourcePackageFile): string {
  const t = f.generated_at ? new Date(f.generated_at).toLocaleString() : ''
  return `${f.filename} (${t})`
}

/**
 * 生成资源包Excel
 */
async function handleGenerateExcel() {
  if (!downloadPackage.value?.id) {
    ElMessage.error('缺少资源包ID')
    return
  }

  try {
    generateLoading.value = true
    // 调用生成Excel的API，构造与查询页一致的payload
    let payload: Record<string, any> = {}

    if (downloadPackage.value?.type === 'elasticsearch') {
      // 优先从查询构建器获取当前选择的索引与DSL
      let indices: string[] = []
      let builtQuery: any = null
      try {
        // 依赖 ESQueryBuilder 暴露的方法
        if (esQueryBuilderRef.value && typeof esQueryBuilderRef.value.getSelectedIndices === 'function') {
          indices = esQueryBuilderRef.value.getSelectedIndices()
        }
        if (esQueryBuilderRef.value && typeof esQueryBuilderRef.value.getQuery === 'function') {
          builtQuery = esQueryBuilderRef.value.getQuery()
        }
      } catch (e) {
        console.warn('从查询构建器获取索引或DSL失败，尝试使用数据资源索引兜底:', e)
      }

      // 索引兜底优先顺序：模板indices -> 数据资源indices
      if ((!indices || indices.length === 0) && downloadTemplateIndices.value && downloadTemplateIndices.value.length > 0) {
        indices = downloadTemplateIndices.value
      }
      if ((!indices || indices.length === 0) && initialIndices.value && initialIndices.value.length > 0) {
        indices = initialIndices.value as string[]
      }

      if (!indices || indices.length === 0) {
        ElMessage.error('缺少索引信息，无法生成Excel，请先在查询设定中选择索引')
        return
      }

      // 构造与查询页一致的 payload 结构
      const queryPart = builtQuery && builtQuery.query ? builtQuery.query : { match_all: {} }
      payload = { index: indices, query: queryPart }
      // 字段导出优先顺序：查询设定的_source -> 模板_source
      if (builtQuery && builtQuery._source) {
        payload._source = builtQuery._source
      } else if (downloadTemplateSourceFields.value && downloadTemplateSourceFields.value.length > 0) {
        payload._source = downloadTemplateSourceFields.value
      }
    }

    const resp = await resourcePackageApi.generateExcel(downloadPackage.value.id, payload)

    if (resp?.success) {
      const hasNew = resp?.data?.has_new_data
      if (hasNew === false) {
        ElMessage.warning(resp?.message || '无最新数据，无需生成')
      } else {
        // 更新弹窗中的下载链接
        const data = resp.data || {}
        if (data.download_url && downloadDialogData.value) {
          downloadDialogData.value.download_url = data.download_url
        }
        // 仅在有新数据时刷新弹窗时间为本地当前时间
        if (downloadDialogData.value) {
          downloadDialogData.value.excel_time = new Date().toISOString()
        }
        ElMessage.success('Excel文件生成成功')
      }
    } else {
      ElMessage.error(resp?.message || '生成Excel失败，请稍后重试')
    }
  } catch (e: any) {
    console.error('生成Excel失败:', e)
    ElMessage.error(e?.message || '生成Excel失败，请稍后重试')
  } finally {
    generateLoading.value = false
  }
}

function openDownloadDialog(pkg: ResourcePackage) {
  downloadPackage.value = pkg
  downloadDialogVisible.value = true
  downloadDialogData.value = {
    excel_time: pkg.excel_time,
    download_time: pkg.download_time,
    download_url: pkg.download_url,
  }
  selectedFileId.value = null
  // 预加载数据资源详情，以便 initialIndices 兜底
  if (pkg.resource_id) {
    fetchDataResourceDetail(pkg.resource_id).catch(err => {
      console.warn('预加载数据资源详情失败:', err)
    })
  }
  // 清空模板兜底数据并在ES类型时预加载模板详情（_source与indices）
  downloadTemplateSourceFields.value = []
  downloadTemplateIndices.value = []
  if (pkg.type === 'elasticsearch' && pkg.template_id) {
    templateApi.getByType(pkg.template_id, 'es')
      .then((resp: any) => {
        const detail = resp?.data || resp
        const idx = detail?.indices || detail?.config?.indices || []
        if (Array.isArray(idx)) {
          downloadTemplateIndices.value = idx
        }
        let q = detail?.query || detail?.query_content || null
        try {
          if (q && typeof q === 'string') {
            q = JSON.parse(q)
          }
        } catch (e) {
          console.warn('解析模板query_content失败，按原值处理:', e)
        }
        if (q && Array.isArray(q._source)) {
          downloadTemplateSourceFields.value = q._source
        }
      })
      .catch(err => {
        console.warn('预加载ES模板详情失败:', err)
      })
  }
  fetchHistoryFiles(pkg.id)
}

async function fetchHistoryFiles(packageId: number) {
  try {
    historyLoading.value = true
    const resp = await resourcePackageApi.listFiles(packageId, 1, 50)
    if (resp.success) {
      historyFiles.value = resp.data?.items || []
    } else {
      historyFiles.value = []
    }
  } catch (err) {
    console.warn('加载历史文件失败:', err)
    historyFiles.value = []
  } finally {
    historyLoading.value = false
  }
}

async function handleDownloadLatest() {
  try {
    if (!downloadPackage.value) return
    if (!downloadDialogData.value?.download_url) {
      ElMessage.error('暂无可下载的最新资源包，请先生成Excel')
      return
    }
    latestDownloadLoading.value = true
    const resp = await resourcePackageApi.downloadLatest(downloadPackage.value.id)
    if (!resp.success) {
      throw new Error(resp.message || '下载失败')
    }
    const url = resp.data?.download_url || downloadDialogData.value?.download_url
    const filename = resp.data?.filename || ''
    if (url) {
      const newWin = window.open(url, '_blank')
      if (!newWin) {
        try {
          const link = document.createElement('a')
          link.href = url
          link.download = filename
          document.body.appendChild(link)
          link.click()
          document.body.removeChild(link)
        } catch (e) {
          console.warn('下载链接触发失败，已尝试回退方案:', e)
        }
      }
      if (resp.data?.download_time) downloadDialogData.value!.download_time = resp.data.download_time
      downloadDialogData.value!.download_time = new Date().toISOString()
      ElMessage.success('正在下载最新资源包...')
    } else {
      ElMessage.error('未返回下载链接')
    }
  } catch (e: any) {
    console.error('下载最新资源包失败:', e)
    ElMessage.error(e.message || '下载失败，请稍后重试')
  } finally {
    latestDownloadLoading.value = false
  }
}

async function handleDownloadHistory() {
  try {
    if (!downloadPackage.value || !selectedFileId.value) {
      ElMessage.error('请选择需要下载的历史文件')
      return
    }
    historyDownloadLoading.value = true
    const resp = await resourcePackageApi.downloadFile(downloadPackage.value.id, selectedFileId.value)
    if (!resp.success) {
      throw new Error(resp.message || '下载失败')
    }
    const url = resp.data?.download_url
    const filename = resp.data?.filename || ''
    if (url) {
      const newWin = window.open(url, '_blank')
      if (!newWin) {
        try {
          const link = document.createElement('a')
          link.href = url
          link.download = filename
          document.body.appendChild(link)
          link.click()
          document.body.removeChild(link)
        } catch (e) {
          console.warn('下载链接触发失败，已尝试回退方案:', e)
        }
      }
      ElMessage.success('正在下载历史文件...')
    } else {
      ElMessage.error('未返回下载链接')
    }
  } catch (e: any) {
    console.error('下载历史文件失败:', e)
    ElMessage.error(e.message || '下载失败，请稍后重试')
  } finally {
    historyDownloadLoading.value = false
  }
}

/**
 * 跳转到资源包查询页面
 */
const handleQuery = (row: ResourcePackage) => {
  router.push(`/data-resources/packages/${row.id}/query`)
}

/**
 * 克隆资源包
 */
const handleClone = (row: ResourcePackage) => {
  ElMessage.info('克隆功能开发中...')
}

/**
 * 删除资源包
 */
const handleDelete = async (row: ResourcePackage) => {
  // 检查资源包是否被锁定
  if (row.is_lock === '1') {
    ElMessage.warning('该资源包已锁定，不可删除')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确定要删除资源包 “${row.name}” 吗？`,
      '确认删除',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await resourcePackageApi.delete(row.id)
    ElMessage.success('删除成功')
    loadPackages()
  } catch (error) {
    // 取消会抛出错误（通常为 'cancel'），不提示为失败
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

/**
 * 分页大小变化处理
 */
const handleSizeChange = (size: number) => {
  pagination.pageSize = size
  pagination.currentPage = 1
  loadPackages() // 重新加载数据
}

/**
 * 当前页变化处理
 */
const handleCurrentChange = (page: number) => {
  pagination.currentPage = page
  loadPackages() // 重新加载数据
}

/**
 * 获取数据资源详情
 * @param resourceId 数据资源ID
 */
const fetchDataResourceDetail = async (resourceId: number) => {
  try {
    const response = await dataResourceApi.getResourceDetail(resourceId)
    if (response.success && response.data) {
      currentDataResource.value = response.data
      return response.data
    }
  } catch (error) {
    console.error('获取数据资源详情失败:', error)
    ElMessage.error('获取数据资源详情失败')
  }
  return null
}

/**
 * ES查询执行处理
 */
const onESQueryExecute = (queryData) => {
  console.log('执行ES查询:', queryData)
}

/**
 * SQL 查询模板保存
 */
const onSQLQuerySave = async (queryData: any) => {
  try {
    const templateData = {
      name: queryData.name,
      description: queryData.description,
      datasourceId: queryData.datasourceId || querySettingPackage.value?.datasource_id,
      dataResourceId: queryData.queryConfig?.resourceId ? parseInt(queryData.queryConfig.resourceId) : (querySettingPackage.value?.resource_id || null),
      query: queryData.sql,
      tags: queryData.tags || [],
      config: queryData.config || {},
      isTemplate: true
    }

    const response: any = await saveSQLTemplate(templateData as any)

    if (response && response.data && response.data.id && sqlQueryBuilderRef.value) {
      const templateId = response.data.id
      sqlQueryBuilderRef.value.setCurrentTemplateId(templateId)
    }

    ElMessage.success('SQL查询模板保存成功')
  } catch (error) {
    console.error('保存SQL查询模板失败:', error)
    ElMessage.error('保存SQL查询模板失败')
  }
}

/**
 * SQL 查询模板更新
 */
const onSQLQueryUpdate = async (queryData: any) => {
  try {
    const templateData = {
      name: queryData.name,
      description: queryData.description,
      datasourceId: queryData.datasourceId || querySettingPackage.value?.datasource_id,
      dataResourceId: queryData.queryConfig?.resourceId ? parseInt(queryData.queryConfig.resourceId) : (querySettingPackage.value?.resource_id || null),
      query: queryData.sql,
      tags: queryData.tags || [],
      config: queryData.config || {},
      isTemplate: true
    }

    await updateSQLTemplate(queryData.id, templateData as any)

    ElMessage.success('SQL查询模板更新成功')
  } catch (error) {
    console.error('更新SQL查询模板失败:', error)
    ElMessage.error('更新SQL查询模板失败')
  }
}

/**
 * 执行 SQL 查询
 */
const onSQLQueryExecute = async (queryData: any) => {
  try {
    if (!queryData.datasourceId) {
      ElMessage.error('缺少数据源ID')
      return
    }
    if (!queryData.sql) {
      ElMessage.error('缺少SQL查询语句')
      return
    }

    const queryRequest = {
      datasourceId: queryData.datasourceId,
      query: queryData.sql,
      limit: queryData.limit || 1000,
      offset: queryData.offset || 0
    }

    const response: any = await executeSQLQuery(queryRequest as any)

    if (response && response.success) {
      const { columns, data, row_count } = response
      if (columns && data) {
        const resultColumns = columns.map((col: string) => ({
          prop: col,
          label: col,
          type: 'string',
          width: 150
        }))
        const resultData = data.map((row: any[]) => {
          const obj: Record<string, any> = {}
          columns.forEach((col: string, index: number) => { obj[col] = row[index] })
          return obj
        })
        if (sqlQueryBuilderRef.value) {
          sqlQueryBuilderRef.value.setQueryResults(resultData, resultColumns)
        }
        ElMessage.success(`查询执行成功，返回 ${row_count} 条记录`)
      } else {
        if (sqlQueryBuilderRef.value) {
          sqlQueryBuilderRef.value.setQueryResults([], [])
        }
        ElMessage.info('查询成功但无数据返回')
      }
    } else {
      const errorMessage = response?.error_details || response?.message || '查询执行失败'
      if (sqlQueryBuilderRef.value) {
        sqlQueryBuilderRef.value.handleQueryError(new Error(errorMessage))
      }
      ElMessage.error(`查询执行失败: ${errorMessage}`)
    }
  } catch (error: any) {
    if (sqlQueryBuilderRef.value) {
      sqlQueryBuilderRef.value.handleQueryError(error)
    }
    const errorMessage = error.response?.data?.detail || error.message || '查询执行失败'
    ElMessage.error(`查询执行失败: ${errorMessage}`)
  }
}

const onSQLResultsExport = (results: any) => {
  console.log('导出SQL查询结果:', results)
}

/**
 * ES查询保存处理
 */
const onESQuerySave = (queryData) => {
  console.log('保存ES查询:', queryData)
}

/**
 * ES查询结果导出处理
 */
const onESResultsExport = (results) => {
  console.log('导出ES查询结果:', results)
}

/**
 * ES数据源加载完成处理
 */
const onESDatasourcesLoaded = (datasources) => {
  esDatasources.value = datasources
  console.log('ES数据源加载完成:', datasources)
}

// 生命周期
onMounted(() => {
  loadDatasources()
  loadPackages()
  loadSQLResources()
})

/** 创建成功后刷新列表 */
const onCreateSuccess = () => {
  createDialogVisible.value = false
  loadPackages()
}

/** 编辑成功后刷新列表 */
const onEditSuccess = () => {
  editDialogVisible.value = false
  loadPackages()
}
</script>

<style scoped lang="scss">
.resource-package-page {
  padding: 20px;
  background-color: var(--el-bg-color-page);
  min-height: 100vh;
}

/* 页面头部 */
.page-header {
  margin-bottom: 20px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.header-left {
  flex: 1;
}

.page-title {
  margin: 0 0 8px 0;
  color: #303133;
  font-size: 24px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 12px;
}

.page-description {
  /* flex中靠下 */
  align-self: flex-end;
  margin: 0;
  color: #606266;
  font-size: 14px;
  font-weight: 400;
}

.header-right {
  display: flex;
  gap: 12px;
}

/* 统计卡片 */
.stats-cards {
  margin-bottom: 20px;
}

.stat-card {
  background: white;
  border-radius: 10px;
  padding: 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
  border: 1px solid #ebeef5;
  display: flex;
  align-items: center;
  gap: 16px;
  transition: all 0.3s ease;
}

.stat-card:hover {
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  transform: translateY(-2px);
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: white;
}

.stat-icon.total {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.stat-icon.active {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.stat-icon.sql {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.stat-icon.elasticsearch {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
  color: #303133;
  line-height: 1;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  font-weight: 500;
}

/* 筛选区域 */
.filter-section {
  margin-bottom: 20px;
}

/* 资源包列表 */
.packages-list {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
  color: #303133;
}

.header-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

/* 网格视图 */
.grid-view {
  margin-top: 20px;
}

.package-card {
  background: white;
  border-radius: 10px;
  border: 1px solid #ebeef5;
  overflow: hidden;
  transition: all 0.3s ease;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.package-card:hover {
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
  transform: translateY(-4px);
  border-color: #409eff;
}

.package-header {
  padding: 16px 20px 0;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.package-type {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 18px;
}

.package-content {
  padding: 16px 20px;
  flex: 1;
  display: flex;
  flex-direction: column;
}

.package-name {
  margin: 0 0 8px 0;
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.package-description {
  margin: 0 0 16px 0;
  color: #606266;
  font-size: 14px;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  flex: 1;
}

.package-meta {
  margin-bottom: 16px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 8px;
  font-size: 13px;
  color: #909399;
}

.meta-item:last-child {
  margin-bottom: 0;
}

.package-tags {
  margin-bottom: 16px;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.tag-item {
  border: none;
  font-size: 12px;
}

.package-preview {
  margin-bottom: 16px;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

.preview-label {
  font-size: 12px;
  color: #6c757d;
  margin-bottom: 8px;
  font-weight: 500;
}

.preview-content {
  display: flex;
  gap: 12px;
}

.condition-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.package-actions {
  padding: 0 20px 20px;
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: center;

  .el-button+.el-button {
    margin-left: 0;
  }
}

/* 列表视图 */
.list-view {
  margin-top: 20px;
}

.package-name-cell {
  display: flex;
  align-items: center;
  gap: 12px;
}

.package-type-icon {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 14px;
}

.package-info {
  flex: 1;
}

.package-info .name {
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}

.package-info .description {
  font-size: 13px;
  color: #909399;
  line-height: 1.4;
}

.action-buttons {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: nowrap;
}

.action-buttons .el-button {
  margin: 0;
}

/* 分页 */
.pagination-wrapper {
  margin-top: 24px;
  display: flex;
  justify-content: center;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .resource-package-page {
    padding: 16px;
  }

  .header-content {
    flex-direction: column;
    gap: 16px;
  }

  .header-right {
    width: 100%;
    justify-content: flex-start;
  }

  .page-title {
    font-size: 24px;
  }

  .stat-card {
    padding: 16px;
  }

  .stat-value {
    font-size: 24px;
  }
}

/* Element Plus 样式覆盖 */
:deep(.el-card) {
  border-radius: 10px;
}

:deep(.el-card__body) {
  padding: 24px;
}

:deep(.el-form--inline .el-form-item) {
  margin-right: 16px;
  margin-bottom: 16px;
}

:deep(.el-table .el-table__cell) {
  padding: 12px 0;
}

:deep(.el-tag) {
  border: none;
  font-weight: 500;
}

:deep(.el-button--small) {
  padding: 6px 12px;
  font-size: 12px;
}

:deep(.el-radio-group .el-radio-button__inner) {
  padding: 8px 12px;
}

/* 下载弹窗样式与查询面板保持一致 */
.download-info {
  margin: 8px 0 4px;
}

.info-row {
  display: flex;
  margin-bottom: 6px;
  align-items: center;
}

.info-row .label {
  color: #606266;
  width: 220px;
}

.info-row .value {
  color: #303133;
}
</style>