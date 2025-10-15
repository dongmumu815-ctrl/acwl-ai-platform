<template>
  <div class="es-query-builder">
    <!-- ES查询构建器头部 -->
    <div class="query-header">
      <h3 class="query-title">
        <el-icon><Search /></el-icon>
        Elasticsearch 查询构建器
      </h3>
      <div class="query-actions">
        <el-button @click="clearQuery" size="small">
          <el-icon><Delete /></el-icon>
          清空
        </el-button>
        <el-button @click="importQuery" size="small">
          <el-icon><Upload /></el-icon>
          导入查询
        </el-button>
        <el-button @click="exportQuery" size="small">
          <el-icon><Download /></el-icon>
          导出查询
        </el-button>
      </div>
    </div>

    <!-- 数据源和索引选择 -->
    <div class="query-section">
      <h4 class="section-title">数据源配置</h4>
      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="ES数据源">
            <el-select
              v-model="queryConfig.datasourceId"
              placeholder="请选择Elasticsearch数据源"
              style="width: 100%"
              @change="onDatasourceChange"
              filterable
            >
              <el-option
                v-for="datasource in esDatasources"
                :key="datasource.id"
                :label="datasource.name"
                :value="datasource.id"
              >
                <div class="datasource-option">
                  <span class="datasource-name">{{ datasource.name }}</span>
                  <el-tag type="success" size="small">ES</el-tag>
                </div>
              </el-option>
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="索引">
            <el-select
              v-model="queryConfig.index"
              placeholder="请选择索引"
              style="width: 100%"
              @change="onIndexChange"
              filterable
              multiple
              collapse-tags
              collapse-tags-tooltip
            >
              <el-option
                v-for="index in availableIndices"
                :key="index.name"
                :label="index.name"
                :value="index.name"
              >
                <div class="index-option">
                  <span class="index-name">{{ index.name }}</span>
                  <span class="index-docs">{{ index.docsCount }} 文档</span>
                </div>
              </el-option>
            </el-select>
          </el-form-item>
        </el-col>
      </el-row>
    </div>

    <!-- 查询类型选择 -->
    <div class="query-section" v-if="queryConfig.index.length > 0">
      <h4 class="section-title">查询类型</h4>
      <el-radio-group v-model="queryConfig.queryType" @change="onQueryTypeChange">
        <el-radio-button label="match">匹配查询</el-radio-button>
        <el-radio-button label="term">精确查询</el-radio-button>
        <el-radio-button label="range">范围查询</el-radio-button>
        <el-radio-button label="bool">布尔查询</el-radio-button>
        <el-radio-button label="wildcard">通配符查询</el-radio-button>
        <el-radio-button label="fuzzy">模糊查询</el-radio-button>
        <el-radio-button label="custom">自定义DSL</el-radio-button>
      </el-radio-group>
    </div>

    <!-- 字段映射显示 -->
    <div class="query-section" v-if="queryConfig.index.length > 0">
      <h4 class="section-title">
        字段映射
        <el-button size="small" @click="refreshFields">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </h4>
      <div class="fields-mapping">
        <el-collapse v-model="activeFieldGroups">
          <el-collapse-item
            v-for="(fields, type) in groupedFields"
            :key="type"
            :title="`${getFieldTypeLabel(type)} (${fields.length})`"
            :name="type"
          >
            <div class="field-list">
              <div
                v-for="field in fields"
                :key="field.name"
                class="field-item"
                @click="addFieldToQuery(field)"
              >
                <el-icon><Plus /></el-icon>
                <span class="field-name">{{ field.name }}</span>
                <el-tag :type="getFieldTypeTag(field.type)" size="small">
                  {{ field.type }}
                </el-tag>
                <span class="field-analyzer" v-if="field.analyzer">
                  分析器: {{ field.analyzer }}
                </span>
              </div>
            </div>
          </el-collapse-item>
        </el-collapse>
      </div>
    </div>

    <!-- 查询条件构建 -->
    <div class="query-section" v-if="queryConfig.queryType !== 'custom'">
      <h4 class="section-title">
        查询条件
        <el-button size="small" @click="addCondition">
          <el-icon><Plus /></el-icon>
          添加条件
        </el-button>
      </h4>
      <div class="conditions-builder">
        <div
          v-for="(condition, index) in queryConfig.conditions"
          :key="index"
          class="condition-item"
        >
          <!-- 逻辑操作符 -->
          <el-select
            v-if="index > 0"
            v-model="condition.logic"
            style="width: 80px"
            size="small"
          >
            <el-option label="AND" value="must" />
            <el-option label="OR" value="should" />
            <el-option label="NOT" value="must_not" />
          </el-select>

          <!-- 字段选择 -->
          <el-select
            v-model="condition.field"
            placeholder="选择字段"
            style="width: 150px"
            size="small"
            filterable
          >
            <el-option
              v-for="field in availableFields"
              :key="field.name"
              :label="field.name"
              :value="field.name"
            >
              <span>{{ field.name }}</span>
              <el-tag :type="getFieldTypeTag(field.type)" size="small" style="margin-left: 8px">
                {{ field.type }}
              </el-tag>
            </el-option>
          </el-select>

          <!-- 查询类型 -->
          <el-select
            v-model="condition.queryType"
            style="width: 120px"
            size="small"
            @change="onConditionTypeChange(condition, index)"
          >
            <el-option label="匹配" value="match" />
            <el-option label="精确" value="term" />
            <el-option label="范围" value="range" />
            <el-option label="存在" value="exists" />
            <el-option label="通配符" value="wildcard" />
            <el-option label="正则" value="regexp" />
          </el-select>

          <!-- 查询值 -->
          <template v-if="condition.queryType === 'range'">
            <el-input
              v-model="condition.value.gte"
              placeholder="最小值"
              style="width: 100px"
              size="small"
            />
            <span style="margin: 0 8px">-</span>
            <el-input
              v-model="condition.value.lte"
              placeholder="最大值"
              style="width: 100px"
              size="small"
            />
          </template>
          <el-input
            v-else-if="condition.queryType !== 'exists'"
            v-model="condition.value"
            placeholder="查询值"
            style="width: 150px"
            size="small"
          />

          <!-- 删除条件 -->
          <el-button
            size="small"
            type="danger"
            @click="removeCondition(index)"
          >
            <el-icon><Delete /></el-icon>
          </el-button>
        </div>
      </div>
    </div>

    <!-- 自定义DSL编辑器 -->
    <div class="query-section" v-if="queryConfig.queryType === 'custom'">
      <h4 class="section-title">
        自定义DSL查询
        <el-button size="small" @click="formatDSL">
          <el-icon><MagicStick /></el-icon>
          格式化
        </el-button>
        <el-button size="small" @click="validateDSL">
          <el-icon><CircleCheck /></el-icon>
          验证
        </el-button>
      </h4>
      <div class="dsl-editor">
        <el-input
          v-model="queryConfig.customDSL"
          type="textarea"
          :rows="12"
          placeholder="请输入Elasticsearch DSL查询语句..."
          class="dsl-textarea"
        />
      </div>
    </div>

    <!-- 聚合查询配置 -->
    <div class="query-section">
      <h4 class="section-title">
        聚合查询
        <el-switch
          v-model="queryConfig.enableAggregation"
          @change="onAggregationToggle"
        />
      </h4>
      <div v-if="queryConfig.enableAggregation" class="aggregation-config">
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="聚合类型">
              <el-select v-model="queryConfig.aggregation.type" style="width: 100%">
                <el-option label="计数" value="terms" />
                <el-option label="求和" value="sum" />
                <el-option label="平均值" value="avg" />
                <el-option label="最大值" value="max" />
                <el-option label="最小值" value="min" />
                <el-option label="日期直方图" value="date_histogram" />
                <el-option label="范围聚合" value="range" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="聚合字段">
              <el-select v-model="queryConfig.aggregation.field" style="width: 100%" filterable>
                <el-option
                  v-for="field in availableFields"
                  :key="field.name"
                  :label="field.name"
                  :value="field.name"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="聚合大小">
              <el-input-number
                v-model="queryConfig.aggregation.size"
                :min="1"
                :max="1000"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>
      </div>
    </div>

    <!-- 查询选项 -->
    <div class="query-section">
      <h4 class="section-title">查询选项</h4>
      <el-row :gutter="20">
        <el-col :span="6">
          <el-form-item label="返回字段">
            <el-select
              v-model="queryConfig.source"
              multiple
              filterable
              placeholder="默认返回所有字段"
              style="width: 100%"
            >
              <el-option
                v-for="field in availableFields"
                :key="field.name"
                :label="field.name"
                :value="field.name"
              />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="6">
          <el-form-item label="排序字段">
            <el-select v-model="queryConfig.sort.field" style="width: 100%" clearable>
              <el-option
                v-for="field in availableFields"
                :key="field.name"
                :label="field.name"
                :value="field.name"
              />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="3">
          <el-form-item label="排序方向">
            <el-select v-model="queryConfig.sort.order" style="width: 100%">
              <el-option label="升序" value="asc" />
              <el-option label="降序" value="desc" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="3">
          <el-form-item label="返回数量">
            <el-input-number
              v-model="queryConfig.size"
              :min="1"
              :max="10000"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
        <el-col :span="3">
          <el-form-item label="偏移量">
            <el-input-number
              v-model="queryConfig.from"
              :min="0"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
        <el-col :span="3">
          <el-form-item label="超时时间">
            <el-input-number
              v-model="queryConfig.timeout"
              :min="1"
              :max="300"
              style="width: 100%"
            />
            <span style="font-size: 12px; color: #999">秒</span>
          </el-form-item>
        </el-col>
      </el-row>
    </div>

    <!-- DSL预览 -->
    <div class="query-section">
      <h4 class="section-title">
        DSL预览
        <el-button size="small" @click="copyDSL">
          <el-icon><CopyDocument /></el-icon>
          复制
        </el-button>
        <el-button size="small" @click="validateGeneratedDSL">
          <el-icon><CircleCheck /></el-icon>
          验证
        </el-button>
      </h4>
      <div class="dsl-preview">
        <pre><code>{{ generatedDSL }}</code></pre>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'

