<template>
  <el-dialog
    v-model="visible"
    :title="isEdit ? '编辑模型服务配置' : '新增模型服务配置'"
    width="800px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="120px"
      label-position="left"
    >
      <el-row :gutter="16">
        <el-col :span="12">
          <el-form-item label="配置名称" prop="name">
            <el-input
              v-model="form.name"
              placeholder="请输入配置名称"
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="显示名称" prop="display_name">
            <el-input
              v-model="form.display_name"
              placeholder="请输入显示名称"
            />
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="16">
        <el-col :span="8">
          <el-form-item label="服务提供商" prop="provider">
            <el-select
              v-model="form.provider"
              placeholder="请选择服务提供商"
              style="width: 100%"
              @change="handleProviderChange"
            >
              <el-option
                v-for="provider in providers"
                :key="provider.value"
                :label="provider.label"
                :value="provider.value"
              />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="模型类型" prop="model_type">
            <el-select
              v-model="form.model_type"
              placeholder="请选择模型类型"
              style="width: 100%"
            >
              <el-option label="聊天对话" value="chat" />
              <el-option label="文本生成" value="text" />
              <el-option label="图像生成" value="image" />
              <el-option label="图像理解" value="vision" />
              <el-option label="语音合成" value="tts" />
              <el-option label="语音识别" value="stt" />
              <el-option label="文本嵌入" value="embedding" />
              <el-option label="代码生成" value="code" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="模型名称" prop="model_name">
            <!-- Ollama类型显示下拉选择 -->
            <el-select
              v-if="form.provider === 'ollama'"
              v-model="form.model_name"
              placeholder="请选择模型"
              style="width: 100%"
              filterable
              :loading="modelsLoading"
              @focus="fetchOllamaModels"
            >
              <el-option
                v-for="model in availableModels"
                :key="model.name"
                :label="model.name"
                :value="model.name"
              >
                <span>{{ model.name }}</span>
                <span style="float: right; color: #8492a6; font-size: 13px">
                  {{ formatModelSize(model.size) }}
                </span>
              </el-option>
            </el-select>
            <!-- 其他类型显示输入框 -->
            <el-input
              v-else
              v-model="form.model_name"
              placeholder="请输入模型名称"
            />
          </el-form-item>
        </el-col>
      </el-row>

      <el-form-item label="API端点" prop="api_endpoint">
        <el-input
          v-model="baseEndpoint"
          placeholder="请输入服务器地址（如：http://localhost:11434）"
          @blur="handleEndpointChange"
        >
          <template #append>
            <span v-if="form.provider" class="endpoint-suffix">
              {{ getEndpointSuffix(form.provider) }}
            </span>
          </template>
        </el-input>
        <div v-if="form.api_endpoint" class="endpoint-preview">
          完整端点：{{ form.api_endpoint }}
        </div>
      </el-form-item>

      <el-form-item label="API密钥" prop="api_key">
        <el-input
          v-model="form.api_key"
          type="password"
          placeholder="请输入API密钥"
          show-password
        />
      </el-form-item>

      <el-row :gutter="12">
        <el-col :span="8">
          <el-form-item label="最大Token" prop="max_tokens">
            <el-input-number
              v-model="form.max_tokens"
              :min="1"
              :max="100000"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
        <el-col :span="8" v-if="['chat', 'text', 'code'].includes(form.model_type)">
          <el-form-item label="温度" prop="temperature">
            <el-input-number
              v-model="form.temperature"
              :min="0"
              :max="2"
              :step="0.1"
              :precision="1"
              style="width: 100%"
              placeholder="控制输出随机性"
            />
            <div class="field-hint">值越高输出越随机，值越低输出越确定</div>
          </el-form-item>
        </el-col>
        <!-- 图像生成模型特有参数 -->
        <el-col :span="8" v-if="form.model_type === 'image'">
          <el-form-item label="图像尺寸">
            <el-select
              v-model="form.image_size"
              placeholder="请选择图像尺寸"
              style="width: 100%"
            >
              <el-option label="512x512" value="512x512" />
              <el-option label="1024x1024" value="1024x1024" />
              <el-option label="1792x1024" value="1792x1024" />
              <el-option label="1024x1792" value="1024x1792" />
            </el-select>
            <div class="field-hint">生成图像的分辨率</div>
          </el-form-item>
        </el-col>
        <!-- 嵌入模型特有参数 -->
        <el-col :span="8" v-if="form.model_type === 'embedding'">
          <el-form-item label="向量维度">
            <el-input-number
              v-model="form.embedding_dimension"
              :min="128"
              :max="4096"
              style="width: 100%"
              placeholder="向量维度"
            />
            <div class="field-hint">嵌入向量的维度大小</div>
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="超时时间(秒)" prop="timeout">
            <el-input-number
              v-model="form.timeout"
              :min="1"
              :max="300"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="16">
        <el-col :span="12">
          <el-form-item label="是否激活">
            <el-switch v-model="form.is_active" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="设为默认">
            <el-switch v-model="form.is_default" />
          </el-form-item>
        </el-col>
      </el-row>

      <el-form-item label="描述">
        <el-input
          v-model="form.description"
          type="textarea"
          :rows="3"
          placeholder="请输入配置描述"
        />
      </el-form-item>

      <!-- 高级配置 -->
      <el-collapse v-model="activeCollapse">
        <el-collapse-item title="高级配置" name="advanced">
          <el-form-item label="请求头">
            <div class="headers-container">
              <div
                v-for="(header, index) in form.headers"
                :key="index"
                class="header-item"
              >
                <el-input
                  v-model="header.key"
                  placeholder="请求头名称"
                  style="width: 40%"
                />
                <el-input
                  v-model="header.value"
                  placeholder="请求头值"
                  style="width: 40%; margin-left: 8px"
                />
                <el-button
                  type="danger"
                  size="small"
                  @click="removeHeader(index)"
                  style="margin-left: 8px"
                >
                  删除
                </el-button>
              </div>
              <el-button type="primary" size="small" @click="addHeader">
                添加请求头
              </el-button>
            </div>
          </el-form-item>

          <el-form-item label="额外参数">
            <el-input
              v-model="extraParamsText"
              type="textarea"
              :rows="4"
              placeholder="请输入JSON格式的额外参数"
              @blur="validateExtraParams"
            />
          </el-form-item>
        </el-collapse-item>
      </el-collapse>
    </el-form>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button type="primary" @click="handleTest" :loading="testLoading">
          测试连接
        </el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitLoading">
          {{ isEdit ? '更新' : '创建' }}
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { modelServiceConfigApi } from '@/api/model-service-configs'

