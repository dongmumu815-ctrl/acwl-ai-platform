<template>
  <div class="app-container">
    <el-card>
      <template #header>
        <div class="clearfix">
          <span>技能测试运行器</span>
        </div>
      </template>

      <el-form :model="form" label-width="120px">
        <el-form-item label="选择技能">
          <el-select v-model="form.skill_names" multiple placeholder="请选择要测试的技能" style="width: 100%">
            <el-option
              v-for="item in skills"
              :key="item.name"
              :label="item.display_name + ' (' + item.name + ')'"
              :value="item.name"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="测试指令">
          <el-input
            v-model="form.prompt"
            type="textarea"
            :rows="4"
            placeholder="请输入测试指令，例如：帮我获取当前时间"
          />
        </el-form-item>
        
        <el-form-item label="模型配置ID" v-if="false">
            <el-input v-model="form.model_service_config_id" />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleExecute" :loading="loading">执行</el-button>
        </el-form-item>
      </el-form>

      <div v-if="result" class="result-section">
        <el-divider content-position="left">执行结果</el-divider>
        <div class="result-content">
          <pre>{{ result }}</pre>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import request from '@/utils/request'
import { ElMessage } from 'element-plus'

const skills = ref([])
const loading = ref(false)
const result = ref('')

const form = ref({
  skill_names: [],
  prompt: '',
  model_service_config_id: null
})

const fetchSkills = async () => {
  try {
    const res = await request({
      url: '/api/v1/agents/tools',
      method: 'get',
      params: {
        page: 1,
        size: 100,
        is_enabled: true
      }
    })
    skills.value = res.items || []
    
    // Auto select local_time if exists
    if (skills.value.find(s => s.name === 'local_time')) {
        if (!form.value.skill_names.includes('local_time')) {
            form.value.skill_names.push('local_time')
        }
        if (!form.value.prompt) {
            form.value.prompt = '请告诉我现在的本地时间是多少？'
        }
    }
    
  } catch (error) {
    console.error('Failed to fetch skills:', error)
  }
}

const handleExecute = async () => {
  if (!form.value.prompt) {
    ElMessage.warning('请输入测试指令')
    return
  }
  if (form.value.skill_names.length === 0) {
    ElMessage.warning('请选择至少一个技能')
    return
  }

  loading.value = true
  result.value = ''
  
  try {
    const res = await request({
      url: '/api/v1/agents/tools/execute',
      method: 'post',
      data: form.value
    })
    result.value = res.result
  } catch (error) {
    console.error('Execution failed:', error)
    result.value = `Error: ${error.message || 'Unknown error'}`
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchSkills()
})
</script>

<style scoped>
.result-section {
  margin-top: 20px;
}
.result-content {
  background-color: #f5f7fa;
  padding: 15px;
  border-radius: 4px;
  border: 1px solid #e4e7ed;
}
pre {
  white-space: pre-wrap;
  word-wrap: break-word;
  margin: 0;
  font-family: Consolas, Monaco, monospace;
}
</style>
