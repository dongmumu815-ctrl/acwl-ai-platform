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
            <el-form-item label="状态">
              <el-switch v-model="form.is_active" active-text="启用" inactive-text="禁用" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="是否可删除">
              <el-switch 
                v-model="is_deletable" 
                active-text="可删除" 
                inactive-text="不可删除"
                :active-value="true"
                :inactive-value="false"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <!-- 预留空间 -->
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item v-if="!isEdit" label="资源类型" prop="resource_id">
              <el-select
                v-model="form.resource_id"
                placeholder="选择资源类型"
                style="width: 100%"
                @change="handleResourceChange"
              >
                <el-option
                  v-for="resource in dataResources"
                  :key="resource.id"
                  :label="resource.name"
                  :value="resource.id"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item v-if="!isEdit" label="查询类型" prop="type">
              <el-select v-model="form.type" placeholder="选择查询类型" style="width: 100%" @change="handleTypeChange">
                <el-option label="SQL" value="sql" />
                <el-option label="Elasticsearch" value="elasticsearch" />
              </el-select>
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

      <!-- 模板配置（编辑模式下隐藏） -->
      <el-card v-if="!isEdit" class="form-section">
        <template #header>
          <span class="section-title">模板配置</span>
        </template>
        
        <el-row :gutter="20">
          <el-col :span="24">
            <el-form-item label="查询模板" prop="template_id">
              <el-select
                v-model="form.template_id"
                placeholder="选择查询模板,该模板为资源类型的查询模板,选取后该资源包自动使用该模板的查询条件"
                style="width: 100%"
                @change="handleTemplateChange"
              >
                <el-option
                  v-for="template in templates"
                  :key="template.id"
                  :label="template.name"
                  :value="template.id"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        
        <!-- 模板预览 -->
        <!-- <el-form-item label="模板内容" v-if="selectedTemplate">
          <el-input
            :model-value="selectedTemplate.content"
            type="textarea"
            :rows="6"
            readonly
            placeholder="模板内容预览"
          />
        </el-form-item> -->
        
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
import { datasourceApi } from '@/api/datasource'
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
const dataResources = ref<any[]>([])
const templates = ref<any[]>([])
const selectedTemplate = ref<any>(null)
const selectedResource = ref<any>(null)
const availableTags = ref<string[]>(['数据分析', '报表', '监控', '业务', '测试'])

// 表单数据
const form = reactive({
  name: '',
  description: '',
  type: 'sql' as PackageType,
  datasource_id: '',
  resource_id: '',
  template_id: '',
  template_type: 'sql' as PackageType,
  dynamic_params: {} as Record<string, any>,
  is_active: true,
  is_lock: '0' as string, // 添加is_lock字段，默认为"0"表示可删除
  tags: [] as string[]
})

// 计算属性：用于UI显示的is_deletable，与is_lock相反
const is_deletable = computed({
  get: () => form.is_lock === '0',
  set: (value: boolean) => {
    form.is_lock = value ? '0' : '1'
  }
})

// 将is_deletable添加到form对象中，方便模板使用
Object.defineProperty(form, 'is_deletable', {
  get: () => is_deletable.value,
  set: (value: boolean) => { is_deletable.value = value }
})

// 表单验证规则
const rules: FormRules = {
  name: [
    { required: true, message: '请输入资源包名称', trigger: 'blur' },
    { min: 2, max: 255, message: '名称长度在 2 到 255 个字符', trigger: 'blur' }
  ],
  type: [
    { required: true, message: '请选择查询类型', trigger: 'change' }
  ],
  resource_id: [
    { required: true, message: '请选择资源类型', trigger: 'change' }
  ],
  template_id: [
    { required: true, message: '请选择查询模板', trigger: 'change' }
  ]
}

