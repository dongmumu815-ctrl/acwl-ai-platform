<template>
  <el-dialog
    v-model="dialogVisible"
    title="资源包查询"
    width="80%"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <div v-loading="loading">
      <!-- 资源包信息 -->
      <el-card class="package-info">
        <template #header>
          <div class="package-header">
            <div>
              <h3>{{ packageData?.name }}</h3>
              <el-text type="info">{{ packageData?.description }}</el-text>
            </div>
            <div class="package-meta">
              <el-tag :type="packageData?.type === 'sql' ? 'primary' : 'success'">
                {{ packageData?.type === 'sql' ? 'SQL查询' : 'Elasticsearch' }}
              </el-tag>
              <el-tag v-for="tag in packageData?.tags" :key="tag.tag_name" class="tag-item">
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
              类型: {{ packageData?.template_type || '未知' }}
            </el-tag>
            <el-tag v-if="packageData?.template_id" type="info" class="template-tag">
              模板ID: {{ packageData.template_id }}
            </el-tag>
          </div>
        </div>
      </el-card>

      <!-- 动态查询参数 -->
      <el-card class="query-form" v-if="packageData?.dynamic_params && Object.keys(packageData.dynamic_params).length">
        <template #header>
          <span class="section-title">查询参数</span>
        </template>
        
        <el-form
          ref="queryFormRef"
          :model="queryForm"
          :rules="queryRules"
          label-width="120px"
        >
          <el-row :gutter="20">
            <el-col
              v-for="(paramValue, paramName) in packageData.dynamic_params"
              :key="paramName"
              :span="12"
            >
              <el-form-item
                :label="paramName"
                :prop="paramName"
              >
                <!-- 根据参数类型显示不同的输入组件 -->
                <template v-if="typeof paramValue === 'boolean'">
                  <el-switch
                    v-model="queryForm[paramName]"
                    active-text="是"
                    inactive-text="否"
                  />
                </template>
                <template v-else-if="typeof paramValue === 'number'">
                  <el-input-number
                    v-model="queryForm[paramName]"
                    :placeholder="`请输入${paramName}`"
                    style="width: 100%"
                  />
                </template>
                <template v-else>
                  <el-input
                    v-model="queryForm[paramName]"
                    :placeholder="`请输入${paramName}`"
                  />
                </template>
                
                <div class="param-info">
                  <el-text size="small" type="info">
                    默认值: {{ paramValue }}
                  </el-text>
                </div>
              </el-form-item>
            </el-col>
          </el-row>
        </el-form>
      </el-card>

      <!-- 查询选项 -->
      <el-card class="query-options">
        <template #header>
          <span class="section-title">查询选项</span>
        </template>
<!--         
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="查询条数">
              <el-input-number
                v-model="queryOptions.limit"
                :min="1"
                :max="10000"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row> -->
      </el-card>

      <!-- 查询结果 -->
      <el-card class="query-results" v-if="queryResults">
        <template #header>
          <div class="results-header">
            <span class="section-title">查询结果</span>
            <div class="results-meta">
              <el-text type="info">共 {{ queryResults.total }} 条记录，耗时 {{ queryResults.execution_time }}ms</el-text>
              <el-button type="primary" size="small" @click="exportResults" :disabled="!queryResults.data?.length">
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
            max-height="400"
            style="width: 100%"
          >
            <el-table-column
              v-for="column in resultColumns"
              :key="column.prop"
              :prop="column.prop"
              :label="column.label"
              :width="column.width"
              :min-width="column.minWidth"
              show-overflow-tooltip
            >
              <template #default="{ row }">
                <span v-if="column.type === 'date'">
                  {{ formatDate(row[column.columnIndex]) }}
                </span>
                <span v-else-if="column.type === 'number'">
                  {{ formatNumber(row[column.columnIndex]) }}
                </span>
                <span v-else-if="column.type === 'boolean'">
                  <el-tag :type="row[column.columnIndex] ? 'success' : 'info'">
                    {{ row[column.columnIndex] ? '是' : '否' }}
                  </el-tag>
                </span>
                <el-tag v-else-if="column.type === 'status'" :type="getStatusTagType(row[column.columnIndex])">
                  {{ row[column.columnIndex] }}
                </el-tag>
                <span v-else-if="column.type === 'object'">
                  {{ JSON.stringify(row[column.columnIndex]) }}
                </span>
                <span v-else>
                  {{ row[column.columnIndex] }}
                </span>
              </template>
            </el-table-column>
          </el-table>
          
          <!-- 分页 -->
          <div class="pagination-wrapper">
            <el-pagination
              v-model:current-page="currentPage"
              v-model:page-size="pageSize"
              :page-sizes="[10, 20, 50, 100]"
              :total="queryResults.total"
              layout="total, sizes, prev, pager, next, jumper"
              @size-change="handleSizeChange"
              @current-change="handleCurrentChange"
            />
          </div>
        </div>
        
        <div v-else class="no-data">
          <el-empty description="暂无数据" />
        </div>
      </el-card>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">关闭</el-button>
        <el-button type="primary" @click="executeQuery" :loading="queryLoading">
          <el-icon><Search /></el-icon>
          执行查询
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, watch, computed, nextTick } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Search, Download } from '@element-plus/icons-vue'
import {
  resourcePackageApi,
  type ResourcePackage,
  type ResourcePackageQueryRequest,
  type ResourcePackageQueryResponse
} from '@/api/resourcePackage'
import * as XLSX from 'xlsx'