// 接口定义
interface ESField {
  name: string
  type: string
  analyzer?: string
  properties?: Record<string, ESField>
}

interface ESIndex {
  name: string
  docsCount: number
  storeSize: string
}

interface ESDatasource {
  id: number
  name: string
  host: string
  port: number
}

interface QueryCondition {
  logic: string
  field: string
  queryType: string
  value: any
}

// Props定义
interface Props {
  datasourceId?: number
  index?: string[]
  /** 初始数据源ID */
  initialDatasourceId?: number
  /** 初始索引列表 */
  initialIndices?: string[]
}

const props = withDefaults(defineProps<Props>(), {
  datasourceId: 0,
  index: () => [],
  initialDatasourceId: 0,
  initialIndices: () => []
})

// Emits定义
const emit = defineEmits<{
  queryChange: [query: any]
  execute: [query: any]
}>()

// 响应式数据
const activeFieldGroups = ref(['text', 'keyword', 'numeric'])
const esDatasources = ref<ESDatasource[]>([])
const availableIndices = ref<ESIndex[]>([])
const availableFields = ref<ESField[]>([])

// 查询配置
const queryConfig = reactive({
  datasourceId: props.initialDatasourceId || props.datasourceId,
  index: [...(props.initialIndices.length > 0 ? props.initialIndices : props.index)],
  queryType: 'match',
  conditions: [] as QueryCondition[],
  customDSL: '',
  enableAggregation: false,
  aggregation: {
    type: 'terms',
    field: '',
    size: 10
  },
  source: [] as string[],
  sort: {
    field: '',
    order: 'desc'
  },
  size: 100,
  from: 0,
  timeout: 30
})

