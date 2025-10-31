<template>
  <div class="resource-query-container">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1 class="page-title">
        <el-icon><Search /></el-icon>
        数据查询
      </h1>
      <p class="page-description">对数据资源进行查询和分析</p>
    </div>

    <!-- 查询类型选择 -->
    <div class="query-type-section">
      <el-card class="type-card">
        <template #header>
          <span>查询类型</span>
        </template>
        <el-radio-group 
          v-model="queryType" 
          @change="onQueryTypeChange"
          :disabled="isQueryTypeSwitchDisabled"
        >
          <el-radio-button label="sql">SQL查询</el-radio-button>
          <el-radio-button label="elasticsearch">Elasticsearch查询</el-radio-button>
        </el-radio-group>
      </el-card>
    </div>

    <!-- SQL查询组件 -->
    <div class="sql-query-section" v-if="queryType === 'sql'">
      <el-tabs v-model="sqlActiveTab" type="card">
        <el-tab-pane label="查询构建器" name="builder">
          <SQLQueryBuilder
            ref="sqlQueryBuilderRef"
            :sql-resources="sqlResources"
            :has-query-permission="hasQueryPermission"
            :has-export-permission="hasExportPermission"
            :has-save-permission="hasSavePermission"
            :initial-datasource-id="initialDatasourceId"
            :initial-resource-id="currentResourceId"
            :initial-schema="initialSchema"
            :initial-table-name="initialTableName"
            @execute-query="onSQLQueryExecute"
            @save-query="onSQLQuerySave"
            @update-query="onSQLQueryUpdate"
            @export-results="onSQLResultsExport"
          />
        </el-tab-pane>
        <el-tab-pane label="SQL模板" name="templates">
          <SQLTemplateManager
            ref="sqlTemplateManagerRef"
            :initial-datasource-id="initialDatasourceId"
            :initial-data-resource-id="currentResourceId"
            @execute-query="onSQLQueryExecute"
            @template-selected="onTemplateSelected"
          />
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- ES查询组件 -->
    <div class="es-query-section" v-if="queryType === 'elasticsearch'">
      <ESQueryBuilder
        ref="esQueryBuilderRef"
        :es-datasources="esDatasources"
        :initial-datasource-id="initialDatasourceId"
        :initial-indices="initialIndices"
        :data-resource-id="currentResourceId"
        :has-es-query-permission="hasESQueryPermission"
        :has-export-permission="hasExportPermission"
        :has-save-permission="hasSavePermission"
        @execute-query="onESQueryExecute"
        @save-query="onESQuerySave"
        @export-results="onESResultsExport"
        @datasources-loaded="onESDatasourcesLoaded"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import SQLQueryBuilder from '@/components/SQLQueryBuilder.vue'
import ESQueryBuilder from '@/components/ESQueryBuilder.vue'
import SQLTemplateManager from '@/components/SQLTemplateManager.vue'
import { saveSQLTemplate, updateSQLTemplate, executeSQLQuery } from '@/api/sqlQuery'
import { saveESQueryTemplate } from '@/api/esQuery'
import { dataResourceApi } from '@/api/dataResource'

// 路由和用户状态管理
const route = useRoute()
const userStore = useUserStore()

// 查询类型
const queryType = ref('sql')

// 计算属性：判断是否禁用查询类型切换
const isQueryTypeSwitchDisabled = computed(() => {
  // 当路由参数中有datasourceType时，禁用切换
  return !!route.query.datasourceType
})

// SQL查询相关状态
const sqlActiveTab = ref('builder')

// 计算属性：获取当前数据源ID（URL中的ID直接是数据源ID）
const initialDatasourceId = computed(() => {
  return route.params.id ? parseInt(route.params.id) : null
})

// 计算属性：获取当前数据资源ID（根据数据源ID查找对应的数据资源）
const currentResourceId = computed(() => {
  if (!initialDatasourceId.value || !sqlResources.value.length) {
    return null
  }
  // 查找当前数据源对应的数据资源
  const resource = sqlResources.value.find(r => r.datasource_id === initialDatasourceId.value)
  return resource ? resource.id : null
})

// 计算属性：获取初始Schema
const initialSchema = computed(() => {
  return route.query.schema || null
})

