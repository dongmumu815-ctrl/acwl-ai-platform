<template>
  <el-dialog
    v-model="dialogVisible"
    :title="isEdit ? '编辑资源包' : '创建资源包'"
    width="80%"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="120px"
      v-loading="loading"
    >
      <!-- 基本信息 -->
      <el-card class="form-section">
        <template #header>
          <span class="section-title">基本信息</span>
        </template>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="资源包名称" prop="name">
              <el-input v-model="form.name" placeholder="请输入资源包名称" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="资源包类型" prop="type">
              <el-select v-model="form.type" placeholder="选择资源包类型" style="width: 100%" @change="handleTypeChange">
                <el-option label="SQL查询" value="sql" />
                <el-option label="Elasticsearch" value="elasticsearch" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="数据源" prop="datasource_id">
              <el-select
                v-model="form.datasource_id"
                placeholder="选择数据源"
                style="width: 100%"
                @change="handleDatasourceChange"
              >
                <el-option
                  v-for="ds in filteredDatasources"
                  :key="ds.id"
                  :label="ds.name"
                  :value="ds.id"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="状态">
              <el-switch v-model="form.is_active" active-text="启用" inactive-text="禁用" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-form-item label="描述">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            placeholder="请输入资源包描述"
          />
        </el-form-item>
        
        <el-form-item label="标签">
          <el-select
            v-model="form.tags"
            multiple
            filterable
            allow-create
            placeholder="选择或创建标签"
            style="width: 100%"
          >
            <el-option
              v-for="tag in availableTags"
              :key="tag"
              :label="tag"
              :value="tag"
            />
          </el-select>
        </el-form-item>
      </el-card>

      <!-- 数据配置 -->
      <el-card class="form-section">
        <template #header>
          <span class="section-title">数据配置</span>
        </template>
        
        <el-row :gutter="20" v-if="form.type === 'sql'">
          <el-col :span="12">
            <el-form-item label="数据库/Schema" prop="base_config.schema">
              <el-select
                v-model="form.base_config.schema"
                placeholder="选择数据库/Schema"
                style="width: 100%"
                @change="handleSchemaChange"
              >
                <el-option
                  v-for="schema in schemas"
                  :key="schema"
                  :label="schema"
                  :value="schema"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="数据表" prop="base_config.table">
              <el-select
                v-model="form.base_config.table"
                placeholder="选择数据表"
                style="width: 100%"
                @change="handleTableChange"
              >
                <el-option
                  v-for="table in tables"
                  :key="table"
                  :label="table"
                  :value="table"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="20" v-else>
          <el-col :span="24">
            <el-form-item label="索引名称" prop="base_config.schema">
              <el-input v-model="form.base_config.schema" placeholder="请输入Elasticsearch索引名称" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-form-item label="查询字段" prop="base_config.fields">
          <el-select
            v-model="form.base_config.fields"
            multiple
            placeholder="选择查询字段"
            style="width: 100%"
          >
            <el-option
              v-for="field in availableFields"
              :key="field.name"
              :label="`${field.name} (${field.type})`"
              :value="field.name"
            />
          </el-select>
        </el-form-item>
      </el-card>

      <!-- 查询条件 -->
      <el-card class="form-section">
        <template #header>
          <div class="section-header">
            <span class="section-title">查询条件</span>
            <el-button type="primary" size="small" @click="addLockedCondition">
              <el-icon><Plus /></el-icon>
              添加锁定条件
            </el-button>
          </div>
        </template>
        
        <!-- 锁定条件 -->
        <div class="condition-section">
          <h4>锁定条件 <el-text type="info" size="small">(固定不变的查询条件)</el-text></h4>
          <div v-if="form.locked_conditions.length === 0" class="empty-condition">
            <el-text type="info">暂无锁定条件</el-text>
          </div>
          <div v-else>
            <div
              v-for="(condition, index) in form.locked_conditions"
              :key="index"
              class="condition-item"
            >
              <el-row :gutter="10" align="middle">
                <el-col :span="4">
                  <el-select v-model="condition.field" placeholder="选择字段">
                    <el-option
                      v-for="field in availableFields"
                      :key="field.name"
                      :label="field.name"
                      :value="field.name"
                    />
                  </el-select>
                </el-col>
                <el-col :span="3">
                  <el-select v-model="condition.operator" placeholder="操作符">
                    <el-option label="等于" value="=" />
                    <el-option label="不等于" value="!=" />
                    <el-option label="大于" value=">" />
                    <el-option label="大于等于" value=">=" />
                    <el-option label="小于" value="<" />
                    <el-option label="小于等于" value="<=" />
                    <el-option label="包含" value="LIKE" />
                    <el-option label="在列表中" value="IN" />
                    <el-option label="不在列表中" value="NOT IN" />
                    <el-option label="为空" value="IS NULL" />
                    <el-option label="不为空" value="IS NOT NULL" />
                  </el-select>
                </el-col>
                <el-col :span="4" v-if="!['IS NULL', 'IS NOT NULL'].includes(condition.operator)">
                  <el-input v-model="condition.value" placeholder="值" />
                </el-col>
                <el-col :span="3">
                  <el-select v-model="condition.logic" placeholder="逻辑">
                    <el-option label="AND" value="AND" />
                    <el-option label="OR" value="OR" />
                  </el-select>
                </el-col>
                <el-col :span="6">
                  <el-input v-model="condition.description" placeholder="条件描述" />
                </el-col>
                <el-col :span="2">
                  <el-button type="danger" size="small" @click="removeLockedCondition(index)">
                    <el-icon><Delete /></el-icon>
                  </el-button>
                </el-col>
              </el-row>
            </div>
          </div>
        </div>
        
        <!-- 动态条件 -->
        <div class="condition-section">
          <div class="section-header">
            <h4>动态条件 <el-text type="info" size="small">(可在查询时动态设置的条件)</el-text></h4>
            <el-button type="success" size="small" @click="addDynamicCondition">
              <el-icon><Plus /></el-icon>
              添加动态条件
            </el-button>
          </div>
          <div v-if="form.dynamic_conditions.length === 0" class="empty-condition">
            <el-text type="info">暂无动态条件</el-text>
          </div>
          <div v-else>
            <div
              v-for="(condition, index) in form.dynamic_conditions"
              :key="index"
              class="condition-item dynamic-condition"
            >
              <el-row :gutter="10" align="middle">
                <el-col :span="3">
                  <el-select v-model="condition.field" placeholder="选择字段">
                    <el-option
                      v-for="field in availableFields"
                      :key="field.name"
                      :label="field.name"
                      :value="field.name"
                    />
                  </el-select>
                </el-col>
                <el-col :span="3">
                  <el-select v-model="condition.operator" placeholder="操作符">
                    <el-option label="等于" value="=" />
                    <el-option label="不等于" value="!=" />
                    <el-option label="大于" value=">" />
                    <el-option label="大于等于" value=">=" />
                    <el-option label="小于" value="<" />
                    <el-option label="小于等于" value="<=" />
                    <el-option label="包含" value="LIKE" />
                    <el-option label="在列表中" value="IN" />
                    <el-option label="不在列表中" value="NOT IN" />
                  </el-select>
                </el-col>
                <el-col :span="3">
                  <el-input v-model="condition.param_name" placeholder="参数名称" />
                </el-col>
                <el-col :span="3">
                  <el-input v-model="condition.default_value" placeholder="默认值" />
                </el-col>
                <el-col :span="2">
                  <el-select v-model="condition.logic" placeholder="逻辑">
                    <el-option label="AND" value="AND" />
                    <el-option label="OR" value="OR" />
                  </el-select>
                </el-col>
                <el-col :span="2">
                  <el-checkbox v-model="condition.required">必填</el-checkbox>
                </el-col>
                <el-col :span="4">
                  <el-input v-model="condition.description" placeholder="条件描述" />
                </el-col>
                <el-col :span="2">
                  <el-button type="danger" size="small" @click="removeDynamicCondition(index)">
                    <el-icon><Delete /></el-icon>
                  </el-button>
                </el-col>
              </el-row>
            </div>
          </div>
        </div>
      </el-card>

      <!-- 排序和限制 -->
      <el-card class="form-section">
        <template #header>
          <span class="section-title">排序和限制</span>
        </template>
        
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="排序字段">
              <el-select v-model="form.order_config.field" placeholder="选择排序字段" clearable>
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
            <el-form-item label="排序方向">
              <el-select v-model="form.order_config.direction" placeholder="选择排序方向">
                <el-option label="升序" value="ASC" />
                <el-option label="降序" value="DESC" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="默认限制条数" prop="limit_config">
              <el-input-number
                v-model="form.limit_config"
                :min="1"
                :max="10000"
                placeholder="默认查询条数"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>
      </el-card>
    </el-form>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="loading">
          {{ isEdit ? '更新' : '创建' }}
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, watch, computed, nextTick } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { Plus, Delete } from '@element-plus/icons-vue'
import {
  resourcePackageApi,
  type ResourcePackage,
  type ResourcePackageCreateRequest,
  type ResourcePackageUpdateRequest,
  PackageType,
  ConditionOperator,
  LogicOperator,
  SortDirection
} from '@/api/resourcePackage'
import { datasourceApi, type Datasource } from '@/api/datasource'
import { dataResourceApi } from '@/api/dataResource'