// Props
interface Props {
  modelValue: boolean
  config?: any
  providers: Array<{ label: string; value: string }>
  existingConfigs?: Array<{ name: string; id?: string }>
}

const props = withDefaults(defineProps<Props>(), {
  config: null,
  existingConfigs: () => []
})

// Emits
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  success: []
}>()

// 响应式数据
const formRef = ref()
const submitLoading = ref(false)
const testLoading = ref(false)
const modelsLoading = ref(false)
const activeCollapse = ref([])
const extraParamsText = ref('')
const baseEndpoint = ref('')
const availableModels = ref([])

// 表单数据
const form = reactive({
  name: '',
  display_name: '',
  provider: '',
  model_type: 'chat',
  model_name: '',
  api_endpoint: '',
  api_key: '',
  max_tokens: 4096,
  temperature: 0.7,
  timeout: 30,
  // 图像生成模型参数
  image_size: '1024x1024',
  // 嵌入模型参数
  embedding_dimension: 1536,
  is_active: true,
  is_default: false,
  description: '',
  headers: [],
  extra_params: {}
})

/**
 * 检查配置名称是否重复
 */
const validateConfigName = async (rule: any, value: string, callback: any) => {
  if (!value) {
    callback()
    return
  }
  
  try {
    // 调用API检查名称是否存在
    const response = await modelServiceConfigApi.getConfigs({
      search: value,
      page: 1,
      size: 100
    })
    
    // 检查是否有同名配置（排除当前编辑的配置）
    const existingConfig = response.items?.find(config => 
      config.name === value && 
      (!isEdit.value || config.id !== props.config?.id)
    )
    
    if (existingConfig) {
      callback(new Error('配置名称已存在，请使用其他名称'))
    } else {
      callback()
    }
  } catch (error) {
    console.error('验证配置名称失败:', error)
    // 如果API调用失败，允许通过验证，避免阻塞用户操作
    callback()
  }
}

// 表单验证规则
const rules = {
  name: [
    { required: true, message: '请输入配置名称', trigger: 'blur' },
    { min: 2, max: 50, message: '长度在 2 到 50 个字符', trigger: 'blur' },
    { validator: validateConfigName, trigger: 'blur' }
  ],
  display_name: [
    { required: true, message: '请输入显示名称', trigger: 'blur' },
    { min: 2, max: 100, message: '长度在 2 到 100 个字符', trigger: 'blur' }
  ],
  provider: [
    { required: true, message: '请选择服务提供商', trigger: 'change' }
  ],
  model_type: [
    { required: true, message: '请选择模型类型', trigger: 'change' }
  ],
  model_name: [
    { required: true, message: '请输入模型名称', trigger: 'blur' }
  ],
  api_endpoint: [
    { required: true, message: '请输入API端点', trigger: 'blur' },
    { type: 'url', message: '请输入有效的URL', trigger: 'blur' }
  ],
  api_key: [
    // API密钥可以为空，某些本地服务不需要密钥
  ],
  max_tokens: [
    { required: true, message: '请输入最大Token数', trigger: 'blur' },
    { type: 'number', min: 1, max: 100000, message: '请输入1-100000之间的数字', trigger: 'blur' }
  ],
  temperature: [
    { required: true, message: '请输入温度值', trigger: 'blur' },
    { type: 'number', min: 0, max: 2, message: '请输入0-2之间的数字', trigger: 'blur' }
  ],
  timeout: [
    { required: true, message: '请输入超时时间', trigger: 'blur' },
    { type: 'number', min: 1, max: 300, message: '请输入1-300之间的数字', trigger: 'blur' }
  ]
}

