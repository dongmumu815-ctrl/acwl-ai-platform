<template>
  <div class="register-container">
    <!-- 背景装饰 -->
    <div class="register-background">
      <div class="bg-shape shape-1"></div>
      <div class="bg-shape shape-2"></div>
      <div class="bg-shape shape-3"></div>
    </div>
    
    <!-- 注册表单 -->
    <div class="register-form-container">
      <div class="register-form">
        <!-- Logo和标题 -->
        <div class="register-header">
          <div class="logo">
            <img src="/logo.svg" alt="ACWL AI" class="logo-image" />
          </div>
          <h1 class="title">创建账户</h1>
          <p class="subtitle">加入 ACWL AI Platform，开启您的AI之旅</p>
        </div>
        
        <!-- 表单 -->
        <el-form
          ref="registerFormRef"
          :model="registerForm"
          :rules="registerRules"
          class="form"
          size="large"
          @keyup.enter="handleRegister"
        >
          <el-form-item prop="username">
            <el-input
              v-model="registerForm.username"
              placeholder="请输入用户名"
              prefix-icon="User"
              clearable
            />
          </el-form-item>
          
          <el-form-item prop="email">
            <el-input
              v-model="registerForm.email"
              placeholder="请输入邮箱"
              prefix-icon="Message"
              clearable
            />
          </el-form-item>
          
          <el-form-item prop="password">
            <el-input
              v-model="registerForm.password"
              type="password"
              placeholder="请输入密码"
              prefix-icon="Lock"
              show-password
              clearable
            />
          </el-form-item>
          
          <el-form-item prop="confirmPassword">
            <el-input
              v-model="registerForm.confirmPassword"
              type="password"
              placeholder="请确认密码"
              prefix-icon="Lock"
              show-password
              clearable
            />
          </el-form-item>
          
          <el-form-item prop="phone">
            <el-input
              v-model="registerForm.phone"
              placeholder="请输入手机号（可选）"
              prefix-icon="Phone"
              clearable
            />
          </el-form-item>
          
          <el-form-item prop="agreement">
            <el-checkbox v-model="registerForm.agreement">
              我已阅读并同意
              <el-link type="primary" @click="showTerms">
                《用户协议》
              </el-link>
              和
              <el-link type="primary" @click="showPrivacy">
                《隐私政策》
              </el-link>
            </el-checkbox>
          </el-form-item>
          
          <el-form-item>
            <el-button
              type="primary"
              class="register-button"
              :loading="loading"
              @click="handleRegister"
            >
              {{ loading ? '注册中...' : '立即注册' }}
            </el-button>
          </el-form-item>
        </el-form>
        
        <!-- 登录链接 -->
        <div class="login-link">
          <span>已有账户？</span>
          <el-link type="primary" @click="$router.push('/login')">
            立即登录
          </el-link>
        </div>
        
        <!-- 第三方注册 -->
        <div class="social-register">
          <el-divider>
            <span class="divider-text">或使用以下方式注册</span>
          </el-divider>
          
          <div class="social-buttons">
            <el-button class="social-button github" @click="handleSocialRegister('github')">
              <el-icon><svg viewBox="0 0 1024 1024"><path d="M512 12.64c-282.752 0-512 229.216-512 512 0 226.208 146.688 418.144 350.08 485.824 25.6 4.736 35.008-11.104 35.008-24.64 0-12.192-0.48-52.544-0.704-95.328-142.464 30.976-172.512-60.416-172.512-60.416-23.296-59.168-56.832-74.912-56.832-74.912-46.464-31.776 3.52-31.136 3.52-31.136 51.392 3.616 78.464 52.768 78.464 52.768 45.664 78.272 119.776 55.648 148.992 42.56 4.576-33.088 17.856-55.68 32.512-68.48-113.728-12.928-233.216-56.864-233.216-253.024 0-55.904 19.936-101.568 52.672-137.408-5.312-12.896-22.848-64.96 4.96-135.488 0 0 42.88-13.76 140.8 52.48 40.832-11.36 84.64-17.024 128.16-17.248 43.488 0.192 87.328 5.888 128.256 17.248 97.728-66.24 140.64-52.48 140.64-52.48 27.872 70.528 10.336 122.592 5.024 135.488 32.832 35.84 52.608 81.504 52.608 137.408 0 196.64-119.776 239.936-233.856 252.64 18.368 15.904 34.72 47.04 34.72 94.816 0 68.512-0.608 123.648-0.608 140.512 0 13.632 9.216 29.6 35.168 24.576C877.472 942.08 1024 750.208 1024 524.64c0-282.784-229.248-512-512-512z"/></svg></el-icon>
              GitHub
            </el-button>
            
            <el-button class="social-button google" @click="handleSocialRegister('google')">
              <el-icon><svg viewBox="0 0 1024 1024"><path d="M881 442.4H519.7v148.5h206.4c-8.9 48-35.9 88.6-76.6 115.8-34.4 23-78.3 36.6-129.9 36.6-99.9 0-184.4-67.5-214.6-158.2-7.6-23-12-47.6-12-72.9s4.4-49.9 12-72.9c30.3-90.6 114.8-158.1 214.6-158.1 56.3 0 106.8 19.4 146.6 57.4l110-110.1c-66.5-62-153.2-100-256.6-100-149.9 0-279.6 86.8-342.7 213.1C59.2 295.6 51.4 357.9 51.4 512s7.8 216.4 40.8 299.9C155.3 937.2 285 1024 434.9 1024c120.7 0 217.6-39.6 290.4-115.1 76.4-79.3 119.7-196.5 119.7-329.8 0-19.8-1.5-39.7-4.9-59.6z"/></svg></el-icon>
              Google
            </el-button>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 用户协议对话框 -->
    <el-dialog v-model="termsVisible" title="用户协议" width="600px">
      <div class="terms-content">
        <h3>1. 服务条款</h3>
        <p>欢迎使用 ACWL AI Platform。通过访问和使用本平台，您同意遵守以下条款和条件。</p>
        
        <h3>2. 用户责任</h3>
        <p>用户应当合法使用本平台提供的服务，不得从事任何违法违规活动。</p>
        
        <h3>3. 知识产权</h3>
        <p>本平台的所有内容和技术均受知识产权法保护。</p>
        
        <h3>4. 免责声明</h3>
        <p>本平台不对用户使用服务过程中产生的任何损失承担责任。</p>
      </div>
      <template #footer>
        <el-button @click="termsVisible = false">关闭</el-button>
      </template>
    </el-dialog>
    
    <!-- 隐私政策对话框 -->
    <el-dialog v-model="privacyVisible" title="隐私政策" width="600px">
      <div class="privacy-content">
        <h3>1. 信息收集</h3>
        <p>我们收集您提供的个人信息，包括但不限于姓名、邮箱、电话号码等。</p>
        
        <h3>2. 信息使用</h3>
        <p>我们使用收集的信息来提供和改进我们的服务。</p>
        
        <h3>3. 信息保护</h3>
        <p>我们采用行业标准的安全措施来保护您的个人信息。</p>
        
        <h3>4. 信息共享</h3>
        <p>除法律要求外，我们不会与第三方共享您的个人信息。</p>
      </div>
      <template #footer>
        <el-button @click="privacyVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { useUserStore } from '@/stores/user'
