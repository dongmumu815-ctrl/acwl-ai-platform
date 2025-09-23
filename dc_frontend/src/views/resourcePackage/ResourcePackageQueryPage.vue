<template>
  <div class="resource-package-query-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="header-left">
        <el-button @click="goBack" type="text" class="back-button">
          <el-icon><ArrowLeft /></el-icon>
          返回列表
        </el-button>
        <div class="title-section">
          <h2>{{ packageData?.name || '资源包查询' }}</h2>
          <p class="page-description">{{ packageData?.description || '执行资源包查询操作' }}</p>
        </div>
      </div>
      <div class="header-right">
        <el-tag :type="packageData?.type === 'sql' ? 'primary' : 'success'" size="large">
          {{ packageData?.type === 'sql' ? 'SQL查询' : 'Elasticsearch' }}
        </el-tag>
      </div>
    </div>

    <div v-loading="loading" class="page-content">
      <!-- 资源包信息卡片 -->
      <el-card class="package-info-card" v-if="packageData">
        <template #header>
          <div class="card-header">
            <span class="card-title">资源包信息</span>
            <div class="package-tags">
              <el-tag 
                v-for="tag in packageData.tags" 
                :key="tag.tag_name" 
                :color="tag.tag_color"
                class="tag-item"
              >
                {{ tag.tag_name }}
              </el-tag>
            </div>
          </div>
        </template>
        
        <!-- 锁定条件展示 -->
        <div v-if="packageData.locked_conditions?.length" class="locked-conditions">
          <h4>锁定条件</h4>
          <div class="condition-list">
            <el-tag
              v-for="(condition, index) in packageData.locked_conditions"
              :key="index"
              type="warning"
              class="condition-tag"
            >
              {{ condition.field }} {{ condition.operator }} {{ condition.value }}
            </el-tag>
          </div>
        </div>

        <!-- 基础配置信息 -->
        <div v-if="packageData.base_config" class="base-config">
          <h4>查询配置</h4>
          <div class="config-info">
            <el-descriptions :column="2" size="small">
              <el-descriptions-item label="数据源">{{ getDatasourceName(packageData.datasource_id) }}</el-descriptions-item>
              <el-descriptions-item label="查询类型">{{ packageData.type.toUpperCase() }}</el-descriptions-item>
              <el-descriptions-item label="数据表" v-if="packageData.base_config.table">
                {{ packageData.base_config.schema }}.{{ packageData.base_config.table }}
              </el-descriptions-item>
              <el-descriptions-item label="查询字段">
                {{ packageData.base_config.fields?.join(', ') || '全部字段' }}
              </el-descriptions-item>
            </el-descriptions>
          </div>
        </div>
      </el-card>

      <!-- 调试信息 -->
      <el-card class="debug-info-card" v-if="packageData" style="margin-bottom: 20px; border: 2px dashed #409eff;">
        <template #header>
          <span class="card-title" style="color: #409eff;">🐛 调试信息</span>
        </template>
        <div style="font-family: monospace; font-size: 12px;">
          <p><strong>资源包ID:</strong> {{ route.params.id }}</p>
          <p><strong>资源包数据:</strong> {{ packageData ? '已加载' : '未加载' }}</p>
          <p><strong>动态条件数组:</strong> {{ packageData?.dynamic_conditions ? `存在 (${packageData.dynamic_conditions.length} 个)` : '不存在' }}</p>
          <p><strong>动态条件长度:</strong> {{ packageData?.dynamic_conditions?.length || 0 }}</p>
          <p><strong>渲染条件:</strong> {{ packageData?.dynamic_conditions?.length ? '满足' : '不满足' }}</p>
          <div v-if="packageData?.dynamic_conditions?.length">
            <p><strong>条件详情:</strong></p>
            <ul style="margin: 0; padding-left: 20px;">
              <li v-for="(condition, index) in packageData.dynamic_conditions" :key="index" style="margin: 5px 0;">
                条件{{ index + 1 }}: param_name="{{ condition.param_name }}", field="{{ condition.field }}", operator="{{ condition.operator }}"
              </li>
            </ul>
          </div>
        </div>
      </el-card>

      <!-- 查询条件表单 -->
      <el-card class="query-form-card" v-if="packageData?.dynamic_conditions?.length">
        <template #header>
          <span class="card-title">查询条件</span>
        </template>
        
        <el-form
          ref="queryFormRef"
          :model="queryForm"
          :rules="queryRules"
          label-width="120px"
          class="query-form"
        >
          <el-row :gutter="20">
            <el-col
              v-for="condition in packageData.dynamic_conditions"
              :key="condition.param_name"
              :span="12"
            >
              <el-form-item
                :label="condition.description || condition.field"
                :prop="condition.param_name"
                :required="condition.required"
              >
                <!-- 不同操作符的输入组件 -->
                <template v-if="['IN', 'NOT IN'].includes(condition.operator)">
                  <el-select
                    v-model="queryForm[condition.param_name]"
                    multiple
                    filterable
                    allow-create
                    :placeholder="getPlaceholder(condition)"
                    style="width: 100%"
                  >
                    <el-option
                      v-for="option in getFieldOptions(condition.field)"
                      :key="option"
                      :label="option"
                      :value="option"
                    />
                  </el-select>
                </template>
                <template v-else-if="condition.operator === 'LIKE'">
                  <el-input
                    v-model="queryForm[condition.param_name]"
                    :placeholder="getPlaceholder(condition)"
                    prefix-icon="Search"
                  />
                </template>
                <template v-else-if="['>', '>=', '<', '<='].includes(condition.operator)">
                  <el-input-number
                    v-model="queryForm[condition.param_name]"
                    :placeholder="getPlaceholder(condition)"
                    style="width: 100%"
                  />
                </template>
                <template v-else>
                  <el-input
                    v-model="queryForm[condition.param_name]"
                    :placeholder="getPlaceholder(condition)"
                  />
                </template>
                
                <div class="condition-info">
                  <el-text size="small" type="info">
                    {{ condition.field }} {{ condition.operator }}
                    <span v-if="condition.default_value">（默认: {{ condition.default_value }}）</span>
                  </el-text>
                </div>
              </el-form-item>
            </el-col>
          </el-row>
        </el-form>
      </el-card>

      <!-- 查询选项 -->
      <el-card class="query-options-card">
        <template #header>
          <div class="card-header">
            <span class="card-title">查询选项</span>
            <div class="query-actions">
              <el-button @click="resetForm">重置</el-button>
              <el-button type="primary" @click="executeQuery" :loading="queryLoading">
                <el-icon><Search /></el-icon>
                执行查询
              </el-button>
            </div>
          </div>
        </template>
        
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="排序字段">
              <el-select v-model="queryOptions.orderField" placeholder="选择排序字段" clearable>
                <el-option
                  v-for="field in packageData?.base_config?.fields"
                  :key="field"
                  :label="field"
                  :value="field"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="排序方向">
              <el-select v-model="queryOptions.orderDirection" placeholder="选择排序方向">
                <el-option label="升序" value="ASC" />
                <el-option label="降序" value="DESC" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="查询条数">
              <el-input-number
                v-model="queryOptions.limit"
                :min="1"
                :max="10000"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>
      </el-card>

      <!-- 查询结果 -->
      <el-card class="query-results-card" v-if="queryResults">
        <template #header>
          <div class="results-header">
            <span class="card-title">查询结果</span>
            <div class="results-meta">
              <el-text type="info">
                共 {{ queryResults.total_count || 0 }} 条记录，
                耗时 {{ queryResults.execution_time }}ms
              </el-text>
              <el-button 
                type="primary" 
                size="small" 
                @click="exportResults" 
                :disabled="!queryResults.data?.length"
              >
                <el-icon><Download /></el-icon>
                导出结果
              </el-button>
            </div>
          </div>
        </template>
        
        <div v-if="queryResults.data?.length">
          <!-- 数据表格 -->
          <el-table
            :data="paginatedData"
            stripe
            border
            max-height="500"
            style="width: 100%"
          >
            <el-table-column
              v-for="field in displayFields"
              :key="field"
              :prop="field"
              :label="field"
              :min-width="120"
              show-overflow-tooltip
            >
              <template #default="{ row }">
                <span v-if="typeof row[field] === 'object'">{{ JSON.stringify(row[field]) }}</span>
                <span v-else>{{ row[field] }}</span>
              </template>
            </el-table-column>
          </el-table>
          
          <!-- 分页 -->
          <div class="pagination-wrapper">
            <el-pagination
              v-model:current-page="currentPage"
              v-model:page-size="pageSize"
              :page-sizes="[10, 20, 50, 100]"
              :total="queryResults.total_count || 0"
              layout="total, sizes, prev, pager, next, jumper"
              @size-change="handleSizeChange"
              @current-change="handleCurrentChange"
            />
          </div>
        </div>
        
        <div v-else class="no-data">
          <el-empty description="暂无查询结果" />
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { ArrowLeft, Search, Download } from '@element-plus/icons-vue'
import * as XLSX from 'xlsx'
import { 
  resourcePackageApi, 
  type ResourcePackage, 
  type ResourcePackageQueryRequest,
  type ResourcePackageQueryResponse 
} from '@/api/resourcePackage'
import { datasourceApi, type DataSource } from '@/api/datasource'

