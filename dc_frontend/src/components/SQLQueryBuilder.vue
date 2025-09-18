<template>
  <div class="sql-query-builder">
    <el-card class="query-card">
      <template #header>
        <div class="card-header">
          <span>SQL查询构建器</span>
          <div class="header-actions">
            <el-button @click="clearQuery">
              <el-icon><Delete /></el-icon>
              清空
            </el-button>
            <el-button @click="saveQuery" :disabled="!hasSavePermission">
              <el-icon><Document /></el-icon>
              保存查询
            </el-button>
            <el-button type="primary" @click="executeQuery" :loading="querying" :disabled="!hasQueryPermission">
              <el-icon><CaretRight /></el-icon>
              执行查询
            </el-button>
            <el-button type="success" @click="addToResourcePackage" :disabled="!queryResults.length || !hasQueryPermission">
              <el-icon><FolderAdd /></el-icon>
              添加到资源包
            </el-button>
          </div>
        </div>
      </template>
      
      <div class="query-builder">
        <!-- 数据源选择 -->
        <div class="query-section">
          <h4 class="section-title">数据源</h4>
          <el-row :gutter="20">
            <el-col :span="8">
              <el-form-item label="数据源ID">
                <el-input
                  v-model="queryConfig.datasourceId"
                  placeholder="数据源ID"
                  style="width: 100%"
                  :disabled="true"
                  readonly
                />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="数据库/Schema" v-if="queryConfig.datasourceId && availableSchemas.length > 0">
                <el-select
                  v-model="queryConfig.schema"
                  placeholder="请选择Schema"
                  style="width: 100%"
                  @change="onSchemaChange"
                >
                  <el-option
                    v-for="schema in availableSchemas"
                    :key="schema.name"
                    :label="schema.name"
                    :value="schema.name"
                  />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="数据表/集合" v-if="queryConfig.datasourceId">
                <el-select
                  v-model="queryConfig.table"
                  placeholder="请选择数据表"
                  style="width: 100%"
                  @change="onTableChange"
                >
                  <el-option
                    v-for="table in availableTables"
                    :key="table.name"
                    :label="table.name"
                    :value="table.name"
                  >
                    <div class="table-option">
                      <span class="table-name">{{ table.name }}</span>
                      <span class="table-count">({{ table.rowCount }} 行)</span>
                    </div>
                  </el-option>
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>
        </div>

        <!-- 字段选择 -->
        <div class="query-section" v-if="queryConfig.table">
          <h4 class="section-title">字段选择</h4>
          <div class="fields-selection">
            <div class="field-groups">
              <div class="available-fields">
                <h5>可用字段</h5>
                <div class="fields-list">
                  <div
                    v-for="field in availableFields"
                    :key="field.name"
                    class="field-item"
                    @click="addField(field)"
                  >
                    <el-icon><Plus /></el-icon>
                    <span class="field-name">{{ field.name }}</span>
                    <el-tag :type="getFieldTypeTag(field.type)" size="small">
                      {{ field.type }}
                    </el-tag>
                  </div>
                </div>
              </div>
              
              <div class="selected-fields">
                <h5>已选字段</h5>
                <div class="fields-list">
                  <div
                    v-for="(field, index) in queryConfig.fields"
                    :key="index"
                    class="field-item selected"
                  >
                    <el-icon @click="removeField(index)"><Close /></el-icon>
                    <span class="field-name">{{ field.name }}</span>
                    <el-input
                      v-model="field.alias"
                      placeholder="别名"
                      size="small"
                      style="width: 80px"
                      clearable
                    />
                  </div>
                  <div v-if="queryConfig.fields.length === 0" class="empty-fields">
                    <el-icon><InfoFilled /></el-icon>
                    <span>请从左侧选择字段</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 条件设置 -->
        <div class="query-section" v-if="queryConfig.fields.length > 0">
          <h4 class="section-title">
            条件设置
            <el-button size="small" @click="addCondition">
              <el-icon><Plus /></el-icon>
              添加条件
            </el-button>
          </h4>
          <div class="conditions-list">
            <div
              v-for="(condition, index) in queryConfig.conditions"
              :key="index"
              class="condition-item"
            >
              <el-select
                v-model="condition.logic"
                style="width: 80px"
                size="small"
                v-if="index > 0"
              >
                <el-option label="AND" value="AND" />
                <el-option label="OR" value="OR" />
              </el-select>
              
              <el-select
                v-model="condition.field"
                placeholder="字段"
                style="width: 150px"
                size="small"
              >
                <el-option
                  v-for="field in availableFields"
                  :key="field.name"
                  :label="field.name"
                  :value="field.name"
                />
              </el-select>
              
              <el-select
                v-model="condition.operator"
                placeholder="操作符"
                style="width: 100px"
                size="small"
              >
                <el-option label="=" value="=" />
                <el-option label="!=" value="!=" />
                <el-option label=">" value=">" />
                <el-option label=">=" value=">=" />
                <el-option label="<" value="<" />
                <el-option label="<=" value="<=" />
                <el-option label="LIKE" value="LIKE" />
                <el-option label="IN" value="IN" />
                <el-option label="NOT IN" value="NOT IN" />
                <el-option label="IS NULL" value="IS NULL" />
                <el-option label="IS NOT NULL" value="IS NOT NULL" />
              </el-select>
              
              <el-input
                v-model="condition.value"
                placeholder="值"
                style="width: 150px"
                size="small"
                v-if="!['IS NULL', 'IS NOT NULL'].includes(condition.operator)"
              />
              
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

        <!-- 排序和限制 -->
        <div class="query-section" v-if="queryConfig.fields.length > 0">
          <h4 class="section-title">排序和限制</h4>
          <el-row :gutter="20">
            <el-col :span="8">
              <el-form-item label="排序字段">
                <el-select
                  v-model="queryConfig.orderBy.field"
                  placeholder="选择排序字段"
                  style="width: 100%"
                  clearable
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
            <el-col :span="4">
              <el-form-item label="排序方式">
                <el-select
                  v-model="queryConfig.orderBy.direction"
                  style="width: 100%"
                  :disabled="!queryConfig.orderBy.field"
                >
                  <el-option label="升序" value="ASC" />
                  <el-option label="降序" value="DESC" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="限制条数">
                <el-input-number
                  v-model="queryConfig.limit"
                  :min="1"
                  :max="10000"
                  style="width: 100%"
                  placeholder="最大1万条"
                />
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="偏移量">
                <el-input-number
                  v-model="queryConfig.offset"
                  :min="0"
                  style="width: 100%"
                  placeholder="起始位置"
                />
              </el-form-item>
            </el-col>
          </el-row>
        </div>

        <!-- SQL预览 -->
        <div class="query-section" v-if="queryConfig.fields.length > 0">
          <h4 class="section-title">
            SQL预览
            <el-button size="small" @click="copySQL">
              <el-icon><CopyDocument /></el-icon>
              复制
            </el-button>
          </h4>
          <div class="sql-preview">
            <pre><code>{{ generatedSQL }}</code></pre>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 查询结果 -->
    <div class="query-results-section" v-if="queryResults.length > 0 || querying">
      <el-card class="results-card">
        <template #header>
          <div class="card-header">
            <span>查询结果 ({{ queryResults.length }} 条记录)</span>
            <div class="header-actions">
              <el-button @click="exportResults" :disabled="queryResults.length === 0 || !hasExportPermission">
                <el-icon><Download /></el-icon>
                导出
              </el-button>
              <el-button @click="refreshQuery" :loading="querying">
                <el-icon><Refresh /></el-icon>
                刷新
              </el-button>
            </div>
          </div>
        </template>
        
        <div class="results-content" v-loading="querying">
          <el-table
            :data="queryResults"
            stripe
            border
            style="width: 100%"
            max-height="500"
            v-if="queryResults.length > 0"
          >
            <el-table-column
              v-for="column in resultColumns"
              :key="column.prop"
              :prop="column.prop"
              :label="column.label"
              :width="column.width"
              show-overflow-tooltip
            >
              <template #default="{ row }">
                <span v-if="column.type === 'date'">
                  {{ formatDate(row[column.prop]) }}
                </span>
                <span v-else-if="column.type === 'number'">
                  {{ formatNumber(row[column.prop]) }}
                </span>
                <el-tag v-else-if="column.type === 'status'" :type="getStatusTagType(row[column.prop])">
                  {{ row[column.prop] }}
                </el-tag>
                <span v-else>
                  {{ row[column.prop] }}
                </span>
              </template>
            </el-table-column>
          </el-table>
          
          <div v-if="queryResults.length === 0 && !querying" class="empty-results">
            <el-empty description="暂无查询结果" />
          </div>
        </div>
      </el-card>
    </div>

    <!-- 保存查询对话框 -->
    <el-dialog
      v-model="saveQueryVisible"
      title="保存查询"
      width="500px"
    >
      <el-form :model="saveQueryForm" label-width="80px">
        <el-form-item label="查询名称" required>
          <el-input
            v-model="saveQueryForm.name"
            placeholder="请输入查询名称"
            maxlength="50"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="saveQueryForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入查询描述"
            maxlength="200"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="标签">
          <el-select
            v-model="saveQueryForm.tags"
            multiple
            filterable
            allow-create
            placeholder="请选择或输入标签"
            style="width: 100%"
          >
            <el-option
              v-for="tag in queryTags"
              :key="tag"
              :label="tag"
              :value="tag"
            />
          </el-select>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="saveQueryVisible = false">取消</el-button>
          <el-button type="primary" @click="confirmSaveQuery">
            保存
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 添加到资源包对话框 -->
    <el-dialog
      v-model="resourcePackageVisible"
      title="添加到资源包"
      width="600px"
    >
      <el-form :model="resourcePackageForm" label-width="100px">
        <el-form-item label="资源包名称" required>
          <el-input
            v-model="resourcePackageForm.name"
            placeholder="请输入资源包名称"
            maxlength="50"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="resourcePackageForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入资源包描述"
            maxlength="200"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="数据源">
          <el-input
            :value="`${queryConfig.datasourceId} (${queryConfig.schema || '默认'}.${queryConfig.table})`"
            readonly
            disabled
          />
        </el-form-item>
        <el-form-item label="查询字段">
          <el-tag
            v-for="field in queryConfig.fields"
            :key="field.name"
            style="margin-right: 8px; margin-bottom: 4px"
          >
            {{ field.alias || field.name }}
          </el-tag>
        </el-form-item>
        <el-form-item label="查询条件">
          <div v-if="queryConfig.conditions.length === 0" class="text-gray-500">
            无查询条件
          </div>
          <div v-else>
            <div
              v-for="(condition, index) in queryConfig.conditions"
              :key="index"
              class="condition-preview"
            >
              <span v-if="index > 0" class="logic-text">{{ condition.logic }}</span>
              <span class="condition-text">
                {{ condition.field }} {{ condition.operator }} 
                <span v-if="!['IS NULL', 'IS NOT NULL'].includes(condition.operator)">
                  "{{ condition.value }}"
                </span>
              </span>
            </div>
          </div>
        </el-form-item>
        <el-form-item label="限制条数">
          <el-input-number
            v-model="resourcePackageForm.limitConfig"
            :min="1"
            :max="10000"
            style="width: 200px"
          />
        </el-form-item>
        <el-form-item label="标签">
          <el-select
            v-model="resourcePackageForm.tags"
            multiple
            filterable
            allow-create
            placeholder="请选择或输入标签"
            style="width: 100%"
          >
            <el-option
              v-for="tag in queryTags"
              :key="tag"
              :label="tag"
              :value="tag"
            />
          </el-select>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="resourcePackageVisible = false">取消</el-button>
          <el-button type="primary" @click="confirmAddToResourcePackage" :loading="creatingResourcePackage">
            创建资源包
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted } from 'vue'
import {
  Search,
  Delete,
  Document,
  CaretRight,
  Plus,
  Close,
  InfoFilled,
  CopyDocument,
  Download,
  Refresh,
  FolderAdd
} from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useUserStore } from '@/stores/user'
import { datasourceApi } from '@/api/datasource'
import { getResourceFields } from '@/api/resource'
import { getSQLTemplates } from '@/api/sqlQuery'
import { resourcePackageApi, PackageType } from '@/api/resourcePackage'