// 计算属性：获取初始表名
const initialTableName = computed(() => {
  return route.query.tableName || null
})

// 计算属性：获取初始索引列表
const initialIndices = computed(() => {
  const indices = route.query.indices
  if (typeof indices === 'string') {
    return [indices]
  } else if (Array.isArray(indices)) {
    return indices
  }
  return []
})

// 数据源数组
const sqlResources = ref([])
const esDatasources = ref([])

// 权限控制
const hasQueryPermission = computed(() => {
  return userStore.hasPermission('data:resource:query') || userStore.hasRole('admin')
})

const hasExportPermission = computed(() => {
  return userStore.hasPermission('data:resource:export') || userStore.hasRole('admin')
})

const hasSavePermission = computed(() => {
  return userStore.hasPermission('data:resource:save') || userStore.hasRole('admin')
})

const hasESQueryPermission = computed(() => {
  return userStore.hasPermission('data:elasticsearch:query') || userStore.hasRole('admin')
})

// 数据安全配置
const dataSecurity = computed(() => {
  return {
    enableFieldMasking: userStore.user?.dataSecurity?.enableFieldMasking || false,
    enableRowLevelSecurity: userStore.user?.dataSecurity?.enableRowLevelSecurity || false,
    maxExportRows: userStore.user?.dataSecurity?.maxExportRows || 10000
  }
})

/**
 * 初始化组件，处理路由参数
 */
onMounted(() => {
  // 处理路由参数
  const { datasourceType } = route.query
  
  // 根据路由参数设置查询类型
  if (datasourceType === 'elasticsearch') {
    queryType.value = 'elasticsearch'
  } else if (datasourceType === 'sql') {
    queryType.value = 'sql'
  }
  
  // 注意：route.params.id 是数据源ID，直接使用
  // initialDatasourceId 计算属性直接返回 route.params.id
  
  // 加载数据源列表
  loadDataSources()
})

/**
 * 加载数据资源列表
 */
const loadDataSources = async () => {
  try {
    // 加载数据资源列表
    const response = await dataResourceApi.getResourceList()
    if (response.data && response.data.items) {
      // 转换数据格式，将后端的 datasource_id 字段映射为前端的 datasourceId 字段
      sqlResources.value = response.data.items.map(item => ({
        ...item,
        datasourceId: item.datasource_id // 字段映射
      }))
    }
  } catch (error) {
    console.error('加载数据资源失败:', error)
    ElMessage.error('加载数据资源失败')
  }
}

/**
 * 查询类型变更处理
 */
const onQueryTypeChange = (type) => {
  queryType.value = type
}

// 事件处理函数
/**
 * 保存SQL查询模板
 * @param queryData 查询数据
 */
const onSQLQuerySave = async (queryData) => {
  try {
    // 构造保存模板的数据
    const templateData = {
      name: queryData.name,
      description: queryData.description,
      datasourceId: initialDatasourceId.value, // 使用正确的数据源ID
      dataResourceId: queryData.queryConfig.resourceId ? parseInt(queryData.queryConfig.resourceId) : null, // 使用正确的数据资源ID
      query: queryData.sql,
      tags: queryData.tags || [],
      config: queryData.config || {}, // 包含配置信息
      isTemplate: true
    }
    
    // 调用API保存模板
    const response = await saveSQLTemplate(templateData)
    
    console.log('SQL查询模板保存成功:', templateData)
    console.log('保存响应:', response)
    
    // 获取返回的模板ID并设置到SQLQueryBuilder组件中
    if (response && response.data && response.data.id && sqlQueryBuilderRef.value) {
      const templateId = response.data.id
      console.log('✅ 获取到保存的模板ID:', templateId)
      sqlQueryBuilderRef.value.setCurrentTemplateId(templateId)
    }
    
    ElMessage.success('SQL查询模板保存成功')
  } catch (error) {
    console.error('保存SQL查询模板失败:', error)
    ElMessage.error('保存SQL查询模板失败')
  }
}

/**
 * 更新SQL查询模板
 * @param queryData 查询数据
 */
