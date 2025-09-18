<template>
  <div class="es-query-component">
    <!-- ES查询构建器 -->
    <el-card class="query-card">
      <template #header>
        <div class="card-header">
          <span>Elasticsearch查询构建器</span>
          <div class="header-actions">
            <el-button @click="clearESQuery">
              <el-icon><Delete /></el-icon>
              清空
            </el-button>
            <el-button @click="loadQueryTemplate">
              <el-icon><FolderOpened /></el-icon>
              加载模板
            </el-button>
            <el-button @click="saveESQuery" :disabled="!hasSavePermission">
              <el-icon><Document /></el-icon>
              保存查询
            </el-button>
            <el-button type="primary" @click="executeESQuery" :loading="querying" :disabled="!canExecuteQuery">
              <el-icon><CaretRight /></el-icon>
              执行查询
            </el-button>
          </div>
        </div>
      </template>
      
      <div class="es-datasource-selector">
        <el-form-item label="数据源">
          <el-select
            v-model="esQueryConfig.datasourceId"
            placeholder="请选择ES数据源"
            @change="onEsDatasourceChange"
            style="width: 300px"
          >
            <el-option
              v-for="ds in esDatasources"
              :key="ds.id"
              :label="ds.name"
              :value="ds.id"
            />
          </el-select>
        </el-form-item>
      </div>
      
      <ESQueryBuilder
        ref="esQueryBuilderRef"
        :datasource-id="esQueryConfig.datasourceId"
        :available-indices="esQueryConfig.availableIndices"
        :available-fields="esQueryConfig.availableFields"
        :initial-query="esQueryConfig.builderQuery"
        :initial-datasource-id="props.initialDatasourceId"
        :initial-indices="props.initialIndices"
        @query-change="onEsQueryChange"
        @indices-change="onEsIndicesChange"
        @execute="onESQueryExecute"
      />
    </el-card>

    <!-- ES查询结果 -->
    <div class="es-results-section" v-if="esQueryResults.length > 0 || querying">
      <el-card class="results-card">
        <template #header>
          <div class="card-header">
            <span>ES查询结果 ({{ esQueryStats.totalHits }} 条记录，耗时 {{ esQueryStats.took }}ms)</span>
            <div class="header-actions">
              <el-button @click="refreshESQuery">
                <el-icon><Refresh /></el-icon>
                刷新
              </el-button>
              <el-button @click="exportESResults" :disabled="!hasExportPermission">
                <el-icon><Download /></el-icon>
                导出
              </el-button>
            </div>
          </div>
        </template>
        
        <div class="es-results" v-loading="querying">
          <!-- ES聚合结果 -->
          <div class="aggregation-results" v-if="esAggregationResults">
            <h4 class="agg-title">
              <el-icon><PieChart /></el-icon>
              聚合统计结果
            </h4>
            <div class="agg-charts">
              <div v-for="(agg, key) in esAggregationResults" :key="key" class="agg-item">
                <el-card class="agg-card" shadow="hover">
                  <template #header>
                    <div class="agg-header">
                      <span class="agg-name">{{ key }}</span>
                      <el-tag size="small" type="info">{{ getAggregationType(agg) }}</el-tag>
                    </div>
                  </template>
                  
                  <!-- 数值型聚合结果 -->
                  <div v-if="agg.value !== undefined" class="metric-result">
                    <div class="metric-value">{{ formatAggValue(agg.value) }}</div>
                  </div>
                  
                  <!-- 桶型聚合结果 -->
                  <div v-else-if="agg.buckets" class="bucket-results">
                    <div class="bucket-list">
                      <div v-for="bucket in agg.buckets.slice(0, 10)" :key="bucket.key" class="bucket-item">
                        <div class="bucket-info">
                          <span class="bucket-key">{{ bucket.key }}</span>
                          <span class="bucket-count">{{ bucket.doc_count }}</span>
                        </div>
                        <div class="bucket-bar">
                          <div 
                            class="bucket-progress" 
                            :style="{ width: getBucketPercentage(bucket, agg.buckets) + '%' }"
                          ></div>
                        </div>
                      </div>
                      <div v-if="agg.buckets.length > 10" class="more-buckets">
                        <el-text type="info">还有 {{ agg.buckets.length - 10 }} 项...</el-text>
                      </div>
                    </div>
                  </div>
                </el-card>
              </div>
            </div>
          </div>
          
          <!-- ES文档结果 -->
          <div class="documents-results">
            <el-table
              :data="esQueryResults"
              style="width: 100%"
              max-height="600"
              stripe
              border
            >
              <el-table-column
                prop="_index"
                label="索引"
                width="120"
                fixed="left"
              />
              <el-table-column
                prop="_id"
                label="文档ID"
                width="200"
                show-overflow-tooltip
              />
              <el-table-column
                prop="_score"
                label="相关性得分"
                width="120"
                sortable
              >
                <template #default="{ row }">
                  <el-tag size="small" :type="getScoreTagType(row._score)">
                    {{ row._score?.toFixed(3) || 'N/A' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column
                label="文档内容"
                min-width="400"
              >
                <template #default="{ row }">
                  <div class="document-source">
                    <el-collapse>
                      <el-collapse-item :title="`查看文档内容 (${Object.keys(row._source || {}).length} 个字段)`">
                        <div class="source-content">
                          <pre>{{ JSON.stringify(row._source, null, 2) }}</pre>
                        </div>
                      </el-collapse-item>
                    </el-collapse>
                  </div>
                </template>
              </el-table-column>
              <el-table-column
                label="高亮显示"
                width="200"
                v-if="hasHighlight"
              >
                <template #default="{ row }">
                  <div class="highlight-content" v-if="row.highlight">
                    <div v-for="(highlights, field) in row.highlight" :key="field" class="highlight-field">
                      <div class="field-name">{{ field }}:</div>
                      <div v-for="(highlight, index) in highlights" :key="index" class="highlight-text" v-html="highlight"></div>
                    </div>
                  </div>
                  <span v-else class="no-highlight">无高亮</span>
                </template>
              </el-table-column>
            </el-table>
            
            <div v-if="esQueryResults.length === 0 && !querying" class="empty-results">
              <el-empty description="暂无查询结果" />
            </div>
          </div>
          
          <!-- 分页 -->
          <div class="pagination-wrapper" v-if="esQueryStats.totalHits > 0">
            <el-pagination
              v-model:current-page="esQueryConfig.currentPage"
              v-model:page-size="esQueryConfig.pageSize"
              :page-sizes="[10, 20, 50, 100]"
              :total="Math.min(esQueryStats.totalHits, 10000)"
              layout="total, sizes, prev, pager, next, jumper"
              @size-change="onPageSizeChange"
              @current-change="onPageChange"
            />
          </div>
        </div>
      </el-card>
    </div>

    <!-- 保存ES查询对话框 -->
    <el-dialog
      v-model="saveESQueryVisible"
      title="保存ES查询"
      width="600px"
    >
      <el-form :model="saveESQueryForm" label-width="100px">
        <el-form-item label="保存类型" required>
          <el-radio-group v-model="saveESQueryForm.saveType">
            <el-radio label="template">查询模板</el-radio>
            <el-radio label="instance">查询实例</el-radio>
          </el-radio-group>
          <div class="save-type-hint">
            <el-text size="small" type="info">
              查询模板：保存查询结构（字段、排序、聚合等），查询值可在使用时修改<br/>
              查询实例：保存完整查询（包含具体查询值），可直接执行
            </el-text>
          </div>
        </el-form-item>
        <el-form-item label="查询名称" required>
          <el-input
            v-model="saveESQueryForm.name"
            placeholder="请输入查询名称"
            maxlength="50"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="saveESQueryForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入查询描述"
            maxlength="200"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="标签">
          <el-select
            v-model="saveESQueryForm.tags"
            multiple
            filterable
            allow-create
            placeholder="请选择或输入标签"
            style="width: 100%"
          >
            <el-option
              v-for="tag in esQueryTags"
              :key="tag"
              :label="tag"
              :value="tag"
            />
          </el-select>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="saveESQueryVisible = false">取消</el-button>
          <el-button type="primary" @click="confirmSaveESQuery">
            保存
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 加载查询模板对话框 -->
    <el-dialog
      v-model="loadTemplateVisible"
      title="加载查询模板"
      width="800px"
    >
      <div class="template-list">
        <el-table
          :data="queryTemplates"
          @row-click="selectTemplate"
          highlight-current-row
          style="width: 100%"
        >
          <el-table-column prop="name" label="模板名称" width="200" />
          <el-table-column prop="description" label="描述" />
          <el-table-column prop="tags" label="标签" width="150">
            <template #default="{ row }">
              <el-tag
                v-for="tag in row.tags"
                :key="tag"
                size="small"
                style="margin-right: 4px"
              >
                {{ tag }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="isTemplate" label="类型" width="100">
            <template #default="{ row }">
              <el-tag :type="row.isTemplate ? 'success' : 'info'" size="small">
                {{ row.isTemplate ? '模板' : '实例' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120">
            <template #default="{ row }">
              <el-button
                size="small"
                @click.stop="previewTemplate(row)"
              >
                预览
              </el-button>
              <el-button
                size="small"
                type="danger"
                @click.stop="deleteTemplate(row)"
              >
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="loadTemplateVisible = false">取消</el-button>
          <el-button
            type="primary"
            @click="confirmLoadTemplate"
            :disabled="!selectedTemplate"
          >
            加载模板
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 模板预览对话框 -->
    <el-dialog
      v-model="previewTemplateVisible"
      title="查询模板预览"
      width="600px"
    >
      <div class="template-preview">
        <h4>{{ previewingTemplate?.name }}</h4>
        <p><strong>描述：</strong>{{ previewingTemplate?.description || '无' }}</p>
        <p><strong>类型：</strong>{{ previewingTemplate?.isTemplate ? '查询模板' : '查询实例' }}</p>
        <div class="query-content">
          <h5>查询内容：</h5>
          <pre>{{ JSON.stringify(previewingTemplate?.query, null, 2) }}</pre>
        </div>
      </div>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="previewTemplateVisible = false">关闭</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted } from 'vue'
import {
  Delete,
  Document,
  CaretRight,
  Refresh,
  FolderOpened,
  Download,
  PieChart
} from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import ESQueryBuilder from '@/components/ESQueryBuilder.vue'
import { 
  executeESQuery as apiExecuteESQuery, 
  exportESQueryResult, 
  getESDatasources, 
  getESIndices, 
  getESFieldMapping,
  saveESQueryTemplate,
  getESQueryTemplates,
  deleteESQueryTemplate
} from '@/api/esQuery'
import type { ESQueryRequest, ESQueryResponse, ESQueryStats, ESIndex, ESField } from '@/api/esQuery'

// 定义组件属性
interface Props {
  esDatasources?: any[]
  hasESQueryPermission?: boolean
  hasExportPermission?: boolean
  
  hasSavePermission?: boolean
  initialDatasourceId?: number
  initialIndices?: string[]
}

// 定义组件事件
interface Emits {
  (e: 'execute-query', config: any): void
  (e: 'save-query', form: any): void
  (e: 'export-results', results: any[]): void
  (e: 'datasources-loaded', datasources: any[]): void
}

const props = withDefaults(defineProps<Props>(), {
  esDatasources: () => [],
  hasESQueryPermission: false,
  hasExportPermission: false,
  hasSavePermission: false,
  initialDatasourceId: 0,
  initialIndices: () => []
})

const emit = defineEmits<Emits>()

// 响应式数据
const querying = ref(false)
const saveESQueryVisible = ref(false)
const loadTemplateVisible = ref(false)
const previewTemplateVisible = ref(false)
const esQueryBuilderRef = ref()

// ES查询配置
const esQueryConfig = reactive({
  datasourceId: 0,
  index: [] as string[],
  currentPage: 1,
  pageSize: 20,
  availableIndices: [] as string[],
  availableFields: [] as any[],
  builderQuery: null as any
})

// ES查询结果
const esQueryResults = ref<any[]>([])
const esQueryStats = ref<ESQueryStats>({
  totalHits: 0,
  took: 0,
  maxScore: 0,
  shardsInfo: {
    total: 0,
    successful: 0,
    failed: 0
  }
})
const esAggregationResults = ref<any>(null)
const currentESQuery = ref<any>(null)
const queryTemplates = ref<any[]>([])
const selectedTemplate = ref<any>(null)
const previewingTemplate = ref<any>(null)

// 保存ES查询表单
const saveESQueryForm = reactive({
  name: '',
  description: '',
  tags: [] as string[],
  saveType: 'template' as 'template' | 'instance'
})

const esQueryTags = ref<string[]>(['日志分析', '性能监控', '业务统计', '异常检测'])

/**
 * 加载查询模板
 */
const loadQueryTemplate = async () => {
  loadTemplateVisible.value = true
  try {
    const response = await getESQueryTemplates(esQueryConfig.datasourceId)
    queryTemplates.value = response.data || []
  } catch (error) {
    console.error('加载查询模板失败:', error)
    ElMessage.error('加载查询模板失败')
  }
}

/**
 * 选择模板
 */
const selectTemplate = (template: any) => {
  selectedTemplate.value = template
}

/**
 * 预览模板
 */
const previewTemplate = (template: any) => {
  previewingTemplate.value = template
  previewTemplateVisible.value = true
}

/**
 * 删除模板
 */
const deleteTemplate = async (template: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除查询模板 "${template.name}" 吗？`,
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await deleteESQueryTemplate(template.id)
    
    // 从列表中移除
    const index = queryTemplates.value.findIndex(t => t.id === template.id)
    if (index > -1) {
      queryTemplates.value.splice(index, 1)
    }
    
    ElMessage.success('模板删除成功')
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除模板失败:', error)
      ElMessage.error('删除模板失败')
    }
  }
}

/**
 * 确认加载模板
 */
const confirmLoadTemplate = () => {
  if (!selectedTemplate.value) {
    ElMessage.warning('请选择要加载的模板')
    return
  }
  
  // 设置数据源
  if (selectedTemplate.value.queryConfig?.datasourceId) {
    esQueryConfig.datasourceId = selectedTemplate.value.queryConfig.datasourceId
  }
  
  // 设置索引
  if (selectedTemplate.value.queryConfig?.index) {
    esQueryConfig.index = selectedTemplate.value.queryConfig.index
  }
  
  // 设置查询条件
  if (selectedTemplate.value.query) {
    esQueryConfig.builderQuery = selectedTemplate.value.query
    currentESQuery.value = selectedTemplate.value.query
    
    // 通知查询构建器更新
    if (esQueryBuilderRef.value) {
      esQueryBuilderRef.value.loadQuery(selectedTemplate.value.query)
    }
  }
  
  loadTemplateVisible.value = false
  selectedTemplate.value = null
  
  ElMessage.success('模板加载成功')
}

/**
 * 组件初始化
 */
onMounted(async () => {
  // 如果传入了初始数据源ID，设置为当前选中的数据源
  if (props.initialDatasourceId && props.initialDatasourceId > 0) {
    esQueryConfig.datasourceId = props.initialDatasourceId
    // 自动加载该数据源的索引
    await onEsDatasourceChange()
  }
  
  // 如果没有传入数据源列表，尝试从API加载
  if (props.esDatasources.length === 0) {
    await loadESDatasources()
  }
})

/**
 * 加载ES数据源列表
 */
const loadESDatasources = async () => {
  try {
    const response = await getESDatasources()
    // 转换数据格式，将后端的 datasource_id 字段映射为前端的 id 字段
    const datasources = response.data.map(item => ({
      ...item,
      id: item.datasource_id || item.id // 字段映射，优先使用datasource_id
    }))
    // 通过emit通知父组件更新数据源列表
    emit('datasources-loaded', datasources)
  } catch (error) {
    console.error('加载ES数据源失败:', error)
    ElMessage.error('加载ES数据源失败')
  }
}

/**
 * 是否有高亮显示
 */
const hasHighlight = computed(() => {
  return esQueryResults.value.some(result => result.highlight)
})

/**
 * 是否可以执行查询
 */
const canExecuteQuery = computed(() => {
  // 检查是否选择了数据源
  if (!esQueryConfig.datasourceId) {
    return false
  }
  
  // 检查是否选择了索引
  if (!esQueryConfig.index || esQueryConfig.index.length === 0) {
    return false
  }
  
  // 检查是否有可用字段（表示已经加载了字段映射）
  if (!esQueryConfig.availableFields || esQueryConfig.availableFields.length === 0) {
    return false
  }
  
  return true
})

/**
 * ES数据源变更处理
 */
const onEsDatasourceChange = async () => {
  if (!esQueryConfig.datasourceId) {
    esQueryConfig.availableIndices = []
    esQueryConfig.availableFields = []
    return
  }
  
  try {
    // 获取可用索引
    const response = await getESIndices(esQueryConfig.datasourceId)
    esQueryConfig.availableIndices = response.data.map((index: ESIndex) => index.name)
    
    // 清空字段列表
    esQueryConfig.availableFields = []
  } catch (error) {
    console.error('获取ES索引失败:', error)
    ElMessage.error('获取ES索引失败')
  }
}

/**
 * 构建ES查询条件
 */
const buildESCondition = (condition: any) => {
  const { field, operator, value } = condition
  
  switch (operator) {
    case 'equals':
      return { term: { [field]: value } }
    case 'not_equals':
      return { bool: { must_not: [{ term: { [field]: value } }] } }
    case 'contains':
      return { wildcard: { [field]: `*${value}*` } }
    case 'not_contains':
      return { bool: { must_not: [{ wildcard: { [field]: `*${value}*` } }] } }
    case 'starts_with':
      return { prefix: { [field]: value } }
    case 'ends_with':
      return { wildcard: { [field]: `*${value}` } }
    case 'greater_than':
      return { range: { [field]: { gt: value } } }
    case 'greater_than_or_equal':
      return { range: { [field]: { gte: value } } }
    case 'less_than':
      return { range: { [field]: { lt: value } } }
    case 'less_than_or_equal':
      return { range: { [field]: { lte: value } } }
    case 'between':
      return { range: { [field]: { gte: value[0], lte: value[1] } } }
    case 'in':
      return { terms: { [field]: Array.isArray(value) ? value : [value] } }
    case 'not_in':
      return { bool: { must_not: [{ terms: { [field]: Array.isArray(value) ? value : [value] } }] } }
    case 'exists':
      return { exists: { field } }
    case 'not_exists':
      return { bool: { must_not: [{ exists: { field } }] } }
    case 'match':
      return { match: { [field]: value } }
    case 'match_phrase':
      return { match_phrase: { [field]: value } }
    case 'regexp':
      return { regexp: { [field]: value } }
    default:
      return { term: { [field]: value } }
  }
}

/**
 * ES查询变更处理
 */
const onEsQueryChange = (query: any) => {
  // 防止递归更新
  if (JSON.stringify(currentESQuery.value) === JSON.stringify(query)) {
    return
  }
  
  esQueryConfig.builderQuery = query
  currentESQuery.value = query
}

/**
 * ES索引变更处理
 */
const onEsIndicesChange = async (indices: string[]) => {
  esQueryConfig.index = indices
  
  if (indices.length > 0 && esQueryConfig.datasourceId) {
    try {
      // 获取字段映射
      const response = await getESFieldMapping(esQueryConfig.datasourceId, [indices[0]])
      esQueryConfig.availableFields = response.data.fields
    } catch (error) {
      console.error('获取ES字段映射失败:', error)
      ElMessage.error('获取ES字段映射失败')
    }
  } else {
    esQueryConfig.availableFields = []
  }
}

/**
 * 执行ES查询
 */
const executeESQuery = async () => {
  if (!esQueryConfig.datasourceId) {
    ElMessage.warning('请选择ES数据源')
    return
  }
  
  if (!currentESQuery.value) {
    ElMessage.warning('请构建查询条件')
    return
  }
  
  querying.value = true
  
  try {
    // 构建标准的ES查询DSL
    let esQuery = { match_all: {} }
    let esSource: string[] = []
    let esSort: any[] = []
    let esAggs: any = {}
    
    if (currentESQuery.value) {
      if (currentESQuery.value.type === 'dsl') {
        // DSL查询：直接解析JSON
        try {
          const parsedDSL = JSON.parse(currentESQuery.value.query)
          esQuery = parsedDSL.query || { match_all: {} }
          esSource = parsedDSL._source || []
          esSort = parsedDSL.sort || []
          esAggs = parsedDSL.aggs || {}
        } catch (error) {
          console.error('DSL解析失败:', error)
          ElMessage.error('DSL格式错误')
          return
        }
      } else if (currentESQuery.value.type === 'visual') {
        // 可视化查询：转换为ES DSL
        const visualQuery = currentESQuery.value.query
        esSource = visualQuery.fields || []
        
        // 构建查询条件
        if (visualQuery.conditions && visualQuery.conditions.length > 0) {
          if (visualQuery.conditions.length === 1) {
            const condition = visualQuery.conditions[0]
            esQuery = buildESCondition(condition)
          } else {
            // 多条件布尔查询
            const boolQuery: any = {
              bool: {
                must: [],
                should: [],
                must_not: []
              }
            }
            
            visualQuery.conditions.forEach((condition: any, index: number) => {
              const conditionQuery = buildESCondition(condition)
              const logic = index === 0 ? 'must' : condition.logic
              
              if (logic === 'must') {
                boolQuery.bool.must.push(conditionQuery)
              } else if (logic === 'should') {
                boolQuery.bool.should.push(conditionQuery)
              } else if (logic === 'must_not') {
                boolQuery.bool.must_not.push(conditionQuery)
              }
            })
            
            // 清理空数组
            Object.keys(boolQuery.bool).forEach(key => {
              if (boolQuery.bool[key].length === 0) {
                delete boolQuery.bool[key]
              }
            })
            
            esQuery = boolQuery
          }
        }
        
        // 构建排序
        if (visualQuery.sort && visualQuery.sort.length > 0) {
          esSort = visualQuery.sort.map((s: any) => ({
            [s.field]: { order: s.order }
          }))
        }
        
        // 构建聚合
        if (visualQuery.aggregations && visualQuery.aggregations.length > 0) {
          visualQuery.aggregations.forEach((agg: any) => {
            esAggs[agg.name] = {
              [agg.type]: {
                field: agg.field,
                ...agg.params
              }
            }
          })
        }
      }
    }
    
    const queryRequest: ESQueryRequest = {
      datasourceId: esQueryConfig.datasourceId,
      index: esQueryConfig.index,
      query: esQuery,
      source: esSource,
      size: esQueryConfig.pageSize,
      from: (esQueryConfig.currentPage - 1) * esQueryConfig.pageSize,
      sort: esSort,
      aggs: esAggs,
      highlight: {}
    }
    
    const response = await apiExecuteESQuery(queryRequest)
    
    esQueryResults.value = response.data.hits?.hits || []
    esQueryStats.value = response.stats
    esAggregationResults.value = response.data.aggregations
    
    emit('execute-query', queryRequest)
    
    ElMessage.success(`查询完成，共找到 ${response.stats.totalHits} 条记录`)
  } catch (error) {
    console.error('ES查询失败:', error)
    ElMessage.error('ES查询失败')
  } finally {
    querying.value = false
  }
}

/**
 * ES查询构建器执行事件
 */
const onESQueryExecute = () => {
  executeESQuery()
}

/**
 * 刷新ES查询
 */
const refreshESQuery = () => {
  executeESQuery()
}

/**
 * 清空ES查询
 */
const clearESQuery = () => {
  esQueryConfig.datasourceId = 0
  esQueryConfig.index = []
  esQueryConfig.currentPage = 1
  esQueryConfig.pageSize = 20
  esQueryConfig.availableIndices = []
  esQueryConfig.availableFields = []
  esQueryConfig.builderQuery = null
  
  esQueryResults.value = []
  esAggregationResults.value = null
  currentESQuery.value = null
  
  if (esQueryBuilderRef.value) {
    esQueryBuilderRef.value.clearQuery()
  }
}

/**
 * 保存ES查询
 */
const saveESQuery = () => {
  if (!currentESQuery.value) {
    ElMessage.warning('请先构建查询条件')
    return
  }
  saveESQueryVisible.value = true
}

/**
 * 创建查询模板（移除具体查询值，保留结构）
 */
const createQueryTemplate = (query: any) => {
  if (!query) return null
  
  const template = JSON.parse(JSON.stringify(query)) // 深拷贝
  
  if (template.type === 'visual' && template.query) {
    // 处理可视化查询模板
    const visualQuery = template.query
    
    // 清空查询条件的具体值，保留结构
    if (visualQuery.conditions) {
      visualQuery.conditions = visualQuery.conditions.map((condition: any) => ({
        logic: condition.logic,
        field: condition.field,
        operator: condition.operator,
        value: getDefaultValueForOperator(condition.operator) // 设置默认值
      }))
    }
    
    // 保留字段选择、排序、聚合等结构配置
    // indices, fields, sort, aggregations, from, size 保持不变
  } else if (template.type === 'dsl' && template.query) {
    // 处理DSL查询模板
    template.query = createDSLTemplate(template.query)
  }
  
  return template
}

/**
 * 根据操作符获取默认值
 */
const getDefaultValueForOperator = (operator: string) => {
  switch (operator) {
    case 'term':
    case 'match':
    case 'prefix':
    case 'wildcard':
      return ''
    case 'range':
      return { gte: '', lte: '' }
    case 'exists':
      return true
    default:
      return ''
  }
}

/**
 * 创建DSL查询模板
 */
const createDSLTemplate = (dslQuery: any) => {
  // 对于DSL查询，可以移除具体的查询值，保留查询结构
  // 这里简化处理，实际可以根据需要进行更复杂的模板化
  const template = JSON.parse(JSON.stringify(dslQuery))
  
  // 递归处理查询对象，移除具体值
  const processQuery = (obj: any): any => {
    if (typeof obj !== 'object' || obj === null) {
      return obj
    }
    
    const result: any = {}
    for (const [key, value] of Object.entries(obj)) {
      if (key === 'term' || key === 'match' || key === 'match_phrase') {
        // 保留查询结构，清空具体值
        result[key] = typeof value === 'object' ? 
          Object.keys(value as object).reduce((acc, field) => {
            acc[field] = ''
            return acc
          }, {} as any) : ''
      } else if (key === 'range') {
        // 保留范围查询结构
        result[key] = typeof value === 'object' ?
          Object.keys(value as object).reduce((acc, field) => {
            acc[field] = { gte: '', lte: '' }
            return acc
          }, {} as any) : value
      } else {
        result[key] = processQuery(value)
      }
    }
    return result
  }
  
  return processQuery(template)
}

/**
 * 确认保存ES查询
 */
const confirmSaveESQuery = async () => {
  if (!saveESQueryForm.name.trim()) {
    ElMessage.warning('请输入查询名称')
    return
  }
  
  if (!esQueryConfig.datasourceId) {
    ElMessage.warning('请先选择数据源')
    return
  }
  
  try {
    let queryToSave = currentESQuery.value
    
    // 如果保存为模板，需要移除具体的查询值，只保留结构
    if (saveESQueryForm.saveType === 'template') {
      queryToSave = createQueryTemplate(currentESQuery.value)
    }
    
    // 调用API保存查询模板
    const templateData = {
      name: saveESQueryForm.name,
      description: saveESQueryForm.description,
      datasourceId: esQueryConfig.datasourceId,
      indices: esQueryConfig.index,
      query: queryToSave,
      tags: saveESQueryForm.tags,
      isTemplate: saveESQueryForm.saveType === 'template'
    }
    
    await saveESQueryTemplate(templateData)
    
    saveESQueryVisible.value = false
    ElMessage.success(`ES${saveESQueryForm.saveType === 'template' ? '查询模板' : '查询实例'}已保存`)
    
    // 清空表单
    Object.assign(saveESQueryForm, {
      name: '',
      description: '',
      tags: [],
      saveType: 'template'
    })
    
  } catch (error) {
    console.error('保存查询失败:', error)
    ElMessage.error('保存查询失败，请重试')
  }
}

/**
 * 导出ES结果
 */
const exportESResults = async () => {
  if (esQueryResults.value.length === 0) {
    ElMessage.warning('没有可导出的数据')
    return
  }
  
  try {
    const queryRequest: ESQueryRequest = {
      datasourceId: esQueryConfig.datasourceId,
      index: esQueryConfig.index,
      query: currentESQuery.value?.query || { match_all: {} },
      source: currentESQuery.value?._source || [],
      size: Math.min(esQueryStats.value.totalHits, 10000), // 最多导出1万条
      from: 0,
      sort: currentESQuery.value?.sort || []
    }
    
    await exportESQueryResult(queryRequest)
    ElMessage.success('导出任务已提交，请稍后查看下载文件')
  } catch (error) {
    console.error('导出ES结果失败:', error)
    ElMessage.error('导出失败')
  }
}

/**
 * 页面大小变更
 */
const onPageSizeChange = (size: number) => {
  esQueryConfig.pageSize = size
  esQueryConfig.currentPage = 1
  executeESQuery()
}

/**
 * 页面变更
 */
const onPageChange = (page: number) => {
  esQueryConfig.currentPage = page
  executeESQuery()
}

/**
 * 获取聚合类型
 */
const getAggregationType = (agg: any) => {
  if (agg.value !== undefined) {
    return '指标聚合'
  } else if (agg.buckets) {
    return '桶聚合'
  }
  return '未知类型'
}

/**
 * 格式化聚合值
 */
const formatAggValue = (value: number) => {
  if (typeof value !== 'number') return value
  
  if (value > 1000000) {
    return (value / 1000000).toFixed(2) + 'M'
  } else if (value > 1000) {
    return (value / 1000).toFixed(2) + 'K'
  }
  return value.toLocaleString()
}

/**
 * 获取桶百分比
 */
const getBucketPercentage = (bucket: any, allBuckets: any[]) => {
  const maxCount = Math.max(...allBuckets.map(b => b.doc_count))
  return (bucket.doc_count / maxCount) * 100
}

/**
 * 获取得分标签类型
 */
const getScoreTagType = (score: number) => {
  if (!score) return 'info'
  if (score >= 1.0) return 'success'
  if (score >= 0.5) return 'warning'
  return 'danger'
}

// 暴露方法给父组件
defineExpose({
  clearESQuery,
  executeESQuery,
  setESQueryResults: (results: any[], stats: ESQueryStats, aggregations: any) => {
    esQueryResults.value = results
    esQueryStats.value = stats
    esAggregationResults.value = aggregations
    querying.value = false
  }
})
</script>

<style scoped>
.es-query-component {
  width: 100%;
}

.query-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.es-datasource-selector {
  margin-bottom: 20px;
}

.results-card {
  margin-top: 20px;
}

.es-results {
  min-height: 200px;
}

.aggregation-results {
  margin-bottom: 24px;
}

.agg-title {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  display: flex;
  align-items: center;
  gap: 8px;
}

.agg-charts {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 16px;
}

.agg-card {
  height: 200px;
}

.agg-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.agg-name {
  font-weight: 600;
  color: #303133;
}

.metric-result {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 120px;
}

.metric-value {
  font-size: 32px;
  font-weight: bold;
  color: #409eff;
}

.bucket-results {
  height: 120px;
  overflow-y: auto;
}

.bucket-item {
  display: flex;
  flex-direction: column;
  margin-bottom: 8px;
}

.bucket-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.bucket-key {
  font-size: 14px;
  color: #303133;
  max-width: 150px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.bucket-count {
  font-size: 12px;
  color: #909399;
  font-weight: 600;
}

.bucket-bar {
  height: 4px;
  background-color: #f5f7fa;
  border-radius: 2px;
  overflow: hidden;
}

.bucket-progress {
  height: 100%;
  background-color: #409eff;
  transition: width 0.3s ease;
}

.more-buckets {
  text-align: center;
  padding: 8px;
  color: #909399;
  font-size: 12px;
}

.documents-results {
  margin-bottom: 20px;
}

.document-source {
  max-width: 400px;
}

.source-content {
  max-height: 300px;
  overflow-y: auto;
  background-color: #f8f9fa;
  padding: 12px;
  border-radius: 4px;
}

.source-content pre {
  margin: 0;
  font-family: 'Courier New', monospace;
  font-size: 12px;
  line-height: 1.4;
  color: #303133;
  white-space: pre-wrap;
  word-break: break-all;
}

.highlight-content {
  max-width: 200px;
}

.highlight-field {
  margin-bottom: 8px;
}

.field-name {
  font-size: 12px;
  font-weight: 600;
  color: #606266;
  margin-bottom: 4px;
}

.highlight-text {
  font-size: 12px;
  line-height: 1.4;
  margin-bottom: 2px;
}

.highlight-text :deep(em) {
  background-color: #fff2cc;
  font-style: normal;
  font-weight: bold;
  color: #e6a23c;
}

.no-highlight {
  color: #c0c4cc;
  font-size: 12px;
}

.empty-results {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 200px;
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.save-type-hint {
  margin-top: 8px;
}

.template-list {
  max-height: 400px;
  overflow-y: auto;
}

.template-preview {
  max-height: 500px;
  overflow-y: auto;
}

.template-preview h4 {
  margin: 0 0 16px 0;
  color: #303133;
}

.template-preview p {
  margin: 8px 0;
  color: #606266;
}

.query-content {
  margin-top: 16px;
}

.query-content h5 {
  margin: 0 0 8px 0;
  color: #303133;
}

.query-content pre {
  background-color: #f8f9fa;
  padding: 12px;
  border-radius: 4px;
  font-size: 12px;
  line-height: 1.4;
  max-height: 300px;
  overflow-y: auto;
  border: 1px solid #e4e7ed;
}
</style>