// 定义组件属性
interface Props {
  sqlResources?: any[]
  hasQueryPermission?: boolean
  hasExportPermission?: boolean
  hasSavePermission?: boolean
  initialDatasourceId?: number | null
  initialResourceId?: number | null
  initialSchema?: string
  initialTableName?: string
}

// 定义组件事件
interface Emits {
  (e: 'execute-query', config: any): void
  (e: 'save-query', form: any): void
  (e: 'update-query', form: any): void
  (e: 'export-results', results: any[]): void
  (e: 'add-to-resource-package', data: any): void
}

const props = withDefaults(defineProps<Props>(), {
  sqlResources: () => [],
  hasQueryPermission: false,
  hasExportPermission: false,
  hasSavePermission: false,
  initialDatasourceId: null,
  initialResourceId: null,
  initialSchema: '',
  initialTableName: ''
})

const emit = defineEmits<Emits>()

// 用户状态管理
const userStore = useUserStore()

// 响应式数据
const querying = ref(false)
const saveQueryVisible = ref(false)
const resourcePackageVisible = ref(false)
const creatingResourcePackage = ref(false)
const currentTemplateId = ref<number | null>(null) // 当前加载的模板ID

// SQL查询配置
const queryConfig = reactive({
  datasourceId: null as number | null, // 直接使用数据源ID
  resourceId: null as number | null, // 数据资源ID
  schema: '',
  table: '',
  fields: [] as any[],
  conditions: [] as any[],
  orderBy: {
    field: '',
    direction: 'ASC'
  },
  limit: 100,
  offset: 0
})

