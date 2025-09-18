import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'

// 导入布局组件
import Layout from '@/components/layout/Layout.vue'

// 导入页面组件
import Login from '@/views/auth/Login.vue'
// Dashboard组件改为动态导入

/**
 * 公共路由
 * 不需要权限验证的路由
 */
const publicRoutes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: {
      title: '登录',
      requiresAuth: false,
      hideInMenu: true
    }
  },
  {
    path: '/404',
    name: 'NotFound',
    component: () => import('@/views/error/404.vue'),
    meta: {
      title: '页面不存在',
      requiresAuth: false,
      hideInMenu: true
    }
  }
]

/**
 * 需要认证的路由
 * 按照新的菜单结构组织：数据中心概览、数据资源管理、权限与用户、系统管理
 */
const authRoutes: RouteRecordRaw[] = [
  {
    path: '/',
    component: Layout,
    redirect: '/dashboard',
    meta: {
      title: '数据中心概览',
      icon: 'DataBoard',
      requiresAuth: true
    },
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/dashboard/Dashboard.vue'),
        meta: {
          title: '仪表盘1',
          icon: 'Monitor',
          requiresAuth: true,
          keepAlive: true
        }
      },
      {
        path: 'statistics',
        name: 'Statistics',
        component: () => import('@/views/statistics/Statistics.vue'),
        meta: {
          title: '数据统计',
          icon: 'TrendCharts',
          requiresAuth: true
        }
      }
    ]
  },
  {
    path: '/data-resources',
    component: Layout,
    redirect: '/data-resources/list',
    meta: {
      title: '数据资源管理',
      icon: 'FolderOpened',
      requiresAuth: true
    },
    children: [
      {
        path: 'list',
        name: 'ResourceList',
        component: () => import('@/views/dataResource/ResourceList.vue'),
        meta: {
          title: '资源列表',
          icon: 'List',
          requiresAuth: true,
          keepAlive: true
        }
      },
      {
        path: 'create',
        name: 'ResourceCreate',
        component: () => import('@/views/dataResource/ResourceCreate.vue'),
        meta: {
          title: '创建资源',
          icon: 'Plus',
          requiresAuth: true,
          hideInMenu: true
        }
      },
      {
        path: 'detail/:id',
        name: 'ResourceDetail',
        component: () => import('@/views/dataResource/ResourceDetail.vue'),
        meta: {
          title: '资源详情',
          requiresAuth: true,
          hideInMenu: true,
          activeMenu: '/data-resources/list'
        }
      },
      {
        path: 'query/:id',
        name: 'ResourceQuery',
        component: () => import('@/views/dataResource/ResourceQuery.vue'),
        meta: {
          title: '数据查询',
          requiresAuth: true,
          hideInMenu: true,
          activeMenu: '/data-resources/list'
        }
      },
      {
        path: 'categories',
        name: 'CategoryManage',
        component: () => import('@/views/dataResource/CategoryManage.vue'),
        meta: {
          title: '资源分类',
          icon: 'FolderAdd',
          requiresAuth: true
        }
      },
      {
        path: 'tags',
        name: 'TagManage',
        component: () => import('@/views/dataResource/TagManage.vue'),
        meta: {
          title: '标签管理',
          icon: 'PriceTag',
          requiresAuth: true
        }
      },
      {
        path: 'packages',
        name: 'ResourcePackageList',
        component: () => import('@/views/resourcePackage/ResourcePackageList.vue'),
        meta: {
          title: '资源包管理',
          icon: 'Box',
          requiresAuth: true
        }
      }
    ]
  },
  {
    path: '/users',
    component: Layout,
    redirect: '/users/list',
    meta: {
      title: '权限与用户',
      icon: 'User',
      requiresAuth: true
    },
    children: [
      {
        path: 'list',
        name: 'UserList',
        component: () => import('@/views/user/UserList.vue'),
        meta: {
          title: '用户管理',
          icon: 'UserFilled',
          requiresAuth: true
        }
      },
      {
        path: 'create',
        name: 'UserCreate',
        component: () => import('@/views/user/UserForm.vue'),
        meta: {
          title: '新建用户',
          requiresAuth: true,
          hideInMenu: true
        }
      },
      {
        path: ':id/edit',
        name: 'UserEdit',
        component: () => import('@/views/user/UserForm.vue'),
        meta: {
          title: '编辑用户',
          requiresAuth: true,
          hideInMenu: true
        }
      },
      {
        path: 'roles',
        name: 'RoleManagement',
        component: () => import('@/views/user/RoleManagement.vue'),
        meta: {
          title: '角色管理',
          icon: 'Avatar',
          requiresAuth: true
        }
      },
      {
        path: 'permissions',
        name: 'UserPermissionManagement',
        component: () => import('@/views/user/PermissionManagement.vue'),
        meta: {
          title: '权限配置',
          icon: 'Key',
          requiresAuth: true
        }
      },
      {
        path: 'resource-permissions',
        name: 'ResourcePermissionManage',
        component: () => import('@/views/dataResource/PermissionManage.vue'),
        meta: {
          title: '访问控制',
          icon: 'Lock',
          requiresAuth: true
        }
      }
    ]
  },
  {
    path: '/system',
    component: Layout,
    redirect: '/system/settings',
    meta: {
      title: '系统管理',
      icon: 'Setting',
      requiresAuth: true
    },
    children: [
      {
        path: 'settings',
        name: 'SystemSettings',
        component: () => import('@/views/settings/Settings.vue'),
        meta: {
          title: '系统设置',
          icon: 'Tools',
          requiresAuth: true
        }
      },
      {
        path: 'monitor',
        name: 'SystemMonitor',
        component: () => import('@/views/system/Monitor.vue'),
        meta: {
          title: '系统监控',
          icon: 'Monitor',
          requiresAuth: true
        }
      },
      {
        path: 'logs',
        name: 'SystemLogs',
        component: () => import('@/views/system/Logs.vue'),
        meta: {
          title: '日志管理',
          icon: 'Document',
          requiresAuth: true
        }
      },
      {
        path: 'backup',
        name: 'SystemBackup',
        component: () => import('@/views/system/Backup.vue'),
        meta: {
          title: '备份管理',
          icon: 'FolderAdd',
          requiresAuth: true
        }
      },
      {
        path: 'update',
        name: 'SystemUpdate',
        component: () => import('@/views/system/Update.vue'),
        meta: {
          title: '系统更新',
          icon: 'Upload',
          requiresAuth: true
        }
      },
      {
        path: 'datasources',
        name: 'DataSourceList',
        component: () => import('@/views/datasource/DataSourceList.vue'),
        meta: {
          title: '数据源管理',
          icon: 'Connection',
          requiresAuth: true
        }
      },
      {
        path: 'auth-error-test',
        name: 'AuthErrorTest',
        component: () => import('@/views/test/AuthErrorTest.vue'),
        meta: {
          title: '认证错误测试',
          icon: 'Warning',
          requiresAuth: true
        }
      }
    ]
  },
  {
    path: '/user',
    component: Layout,
    redirect: '/user/profile',
    meta: {
      title: '用户中心',
      icon: 'User',
      requiresAuth: true,
      hideInMenu: true
    },
    children: [
      {
        path: 'profile',
        name: 'Profile',
        component: () => import('@/views/user/Profile.vue'),
        meta: {
          title: '个人资料',
          requiresAuth: true,
          hideInMenu: true
        }
      }
    ]
  }
]

