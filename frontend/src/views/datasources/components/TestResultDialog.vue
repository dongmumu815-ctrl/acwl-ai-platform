<template>
  <el-dialog
    v-model="visible"
    title="连接测试结果"
    width="600px"
    :close-on-click-modal="false"
  >
    <div v-if="testResult" class="test-result-container">
      <!-- 测试状态 -->
      <div class="result-header">
        <div class="status-indicator">
          <el-icon
            :class="['status-icon', testResult.success ? 'success' : 'error']"
            :size="32"
          >
            <CircleCheck v-if="testResult.success" />
            <CircleClose v-else />
          </el-icon>
          <div class="status-text">
            <h3 :class="['status-title', testResult.success ? 'success' : 'error']">
              {{ testResult.success ? '连接成功' : '连接失败' }}
            </h3>
            <p class="status-message">{{ testResult.message }}</p>
          </div>
        </div>
      </div>

      <!-- 测试详情 -->
      <div class="result-details">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="测试时间">
            {{ formatDateTime(testResult.test_time) }}
          </el-descriptions-item>
          <el-descriptions-item label="响应时间">
            <span v-if="testResult.response_time">
              {{ testResult.response_time }}ms
              <el-tag
                :type="getResponseTimeType(testResult.response_time)"
                size="small"
                style="margin-left: 8px"
              >
                {{ getResponseTimeLabel(testResult.response_time) }}
              </el-tag>
            </span>
            <span v-else>-</span>
          </el-descriptions-item>
        </el-descriptions>
      </div>

      <!-- 连接信息 -->
      <div v-if="testResult.connection_info" class="connection-info">
        <h4>连接信息</h4>
        <el-descriptions :column="1" border>
          <el-descriptions-item
            v-for="(value, key) in testResult.connection_info"
            :key="key"
            :label="formatLabel(key)"
          >
            <template v-if="typeof value === 'object'">
              <pre class="json-content">{{ JSON.stringify(value, null, 2) }}</pre>
            </template>
            <template v-else>
              {{ value }}
            </template>
          </el-descriptions-item>
        </el-descriptions>
      </div>

      <!-- 错误详情 -->
      <div v-if="!testResult.success && testResult.error_details" class="error-details">
        <h4>错误详情</h4>
        <el-alert
          :title="testResult.error_details"
          type="error"
          :closable="false"
          show-icon
        >
          <template #default>
            <div class="error-content">
              <p><strong>错误信息：</strong>{{ testResult.error_details }}</p>
              <div class="error-suggestions">
                <p><strong>可能的解决方案：</strong></p>
                <ul>
                  <li v-for="suggestion in getErrorSuggestions(testResult.error_details)" :key="suggestion">
                    {{ suggestion }}
                  </li>
                </ul>
              </div>
            </div>
          </template>
        </el-alert>
      </div>

      <!-- 性能指标 -->
      <div v-if="testResult.success && testResult.response_time" class="performance-metrics">
        <h4>性能指标</h4>
        <div class="metrics-grid">
          <div class="metric-item">
            <div class="metric-value">{{ testResult.response_time }}ms</div>
            <div class="metric-label">响应时间</div>
          </div>
          <div class="metric-item">
            <div class="metric-value">
              {{ getConnectionQuality(testResult.response_time) }}
            </div>
            <div class="metric-label">连接质量</div>
          </div>
          <div class="metric-item">
            <div class="metric-value">
              {{ getNetworkLatency(testResult.response_time) }}
            </div>
            <div class="metric-label">网络延迟</div>
          </div>
        </div>
      </div>

      <!-- 建议 -->
      <div v-if="testResult.success" class="recommendations">
        <h4>优化建议</h4>
        <el-alert
          type="info"
          :closable="false"
          show-icon
        >
          <template #default>
            <ul class="recommendation-list">
              <li v-for="recommendation in getRecommendations(testResult)" :key="recommendation">
                {{ recommendation }}
              </li>
            </ul>
          </template>
        </el-alert>
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">关闭</el-button>
        <el-button
          v-if="testResult && testResult.success"
          type="primary"
          @click="handleRetry"
        >
          重新测试
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { CircleCheck, CircleClose } from '@element-plus/icons-vue'
import { formatDateTime } from '@/utils/date'

// Props
const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  testResult: {
    type: Object,
    default: null
  }
})

// Emits
const emit = defineEmits(['update:modelValue', 'retry'])

// 响应式数据
const visible = ref(false)

// 监听器
watch(() => props.modelValue, (val) => {
  visible.value = val
})

watch(visible, (val) => {
  emit('update:modelValue', val)
})

// 方法
const handleClose = () => {
  visible.value = false
}

const handleRetry = () => {
  emit('retry')
  handleClose()
}

// 工具方法
const formatLabel = (key) => {
  const labelMap = {
    connection_type: '连接类型',
    server_version: '服务器版本',
    test_query_result: '测试查询结果',
    connection_params: '连接参数',
    datasource_type: '数据源类型',
    host: '主机地址',
    port: '端口',
    database: '数据库'
  }
  return labelMap[key] || key
}

