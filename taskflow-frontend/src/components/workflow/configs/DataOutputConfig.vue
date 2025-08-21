<template>
  <div class="config-section">
    <h4>数据输出配置</h4>
    <el-form-item label="输出类型">
      <el-select v-model="localConfig.outputType" @change="handleChange">
        <el-option label="文件" value="file" />
        <el-option label="数据库" value="database" />
        <el-option label="API" value="api" />
      </el-select>
    </el-form-item>
    <el-form-item label="输出路径">
      <el-input v-model="localConfig.outputPath" placeholder="输入输出路径" @change="handleChange" />
    </el-form-item>
    <el-form-item label="格式">
      <el-select v-model="localConfig.format" @change="handleChange">
        <el-option label="CSV" value="csv" />
        <el-option label="JSON" value="json" />
        <el-option label="Excel" value="excel" />
      </el-select>
    </el-form-item>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
const props = defineProps({ modelValue: { type: Object, default: () => ({}) } })
const emit = defineEmits(['update:modelValue', 'change'])
const localConfig = ref({ outputType: 'file', outputPath: '', format: 'csv', ...props.modelValue })
watch(() => props.modelValue, (newValue) => { localConfig.value = { ...localConfig.value, ...newValue } }, { deep: true })
const handleChange = () => { emit('update:modelValue', localConfig.value); emit('change', localConfig.value) }
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