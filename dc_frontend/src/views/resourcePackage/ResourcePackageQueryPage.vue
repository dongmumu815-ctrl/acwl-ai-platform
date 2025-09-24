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
        
        <!-- 模板信息展示 -->
        <div class="template-info">
          <h4>模板信息</h4>
          <div class="template-details">
            <el-tag type="primary" class="template-tag">
              类型: {{ packageData.template_type || '未知' }}
            </el-tag>
            <el-tag v-if="packageData.template_id" type="info" class="template-tag">
              模板ID: {{ packageData.template_id }}
            </el-tag>
          </div>
        </div>

        <!-- 基础配置信息 -->
        <div class="base-config">
          <h4>查询配置</h4>
          <div class="config-info">
            <el-descriptions :column="2" size="small">
              <el-descriptions-item label="数据源">{{ getDatasourceName(packageData.datasource_id) }}</el-descriptions-item>
              <el-descriptions-item label="查询类型">{{ packageData.type?.toUpperCase() || '未知' }}</el-descriptions-item>
              <el-descriptions-item label="模板类型">{{ packageData.template_type || '未知' }}</el-descriptions-item>
              <el-descriptions-item label="模板ID">{{ packageData.template_id || '无' }}</el-descriptions-item>
            </el-descriptions>
          </div>
        </div>
      </el-card>

      <!-- 调试信息 -->
      <!-- <el-card class="debug-info-card" v-if="packageData" style="margin-bottom: 20px; border: 2px dashed #409eff;">
        <template #header>
          <span class="card-title" style="color: #409eff;">🐛 调试信息</span>
        </template>
        <div style="font-family: monospace; font-size: 12px;">
          <p><strong>资源包ID:</strong> {{ route.params.id }}</p>
          <p><strong>资源包数据:</strong> {{ packageData ? '已加载' : '未加载' }}</p>
          <p><strong>模板类型:</strong> {{ packageData?.template_type || '未知' }}</p>
          <p><strong>模板ID:</strong> {{ packageData?.template_id || '无' }}</p>
          <p><strong>动态参数:</strong> {{ packageData?.dynamic_params ? `存在 (${Object.keys(packageData.dynamic_params).length} 个)` : '不存在' }}</p>
          <div v-if="packageData?.dynamic_params && Object.keys(packageData.dynamic_params).length">
            <p><strong>参数详情:</strong></p>
            <ul style="margin: 0; padding-left: 20px;">
              <li v-for="(value, key) in packageData.dynamic_params" :key="key" style="margin: 5px 0;">
                参数: {{ key }} = {{ value }}
              </li>
            </ul>
          </div>
        </div>
      </el-card> -->

      <!-- 查询参数表单 -->
      <el-card class="query-form-card" v-if="packageData?.dynamic_params && Object.keys(packageData.dynamic_params).length">
        <template #header>
          

          <div class="card-header">
           <span class="card-title">查询参数</span>
            <div class="query-actions">
              <el-button @click="resetForm">重置</el-button>
              <el-button type="primary" @click="handleUserQuery" :loading="queryLoading">
                <el-icon><Search /></el-icon>
                执行查询
              </el-button>
            </div>
          </div>
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
              v-for="(paramValue, paramName) in packageData.dynamic_params"
              :key="paramName"
              :span="12"
            >
              <el-form-item
                :label="getConditionLabel(paramName)"
                :prop="paramName"
              >
                <!-- 根据参数类型显示不同的输入组件 -->
                <template v-if="typeof paramValue === 'boolean'">
                  <el-switch
                    v-model="queryForm[paramName]"
                    active-text="是"
                    inactive-text="否"
                    @focus="markFieldTouched(paramName)"
                    @change="markFieldTouched(paramName)"
                  />
                </template>
                <template v-else-if="typeof paramValue === 'number'">
                  <el-input-number
                    v-model="queryForm[paramName]"
                    :placeholder="`请输入${getConditionLabel(paramName)}`"
                    style="width: 100%"
                    @focus="markFieldTouched(paramName)"
                    @input="markFieldTouched(paramName)"
                  />
                </template>
                <template v-else>
                  <el-input
                    v-model="queryForm[paramName]"
                    :placeholder="`请输入${getConditionLabel(paramName)}`"
                    @focus="markFieldTouched(paramName)"
                    @input="markFieldTouched(paramName)"
                  />
                </template>
                
                <div class="condition-info" v-if="getConditionInfo(paramName)">
                  <el-text size="small" type="info">
                    {{ getConditionInfo(paramName) }}
                  </el-text>
                </div>
              </el-form-item>
            </el-col>
          </el-row>
        </el-form>
      </el-card>

      <!-- 查询选项
      <el-card class="query-options-card">
        <template #header>
          <div class="card-header">
            <span class="card-title">查询选项</span>
            <div class="query-actions">
              <el-button @click="resetForm">重置</el-button>
              <el-button type="primary" @click="handleUserQuery" :loading="queryLoading">
                <el-icon><Search /></el-icon>
                执行查询
              </el-button>
            </div>
          </div>
        </template>
        
        <el-row :gutter="20">
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
      </el-card> -->

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
              v-for="(field, index) in displayFields"
              :key="field"
              :prop="index.toString()"
              :label="field"
              :min-width="120"
              show-overflow-tooltip
            >
              <template #default="{ row }">
                <span v-if="typeof row[index] === 'object'">{{ JSON.stringify(row[index]) }}</span>
                <span v-else>{{ row[index] }}</span>
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
import { datasourceApi } from '@/api/datasource'
import { type DataSource } from '@/types/datasource'
import { getSQLTemplate, type SQLTemplateResponse } from '@/api/sqlQuery'
import { templateApi } from '@/api/template'

