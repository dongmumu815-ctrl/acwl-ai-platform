<template>
  <div class="config-section">
    <h4>数据输入配置</h4>
    <el-form-item label="数据源类型">
      <el-select v-model="localConfig.dataSource" @change="handleChange">
        <el-option label="MySQL" value="mysql" />
        <el-option label="PostgreSQL" value="postgresql" />
        <el-option label="SQLite" value="sqlite" />
        <el-option label="CSV文件" value="csv" />
        <el-option label="JSON文件" value="json" />
        <el-option label="Excel文件" value="excel" />
      </el-select>
    </el-form-item>
    
    <el-form-item label="连接字符串" v-if="isDatabaseSource">
      <el-input 
        v-model="localConfig.connectionString" 
        type="textarea"
        :rows="2"
        placeholder="例如: mysql://user:password@host:port/database"
        @change="handleChange"
      />
    </el-form-item>
    
    <el-form-item label="文件路径" v-if="isFileSource">
      <el-input 
        v-model="localConfig.filePath" 
        placeholder="输入文件路径"
        @change="handleChange"
      />
    </el-form-item>
    
    <el-form-item label="表名" v-if="isDatabaseSource">
      <el-input 
        v-model="localConfig.tableName" 
        placeholder="输入表名"
        @change="handleChange"
      />
    </el-form-item>
    
    <el-form-item label="查询语句" v-if="isDatabaseSource">
      <el-input 
        v-model="localConfig.query" 
        type="textarea"
        :rows="4"
        placeholder="输入SQL查询语句（可选，留空则查询整个表）"
        @change="handleChange"
      />
    </el-form-item>
    
    <el-form-item label="编码格式" v-if="isFileSource">
      <el-select v-model="localConfig.encoding" @change="handleChange">
        <el-option label="UTF-8" value="utf-8" />
        <el-option label="GBK" value="gbk" />
        <el-option label="ASCII" value="ascii" />
      </el-select>
    </el-form-item>
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue'

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
const localConfig = ref({ ...props.modelValue })

// 监听外部配置变化
watch(() => props.modelValue, (newValue) => {
  localConfig.value = { ...newValue }
}, { deep: true })

// 计算属性
const isDatabaseSource = computed(() => {
  return ['mysql', 'postgresql', 'sqlite'].includes(localConfig.value.dataSource)
})

const isFileSource = computed(() => {
  return ['csv', 'json', 'excel'].includes(localConfig.value.dataSource)
})

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