// 计算属性
const filteredTemplates = computed(() => {
  return templates.value.filter(template => {
    // 根据查询类型筛选模板
    return template.type === form.type || template.template_type === form.type
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
    loadDataResources()
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

watch(() => form.type, () => {
  // 当查询类型改变时，重新加载模板
  form.template_id = ''
  form.template_type = form.type
  selectedTemplate.value = null
  
  if (form.type && form.resource_id) {
    console.log('form.type 变化，重新加载模板:', { type: form.type, resource_id: form.resource_id })
    loadTemplates()
  } else {
    console.log('form.type 变化，但缺少必要参数:', { type: form.type, resource_id: form.resource_id })
    templates.value = []
  }
})

watch(() => form.template_id, () => {
  // 当模板改变时，更新模板信息
  handleTemplateChange()
})

// 方法
const loadDataResources = async () => {
  try {
    loading.value = true
    const response = await dataResourceApi.getResourceList()
    dataResources.value = response.data?.items || []
  } catch (error) {
    console.error('加载数据资源失败:', error)
    ElMessage.error('加载数据资源失败')
  } finally {
    loading.value = false
  }
}

const loadTemplates = async () => {
  try {
    if (!form.type) {
      console.log('loadTemplates: form.type 为空，跳过加载')
      return
    }
    
    // 获取data_resource_id和datasource_id，两个参数都需要传递
    let data_resource_id = form.resource_id
    let datasource_id = form.datasource_id
    
    if (!data_resource_id && selectedResource.value) {
      data_resource_id = selectedResource.value.id
    }
    if (!datasource_id && selectedResource.value) {
      datasource_id = selectedResource.value.datasource_id
    }
    
    console.log('loadTemplates 参数检查:', {
      'form.type': form.type,
      'form.resource_id': form.resource_id,
      'form.datasource_id': form.datasource_id,
      'selectedResource.value': selectedResource.value,
      'data_resource_id': data_resource_id,
      'datasource_id': datasource_id
    })
    
    // 确保两个参数都有值才调用API
    if (!data_resource_id || !datasource_id) {
      console.warn('缺少必要参数：data_resource_id 或 datasource_id', {
        data_resource_id,
        datasource_id
      })
      templates.value = []
      return
    }
    
    console.log('调用 templateApi.list，参数:', { datasource_id, type: form.type, data_resource_id })
    // 修复：确保正确传递类型参数，并转换为数字类型
    const templates_data = await templateApi.list({
      datasource_id: parseInt(datasource_id),
      type: form.type,
      data_resource_id: parseInt(data_resource_id)
    })
    console.log(templates_data,'templates_data')
    templates.value = templates_data.data || []
  } catch (error) {
    console.error('加载模板失败:', error)
    ElMessage.error('加载模板失败')
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
    resource_id: data.resource_id,
    template_id: data.template_id,
    template_type: data.template_type,
    dynamic_params: data.dynamic_params || {},
    is_active: data.is_active,
    is_lock: data.is_lock || '0', // 加载is_lock字段，默认为'0'
    tags: data.tags?.map(tag => tag.tag_name) || []
  })
  
  // 加载相关数据
  if (form.type && form.resource_id) {
    console.log('loadFormData 加载模板:', { type: form.type, resource_id: form.resource_id })
    loadTemplates()
  } else {
    console.log('loadFormData 缺少必要参数:', { type: form.type, resource_id: form.resource_id })
  }
}

const resetForm = () => {
  Object.assign(form, {
    name: '',
    description: '',
    type: 'sql',
    datasource_id: '',
    resource_id: '',
    template_id: '',
    template_type: 'sql',
    dynamic_params: {},
    is_active: true,
    is_lock: '0', // 重置is_lock字段为'0'，表示可删除
    tags: []
  })
  
  templates.value = []
  selectedTemplate.value = null
  selectedResource.value = null
  
  nextTick(() => {
    formRef.value?.clearValidate()
  })
}

const handleResourceChange = () => {
  const resource = dataResources.value.find(r => r.id === form.resource_id)
  if (resource) {
    selectedResource.value = resource
    form.description = resource.description || ''
    form.datasource_id = resource.datasource_id
    
    // 资源变更后重新加载模板
    if (form.type) {
      console.log('handleResourceChange 触发模板加载:', { type: form.type, resource_id: form.resource_id })
      loadTemplates()
    }
  }
}

const handleTypeChange = () => {
  // 当查询类型改变时，重新加载模板
  form.template_id = ''
  form.template_type = form.type
  selectedTemplate.value = null
  
  if (form.type && form.resource_id) {
    console.log('handleTypeChange 触发模板加载:', { type: form.type, resource_id: form.resource_id })
    loadTemplates()
  } else {
    console.log('handleTypeChange 缺少必要参数:', { type: form.type, resource_id: form.resource_id })
    templates.value = []
  }
}

const handleTemplateChange = () => {
  const template = templates.value.find(t => t.id === form.template_id)
  if (template) {
    selectedTemplate.value = template
    // 如果模板有默认参数，可以在这里处理
    if (template.default_params) {
      form.dynamic_params = { ...template.default_params }
    }
  } else {
    selectedTemplate.value = null
    form.dynamic_params = {}
  }
}



const handleSubmit = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    
    loading.value = true
    
    if (props.isEdit && props.packageData) {
      // 编辑模式下仅允许更新指定字段
      const updateData: ResourcePackageUpdateRequest = {
        name: form.name,
        description: form.description,
        is_active: form.is_active,
        is_lock: form.is_lock,
        tags: form.tags
      }
      await resourcePackageApi.update(props.packageData.id, updateData)
      ElMessage.success('更新成功')
    } else {
      // 创建模式下提交完整数据，修复类型转换问题
      const submitData: ResourcePackageCreateRequest = {
        name: form.name,
        description: form.description,
        type: form.type,
        datasource_id: parseInt(form.datasource_id),
        resource_id: parseInt(form.resource_id),
        template_id: parseInt(form.template_id),
        template_type: form.template_type,
        dynamic_params: form.dynamic_params,
        is_active: form.is_active,
        is_lock: form.is_lock,
        tags: form.tags
      }
      await resourcePackageApi.create(submitData)
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

.form-item-tip {
  margin-top: 4px;
}
</style>