/**
 * 路由和导航
 */
const route = useRoute()
const router = useRouter()

/**
 * 响应式数据
 */
const loading = ref(false)
const queryLoading = ref(false)
const packageData = ref<ResourcePackage | null>(null)
const datasources = ref<DataSource[]>([])
const queryResults = ref<ResourcePackageQueryResponse | null>(null)
const queryFormRef = ref<FormInstance>()

// 分页数据
const currentPage = ref(1)
const pageSize = ref(20)

// 查询表单数据
const queryForm = reactive<Record<string, any>>({})

// 查询选项
const queryOptions = reactive({
  orderField: '',
  orderDirection: 'ASC',
  limit: 1000
})

/**
 * 表单验证规则
 */
const queryRules = computed(() => {
  console.log('🔄 计算表单验证规则...')
  const rules: FormRules = {}
  
  if (packageData.value?.dynamic_conditions) {
    console.log('📋 处理动态条件验证规则:', packageData.value.dynamic_conditions.length)
    packageData.value.dynamic_conditions.forEach((condition, index) => {
      console.log(`  条件 ${index + 1} 验证规则:`, {
        param_name: condition.param_name,
        required: condition.required,
        hasParamName: !!condition.param_name
      })
      
      if (condition.required && condition.param_name) {
        rules[condition.param_name] = [
          { required: true, message: `请输入${condition.description || condition.field}`, trigger: 'blur' }
        ]
        console.log(`    ✅ 添加验证规则: ${condition.param_name}`)
      } else {
        console.log(`    ⚠️ 跳过验证规则: required=${condition.required}, param_name=${condition.param_name}`)
      }
    })
  } else {
    console.log('⚠️ 没有动态条件数据，无法生成验证规则')
  }
  
  console.log('📋 最终验证规则:', rules)
  return rules
})

