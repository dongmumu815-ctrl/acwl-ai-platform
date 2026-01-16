<template>
  <div class="config-section">
    <h4>{{ taskTitle }}配置</h4>
    
    <el-form-item label="任务类型">
      <el-tag>{{ taskTitle }}</el-tag>
    </el-form-item>

    <el-form-item label="输入数据">
      <el-input 
        v-model="localConfig.input" 
        type="textarea"
        :rows="3"
        placeholder="输入要处理的数据或变量引用..."
        @change="handleChange"
      />
    </el-form-item>

    <el-form-item label="模型选择">
      <el-select v-model="localConfig.model" placeholder="选择模型" @change="handleChange">
        <el-option label="默认模型" value="default" />
        <el-option label="高性能模型" value="high_performance" />
        <el-option label="低延迟模型" value="low_latency" />
      </el-select>
    </el-form-item>

    <el-form-item label="置信度阈值">
      <el-slider 
        v-model="localConfig.threshold" 
        :min="0" 
        :max="1" 
        :step="0.01" 
        show-input
        @change="handleChange"
      />
    </el-form-item>
    
    <template v-if="nodeType === 'text-analysis'">
       <el-form-item label="分析维度">
        <el-checkbox-group v-model="localConfig.dimensions" @change="handleChange">
          <el-checkbox value="sentiment">情感分析</el-checkbox>
          <el-checkbox value="keywords">关键词提取</el-checkbox>
          <el-checkbox value="summary">文本摘要</el-checkbox>
          <el-checkbox value="entity">实体识别</el-checkbox>
        </el-checkbox-group>
      </el-form-item>
    </template>
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue'

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

const emit = defineEmits(['update:modelValue', 'change'])

const localConfig = ref({
  input: '',
  model: 'default',
  threshold: 0.6,
  dimensions: [], // specific for text-analysis
  ...props.modelValue
})

const taskTitle = computed(() => {
  const map = {
    'text-analysis': '文本分析',
    'image-recognition': '图像识别',
    'speech-processing': '语音处理'
  }
  return map[props.nodeType] || 'AI任务'
})

watch(() => props.modelValue, (newValue) => {
  localConfig.value = { 
    input: '',
    model: 'default',
    threshold: 0.6,
    dimensions: [],
    ...newValue 
  }
}, { deep: true })

const handleChange = () => {
  emit('update:modelValue', localConfig.value)
  emit('change', localConfig.value)
}
</script>
