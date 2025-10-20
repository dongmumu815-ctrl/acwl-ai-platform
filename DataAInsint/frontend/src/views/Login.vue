<template>
  <div class="login-container">
    <div class="login-box">
      <div class="login-header">
        <h1>DataAInsight</h1>
        <p>奥诚未来 · 数据探查工具 </p>
      </div>
      
      <el-form 
        ref="loginForm" 
        :model="loginData" 
        :rules="rules" 
        class="login-form"
        @submit.prevent="handleLogin"
      >
        <el-form-item prop="secretKey">
          <el-input
            v-model="loginData.secretKey"
            type="password"
            placeholder="请输入访问密钥"
            size="large"
            show-password
            @keyup.enter="handleLogin"
          >
            <template #prefix>
              <el-icon><Key /></el-icon>
            </template>
          </el-input>
        </el-form-item>
        
        <el-form-item>
          <el-button 
            type="primary" 
            size="large" 
            :loading="loading" 
            @click="handleLogin"
            class="login-button"
          >
            {{ loading ? '验证中...' : '登录' }}
          </el-button>
        </el-form-item>
      </el-form>
      
      <div class="login-footer">
        <p>请输入正确的访问密钥以使用系统功能</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Key } from '@element-plus/icons-vue'
import { login } from '@/api/auth'

const router = useRouter()
const loginForm = ref()
const loading = ref(false)

const loginData = reactive({
  secretKey: ''
})

const rules = {
  secretKey: [
    { required: true, message: '请输入访问密钥', trigger: 'blur' },
    { min: 1, message: '密钥不能为空', trigger: 'blur' }
  ]
}

const handleLogin = async () => {
  try {
    const valid = await loginForm.value.validate()
    if (!valid) return
    
    loading.value = true
    
    const response = await login(loginData.secretKey)
    
    if (response.success) {
      // 保存token到localStorage
      localStorage.setItem('auth_token', response.token)
      
      ElMessage.success('登录成功')
      
      // 跳转到主页
      router.push('/')
    } else {
      ElMessage.error(response.message || '登录失败')
    }
  } catch (error) {
    console.error('登录错误:', error)
    ElMessage.error('登录失败，请检查密钥是否正确')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.login-box {
  width: 100%;
  max-width: 400px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  padding: 40px;
  text-align: center;
}

.login-header {
  margin-bottom: 40px;
}

.login-header h1 {
  font-size: 32px;
  font-weight: bold;
  color: #2c3e50;
  margin: 0 0 8px 0;
}

.login-header p {
  color: #7f8c8d;
  font-size: 16px;
  margin: 0;
}

.login-form {
  margin-bottom: 30px;
}

.login-button {
  width: 100%;
  height: 48px;
  font-size: 16px;
  font-weight: 500;
}

.login-footer {
  color: #95a5a6;
  font-size: 14px;
}

.login-footer p {
  margin: 0;
}

:deep(.el-input__inner) {
  height: 48px;
  font-size: 16px;
}

:deep(.el-form-item) {
  margin-bottom: 24px;
}
</style>