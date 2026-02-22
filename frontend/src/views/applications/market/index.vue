<template>
  <div class="market-page">
    <div class="page-header">
      <div class="header-left">
        <h2>应用市场</h2>
        <p class="description">浏览和安装应用模板，快速部署服务。</p>
      </div>
      <div class="header-actions">
        <el-input
          v-model="searchQuery"
          placeholder="搜索应用模板..."
          clearable
          class="search-input"
          @clear="handleSearch"
          @keyup.enter="handleSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-button @click="fetchTemplates">
          <el-icon><Refresh /></el-icon>
        </el-button>
        <el-button type="primary" @click="handleAdd">
          <el-icon><Plus /></el-icon>
          添加模板
        </el-button>
      </div>
    </div>

    <div v-loading="loading" class="template-grid">
      <el-empty v-if="!loading && templates.length === 0" description="暂无应用模板" />
      
      <el-card v-for="item in templates" :key="item.id" class="template-card" shadow="hover">
        <div class="card-header">
          <div class="icon-wrapper">
            <el-image v-if="item.icon" :src="item.icon" class="app-icon" />
            <el-icon v-else class="app-icon-placeholder" :size="40"><Box /></el-icon>
          </div>
          <div class="app-info">
            <h3 class="app-name">{{ item.display_name || item.name }}</h3>
            <span class="app-version">v{{ item.version }}</span>
          </div>
        </div>
        <div class="card-body">
          <p class="app-desc">{{ item.description || '暂无描述' }}</p>
          <div class="app-tags">
            <el-tag size="small" :type="getAppTypeTagType(item.app_type)" effect="plain">
              {{ formatAppType(item.app_type) }}
            </el-tag>
          </div>
        </div>
        <div class="card-footer">
          <el-button type="primary" plain block @click="handleInstall(item)">
            安装部署
          </el-button>
          <el-dropdown trigger="click" @command="(cmd) => handleAction(cmd, item)">
            <el-button link class="more-btn">
              <el-icon><MoreFilled /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="edit">编辑模板</el-dropdown-item>
                <el-dropdown-item command="delete" divided type="danger">删除</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-card>
    </div>

    <!-- Template Edit Dialog -->
    <el-dialog
      v-model="templateDialogVisible"
      :title="templateDialogType === 'create' ? '添加应用模板' : '编辑应用模板'"
      width="600px"
    >
      <el-form ref="templateFormRef" :model="templateForm" :rules="templateRules" label-width="100px">
        <el-form-item label="应用标识" prop="name">
          <el-input v-model="templateForm.name" placeholder="例如: doris" :disabled="templateDialogType === 'edit'" />
        </el-form-item>
        <el-form-item label="显示名称" prop="display_name">
          <el-input v-model="templateForm.display_name" placeholder="例如: Apache Doris" />
        </el-form-item>
        <el-form-item label="版本" prop="version">
          <el-input v-model="templateForm.version" placeholder="latest" />
        </el-form-item>
        <el-form-item label="应用类型" prop="app_type">
          <el-select v-model="templateForm.app_type">
            <el-option label="Docker Compose" value="docker_compose" />
            <el-option label="Docker Image" value="docker_image" />
            <el-option label="Shell Script" value="shell_script" />
          </el-select>
        </el-form-item>
        <el-form-item label="图标URL" prop="icon">
          <el-input v-model="templateForm.icon" placeholder="图标 URL" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="templateForm.description" type="textarea" :rows="3" />
        </el-form-item>
        <!-- Simplified config for now -->
        <el-form-item label="部署模板" prop="deploy_template">
          <el-input 
            v-model="templateForm.deploy_template" 
            type="textarea" 
            :rows="6" 
            placeholder="Docker Compose Content or Script" 
            style="font-family: monospace;"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="templateDialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="templateSubmitting" @click="submitTemplate">
            确定
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- Install Drawer -->
    <el-drawer
      v-model="installDialogVisible"
      title="安装应用"
      size="60%"
    >
      <el-form ref="installFormRef" :model="installForm" :rules="installRules" label-width="100px">
        <el-tabs v-model="activeInstallTab">
          <el-tab-pane label="基础配置" name="basic">
            <el-form-item label="应用名称" prop="name">
              <el-input v-model="installForm.name" placeholder="给实例起个名字" />
            </el-form-item>
            <el-form-item label="描述" prop="description">
              <el-input v-model="installForm.description" type="textarea" :rows="2" />
            </el-form-item>
            
            <el-divider content-position="left">部署模板</el-divider>
             <div class="template-editor-wrapper">
                <el-alert 
                  title="注意：您可以直接编辑下方的部署模板，支持 Jinja2 语法。"
                  type="info" 
                  show-icon 
                  :closable="false"
                  style="margin-bottom: 10px;"
                />
               <el-input
                  v-model="currentDeployTemplate"
                  type="textarea"
                  :rows="15"
                  placeholder="Docker Compose Template"
                  class="code-editor"
                />
             </div>

          </el-tab-pane>
          
          <el-tab-pane label="服务器配置" name="servers">
            <el-form-item label="选择服务器" required>
               <el-select
                v-model="selectedServerIds"
                multiple
                placeholder="请选择部署服务器"
                style="width: 100%"
              >
                <el-option
                  v-for="server in serverList"
                  :key="server.id"
                  :label="`${server.name} (${server.ip_address})`"
                  :value="server.id"
                />
              </el-select>
            </el-form-item>

            <!-- Global Configuration -->
            <el-card v-if="currentTemplateSchema && currentTemplateSchema.properties" class="global-config-card" shadow="never">
              <template #header>
                <div class="card-header">
                  <span>集群通用配置 (Global Config)</span>
                  <el-tooltip content="在此处修改将同步更新下方所有节点的配置" placement="top">
                    <el-icon><QuestionFilled /></el-icon>
                  </el-tooltip>
                </div>
              </template>
              <el-row :gutter="20">
                <el-col :span="12" v-for="(prop, key) in currentTemplateSchema.properties" :key="key">
                  <el-form-item 
                    :label="prop.title || key" 
                    label-width="160px"
                  >
                    <template #label>
                      <div class="form-label-with-help">
                        <span>{{ prop.title || key }}</span>
                        <el-tooltip v-if="prop.description" :content="prop.description" placement="top">
                            <el-icon class="help-icon"><QuestionFilled /></el-icon>
                        </el-tooltip>
                      </div>
                    </template>

                    <el-select v-if="prop.enum" v-model="globalConfig[key]" style="width: 100%">
                      <el-option v-for="opt in prop.enum" :key="opt" :label="opt" :value="opt" />
                    </el-select>
                    <el-input-number 
                      v-else-if="prop.type === 'integer' || prop.type === 'number'" 
                      v-model="globalConfig[key]" 
                      style="width: 100%"
                    />
                    <el-switch v-else-if="prop.type === 'boolean'" v-model="globalConfig[key]" />
                    <el-input v-else v-model="globalConfig[key]" />
                  </el-form-item>
                </el-col>
              </el-row>
            </el-card>

            <div v-for="(deploy, index) in installForm.deployments" :key="index" class="deployment-config">
              <div class="deployment-header">
                <span>{{ getServerName(deploy.server_id) }}</span>
                <el-button link type="danger" @click="removeDeployment(index)">移除</el-button>
              </div>
              <el-row :gutter="20">
                <el-col :span="12">
                  <el-form-item label="角色" :prop="'deployments.' + index + '.role'" label-width="160px">
                    <el-select v-if="availableRoles" v-model="deploy.role" placeholder="Select Role" style="width: 100%" multiple collapse-tags collapse-tags-tooltip>
                       <el-option v-for="role in availableRoles" :key="role" :label="role" :value="role" />
                    </el-select>
                    <el-input v-else v-model="deploy.role" placeholder="default/master/worker" />
                  </el-form-item>
                </el-col>
                
                <!-- 动态渲染配置项 -->
                <template v-if="currentTemplateSchema && currentTemplateSchema.properties">
                  <template v-for="(prop, key) in currentTemplateSchema.properties" :key="key">
                    <el-col :span="12" v-if="shouldShowConfig(key, deploy)">
                      <el-form-item 
                        :label="prop.title || key" 
                        :prop="'deployments.' + index + '.variables.' + key"
                        :rules="getVariableRules(key, prop)"
                        label-width="160px"
                      >
                        <template #label>
                          <div class="form-label-with-help">
                            <span>{{ prop.title || key }}</span>
                            <el-tooltip v-if="prop.description" :content="prop.description" placement="top">
                              <el-icon class="help-icon"><QuestionFilled /></el-icon>
                            </el-tooltip>
                          </div>
                        </template>

                        <el-select v-if="prop.enum" v-model="deploy.variables[key]" style="width: 100%">
                          <el-option v-for="opt in prop.enum" :key="opt" :label="opt" :value="opt" />
                        </el-select>
                        <el-input-number 
                          v-else-if="prop.type === 'integer' || prop.type === 'number'" 
                          v-model="deploy.variables[key]" 
                          style="width: 100%"
                        />
                        <el-switch v-else-if="prop.type === 'boolean'" v-model="deploy.variables[key]" />
                        <el-input v-else v-model="deploy.variables[key]" />
                      </el-form-item>
                    </el-col>
                  </template>
                </template>
              </el-row>
            </div>
          </el-tab-pane>
        </el-tabs>

      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="installDialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="installSubmitting" @click="submitInstall">
            开始安装
          </el-button>
        </span>
      </template>
    </el-drawer>

  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Box, MoreFilled, QuestionFilled, Search, Refresh } from '@element-plus/icons-vue'