// 计算属性
const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const isEdit = computed(() => !!props.config)

/**
 * 获取端点后缀
 */
const getEndpointSuffix = (provider) => {
  const suffixMap = {
    'openai': '/v1/chat/completions',
    'azure_openai': '/openai/deployments/{deployment}/chat/completions?api-version=2023-05-15',
    'anthropic': '/v1/messages',
    'google': '/v1beta/models/{model}:generateContent',
    'ollama': '/api/chat',
    'vllm': '/v1/chat/completions'
  }
  return suffixMap[provider] || ''
}

/**
 * 重置表单
 */
const resetForm = () => {
  Object.assign(form, {
    name: '',
    display_name: '',
    provider: '',
    model_type: 'chat',
    model_name: '',
    api_endpoint: '',
    api_key: '',
    max_tokens: 4096,
    temperature: 0.7,
    timeout: 30,
    // 图像生成模型参数
    image_size: '1024x1024',
    // 嵌入模型参数
    embedding_dimension: 1536,
    is_active: true,
    is_default: false,
    description: '',
    headers: [],
    extra_params: {}
  })
  extraParamsText.value = ''
  activeCollapse.value = []
  
  nextTick(() => {
    formRef.value?.clearValidate()
  })
}

// 监听配置变化
watch(
  () => props.config,
  (newConfig) => {
    if (newConfig) {
      // 编辑模式，填充表单
      Object.assign(form, {
        ...newConfig,
        // 确保数值类型字段为number类型
        max_tokens: Number(newConfig.max_tokens) || 4096,
        temperature: Number(newConfig.temperature) || 0.7,
        timeout: Number(newConfig.timeout) || 30,
        // 确保模型类型字段有默认值
        model_type: newConfig.model_type || 'chat',
        // 图像生成模型参数
        image_size: newConfig.image_size || '1024x1024',
        // 嵌入模型参数
        embedding_dimension: Number(newConfig.embedding_dimension) || 1536,
        headers: newConfig.headers ? JSON.parse(JSON.stringify(newConfig.headers)) : []
      })
      extraParamsText.value = newConfig.extra_params 
        ? JSON.stringify(newConfig.extra_params, null, 2) 
        : ''
      
      // 从完整端点中提取基础端点
      if (newConfig.api_endpoint && newConfig.provider) {
        const suffix = getEndpointSuffix(newConfig.provider)
        if (suffix && newConfig.api_endpoint.endsWith(suffix)) {
          baseEndpoint.value = newConfig.api_endpoint.slice(0, -suffix.length)
        } else {
          baseEndpoint.value = newConfig.api_endpoint
        }
      }
    } else {
      // 新增模式，重置表单
      resetForm()
    }
  },
  { immediate: true }
)

/**
 * 处理端点变化
 */
const handleEndpointChange = () => {
  if (baseEndpoint.value && form.provider) {
    const suffix = getEndpointSuffix(form.provider)
    // 移除末尾的斜杠
    const cleanBase = baseEndpoint.value.replace(/\/$/, '')
    form.api_endpoint = cleanBase + suffix
  }
}

/**
 * 格式化模型大小
 */
const formatModelSize = (size) => {
  if (!size) return ''
  const gb = size / (1024 * 1024 * 1024)
  return gb >= 1 ? `${gb.toFixed(1)}GB` : `${(size / (1024 * 1024)).toFixed(0)}MB`
}

/**
 * 获取Ollama模型列表
 */
const fetchOllamaModels = async () => {
  if (!baseEndpoint.value || modelsLoading.value || availableModels.value.length > 0) {
    return
  }
  
  try {
    modelsLoading.value = true
    const cleanBase = baseEndpoint.value.replace(/\/$/, '')
    const response = await fetch(`${cleanBase}/api/tags`)
    
    if (response.ok) {
      const data = await response.json()
      availableModels.value = data.models || []
    } else {
      ElMessage.warning('无法获取模型列表，请检查Ollama服务是否正常运行')
    }
  } catch (error) {
    console.error('获取Ollama模型列表失败:', error)
    ElMessage.warning('获取模型列表失败，请检查网络连接')
  } finally {
    modelsLoading.value = false
  }
}

