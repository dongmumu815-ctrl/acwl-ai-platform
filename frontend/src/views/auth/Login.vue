<template>
  <div class="login-container">
    <!-- 背景装饰 -->
    <div class="login-background">
      <div class="bg-shape shape-1"></div>
      <div class="bg-shape shape-2"></div>
      <div class="bg-shape shape-3"></div>
    </div>
    
    <!-- 登录表单 -->
    <div class="login-form-container">
      <div class="login-form">
        <!-- Logo和标题 -->
        <div class="login-header">
          <div class="logo">
            <img src="/logo.svg" alt="AI算力中心" class="logo-image" />
          </div>
          <h1 class="title">AI算力中心</h1>
        </div>
        
        <!-- 表单 -->
        <el-form
          ref="loginFormRef"
          :model="loginForm"
          :rules="loginRules"
          class="form"
          size="large"
          @keyup.enter="handleLogin"
        >
          <el-form-item prop="account">
            <el-input
              v-model="loginForm.account"
              placeholder="请输入用户名或邮箱"
              prefix-icon="User"
              clearable
            />
          </el-form-item>
          
          <el-form-item prop="password">
            <el-input
              v-model="loginForm.password"
              type="password"
              placeholder="请输入密码"
              prefix-icon="Lock"
              show-password
              clearable
            />
          </el-form-item>
          
          <el-form-item>
            <div class="form-options">
              <el-checkbox v-model="loginForm.remember">
                记住我
              </el-checkbox>
              <el-link type="primary" @click="$router.push('/forgot-password')">
                忘记密码？
              </el-link>
            </div>
          </el-form-item>
          
          <el-form-item>
            <el-button
              type="primary"
              class="login-button"
              :loading="loading"
              @click="handleLogin"
            >
              {{ loading ? '登录中...' : '登录' }}
            </el-button>
          </el-form-item>
        </el-form>
        
        <!-- 注册链接 -->
        <!-- <div class="register-link">
          <span>还没有账户？</span>
          <el-link type="primary" @click="$router.push('/register')">
            立即注册
          </el-link>
        </div> -->
        
        <!-- 第三方登录 -->
        <!-- <div class="social-login">
          <el-divider>
            <span class="divider-text">或使用以下方式登录</span>
          </el-divider>
          
          <div class="social-buttons">
            <el-button class="social-button github" @click="handleSocialLogin('github')">
              <el-icon><svg viewBox="0 0 1024 1024"><path d="M512 12.64c-282.752 0-512 229.216-512 512 0 226.208 146.688 418.144 350.08 485.824 25.6 4.736 35.008-11.104 35.008-24.64 0-12.192-0.48-52.544-0.704-95.328-142.464 30.976-172.512-60.416-172.512-60.416-23.296-59.168-56.832-74.912-56.832-74.912-46.464-31.776 3.52-31.136 3.52-31.136 51.392 3.616 78.464 52.768 78.464 52.768 45.664 78.272 119.776 55.648 148.992 42.56 4.576-33.088 17.856-55.68 32.512-68.48-113.728-12.928-233.216-56.864-233.216-253.024 0-55.904 19.936-101.568 52.672-137.408-5.312-12.896-22.848-64.96 4.96-135.488 0 0 42.88-13.76 140.8 52.48 40.832-11.36 84.64-17.024 128.16-17.248 43.488 0.192 87.328 5.888 128.256 17.248 97.728-66.24 140.64-52.48 140.64-52.48 27.872 70.528 10.336 122.592 5.024 135.488 32.832 35.84 52.608 81.504 52.608 137.408 0 196.64-119.776 239.936-233.856 252.64 18.368 15.904 34.72 47.04 34.72 94.816 0 68.512-0.608 123.648-0.608 140.512 0 13.632 9.216 29.6 35.168 24.576C877.472 942.08 1024 750.208 1024 524.64c0-282.784-229.248-512-512-512z"/></svg></el-icon>
              GitHub
            </el-button>
            
            <el-button class="social-button google" @click="handleSocialLogin('google')">
              <el-icon><svg viewBox="0 0 1024 1024"><path d="M881 442.4H519.7v148.5h206.4c-8.9 48-35.9 88.6-76.6 115.8-34.4 23-78.3 36.6-129.9 36.6-99.9 0-184.4-67.5-214.6-158.2-7.6-23-12-47.6-12-72.9s4.4-49.9 12-72.9c30.3-90.6 114.8-158.1 214.6-158.1 56.3 0 106.8 19.4 146.6 57.4l110-110.1c-66.5-62-153.2-100-256.6-100-149.9 0-279.6 86.8-342.7 213.1C59.2 295.6 51.4 357.9 51.4 512s7.8 216.4 40.8 299.9C155.3 937.2 285 1024 434.9 1024c120.7 0 217.6-39.6 290.4-115.1 76.4-79.3 119.7-196.5 119.7-329.8 0-19.8-1.5-39.7-4.9-59.6z"/></svg></el-icon>
              Google
            </el-button>
          </div>
        </div> -->
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { useUserStore } from '@/stores/user'
import type { LoginForm } from '@/types/auth'

