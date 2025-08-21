<template>
  <div class="config-section">
    <h4>条件判断配置</h4>
    <el-form-item label="条件表达式">
      <el-input v-model="localConfig.conditionExpression" type="textarea" :rows="3" placeholder="例如: ${input.value} > 100" @change="handleChange" />
    </el-form-item>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
const props = defineProps({ modelValue: { type: Object, default: () => ({}) } })
const emit = defineEmits(['update:modelValue', 'change'])
const localConfig = ref({ conditionExpression: '', ...props.modelValue })
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