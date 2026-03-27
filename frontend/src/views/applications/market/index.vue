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
            <el-form-item label="镜像版本" required>
               <el-input v-model="globalConfig.version" placeholder="例如: latest, v1.0.0">
                 <template #append>
                   <el-tooltip content="在模板中使用 {{ version }} 引用此版本号" placement="top">
                     <el-icon><QuestionFilled /></el-icon>
                   </el-tooltip>
                 </template>
               </el-input>
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
                    <el-input 
                      v-else 
                      v-model="globalConfig[key]" 
                      :show-password="key.toLowerCase().includes('password')"
                      :type="key.toLowerCase().includes('password') ? 'password' : 'text'"
                    >
                      <template v-if="key.toLowerCase().includes('password')" #append>
                        <el-button @click="globalConfig[key] = generateRandomPassword()" title="重新生成">
                          <el-icon><Refresh /></el-icon>
                        </el-button>
                      </template>
                    </el-input>
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
                        <el-input 
                          v-else 
                          v-model="deploy.variables[key]" 
                          :show-password="key.toLowerCase().includes('password')"
                          :type="key.toLowerCase().includes('password') ? 'password' : 'text'"
                        >
                          <template v-if="key.toLowerCase().includes('password')" #append>
                            <el-button @click="deploy.variables[key] = generateRandomPassword()" title="重新生成">
                              <el-icon><Refresh /></el-icon>
                            </el-button>
                          </template>
                        </el-input>
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

const generateRandomPassword = (length = 16) => {
  const charset = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
  let ret = ''
  for (let i = 0; i < length; ++i) {
    ret += charset.charAt(Math.floor(Math.random() * charset.length))
  }
  return ret
}

// 提取模板处理逻辑
const processTemplateContent = (tplId: number) => {
  const tpl = templates.value.find(t => t.id === tplId)
  if (!tpl) return

  let content = tpl.deploy_template || ''
  
  // Auto-replace docker registry for Harbor and other apps using bitnami images
  // All public mirrors (docker.io, m.daocloud.io, swr, rainbond, 1ms.run) are failing (403 or Not Found).
  // 1ms.run also returned "not found" for postgresql:11.
  // We will NOT force replacement anymore and let the user decide.
  if (content.includes('bitnami/')) {
       // Matches: image: bitnami/..., image: "bitnami/...", image: docker.io/bitnami/...
       // Also handles potential leading spaces or quotes
       // content = content.replace(/image:\s*(["']?)(?:docker\.io\/)?bitnami\//g, 'image: $1docker.1ms.run/bitnami/')
       
       // We will append a comment to the top of the file to hint the user
        if (!content.includes('# HINT:')) {
            content = '# HINT: If you face 403/Not Found errors, try replacing "bitnami/" with "swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/bitnami/" or "public.ecr.aws/bitnami/" or your private registry.\n' + content
        }
  }
  
  currentDeployTemplate.value = content
  
  // 初始化全局配置
  const defaults = tpl.default_config ? JSON.parse(JSON.stringify(tpl.default_config)) : {}
  
  // 确保 schema 中的所有属性都在 globalConfig 中有定义
  if (tpl.config_schema?.properties) {
    Object.keys(tpl.config_schema.properties).forEach(key => {
        if (defaults[key] === undefined) {
            defaults[key] = '' // 初始化为空字符串，确保响应式
        }
        
        // 自动生成密码逻辑：只要 key 包含 password 且值为空
        if (key.toLowerCase().includes('password') && !defaults[key]) {
            defaults[key] = generateRandomPassword()
        }
    })
  }
  
  globalConfig.value = defaults
}

// 监听模板选择，初始化部署模板内容
watch(() => installForm.template_id, (newVal) => {
  if (newVal) {
    processTemplateContent(newVal)
  }
})