import { getAppTemplates, createAppTemplate, updateAppTemplate, deleteAppTemplate, createAppInstance } from '@/api/application'
import { getServers } from '@/api/servers'
import type { AppTemplate, AppTemplateForm, AppInstanceForm, AppDeploymentForm } from '@/api/application'
import type { ServerResponse } from '@/api/servers'

// --- State ---
const router = useRouter()
const loading = ref(false)
const searchQuery = ref('')
const templates = ref<AppTemplate[]>([])
const serverList = ref<ServerResponse[]>([])

// --- Template Dialog ---
const templateDialogVisible = ref(false)
const templateDialogType = ref<'create' | 'edit'>('create')
const templateSubmitting = ref(false)
const templateFormRef = ref()
const currentTemplateId = ref<number | null>(null)

const templateForm = reactive<AppTemplateForm>({
  name: '',
  display_name: '',
  version: 'latest',
  description: '',
  icon: '',
  app_type: 'docker_compose',
  deploy_template: '',
  is_system: false
})

const templateRules = {
  name: [{ required: true, message: '请输入应用标识', trigger: 'blur' }],
  app_type: [{ required: true, message: '请选择应用类型', trigger: 'change' }]
}

const activeInstallTab = ref('basic')
const currentDeployTemplate = ref('')

