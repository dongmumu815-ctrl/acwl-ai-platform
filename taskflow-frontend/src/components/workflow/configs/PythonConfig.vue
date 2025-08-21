<template>
  <div class="config-section">
    <h4>Python脚本配置</h4>
    <el-form-item label="执行类型">
      <el-select v-model="localConfig.executionType" @change="handleChange">
        <el-option label="内联脚本" value="inline" />
        <el-option label="文件路径" value="file" />
      </el-select>
    </el-form-item>
    <el-form-item :label="localConfig.executionType === 'file' ? '脚本文件路径' : 'Python代码'">
      <el-input 
        v-model="localConfig.scriptContent" 
        :type="localConfig.executionType === 'file' ? 'text' : 'textarea'"
        :rows="localConfig.executionType === 'file' ? 1 : 8"
        :placeholder="localConfig.executionType === 'file' ? '输入Python文件路径' : '输入Python代码'"
        @change="handleChange"
      />
    </el-form-item>
    <el-form-item label="命令参数">
      <el-input v-model="localConfig.arguments" placeholder="输入命令行参数" @change="handleChange" />
    </el-form-item>
    <el-form-item label="工作目录">
      <el-input v-model="localConfig.workingDirectory" placeholder="输入工作目录路径" @change="handleChange" />
    </el-form-item>
    <el-form-item label="Python版本">
      <el-select v-model="localConfig.pythonVersion" @change="handleChange">
        <el-option label="Python 3.8" value="python3.8" />
        <el-option label="Python 3.9" value="python3.9" />
        <el-option label="Python 3.10" value="python3.10" />
        <el-option label="Python 3.11" value="python3.11" />
        <el-option label="Python 3.12" value="python3.12" />
      </el-select>
    </el-form-item>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  modelValue: { type: Object, default: () => ({}) }
})

const emit = defineEmits(['update:modelValue', 'change'])

const localConfig = ref({ 
  executionType: 'inline', 
  scriptContent: '', 
  arguments: '', 
  workingDirectory: '', 
  pythonVersion: 'python3.11',
  ...props.modelValue 
})

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