/**
 * 处理提供商变化
 */
const handleProviderChange = () => {
  // 清空模型列表
  availableModels.value = []
  
  // 根据不同的服务提供商设置默认值
  switch (form.provider) {
    case 'openai':
      baseEndpoint.value = 'https://api.openai.com'
      form.model_name = 'gpt-3.5-turbo'
      break
    case 'azure_openai':
      baseEndpoint.value = 'https://your-resource.openai.azure.com'
      form.model_name = 'gpt-35-turbo'
      break
    case 'anthropic':
      baseEndpoint.value = 'https://api.anthropic.com'
      form.model_name = 'claude-3-sonnet-20240229'
      break
    case 'google':
      baseEndpoint.value = 'https://generativelanguage.googleapis.com'
      form.model_name = 'gemini-pro'
      break
    case 'ollama':
      baseEndpoint.value = 'http://localhost:11434'
      form.model_name = 'llama2'
      break
    case 'vllm':
      baseEndpoint.value = 'http://localhost:8000'
      form.model_name = 'meta-llama/Llama-2-7b-chat-hf'
      break
    default:
      baseEndpoint.value = ''
      form.model_name = ''
  }
  
  // 更新完整端点
  handleEndpointChange()
}

/**
 * 添加请求头
 */
const addHeader = () => {
  form.headers.push({ key: '', value: '' })
}

/**
 * 删除请求头
 */
const removeHeader = (index: number) => {
  form.headers.splice(index, 1)
}

/**
 * 验证额外参数
 */
const validateExtraParams = () => {
  if (!extraParamsText.value.trim()) {
    form.extra_params = {}
    return
  }
  
  try {
    form.extra_params = JSON.parse(extraParamsText.value)
  } catch (error) {
    ElMessage.error('额外参数格式错误，请输入有效的JSON')
    extraParamsText.value = JSON.stringify(form.extra_params, null, 2)
  }
}

/**
 * 测试连接
 */
const handleTest = async () => {
  try {
    await formRef.value.validate()
    
    testLoading.value = true
    
    // 准备测试数据
    const testData = {
      provider: form.provider,
      model_name: form.model_name,
      api_endpoint: form.api_endpoint,
      api_key: form.api_key,
      max_tokens: form.max_tokens,
      temperature: form.temperature,
      timeout: form.timeout,
      headers: form.headers.filter(h => h.key && h.value),
      extra_params: form.extra_params,
      test_message: 'Hello, this is a test message.'
    }
    
    const result = await modelServiceConfigApi.testConfig(testData)
    
    if (result.success) {
      ElMessage.success('连接测试成功')
    } else {
      ElMessage.error(`连接测试失败: ${result.error}`)
    }
  } catch (error) {
    if (error !== 'validation failed') {
      ElMessage.error('测试连接失败')
      console.error('测试连接失败:', error)
    }
  } finally {
    testLoading.value = false
  }
}

/**
 * 提交表单
 */
const handleSubmit = async () => {
  try {
    await formRef.value.validate()
    
    submitLoading.value = true
    
    // 准备提交数据
    const submitData = {
      ...form,
      headers: form.headers.filter(h => h.key && h.value)
    }
    
    if (isEdit.value) {
      await modelServiceConfigApi.updateConfig(props.config.id, submitData)
      ElMessage.success('更新成功')
    } else {
      await modelServiceConfigApi.createConfig(submitData)
      ElMessage.success('创建成功')
    }
    
    emit('success')
  } catch (error) {
    if (error !== 'validation failed') {
      ElMessage.error(isEdit.value ? '更新失败' : '创建失败')
      console.error('提交失败:', error)
    }
  } finally {
    submitLoading.value = false
  }
}

/**
 * 关闭对话框
 */
const handleClose = () => {
  visible.value = false
}
</script>

<style scoped>
.headers-container {
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  padding: 12px;
  background-color: #fafafa;
}

.header-item {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}

.header-item:last-of-type {
  margin-bottom: 12px;
}

.dialog-footer {
  text-align: right;
}

.endpoint-suffix {
  color: #909399;
  font-size: 12px;
  padding: 0 8px;
  background-color: #f5f7fa;
  border-left: 1px solid #dcdfe6;
}

.endpoint-preview {
  margin-top: 4px;
  font-size: 12px;
  color: #606266;
  background-color: #f5f7fa;
  padding: 4px 8px;
  border-radius: 4px;
  border: 1px solid #e4e7ed;
}

:deep(.el-collapse-item__header) {
  font-weight: 500;
}

:deep(.el-form-item__label) {
  font-weight: 500;
}

:deep(.el-input-number) {
  width: 100%;
}

.field-hint {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
  line-height: 1.4;
}
</style>