// 保存查询表单
const saveQueryForm = reactive({
  name: '',
  description: '',
  tags: [] as string[]
})

// 资源包表单
const resourcePackageForm = reactive({
  name: '',
  description: '',
  limitConfig: 1000,
  tags: [] as string[]
})

// 查询结果
const queryResults = ref<any[]>([])
const resultColumns = ref<any[]>([])
const availableSchemas = ref<any[]>([])
const availableTables = ref<any[]>([])
const availableFields = ref<any[]>([])
const queryTags = ref<string[]>(['常用查询', '报表查询', '数据分析', '业务查询'])

/**
 * 判断是否禁用数据源选择
 */
const isResourceSelectionDisabled = computed(() => {
  return props.initialDatasourceId !== null && props.initialDatasourceId !== undefined
})

/**
 * 生成SQL语句
 */
const generatedSQL = computed(() => {
  if (!queryConfig.table || queryConfig.fields.length === 0) {
    return ''
  }
  
  let sql = 'SELECT '
  
  // 字段列表
  const fieldList = queryConfig.fields.map((field: any) => {
    return field.alias && field.alias !== field.name
      ? `${field.name} AS ${field.alias}`
      : field.name
  }).join(', ')
  
  sql += fieldList
  sql += ` FROM ${queryConfig.table}`
  
  // WHERE条件
  if (queryConfig.conditions.length > 0) {
    sql += ' WHERE '
    const conditionList = queryConfig.conditions.map((condition: any, index: number) => {
      let condStr = ''
      if (index > 0) {
        condStr += `${condition.logic} `
      }
      
      if (['IS NULL', 'IS NOT NULL'].includes(condition.operator)) {
        condStr += `${condition.field} ${condition.operator}`
      } else {
        condStr += `${condition.field} ${condition.operator} '${condition.value}'`
      }
      
      return condStr
    }).join(' ')
    sql += conditionList
  }
  
  // ORDER BY
  if (queryConfig.orderBy.field) {
    sql += ` ORDER BY ${queryConfig.orderBy.field} ${queryConfig.orderBy.direction}`
  }
  
  // LIMIT
  if (queryConfig.limit) {
    sql += ` LIMIT ${queryConfig.limit}`
  }
  
  // OFFSET
  if (queryConfig.offset) {
    sql += ` OFFSET ${queryConfig.offset}`
  }
  
  return sql
})