// 扩展ResourcePackage接口以包含模板条件
interface ExtendedResourcePackage extends ResourcePackage {
  template_conditions?: any[]
  query?: string
}

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
const packageData = ref<ExtendedResourcePackage | null>(null)
const datasources = ref<DataSource[]>([])
const queryResults = ref<ResourcePackageQueryResponse | null>(null)
const queryFormRef = ref<FormInstance>()

// 分页数据
const currentPage = ref(1)
const pageSize = ref(20)

// 查询表单数据
const queryForm = reactive<Record<string, any>>({})

// 跟踪用户是否主动操作过每个输入框
const fieldTouched = reactive<Record<string, boolean>>({})

// 查询选项
const queryOptions = reactive({
  limit: 1000
})

/**
 * 表单验证规则
 */
const queryRules = computed(() => {
  console.log('🔄 计算表单验证规则...')
  const rules: FormRules = {}
  
  if (packageData.value?.template_conditions) {
    console.log('📋 处理模板条件验证规则:', packageData.value.template_conditions.length)
    packageData.value.template_conditions.forEach((condition: any) => {
      // 只为未锁定的条件添加验证规则
      if (!condition.locked) {
        const fieldRules: any[] = []
        
        // 必填验证
        if (condition.required) {
          fieldRules.push({
            required: true,
            message: `请输入${condition.label || condition.name}`,
            trigger: 'blur'
          })
        }
        
        // 类型验证
        if (condition.type === 'number') {
          fieldRules.push({
            type: 'number',
            message: `${condition.label || condition.name}必须是数字`,
            trigger: 'blur',
            transform: (value: any) => Number(value)
          })
        }
        
        if (fieldRules.length > 0) {
          rules[condition.name] = fieldRules
        }
      }
    })
  } else {
    console.log('⚠️ 没有模板条件数据，无法生成验证规则')
  }
  
  console.log('📋 最终验证规则:', rules)
  return rules
})

/**
 * 计算属性
 */
const displayFields = computed(() => {
  // 🐛 调试日志：输出计算过程
  console.log('🔍 displayFields计算中...')
  console.log('🔍 queryResults.value:', queryResults.value)
  console.log('🔍 queryResults.value?.columns:', queryResults.value?.columns)
  console.log('🔍 queryResults.value?.data:', queryResults.value?.data)
  
  // 使用API返回的columns作为显示字段
  const fields = queryResults.value?.columns || []
  console.log('🔍 最终的displayFields:', fields)
  
  return fields
})