// Props
interface Props {
  visible: boolean
  packageData?: ResourcePackage | null
  isEdit: boolean
}

const props = withDefaults(defineProps<Props>(), {
  visible: false,
  packageData: null,
  isEdit: false
})

// Emits
const emit = defineEmits<{
  'update:visible': [value: boolean]
  success: []
}>()

// 响应式数据
const formRef = ref<FormInstance>()
const loading = ref(false)
const dialogVisible = ref(false)
const datasources = ref<Datasource[]>([])
const schemas = ref<string[]>([])
const tables = ref<string[]>([])
const availableFields = ref<any[]>([])
const availableTags = ref<string[]>(['数据分析', '报表', '监控', '业务', '测试'])

// 表单数据
const form = reactive({
  name: '',
  description: '',
  type: 'sql' as PackageType,
  datasource_id: '',
  is_active: true,
  tags: [] as string[],
  base_config: {
    schema: '',
    table: '',
    fields: [] as string[]
  },
  locked_conditions: [] as any[],
  dynamic_conditions: [] as any[],
  order_config: {
    field: '',
    direction: 'ASC' as SortDirection
  },
  limit_config: 1000
})

// 表单验证规则
const rules: FormRules = {
  name: [
    { required: true, message: '请输入资源包名称', trigger: 'blur' },
    { min: 2, max: 255, message: '名称长度在 2 到 255 个字符', trigger: 'blur' }
  ],
  type: [
    { required: true, message: '请选择资源包类型', trigger: 'change' }
  ],
  datasource_id: [
    { required: true, message: '请选择数据源', trigger: 'change' }
  ],
  'base_config.schema': [
    { required: true, message: '请选择数据库/Schema或输入索引名称', trigger: 'change' }
  ],
  'base_config.table': [
    { required: true, message: '请选择数据表', trigger: 'change' }
  ],
  'base_config.fields': [
    { required: true, message: '请至少选择一个查询字段', trigger: 'change' }
  ],
  limit_config: [
    { required: true, message: '请输入默认限制条数', trigger: 'blur' },
    { type: 'number', min: 1, max: 10000, message: '限制条数在 1 到 10000 之间', trigger: 'blur' }
  ]
}