/**
 * 数据源变更处理
 */
const onDatasourceChange = async () => {
  console.log('[onDatasourceChange] 开始处理数据源变更，当前数据源ID:', queryConfig.datasourceId)
  
  queryConfig.schema = ''
  queryConfig.table = ''
  queryConfig.fields = []
  queryConfig.conditions = []
  availableSchemas.value = []
  availableTables.value = []
  availableFields.value = []
  
  console.log('[onDatasourceChange] 已清空所有配置和可用选项')
  
  if (!queryConfig.datasourceId) {
    console.log('[onDatasourceChange] 数据源ID为空，结束处理')
    return
  }
  
  try {
    const datasourceId = queryConfig.datasourceId
    console.log('[onDatasourceChange] 开始获取Schema列表，数据源ID:', datasourceId)
    
    // 先获取Schema列表
    const schemasResponse = await datasourceApi.getDataSourceSchemas(datasourceId)
    console.log('[onDatasourceChange] Schema API响应:', schemasResponse)
    
    if (schemasResponse.data && schemasResponse.data.length > 0) {
      availableSchemas.value = schemasResponse.data
      console.log('[onDatasourceChange] 成功加载Schema列表:', availableSchemas.value)
      
      // 如果有初始Schema或者只有一个Schema，自动选择
      if (props.initialSchema && schemasResponse.data.find(s => s.name === props.initialSchema)) {
        queryConfig.schema = props.initialSchema
        console.log('[onDatasourceChange] 自动选择初始Schema:', props.initialSchema)
      } else if (schemasResponse.data.length === 1) {
        queryConfig.schema = schemasResponse.data[0].name
        console.log('[onDatasourceChange] 自动选择唯一Schema:', queryConfig.schema)
      }
      
      // 如果已选择Schema，加载表列表
      if (queryConfig.schema) {
        console.log('[onDatasourceChange] 开始加载表列表，Schema:', queryConfig.schema)
        await loadTablesForSchema(datasourceId, queryConfig.schema)
      }
    } else {
      console.log('[onDatasourceChange] 无Schema数据，尝试直接获取表列表')
      // 如果没有Schema，尝试直接获取表列表（兼容非关系型数据库）
      const response = await datasourceApi.getDataSourceTables(datasourceId)
      console.log('[onDatasourceChange] 表列表API响应:', response)
      
      if (response.data) {
        availableTables.value = response.data.map(table => ({
          name: table.name,
          type: table.type || 'table',
          schema: table.schema,
          rowCount: 0 // 暂时设为0，后续可以通过其他API获取
        }))
      }
    }
    
    // 注释掉这里的调用，避免重复加载
  // await loadLatestSQLTemplate()
  } catch (error) {
    console.error('获取数据源信息失败:', error)
    ElMessage.error('获取数据源信息失败')
    availableSchemas.value = []
    availableTables.value = []
  }
}

/**
 * 加载当前数据资源的最新SQL模板
 */
const loadLatestSQLTemplate = async () => {
  if (!queryConfig.resourceId) {
    return
  }
  
  try {
    // 获取当前数据资源的SQL模板列表，按ID降序排列获取最新的
    const response = await getSQLTemplates({
      dataResourceId: queryConfig.resourceId,
      isTemplate: true
    })
    
    if (response.data && response.data.length > 0) {
      // 按ID降序排序，获取最新的模板
      const latestTemplate = response.data.sort((a, b) => b.id - a.id)[0]

      console.log('[loadLatestSQLTemplate] 最新模板:', latestTemplate)
      
      // 保存当前模板ID和信息
      currentTemplateId.value = latestTemplate.id
      saveQueryForm.name = latestTemplate.name
      saveQueryForm.description = latestTemplate.description || ''
      saveQueryForm.tags = latestTemplate.tags || []
      
      // 解析SQL模板并填充到查询构建器
      await parseSQLTemplate(latestTemplate.query)
      
      ElMessage.success(`已加载最新的SQL模板: ${latestTemplate.name}`)
    }
  } catch (error) {
    console.error('加载SQL模板失败:', error)
    // 不显示错误消息，因为没有模板是正常情况
  }
}

/**
 * 加载指定Schema下的表列表
 */
