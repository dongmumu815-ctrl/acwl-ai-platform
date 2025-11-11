<template>
  <div class="sql-package-query-panel">
    <!-- 查询参数表单 -->
    <el-card class="query-form-card">
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
            v-for="(paramValue, paramName) in (props.packageData?.dynamic_params || {})"
            :key="paramName"
            :span="12"
          >
            <el-form-item
              :label="getConditionLabel(String(paramName))"
              :prop="String(paramName)"
            >
              <!-- 根据参数类型显示不同的输入组件 -->
              <template v-if="typeof paramValue === 'boolean'">
                <el-switch
                  v-model="queryForm[String(paramName)]"
                  active-text="是"
                  inactive-text="否"
                  @focus="markFieldTouched(String(paramName))"
                  @change="markFieldTouched(String(paramName))"
                />
              </template>
              <template v-else-if="typeof paramValue === 'number'">
                <el-input-number
                  v-model="queryForm[String(paramName)]"
                  :placeholder="`请输入${getConditionLabel(String(paramName))}`"
                  style="width: 100%"
                  @focus="markFieldTouched(String(paramName))"
                  @input="markFieldTouched(String(paramName))"
                />
              </template>
              <template v-else>
                <el-input
                  v-model="queryForm[String(paramName)]"
                  :placeholder="`请输入${getConditionLabel(String(paramName))}`"
                  @focus="markFieldTouched(String(paramName))"
                  @input="markFieldTouched(String(paramName))"
                />
              </template>

              <div class="condition-info" v-if="getConditionInfo(String(paramName))">
                <el-text size="small" type="info">
                  {{ getConditionInfo(String(paramName)) }}
                </el-text>
              </div>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
    </el-card>

    <!-- 查询结果 -->
    <el-card class="query-results-card" v-if="queryResults">
      <template #header>
        <div class="results-header">
          <span class="card-title">查询结果</span>
          <div class="results-meta">
            <el-text type="info">
              共 {{ queryResults?.total_count || 0 }} 条记录，
              耗时 {{ queryResults?.execution_time || 0 }}ms
            </el-text>
            <!-- 新增：全字段搜索 -->
            <el-input v-model="globalKeyword" size="small" placeholder="按所有字段搜索" clearable :prefix-icon="Search" style="width: 240px" />
            <el-button 
              type="primary" 
              size="small" 
              @click="exportResults" 
              :disabled="!queryResults?.data?.length"
            >
              <el-icon><Download /></el-icon>
              导出结果
            </el-button>
          </div>
        </div>
      </template>

      <div v-if="queryResults?.data?.length">
        <!-- 数据表格 -->
        <el-table
          :data="processedData"
          stripe
          border
          max-height="500"
          style="width: 100%"
          @sort-change="onSortChange"
          @row-click="openRowDetail"
        >
          <el-table-column
            v-for="(field, index) in displayFields"
            :key="field"
            :prop="index.toString()"
            :label="field"
            :min-width="120"
            show-overflow-tooltip
            sortable="custom"
          >
            <template #default="{ row }">
              <span v-if="typeof row[index] === 'object'">{{ JSON.stringify(row[index]) }}</span>
              <span v-else>{{ mapTypeLabel(row[index]) }}</span>
            </template>
          </el-table-column>
        </el-table>

        <!-- 新增：行详情弹窗 -->
        <el-dialog v-model="detailVisible" title="数据详情" width="600px">
          <el-descriptions :column="1" border>
            <el-descriptions-item v-for="(field, idx) in displayFields" :key="field" :label="field">
              <!-- 如果是PDF字段且有值，显示为可点击链接 -->
              <template v-if="field === 'pdf_url' && selectedRow?.[idx] && selectedRow?.[idx] !== 'null'">
                <a 
                  :href="selectedRow[idx]" 
                  target="_blank" 
                  class="pdf-link"
                  style="color: #409EFF; text-decoration: none; cursor: pointer;"
                >
                  查看PDF文档
                </a>
              </template>
              <!-- 其他字段正常显示 -->
              <template v-else>
                <span v-if="typeof selectedRow?.[idx] === 'object'">{{ JSON.stringify(selectedRow?.[idx], null, 2) }}</span>
                <span v-else>{{ mapTypeLabel(selectedRow?.[idx]) }}</span>
              </template>
            </el-descriptions-item>
          </el-descriptions>
          <template #footer>
            <span class="dialog-footer">
              <el-button @click="detailVisible = false">关闭</el-button>
              <!-- 注释掉打开全文按钮
              <el-button
                v-if="displayFields.includes('pdf_url') && selectedRow && selectedRow[displayFields.indexOf('pdf_url')] && selectedRow[displayFields.indexOf('pdf_url')] !== 'null'"
                type="primary"
                @click="openPdf"
              >
                打开全文
              </el-button>
              -->
            </span>
          </template>
        </el-dialog>

        <!-- 注释掉PDF预览弹窗
        <el-dialog v-model="pdfDialogVisible" title="全文预览" width="80%">
          <PdfViewer :src="pdfUrl || ''" />
        </el-dialog>
        -->

        <!-- 分页 -->
        <div class="pagination-wrapper">
          <el-pagination
            v-model:current-page="currentPage"
            v-model:page-size="pageSize"
            :page-sizes="[10, 20, 50, 100]"
            :total="queryResults?.total_count || 0"
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
  
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, nextTick } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Search, Download } from '@element-plus/icons-vue'
import * as XLSX from 'xlsx'
import PdfViewer from '@/components/PdfViewer.vue'
import { 
  resourcePackageApi, 
  type ResourcePackage, 
  type ResourcePackageQueryRequest,
  type ResourcePackageQueryResponse
} from '@/api/resourcePackage'

