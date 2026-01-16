<template>
  <div class="config-section">
    <h4>邮件发送配置</h4>
    
    <el-form-item label="收件人">
      <el-input 
        v-model="localConfig.to" 
        placeholder="email@example.com"
        @change="handleChange"
      />
      <div class="help-text">多个收件人请用逗号分隔</div>
    </el-form-item>
    
    <el-form-item label="主题">
      <el-input 
        v-model="localConfig.subject" 
        placeholder="邮件主题"
        @change="handleChange"
      />
    </el-form-item>

    <el-form-item label="正文类型">
      <el-radio-group v-model="localConfig.contentType" @change="handleChange">
        <el-radio value="text">纯文本</el-radio>
        <el-radio value="html">HTML</el-radio>
      </el-radio-group>
    </el-form-item>

    <el-form-item label="邮件内容">
      <el-input 
        v-model="localConfig.content" 
        type="textarea" 
        :rows="6"
        placeholder="邮件正文内容..."
        @change="handleChange"
      />
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
  to: '',
  subject: '',
  contentType: 'text',
  content: '',
  ...props.modelValue
})

watch(() => props.modelValue, (newValue) => {
  localConfig.value = { 
    to: '',
    subject: '',
    contentType: 'text',
    content: '',
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
}
</style>