const loadTablesForSchema = async (datasourceId: number, schema: string) => {
  console.log('[loadTablesForSchema] 开始加载表列表:', { datasourceId, schema })
  
  try {
    const tablesResponse = await datasourceApi.getDataSourceTablesWithSchema(datasourceId, schema)
    console.log('[loadTablesForSchema] 表列表API响应:', tablesResponse)
    
    if (tablesResponse.data) {
      availableTables.value = tablesResponse.data.map(table => ({
        name: table.name,
        type: table.type || 'table',
        schema: schema,
        rowCount: 0 // 暂时设为0，后续可以通过其他API获取
      }))
      console.log('[loadTablesForSchema] 成功加载表列表:', availableTables.value)
    } else {
      console.log('[loadTablesForSchema] API响应无数据')
      availableTables.value = []
    }
  } catch (error) {
    console.error('[loadTablesForSchema] 获取数据表列表失败:', error)
    ElMessage.error('获取数据表列表失败')
    availableTables.value = []
  }
}

/**
 * Schema变更处理
 */
const onSchemaChange = async () => {
  queryConfig.table = ''
  queryConfig.fields = []
  queryConfig.conditions = []
  availableTables.value = []
  availableFields.value = []
  
  if (!queryConfig.schema || !queryConfig.datasourceId) {
    return
  }
  
  try {
    const datasourceId = queryConfig.datasourceId
    await loadTablesForSchema(datasourceId, queryConfig.schema)
  } catch (error) {
    console.error('Schema变更失败:', error)
    ElMessage.error('Schema变更失败')
  }
}

/**
 * 数据表变更处理
 */
const onTableChange = async () => {
  console.log('🔄 开始表变更处理:', {
    table: queryConfig.table,
    schema: queryConfig.schema,
    datasourceId: queryConfig.datasourceId
  })
  
  queryConfig.fields = []
  queryConfig.conditions = []
  availableFields.value = []
  
  if (!queryConfig.table || !queryConfig.schema) {
    console.log('⚠️ 表名或Schema为空，跳过字段加载')
    return
  }
  
  try {
    // 获取数据源ID
    if (!queryConfig.datasourceId) {
      console.log('❌ 数据源ID为空')
      ElMessage.error('请先设置有效的数据源ID')
      return
    }
    const datasourceId = queryConfig.datasourceId
    
    console.log('🔄 开始获取表字段信息:', {
      datasourceId,
      schema: queryConfig.schema,
      table: queryConfig.table
    })
    
    // 调用数据源API获取表字段信息
    const response = await datasourceApi.getDataSourceTableFields(datasourceId, queryConfig.schema, queryConfig.table)
    console.log('📊 API响应:', response)
    
    if (response.data) {
      availableFields.value = response.data.map(field => ({
        name: field.name,
        type: field.type || 'varchar',
        description: field.comment || ''
      }))
      console.log('✅ 字段信息加载成功:', availableFields.value)
    } else {
      console.log('⚠️ API响应中没有数据')
    }
  } catch (error) {
    console.error('❌ 获取字段信息失败:', error)
    ElMessage.error('获取字段信息失败')
    availableFields.value = []
  }
}

/**
 * 添加字段
 */
const addField = (field: any) => {
  const exists = queryConfig.fields.some((f: any) => f.name === field.name)
  if (!exists) {
    queryConfig.fields.push({ ...field, alias: '' })
  }
}

/**
 * 移除字段
 */
const removeField = (index: number) => {
  queryConfig.fields.splice(index, 1)
}

/**
 * 添加条件
 */
const addCondition = () => {
  queryConfig.conditions.push({
    logic: 'AND',
    field: '',
    operator: '=',
    value: ''
  })
}

/**
 * 移除条件
 */
const removeCondition = (index: number) => {
  queryConfig.conditions.splice(index, 1)
}

/**
 * 清空查询
 */
const clearQuery = () => {
  queryConfig.datasourceId = null
  queryConfig.schema = ''
  queryConfig.table = ''
  queryConfig.fields = []
  queryConfig.conditions = []
  queryConfig.orderBy.field = ''
  queryConfig.orderBy.direction = 'ASC'
  queryConfig.limit = 100
  queryConfig.offset = 0
  availableSchemas.value = []
  availableTables.value = []
  availableFields.value = []
  queryResults.value = []
  resultColumns.value = []
  
  // 清除当前模板ID和保存表单
  currentTemplateId.value = null
  saveQueryForm.name = ''
  saveQueryForm.description = ''
  saveQueryForm.tags = []
}

/**
 * 执行查询
 */
const executeQuery = () => {
  if (queryConfig.fields.length === 0) {
    ElMessage.warning('请至少选择一个字段')
    return
  }
  
  if (!queryConfig.datasourceId) {
    ElMessage.warning('请选择数据源')
    return
  }
  
  if (!queryConfig.table) {
    ElMessage.warning('请选择数据表')
    return
  }
  
  querying.value = true
  
  // 构建查询参数
  const queryParams = {
    datasourceId: queryConfig.datasourceId,
    resourceId: queryConfig.resourceId,
    schema: queryConfig.schema,
    table: queryConfig.table,
    fields: queryConfig.fields.map(field => ({
      name: field.name,
      alias: field.alias || '',
      type: field.type
    })),
    conditions: queryConfig.conditions,
    orderBy: queryConfig.orderBy,
    limit: queryConfig.limit,
    offset: queryConfig.offset,
    sql: generatedSQL.value // 包含生成的SQL语句
  }
  
  console.log('🚀 执行查询，参数:', queryParams)
  
  // 发送查询请求到父组件
  emit('execute-query', queryParams)
}