const getResponseTimeType = (responseTime) => {
  if (responseTime < 100) return 'success'
  if (responseTime < 500) return 'warning'
  return 'danger'
}

const getResponseTimeLabel = (responseTime) => {
  if (responseTime < 100) return '优秀'
  if (responseTime < 500) return '良好'
  if (responseTime < 1000) return '一般'
  return '较慢'
}

const getConnectionQuality = (responseTime) => {
  if (responseTime < 50) return '优秀'
  if (responseTime < 100) return '良好'
  if (responseTime < 300) return '一般'
  if (responseTime < 1000) return '较差'
  return '很差'
}

const getNetworkLatency = (responseTime) => {
  if (responseTime < 50) return '低延迟'
  if (responseTime < 200) return '中等延迟'
  return '高延迟'
}

const getErrorSuggestions = (errorDetails) => {
  const suggestions = []
  const error = errorDetails.toLowerCase()
  
  if (error.includes('connection refused') || error.includes('连接被拒绝')) {
    suggestions.push('检查主机地址和端口是否正确')
    suggestions.push('确认目标服务是否正在运行')
    suggestions.push('检查防火墙设置')
  } else if (error.includes('timeout') || error.includes('超时')) {
    suggestions.push('检查网络连接是否稳定')
    suggestions.push('增加连接超时时间')
    suggestions.push('确认目标服务响应正常')
  } else if (error.includes('authentication') || error.includes('认证') || error.includes('密码')) {
    suggestions.push('检查用户名和密码是否正确')
    suggestions.push('确认用户是否有相应权限')
    suggestions.push('检查数据库用户配置')
  } else if (error.includes('database') || error.includes('数据库')) {
    suggestions.push('检查数据库名称是否正确')
    suggestions.push('确认数据库是否存在')
    suggestions.push('检查用户是否有访问该数据库的权限')
  } else {
    suggestions.push('检查所有连接参数是否正确')
    suggestions.push('确认网络连接正常')
    suggestions.push('联系系统管理员获取帮助')
  }
  
  return suggestions
}

const getRecommendations = (testResult) => {
  const recommendations = []
  
  if (testResult.response_time > 1000) {
    recommendations.push('响应时间较长，建议检查网络连接或优化数据库配置')
  }
  
  if (testResult.response_time < 50) {
    recommendations.push('连接性能优秀，可以正常使用')
  }
  
  recommendations.push('建议定期测试连接以确保数据源稳定性')
  recommendations.push('可以配置连接池参数以优化性能')
  
  return recommendations
}
</script>

<style scoped>
.test-result-container {
  padding: 10px 0;
}

.result-header {
  margin-bottom: 24px;
}

.status-indicator {
  display: flex;
  align-items: center;
  padding: 20px;
  background-color: #f8f9fa;
  border-radius: 8px;
  border-left: 4px solid #409eff;
}

.status-indicator.success {
  border-left-color: #67c23a;
  background-color: #f0f9ff;
}

.status-indicator.error {
  border-left-color: #f56c6c;
  background-color: #fef0f0;
}

.status-icon {
  margin-right: 16px;
}

.status-icon.success {
  color: #67c23a;
}

.status-icon.error {
  color: #f56c6c;
}

.status-text {
  flex: 1;
}

.status-title {
  margin: 0 0 8px 0;
  font-size: 18px;
  font-weight: 600;
}

.status-title.success {
  color: #67c23a;
}

.status-title.error {
  color: #f56c6c;
}

.status-message {
  margin: 0;
  color: #606266;
  font-size: 14px;
}

.result-details,
.connection-info,
.error-details,
.performance-metrics,
.recommendations {
  margin-bottom: 24px;
}

.result-details h4,
.connection-info h4,
.error-details h4,
.performance-metrics h4,
.recommendations h4 {
  margin: 0 0 12px 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.json-content {
  background-color: #f5f7fa;
  padding: 8px 12px;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  font-size: 12px;
  color: #606266;
  white-space: pre-wrap;
  word-break: break-all;
}

.error-content {
  line-height: 1.6;
}

.error-suggestions {
  margin-top: 12px;
}

.error-suggestions ul {
  margin: 8px 0 0 0;
  padding-left: 20px;
}

.error-suggestions li {
  margin-bottom: 4px;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.metric-item {
  text-align: center;
  padding: 16px;
  background-color: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
}

.metric-value {
  font-size: 24px;
  font-weight: bold;
  color: #409eff;
  margin-bottom: 4px;
}

.metric-label {
  font-size: 12px;
  color: #909399;
}

.recommendation-list {
  margin: 0;
  padding-left: 20px;
}

.recommendation-list li {
  margin-bottom: 8px;
  line-height: 1.5;
}

.dialog-footer {
  text-align: right;
}

:deep(.el-descriptions__label) {
  font-weight: 500;
  width: 120px;
}

:deep(.el-alert__content) {
  line-height: 1.6;
}
</style>