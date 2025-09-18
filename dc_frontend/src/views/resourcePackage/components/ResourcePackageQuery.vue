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
        
        <!-- 锁定条件展示 -->
        <div v-if="packageData?.locked_conditions?.length" class="locked-conditions">
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
      </el-card>

      <!-- 动态查询条件 -->
      <el-card class="query-form" v-if="packageData?.dynamic_conditions?.length">
        <template #header>
          <span class="section-title">查询条件</span>
        </template>
        
        <el-form
          ref="queryFormRef"
          :model="queryForm"
          :rules="queryRules"
          label-width="120px"
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
      <el-card class="query-options">
        <template #header>
          <span class="section-title">查询选项</span>
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
            :data="queryResults.data"
            stripe
            border
            max-height="400"
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
  if (!queryResults.value?.data?.length) return []
  
  // 如果配置了查询字段，优先显示配置的字段
  if (props.packageData?.base_config?.fields?.length) {
    return props.packageData.base_config.fields
  }
  
  // 否则显示结果中的所有字段
  return Object.keys(queryResults.value.data[0])
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
      limit: queryOptions.limit,
      offset: (currentPage.value - 1) * pageSize.value
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
  executeQuery()
}

const handleCurrentChange = (newPage: number) => {
  currentPage.value = newPage
  executeQuery()
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