/**
 * 刷新查询
 */
const refreshQuery = () => {
  executeQuery()
}

/**
 * 保存查询
 */
const saveQuery = () => {
  if (queryConfig.fields.length === 0) {
    ElMessage.warning('请先构建查询条件')
    return
  }
  saveQueryVisible.value = true
}

/**
 * 确认保存查询
 */
const confirmSaveQuery = () => {
  if (!saveQueryForm.name.trim()) {
    ElMessage.warning('请输入查询名称')
    return
  }
  
  const saveData = {
    ...saveQueryForm,
    queryConfig: { ...queryConfig },
    sql: generatedSQL.value,
    datasourceId: queryConfig.datasourceId
  }
  
  // 如果有当前模板ID，则是更新操作
  if (currentTemplateId.value) {
    saveData.id = currentTemplateId.value
    emit('update-query', saveData)
    ElMessage.success('查询模板已更新')
  } else {
    // 否则是新增操作
    emit('save-query', saveData)
    ElMessage.success('查询已保存')
  }
  
  saveQueryVisible.value = false
}

/**
 * 导出结果
 */
const exportResults = () => {
  emit('export-results', queryResults.value)
}

/**
 * 复制SQL
 */
const copySQL = async () => {
  try {
    await navigator.clipboard.writeText(generatedSQL.value)
    ElMessage.success('SQL已复制到剪贴板')
  } catch (err) {
    ElMessage.error('复制失败')
  }
}

/**
 * 解析SQL模板并填充到查询构建器
 * @param sqlQuery SQL查询语句
 */
const parseSQLTemplate = async (sqlQuery: string) => {
  try {
    console.log('🔍 开始解析SQL:', sqlQuery)
    
    // 解析SQL语句并尝试提取表名和字段
    const sql = sqlQuery.toLowerCase().trim()
    console.log('🔍 转换为小写SQL:', sql)
    
    // 简单的SQL解析，提取表名
    const fromMatch = sql.match(/from\s+([\w_]+)/)
    console.log('🔍 表名匹配结果:', fromMatch)
    
    if (fromMatch) {
      queryConfig.table = fromMatch[1]
      console.log('📝 设置表名:', queryConfig.table)
      
      // 如果找到表名，尝试加载该表的字段信息
      console.log('🔄 开始加载表字段信息...')
      try {
        await onTableChange()
        console.log('✅ 表字段信息加载完成')
      } catch (error) {
        console.error('❌ 表字段信息加载失败:', error)
        // 继续执行，不中断解析过程
      }
      
      // 等待字段信息加载完成后再解析字段
      await new Promise(resolve => setTimeout(resolve, 500))
      console.log('📊 当前可用字段数量:', availableFields.value.length)
      console.log('📊 当前可用字段:', availableFields.value)
    }
    
    // 提取字段（简单处理SELECT后的字段）
    console.log('🔍 开始提取字段...')
    const selectMatch = sql.match(/select\s+(.+?)\s+from/)
    console.log('🔍 字段匹配结果:', selectMatch)
    
    if (selectMatch) {
      const fieldsStr = selectMatch[1].trim()
      console.log('📝 提取的字段字符串:', fieldsStr)
      
      if (fieldsStr !== '*') {
        console.log('🔍 开始解析字段名称...')
        const fieldNames = fieldsStr.split(',').map((field: string) => {
          const trimmed = field.trim()
          const parts = trimmed.split(/\s+as\s+/i)
          return {
            name: parts[0],
            alias: parts[1] || '',
            type: 'varchar' // 默认类型，会在字段匹配时更新
          }
        })
        
        console.log('📝 解析的字段名称:', fieldNames)
        console.log('📊 可用字段列表:', availableFields.value.map(f => f.name))
        
        // 匹配已加载的字段信息（使用不区分大小写的匹配）
        console.log('🔍 开始匹配字段...')
        queryConfig.fields = fieldNames.map(field => {
          const availableField = availableFields.value.find(af => 
            af.name.toLowerCase() === field.name.toLowerCase()
          )
          console.log(`🔍 匹配字段 ${field.name}:`, availableField)
          
          const matchedField = {
            name: availableField?.name || field.name, // 使用原始字段名
            alias: field.alias,
            type: availableField?.type || field.type,
            description: availableField?.description || ''
          }
          console.log(`✅ 字段匹配结果:`, matchedField)
          return matchedField
        })
        
        console.log('✅ 最终设置的字段:', queryConfig.fields)
        console.log('✅ 字段数量:', queryConfig.fields.length)
      } else {
        console.log('🔍 检测到SELECT *，不设置具体字段')
      }
    }
    
    // 解析WHERE条件（简单处理）
    const whereMatch = sql.match(/where\s+(.+?)(?:\s+order\s+by|\s+limit|$)/)
    if (whereMatch) {
      const whereClause = whereMatch[1].trim()
      console.log('🔍 WHERE条件:', whereClause)
      // 这里可以进一步解析WHERE条件，暂时简化处理
      queryConfig.conditions = []
    }
    
    // 解析ORDER BY
    const orderMatch = sql.match(/order\s+by\s+([\w_]+)\s+(asc|desc)?/)
    if (orderMatch) {
      queryConfig.orderBy.field = orderMatch[1]
      queryConfig.orderBy.direction = orderMatch[2]?.toUpperCase() || 'ASC'
      console.log('📝 设置排序:', queryConfig.orderBy)
    }
    
    // 解析LIMIT
    const limitMatch = sql.match(/limit\s+(\d+)/)
    if (limitMatch) {
      queryConfig.limit = parseInt(limitMatch[1])
      console.log('📝 设置限制:', queryConfig.limit)
    }
    
    // 解析OFFSET
    const offsetMatch = sql.match(/offset\s+(\d+)/)
    if (offsetMatch) {
      queryConfig.offset = parseInt(offsetMatch[1])
      console.log('📝 设置偏移:', queryConfig.offset)
    }
    
    console.log('✅ SQL解析完成，最终配置:', {
      table: queryConfig.table,
      fields: queryConfig.fields,
      conditions: queryConfig.conditions,
      orderBy: queryConfig.orderBy,
      limit: queryConfig.limit,
      offset: queryConfig.offset
    })
  } catch (error) {
    console.error('❌ 解析SQL模板失败:', error)
  }
}

