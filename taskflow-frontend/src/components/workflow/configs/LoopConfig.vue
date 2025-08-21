<template>
  <div class="config-section">
    <h4>循环执行配置</h4>
    <el-form-item label="循环类型">
      <el-select v-model="localConfig.loopType" @change="handleChange">
        <el-option label="For循环" value="for" />
        <el-option label="While循环" value="while" />
        <el-option label="数据遍历" value="foreach" />
      </el-select>
    </el-form-item>
    <el-form-item label="循环条件">
      <el-input v-model="localConfig.loopCondition" placeholder="输入循环条件" @change="handleChange" />
    </el-form-item>
    <el-form-item label="最大迭代次数">
      <el-input-number v-model="localConfig.maxIterations" :min="1" :max="10000" @change="handleChange" />
    </el-form-item>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
const props = defineProps({ modelValue: { type: Object, default: () => ({}) } })
const emit = defineEmits(['update:modelValue', 'change'])
const localConfig = ref({ loopType: 'for', loopCondition: '', maxIterations: 100, ...props.modelValue })
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