<template>
  <div class="config-section">
    <h4>文件处理配置</h4>
    
    <el-form-item label="操作类型">
      <el-select v-model="localConfig.operation" placeholder="选择操作" @change="handleChange">
        <el-option label="读取文件" value="read" />
        <el-option label="写入文件" value="write" />
        <el-option label="追加内容" value="append" />
        <el-option label="删除文件" value="delete" />
        <el-option label="复制文件" value="copy" />
        <el-option label="移动文件" value="move" />
      </el-select>
    </el-form-item>
    
    <el-form-item label="文件路径">
      <el-input 
        v-model="localConfig.path" 
        placeholder="/path/to/file.txt"
        @change="handleChange"
      />
    </el-form-item>

    <template v-if="['copy', 'move'].includes(localConfig.operation)">
      <el-form-item label="目标路径">
        <el-input 
          v-model="localConfig.destPath" 
          placeholder="/path/to/destination"
          @change="handleChange"
        />
      </el-form-item>
    </template>

    <template v-if="['write', 'append'].includes(localConfig.operation)">
      <el-form-item label="写入内容">
        <el-input 
          v-model="localConfig.content" 
          type="textarea" 
          :rows="5"
          placeholder="输入要写入的内容..."
          @change="handleChange"
        />
      </el-form-item>
    </template>

    <el-form-item label="编码格式">
      <el-select v-model="localConfig.encoding" @change="handleChange">
        <el-option label="UTF-8" value="utf-8" />
        <el-option label="GBK" value="gbk" />
        <el-option label="ASCII" value="ascii" />
      </el-select>
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
  operation: 'read',
  path: '',
  destPath: '',
  content: '',
  encoding: 'utf-8',
  ...props.modelValue
})

watch(() => props.modelValue, (newValue) => {
  localConfig.value = { 
    operation: 'read',
    path: '',
    destPath: '',
    content: '',
    encoding: 'utf-8',
    ...newValue 
  }
}, { deep: true })

const handleChange = () => {
  emit('update:modelValue', localConfig.value)
  emit('change', localConfig.value)
}
</script>