const onSQLQueryUpdate = async (queryData) => {
  try {
    // 构造更新模板的数据
    const templateData = {
      name: queryData.name,
      description: queryData.description,
      datasourceId: initialDatasourceId.value, // 使用正确的数据源ID
      dataResourceId: queryData.queryConfig.resourceId ? parseInt(queryData.queryConfig.resourceId) : null, // 使用正确的数据资源ID
      query: queryData.sql,
      tags: queryData.tags || [],
      config: queryData.config || {}, // 包含配置信息
      isTemplate: true
    }
    
    // 调用API更新模板
    await updateSQLTemplate(queryData.id, templateData)
    
    console.log('SQL查询模板更新成功:', templateData)
    ElMessage.success('SQL查询模板更新成功')
  } catch (error) {
    console.error('更新SQL查询模板失败:', error)
    ElMessage.error('更新SQL查询模板失败')
  }
}

/**
 * 执行SQL查询
 * @param queryData 查询数据
 */
const onSQLQueryExecute = async (queryData) => {
  console.log('🚀 执行SQL查询:', queryData)
  
  try {
    // 验证查询参数
    if (!queryData.datasourceId) {
      ElMessage.error('缺少数据源ID')
      return
    }
    
    if (!queryData.sql) {
      ElMessage.error('缺少SQL查询语句')
      return
    }
    
    // 构建查询请求参数
    const queryRequest = {
      datasourceId: queryData.datasourceId,
      query: queryData.sql,
      limit: queryData.limit || 1000,
      offset: queryData.offset || 0
    }
    
    console.log('📤 发送查询请求:', queryRequest)
    
    // 调用API执行查询
    const response = await executeSQLQuery(queryRequest)
    
    console.log('📥 查询响应完整结构:', response)
    console.log('📥 响应数据类型:', typeof response)
    console.log('📥 响应数据键:', Object.keys(response || {}))
    
    // 获取实际的查询结果数据
    // 根据API响应格式，直接使用response作为查询结果对象
    const apiResult = response
    console.log('📊 API响应对象:', apiResult)
    console.log('📊 API响应类型:', typeof apiResult)
    console.log('📊 API响应键:', Object.keys(apiResult || {}))
    
    // 统一处理查询结果
    const success = !!apiResult?.success
    const columns = apiResult?.columns
    const data = apiResult?.data
    const row_count = apiResult?.row_count ?? (Array.isArray(data) ? data.length : 0)
    const execution_time = apiResult?.execution_time ?? 0

    // 处理查询结果
    if (success) {
      console.log('📊 统一后的数据:')
      console.log('  - columns:', columns, '类型:', typeof columns)
      console.log('  - data:', data, '类型:', typeof data, '长度:', Array.isArray(data) ? data.length : 'N/A')
      console.log('  - row_count:', row_count)
      console.log('  - execution_time:', execution_time)
      
      if (columns && data) {
        console.log('✅ 有columns和data，进行正常转换')
        
        // 转换列信息格式
        const resultColumns = columns.map(col => ({
          prop: col,
          label: col,
          type: 'string', // 默认类型，后续可以根据数据推断
          width: 150
        }))
        
        // 转换数据格式 - 将二维数组转换为对象数组
        const resultData = data.map(row => {
          const obj = {}
          columns.forEach((col, index) => {
            obj[col] = row[index]
          })
          return obj
        })
        
        console.log('📋 转换后的列信息:', resultColumns)
        console.log('📋 转换后的数据 (前3条):', resultData.slice(0, 3))
        
        // 将结果传递给SQLQueryBuilder组件
        if (sqlQueryBuilderRef.value) {
          sqlQueryBuilderRef.value.setQueryResults(resultData, resultColumns)
        }
        
        console.log(`✅ 查询执行成功，返回 ${row_count} 条记录，执行时间: ${execution_time}ms`)
        ElMessage.success(`查询执行成功，返回 ${row_count} 条记录`)
      } else if (data && Array.isArray(data) && data.length > 0) {
        console.log('⚠️ 没有columns但有data，尝试自动生成列名',data)
        
        // 如果没有columns但有data，尝试自动生成列名
        const firstRow = data[0]
        const autoColumns = Array.isArray(firstRow) 
          ? firstRow.map((_, index) => `column_${index + 1}_${_}`)
          : ['column_1']
        
        console.log('🔧 自动生成的列名:', autoColumns)
        
        // 转换列信息格式
        const resultColumns = autoColumns.map(col => ({
          prop: col,
          label: col,
          type: 'string',
          width: 150
        }))
        
        // 转换数据格式
        const resultData = data.map(row => {
          const obj = {}
          if (Array.isArray(row)) {
            autoColumns.forEach((col, index) => {
              obj[col] = row[index]
            })
          } else {
            obj['column_1'] = row
          }
          return obj
        })
        
        console.log('📋 自动转换后的列信息:', resultColumns)
        console.log('📋 自动转换后的数据 (前3条):', resultData.slice(0, 3))
        
        // 将结果传递给SQLQueryBuilder组件
        if (sqlQueryBuilderRef.value) {
          sqlQueryBuilderRef.value.setQueryResults(resultData, resultColumns)
        }
        
        console.log(`✅ 查询执行成功，返回 ${data.length} 条记录`)
        ElMessage.success(`查询执行成功，返回 ${data.length} 条记录`)
      } else {
        console.log('⚠️ 查询成功但无数据返回')
        ElMessage.info('查询成功但无数据返回')
        
        // 清空结果
        if (sqlQueryBuilderRef.value) {
          sqlQueryBuilderRef.value.setQueryResults([], [])
        }
      }
    } else {
      // 查询失败
      const errorMessage = apiResult?.error_details || apiResult?.message || response?.message || '查询执行失败'
      console.error('❌ 查询执行失败:', errorMessage)
      
      if (sqlQueryBuilderRef.value) {
        sqlQueryBuilderRef.value.handleQueryError(new Error(errorMessage))
      }
      
      ElMessage.error(`查询执行失败: ${errorMessage}`)
    }
    
  } catch (error) {
    console.error('❌ SQL查询执行失败:', error)
    
    // 通知SQLQueryBuilder组件查询失败
    if (sqlQueryBuilderRef.value) {
      sqlQueryBuilderRef.value.handleQueryError(error)
    }
    
    // 显示错误消息
    const errorMessage = error.response?.data?.detail || error.message || '查询执行失败'
    ElMessage.error(`查询执行失败: ${errorMessage}`)
  }
}

