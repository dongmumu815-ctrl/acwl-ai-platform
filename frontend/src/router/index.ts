import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { PERMISSIONS, ROLES } from '@/utils/permission'

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
      requiresAuth: true,
      permission: PERMISSIONS.MODEL_READ
    },
    children: [
      {
        path: 'list',
        name: 'ModelList',
        component: () => import('@/views/models/index.vue'),
        meta: {
          title: '模型列表',
          icon: 'List',
          requiresAuth: true,
          permission: PERMISSIONS.MODEL_READ
        }
      },
      {
        path: 'upload',
        name: 'ModelUpload',
        component: () => import('@/views/models/index.vue'),
        meta: {
          title: '模型上传',
          icon: 'Upload',
          requiresAuth: true,
          permission: PERMISSIONS.MODEL_CREATE
        }
      },
      {
        path: 'service-configs',
        name: 'ModelServiceConfigs',
        component: () => import('@/views/model-service-configs/index.vue'),
        meta: {
          title: '服务配置',
          icon: 'Setting',
          requiresAuth: true,
          permissions: [PERMISSIONS.MODEL_READ, PERMISSIONS.MODEL_UPDATE]
        }
      },
      {
        path: 'detail/:id',
        name: 'ModelDetail',
        component: () => import('@/views/models/index.vue'),
        meta: {
          title: '模型详情',
          hidden: true,
          requiresAuth: true,
          permission: PERMISSIONS.MODEL_READ
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
      requiresAuth: true,
      permission: PERMISSIONS.MODEL_DEPLOY
    },
    children: [
      {
        path: 'list',
        name: 'DeploymentList',
        component: () => import('@/views/deployments/index.vue'),
        meta: {
          title: '部署列表',
          icon: 'List',
          requiresAuth: true,
          permission: PERMISSIONS.MODEL_DEPLOY
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
          hideInMenu: true,
          permission: PERMISSIONS.MODEL_DEPLOY
        }
      },
      {
        path: 'detail/:id',
        name: 'DeploymentDetail',
        component: () => import('@/views/deployments/index.vue'),
        meta: {
          title: '部署详情',
          hidden: true,
          requiresAuth: true,
          permission: PERMISSIONS.MODEL_DEPLOY
        }
      },
      {
        path: 'logs/:id',
        name: 'DeploymentLogs',
        component: () => import('@/views/logs/index.vue'),
        meta: {
          title: '部署日志',
          hidden: true,
          requiresAuth: true,
          permissions: [PERMISSIONS.MODEL_DEPLOY, PERMISSIONS.SYSTEM_MONITOR]
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
      requiresAuth: true,
      permission: PERMISSIONS.DATASET_READ
    },
    children: [
      {
        path: 'list',
        name: 'DatasetList',
        component: () => import('@/views/datasets/index.vue'),
        meta: {
          title: '数据集列表',
          icon: 'List',
          requiresAuth: true,
          permission: PERMISSIONS.DATASET_READ
        }
      },
      {
        path: 'upload',
        name: 'DatasetUpload',
        component: () => import('@/views/datasets/index.vue'),
        meta: {
          title: '数据集上传',
          icon: 'Upload',
          requiresAuth: true,
          permission: PERMISSIONS.DATASET_CREATE
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
      requiresAuth: true,
      permission: PERMISSIONS.PROJECT_READ
    },
    children: [
      {
        path: 'list',
        name: 'ProjectList',
        component: () => import('@/views/projects/index.vue'),
        meta: {
          title: '项目列表',
          icon: 'List',
          requiresAuth: true,
          permission: PERMISSIONS.PROJECT_READ
        }
      }
    ]
  },
  {
    path: '/agents',
    component: Layout,
    redirect: '/agents/list',
    meta: {
      title: '智能体管理',
      icon: 'Robot',
      requiresAuth: true
    },
    children: [
      {
        path: 'list',
        name: 'AgentList',
        component: () => import('@/views/agents/index.vue'),
        meta: {
          title: '智能体列表',
          icon: 'List',
          requiresAuth: true
        }
      },
      {
        path: 'create',
        name: 'AgentCreate',
        component: () => import('@/views/agents/index.vue'),
        meta: {
          title: '创建智能体',
          icon: 'Plus',
          requiresAuth: true,
          hideInMenu: true
        }
      },
      {
        path: 'detail/:id',
        name: 'AgentDetail',
        component: () => import('@/views/agents/index.vue'),
        meta: {
          title: '智能体详情',
          hidden: true,
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
      role: ROLES.ADMIN
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
          permission: PERMISSIONS.USER_READ
        }
      },
      {
        path: 'roles',
        name: 'SystemRoles',
        component: () => import('@/views/roles/index.vue'),
        meta: {
          title: '角色管理',
          icon: 'UserFilled',
          requiresAuth: true,
          permission: PERMISSIONS.ROLE_READ
        }
      },
      {
        path: 'permissions',
        name: 'SystemPermissions',
        component: () => import('@/views/permissions/index.vue'),
        meta: {
          title: '权限管理',
          icon: 'Key',
          requiresAuth: true,
          permission: PERMISSIONS.PERMISSION_READ
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
          permission: PERMISSIONS.SYSTEM_UPDATE
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
          permission: PERMISSIONS.SYSTEM_MONITOR
        }
      }
    ]
  },
  {
    path: '/monitoring',
    component: Layout,
    redirect: '/monitoring/index',
    meta: {
      title: '系统监控',
      icon: 'Monitor',
      requiresAuth: true,
      requiresAdmin: true
    },
    children: [
      {
        path: 'index',
        name: 'Monitoring',
        component: () => import('@/views/monitoring/index.vue'),
        meta: {
          title: '系统监控',
          icon: 'Monitor',
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
  },
  {
    path: '/instruction-sets',
    component: Layout,
    redirect: '/instruction-sets/index',
    meta: {
      title: '指令集管理',
      icon: 'Document',
      requiresAuth: true,
      permission: PERMISSIONS.INSTRUCTION_SET_READ
    },
    children: [
      {
        path: 'index',
        name: 'InstructionSets',
        component: () => import('@/views/instruction-sets/index.vue'),
        meta: {
          title: '指令集管理',
          icon: 'List',
          requiresAuth: true,
          permission: PERMISSIONS.INSTRUCTION_SET_READ
        }
      }
    ]
  },
  // 数据中心模块
  {
    path: '/data-center',
    component: Layout,
    redirect: '/data-center/dashboard',
    meta: {
      title: '数据中心',
      icon: 'DataBoard',
      requiresAuth: true
    },
    children: [
      {
        path: 'dashboard',
        name: 'DataCenterDashboard',
        component: () => import('@/views/data-center/dashboard/index.vue'),
        meta: {
          title: '数据概览',
          icon: 'Monitor',
          requiresAuth: true,
          keepAlive: true
        }
      },
      {
        path: 'statistics',
        name: 'DataCenterStatistics',
        component: () => import('@/views/data-center/statistics/index.vue'),
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
        name: 'DataResourceList',
        component: () => import('@/views/data-center/data-resources/ResourceList.vue'),
        meta: {
          title: '资源列表',
          icon: 'List',
          requiresAuth: true,
          keepAlive: true
        }
      },
      {
        path: 'create',
        name: 'DataResourceCreate',
        component: () => import('@/views/data-center/data-resources/ResourceCreate.vue'),
        meta: {
          title: '创建资源',
          icon: 'Plus',
          requiresAuth: true,
          hideInMenu: true
        }
      },
      {
        path: 'detail/:id',
        name: 'DataResourceDetail',
        component: () => import('@/views/data-center/data-resources/ResourceDetail.vue'),
        meta: {
          title: '资源详情',
          requiresAuth: true,
          hideInMenu: true,
          activeMenu: '/data-resources/list'
        }
      },
      {
        path: 'query/:id',
        name: 'DataResourceQuery',
        component: () => import('@/views/data-center/data-resources/ResourceQuery.vue'),
        meta: {
          title: '数据查询',
          requiresAuth: true,
          hideInMenu: true,
          activeMenu: '/data-resources/list'
        }
      },
      {
        path: 'categories',
        name: 'DataResourceCategories',
        component: () => import('@/views/data-center/data-resources/CategoryManage.vue'),
        meta: {
          title: '资源分类',
          icon: 'FolderAdd',
          requiresAuth: true
        }
      },
      {
        path: 'tags',
        name: 'DataResourceTags',
        component: () => import('@/views/data-center/data-resources/TagManage.vue'),
        meta: {
          title: '标签管理',
          icon: 'PriceTag',
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
        component: () => import('@/views/data-center/datasources/DatasourceList.vue'),
        meta: {
          title: '数据源列表',
          icon: 'List',
          requiresAuth: true
        }
      },
      {
        path: 'create',
        name: 'DatasourceCreate',
        component: () => import('@/views/data-center/datasources/DatasourceCreate.vue'),
        meta: {
          title: '创建数据源',
          icon: 'Plus',
          requiresAuth: true,
          hideInMenu: true
        }
      },
      {
        path: 'detail/:id',
        name: 'DatasourceDetail',
        component: () => import('@/views/data-center/datasources/DatasourceDetail.vue'),
        meta: {
          title: '数据源详情',
          requiresAuth: true,
          hideInMenu: true,
          activeMenu: '/datasources/list'
        }
      }
    ]
  },
  {
    path: '/instruction-sets/:id',
    component: Layout,
    meta: {
      hidden: true,
      requiresAuth: true,
      permission: PERMISSIONS.INSTRUCTION_SET_READ
    },
    children: [
      {
        path: '',
        name: 'InstructionSetDetail',
        component: () => import('@/views/instruction-sets/detail.vue'),
        meta: {
          title: '指令集详情',
          requiresAuth: true,
          permission: PERMISSIONS.INSTRUCTION_SET_READ
        }
      }
    ]
  },
  {
    path: '/instruction-sets/:id/test',
    component: Layout,
    meta: {
      hidden: true,
      requiresAuth: true,
      permission: PERMISSIONS.INSTRUCTION_SET_TEST
    },
    children: [
      {
        path: '',
        name: 'InstructionSetTest',
        component: () => import('@/views/instruction-sets/test.vue'),
        meta: {
          title: '指令集测试',
          requiresAuth: true,
          permission: PERMISSIONS.INSTRUCTION_SET_TEST
        }
      }
    ]
  }
  // 工作流模块 - 暂时注释掉，等待后续迁移
  /*
  {
    path: '/workflows',
    component: Layout,
    redirect: '/workflows/dashboard',
    meta: {
      title: '工作流管理',
      icon: 'Connection',
      requiresAuth: true
    },
    children: [
      {
        path: 'dashboard',
        name: 'WorkflowDashboard',
        component: () => import('@/views/workflows/dashboard/index.vue'),
        meta: {
          title: '工作流概览',
          icon: 'Monitor',
          requiresAuth: true,
          keepAlive: true
        }
      },
      {
        path: 'list',
        name: 'WorkflowList',
        component: () => import('@/views/workflows/list/index.vue'),
        meta: {
          title: '工作流管理',
          icon: 'List',
          requiresAuth: true
        }
      },
      {
        path: 'create',
        name: 'WorkflowCreate',
        component: () => import('@/views/workflows/create/index.vue'),
        meta: {
          title: '创建工作流',
          icon: 'Plus',
          requiresAuth: true
        }
      },
      {
        path: 'detail/:id',
        name: 'WorkflowDetail',
        component: () => import('@/views/workflows/detail/index.vue'),
        meta: {
          title: '工作流详情',
          icon: 'View',
          requiresAuth: true,
          hideInMenu: true
        }
      },
      {
        path: 'edit/:id',
        name: 'WorkflowEdit',
        component: () => import('@/views/workflows/edit/index.vue'),
        meta: {
          title: '编辑工作流',
          icon: 'Edit',
          requiresAuth: true,
          hideInMenu: true
        }
      },
      {
        path: 'executions/:id',
        name: 'WorkflowExecutions',
        component: () => import('@/views/workflows/executions/index.vue'),
        meta: {
          title: '执行历史',
          icon: 'Clock',
          requiresAuth: true,
          hideInMenu: true
        }
      },
      {
        path: 'execution-detail/:id/:executionId',
        name: 'WorkflowExecutionDetail',
        component: () => import('@/views/workflows/execution-detail/index.vue'),
        meta: {
          title: '执行详情',
          icon: 'View',
          requiresAuth: true,
          hideInMenu: true
        }
      },
      {
        path: 'tasks',
        name: 'TaskList',
        component: () => import('@/views/workflows/tasks/index.vue'),
        meta: {
          title: '任务管理',
          icon: 'Operation',
          requiresAuth: true
        }
      },
      {
        path: 'task-create',
        name: 'TaskCreate',
        component: () => import('@/views/workflows/task-create/index.vue'),
        meta: {
          title: '创建任务',
          icon: 'Plus',
          requiresAuth: true,
          hideInMenu: true
        }
      },
      {
        path: 'task-detail/:id',
        name: 'TaskDetail',
        component: () => import('@/views/workflows/task-detail/index.vue'),
        meta: {
          title: '任务详情',
          icon: 'View',
          requiresAuth: true,
          hideInMenu: true
        }
      },
      {
        path: 'task-edit/:id',
        name: 'TaskEdit',
        component: () => import('@/views/workflows/task-edit/index.vue'),
        meta: {
          title: '编辑任务',
          icon: 'Edit',
          requiresAuth: true,
          hideInMenu: true
        }
      },
      {
        path: 'projects',
        name: 'ProjectList',
        component: () => import('@/views/workflows/projects/index.vue'),
        meta: {
          title: '项目管理',
          icon: 'Folder',
          requiresAuth: true
        }
      },
      {
        path: 'project-create',
        name: 'ProjectCreate',
        component: () => import('@/views/workflows/project-create/index.vue'),
        meta: {
          title: '创建项目',
          icon: 'Plus',
          requiresAuth: true,
          hideInMenu: true
        }
      },
      {
        path: 'project-detail/:id',
        name: 'ProjectDetail',
        component: () => import('@/views/workflows/project-detail/index.vue'),
        meta: {
          title: '项目详情',
          icon: 'View',
          requiresAuth: true,
          hideInMenu: true
        }
      },
      {
        path: 'project-edit/:id',
        name: 'ProjectEdit',
        component: () => import('@/views/workflows/project-edit/index.vue'),
        meta: {
          title: '编辑项目',
          icon: 'Edit',
          requiresAuth: true,
          hideInMenu: true
        }
      },
      {
        path: 'monitoring',
        name: 'WorkflowMonitoring',
        component: () => import('@/views/workflows/monitoring/index.vue'),
        meta: {
          title: '实时监控',
          icon: 'Monitor',
          requiresAuth: true
        }
      },
      {
        path: 'settings',
        name: 'WorkflowSettings',
        component: () => import('@/views/workflows/settings/index.vue'),
        meta: {
          title: '工作流设置',
          icon: 'Setting',
          requiresAuth: true
        }
      }
    ]
  }
  */
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