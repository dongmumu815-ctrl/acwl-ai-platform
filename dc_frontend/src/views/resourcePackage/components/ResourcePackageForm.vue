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

      <!-- 模板配置 -->
      <el-card class="form-section">
        <template #header>
          <span class="section-title">模板配置</span>
        </template>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="模板类型" prop="template_type">
              <el-select 
                v-model="form.template_type" 
                placeholder="选择模板类型" 
                style="width: 100%" 
                @change="handleTemplateTypeChange"
              >
                <el-option label="SQL查询" value="sql" />
                <el-option label="Elasticsearch" value="elasticsearch" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="查询模板" prop="template_id">
              <el-select
                v-model="form.template_id"
                placeholder="选择查询模板"
                style="width: 100%"
                @change="handleTemplateChange"
              >
                <el-option
                  v-for="template in filteredTemplates"
                  :key="template.id"
                  :label="template.name"
                  :value="template.id"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        
        <!-- 模板预览 -->
        <el-form-item label="模板内容" v-if="selectedTemplate">
          <el-input
            :model-value="selectedTemplate.content"
            type="textarea"
            :rows="6"
            readonly
            placeholder="模板内容预览"
          />
        </el-form-item>
        
        <!-- 动态参数配置 -->
        <el-form-item label="动态参数" v-if="selectedTemplate && selectedTemplate.default_params">
          <div class="dynamic-params">
            <div 
              v-for="(value, key) in selectedTemplate.default_params" 
              :key="key"
              class="param-item"
            >
              <el-row :gutter="10" align="middle">
                <el-col :span="6">
                  <el-text>{{ key }}</el-text>
                </el-col>
                <el-col :span="18">
                  <el-input
                    v-model="form.dynamic_params[key]"
                    :placeholder="`默认值: ${value}`"
                  />
                </el-col>
              </el-row>
            </div>
          </div>
        </el-form-item>
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
  templateApi,
  type ResourcePackage,
  type ResourcePackageCreateRequest,
  type ResourcePackageUpdateRequest,
  type Template,
  PackageType
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
const templates = ref<any[]>([])
const selectedTemplate = ref<any>(null)
const availableTags = ref<string[]>(['数据分析', '报表', '监控', '业务', '测试'])

// 表单数据
const form = reactive({
  name: '',
  description: '',
  type: 'sql' as PackageType,
  datasource_id: '',
  template_id: '',
  template_type: 'sql' as PackageType,
  dynamic_params: {} as Record<string, any>,
  is_active: true,
  tags: [] as string[]
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
  template_id: [
    { required: true, message: '请选择模板', trigger: 'change' }
  ],
  template_type: [
    { required: true, message: '请选择模板类型', trigger: 'change' }
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

const templateTypeOptions = computed(() => {
  if (form.type === 'sql') {
    return [
      { label: '查询模板', value: 'query' },
      { label: '统计模板', value: 'aggregation' }
    ]
  } else {
    return [
      { label: '搜索模板', value: 'search' },
      { label: '聚合模板', value: 'aggregation' }
    ]
  }
})

const filteredTemplates = computed(() => {
  return templates.value.filter(template => {
    return template.type === form.template_type
  })
})

const templateContent = computed(() => {
  if (!selectedTemplate.value) return ''
  try {
    return JSON.stringify(selectedTemplate.value.content, null, 2)
  } catch {
    return selectedTemplate.value.content
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

watch(() => form.template_type, () => {
  handleTemplateTypeChange()
})

watch(() => form.datasource_id, (newVal) => {
  if (newVal) {
    handleDatasourceChange(newVal)
  }
})

watch(() => form.template_id, (newVal) => {
  if (newVal) {
    handleTemplateChange(newVal)
  }
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

const loadTemplates = async () => {
  try {
    const response = await templateApi.list({
      type: form.template_type as any,
      datasource_id: Number(form.datasource_id)
    })
    templates.value = response.data || []
  } catch (error) {
    console.error('加载模板失败:', error)
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
    template_id: data.template_id,
    template_type: data.template_type,
    dynamic_params: data.dynamic_params || {},
    is_active: data.is_active,
    tags: data.tags?.map(tag => tag.tag_name) || []
  })
  
  // 加载相关数据
  if (form.datasource_id && form.template_type) {
    loadTemplates()
  }
  if (form.template_id) {
    loadTemplateDetails(form.template_id)
  }
}

const resetForm = () => {
  Object.assign(form, {
    name: '',
    description: '',
    type: 'sql',
    datasource_id: '',
    template_id: '',
    template_type: 'query',
    dynamic_params: {},
    is_active: true,
    tags: []
  })
  
  templates.value = []
  selectedTemplate.value = null
  
  nextTick(() => {
    formRef.value?.clearValidate()
  })
}

const handleTypeChange = () => {
  form.datasource_id = ''
  form.template_id = ''
  form.template_type = form.type === 'sql' ? 'query' : 'search'
  form.dynamic_params = {}
  templates.value = []
  selectedTemplate.value = null
}

const handleDatasourceChange = async (datasourceId: number | string) => {
  if (!datasourceId) return
  
  form.template_id = ''
  form.dynamic_params = {}
  templates.value = []
  selectedTemplate.value = null
  
  if (form.template_type) {
    await loadTemplates()
  }
}

const handleTemplateTypeChange = async () => {
  form.template_id = ''
  form.dynamic_params = {}
  templates.value = []
  selectedTemplate.value = null
  
  if (form.datasource_id) {
    await loadTemplates()
  }
}

const handleTemplateChange = async (templateId: string) => {
  if (!templateId) {
    selectedTemplate.value = null
    form.dynamic_params = {}
    return
  }
  
  await loadTemplateDetails(templateId)
}

const loadTemplateDetails = async (templateId: string) => {
  try {
    const response = await templateApi.get(Number(templateId), form.template_type as any)
    const template = response.data
    selectedTemplate.value = template
    
    // 初始化动态参数
    const defaultParams = template.default_params || {}
    form.dynamic_params = { ...defaultParams }
  } catch (error) {
    console.error('加载模板详情失败:', error)
  }
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