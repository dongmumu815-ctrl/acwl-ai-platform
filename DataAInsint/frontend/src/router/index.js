import { createRouter, createWebHistory } from 'vue-router'
import DataSource from '@/views/DataSource.vue'
import Explorer from '@/views/Explorer.vue'
import Login from '@/views/Login.vue'
import { isAuthenticated } from '@/api/auth'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: {
      title: '登录',
      requiresAuth: false
    }
  },
  {
    path: '/',
    redirect: '/datasource'
  },
  {
    path: '/datasource',
    name: 'DataSource',
    component: DataSource,
    meta: {
      title: '数据源配置',
      requiresAuth: true
    }
  },
  {
    path: '/explorer',
    name: 'Explorer',
    component: Explorer,
    meta: {
      title: '数据探查',
      requiresAuth: true
    }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const authenticated = isAuthenticated()
  
  // 如果路由需要认证但用户未登录，跳转到登录页
  if (to.meta.requiresAuth && !authenticated) {
    next('/login')
    return
  }
  
  // 如果用户已登录但访问登录页，跳转到首页
  if (to.name === 'Login' && authenticated) {
    next('/')
    return
  }
  
  next()
})

export default router