// Props
interface Props {
  visible: boolean
  packageData?: ResourcePackage | null
}

const props = withDefaults(defineProps<Props>(), {
  visible: false,
  packageData: null
})

// Emits
const emit = defineEmits<{
  'update:visible': [value: boolean]
}>()

// 响应式数据
const queryFormRef = ref<FormInstance>()
const loading = ref(false)
const queryLoading = ref(false)
const dialogVisible = ref(false)
const queryResults = ref<ResourcePackageQueryResponse | null>(null)
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

// 表单验证规则
const queryRules = computed(() => {
  const rules: FormRules = {}
  
  if (props.packageData?.dynamic_conditions) {
    props.packageData.dynamic_conditions.forEach(condition => {
      if (condition.required) {
        rules[condition.param_name] = [
          { required: true, message: `请输入${condition.description || condition.field}`, trigger: 'blur' }
        ]
      }
    })
  }
  
  return rules
})

// 计算属性
const displayFields = computed(() => {
  // 使用API返回的columns作为显示字段
  return queryResults.value?.columns || []
})

/**
 * 表格列配置
 * 使用API返回的columns作为表头，并根据数据自动检测列类型设置相应的格式化
 */
const resultColumns = computed(() => {
  // 如果没有columns信息或没有数据，返回空数组
  if (!queryResults.value?.columns?.length || !queryResults.value?.data?.length) return []
  
  const firstRow = queryResults.value.data[0]
  
  return queryResults.value.columns.map((columnName, index) => {
    // 获取对应位置的数据值用于类型检测
    const value = Array.isArray(firstRow) ? firstRow[index] : firstRow[columnName]
    
    const column = {
      prop: index.toString(), // 使用索引作为prop，因为数据是数组格式
      label: columnName, // 直接使用API返回的列名
      type: detectColumnType(columnName, value),
      width: undefined as number | undefined,
      minWidth: getColumnMinWidth(columnName, value),
      columnIndex: index // 保存列索引用于数据访问
    }
    
    // 根据字段类型设置固定宽度
    if (column.type === 'boolean') {
      column.width = 80
    } else if (column.type === 'date') {
      column.width = 160
    } else if (column.type === 'number') {
      column.width = 120
    }
    
    return column
  })
})

/**
 * 分页数据
 * 现在使用后端分页，直接返回API数据
 */
const paginatedData = computed(() => {
  if (!queryResults.value?.data?.length) return []
  return queryResults.value.data
})

// 监听器
watch(() => props.visible, (newVal) => {
  dialogVisible.value = newVal
  if (newVal) {
    initializeForm()
  }
})

watch(dialogVisible, (newVal) => {
  emit('update:visible', newVal)
})

// 辅助函数

/**
 * 检测列数据类型
 * @param fieldName 字段名
 * @param value 字段值
 */
