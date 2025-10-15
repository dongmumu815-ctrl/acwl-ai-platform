import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

// 导入页面组件
const Login = () => import('@/views/Login.vue')
const Layout = () => import('@/layout/index.vue')
const Dashboard = () => import('@/views/Dashboard.vue')
const CustomerList = () => import('@/views/customer/List.vue')
const BatchList = () => import('@/views/batch/List.vue')
const BatchDetail = () => import('@/views/batch/Detail.vue')
const ApiList = () => import('@/views/api/List.vue')
const ApiFields = () => import('@/views/api/Fields.vue')
const SystemConfig = () => import('@/views/config/List.vue')
const AdminList = () => import('@/views/admin/List.vue')

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    component: Layout,
    redirect: '/dashboard',
    meta: { requiresAuth: true },
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: Dashboard,
        meta: { title: '仪表板', icon: 'DataBoard' }
      },
      {
        path: 'customers',
        name: 'CustomerList',
        component: CustomerList,
        meta: { title: '客户管理', icon: 'User' }
      },
      {
        path: 'batches',
        name: 'BatchList',
        component: BatchList,
        meta: { title: '批次管理', icon: 'Box' }
      },
      {
        path: 'batches/:id',
        name: 'BatchDetail',
        component: BatchDetail,
        meta: { title: '批次详情', hidden: true }
      },
      {
        path: 'apis',
        name: 'ApiList',
        component: ApiList,
        meta: { title: 'API管理', icon: 'Connection' }
      },
      {
        path: 'apis/:id/fields',
        name: 'ApiFields',
        component: ApiFields,
        meta: { title: 'API字段管理', hidden: true }
      },
      {
        path: 'admins',
        name: 'AdminList',
        component: AdminList,
        meta: { title: '管理员', icon: 'UserFilled' }
      },
      {
        path: 'system',
        name: 'SystemConfig',
        component: SystemConfig,
        meta: { title: '系统配置', icon: 'Setting' }
      }
    ]
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/dashboard'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  
  if (to.meta.requiresAuth !== false && !authStore.isAuthenticated) {
    next('/login')
  } else if (to.path === '/login' && authStore.isAuthenticated) {
    next('/dashboard')
  } else {
    next()
  }
})

export default router