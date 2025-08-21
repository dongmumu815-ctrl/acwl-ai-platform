import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

// 导入布局组件
const Layout = () => import('@/layout/index.vue')

// 公共路由
export const constantRoutes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/auth/Login.vue'),
    meta: {
      title: '登录',
      hidden: true
    }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/auth/Register.vue'),
    meta: {
      title: '注册',
      hidden: true
    }
  },
  {
    path: '/404',
    name: '404',
    component: () => import('@/views/error/404.vue'),
    meta: {
      title: '页面不存在',
      hidden: true
    }
  },
  {
    path: '/403',
    name: '403',
    component: () => import('@/views/error/403.vue'),
    meta: {
      title: '权限不足',
      hidden: true
    }
  },
  {
    path: '/500',
    name: '500',
    component: () => import('@/views/error/500.vue'),
    meta: {
      title: '服务器错误',
      hidden: true
    }
  }
]

// 需要认证的路由
export const asyncRoutes: RouteRecordRaw[] = [
  {
    path: '/',
    component: Layout,
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/dashboard/index.vue'),
        meta: {
          title: '仪表盘',
          icon: 'Dashboard',
          requiresAuth: true
        }
      }
    ]
  },
  {
    path: '/models',
    component: Layout,
    redirect: '/models/list',
    meta: {
      title: '模型管理',
      icon: 'Box',
      requiresAuth: true
    },
    children: [
      {
        path: 'list',
        name: 'ModelList',
        component: () => import('@/views/models/index.vue'),
        meta: {
          title: '模型列表',
          icon: 'List',
          requiresAuth: true
        }
      },
      {
        path: 'upload',
        name: 'ModelUpload',
        component: () => import('@/views/models/index.vue'),
        meta: {
          title: '模型上传',
          icon: 'Upload',
          requiresAuth: true
        }
      },
      {
        path: 'detail/:id',
        name: 'ModelDetail',
        component: () => import('@/views/models/index.vue'),
        meta: {
          title: '模型详情',
          hidden: true,
          requiresAuth: true
        }
      }
    ]
  },
  {
    path: '/deployments',
    component: Layout,
    redirect: '/deployments/list',
    meta: {
      title: '部署管理',
      icon: 'Monitor',
      requiresAuth: true
    },
    children: [
      {
        path: 'list',
        name: 'DeploymentList',
        component: () => import('@/views/deployments/index.vue'),
        meta: {
          title: '部署列表',
          icon: 'List',
          requiresAuth: true
        }
      },
      {
        path: 'create',
        name: 'CreateDeployment',
        component: () => import('@/views/deployments/create.vue'),
        meta: {
          title: '创建部署',
          icon: 'Plus',
          requiresAuth: true,
          hideInMenu: true
        }
      },
      {
        path: 'detail/:id',
        name: 'DeploymentDetail',
        component: () => import('@/views/deployments/index.vue'),
        meta: {
          title: '部署详情',
          hidden: true,
          requiresAuth: true
        }
      },
      {
        path: 'logs/:id',
        name: 'DeploymentLogs',
        component: () => import('@/views/logs/index.vue'),
        meta: {
          title: '部署日志',
          hidden: true,
          requiresAuth: true
        }
      }
    ]
  },
  {
    path: '/datasets',
    component: Layout,
    redirect: '/datasets/list',
    meta: {
      title: '数据集管理',
      icon: 'Document',
      requiresAuth: true
    },
    children: [
      {
        path: 'list',
        name: 'DatasetList',
        component: () => import('@/views/datasets/index.vue'),
        meta: {
          title: '数据集列表',
          icon: 'List',
          requiresAuth: true
        }
      },
      {
        path: 'upload',
        name: 'DatasetUpload',
        component: () => import('@/views/datasets/index.vue'),
        meta: {
          title: '数据集上传',
          icon: 'Upload',
          requiresAuth: true
        }
      }
    ]
  },
  {
    path: '/datasources',
    component: Layout,
    redirect: '/datasources/list',
    meta: {
      title: '数据源管理',
      icon: 'Connection',
      requiresAuth: true
    },
    children: [
      {
        path: 'list',
        name: 'DatasourceList',
        component: () => import('@/views/datasources/index.vue'),
        meta: {
          title: '数据源列表',
          icon: 'List',
          requiresAuth: true
        }
      }
    ]
  },
  {
    path: '/projects',
    component: Layout,
    redirect: '/projects/list',
    meta: {
      title: '项目管理',
      icon: 'Folder',
      requiresAuth: true
    },
    children: [
      {
        path: 'list',
        name: 'ProjectList',
        component: () => import('@/views/projects/index.vue'),
        meta: {
          title: '项目列表',
          icon: 'List',
          requiresAuth: true
        }
      }
    ]
  },
  {
    path: '/fine-tuning',
    component: Layout,
    redirect: '/fine-tuning/jobs',
    meta: {
      title: '模型微调',
      icon: 'Setting',
      requiresAuth: true
    },
    children: [
      {
        path: 'jobs',
        name: 'FineTuningJobs',
        component: () => import('@/views/training/index.vue'),
        meta: {
          title: '微调任务',
          icon: 'List',
          requiresAuth: true
        }
      },
      {
        path: 'create',
        name: 'FineTuningCreate',
        component: () => import('@/views/training/index.vue'),
        meta: {
          title: '创建微调',
          icon: 'Plus',
          requiresAuth: true
        }
      }
    ]
  },
  {
    path: '/resources',
    component: Layout,
    redirect: '/resources/servers',
    meta: {
      title: '资源管理',
      icon: 'Cpu',
      requiresAuth: true,
      requiresAdmin: true
    },
    children: [
      {
        path: 'servers',
        name: 'ResourceServers',
        component: () => import('@/views/servers/index.vue'),
        meta: {
          title: '服务器资源池',
          icon: 'Monitor',
          requiresAuth: true,
          requiresAdmin: true
        }
      },
      {
        path: 'gpus',
        name: 'ResourceGpus',
        component: () => import('@/views/gpus/index.vue'),
        meta: {
          title: 'GPU资源池',
          icon: 'Cpu',
          requiresAuth: true,
          requiresAdmin: true
        }
      }
    ]
  },
  {
    path: '/system',
    component: Layout,
    redirect: '/system/users',
    meta: {
      title: '系统管理',
      icon: 'Tools',
      requiresAuth: true,
      requiresAdmin: true
    },
    children: [
      {
        path: 'users',
        name: 'SystemUsers',
        component: () => import('@/views/users/index.vue'),
        meta: {
          title: '用户管理',
          icon: 'User',
          requiresAuth: true,
          requiresAdmin: true
        }
      },
      {
        path: 'settings',
        name: 'SystemSettings',
        component: () => import('@/views/settings/index.vue'),
        meta: {
          title: '系统设置',
          icon: 'Setting',
          requiresAuth: true,
          requiresAdmin: true
        }
      },
      {
        path: 'logs',
        name: 'SystemLogs',
        component: () => import('@/views/logs/index.vue'),
        meta: {
          title: '系统日志',
          icon: 'Document',
          requiresAuth: true,
          requiresAdmin: true
        }
      }
    ]
  },
  {
    path: '/profile',
    component: Layout,
    redirect: '/profile/index',
    meta: {
      hidden: true
    },
    children: [
      {
        path: 'index',
        name: 'Profile',
        component: () => import('@/views/profile/index.vue'),
        meta: {
          title: '个人中心',
          requiresAuth: true
        }
      }
    ]
  }
]

// 创建路由实例
const router = createRouter({
  history: createWebHistory('/ui/'),
  routes: [...constantRoutes, ...asyncRoutes],
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    } else {
      return { top: 0 }
    }
  }
})

// 404路由必须放在最后
router.addRoute({
  path: '/:pathMatch(.*)*',
  redirect: '/404',
  meta: {
    hidden: true
  }
})

export default router