// --- Install Dialog ---
const installDialogVisible = ref(false)
const installSubmitting = ref(false)
const installFormRef = ref()
const selectedServerIds = ref<number[]>([])

const installForm = reactive<AppInstanceForm>({
  name: '',
  template_id: undefined,
  description: '',
  deployments: []
})

const installRules = {
  name: [{ required: true, message: '请输入实例名称', trigger: 'blur' }]
}

const globalConfig = ref<any>({})

// 获取当前模板的 schema
const currentTemplateSchema = computed(() => {
  if (!installForm.template_id) return null
  const tpl = templates.value.find(t => t.id === installForm.template_id)
  return tpl?.config_schema
})

const availableRoles = computed(() => {
  const schema = currentTemplateSchema.value
  return schema?.['x-roles'] || null
})

// 监听模板选择，初始化部署模板内容
watch(() => installForm.template_id, (newVal) => {
  if (newVal) {
    const tpl = templates.value.find(t => t.id === newVal)
    if (tpl) {
      currentDeployTemplate.value = tpl.deploy_template || ''
      // 初始化全局配置
      globalConfig.value = tpl.default_config ? JSON.parse(JSON.stringify(tpl.default_config)) : {}
    }
  }
})

// 监听全局配置变化，同步到所有节点
watch(globalConfig, (newVal) => {
  if (installForm.deployments.length > 0) {
    installForm.deployments.forEach(deploy => {
      // 简单策略：如果节点变量存在于全局配置中，则更新
      // 实际上，为了方便，我们直接把所有变量都同步过去
      // 用户如果想覆盖，可以在节点配置里改，但是下次改全局又会被覆盖
      // 改进：只同步那些“之前和全局一样”的值？太复杂。
      // 策略：强制同步。Global Config 意为“批量设置”。
      if (deploy.variables) {
        Object.keys(newVal).forEach(key => {
          deploy.variables[key] = newVal[key]
        })
      }
    })
  }
}, { deep: true })

