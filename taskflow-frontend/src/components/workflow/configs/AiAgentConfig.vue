<template>
  <div class="config-section">
    <h4>AI智能体配置</h4>
    
    <el-form-item label="智能体名称">
      <el-input 
        v-model="localConfig.agentName" 
        placeholder="给智能体起个名字"
        @change="handleChange"
      />
    </el-form-item>
    
    <el-form-item label="角色设定">
      <el-input 
        v-model="localConfig.role" 
        type="textarea" 
        :rows="3"
        placeholder="定义智能体的角色和专业领域..."
        @change="handleChange"
      />
    </el-form-item>

    <el-form-item label="任务目标">
      <el-input 
        v-model="localConfig.goal" 
        type="textarea" 
        :rows="3"
        placeholder="描述智能体需要完成的具体目标..."
        @change="handleChange"
      />
    </el-form-item>

    <el-form-item label="可用工具">
      <el-checkbox-group v-model="localConfig.tools" @change="handleChange">
        <el-checkbox value="web_search">网络搜索</el-checkbox>
        <el-checkbox value="code_interpreter">代码解释器</el-checkbox>
        <el-checkbox value="file_browser">文件浏览</el-checkbox>
        <el-checkbox value="calculator">计算器</el-checkbox>
      </el-checkbox-group>
    </el-form-item>

    <el-form-item label="思考模式">
      <el-select v-model="localConfig.thinkingMode" @change="handleChange">
        <el-option label="ReAct (推理+行动)" value="react" />
        <el-option label="CoT (思维链)" value="cot" />
        <el-option label="Direct (直接回答)" value="direct" />
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
  agentName: '',
  role: '',
  goal: '',
  tools: [],
  thinkingMode: 'react',
  ...props.modelValue
})

watch(() => props.modelValue, (newValue) => {
  localConfig.value = { 
    agentName: '',
    role: '',
    goal: '',
    tools: [],
    thinkingMode: 'react',
    ...newValue 
  }
}, { deep: true })

const handleChange = () => {
  emit('update:modelValue', localConfig.value)
  emit('change', localConfig.value)
}
</script>