/**
 * 创建路由实例
 */
const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    ...publicRoutes,
    ...authRoutes,
    {
      path: '/:pathMatch(.*)*',
      redirect: '/404'
    }
  ],
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    } else {
      return { top: 0 }
    }
  }
})

/**
 * 路由守卫
 * 检查用户认证状态和权限
 */
router.beforeEach(async (to, from, next) => {
  const userStore = useUserStore()
  
  // 如果访问登录页面且已登录，跳转到仪表盘
  if (to.path === '/login' && userStore.isLoggedIn) {
    next('/dashboard')
    return
  }
  
  // 检查是否需要认证
  if (to.meta.requiresAuth) {
    if (!userStore.isLoggedIn) {
      ElMessage.warning('请先登录')
      next('/login')
      return
    }
    
    // 检查角色权限
    if (to.meta.roles) {
      const roles = to.meta.roles as string[]
      if (!roles.some(role => userStore.hasRole(role))) {
        ElMessage.error('没有访问权限')
        next('/404')
        return
      }
    }
  }
  
  next()
})

/**
 * 路由错误处理
 */
router.onError((error) => {
  console.error('路由错误:', error)
})

export default router

/**
 * 导出认证路由供菜单组件使用
 */
export { authRoutes }

/**
 * 获取扁平化路由列表
 * @param routes 路由配置
 * @returns 扁平化的路由列表
 */
export function getFlatRoutes(routes: RouteRecordRaw[]): RouteRecordRaw[] {
  const flatRoutes: RouteRecordRaw[] = []
  
  function flatten(routes: RouteRecordRaw[], parentPath = '') {
    routes.forEach(route => {
      const fullPath = parentPath + route.path
      flatRoutes.push({ ...route, path: fullPath })
      
      if (route.children) {
        flatten(route.children, fullPath + '/')
      }
    })
  }
  
  flatten(routes)
  return flatRoutes
}

/**
 * 根据路由名称获取面包屑导航
 * @param routeName 路由名称
 * @returns 面包屑数组
 */
export function getBreadcrumbs(routeName: string): Array<{ title: string; path?: string }> {
  const flatRoutes = getFlatRoutes(authRoutes)
  const route = flatRoutes.find(r => r.name === routeName)
  
  if (!route || !route.meta?.breadcrumb) {
    return []
  }
  
  return route.meta.breadcrumb as Array<{ title: string; path?: string }>
}