// 生成校验规则
const getVariableRules = (key: string, prop: any) => {
  const rules = []
  const schema = currentTemplateSchema.value
  if (schema?.required?.includes(key)) {
    rules.push({ required: true, message: `${prop.title || key} 必填`, trigger: 'blur' })
  }
  return rules
}

const shouldShowConfig = (key: string, deploy: any) => {
  const role = deploy.role
  
  // Define role-specific config keys
  const feConfigs = ['fe_memory', 'fe_memory_limit']
  const beConfigs = ['be_memory_limit']
  
  // If config is not in our specific lists, always show it
  if (!feConfigs.includes(key) && !beConfigs.includes(key)) {
    return true
  }
  
  // Determine if the current role includes FE or BE capability
  let hasFe = false
  let hasBe = false
  
  if (Array.isArray(role)) {
    hasFe = role.some(r => r.includes('fe-master') || r.includes('fe-follower'))
    hasBe = role.includes('be')
  } else if (typeof role === 'string' && role) {
    hasFe = role.includes('fe')
    hasBe = role.includes('be')
  }
  
  // Filter based on role capability
  if (feConfigs.includes(key)) return hasFe
  if (beConfigs.includes(key)) return hasBe
  
  return true
}

// --- Methods ---

const getAppTypeTagType = (type: string) => {
  switch (type) {
    case 'docker_compose': return 'primary'
    case 'docker_image': return 'success'
    case 'shell_script': return 'warning'
    default: return 'info'
  }
}

const formatAppType = (type: string) => {
  switch (type) {
    case 'docker_compose': return 'Docker Compose'
    case 'docker_image': return 'Docker Image'
    case 'shell_script': return 'Shell Script'
    default: return type
  }
}

const handleSearch = () => {
  fetchTemplates()
}

const fetchTemplates = async () => {
  loading.value = true
  try {
    const params: any = { page: 1, size: 100 }
    if (searchQuery.value) {
      params.keyword = searchQuery.value
    }
    const res = await getAppTemplates(params)
    templates.value = res.items
  } catch (error) {
    console.error(error)
    ElMessage.error('获取应用模板失败')
  } finally {
    loading.value = false
  }
}

const fetchServers = async () => {
  try {
    const res = await getServers({ 
      page: 1, 
      size: 1000, 
      sort_by: 'created_at',
      sort_order: 'desc' 
    })
    serverList.value = res.items
  } catch (error) {
    console.error(error)
  }
}

const getServerName = (id: number) => {
  const server = serverList.value.find(s => s.id === id)
  return server ? `${server.name} (${server.ip_address})` : `Server ${id}`
}

// Template CRUD
const handleAdd = () => {
  templateDialogType.value = 'create'
  currentTemplateId.value = null
  Object.assign(templateForm, {
    name: '',
    display_name: '',
    version: 'latest',
    description: '',
    icon: '',
    app_type: 'docker_compose',
    deploy_template: '',
    is_system: false
  })
  templateDialogVisible.value = true
}

