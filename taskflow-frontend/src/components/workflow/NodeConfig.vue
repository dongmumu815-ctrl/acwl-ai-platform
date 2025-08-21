<template>
  <div class="node-config">
    <!-- 基础配置 -->
    <div class="config-section">
      <h4>基础配置</h4>
      <el-form-item label="超时时间">
        <el-input-number 
          v-model="localConfig.timeout" 
          :min="1" 
          :max="3600"
          @change="handleChange"
        />
        <span class="unit">秒</span>
      </el-form-item>
      <el-form-item label="重试次数">
        <el-input-number 
          v-model="localConfig.retryCount" 
          :min="0" 
          :max="10"
          @change="handleChange"
        />
      </el-form-item>
      <el-form-item label="工作组">
        <el-select v-model="localConfig.workerGroup" @change="handleChange">
          <el-option label="默认组" value="default" />
          <el-option label="高性能组" value="high-performance" />
          <el-option label="GPU组" value="gpu" />
        </el-select>
      </el-form-item>
      <el-form-item label="运行环境">
        <el-select v-model="localConfig.environment" @change="handleChange">
          <el-option label="生产环境" value="production" />
          <el-option label="测试环境" value="test" />
          <el-option label="开发环境" value="development" />
        </el-select>
      </el-form-item>
    </div>

    <!-- 动态配置组件 -->
    <component 
      :is="getConfigComponent(nodeType)"
      v-model="localConfig"
      @change="handleChange"
    />
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import DataInputConfig from './configs/DataInputConfig.vue'
import DataFilterConfig from './configs/DataFilterConfig.vue'
import DataTransformConfig from './configs/DataTransformConfig.vue'
import DataOutputConfig from './configs/DataOutputConfig.vue'
import DataJoinConfig from './configs/DataJoinConfig.vue'
import ConditionConfig from './configs/ConditionConfig.vue'
import LoopConfig from './configs/LoopConfig.vue'
import ShellConfig from './configs/ShellConfig.vue'
import PythonConfig from './configs/PythonConfig.vue'
import DelayConfig from './configs/DelayConfig.vue'
import HttpRequestConfig from './configs/HttpRequestConfig.vue'
import FileProcessConfig from './configs/FileProcessConfig.vue'
import EmailSendConfig from './configs/EmailSendConfig.vue'
import FtpTransferConfig from './configs/FtpTransferConfig.vue'
import DatabaseQueryConfig from './configs/DatabaseQueryConfig.vue'

// Props
const props = defineProps({
  modelValue: {
    type: Object,
    default: () => ({})
  },
  nodeType: {
    type: String,
    required: true
  }
})

// Emits
const emit = defineEmits(['update:modelValue', 'change'])

// 本地配置数据
const localConfig = ref({ ...props.modelValue })

// 监听外部配置变化
watch(() => props.modelValue, (newValue) => {
  localConfig.value = { ...newValue }
}, { deep: true })

/**
 * 获取配置组件
 */
const getConfigComponent = (type) => {
  const componentMap = {
    'data-input': DataInputConfig,
    'data-filter': DataFilterConfig,
    'data-transform': DataTransformConfig,
    'data-output': DataOutputConfig,
    'data-join': DataJoinConfig,
    'condition': ConditionConfig,
    'loop': LoopConfig,
    'shell': ShellConfig,
    'python': PythonConfig,
    'delay': DelayConfig,
    'http-request': HttpRequestConfig,
    'file-process': FileProcessConfig,
    'email-send': EmailSendConfig,
    'ftp-transfer': FtpTransferConfig,
    'database-query': DatabaseQueryConfig
  }
  return componentMap[type] || 'div'
}

/**
 * 处理配置变化
 */
const handleChange = () => {
  emit('update:modelValue', localConfig.value)
  emit('change', localConfig.value)
}
</script>

<style scoped>
.node-config {
  padding: 0;
}

.config-section {
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid #e8e8e8;
}

.config-section:last-child {
  border-bottom: none;
  margin-bottom: 0;
}

.config-section h4 {
  margin: 0 0 12px 0;
  font-size: 13px;
  font-weight: 500;
  color: #262626;
}

.unit {
  margin-left: 8px;
  font-size: 12px;
  color: #8c8c8c;
}

:deep(.el-form-item) {
  margin-bottom: 12px;
}

:deep(.el-form-item__label) {
  font-size: 12px;
  line-height: 1.5;
}

:deep(.el-input), :deep(.el-select) {
  width: 100%;
}

:deep(.el-input-number) {
  width: 120px;
}
</style>