/**
 * 按类型分组的字段
 */
const groupedFields = computed(() => {
  const groups: Record<string, ESField[]> = {}
  
  availableFields.value.forEach(field => {
    const type = field.type
    if (!groups[type]) {
      groups[type] = []
    }
    groups[type].push(field)
  })
  
  return groups
})

/**
 * 生成的DSL查询
 */
const generatedDSL = computed(() => {
  if (queryConfig.queryType === 'custom') {
    return queryConfig.customDSL
  }
  
  return generateDSLFromConditions()
})

/**
 * 从条件生成DSL查询
 */
function generateDSLFromConditions(): string {
  const query: any = {
    query: {},
    size: queryConfig.size,
    from: queryConfig.from
  }
  
  // 设置返回字段
  if (queryConfig.source.length > 0) {
    query._source = queryConfig.source
  }
  
  // 设置排序
  if (queryConfig.sort.field) {
    query.sort = [{
      [queryConfig.sort.field]: {
        order: queryConfig.sort.order
      }
    }]
  }
  
  // 设置超时
  if (queryConfig.timeout) {
    query.timeout = `${queryConfig.timeout}s`
  }
  
  // 构建查询条件
  if (queryConfig.conditions.length === 0) {
    query.query = { match_all: {} }
  } else if (queryConfig.conditions.length === 1) {
    const condition = queryConfig.conditions[0]
    query.query = buildSingleCondition(condition)
  } else {
    // 多条件布尔查询
    const boolQuery: any = {
      bool: {
        must: [],
        should: [],
        must_not: []
      }
    }
    
    queryConfig.conditions.forEach((condition, index) => {
      const conditionQuery = buildSingleCondition(condition)
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
    
    query.query = boolQuery
  }
  
  // 添加聚合查询
  if (queryConfig.enableAggregation && queryConfig.aggregation.field) {
    query.aggs = {
      aggregation_result: {
        [queryConfig.aggregation.type]: {
          field: queryConfig.aggregation.field,
          size: queryConfig.aggregation.size
        }
      }
    }
  }
  
  return JSON.stringify(query, null, 2)
}

/**
 * 构建单个查询条件
 */
function buildSingleCondition(condition: QueryCondition): any {
  const { field, queryType, value } = condition
  
  switch (queryType) {
    case 'match':
      return { match: { [field]: value } }
    case 'term':
      return { term: { [field]: value } }
    case 'range':
      return { range: { [field]: value } }
    case 'exists':
      return { exists: { field } }
    case 'wildcard':
      return { wildcard: { [field]: value } }
    case 'regexp':
      return { regexp: { [field]: value } }
    default:
      return { match: { [field]: value } }
  }
}

/**
 * 获取字段类型标签
 */
function getFieldTypeTag(type: string): string {
  const tagMap: Record<string, string> = {
    text: 'primary',
    keyword: 'success',
    long: 'warning',
    integer: 'warning',
    short: 'warning',
    byte: 'warning',
    double: 'warning',
    float: 'warning',
    date: 'info',
    boolean: 'danger',
    ip: 'info',
    geo_point: 'info'
  }
  return tagMap[type] || 'info'
}

/**
 * 获取字段类型标签文本
 */
function getFieldTypeLabel(type: string): string {
  const labelMap: Record<string, string> = {
    text: '文本字段',
    keyword: '关键词字段',
    long: '长整型字段',
    integer: '整型字段',
    short: '短整型字段',
    byte: '字节字段',
    double: '双精度字段',
    float: '浮点字段',
    date: '日期字段',
    boolean: '布尔字段',
    ip: 'IP字段',
    geo_point: '地理位置字段'
  }
  return labelMap[type] || type
}

/**
 * 数据源变化处理
 */
function onDatasourceChange() {
  queryConfig.index = []
  availableIndices.value = []
  availableFields.value = []
  
  if (queryConfig.datasourceId) {
    loadIndices()
  }
}

/**
 * 索引变化处理
 */
function onIndexChange() {
  availableFields.value = []
  
  if (queryConfig.index.length > 0) {
    loadFields()
  }
}

/**
 * 查询类型变化处理
 */
function onQueryTypeChange() {
  if (queryConfig.queryType !== 'custom') {
    queryConfig.customDSL = ''
  }
  
  if (queryConfig.queryType !== 'bool') {
    queryConfig.conditions = []
  }
}

/**
 * 条件类型变化处理
 */
function onConditionTypeChange(condition: QueryCondition, index: number) {
  if (condition.queryType === 'range') {
    condition.value = { gte: '', lte: '' }
  } else if (condition.queryType === 'exists') {
    condition.value = ''
  } else {
    condition.value = ''
  }
}

/**
 * 聚合开关切换
 */
function onAggregationToggle() {
  if (!queryConfig.enableAggregation) {
    queryConfig.aggregation = {
      type: 'terms',
      field: '',
      size: 10
    }
  }
}

/**
 * 加载ES数据源列表
 */
async function loadDatasources() {
  try {
    // 这里调用API获取ES数据源
    // const response = await getESDatasources()
    // esDatasources.value = response.data
    
    // 模拟数据
    esDatasources.value = [
      { id: 1, name: 'ES集群-生产环境', host: '192.168.1.100', port: 9200 },
      { id: 2, name: 'ES集群-测试环境', host: '192.168.1.101', port: 9200 }
    ]
  } catch (error) {
    ElMessage.error('加载ES数据源失败')
  }
}

/**
 * 加载索引列表
 */
async function loadIndices() {
  try {
    // 这里调用API获取索引列表
    // const response = await getESIndices(queryConfig.datasourceId)
    // availableIndices.value = response.data
    
    // 模拟数据
    availableIndices.value = [
      { name: 'user_logs', docsCount: 1000000, storeSize: '2.5GB' },
      { name: 'order_data', docsCount: 500000, storeSize: '1.2GB' },
      { name: 'product_info', docsCount: 50000, storeSize: '100MB' }
    ]

    // 确保预选索引出现在选项中
    const existing = new Set(availableIndices.value.map(i => i.name))
    const preselected = Array.isArray(queryConfig.index) ? queryConfig.index : []
    preselected.forEach(name => {
      if (!existing.has(name)) {
        availableIndices.value.push({ name, docsCount: 0, storeSize: '-' })
      }
    })
    
    // 预选索引已确定时，加载字段映射
    if (queryConfig.index.length > 0) {
      await loadFields()
    }
  } catch (error) {
    ElMessage.error('加载索引列表失败')
  }
}

/**
 * 加载字段映射
 */
async function loadFields() {
  try {
    // 这里调用API获取字段映射
    // const response = await getESFieldMapping(queryConfig.datasourceId, queryConfig.index)
    // availableFields.value = response.data
    
    // 模拟数据
    availableFields.value = [
      { name: 'user_id', type: 'keyword' },
      { name: 'username', type: 'text', analyzer: 'standard' },
      { name: 'email', type: 'keyword' },
      { name: 'age', type: 'integer' },
      { name: 'created_at', type: 'date' },
      { name: 'is_active', type: 'boolean' },
      { name: 'score', type: 'float' },
      { name: 'tags', type: 'keyword' },
      { name: 'description', type: 'text', analyzer: 'ik_max_word' }
    ]
  } catch (error) {
    ElMessage.error('加载字段映射失败')
  }
}

/**
 * 刷新字段映射
 */
function refreshFields() {
  if (queryConfig.index.length > 0) {
    loadFields()
  }
}

/**
 * 添加字段到查询
 */
function addFieldToQuery(field: ESField) {
  // 根据字段类型添加合适的查询条件
  const condition: QueryCondition = {
    logic: 'must',
    field: field.name,
    queryType: field.type === 'text' ? 'match' : 'term',
    value: ''
  }
  
  queryConfig.conditions.push(condition)
}

/**
 * 添加查询条件
 */
function addCondition() {
  const condition: QueryCondition = {
    logic: 'must',
    field: '',
    queryType: 'match',
    value: ''
  }
  
  queryConfig.conditions.push(condition)
}

/**
 * 移除查询条件
 */
function removeCondition(index: number) {
  queryConfig.conditions.splice(index, 1)
}

/**
 * 清空查询
 */
function clearQuery() {
  queryConfig.conditions = []
  queryConfig.customDSL = ''
  queryConfig.source = []
  queryConfig.sort.field = ''
  queryConfig.enableAggregation = false
  queryConfig.aggregation = {
    type: 'terms',
    field: '',
    size: 10
  }
}

/**
 * 导入查询
 */
function importQuery() {
  // 实现查询导入功能
  ElMessage.info('查询导入功能开发中...')
}

/**
 * 导出查询
 */
function exportQuery() {
  const queryData = {
    config: queryConfig,
    dsl: generatedDSL.value
  }
  
  const blob = new Blob([JSON.stringify(queryData, null, 2)], {
    type: 'application/json'
  })
  
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `es-query-${Date.now()}.json`
  a.click()
  
  URL.revokeObjectURL(url)
  ElMessage.success('查询已导出')
}

/**
 * 格式化DSL
 */
function formatDSL() {
  try {
    const parsed = JSON.parse(queryConfig.customDSL)
    queryConfig.customDSL = JSON.stringify(parsed, null, 2)
    ElMessage.success('DSL格式化成功')
  } catch (error) {
    ElMessage.error('DSL格式错误，无法格式化')
  }
}

/**
 * 验证DSL
 */
function validateDSL() {
  try {
    JSON.parse(queryConfig.customDSL)
    ElMessage.success('DSL语法正确')
  } catch (error) {
    ElMessage.error('DSL语法错误')
  }
}

/**
 * 验证生成的DSL
 */
function validateGeneratedDSL() {
  try {
    JSON.parse(generatedDSL.value)
    ElMessage.success('生成的DSL语法正确')
  } catch (error) {
    ElMessage.error('生成的DSL语法错误')
  }
}

/**
 * 复制DSL
 */
function copyDSL() {
  navigator.clipboard.writeText(generatedDSL.value).then(() => {
    ElMessage.success('DSL已复制到剪贴板')
  }).catch(() => {
    ElMessage.error('复制失败')
  })
}

// 监听查询配置变化
watch(
  () => queryConfig,
  (newConfig) => {
    emit('queryChange', newConfig)
  },
  { deep: true }
)

// 组件挂载时初始化
onMounted(async () => {
  await loadDatasources()
  
  // 数据源初始化：优先使用 initialDatasourceId
  if (props.initialDatasourceId || props.datasourceId) {
    queryConfig.datasourceId = props.initialDatasourceId || props.datasourceId
    await loadIndices()
  }
  
  // 索引初始化：优先使用 initialIndices
  const preselected = props.initialIndices.length > 0 ? props.initialIndices : props.index
  if (preselected && preselected.length > 0) {
    queryConfig.index = [...preselected]
    // 索引已设置后，保证可选项包含它们，并加载字段
    const existing = new Set(availableIndices.value.map(i => i.name))
    preselected.forEach(name => {
      if (!existing.has(name)) {
        availableIndices.value.push({ name, docsCount: 0, storeSize: '-' })
      }
    })
    await loadFields()
  }
})

// 暴露方法给父组件
defineExpose({
  executeQuery: () => emit('execute', queryConfig),
  getGeneratedDSL: () => generatedDSL.value,
  clearQuery,
  validateDSL: validateGeneratedDSL
})
</script>

<style lang="scss" scoped>
.es-query-builder {
  .query-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    padding-bottom: 16px;
    border-bottom: 1px solid var(--el-border-color-lighter);
    
    .query-title {
      display: flex;
      align-items: center;
      font-size: 18px;
      font-weight: 600;
      color: var(--el-text-color-primary);
      margin: 0;
      
      .el-icon {
        margin-right: 8px;
        color: var(--el-color-primary);
      }
    }
    
    .query-actions {
      display: flex;
      gap: 8px;
    }
  }
  
  .query-section {
    margin-bottom: 24px;
    padding: 16px;
    background: var(--el-bg-color-page);
    border-radius: 8px;
    border: 1px solid var(--el-border-color-lighter);
    
    .section-title {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin: 0 0 16px 0;
      font-size: 16px;
      font-weight: 600;
      color: var(--el-text-color-primary);
    }
  }
  
  .datasource-option,
  .index-option {
    display: flex;
    justify-content: space-between;
    align-items: center;
    width: 100%;
    
    .datasource-name,
    .index-name {
      flex: 1;
    }
    
    .index-docs {
      font-size: 12px;
      color: var(--el-text-color-placeholder);
    }
  }
  
  .fields-mapping {
    .field-list {
      .field-item {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 8px 12px;
        margin-bottom: 4px;
        border-radius: 4px;
        cursor: pointer;
        transition: all 0.2s;
        
        &:hover {
          background: var(--el-color-primary-light-9);
        }
        
        .field-name {
          flex: 1;
          font-size: 14px;
          font-weight: 500;
        }
        
        .field-analyzer {
          font-size: 12px;
          color: var(--el-text-color-placeholder);
        }
        
        .el-icon {
          color: var(--el-color-primary);
        }
      }
    }
  }
  
  .conditions-builder {
    .condition-item {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 8px;
      padding: 12px;
      background: var(--el-bg-color);
      border-radius: 6px;
      border: 1px solid var(--el-border-color-light);
    }
  }
  
  .dsl-editor {
    .dsl-textarea {
      font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
      
      :deep(.el-textarea__inner) {
        font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
        font-size: 14px;
        line-height: 1.5;
      }
    }
  }
  
  .dsl-preview {
    background: var(--el-bg-color-page);
    border: 1px solid var(--el-border-color-light);
    border-radius: 6px;
    padding: 16px;
    
    pre {
      margin: 0;
      font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
      font-size: 14px;
      line-height: 1.5;
      color: var(--el-text-color-primary);
      white-space: pre-wrap;
      word-wrap: break-word;
    }
  }
  
  .aggregation-config {
    padding: 16px;
    background: var(--el-bg-color);
    border-radius: 6px;
    border: 1px solid var(--el-border-color-light);
  }
}

// 响应式设计
@media (max-width: 1200px) {
  .es-query-builder {
    .query-header {
      flex-direction: column;
      gap: 12px;
      align-items: stretch;
      
      .query-actions {
        justify-content: center;
      }
    }
    
    .condition-item {
      flex-wrap: wrap;
      gap: 8px;
      
      .el-select,
      .el-input {
        min-width: 120px;
      }
    }
  }
}

@media (max-width: 768px) {
  .es-query-builder {
    .query-section {
      padding: 12px;
    }
    
    .el-col {
      margin-bottom: 12px;
    }
  }
}
</style>