const handleAction = (cmd: string, item: AppTemplate) => {
  if (cmd === 'edit') {
    templateDialogType.value = 'edit'
    currentTemplateId.value = item.id
    Object.assign(templateForm, {
      name: item.name,
      display_name: item.display_name,
      version: item.version,
      description: item.description,
      icon: item.icon,
      app_type: item.app_type,
      deploy_template: item.deploy_template,
      is_system: item.is_system
    })
    templateDialogVisible.value = true
  } else if (cmd === 'delete') {
    ElMessageBox.confirm('确定要删除该模板吗？', '提示', { type: 'warning' })
      .then(async () => {
        await deleteAppTemplate(item.id)
        ElMessage.success('删除成功')
        fetchTemplates()
      })
  }
}

const submitTemplate = async () => {
  if (!templateFormRef.value) return
  await templateFormRef.value.validate(async (valid: boolean) => {
    if (valid) {
      templateSubmitting.value = true
      try {
        if (templateDialogType.value === 'create') {
          await createAppTemplate(templateForm)
          ElMessage.success('创建成功')
        } else {
          await updateAppTemplate(currentTemplateId.value!, templateForm)
          ElMessage.success('更新成功')
        }
        templateDialogVisible.value = false
        fetchTemplates()
      } catch (error) {
        console.error(error)
      } finally {
        templateSubmitting.value = false
      }
    }
  })
}

// Install Flow
const handleInstall = (item: AppTemplate) => {
  Object.assign(installForm, {
    name: `${item.name}-instance`,
    template_id: item.id,
    description: `Deploying ${item.display_name || item.name} v${item.version}`,
    deployments: []
  })
  selectedServerIds.value = []
  installDialogVisible.value = true
}

// Watch selected servers to update deployments list
watch(selectedServerIds, (newIds) => {
  const tpl = templates.value.find(t => t.id === installForm.template_id)
  const isDoris = tpl?.name === 'apache-doris'
  const hasRoles = !!(tpl?.config_schema?.['x-roles'])

  // Keep existing configs if server is still selected
  const newDeployments: AppDeploymentForm[] = []
  
  newIds.forEach(id => {
    const existing = installForm.deployments.find(d => d.server_id === id)
    if (existing) {
      newDeployments.push(existing)
    } else {
      const defaultVars = JSON.parse(JSON.stringify(globalConfig.value)) // 使用当前的 globalConfig 初始化
      
      newDeployments.push({
        server_id: id,
        role: hasRoles ? [] : 'default',
        cpu_limit: '',
        mem_limit: '',
        variables: defaultVars
      } as any)
    }
  })
  
  // Apache Doris Automatic Role Assignment Strategy
  if (isDoris && newDeployments.length > 0) {
    // 1. Sort by IP Address
    newDeployments.sort((a, b) => {
      const serverA = serverList.value.find(s => s.id === a.server_id)
      const serverB = serverList.value.find(s => s.id === b.server_id)
      if (!serverA || !serverB) return 0
      // Simple string comparison for IP works well enough for 10.20.1.x
      return serverA.ip_address.localeCompare(serverB.ip_address, undefined, { numeric: true })
    })

    // 2. Assign Roles & Master IP
    let masterIp = ''
    newDeployments.forEach((deploy, index) => {
      const server = serverList.value.find(s => s.id === deploy.server_id)
      
      if (index === 0) {
        deploy.role = ['fe-master', 'be']
        if (server) masterIp = server.ip_address
      } else if (index === 1 || index === 2) {
        deploy.role = ['fe-follower', 'be']
      } else {
        deploy.role = ['be']
      }
    })

    // 3. Update Global Config with Master IP
    if (masterIp) {
      globalConfig.value.fe_master_ip = masterIp
    }
  }

  installForm.deployments = newDeployments
})

const removeDeployment = (index: number) => {
  const deploy = installForm.deployments[index]
  selectedServerIds.value = selectedServerIds.value.filter(id => id !== deploy.server_id)
}

