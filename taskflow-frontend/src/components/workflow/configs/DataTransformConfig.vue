<template>
  <div class="config-section">
    <h4>数据转换配置</h4>
    <el-form-item label="转换类型">
      <el-select v-model="localConfig.transformType" @change="handleChange">
        <el-option label="Python脚本" value="python" />
        <el-option label="SQL查询" value="sql" />
        <el-option label="JSON转换" value="json" />
      </el-select>
    </el-form-item>
    <el-form-item label="转换脚本">
      <el-input 
        v-model="localConfig.transformScript" 
        type="textarea"
        :rows="6"
        placeholder="输入转换脚本"
        @change="handleChange"
      />
    </el-form-item>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  modelValue: { type: Object, default: () => ({}) }
})

const emit = defineEmits(['update:modelValue', 'change'])

const localConfig = ref({ transformType: 'python', transformScript: '', ...props.modelValue })

watch(() => props.modelValue, (newValue) => {
  localConfig.value = { ...localConfig.value, ...newValue }
}, { deep: true })

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