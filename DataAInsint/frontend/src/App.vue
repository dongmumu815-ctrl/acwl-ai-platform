<template>
  <div id="app">
    <el-container class="app-container">
      <!-- 头部导航 -->
      <el-header class="app-header" v-if="showHeader">
        <div class="header-content">
          <div class="logo">
            <el-icon class="logo-icon"><DataAnalysis /></el-icon>
            <span class="logo-text">DataAInsight</span>
          </div>
          <div class="menu-center">
            <div class="custom-menu">
              <div 
                class="menu-item" 
                :class="{ active: activeIndex === '/datasource' }"
                @click="handleMenuSelect('/datasource')"
              >
                数据源配置
              </div>
              <div 
                class="menu-item" 
                :class="{ active: activeIndex === '/explorer' }"
                @click="handleMenuSelect('/explorer')"
              >
                数据探查
              </div>
            </div>
          </div>
          <div class="header-right">
            <span class="logout-btn" @click="handleLogout" title="退出登录">
              <el-icon><SwitchButton /></el-icon>
            </span>
          </div>
        </div>
      </el-header>
      
      <!-- 主内容区域 -->
      <el-main class="app-main">
        <router-view />
      </el-main>
      
      <!-- 底部 -->
      <el-footer class="app-footer" v-if="showHeader">
        <div class="footer-content">
          <span>© 2024 奥诚未来 版权所有</span>
        </div>
      </el-footer>
    </el-container>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { DataAnalysis, User, SwitchButton, ArrowDown } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { logout, isAuthenticated } from '@/api/auth'

const route = useRoute()
const router = useRouter()

const activeIndex = computed(() => {
  return route.path
})

// 是否显示头部和底部
const showHeader = computed(() => {
  return route.name !== 'Login'
})

const handleMenuSelect = (index) => {
  router.push(index)
}

// 处理退出登录
const handleLogout = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要退出登录吗？',
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    logout()
    ElMessage.success('已退出登录')
    router.push('/login')
  } catch {
    // 用户取消
  }
}

// 监听路由变化，设置页面标题
watch(
  () => route.path,
  (newPath) => {
    if (newPath === '/datasource') {
      document.title = '数据源配置 - DataAInsight'
    } else if (newPath === '/explorer') {
      document.title = '数据探查 - DataAInsight'
    } else {
      document.title = 'DataAInsight - 数据探查工具'
    }
  },
  { immediate: true }
)
</script>

<style scoped>
.app-container {
  height: 100vh;
}

.app-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-bottom: none;
  padding: 0;
  height: 50px;
  line-height: 50px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  position: relative;
  overflow: hidden;
}

.app-header::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(45deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%);
  pointer-events: none;
}

.header-content {
  display: flex;
  align-items: center;
  height: 100%;
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 30px;
  position: relative;
  z-index: 1;
}

.logo {
  display: flex;
  align-items: center;
  font-size: 18px;
  font-weight: 700;
  color: #ffffff;
  flex: 0 0 auto;
  transition: all 0.3s ease;
  cursor: pointer;
}

.logo:hover {
  transform: scale(1.05);
  text-shadow: 0 0 20px rgba(255,255,255,0.5);
}

.logo-icon {
  font-size: 22px;
  margin-right: 8px;
  filter: drop-shadow(0 2px 4px rgba(0,0,0,0.2));
  transition: all 0.3s ease;
}

.logo:hover .logo-icon {
  transform: rotate(360deg);
}

.logo-text {
  font-size: 18px;
  letter-spacing: 1px;
  text-shadow: 0 2px 4px rgba(0,0,0,0.2);
}

.menu-center {
  flex: 1;
  display: flex;
  justify-content: flex-end;
  margin-right: 40px;
}

.custom-menu {
  display: flex;
  align-items: center;
  gap: 20px;
}

.menu-item {
  color: rgba(255,255,255,0.9);
  font-weight: 500;
  font-size: 14px;
  padding: 8px 16px;
  border-bottom: 2px solid transparent;
  border-radius: 6px 6px 0 0;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
  white-space: nowrap;
  user-select: none;
}

.menu-item::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
  transition: left 0.5s ease;
}

.menu-item:hover::before {
  left: 100%;
}

.menu-item:hover {
  color: #ffffff;
  background-color: rgba(255,255,255,0.1);
  border-bottom-color: #ffffff;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

.menu-item.active {
  color: #ffffff;
  background-color: rgba(255,255,255,0.15);
  border-bottom-color: #ffffff;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.header-right {
  flex: 0 0 auto;
}

.logout-btn {
  color: rgba(255,255,255,0.9);
  font-size: 16px;
  cursor: pointer;
  display: flex;
  align-items: center;
  padding: 6px;
  border-radius: 4px;
  transition: all 0.3s ease;
}

.logout-btn:hover {
  background: rgba(255,255,255,0.1);
  color: white;
  transform: scale(1.1);
}

.app-main {
  padding: 0;
  background-color: #f5f7fa;
  flex: 1;
}

.app-footer {
  background-color: #fff;
  border-top: 1px solid #e4e7ed;
  height: 30px;
  line-height: 30px;
  padding: 0;
}

.footer-content {
  text-align: center;
  color: #909399;
  font-size: 12px;
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
}
</style>