// 计算属性
const filteredDatasources = computed(() => {
  if (form.type === 'sql') {
    return datasources.value.filter(ds => ds.type !== 'elasticsearch')
  } else {
    return datasources.value.filter(ds => ds.type === 'elasticsearch')
  }
})

// 监听器
watch(() => props.visible, (newVal) => {
  dialogVisible.value = newVal
  if (newVal) {
    loadDatasources()
    if (props.isEdit && props.packageData) {
      loadFormData()
    } else {
      resetForm()
    }
  }
})

watch(dialogVisible, (newVal) => {
  emit('update:visible', newVal)
})

// 方法
const loadDatasources = async () => {
  try {
    const response = await datasourceApi.list()
    datasources.value = response.items || []
  } catch (error) {
    console.error('加载数据源失败:', error)
  }
}

const loadFormData = () => {
  if (!props.packageData) return
  
  const data = props.packageData
  Object.assign(form, {
    name: data.name,
    description: data.description || '',
    type: data.type,
    datasource_id: data.datasource_id,
    is_active: data.is_active,
    tags: data.tags?.map(tag => tag.tag_name) || [],
    base_config: {
      schema: data.base_config.schema || '',
      table: data.base_config.table || '',
      fields: data.base_config.fields || []
    },
    locked_conditions: data.locked_conditions || [],
    dynamic_conditions: data.dynamic_conditions || [],
    order_config: {
      field: data.order_config?.field || '',
      direction: data.order_config?.direction || 'ASC'
    },
    limit_config: data.limit_config || 1000
  })
  
  // 加载相关数据
  if (form.datasource_id) {
    handleDatasourceChange(form.datasource_id)
  }
}