/**
 * 计算属性
 */
const displayFields = computed(() => {
  if (!queryResults.value?.data?.length) return []
  
  // 如果配置了查询字段，优先显示配置的字段
  if (packageData.value?.base_config?.fields?.length) {
    return packageData.value.base_config.fields
  }
  
  // 否则显示结果中的所有字段
  return Object.keys(queryResults.value.data[0])
})

const paginatedData = computed(() => {
  if (!queryResults.value?.data?.length) return []
  
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return queryResults.value.data.slice(start, end)
})

const getDatasourceName = computed(() => {
  return (datasourceId: number) => {
    const ds = datasources.value.find((d: DataSource) => d.id === datasourceId)
    return ds ? ds.name : '未知数据源'
  }
})

/**
 * 方法定义
 */

/**
 * 返回列表页面
 */
const goBack = () => {
  router.push('/data-resources/packages')
}

/**
 * 加载资源包详情
 */
const loadPackageData = async () => {
  const packageId = route.params.id as string
  console.log('📦 开始加载资源包详情, ID:', packageId)
  
  if (!packageId) {
    console.error('❌ 资源包ID为空')
    ElMessage.error('资源包ID不能为空')
    goBack()
    return
  }

  try {
    loading.value = true
    console.log('🔄 正在请求资源包API...')
    const response = await resourcePackageApi.get(Number(packageId))
    console.log('✅ API响应:', response)
    
    // 检查响应结构并正确提取数据
    if (response.success && response.data) {
      packageData.value = response.data
      console.log('✅ 资源包数据加载成功:', packageData.value)
    } else {
      // 如果响应直接是资源包数据（向后兼容）
      packageData.value = response as any
      console.log('✅ 资源包数据加载成功（直接格式）:', packageData.value)
    }
    
    console.log('🔍 动态条件数据:', packageData.value?.dynamic_conditions)
    
    if (packageData.value?.dynamic_conditions) {
      console.log('📋 动态条件详情:')
      packageData.value.dynamic_conditions.forEach((condition, index) => {
        console.log(`  条件 ${index + 1}:`, {
          param_name: condition.param_name,
          field: condition.field,
          operator: condition.operator,
          description: condition.description,
          required: condition.required,
          default_value: condition.default_value
        })
      })
    } else {
      console.warn('⚠️ 没有找到动态条件数据')
    }
    
    initializeForm()
  } catch (error) {
    console.error('❌ 加载资源包详情失败:', error)
    ElMessage.error('加载资源包详情失败')
    goBack()
  } finally {
    loading.value = false
  }
}

