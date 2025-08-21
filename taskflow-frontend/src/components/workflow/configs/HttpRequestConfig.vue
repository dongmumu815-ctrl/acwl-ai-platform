<template>
  <div class="config-section">
    <h4>HTTP请求配置</h4>
    
    <el-form-item label="请求URL">
      <el-input 
        v-model="localConfig.url" 
        placeholder="输入请求URL"
        @change="handleChange"
      />
    </el-form-item>
    
    <el-form-item label="请求方法">
      <el-select v-model="localConfig.method" @change="handleChange">
        <el-option label="GET" value="GET" />
        <el-option label="POST" value="POST" />
        <el-option label="PUT" value="PUT" />
        <el-option label="DELETE" value="DELETE" />
        <el-option label="PATCH" value="PATCH" />
        <el-option label="HEAD" value="HEAD" />
        <el-option label="OPTIONS" value="OPTIONS" />
      </el-select>
    </el-form-item>
    
    <el-form-item label="请求头">
      <div class="headers-list">
        <div 
          v-for="(header, index) in localConfig.headers" 
          :key="index"
          class="header-item"
        >
          <el-input 
            v-model="header.name" 
            placeholder="Header名称"
            @change="handleChange"
          />
          <span class="separator">:</span>
          <el-input 
            v-model="header.value" 
            placeholder="Header值"
            @change="handleChange"
          />
          <el-button 
            @click="removeHeader(index)" 
            size="small" 
            type="danger" 
            text
          >
            删除
          </el-button>
        </div>
        <el-button @click="addHeader" size="small" type="primary" text>
          + 添加请求头
        </el-button>
      </div>
    </el-form-item>
    
    <el-form-item label="请求体" v-if="hasBody">
      <el-tabs v-model="bodyType" @tab-change="handleBodyTypeChange">
        <el-tab-pane label="JSON" name="json">
          <el-input 
            v-model="localConfig.body" 
            type="textarea"
            :rows="6"
            placeholder="输入JSON格式的请求体"
            @change="handleChange"
          />
        </el-tab-pane>
        <el-tab-pane label="表单" name="form">
          <div class="form-data-list">
            <div 
              v-for="(field, index) in formData" 
              :key="index"
              class="form-field-item"
            >
              <el-input 
                v-model="field.name" 
                placeholder="字段名"
                @change="handleFormDataChange"
              />
              <span class="separator">=</span>
              <el-input 
                v-model="field.value" 
                placeholder="字段值"
                @change="handleFormDataChange"
              />
              <el-button 
                @click="removeFormField(index)" 
                size="small" 
                type="danger" 
                text
              >
                删除
              </el-button>
            </div>
            <el-button @click="addFormField" size="small" type="primary" text>
              + 添加字段
            </el-button>
          </div>
        </el-tab-pane>
        <el-tab-pane label="原始文本" name="raw">
          <el-input 
            v-model="localConfig.body" 
            type="textarea"
            :rows="6"
            placeholder="输入原始请求体内容"
            @change="handleChange"
          />
        </el-tab-pane>
      </el-tabs>
    </el-form-item>
    
    <el-form-item label="超时时间">
      <el-input-number 
        v-model="localConfig.timeout" 
        :min="1" 
        :max="300"
        @change="handleChange"
      />
      <span class="unit">秒</span>
    </el-form-item>
    
    <el-form-item label="SSL验证">
      <el-switch 
        v-model="localConfig.verifySSL" 
        @change="handleChange"
      />
    </el-form-item>
    
    <el-form-item label="跟随重定向">
      <el-switch 
        v-model="localConfig.followRedirects" 
        @change="handleChange"
      />
    </el-form-item>
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue'

// Props
const props = defineProps({
  modelValue: {
    type: Object,
    default: () => ({})
  }
})

// Emits
const emit = defineEmits(['update:modelValue', 'change'])

// 本地配置数据
const localConfig = ref({
  url: '',
  method: 'GET',
  headers: [],
  body: '',
  timeout: 30,
  verifySSL: true,
  followRedirects: true,
  ...props.modelValue
})

// 请求体类型
const bodyType = ref('json')

// 表单数据
const formData = ref([])

// 监听外部配置变化
watch(() => props.modelValue, (newValue) => {
  localConfig.value = { ...localConfig.value, ...newValue }
  // 解析headers
  if (newValue.headers && typeof newValue.headers === 'object') {
    localConfig.value.headers = Object.entries(newValue.headers).map(([name, value]) => ({ name, value }))
  }
}, { deep: true })

// 计算属性
const hasBody = computed(() => {
  return ['POST', 'PUT', 'PATCH'].includes(localConfig.value.method)
})

/**
 * 添加请求头
 */
const addHeader = () => {
  localConfig.value.headers.push({ name: '', value: '' })
  handleChange()
}

/**
 * 删除请求头
 */
const removeHeader = (index) => {
  localConfig.value.headers.splice(index, 1)
  handleChange()
}

/**
 * 添加表单字段
 */
const addFormField = () => {
  formData.value.push({ name: '', value: '' })
  handleFormDataChange()
}

/**
 * 删除表单字段
 */
const removeFormField = (index) => {
  formData.value.splice(index, 1)
  handleFormDataChange()
}

/**
 * 处理请求体类型变化
 */
const handleBodyTypeChange = (type) => {
  bodyType.value = type
  if (type === 'form') {
    // 切换到表单模式时，清空body并初始化表单数据
    localConfig.value.body = ''
    if (formData.value.length === 0) {
      formData.value = [{ name: '', value: '' }]
    }
  }
  handleChange()
}

/**
 * 处理表单数据变化
 */
const handleFormDataChange = () => {
  // 将表单数据转换为URL编码格式
  const formString = formData.value
    .filter(field => field.name && field.value)
    .map(field => `${encodeURIComponent(field.name)}=${encodeURIComponent(field.value)}`)
    .join('&')
  localConfig.value.body = formString
  handleChange()
}

/**
 * 处理配置变化
 */
const handleChange = () => {
  // 将headers数组转换为对象
  const headersObj = {}
  localConfig.value.headers.forEach(header => {
    if (header.name && header.value) {
      headersObj[header.name] = header.value
    }
  })
  
  const configToEmit = {
    ...localConfig.value,
    headers: headersObj
  }
  
  emit('update:modelValue', configToEmit)
  emit('change', configToEmit)
}
</script>

<style scoped>
.config-section {
  margin-bottom: 0;
  padding: 16px;
  background: #fafafa;
  border-radius: 8px;
  border: 1px solid #e8e8e8;
}

.config-section h4 {
  margin: 0 0 16px 0;
  font-size: 14px;
  font-weight: 600;
  color: #333;
  padding-bottom: 8px;
  border-bottom: 1px solid #e0e0e0;
}

.headers-list, .form-data-list {
  border: 1px solid #e8e8e8;
  border-radius: 4px;
  padding: 8px;
  background: #fff;
}

.header-item, .form-field-item {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.header-item:last-of-type, .form-field-item:last-of-type {
  margin-bottom: 8px;
}

.separator {
  font-weight: bold;
  color: #666;
  min-width: 16px;
  text-align: center;
}

.unit {
  margin-left: 8px;
  font-size: 12px;
  color: #8c8c8c;
}

:deep(.el-tabs__content) {
  padding-top: 12px;
}
</style>