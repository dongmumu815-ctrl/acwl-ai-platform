<template>
  <div class="config-section">
    <h4>延时等待配置</h4>
    
    <el-form-item label="延时时间">
      <div class="delay-input">
        <el-input-number 
          v-model="localConfig.delayTime" 
          :min="1" 
          :max="86400"
          @change="handleChange"
        />
        <el-select v-model="localConfig.delayUnit" @change="handleChange">
          <el-option label="秒" value="seconds" />
          <el-option label="分钟" value="minutes" />
          <el-option label="小时" value="hours" />
        </el-select>
      </div>
    </el-form-item>
    
    <el-form-item label="延时描述">
      <el-input 
        v-model="localConfig.description" 
        placeholder="描述延时的目的（可选）"
        @change="handleChange"
      />
    </el-form-item>
    
    <div class="delay-preview">
      <span class="preview-label">预计延时：</span>
      <span class="preview-value">{{ getDelayPreview() }}</span>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

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
  delayTime: 60,
  delayUnit: 'seconds',
  description: '',
  ...props.modelValue
})

// 监听外部配置变化
watch(() => props.modelValue, (newValue) => {
  localConfig.value = { ...localConfig.value, ...newValue }
}, { deep: true })

/**
 * 获取延时预览
 */
const getDelayPreview = () => {
  const time = localConfig.value.delayTime
  const unit = localConfig.value.delayUnit
  
  let totalSeconds = time
  if (unit === 'minutes') {
    totalSeconds = time * 60
  } else if (unit === 'hours') {
    totalSeconds = time * 3600
  }
  
  if (totalSeconds < 60) {
    return `${totalSeconds}秒`
  } else if (totalSeconds < 3600) {
    const minutes = Math.floor(totalSeconds / 60)
    const seconds = totalSeconds % 60
    return seconds > 0 ? `${minutes}分${seconds}秒` : `${minutes}分钟`
  } else {
    const hours = Math.floor(totalSeconds / 3600)
    const minutes = Math.floor((totalSeconds % 3600) / 60)
    const seconds = totalSeconds % 60
    
    let result = `${hours}小时`
    if (minutes > 0) result += `${minutes}分钟`
    if (seconds > 0) result += `${seconds}秒`
    
    return result
  }
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

.delay-input {
  display: flex;
  gap: 8px;
  align-items: center;
}

.delay-input .el-input-number {
  flex: 1;
}

.delay-input .el-select {
  width: 80px;
}

.delay-preview {
  padding: 8px 12px;
  background: #f0f9ff;
  border: 1px solid #bae7ff;
  border-radius: 4px;
  margin-top: 8px;
}

.preview-label {
  font-size: 12px;
  color: #666;
}

.preview-value {
  font-size: 12px;
  color: #1890ff;
  font-weight: 500;
}
</style>