/**
 * 加载数据源列表
 */
const loadDatasources = async () => {
  try {
    console.log('🔄 开始加载数据源列表...')
    const response = await datasourceApi.getDataSourceList()
    datasources.value = response.data?.items || []
    console.log('✅ 数据源列表加载成功:', datasources.value)
  } catch (error) {
    console.error('❌ 加载数据源列表失败:', error)
  }
}

/**
 * 初始化查询表单
 */
const initializeForm = () => {
  console.log('🔄 开始初始化查询表单...')
  
  // 重置查询表单
  Object.keys(queryForm).forEach(key => {
    delete queryForm[key]
  })
  console.log('🧹 查询表单已重置')
  
  // 设置默认值
  if (packageData.value?.dynamic_conditions) {
    console.log('📝 设置表单默认值...')
    packageData.value.dynamic_conditions.forEach((condition, index) => {
      console.log(`  处理条件 ${index + 1}:`, {
        param_name: condition.param_name,
        default_value: condition.default_value,
        hasParamName: !!condition.param_name,
        hasDefaultValue: condition.default_value !== undefined && condition.default_value !== null
      })
      
      if (condition.default_value !== undefined && condition.default_value !== null && condition.param_name) {
        queryForm[condition.param_name] = condition.default_value
        console.log(`    ✅ 设置默认值: ${condition.param_name} = ${condition.default_value}`)
      } else {
        console.log(`    ⚠️ 跳过设置默认值: param_name=${condition.param_name}, default_value=${condition.default_value}`)
      }
    })
    console.log('📋 最终表单数据:', queryForm)
  } else {
    console.warn('⚠️ 没有动态条件数据，无法设置默认值')
  }
  
  // 重置查询结果
  queryResults.value = null
  currentPage.value = 1
  console.log('✅ 查询表单初始化完成')
}

/**
 * 获取字段选项
 */
const getFieldOptions = (field: string): string[] => {
  // 这里可以根据字段类型返回预设选项
  // 暂时返回空数组，让用户自由输入
  return []
}

/**
 * 获取输入框占位符
 */
const getPlaceholder = (condition: any): string => {
  if (condition.default_value) {
    return `默认值: ${condition.default_value}`
  }
  
  switch (condition.operator) {
    case 'LIKE':
      return '支持通配符 %'
    case 'IN':
    case 'NOT IN':
      return '选择或输入多个值'
    case '>':
    case '>=':
    case '<':
    case '<=':
      return '输入数值'
    default:
      return `请输入${condition.description || condition.field}`
  }
}

/**
 * 重置表单
 */
const resetForm = () => {
  queryFormRef.value?.resetFields()
  initializeForm()
}

/**
 * 执行查询
 */
const executeQuery = async () => {
  if (!packageData.value) {
    ElMessage.error('资源包数据未加载')
    return
  }

  // 验证表单
  if (queryFormRef.value) {
    try {
      await queryFormRef.value.validate()
    } catch (error) {
      return
    }
  }
  
  try {
    queryLoading.value = true
    
    const queryRequest: ResourcePackageQueryRequest = {
      dynamic_params: { ...queryForm },
      limit: queryOptions.limit,
      offset: 0
    }
    
    const response = await resourcePackageApi.query(packageData.value.id, queryRequest)
    queryResults.value = response
    currentPage.value = 1
    
    ElMessage.success(`查询成功，共找到 ${response.total_count || 0} 条记录`)
    
  } catch (error) {
    console.error('查询失败:', error)
    ElMessage.error('查询失败')
  } finally {
    queryLoading.value = false
  }
}

