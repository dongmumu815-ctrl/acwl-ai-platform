<template>
  <el-dialog
    v-model="visible"
    title="测试结果"
    width="600px"
    :close-on-click-modal="false"
  >
    <div class="test-result-container">
      <!-- 测试状态 -->
      <div class="status-section">
        <div class="status-header">
          <el-icon :size="20" :color="result?.success ? '#67c23a' : '#f56c6c'">
            <SuccessFilled v-if="result?.success" />
            <CircleCloseFilled v-else />
          </el-icon>
          <span class="status-text" :class="{ success: result?.success, error: !result?.success }">
            {{ result?.success ? '测试成功' : '测试失败' }}
          </span>
        </div>
        
        <div class="status-details">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="响应时间">
              {{ result?.response_time ? `${result.response_time}ms` : '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="状态码">
              {{ result?.status_code || '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="模型">
              {{ result?.model || '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="Token使用">
              {{ formatTokenUsage(result?.token_usage) }}
            </el-descriptions-item>
          </el-descriptions>
        </div>
      </div>

      <!-- 错误信息 -->
      <div v-if="!result?.success && result?.error" class="error-section">
        <h4>错误信息</h4>
        <el-alert
          :title="result.error"
          type="error"
          :closable="false"
          show-icon
        />
        
        <div v-if="result.error_details" class="error-details">
          <h5>详细信息</h5>
          <pre class="error-code">{{ result.error_details }}</pre>
        </div>
      </div>

      <!-- 成功响应 -->
      <div v-if="result?.success" class="response-section">
        <h4>响应内容</h4>
        
        <!-- 消息内容 -->
        <div v-if="result.response_content" class="response-content">
          <h5>AI回复</h5>
          <div class="message-content">
            {{ result.response_content }}
          </div>
        </div>
        
        <!-- 原始响应 -->
        <el-collapse v-if="result.raw_response">
          <el-collapse-item title="查看原始响应" name="raw">
            <pre class="raw-response">{{ formatRawResponse(result.raw_response) }}</pre>
          </el-collapse-item>
        </el-collapse>
      </div>

      <!-- 请求信息 -->
      <div v-if="result?.request_info" class="request-section">
        <el-collapse>
          <el-collapse-item title="查看请求信息" name="request">
            <el-descriptions :column="1" border>
              <el-descriptions-item label="请求URL">
                <code>{{ result.request_info.url }}</code>
              </el-descriptions-item>
              <el-descriptions-item label="请求方法">
                <el-tag size="small">{{ result.request_info.method }}</el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="请求头" v-if="result.request_info.headers">
                <pre class="headers-content">{{ formatHeaders(result.request_info.headers) }}</pre>
              </el-descriptions-item>
              <el-descriptions-item label="请求体" v-if="result.request_info.body">
                <pre class="request-body">{{ formatRequestBody(result.request_info.body) }}</pre>
              </el-descriptions-item>
            </el-descriptions>
          </el-collapse-item>
        </el-collapse>
      </div>

      <!-- 建议 -->
      <div v-if="getSuggestions().length > 0" class="suggestions-section">
        <h4>建议</h4>
        <ul class="suggestions-list">
          <li v-for="(suggestion, index) in getSuggestions()" :key="index">
            {{ suggestion }}
          </li>
        </ul>
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">关闭</el-button>
        <el-button v-if="result?.success" type="primary" @click="handleCopyResponse">
          复制响应
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { ElMessage } from 'element-plus'
import { SuccessFilled, CircleCloseFilled } from '@element-plus/icons-vue'

// Props
interface Props {
  modelValue: boolean
  result?: any
}

const props = withDefaults(defineProps<Props>(), {
  result: null
})

// Emits
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

// 计算属性
const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

/**
 * 格式化Token使用情况
 */
const formatTokenUsage = (tokenUsage: any) => {
  if (!tokenUsage) return '-'
  
  const parts = []
  if (tokenUsage.prompt_tokens) {
    parts.push(`输入: ${tokenUsage.prompt_tokens}`)
  }
  if (tokenUsage.completion_tokens) {
    parts.push(`输出: ${tokenUsage.completion_tokens}`)
  }
  if (tokenUsage.total_tokens) {
    parts.push(`总计: ${tokenUsage.total_tokens}`)
  }
  
  return parts.length > 0 ? parts.join(', ') : '-'
}

/**
 * 格式化原始响应
 */
const formatRawResponse = (rawResponse: any) => {
  if (typeof rawResponse === 'string') {
    try {
      return JSON.stringify(JSON.parse(rawResponse), null, 2)
    } catch {
      return rawResponse
    }
  }
  return JSON.stringify(rawResponse, null, 2)
}

/**
 * 格式化请求头
 */
const formatHeaders = (headers: any) => {
  if (typeof headers === 'string') {
    try {
      headers = JSON.parse(headers)
    } catch {
      return headers
    }
  }
  
  return Object.entries(headers)
    .map(([key, value]) => `${key}: ${value}`)
    .join('\n')
}

/**
 * 格式化请求体
 */
const formatRequestBody = (body: any) => {
  if (typeof body === 'string') {
    try {
      return JSON.stringify(JSON.parse(body), null, 2)
    } catch {
      return body
    }
  }
  return JSON.stringify(body, null, 2)
}

/**
 * 获取建议
 */
const getSuggestions = () => {
  const suggestions = []
  const result = props.result
  
  if (!result) return suggestions
  
  if (!result.success) {
    if (result.status_code === 401) {
      suggestions.push('请检查API密钥是否正确')
    } else if (result.status_code === 403) {
      suggestions.push('请检查API密钥权限或账户余额')
    } else if (result.status_code === 404) {
      suggestions.push('请检查API端点URL是否正确')
    } else if (result.status_code === 429) {
      suggestions.push('请求频率过高，请稍后重试')
    } else if (result.status_code >= 500) {
      suggestions.push('服务器错误，请稍后重试或联系服务提供商')
    } else if (result.error && result.error.includes('timeout')) {
      suggestions.push('请求超时，可以尝试增加超时时间')
    } else if (result.error && result.error.includes('connection')) {
      suggestions.push('网络连接问题，请检查网络设置和防火墙')
    }
    
    if (result.error && result.error.includes('SSL')) {
      suggestions.push('SSL证书问题，请检查证书配置')
    }
  } else {
    if (result.response_time > 5000) {
      suggestions.push('响应时间较长，可以考虑优化网络或选择更近的服务节点')
    }
    
    if (result.token_usage && result.token_usage.total_tokens > 3000) {
      suggestions.push('Token使用量较高，注意控制输入长度以降低成本')
    }
  }
  
  return suggestions
}

/**
 * 复制响应内容
 */
const handleCopyResponse = async () => {
  try {
    const content = props.result?.response_content || ''
    await navigator.clipboard.writeText(content)
    ElMessage.success('响应内容已复制到剪贴板')
  } catch (error) {
    ElMessage.error('复制失败')
    console.error('复制失败:', error)
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
.test-result-container {
  max-height: 70vh;
  overflow-y: auto;
}

.status-section {
  margin-bottom: 24px;
}

.status-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
}

.status-text {
  font-size: 18px;
  font-weight: 600;
}

.status-text.success {
  color: #67c23a;
}

.status-text.error {
  color: #f56c6c;
}

.status-details {
  margin-top: 16px;
}

.error-section,
.response-section,
.request-section,
.suggestions-section {
  margin-bottom: 24px;
}

.error-section h4,
.response-section h4,
.request-section h4,
.suggestions-section h4 {
  margin: 0 0 12px 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.error-section h5,
.response-section h5 {
  margin: 16px 0 8px 0;
  font-size: 14px;
  font-weight: 500;
  color: #606266;
}

.error-details {
  margin-top: 16px;
}

.error-code,
.raw-response,
.headers-content,
.request-body {
  background-color: #f5f7fa;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  padding: 12px;
  font-family: 'Courier New', monospace;
  font-size: 12px;
  line-height: 1.4;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 200px;
  overflow-y: auto;
}

.message-content {
  background-color: #f0f9ff;
  border: 1px solid #bfdbfe;
  border-radius: 8px;
  padding: 16px;
  line-height: 1.6;
  color: #1e40af;
}

.suggestions-list {
  margin: 0;
  padding-left: 20px;
}

.suggestions-list li {
  margin-bottom: 8px;
  color: #606266;
  line-height: 1.5;
}

.dialog-footer {
  text-align: right;
}

code {
  background-color: #f5f7fa;
  padding: 2px 6px;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
  font-size: 12px;
}

:deep(.el-descriptions__label) {
  font-weight: 500;
}

:deep(.el-collapse-item__header) {
  font-weight: 500;
}

:deep(.el-alert__title) {
  word-break: break-all;
}

/* 滚动条样式 */
.test-result-container::-webkit-scrollbar,
.error-code::-webkit-scrollbar,
.raw-response::-webkit-scrollbar,
.headers-content::-webkit-scrollbar,
.request-body::-webkit-scrollbar {
  width: 6px;
}

.test-result-container::-webkit-scrollbar-track,
.error-code::-webkit-scrollbar-track,
.raw-response::-webkit-scrollbar-track,
.headers-content::-webkit-scrollbar-track,
.request-body::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.test-result-container::-webkit-scrollbar-thumb,
.error-code::-webkit-scrollbar-thumb,
.raw-response::-webkit-scrollbar-thumb,
.headers-content::-webkit-scrollbar-thumb,
.request-body::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.test-result-container::-webkit-scrollbar-thumb:hover,
.error-code::-webkit-scrollbar-thumb:hover,
.raw-response::-webkit-scrollbar-thumb:hover,
.headers-content::-webkit-scrollbar-thumb:hover,
.request-body::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}
</style>