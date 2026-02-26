<template>
  <div class="skill-edit-container">
    <div class="toolbar">
      <div class="left">
        <el-button link @click="cancel">
          <el-icon><ArrowLeft /></el-icon> 返回
        </el-button>
        <span class="page-title">{{ isEdit ? '编辑技能' : '新增技能' }}</span>
        <el-tag v-if="form.name" size="small" style="margin-left: 10px">{{ form.name }}</el-tag>
      </div>
      <div class="right">
        <el-button :icon="Setting" @click="schemaDrawerVisible = true">配置 Schema</el-button>
        <el-button type="success" :icon="MagicStick" @click="handleGenerateCode" :loading="generating" plain>AI 生成</el-button>
        <el-button type="primary" @click="submitForm" :loading="saving">保存 (Ctrl+S)</el-button>
      </div>
    </div>
    
    <div class="main-content">
       <el-form ref="formRef" :model="form" :rules="rules" label-width="80px" class="meta-form">
          <el-row :gutter="20">
             <el-col :span="6">
                <el-form-item label="标识符" prop="name">
                  <el-input v-model="form.name" :disabled="isEdit" placeholder="英文唯一标识" />
                </el-form-item>
             </el-col>
             <el-col :span="6">
                <el-form-item label="名称" prop="display_name">
                  <el-input v-model="form.display_name" placeholder="显示名称" />
                </el-form-item>
             </el-col>
             <el-col :span="6">
                <el-form-item label="类型" prop="tool_type">
                  <el-select v-model="form.tool_type" placeholder="类型" style="width: 100%">
                    <el-option label="自定义代码" value="custom" />
                    <el-option label="API 接口" value="api" />
                  </el-select>
                </el-form-item>
             </el-col>
             <el-col :span="6">
                <el-form-item label="描述" prop="description">
                  <el-input v-model="form.description" placeholder="简短描述" />
                </el-form-item>
             </el-col>
          </el-row>
       </el-form>
       
       <div class="editor-area" v-if="form.tool_type === 'custom'">
          <SkillIde 
             ref="skillIdeRef"
             v-model="fileMap" 
             @save="submitForm"
          />
       </div>
       
       <div class="api-editor-area" v-else>
          <el-empty description="API 类型暂未支持可视化编辑，请使用 JSON Schema 配置" />
       </div>
    </div>

    <!-- Schema Drawer -->
    <el-drawer v-model="schemaDrawerVisible" title="配置参数 Schema" size="50%">
       <div class="schema-editor-container">
          <el-alert title="定义工具的输入参数结构 (JSON Schema)" type="info" :closable="false" style="margin-bottom: 10px" />
          <el-input
             v-model="configSchemaJson"
             type="textarea"
             :rows="20"
             placeholder="JSON Schema for configuration"
             style="font-family: monospace;"
           />
       </div>
    </el-drawer>

    <!-- Code Generation Dialog -->
    <el-dialog v-model="generateDialogVisible" title="AI 生成代码" width="600px" append-to-body>
       <el-form label-position="top">
         <el-form-item label="选择模型">
            <el-select v-model="selectedModelConfigId" placeholder="请选择用于生成的模型" style="width: 100%">
              <el-option
                v-for="item in modelConfigs"
                :key="item.model_id"
                :label="item.label + ' (' + item.provider_display_name + ')'"
                :value="item.model_id"
              />
            </el-select>
         </el-form-item>
         <el-form-item label="需求描述">
           <el-input 
             v-model="generateRequirements" 
             type="textarea" 
             :rows="6" 
             placeholder="请描述该技能的功能、输入输出参数等。例如：创建一个查询天气预报的工具，输入参数为城市名称。" 
           />
         </el-form-item>
         <el-alert title="生成将覆盖当前所有文件结构，请谨慎操作。" type="warning" show-icon :closable="false" />
       </el-form>
       <template #footer>
         <el-button @click="generateDialogVisible = false">取消</el-button>
         <el-button type="primary" @click="confirmGenerate" :loading="generating">开始生成</el-button>
       </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { MagicStick, ArrowLeft, Setting } from '@element-plus/icons-vue'
import { getAgentTool, createAgentTool, updateAgentTool, generateAgentToolCode } from '@/api/agents'
import { modelServiceConfigApi } from '@/api/model-service-configs'
import SkillIde from './components/SkillIde.vue'

const route = useRoute()
const router = useRouter()
const formRef = ref()
const skillIdeRef = ref()

const isEdit = computed(() => !!route.params.id)
const id = computed(() => Number(route.params.id))
const saving = ref(false)
const schemaDrawerVisible = ref(false)

const form = reactive({
  name: '',
  display_name: '',
  description: '',
  tool_type: 'custom',
  code: '',
  config_schema: {},
  default_config: {},
  is_enabled: true
})

const configSchemaJson = computed({
  get: () => JSON.stringify(form.config_schema, null, 2),
  set: (val) => {
    try {
      form.config_schema = JSON.parse(val)
    } catch (e) {
      // ignore parse error during typing
    }
  }
})