// Props
interface ExtendedResourcePackage extends ResourcePackage {
  template_conditions?: any[]
  dynamic_params?: Record<string, any>
}

const props = defineProps<{
  packageData: ExtendedResourcePackage | null
}>()

// 响应式数据
const queryFormRef = ref<FormInstance>()
const queryLoading = ref(false)
const queryResults = ref<ResourcePackageQueryResponse | null>(null)
const currentPage = ref(1)
const pageSize = ref(20)
// 新增：全字段搜索关键词
const globalKeyword = ref('')
// 新增：排序状态
const sortState = ref<{ index: number | null; order: 'ascending' | 'descending' | null }>({ index: null, order: null })

// 查询表单数据
const queryForm = reactive<Record<string, any>>({})

// 跟踪用户是否主动操作过每个输入框
const fieldTouched = reactive<Record<string, boolean>>({})

/**
 * 表单验证规则
 */
const queryRules = computed(() => {
  const rules: FormRules = {}
  const conditions = props.packageData?.template_conditions || []
  conditions.forEach((condition: any) => {
    if (!condition.locked) {
      const fieldRules: any[] = []
      if (condition.required) {
        fieldRules.push({
          required: true,
          message: `请输入${condition.label || condition.name}`,
          trigger: 'blur'
        })
      }
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
  return rules
})

/**
 * 计算属性
 */
const displayFields = computed(() => {
  return queryResults.value?.columns || []
})

const processedData = computed(() => {
  const rows = queryResults.value?.data || []
  // 过滤
  const kw = globalKeyword.value.trim().toLowerCase()
  let filtered = kw
    ? rows.filter((row: any[]) => row.some((cell: any) => String(cell ?? '').toLowerCase().includes(kw)))
    : rows
  // 排序
  const { index, order } = sortState.value
  if (index !== null && order) {
    filtered = [...filtered].sort((a: any[], b: any[]) => {
      const va = a[index]
      const vb = b[index]
      // 数字优先比较，其次字符串自然排序
      const na = typeof va === 'number' ? va : Number.isFinite(Number(va)) ? Number(va) : null
      const nb = typeof vb === 'number' ? vb : Number.isFinite(Number(vb)) ? Number(vb) : null
      let cmp = 0
      if (na !== null && nb !== null) {
        cmp = na - nb
      } else {
        cmp = String(mapTypeLabel(va ?? '')).localeCompare(String(mapTypeLabel(vb ?? '')), 'zh-CN', { numeric: true, sensitivity: 'base' })
      }
      return order === 'ascending' ? cmp : -cmp
    })
  }
  return filtered
})

const paginatedData = computed(() => {
  if (!queryResults.value?.data?.length) return []
  return queryResults.value.data
})

/**
 * 获取条件标签
 */
const getConditionLabel = (paramName: string) => {
  if (!props.packageData?.template_conditions) return paramName
  const condition = props.packageData.template_conditions.find((c: any) => c.name === paramName)
  return condition?.label || paramName
}

/**
 * 获取条件信息
 */
const getConditionInfo = (paramName: string) => {
  if (!props.packageData?.template_conditions) return ''
  const condition = props.packageData.template_conditions.find((c: any) => c.name === paramName)
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
const markFieldTouched = (fieldName: string) => {
  fieldTouched[fieldName] = true
}

const initializeForm = () => {
  // 重置查询表单
  Object.keys(queryForm).forEach(key => {
    delete queryForm[key]
  })
  // 重置字段操作状态
  Object.keys(fieldTouched).forEach(key => {
    delete fieldTouched[key]
  })
  // 设置默认值
  const params = props.packageData?.dynamic_params || {}
  Object.keys(params).forEach((name) => {
    const defaultVal = (params as any)[name]
    // 只处理未锁定的条件，若有模板条件
    const cond = props.packageData?.template_conditions?.find((c: any) => c.name === name)
    if (!cond || !cond.locked) {
      queryForm[name] = defaultVal ?? (cond?.type === 'number' ? null : '')
    }
  })
  // 重置查询结果
  queryResults.value = null
  currentPage.value = 1
  nextTick(() => {
    queryFormRef.value?.clearValidate()
  })
}

const resetForm = () => {
  queryFormRef.value?.resetFields()
  initializeForm()
}

const handleUserQuery = async () => {
  currentPage.value = 1
  await executeQuery()
}

const executeQuery = async () => {
  if (!props.packageData) {
    ElMessage.error('资源包数据未加载')
    return
  }
  if (queryFormRef.value) {
    try {
      await queryFormRef.value.validate()
    } catch (error) {
      return
    }
  }
  try {
    queryLoading.value = true
    // 过滤参数：只包含用户主动操作过的字段或非空值
    const filteredParams: Record<string, any> = {}
    Object.keys(queryForm).forEach(key => {
      if (fieldTouched[key] || (queryForm[key] !== '' && queryForm[key] !== null && queryForm[key] !== undefined)) {
        filteredParams[key] = queryForm[key]
      }
    })
    const queryRequest: ResourcePackageQueryRequest = {
      dynamic_params: filteredParams,
      limit: pageSize.value,
      offset: (currentPage.value - 1) * pageSize.value
    }
    const response = await resourcePackageApi.secureQuery(props.packageData.id, queryRequest)
    if (response && response.data) {
      queryResults.value = {
        success: response.data.success ?? true,
        data: response.data.data || [],
        columns: response.data.columns || [],
        total_count: response.data.total_count || 0,
        execution_time: response.data.execution_time || 0,
        query_id: response.data.query_id,
        generated_query: response.data.generated_query,
        error_message: response.data.error_message
      } as any
    } else {
      queryResults.value = response as any
    }
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

const handleSizeChange = (newSize: number) => {
  pageSize.value = newSize
  currentPage.value = 1
  if (queryResults.value) {
    executeQuery()
  }
}

const handleCurrentChange = (newPage: number) => {
  currentPage.value = newPage
  if (queryResults.value) {
    executeQuery()
  }
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
    const wb = XLSX.utils.book_new()
    const exportData = queryResults.value.data.map((row: any[]) => {
      const newRow: Record<string, any> = {}
      displayFields.value.forEach((field: string, idx: number) => {
        const cell = row[idx]
        newRow[field] = typeof cell === 'object' ? JSON.stringify(cell) : cell
      })
      return newRow
    })
    const ws = XLSX.utils.json_to_sheet(exportData)
    XLSX.utils.book_append_sheet(wb, ws, '查询结果')
    const fileName = `${props.packageData?.name || '资源包查询'}_${new Date().toISOString().slice(0, 10)}.xlsx`
    XLSX.writeFile(wb, fileName)
    ElMessage.success('导出成功')
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('导出失败:', error)
      ElMessage.error('导出失败')
    }
  }
}

// 初始化与监听
// 表格排序事件
const onSortChange = (payload: { prop: string; order: 'ascending' | 'descending' | null }) => {
  const idx = payload?.prop ? Number(payload.prop) : null
  sortState.value = { index: Number.isFinite(idx) ? idx : null, order: payload.order || null }
}

// 行详情弹窗
const detailVisible = ref(false)
const selectedRow = ref<any[] | null>(null)
const pdfDialogVisible = ref(false)
const pdfUrl = ref<string | null>(null)

const openRowDetail = (row: any[]) => {
  selectedRow.value = row
  detailVisible.value = true
}

const openPdf = () => {
  const idx = displayFields.value.indexOf('pdf_url')
  const val = idx >= 0 ? selectedRow.value?.[idx] : null
  const url = val ? String(val) : ''
  if (url && url !== 'null') {
    pdfUrl.value = url
    pdfDialogVisible.value = true
  } else {
    ElMessage.warning('未找到有效的 pdf_url 字段')
  }
}

// 英文出版物类型到中文的映射（与 ES 面板保持一致）
const typeLabelMap: Record<string, string> = {
  BOOK: '图书',
  JOURNAL_ARTICLE: '期刊文章',
  CONFERENCE_PAPER: '会议论文',
  REPORT: '报告',
  THESIS: '学位论文',
  STANDARD: '标准',
  PATENT: '专利',
  OTHER: '其他'
}

const mapTypeLabel = (val: any): string => {
  const key = String(val ?? '').toUpperCase()
  return typeLabelMap[key] || String(val ?? '')
}

watch(() => props.packageData, (newVal) => {
  if (newVal) {
    initializeForm()
  }
}, { immediate: true })

</script>

<style scoped>
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
.query-actions {
  display: flex;
  gap: 12px;
}
.condition-info { margin-top: 4px; }
.results-header { display: flex; justify-content: space-between; align-items: center; }
.results-meta { display: flex; gap: 16px; align-items: center; }
.pagination-wrapper { margin-top: 16px; text-align: center; }
.no-data { text-align: center; padding: 40px; }
</style>