import type { RegisterForm } from '@/types/auth'

const router = useRouter()
const userStore = useUserStore()

const registerFormRef = ref<FormInstance>()
const loading = ref(false)
const termsVisible = ref(false)
const privacyVisible = ref(false)

// 注册表单数据
const registerForm = reactive<RegisterForm>({
  username: '',
  email: '',
  password: '',
  confirmPassword: '',
  phone: '',
  agreement: false
})

// 确认密码验证
const validateConfirmPassword = (rule: any, value: any, callback: any) => {
  if (value === '') {
    callback(new Error('请确认密码'))
  } else if (value !== registerForm.password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

// 表单验证规则
const registerRules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度在 3 到 20 个字符', trigger: 'blur' },
    { pattern: /^[a-zA-Z0-9_]+$/, message: '用户名只能包含字母、数字和下划线', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 8, message: '密码长度不能少于8位', trigger: 'blur' },
    { pattern: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d@$!%*?&]{8,}$/, message: '密码必须包含大小写字母和数字', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, validator: validateConfirmPassword, trigger: 'blur' }
  ],
  phone: [
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号格式', trigger: 'blur' }
  ],
  agreement: [
    { required: true, message: '请阅读并同意用户协议和隐私政策', trigger: 'change' }
  ]
}

// 处理注册
const handleRegister = async () => {
  if (!registerFormRef.value) return
  
  try {
    await registerFormRef.value.validate()
    loading.value = true
    
    await userStore.register(registerForm)
    
    ElMessage.success('注册成功，请登录')
    router.push('/login')
  } catch (error: any) {
    console.error('注册失败:', error)
    ElMessage.error(error.message || '注册失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

// 第三方注册
const handleSocialRegister = (provider: string) => {
  ElMessage.info(`${provider} 注册功能开发中...`)
}

// 显示用户协议
const showTerms = () => {
  termsVisible.value = true
}

// 显示隐私政策
const showPrivacy = () => {
  privacyVisible.value = true
}
</script>

<style lang="scss" scoped>
.register-container {
  position: relative;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  overflow: hidden;
  
  .register-background {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    z-index: 1;
    
    .bg-shape {
      position: absolute;
      border-radius: 50%;
      background: rgba(255, 255, 255, 0.1);
      animation: float 6s ease-in-out infinite;
      
      &.shape-1 {
        width: 200px;
        height: 200px;
        top: 10%;
        left: 10%;
        animation-delay: 0s;
      }
      
      &.shape-2 {
        width: 150px;
        height: 150px;
        top: 60%;
        right: 10%;
        animation-delay: 2s;
      }
      
      &.shape-3 {
        width: 100px;
        height: 100px;
        bottom: 20%;
        left: 20%;
        animation-delay: 4s;
      }
    }
  }
  
  .register-form-container {
    position: relative;
    z-index: 2;
    width: 100%;
    max-width: 450px;
    padding: 20px;
    
    .register-form {
      background: rgba(255, 255, 255, 0.95);
      backdrop-filter: blur(10px);
      border-radius: 16px;
      padding: 40px;
      box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
      
      .register-header {
        text-align: center;
        margin-bottom: 32px;
        
        .logo {
          margin-bottom: 16px;
          
          .logo-image {
            width: 64px;
            height: 64px;
          }
        }
        
        .title {
          font-size: 24px;
          font-weight: 600;
          color: #2c3e50;
          margin: 0 0 8px 0;
        }
        
        .subtitle {
          font-size: 14px;
          color: #7f8c8d;
          margin: 0;
        }
      }
      
      .form {
        .register-button {
          width: 100%;
          height: 44px;
          font-size: 16px;
          font-weight: 500;
        }
      }
      
      .login-link {
        text-align: center;
        margin-top: 24px;
        font-size: 14px;
        color: #7f8c8d;
        
        .el-link {
          margin-left: 4px;
        }
      }
      
      .social-register {
        margin-top: 24px;
        
        .divider-text {
          font-size: 12px;
          color: #bdc3c7;
        }
        
        .social-buttons {
          display: flex;
          gap: 12px;
          margin-top: 16px;
          
          .social-button {
            flex: 1;
            height: 40px;
            border: 1px solid #e1e8ed;
            background: white;
            color: #657786;
            
            &:hover {
              border-color: #1da1f2;
              color: #1da1f2;
            }
            
            .el-icon {
              margin-right: 8px;
              
              svg {
                width: 16px;
                height: 16px;
              }
            }
            
            &.github:hover {
              border-color: #333;
              color: #333;
            }
            
            &.google:hover {
              border-color: #4285f4;
              color: #4285f4;
            }
          }
        }
      }
    }
  }
}

.terms-content,
.privacy-content {
  max-height: 400px;
  overflow-y: auto;
  
  h3 {
    color: #2c3e50;
    margin-top: 20px;
    margin-bottom: 10px;
    
    &:first-child {
      margin-top: 0;
    }
  }
  
  p {
    color: #7f8c8d;
    line-height: 1.6;
    margin-bottom: 15px;
  }
}

@keyframes float {
  0%, 100% {
    transform: translateY(0px);
  }
  50% {
    transform: translateY(-20px);
  }
}

// 响应式设计
@media (max-width: 480px) {
  .register-container {
    padding: 20px;
    
    .register-form-container {
      .register-form {
        padding: 24px;
        
        .social-register {
          .social-buttons {
            flex-direction: column;
          }
        }
      }
    }
  }
}

// 暗色主题
.dark {
  .register-container {
    background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
    
    .register-form {
      background: rgba(44, 62, 80, 0.95) !important;
      
      .title {
        color: #ecf0f1 !important;
      }
      
      .subtitle {
        color: #bdc3c7 !important;
      }
    }
  }
  
  .terms-content,
  .privacy-content {
    h3 {
      color: #ecf0f1;
    }
    
    p {
      color: #bdc3c7;
    }
  }
}
</style>