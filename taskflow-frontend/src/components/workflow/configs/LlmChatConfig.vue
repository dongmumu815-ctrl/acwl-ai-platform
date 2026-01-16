<template>
  <div class="config-section">
    <h4>大语言模型配置</h4>
    
    <el-form-item label="模型提供商">
      <el-select v-model="localConfig.provider" placeholder="选择提供商" @change="handleChange">
        <el-option label="OpenAI" value="openai" />
        <el-option label="Anthropic" value="anthropic" />
        <el-option label="Local (Ollama)" value="ollama" />
        <el-option label="Azure OpenAI" value="azure" />
      </el-select>
    </el-form-item>
    
    <el-form-item label="模型名称">
      <el-select v-model="localConfig.model" placeholder="选择模型" @change="handleChange">
        <el-option label="GPT-4o" value="gpt-4o" />
        <el-option label="GPT-3.5 Turbo" value="gpt-3.5-turbo" />
        <el-option label="Claude 3.5 Sonnet" value="claude-3-5-sonnet" />
        <el-option label="Llama 3" value="llama3" />
      </el-select>
    </el-form-item>

    <el-form-item label="温度 (Temperature)">
      <el-slider 
        v-model="localConfig.temperature" 
        :min="0" 
        :max="1" 
        :step="0.1" 
        show-input
        @change="handleChange"
      />
    </el-form-item>

    <el-form-item label="系统提示词">
      <el-input 
        v-model="localConfig.systemPrompt" 
        type="textarea" 
        :rows="3"
        placeholder="设定AI的角色和行为准则..."
        @change="handleChange"
      />
    </el-form-item>

    <el-form-item label="用户提示词">
      <el-input 
        v-model="localConfig.userPrompt" 
        type="textarea" 
        :rows="5"
        placeholder="输入问题或任务描述，支持 {{ variable }} 变量..."
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
  provider: 'openai',
  model: 'gpt-3.5-turbo',
  temperature: 0.7,
  systemPrompt: '',
  userPrompt: '',
  ...props.modelValue
})

watch(() => props.modelValue, (newValue) => {
  localConfig.value = { 
    provider: 'openai',
    model: 'gpt-3.5-turbo',
    temperature: 0.7,
    systemPrompt: '',
    userPrompt: '',
    ...newValue 
  }
}, { deep: true })

const handleChange = () => {
  emit('update:modelValue', localConfig.value)
  emit('change', localConfig.value)
}
</script>
