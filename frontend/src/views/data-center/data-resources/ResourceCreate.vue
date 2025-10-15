<template>
  <div class="resource-create">
    <div class="page-header">
      <h1>创建数据资源</h1>
      <p>添加新的数据资源到系统中</p>
    </div>

    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="120px"
      class="resource-form"
    >
      <el-card title="基本信息">
        <el-form-item label="资源名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入资源名称" />
        </el-form-item>
        
        <el-form-item label="显示名称" prop="display_name">
          <el-input v-model="form.display_name" placeholder="请输入显示名称" />
        </el-form-item>
        
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            placeholder="请输入资源描述"
          />
        </el-form-item>
        
        <el-form-item label="资源类型" prop="resource_type">
          <el-select v-model="form.resource_type" placeholder="请选择资源类型">
            <el-option label="Doris表" value="doris_table" />
            <el-option label="Elasticsearch索引" value="elasticsearch_index" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="分类" prop="category_id">
          <el-select v-model="form.category_id" placeholder="请选择分类">
            <el-option label="业务数据" :value="1" />
            <el-option label="日志数据" :value="2" />
            <el-option label="监控数据" :value="3" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="是否公开" prop="is_public">
          <el-switch v-model="form.is_public" />
        </el-form-item>
      </el-card>

      <el-card title="连接配置" style="margin-top: 20px;">
        <el-form-item label="主机地址" prop="connection_config.host">
          <el-input v-model="form.connection_config.host" placeholder="请输入主机地址" />
        </el-form-item>
        
        <el-form-item label="端口" prop="connection_config.port">
          <el-input-number v-model="form.connection_config.port" :min="1" :max="65535" />
        </el-form-item>
        
        <el-form-item label="数据库" prop="connection_config.database">
          <el-input v-model="form.connection_config.database" placeholder="请输入数据库名称" />
        </el-form-item>
        
        <el-form-item label="用户名" prop="connection_config.username">
          <el-input v-model="form.connection_config.username" placeholder="请输入用户名" />
        </el-form-item>
        
        <el-form-item label="密码" prop="connection_config.password">
          <el-input
            v-model="form.connection_config.password"
            type="password"
            placeholder="请输入密码"
            show-password
          />
        </el-form-item>
        
        <el-form-item label="表名" prop="table_name">
          <el-input v-model="form.table_name" placeholder="请输入表名" />
        </el-form-item>
        
        <el-form-item label="模式名" prop="schema_name">
          <el-input v-model="form.schema_name" placeholder="请输入模式名（可选）" />
        </el-form-item>
      </el-card>

      <div class="form-actions">
        <el-button @click="handleCancel">取消</el-button>
        <el-button type="primary" :loading="loading" @click="handleSubmit">
          创建资源
        </el-button>
      </div>
    </el-form>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import type { DataResourceCreateRequest } from '@/types/data-resource'

/**
 * 路由实例
 */
const router = useRouter()

/**
 * 表单引用
 */
const formRef = ref<FormInstance>()

/**
 * 加载状态
 */
const loading = ref(false)

/**
 * 表单数据
 */
const form = reactive<DataResourceCreateRequest>({
  name: '',
  display_name: '',
  description: '',
  resource_type: 'doris_table',
  category_id: 1,
  connection_config: {
    host: '',
    port: 9030,
    database: '',
    username: '',
    password: ''
  },
  table_name: '',
  schema_name: '',
  is_public: false
})

/**
 * 表单验证规则
 */
const rules: FormRules = {
  name: [
    { required: true, message: '请输入资源名称', trigger: 'blur' },
    { min: 2, max: 50, message: '长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  display_name: [
    { required: true, message: '请输入显示名称', trigger: 'blur' },
    { min: 2, max: 100, message: '长度在 2 到 100 个字符', trigger: 'blur' }
  ],
  resource_type: [
    { required: true, message: '请选择资源类型', trigger: 'change' }
  ],
  category_id: [
    { required: true, message: '请选择分类', trigger: 'change' }
  ],
  'connection_config.host': [
    { required: true, message: '请输入主机地址', trigger: 'blur' }
  ],
  'connection_config.port': [
    { required: true, message: '请输入端口', trigger: 'blur' }
  ],
  'connection_config.username': [
    { required: true, message: '请输入用户名', trigger: 'blur' }
  ],
  'connection_config.password': [
    { required: true, message: '请输入密码', trigger: 'blur' }
  ],
  table_name: [
    { required: true, message: '请输入表名', trigger: 'blur' }
  ]
}

/**
 * 提交表单
 */
const handleSubmit = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    loading.value = true
    
    // TODO: 调用创建API
    // await dataResourceApi.create(form)
    
    ElMessage.success('创建成功')
    router.push('/data-resources/list')
  } catch (error) {
    if (error !== false) {
      ElMessage.error('创建失败')
    }
  } finally {
    loading.value = false
  }
}

/**
 * 取消操作
 */
const handleCancel = () => {
  router.back()
}
</script>

<style scoped>
.resource-create {
  padding: 20px;
  max-width: 800px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 20px;
}

.page-header h1 {
  margin: 0 0 8px 0;
  font-size: 24px;
  font-weight: 600;
}

.page-header p {
  margin: 0;
  color: #666;
}

.resource-form {
  margin-bottom: 20px;
}

.form-actions {
  text-align: center;
  margin-top: 30px;
}

.form-actions .el-button {
  margin: 0 10px;
  min-width: 100px;
}
</style>