// 监听全局配置变化，同步到所有节点
watch(globalConfig, (newVal) => {
  if (installForm.deployments.length > 0) {
    installForm.deployments.forEach(deploy => {
      if (deploy.variables) {
        Object.keys(newVal).forEach(key => {
          // 不覆盖 ZOO_MY_ID，因为这是节点特有的配置
          if (key === 'ZOO_MY_ID') return
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
  
  // Force process template content to ensure replacements are applied even if template_id doesn't change
  processTemplateContent(item.id)
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

  // Harbor Registry Automatic Configuration
  const isHarbor = tpl?.name === 'harbor' || tpl?.name === 'harbor-registry'
  if (isHarbor && newDeployments.length > 0) {
    // For single node Harbor, we use the first server's IP as hostname
    const server = serverList.value.find(s => s.id === newDeployments[0].server_id)
    if (server) {
      if (globalConfig.value.hostname !== undefined) globalConfig.value.hostname = server.ip_address
      if (globalConfig.value.harbor_hostname !== undefined) globalConfig.value.harbor_hostname = server.ip_address
      if (globalConfig.value.external_url !== undefined) globalConfig.value.external_url = `http://${server.ip_address}`
    }
    
    // Default role
    newDeployments.forEach(deploy => {
      if (!deploy.role || (Array.isArray(deploy.role) && deploy.role.length === 0)) {
        deploy.role = 'default'
      }
    })
  }

  // PostgreSQL Cluster Automatic Role Assignment
  const isPostgres = tpl?.name?.toLowerCase().includes('postgres') || tpl?.name?.toLowerCase().includes('pgsql')
  if (isPostgres && newDeployments.length > 0) {
    // 1. Sort by IP Address
    newDeployments.sort((a, b) => {
      const serverA = serverList.value.find(s => s.id === a.server_id)
      const serverB = serverList.value.find(s => s.id === b.server_id)
      if (!serverA || !serverB) return 0
      return serverA.ip_address.localeCompare(serverB.ip_address, undefined, { numeric: true })
    })

    // 2. Assign Roles & Master IP
    let masterIp = ''
    newDeployments.forEach((deploy, index) => {
      const server = serverList.value.find(s => s.id === deploy.server_id)
      
      if (index === 0) {
        deploy.role = 'primary'
        if (server) masterIp = server.ip_address
      } else {
        deploy.role = 'read-replica'
      }
    })

    // 3. Update Global Config
    if (masterIp) {
       // Support various naming conventions for master host variable
       if (globalConfig.value.primary_ip !== undefined) globalConfig.value.primary_ip = masterIp
       if (globalConfig.value.master_ip !== undefined) globalConfig.value.master_ip = masterIp
       if (globalConfig.value.postgres_master_host !== undefined) globalConfig.value.postgres_master_host = masterIp
       if (globalConfig.value.POSTGRESQL_MASTER_HOST !== undefined) globalConfig.value.POSTGRESQL_MASTER_HOST = masterIp
    }
  }

  // Zookeeper Cluster Automatic Role Assignment
  const isZookeeper = tpl?.name?.toLowerCase().includes('zookeeper') || tpl?.name?.toLowerCase().includes('zk')
  if (isZookeeper && newDeployments.length > 0) {
    // 1. Sort by IP Address
    newDeployments.sort((a, b) => {
      const serverA = serverList.value.find(s => s.id === a.server_id)
      const serverB = serverList.value.find(s => s.id === b.server_id)
      if (!serverA || !serverB) return 0
      return serverA.ip_address.localeCompare(serverB.ip_address, undefined, { numeric: true })
    })

    // 2. Generate ZOO_SERVERS string and assign ZOO_MY_ID
    let zooServers: string[] = []
    newDeployments.forEach((deploy, index) => {
      const server = serverList.value.find(s => s.id === deploy.server_id)
      const myId = index + 1
      
      // 注意：这里的 role 如果在 schema 的 x-roles 中定义了，必须是数组才能被 el-select correctly 识别并显示
      // 区分主从角色：第一个节点作为 leader，其余作为 follower
      if (index === 0) {
        deploy.role = ['leader']
      } else {
        deploy.role = ['follower']
      }
      
      // Ensure deploy.variables is completely disconnected from globalConfig
      // so we don't accidentally modify the global object when assigning myId
      if (!deploy.variables) {
         deploy.variables = {}
      } else {
         deploy.variables = { ...deploy.variables } 
      }
      
      deploy.variables.ZOO_MY_ID = myId
      
      if (server) {
        // bitnami/zookeeper 镜像对 ZOO_SERVERS 的格式要求是只传 host:port:port::id 列表（空格分隔），
        // 或者不带角色的 host:port:port 或者 host:port:port::id
        // 从报错日志 java.net.UnknownHostException: server.2=10.20.1.211 来看，它不认识 `server.x=` 前缀
        // 所以我们必须去掉 `server.${myId}=` 这一部分
        let roleStr = ''
        if (deploy.role && deploy.role.includes('observer')) {
            roleStr = 'observer'
        }
        
        if (roleStr) {
            zooServers.push(`${server.ip_address}:2888:3888:${roleStr}::${myId}`)
        } else {
            zooServers.push(`${server.ip_address}:2888:3888::${myId}`)
        }
      }
    })

    // 3. Update Global Config
    if (zooServers.length > 0) {
       if (globalConfig.value.ZOO_SERVERS !== undefined) {
         globalConfig.value.ZOO_SERVERS = zooServers.join(' ')
       } else {
         globalConfig.value.ZOO_SERVERS = zooServers.join(' ')
       }
    }
  }

  // DolphinScheduler Automatic Role Assignment
  const isDolphin = tpl?.name?.toLowerCase().includes('dolphinscheduler') || tpl?.name?.toLowerCase().includes('dol')
  if (isDolphin && newDeployments.length > 0) {
    newDeployments.forEach((deploy) => {
      // By default, if the user selects a node, assign all roles to it
      // Users can manually remove the roles they don't want on specific nodes
      if (!deploy.role || deploy.role === 'default' || (Array.isArray(deploy.role) && deploy.role.length === 0)) {
        deploy.role = ['master', 'worker', 'api', 'alert']
      }
    })
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
        // 1. 全局配置：使用当前界面上的全局配置
        // Use the current reactive globalConfig which contains user inputs and auto-generated values
        const currentGlobalConfig = JSON.parse(JSON.stringify(globalConfig.value))
        
        // 2. 构造 config 对象
        submissionData.config = {
          global: currentGlobalConfig,
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