// File Editor Logic
const fileMap = ref<Record<string, string>>({
  'SKILL.md': '# Skill Name\n\n## Instructions\n'
})

const rules = {
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
  display_name: [{ required: true, message: '请输入显示名称', trigger: 'blur' }],
  tool_type: [{ required: true, message: '请选择类型', trigger: 'change' }]
}

// AI Generation state
const generateDialogVisible = ref(false)
const generateRequirements = ref('')
const generating = ref(false)
const modelConfigs = ref<any[]>([])
const selectedModelConfigId = ref<number | undefined>(undefined)

const loadData = async () => {
  if (!isEdit.value) return
  try {
    const data = await getAgentTool(id.value)
    form.name = data.name
    form.display_name = data.display_name
    form.description = data.description || ''
    form.tool_type = data.tool_type
    form.code = data.code || ''
    form.config_schema = data.config_schema || {}
    form.default_config = data.default_config || {}
    form.is_enabled = data.is_enabled
    
    try {
        const parsed = JSON.parse(form.code)
        if (typeof parsed === 'object' && parsed !== null && !Array.isArray(parsed)) {
            fileMap.value = parsed
        } else {
            throw new Error('Not a file map')
        }
    } catch (e) {
        if (form.code && form.code.trim()) {
            console.warn('Failed to parse skill code:', e)
            // ElMessage.warning('代码格式解析失败，已加载为普通文件')
            fileMap.value = {
                'legacy_script.py': form.code,
                'SKILL.md': '# ' + form.name + '\n\nConverted from legacy code.'
            }
        } else {
             fileMap.value = {
                'SKILL.md': '# ' + form.name + '\n\n'
            }
        }
    }
    
    // Open default file
    setTimeout(() => {
        if (skillIdeRef.value) {
            const files = Object.keys(fileMap.value)
            const readme = files.find(f => f === 'SKILL.md') || files[0]
            if (readme) skillIdeRef.value.openFile(readme)
        }
    }, 200)
    
  } catch (error) {
    console.error(error)
    ElMessage.error('加载数据失败')
  }
}

const submitForm = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid: boolean) => {
    if (valid) {
      saving.value = true
      form.code = JSON.stringify(fileMap.value)
      
      try {
        if (isEdit.value) {
          await updateAgentTool(id.value, form)
        } else {
          await createAgentTool(form)
        }
        ElMessage.success('保存成功')
        if (!isEdit.value) {
             router.push('/agents/skills')
        }
      } catch (error) {
        ElMessage.error('保存失败')
      } finally {
        saving.value = false
      }
    }
  })
}

const cancel = () => {
  router.push('/agents/skills')
}

// AI Generation
const fetchModelConfigs = async () => {
  try {
    const res = await modelServiceConfigApi.getAvailableConfigs()
    modelConfigs.value = res
    if (modelConfigs.value.length > 0) {
      const defaultModel = modelConfigs.value.find((m: any) => m.is_default)
      selectedModelConfigId.value = defaultModel ? defaultModel.model_id : modelConfigs.value[0].model_id
    }
  } catch (error) {
    console.error(error)
  }
}

const handleGenerateCode = () => {
  generateRequirements.value = ''
  generateDialogVisible.value = true
  fetchModelConfigs()
}

const confirmGenerate = async () => {
  if (!generateRequirements.value.trim()) {
    ElMessage.warning('请输入需求描述')
    return
  }
  
  generating.value = true
  try {
    const res = await generateAgentToolCode({
      requirements: generateRequirements.value,
      model_service_config_id: selectedModelConfigId.value
    })
    
    if (res.code_structure) {
      fileMap.value = res.code_structure
      
      // Auto open relevant file
      const keys = Object.keys(fileMap.value)
      if (keys.length > 0 && skillIdeRef.value) {
          const mainFile = keys.find(k => k === 'SKILL.md' || k === '__init__.py') || keys[0]
          skillIdeRef.value.openFile(mainFile)
      }
      
      ElMessage.success('代码生成成功')
      generateDialogVisible.value = false
    } else {
      ElMessage.warning('生成结果为空，请重试')
    }
  } catch (error) {
    console.error(error)
    ElMessage.error('生成失败')
  } finally {
    generating.value = false
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.skill-edit-container {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 50px); /* Adjust based on AppMain padding/header */
  background-color: #f0f2f5;
}

.toolbar {
  height: 50px;
  background-color: #fff;
  border-bottom: 1px solid #dcdfe6;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.05);
  flex-shrink: 0;
}

.left {
  display: flex;
  align-items: center;
}

.page-title {
  font-size: 16px;
  font-weight: 600;
  margin-left: 10px;
  color: #303133;
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 10px;
  overflow: hidden;
}

.meta-form {
  background-color: #fff;
  padding: 15px 15px 0 15px;
  border-radius: 4px;
  margin-bottom: 10px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.05);
  flex-shrink: 0;
}

.editor-area {
  flex: 1;
  overflow: hidden;
  border-radius: 4px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.05);
}

.api-editor-area {
  flex: 1;
  background-color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
