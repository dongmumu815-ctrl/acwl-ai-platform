<template>
  <div class="config-section">
    <h4>Shell脚本配置</h4>
    
    <el-form-item label="执行方式">
      <el-radio-group v-model="localConfig.executeType" @change="handleChange">
        <el-radio label="inline">内联脚本</el-radio>
        <el-radio label="file">脚本文件</el-radio>
      </el-radio-group>
    </el-form-item>
    
    <el-form-item label="脚本内容" v-if="localConfig.executeType === 'inline'">
      <el-input 
        v-model="localConfig.script" 
        type="textarea"
        :rows="8"
        placeholder="输入Shell脚本内容"
        @change="handleChange"
      />
    </el-form-item>
    
    <el-form-item label="脚本文件路径" v-if="localConfig.executeType === 'file'">
      <el-input 
        v-model="localConfig.scriptPath" 
        placeholder="输入脚本文件路径"
        @change="handleChange"
      />
    </el-form-item>
    
    <el-form-item label="命令参数">
      <div class="arguments-list">
        <div 
          v-for="(arg, index) in localConfig.arguments" 
          :key="index"
          class="argument-item"
        >
          <el-input 
            v-model="localConfig.arguments[index]" 
            placeholder="参数值"
            @change="handleChange"
          />
          <el-button 
            @click="removeArgument(index)" 
            size="small" 
            type="danger" 
            text
          >
            删除
          </el-button>
        </div>
        <el-button @click="addArgument" size="small" type="primary" text>
          + 添加参数
        </el-button>
      </div>
    </el-form-item>
    
    <el-form-item label="工作目录">
      <el-input 
        v-model="localConfig.workingDirectory" 
        placeholder="脚本执行的工作目录（可选）"
        @change="handleChange"
      />
    </el-form-item>
    
    <el-form-item label="环境变量">
      <div class="env-vars-list">
        <div 
          v-for="(envVar, index) in localConfig.environmentVariables" 
          :key="index"
          class="env-var-item"
        >
          <el-input 
            v-model="envVar.name" 
            placeholder="变量名"
            @change="handleChange"
          />
          <span class="separator">=</span>
          <el-input 
            v-model="envVar.value" 
            placeholder="变量值"
            @change="handleChange"
          />
          <el-button 
            @click="removeEnvVar(index)" 
            size="small" 
            type="danger" 
            text
          >
            删除
          </el-button>
        </div>
        <el-button @click="addEnvVar" size="small" type="primary" text>
          + 添加环境变量
        </el-button>
      </div>
    </el-form-item>
    
    <el-form-item label="Shell类型">
      <el-select v-model="localConfig.shellType" @change="handleChange">
        <el-option label="Bash" value="bash" />
        <el-option label="Zsh" value="zsh" />
        <el-option label="PowerShell" value="powershell" />
        <el-option label="CMD" value="cmd" />
      </el-select>
    </el-form-item>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

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
const localConfig = ref({
  executeType: 'inline',
  script: '',
  scriptPath: '',
  arguments: [],
  workingDirectory: '',
  environmentVariables: [],
  shellType: 'bash',
  ...props.modelValue
})

// 监听外部配置变化
watch(() => props.modelValue, (newValue) => {
  localConfig.value = { ...localConfig.value, ...newValue }
}, { deep: true })

/**
 * 添加参数
 */
const addArgument = () => {
  localConfig.value.arguments.push('')
  handleChange()
}

/**
 * 删除参数
 */
const removeArgument = (index) => {
  localConfig.value.arguments.splice(index, 1)
  handleChange()
}

/**
 * 添加环境变量
 */
const addEnvVar = () => {
  localConfig.value.environmentVariables.push({ name: '', value: '' })
  handleChange()
}

/**
 * 删除环境变量
 */
const removeEnvVar = (index) => {
  localConfig.value.environmentVariables.splice(index, 1)
  handleChange()
}

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

.arguments-list, .env-vars-list {
  border: 1px solid #e8e8e8;
  border-radius: 4px;
  padding: 8px;
  background: #fff;
}

.argument-item, .env-var-item {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.argument-item:last-of-type, .env-var-item:last-of-type {
  margin-bottom: 8px;
}

.separator {
  font-weight: bold;
  color: #666;
}

.env-var-item .el-input:first-child {
  flex: 1;
}

.env-var-item .el-input:last-of-type {
  flex: 2;
}
</style>