/**
 * 加载模板
 * @param template 模板数据
 */
const loadTemplate = async (template: any) => {
  try {
    console.log('🔄 开始加载模板:', template)
    
    // 设置数据源和资源ID
    queryConfig.datasourceId = template.datasource_id || null
    queryConfig.resourceId = template.data_resource_id || null
    
    console.log('📝 设置配置:', {
      datasourceId: queryConfig.datasourceId,
      resourceId: queryConfig.resourceId
    })
    
    // 先加载数据源信息
    if (queryConfig.datasourceId) {
      console.log('🔄 开始加载数据源信息...')
      await onDatasourceChange()
      console.log('✅ 数据源信息加载完成')
    }
    
    // 调用SQL解析函数（等待解析完成）
    console.log('🔄 开始解析SQL:', template.query)
    await parseSQLTemplate(template.query)
    console.log('✅ SQL解析完成')
    
    // 额外等待确保所有异步操作完成
    await new Promise(resolve => setTimeout(resolve, 200))
    
    console.log('📊 当前查询配置:', {
      table: queryConfig.table,
      fields: queryConfig.fields,
      conditions: queryConfig.conditions,
      orderBy: queryConfig.orderBy,
      limit: queryConfig.limit
    })
    
    console.log('📊 字段详细信息:', queryConfig.fields.map(f => ({
      name: f.name,
      type: f.type,
      description: f.description
    })))
    
    ElMessage.success(`已加载模板: ${template.name}`)
  } catch (error) {
    console.error('❌ 加载模板失败:', error)
    ElMessage.error('加载模板失败')
  }
}

/**
 * 获取资源类型标签
 */
const getResourceTypeTag = (type: string) => {
  const typeMap: Record<string, string> = {
    'mysql': 'success',
    'postgresql': 'info',
    'oracle': 'warning',
    'sqlserver': 'danger'
  }
  return typeMap[type] || 'info'
}

/**
 * 获取资源类型标签文本
 */
const getResourceTypeLabel = (type: string) => {
  const labelMap: Record<string, string> = {
    'mysql': 'MySQL',
    'postgresql': 'PostgreSQL',
    'oracle': 'Oracle',
    'sqlserver': 'SQL Server'
  }
  return labelMap[type] || type
}

/**
 * 获取字段类型标签
 */
const getFieldTypeTag = (type: string): 'success' | 'primary' | 'warning' | 'info' | 'danger' => {
  const typeMap: Record<string, 'success' | 'primary' | 'warning' | 'info' | 'danger'> = {
    'int': 'success',
    'varchar': 'info',
    'datetime': 'warning',
    'decimal': 'danger',
    'enum': 'primary'
  }
  return typeMap[type] || 'info'
}

/**
 * 格式化日期
 */
const formatDate = (date: string) => {
  if (!date) return ''
  return new Date(date).toLocaleString()
}

/**
 * 格式化数字
 */
const formatNumber = (num: number) => {
  if (num === null || num === undefined) return ''
  return num.toLocaleString()
}

/**
 * 获取状态标签类型
 */
const getStatusTagType = (status: string): 'success' | 'primary' | 'warning' | 'info' | 'danger' => {
  const statusMap: Record<string, 'success' | 'primary' | 'warning' | 'info' | 'danger'> = {
    'active': 'success',
    'inactive': 'info',
    'pending': 'warning',
    'deleted': 'danger'
  }
  return statusMap[status] || 'info'
}

/**
 * 组件挂载时初始化
 */
onMounted(async () => {
  // 如果有初始数据源ID，设置并加载相关数据
  if (props.initialDatasourceId) {
    queryConfig.datasourceId = props.initialDatasourceId
  }
  
  // 如果有初始资源ID，设置资源ID
  if (props.initialResourceId) {
    queryConfig.resourceId = props.initialResourceId
    console.log('🔄 onMounted设置resourceId:', props.initialResourceId)
  }
  
  // 加载数据源相关信息
  if (queryConfig.datasourceId) {
    await onDatasourceChange()
  }
  
  // 设置初始Schema
  if (props.initialSchema) {
    queryConfig.schema = props.initialSchema
    await onSchemaChange()
  }
  
  // 设置初始表名
  if (props.initialTableName) {
    queryConfig.table = props.initialTableName
    await onTableChange()
  }
  
  // resourceId的模板加载由watch监听器处理，避免重复调用
})