const resetForm = () => {
  Object.assign(form, {
    name: '',
    description: '',
    type: 'sql',
    datasource_id: '',
    is_active: true,
    tags: [],
    base_config: {
      schema: '',
      table: '',
      fields: []
    },
    locked_conditions: [],
    dynamic_conditions: [],
    order_config: {
      field: '',
      direction: 'ASC'
    },
    limit_config: 1000
  })
  
  schemas.value = []
  tables.value = []
  availableFields.value = []
  
  nextTick(() => {
    formRef.value?.clearValidate()
  })
}

const handleTypeChange = () => {
  form.datasource_id = ''
  form.base_config.schema = ''
  form.base_config.table = ''
  form.base_config.fields = []
  schemas.value = []
  tables.value = []
  availableFields.value = []
}

const handleDatasourceChange = async (datasourceId: number | string) => {
  if (!datasourceId) return
  
  try {
    if (form.type === 'sql') {
      // 加载数据库列表
      const response = await dataResourceApi.getSchemas(Number(datasourceId))
      schemas.value = response
    }
    
    form.base_config.schema = ''
    form.base_config.table = ''
    form.base_config.fields = []
    tables.value = []
    availableFields.value = []
  } catch (error) {
    console.error('加载数据库列表失败:', error)
  }
}

const handleSchemaChange = async () => {
  if (!form.datasource_id || !form.base_config.schema) return
  
  try {
    if (form.type === 'sql') {
      // 加载表列表
      const response = await dataResourceApi.getTables(Number(form.datasource_id), form.base_config.schema)
      tables.value = response
    }
    
    form.base_config.table = ''
    form.base_config.fields = []
    availableFields.value = []
  } catch (error) {
    console.error('加载表列表失败:', error)
  }
}

const handleTableChange = async () => {
  if (!form.datasource_id || !form.base_config.schema || !form.base_config.table) return
  
  try {
    if (form.type === 'sql') {
      // 加载字段列表
      const response = await dataResourceApi.getColumns(Number(form.datasource_id), form.base_config.schema, form.base_config.table)
      availableFields.value = response
    }
    
    form.base_config.fields = []
  } catch (error) {
    console.error('加载字段列表失败:', error)
  }
}

const addLockedCondition = () => {
  form.locked_conditions.push({
    field: '',
    operator: ConditionOperator.EQ,
    value: '',
    logic: LogicOperator.AND,
    description: ''
  })
}

const removeLockedCondition = (index: number) => {
  form.locked_conditions.splice(index, 1)
}

const addDynamicCondition = () => {
  form.dynamic_conditions.push({
    field: '',
    operator: ConditionOperator.EQ,
    param_name: '',
    default_value: '',
    required: false,
    logic: LogicOperator.AND,
    description: '',
    param_type: 'string'
  })
}

const removeDynamicCondition = (index: number) => {
  form.dynamic_conditions.splice(index, 1)
}

const handleSubmit = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    
    loading.value = true
    
    const submitData = {
      ...form,
      datasource_id: Number(form.datasource_id)
    }
    
    if (props.isEdit && props.packageData) {
      await resourcePackageApi.update(props.packageData.id, submitData as ResourcePackageUpdateRequest)
      ElMessage.success('更新成功')
    } else {
      await resourcePackageApi.create(submitData as ResourcePackageCreateRequest)
      ElMessage.success('创建成功')
    }
    
    emit('success')
    
  } catch (error) {
    console.error('提交失败:', error)
    ElMessage.error('提交失败')
  } finally {
    loading.value = false
  }
}

const handleClose = () => {
  dialogVisible.value = false
}
</script>

<style scoped>
.form-section {
  margin-bottom: 20px;
}

.section-title {
  font-weight: 600;
  color: #303133;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.condition-section {
  margin-bottom: 20px;
}

.condition-section h4 {
  margin: 0 0 12px 0;
  color: #606266;
  font-size: 14px;
  font-weight: 600;
}

.condition-item {
  margin-bottom: 12px;
  padding: 12px;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  background-color: #fafafa;
}

.dynamic-condition {
  border-color: #67c23a;
  background-color: #f0f9ff;
}

.empty-condition {
  text-align: center;
  padding: 20px;
  color: #909399;
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
</style>