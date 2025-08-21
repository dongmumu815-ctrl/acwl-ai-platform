<template>
  <div class="node-config">
    <!-- 通用配置 -->
    <div class="config-section">
      <h4>通用配置</h4>
      <el-form-item label="超时时间(秒)">
        <el-input-number 
          v-model="localConfig.timeout" 
          :min="1" 
          :max="3600" 
          @change="handleChange"
        />
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
        <el-input 
          v-model="localConfig.workerGroup" 
          placeholder="默认工作组"
          @change="handleChange"
        />
      </el-form-item>
      <el-form-item label="环境变量">
        <el-input 
          v-model="localConfig.environment" 
          placeholder="production"
          @change="handleChange"
        />
      </el-form-item>
    </div>

    <!-- 节点特定配置 -->
    <component 
      :is="getSpecificConfigComponent()"
      v-model="localConfig"
      @change="handleChange"
    />
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import DataInputConfig from './DataInputConfig.vue'
import DataFilterConfig from './DataFilterConfig.vue'
import DataTransformConfig from './DataTransformConfig.vue'
import DataOutputConfig from './DataOutputConfig.vue'
import DataJoinConfig from './DataJoinConfig.vue'
import ConditionConfig from './ConditionConfig.vue'
import LoopConfig from './LoopConfig.vue'
import ShellConfig from './ShellConfig.vue'
import PythonConfig from './PythonConfig.vue'
import HttpRequestConfig from './HttpRequestConfig.vue'
import DelayConfig from './DelayConfig.vue'

/**
 * 组件属性定义
 */
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

/**
 * 组件事件定义
 */
const emit = defineEmits(['update:modelValue', 'change'])

/**
 * 本地配置数据
 */
const localConfig = ref({
  timeout: 30,
  retryCount: 0,
  workerGroup: 'default',
  environment: 'production',
  ...props.modelValue
})

/**
 * 监听外部数据变化
 */
watch(() => props.modelValue, (newValue) => {
  localConfig.value = {
    timeout: 30,
    retryCount: 0,
    workerGroup: 'default',
    environment: 'production',
    ...newValue
  }
}, { deep: true })

/**
 * 获取特定节点类型的配置组件
 * @returns {Object|String} 配置组件
 */
const getSpecificConfigComponent = () => {
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
    'http-request': HttpRequestConfig,
    'delay': DelayConfig,
    'file-process': 'div', // 占位符
    'email-send': 'div', // 占位符
    'ftp-transfer': 'div', // 占位符
    'database-query': 'div' // 占位符
  }
  
  return componentMap[props.nodeType] || 'div'
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
  padding: 16px;
  background: #fafafa;
  border-radius: 8px;
  border: 1px solid #e8e8e8;
}

.config-section:last-child {
  margin-bottom: 0;
}

.config-section h4 {
  margin: 0 0 16px 0;
  font-size: 14px;
  font-weight: 600;
  color: #333;
  padding-bottom: 8px;
  border-bottom: 1px solid #e0e0e0;
}
</style>