/**
 * 分页处理
 */
const handleSizeChange = (newSize: number) => {
  pageSize.value = newSize
  currentPage.value = 1
}

const handleCurrentChange = (newPage: number) => {
  currentPage.value = newPage
}

/**
 * 导出查询结果
 */
const exportResults = async () => {
  if (!queryResults.value?.data?.length) {
    ElMessage.warning('没有数据可导出')
    return
  }
  
  try {
    await ElMessageBox.confirm('确定要导出查询结果吗？', '确认导出', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'info'
    })
    
    // 创建工作簿
    const wb = XLSX.utils.book_new()
    
    // 准备数据
    const exportData = queryResults.value.data.map((row: any) => {
      const newRow: Record<string, any> = {}
      displayFields.value.forEach((field: string) => {
        newRow[field] = typeof row[field] === 'object' ? JSON.stringify(row[field]) : row[field]
      })
      return newRow
    })
    
    // 创建工作表
    const ws = XLSX.utils.json_to_sheet(exportData)
    XLSX.utils.book_append_sheet(wb, ws, '查询结果')
    
    // 导出文件
    const fileName = `${packageData.value?.name || '资源包查询'}_${new Date().toISOString().slice(0, 10)}.xlsx`
    XLSX.writeFile(wb, fileName)
    
    ElMessage.success('导出成功')
    
  } catch (error) {
    if (error !== 'cancel') {
      console.error('导出失败:', error)
      ElMessage.error('导出失败')
    }
  }
}

/**
 * 生命周期
 */
onMounted(() => {
  console.log('🔄 ResourcePackageQueryPage 组件已挂载')
  console.log('📍 当前路由参数:', route.params)
  loadDatasources()
  loadPackageData()
})

// 监听路由参数变化
watch(() => route.params.id, () => {
  console.log('🔄 路由参数变化:', route.params.id)
  if (route.params.id) {
    loadPackageData()
  }
})
</script>

<style scoped>
.resource-package-query-page {
  padding: 20px;
  min-height: 100vh;
  background-color: #f5f5f5;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
  padding: 20px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.header-left {
  display: flex;
  align-items: flex-start;
  gap: 16px;
}

.back-button {
  padding: 8px;
  font-size: 16px;
  color: #606266;
}

.back-button:hover {
  color: #409eff;
}

.title-section h2 {
  margin: 0 0 8px 0;
  color: #303133;
  font-size: 24px;
  font-weight: 600;
}

.page-description {
  margin: 0;
  color: #606266;
  font-size: 14px;
}

.header-right {
  display: flex;
  align-items: center;
}

.page-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.package-info-card,
.query-form-card,
.query-options-card,
.query-results-card {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  font-weight: 600;
  color: #303133;
  font-size: 16px;
}

.package-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tag-item {
  margin: 0;
}

.locked-conditions,
.base-config {
  margin-top: 16px;
}

.locked-conditions h4,
.base-config h4 {
  margin: 0 0 12px 0;
  color: #303133;
  font-size: 14px;
  font-weight: 600;
}

.condition-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.condition-tag {
  margin: 0;
}

.config-info {
  margin-top: 8px;
}

.query-form {
  padding: 0;
}

.condition-info {
  margin-top: 4px;
}

.query-actions {
  display: flex;
  gap: 12px;
}

.results-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.results-meta {
  display: flex;
  gap: 16px;
  align-items: center;
}

.pagination-wrapper {
  margin-top: 16px;
  text-align: center;
}

.no-data {
  text-align: center;
  padding: 40px;
}

:deep(.el-card__header) {
  padding: 16px 20px;
  border-bottom: 1px solid #e4e7ed;
}

:deep(.el-card__body) {
  padding: 20px;
}

:deep(.el-form-item) {
  margin-bottom: 18px;
}

:deep(.el-input-number) {
  width: 100%;
}

:deep(.el-table) {
  font-size: 12px;
}

:deep(.el-table th) {
  background-color: #fafafa;
}

:deep(.el-descriptions__label) {
  font-weight: 600;
}
</style>