const submitInstall = async () => {
  if (!installFormRef.value) return
  if (installForm.deployments.length === 0) {
    ElMessage.warning('请至少选择一个部署服务器')
    return
  }
  
  await installFormRef.value.validate(async (valid: boolean) => {
    if (valid) {
      installSubmitting.value = true
      try {
        // 构造提交数据
        const submissionData = JSON.parse(JSON.stringify(installForm))
        
        // 处理配置覆盖
        // 1. 全局配置：使用模板默认值
        const tpl = templates.value.find(t => t.id === installForm.template_id)
        const globalConfig = tpl?.default_config ? JSON.parse(JSON.stringify(tpl.default_config)) : {}
        
        // 2. 构造 config 对象
        submissionData.config = {
          global: globalConfig,
          overrides: {}
        }
        
        // 如果用户修改了模板，将其放入 config 中
        if (currentDeployTemplate.value) {
            submissionData.config.deploy_template = currentDeployTemplate.value
        }
        
        // 3. 处理每个部署
        submissionData.deployments.forEach((deploy: any) => {
          // Convert array role to string
          if (Array.isArray(deploy.role)) {
             deploy.role = deploy.role.join(',')
          }

          // 提取标准字段
          if (deploy.variables?.cpu_limit) deploy.cpu_limit = deploy.variables.cpu_limit
          if (deploy.variables?.mem_limit) deploy.mem_limit = deploy.variables.mem_limit
          
          // 存入 overrides
          if (deploy.variables) {
             // 必须转为 string key
            submissionData.config.overrides[String(deploy.server_id)] = deploy.variables
          }
          
          // 清理前端临时字段
          delete deploy.variables
        })

        await createAppInstance(submissionData)
        ElMessage.success('应用安装任务已创建')
        installDialogVisible.value = false
        
        ElMessageBox.confirm(
          '应用实例创建成功，是否前往应用列表查看部署进度？',
          '部署启动成功',
          {
            confirmButtonText: '前往查看',
            cancelButtonText: '留在此处',
            type: 'success'
          }
        ).then(() => {
          router.push('/applications/list')
        }).catch(() => {})
        
      } catch (error) {
        console.error(error)
      } finally {
        installSubmitting.value = false
      }
    }
  })
}

onMounted(() => {
  fetchTemplates()
  fetchServers()
})
</script>

<style scoped>
.market-page {
  padding: 20px;
  background-color: #f5f7fa;
  min-height: 100%;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.header-left h2 {
  margin: 0 0 8px 0;
  font-size: 20px;
  font-weight: 500;
}

.header-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.search-input {
  width: 240px;
}

.description {
  color: #666;
  font-size: 14px;
  margin: 0;
}

.template-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
}

.template-card {
  transition: all 0.3s;
}

.template-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
}

.icon-wrapper {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  background-color: #f0f2f5;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 16px;
}

.app-icon {
  width: 32px;
  height: 32px;
}

.app-icon-placeholder {
  color: #909399;
}

.app-info {
  flex: 1;
  overflow: hidden;
}

.app-name {
  margin: 0 0 4px 0;
  font-size: 16px;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.app-version {
  font-size: 12px;
  color: #909399;
  background-color: #f4f4f5;
  padding: 2px 6px;
  border-radius: 4px;
}

.card-body {
  margin-bottom: 20px;
  height: 80px; /* Fixed height for consistency */
}

.app-desc {
  color: #606266;
  font-size: 14px;
  line-height: 1.5;
  margin: 0 0 12px 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-footer {
  display: flex;
  align-items: center;
  gap: 12px;
}

.more-btn {
  padding: 8px;
}

.global-config-card {
  margin-bottom: 24px;
  border-left: 4px solid #409eff;
}

.deployment-config {
  margin-top: 24px;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 4px;
  border: 1px solid #ebeef5;
}

.deployment-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 1px solid #e4e7ed;
  font-weight: 500;
  font-size: 16px;
}

.form-label-with-help {
  display: flex;
  align-items: center;
  gap: 4px;
}

.help-icon {
  color: #909399;
  cursor: help;
  font-size: 14px;
}
.code-editor :deep(.el-textarea__inner) {
  font-family: 'Menlo', 'Monaco', 'Courier New', monospace;
  background-color: #f8f9fa;
  color: #303133;
}

.template-editor-wrapper {
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  padding: 10px;
  background-color: #fff;
}
</style>