const detectColumnType = (fieldName: string, value: any): string => {
  // 根据字段名判断
  const fieldLower = fieldName.toLowerCase()
  
  if (fieldLower.includes('time') || fieldLower.includes('date') || fieldLower.includes('created') || fieldLower.includes('updated')) {
    return 'date'
  }
  
  if (fieldLower.includes('status') || fieldLower.includes('state')) {
    return 'status'
  }
  
  // 根据值类型判断
  if (typeof value === 'boolean') {
    return 'boolean'
  }
  
  if (typeof value === 'number') {
    return 'number'
  }
  
  if (typeof value === 'object' && value !== null) {
    return 'object'
  }
  
  // 检查是否为日期字符串
  if (typeof value === 'string' && /^\d{4}-\d{2}-\d{2}/.test(value)) {
    return 'date'
  }
  
  return 'string'
}

/**
 * 获取列标签（友好的显示名称）
 * @param fieldName 字段名
 */
const getColumnLabel = (fieldName: string): string => {
  // 字段名映射表
  const labelMap: Record<string, string> = {
    'id': 'ID',
    'name': '名称',
    'title': '标题',
    'description': '描述',
    'status': '状态',
    'state': '状态',
    'type': '类型',
    'created_at': '创建时间',
    'updated_at': '更新时间',
    'created_time': '创建时间',
    'updated_time': '更新时间',
    'create_time': '创建时间',
    'update_time': '更新时间',
    'is_active': '是否激活',
    'is_deleted': '是否删除',
    'is_enabled': '是否启用',
    'count': '数量',
    'total': '总计',
    'amount': '金额',
    'price': '价格',
    'email': '邮箱',
    'phone': '电话',
    'address': '地址',
    'remark': '备注',
    'comment': '评论'
  }
  
  // 先查找完全匹配
  if (labelMap[fieldName.toLowerCase()]) {
    return labelMap[fieldName.toLowerCase()]
  }
  
  // 转换驼峰命名和下划线命名为友好显示
  return fieldName
    .replace(/_/g, ' ')
    .replace(/([A-Z])/g, ' $1')
    .replace(/^\w/, c => c.toUpperCase())
    .trim()
}

/**
 * 获取列最小宽度
 * @param fieldName 字段名
 * @param value 字段值
 */
const getColumnMinWidth = (fieldName: string, value: any): number => {
  const label = getColumnLabel(fieldName)
  const labelLength = label.length * 14 // 估算字符宽度
  const valueLength = String(value || '').length * 8
  
  return Math.max(labelLength, valueLength, 80)
}

/**
 * 格式化日期
 * @param date 日期字符串或对象
 */
const formatDate = (date: string | Date): string => {
  if (!date) return ''
  
  try {
    const dateObj = typeof date === 'string' ? new Date(date) : date
    if (isNaN(dateObj.getTime())) return String(date)
    
    return dateObj.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  } catch (error) {
    return String(date)
  }
}

/**
 * 格式化数字
 * @param num 数字
 */
const formatNumber = (num: number | string): string => {
  if (num === null || num === undefined || num === '') return ''
  
  const numValue = typeof num === 'string' ? parseFloat(num) : num
  if (isNaN(numValue)) return String(num)
  
  return numValue.toLocaleString('zh-CN')
}

/**
 * 获取状态标签类型
 * @param status 状态值
 */
const getStatusTagType = (status: string): 'success' | 'primary' | 'warning' | 'info' | 'danger' => {
  if (!status) return 'info'
  
  const statusLower = String(status).toLowerCase()
  const statusMap: Record<string, 'success' | 'primary' | 'warning' | 'info' | 'danger'> = {
    'active': 'success',
    'enabled': 'success',
    'success': 'success',
    'completed': 'success',
    'finished': 'success',
    'approved': 'success',
    '激活': 'success',
    '启用': 'success',
    '成功': 'success',
    '完成': 'success',
    '通过': 'success',
    
    'inactive': 'info',
    'disabled': 'info',
    'draft': 'info',
    '禁用': 'info',
    '草稿': 'info',
    '待处理': 'info',
    
    'pending': 'warning',
    'processing': 'warning',
    'waiting': 'warning',
    '处理中': 'warning',
    '等待': 'warning',
    '审核中': 'warning',
    
    'failed': 'danger',
    'error': 'danger',
    'deleted': 'danger',
    'rejected': 'danger',
    '失败': 'danger',
    '错误': 'danger',
    '删除': 'danger',
    '拒绝': 'danger'
  }
  
  return statusMap[statusLower] || 'primary'
}