const onSQLResultsExport = (results) => {
  console.log('导出SQL查询结果:', results)
}

/**
 * 保存ES查询模板
 * @param queryData 查询数据
 */
const onESQuerySave = async (queryData) => {
  try {
    // 构造保存模板的数据
    const templateData = {
      name: queryData.name,
      description: queryData.description,
      datasourceId: queryData.datasourceId || initialDatasourceId.value,
      indices: queryData.indices || [],
      query: queryData.query,
      tags: queryData.tags || [],
      isTemplate: queryData.isTemplate !== undefined ? queryData.isTemplate : true
    }
    
    // 调用API保存模板
    await saveESQueryTemplate(templateData)
    
    console.log('ES查询模板保存成功:', templateData)
  } catch (error) {
    console.error('保存ES查询模板失败:', error)
  }
}

const onESQueryExecute = (queryData) => {
  console.log('执行ES查询:', queryData)
}

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

/**
 * SQL模板选择处理
 */
const onTemplateSelected = (template) => {
  console.log('选择SQL模板:', template)
  // 切换到查询构建器标签页
  sqlActiveTab.value = 'builder'
  // 将模板内容传递给查询构建器
  if (sqlQueryBuilderRef.value) {
    sqlQueryBuilderRef.value.loadTemplate(template)
  }
}

// 组件引用
const sqlQueryBuilderRef = ref(null)
const sqlTemplateManagerRef = ref(null)
const esQueryBuilderRef = ref(null)
</script>

<style scoped>
.resource-query {
  padding: 20px;
}

.query-type-selector {
  margin-bottom: 20px;
}

.query-type-selector .el-radio-group {
  display: flex;
  gap: 20px;
}

.query-type-selector .el-radio-button {
  flex: 1;
}

.query-type-selector .el-radio-button__inner {
  width: 100%;
  text-align: center;
  padding: 12px 20px;
  font-weight: 500;
}
</style>