const paginatedData = computed(() => {
  // 现在使用后端分页，直接返回API返回的数据
  if (!queryResults.value?.data?.length) return []
  return queryResults.value.data
})

const getDatasourceName = computed(() => {
  return (datasourceId: number) => {
    const ds = datasources.value.find((d: DataSource) => d.id === datasourceId)
    return ds ? ds.name : '未知数据源'
  }
})

/**
 * 获取条件标签
 */
const getConditionLabel = (paramName: string) => {
  if (!packageData.value?.template_conditions) return paramName
  const condition = packageData.value.template_conditions.find((c: any) => c.name === paramName)
  return condition?.label || paramName
}

/**
 * 获取条件信息
 */
const getConditionInfo = (paramName: string) => {
  if (!packageData.value?.template_conditions) return ''
  const condition = packageData.value.template_conditions.find((c: any) => c.name === paramName)
  if (!condition) return ''
  
  let info = `${condition.name} ${condition.operator}`
  if (condition.default_value) {
    info += ` (默认: ${condition.default_value})`
  }
  return info
}

/**
 * 方法定义
 */

/**
 * 标记字段为用户主动操作过
 */
const markFieldTouched = (fieldName: string) => {
  fieldTouched[fieldName] = true
  console.log(`🎯 字段 ${fieldName} 被用户操作，已标记为touched`)
}

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
    
    // 检查响应格式并提取数据
    if (response && typeof response === 'object' && 'data' in response) {
      // 如果是ApiResponse格式，提取data字段
      packageData.value = response.data
      console.log('✅ 资源包数据加载成功 (从response.data):', packageData.value)
    } else {
      // 如果直接是数据对象
      packageData.value = response as any
      console.log('✅ 资源包数据加载成功 (直接使用response):', packageData.value)
    }
    
    console.log('🔍 资源包数据:', packageData.value)
    console.log('🔍 模板ID:', packageData.value?.template_id)
    console.log('🔍 模板类型:', packageData.value?.template_type)
    
    // 如果有模板信息，加载参数配置
    if (packageData.value?.template_id && packageData.value?.template_type) {
      console.log('✅ 满足模板加载条件，开始加载模板参数...')
      await loadTemplateParams()
    } else {
      console.warn('⚠️ 不满足模板加载条件:', {
        template_id: packageData.value?.template_id,
        template_type: packageData.value?.template_type
      })
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
 * 根据模板类型加载参数配置
 */
const loadTemplateParams = async () => {
  if (!packageData.value?.template_id || !packageData.value?.template_type) {
    console.warn('模板ID或类型不存在，无法加载参数')
    return
  }

  try {
    console.log('🔄 开始加载模板参数，模板ID:', packageData.value.template_id, '类型:', packageData.value.template_type)
    
    let templateData: SQLTemplateResponse | any = null
    
    if (packageData.value.template_type === 'sql') {
      // 调用SQL模板API
      const response = await getSQLTemplate(packageData.value.template_id)
      templateData = response.data
    } else if (packageData.value.template_type === 'elasticsearch') {
      // 调用ES模板API
      const response = await templateApi.getByType(packageData.value.template_id, 'es')
      templateData = response
    }
    
    if (templateData && templateData.config) {
      console.log('✅ 模板参数加载成功:', templateData.config)
      // 从模板配置中解析条件参数，过滤掉锁定的条件
      const conditions = templateData.config.conditions || []
      const unlockedConditions = conditions.filter((condition: any) => !condition.locked)
      
      // 将未锁定的条件转换为动态参数格式
      const dynamicParams: Record<string, any> = {}
      unlockedConditions.forEach((condition: any) => {
        dynamicParams[condition.name] = condition.default_value || ''
      })
      
      if (packageData.value) {
        packageData.value.dynamic_params = dynamicParams
        packageData.value.template_conditions = unlockedConditions
      }
    } else {
      console.warn('⚠️ 模板配置中没有找到参数信息')
    }
  } catch (error) {
    console.error('❌ 加载模板参数失败:', error)
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
  
  // 重置字段操作状态
  Object.keys(fieldTouched).forEach(key => {
    delete fieldTouched[key]
  })
  console.log('🧹 字段操作状态已重置')
  
  // 设置默认值
  if (packageData.value?.template_conditions) {
    console.log('📝 设置表单默认值...')
    packageData.value.template_conditions.forEach((condition: any, index: number) => {
      console.log(`  处理条件 ${index + 1}:`, {
        name: condition.name,
        default_value: condition.default_value,
        type: condition.type,
        locked: condition.locked
      })
      
      // 只处理未锁定的条件
      if (!condition.locked) {
        if (condition.default_value !== undefined && condition.default_value !== null) {
          queryForm[condition.name] = condition.default_value
          console.log(`    ✅ 设置默认值: ${condition.name} = ${condition.default_value}`)
        } else {
          // 根据类型设置空值
          switch (condition.type) {
            case 'string':
              queryForm[condition.name] = ''
              break
            case 'number':
              queryForm[condition.name] = null
              break
            default:
              queryForm[condition.name] = ''
          }
          console.log(`    ⚠️ 设置空值: ${condition.name} = ${queryForm[condition.name]}`)
        }
      } else {
        console.log(`    🔒 跳过锁定条件: ${condition.name}`)
      }
    })
    console.log('📋 最终表单数据:', queryForm)
  } else {
    console.warn('⚠️ 没有模板条件数据，无法设置默认值')
  }
  
  // 重置查询结果
  queryResults.value = null
  currentPage.value = 1
  console.log('✅ 查询表单初始化完成')
}



/**
 * 重置表单
 */
const resetForm = () => {
  queryFormRef.value?.resetFields()
  initializeForm()
}

/**
 * 处理用户主动查询（重置到第一页）
 */
const handleUserQuery = async () => {
  // 用户主动查询时，重置到第一页
  currentPage.value = 1
  await executeQuery()
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
    
    // 过滤参数：只包含用户主动操作过的字段
    const filteredParams: Record<string, any> = {}
    Object.keys(queryForm).forEach(key => {
      // 如果用户操作过这个字段，或者字段有非空值，则包含在请求中
      if (fieldTouched[key] || (queryForm[key] !== '' && queryForm[key] !== null && queryForm[key] !== undefined)) {
        filteredParams[key] = queryForm[key]
      }
    })
    
    console.log('🔍 原始表单数据:', queryForm)
    console.log('🎯 用户操作过的字段:', fieldTouched)
    console.log('✅ 过滤后的参数:', filteredParams)
    
    // 使用新的安全查询接口
    const queryRequest: ResourcePackageQueryRequest = {
      dynamic_params: filteredParams,
      limit: pageSize.value,
      offset: (currentPage.value - 1) * pageSize.value
    }
    
    console.log('🔄 使用安全查询接口执行查询...')
    const response = await resourcePackageApi.secureQuery(packageData.value.id, queryRequest)
    
    // 🐛 调试日志：输出完整的API响应
    console.log('📊 API完整响应:', response)
    console.log('📊 response.data:', response.data)
    console.log('📊 response.data.columns:', response.data?.columns)
    console.log('📊 response.data.data:', response.data?.data)
    
    // 处理响应数据
    if (response && response.data) {
      queryResults.value = {
        data: response.data.data || [],
        columns: response.data.columns || [], // 🐛 添加columns字段
        total_count: response.data.total_count || 0,
        execution_time: response.data.execution_time || 0,
        generated_query: response.data.generated_query,
        status: response.data.status,
        error_message: response.data.error_message
      }
    } else {
      queryResults.value = response
    }
    
    // 🐛 调试日志：输出处理后的queryResults
    console.log('📊 处理后的queryResults:', queryResults.value)
    
    if (queryResults.value?.error_message) {
      ElMessage.error(`查询失败: ${queryResults.value.error_message}`)
    } else {
      ElMessage.success(`查询成功，共找到 ${queryResults.value?.total_count || 0} 条记录`)
    }
    
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
  // 重新执行查询
  if (queryResults.value) {
    executeQuery()
  }
}

const handleCurrentChange = (newPage: number) => {
  currentPage.value = newPage
  // 重新执行查询
  if (queryResults.value) {
    executeQuery()
  }
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