const router = useRouter()
const userStore = useUserStore()

const loginFormRef = ref<FormInstance>()
const loading = ref(false)

// 登录表单视图数据（用户名或邮箱 + 密码）
const loginForm = reactive({
  account: 'admin',
  password: 'password',
  remember: false
})

// 表单验证规则
const loginRules: FormRules = {
  account: [
    { required: true, message: '请输入用户名或邮箱', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
  ]
}

/**
 * 提交登录
 * 将单一输入的“用户名或邮箱”映射为后端所需的 `username` 或 `email` 字段
 */
const handleLogin = async () => {
  if (!loginFormRef.value) return
  
  try {
    await loginFormRef.value.validate()
    loading.value = true

    // 判定是否为邮箱
    const isEmail = /.+@.+\..+/.test(loginForm.account)
    // 构造后端需要的登录数据
    const payload: LoginForm = {
      password: loginForm.password,
      ...(isEmail ? { email: loginForm.account } : { username: loginForm.account }),
      remember: loginForm.remember
    }
    
    await userStore.login(payload)
    
    ElMessage.success('登录成功')
    
    // 跳转到首页或之前访问的页面
    const redirect = router.currentRoute.value.query.redirect as string
    router.push(redirect || '/dashboard')
  } catch (error: any) {
    console.error('登录失败:', error)
    ElMessage.error(error.message || '登录失败，请检查用户名和密码')
  } finally {
    loading.value = false
  }
}

/**
 * 第三方登录入口
 */
const handleSocialLogin = (provider: string) => {
  ElMessage.info(`${provider} 登录功能开发中...`)
}
</script>

<style lang="scss" scoped>
.login-container {
  position: relative;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  overflow: hidden;
  
  .login-background {
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
  
  .login-form-container {
    position: relative;
    z-index: 2;
    width: 100%;
    max-width: 400px;
    padding: 20px;
    
    .login-form {
      background: rgba(255, 255, 255, 0.95);
      backdrop-filter: blur(10px);
      border-radius: 16px;
      padding: 40px;
      box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
      
      .login-header {
        display: flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 32px;
        
        .logo {
          margin-right: 16px;
          
          .logo-image {
            width: 48px;
            height: 48px;
          }
        }
        
        .title {
          font-size: 24px;
          font-weight: 600;
          color: #2c3e50;
          margin: 0;
        }
        
        .subtitle {
          font-size: 14px;
          color: #7f8c8d;
          margin: 0;
        }
      }
      
      .form {
        .form-options {
          display: flex;
          justify-content: space-between;
          align-items: center;
          width: 100%;
        }
        
        .login-button {
          width: 100%;
          height: 44px;
          font-size: 16px;
          font-weight: 500;
        }
      }
      
      .register-link {
        text-align: center;
        margin-top: 24px;
        font-size: 14px;
        color: #7f8c8d;
        
        .el-link {
          margin-left: 4px;
        }
      }
      
      .social-login {
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
  .login-container {
    padding: 20px;
    
    .login-form-container {
      .login-form {
        padding: 24px;
        
        .social-login {
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
  .login-container {
    background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
    
    .login-form {
      background: rgba(44, 62, 80, 0.95) !important;
      
      .title {
        color: #ecf0f1 !important;
      }
      
      .subtitle {
        color: #bdc3c7 !important;
      }
    }
  }
}
</style>