// 监听props变化
watch(() => props.initialResourceId, (newVal, oldVal) => {
  if (newVal && newVal !== oldVal && oldVal !== undefined) {
    queryConfig.resourceId = newVal
    console.log('🔄 监听到resourceId变化:', newVal)
    // 当resourceId变化时，不在这里调用loadLatestSQLTemplate，由queryConfig.resourceId的监听器统一处理
  }
}, { immediate: false })

// 监听queryConfig.resourceId变化，处理模板加载
watch(() => queryConfig.resourceId, (newVal, oldVal) => {
  if (newVal && newVal !== oldVal) {
    console.log('🔄 queryConfig.resourceId变化，加载SQL模板:', newVal)
    loadLatestSQLTemplate()
  }
}, { immediate: true })

/**
 * 设置查询结果
 * @param results 查询结果数据
 * @param columns 结果列信息
 */
const setQueryResults = (results: any[], columns: any[]) => {
  queryResults.value = results
  resultColumns.value = columns
  querying.value = false
  
  if (results && results.length > 0) {
    ElMessage.success(`查询成功，共返回 ${results.length} 条记录`)
  } else {
    ElMessage.info('查询完成，未找到匹配的记录')
  }
}

/**
 * 处理查询错误
 * @param error 错误信息
 */
const handleQueryError = (error: string | Error) => {
  querying.value = false
  const errorMessage = typeof error === 'string' ? error : error.message
  ElMessage.error(`查询失败: ${errorMessage}`)
  console.error('❌ 查询执行失败:', error)
}

/**
 * 重置查询状态
 */
const resetQueryState = () => {
  querying.value = false
}

/**
 * 打开添加到资源包对话框
 */
const openAddToResourcePackage = () => {
  if (!queryConfig.table || queryConfig.fields.length === 0) {
    ElMessage.warning('请先配置查询条件')
    return
  }
  
  // 重置表单
  resourcePackageForm.name = ''
  resourcePackageForm.description = ''
  resourcePackageForm.limitConfig = 1000
  resourcePackageForm.tags = []
  
  resourcePackageVisible.value = true
}

/**
 * 确认添加到资源包
 */
const confirmAddToResourcePackage = async () => {
  if (!resourcePackageForm.name.trim()) {
    ElMessage.warning('请输入资源包名称')
    return
  }
  
  try {
    creatingResourcePackage.value = true
    
    // 构建资源包数据
    const packageData = {
      name: resourcePackageForm.name,
      description: resourcePackageForm.description,
      packageType: PackageType.SQL_QUERY,
      datasourceId: queryConfig.datasourceId,
      queryFields: queryConfig.fields.map(f => f.name),
      queryConditions: queryConfig.conditions,
      limitConfig: resourcePackageForm.limitConfig,
      tags: resourcePackageForm.tags,
      sqlQuery: generatedSQL.value
    }
    
    await resourcePackageApi.create(packageData)
    
    ElMessage.success('资源包创建成功')
    resourcePackageVisible.value = false
    
    // 触发事件通知父组件
    emit('add-to-resource-package', packageData)
    
  } catch (error) {
    console.error('创建资源包失败:', error)
    ElMessage.error('创建资源包失败')
  } finally {
    creatingResourcePackage.value = false
  }
}

// 暴露方法给父组件
defineExpose({
  clearQuery,
  executeQuery,
  loadTemplate,
  setQueryResults,
  handleQueryError,
  resetQueryState
})
</script>

<style scoped>
.sql-query-builder {
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

.query-section {
  margin-bottom: 24px;
}

.section-title {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  display: flex;
  align-items: center;
  gap: 8px;
}

.fields-selection {
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  padding: 16px;
}

.field-groups {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.available-fields h5,
.selected-fields h5 {
  margin: 0 0 12px 0;
  font-size: 14px;
  font-weight: 600;
  color: #606266;
}

.fields-list {
  min-height: 200px;
  max-height: 300px;
  overflow-y: auto;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  padding: 8px;
}

.field-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px;
  margin-bottom: 4px;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.field-item:hover {
  background-color: #f5f7fa;
}

.field-item.selected {
  background-color: #e1f3d8;
}

.field-name {
  flex: 1;
  font-size: 14px;
}

.empty-fields {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 40px;
  color: #909399;
  font-size: 14px;
}

.conditions-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.condition-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background-color: #f8f9fa;
  border-radius: 4px;
}

.sql-preview {
  background-color: #f8f9fa;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  padding: 16px;
}

.sql-preview pre {
  margin: 0;
  font-family: 'Courier New', monospace;
  font-size: 14px;
  line-height: 1.5;
  color: #303133;
  white-space: pre-wrap;
  word-break: break-all;
}

.results-card {
  margin-top: 20px;
}

.results-content {
  min-height: 200px;
}

.empty-results {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 200px;
}

.resource-option,
.table-option {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.table-count {
  color: #909399;
  font-size: 12px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
</style>