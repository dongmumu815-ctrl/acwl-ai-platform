<template>
  <div class="config-section">
    <h4>SQL执行配置</h4>
    
    <el-form-item label="数据源">
      <el-select v-model="localConfig.datasourceId" placeholder="选择数据源" @change="handleChange">
        <el-option label="主数据库 (MySQL)" value="ds_1" />
        <el-option label="数据仓库 (ClickHouse)" value="ds_2" />
        <el-option label="测试库 (PostgreSQL)" value="ds_3" />
      </el-select>
    </el-form-item>
    
    <el-form-item label="SQL语句">
      <el-input 
        v-model="localConfig.sql" 
        type="textarea" 
        :rows="6"
        placeholder="SELECT * FROM table WHERE id = {{ input.id }}"
        @change="handleChange"
      />
      <div class="help-text">支持使用 {{ variable }} 语法引用上下文变量</div>
    </el-form-item>

    <el-form-item label="操作类型">
      <el-radio-group v-model="localConfig.operationType" @change="handleChange">
        <el-radio value="query">查询</el-radio>
        <el-radio value="update">更新/非查询</el-radio>
      </el-radio-group>
    </el-form-item>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  modelValue: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['update:modelValue', 'change'])

const localConfig = ref({
  datasourceId: '',
  sql: '',
  operationType: 'query',
  ...props.modelValue
})

watch(() => props.modelValue, (newValue) => {
  localConfig.value = { 
    datasourceId: '',
    sql: '',
    operationType: 'query',
    ...newValue 
  }
}, { deep: true })

const handleChange = () => {
  emit('update:modelValue', localConfig.value)
  emit('change', localConfig.value)
}
</script>

<style scoped>
.help-text {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}
</style>