// 方法
const initializeForm = () => {
  // 重置查询表单
  Object.keys(queryForm).forEach(key => {
    delete queryForm[key]
  })
  
  // 初始化动态条件的默认值
  if (props.packageData?.dynamic_conditions) {
    props.packageData.dynamic_conditions.forEach(condition => {
      if (condition.default_value) {
        queryForm[condition.param_name] = condition.default_value
      }
    })
  }
  
  // 初始化查询选项
  queryOptions.orderField = props.packageData?.order_config?.field || ''
  queryOptions.orderDirection = props.packageData?.order_config?.direction || 'ASC'
  queryOptions.limit = props.packageData?.limit_config || 1000
  
  // 重置查询结果
  queryResults.value = null
  currentPage.value = 1
  pageSize.value = 20
  
  nextTick(() => {
    queryFormRef.value?.clearValidate()
  })
}

const getPlaceholder = (condition: any) => {
  const baseText = `请输入${condition.description || condition.field}`
  
  if (condition.operator === 'LIKE') {
    return `${baseText}（支持模糊搜索）`
  } else if (['IN', 'NOT IN'].includes(condition.operator)) {
    return `${baseText}（多选）`
  } else if (condition.default_value) {
    return `${baseText}（默认: ${condition.default_value}）`
  }
  
  return baseText
}

const getFieldOptions = (fieldName: string) => {
  // 这里可以根据字段名返回预设的选项
  // 实际项目中可能需要从API获取字段的可选值
  return []
}

const executeQuery = async () => {
  if (!props.packageData) return
  
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
      parameters: { ...queryForm },
      order_field: queryOptions.orderField || undefined,
      order_direction: queryOptions.orderDirection,
      limit: queryOptions.limit
      // 移除offset，使用前端分页
    }
    
    const response = await resourcePackageApi.query(props.packageData.id, queryRequest)
    queryResults.value = response
    
    ElMessage.success(`查询成功，共找到 ${response.total} 条记录`)
    
  } catch (error) {
    console.error('查询失败:', error)
    ElMessage.error('查询失败')
  } finally {
    queryLoading.value = false
  }
}

const handleSizeChange = (newSize: number) => {
  pageSize.value = newSize
  currentPage.value = 1
  // 前端分页不需要重新查询，数据会自动更新
}

const handleCurrentChange = (newPage: number) => {
  currentPage.value = newPage
  // 前端分页不需要重新查询，数据会自动更新
}

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
    const exportData = queryResults.value.data.map(row => {
      const newRow: Record<string, any> = {}
      displayFields.value.forEach(field => {
        newRow[field] = typeof row[field] === 'object' ? JSON.stringify(row[field]) : row[field]
      })
      return newRow
    })
    
    // 创建工作表
    const ws = XLSX.utils.json_to_sheet(exportData)
    
    // 添加工作表到工作簿
    XLSX.utils.book_append_sheet(wb, ws, '查询结果')
    
    // 生成文件名
    const fileName = `${props.packageData?.name}_查询结果_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.xlsx`
    
    // 导出文件
    XLSX.writeFile(wb, fileName)
    
    ElMessage.success('导出成功')
    
  } catch (error) {
    if (error !== 'cancel') {
      console.error('导出失败:', error)
      ElMessage.error('导出失败')
    }
  }
}

const handleClose = () => {
  dialogVisible.value = false
}
</script>

<style scoped>
.package-info {
  margin-bottom: 20px;
}

.package-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.package-header h3 {
  margin: 0 0 8px 0;
  color: #303133;
}

.package-meta {
  display: flex;
  gap: 8px;
  align-items: center;
}

.tag-item {
  margin-left: 8px;
}

.locked-conditions {
  margin-top: 16px;
}

.locked-conditions h4 {
  margin: 0 0 12px 0;
  color: #606266;
  font-size: 14px;
  font-weight: 600;
}

.condition-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.condition-tag {
  font-family: 'Courier New', monospace;
}

.query-form,
.query-options,
.query-results {
  margin-bottom: 20px;
}

.section-title {
  font-weight: 600;
  color: #303133;
}

.condition-info {
  margin-top: 4px;
}

.results-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.results-meta {
  display: flex;
  gap: 12px;
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

.dialog-footer {
  text-align: right;
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
</style>