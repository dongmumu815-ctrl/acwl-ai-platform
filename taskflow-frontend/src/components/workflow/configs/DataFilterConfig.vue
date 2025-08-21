<template>
  <div class="config-section">
    <h4>数据筛选配置</h4>
    
    <el-form-item label="筛选类型">
      <el-select v-model="localConfig.filterType" @change="handleChange">
        <el-option label="WHERE条件" value="where" />
        <el-option label="正则表达式" value="regex" />
        <el-option label="Python表达式" value="python" />
      </el-select>
    </el-form-item>
    
    <el-form-item label="筛选条件">
      <el-input 
        v-model="localConfig.filterCondition" 
        type="textarea"
        :rows="4"
        :placeholder="getPlaceholder()"
        @change="handleChange"
      />
    </el-form-item>
    
    <el-form-item label="大小写敏感" v-if="localConfig.filterType === 'regex'">
      <el-switch 
        v-model="localConfig.caseSensitive" 
        @change="handleChange"
      />
    </el-form-item>
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
  filterType: 'where',
  filterCondition: '',
  caseSensitive: true,
  ...props.modelValue
})

// 监听外部配置变化
watch(() => props.modelValue, (newValue) => {
  localConfig.value = { ...localConfig.value, ...newValue }
}, { deep: true })

/**
 * 获取占位符文本
 */
const getPlaceholder = () => {
  switch (localConfig.value.filterType) {
    case 'where':
      return '例如: age > 18 AND status = "active"'
    case 'regex':
      return '例如: ^[A-Za-z]+$'
    case 'python':
      return '例如: row["age"] > 18 and row["status"] == "active"'
    default:
      return '输入筛选条件'
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
</style>