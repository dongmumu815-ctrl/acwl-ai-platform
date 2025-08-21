<template>
  <div class="config-section">
    <h4>数据合并配置</h4>
    <el-form-item label="合并类型">
      <el-select v-model="localConfig.joinType" @change="handleChange">
        <el-option label="内连接" value="inner" />
        <el-option label="左连接" value="left" />
        <el-option label="右连接" value="right" />
        <el-option label="全连接" value="full" />
      </el-select>
    </el-form-item>
    <el-form-item label="连接条件">
      <el-input v-model="localConfig.joinCondition" placeholder="例如: table1.id = table2.user_id" @change="handleChange" />
    </el-form-item>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
const props = defineProps({ modelValue: { type: Object, default: () => ({}) } })
const emit = defineEmits(['update:modelValue', 'change'])
const localConfig = ref({ joinType: 'inner', joinCondition: '', ...props.modelValue })
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