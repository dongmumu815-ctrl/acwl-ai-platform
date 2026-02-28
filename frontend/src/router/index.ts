import { createRouter, createWebHistory, RouterView } from 'vue-router'
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
  },
  // 帮助中心（公共路由，默认展示在主布局内）
  {
    path: '/help',
    component: Layout,
    children: [
      {
        path: '',
        name: 'HelpCenter',
        component: () => import('@/views/help/index.vue'),
        meta: {
          title: '帮助中心',
          hidden: true
        }
      }
    ]
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
      permission: PERMISSIONS.MODEL_READ,
      noPermissionBehavior: 'hide'
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
          permission: PERMISSIONS.MODEL_READ,
          noPermissionBehavior: 'hide'
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
          permissions: [PERMISSIONS.MODEL_READ, PERMISSIONS.MODEL_UPDATE],
          noPermissionBehavior: 'hide'
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
          permission: PERMISSIONS.MODEL_READ,
          noPermissionBehavior: 'hide'
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
      permission: PERMISSIONS.MODEL_DEPLOY,
      noPermissionBehavior: 'hide'
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
          permission: PERMISSIONS.MODEL_DEPLOY,
          noPermissionBehavior: 'hide'
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
          permission: PERMISSIONS.MODEL_DEPLOY,
          noPermissionBehavior: 'hide'
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
          permission: PERMISSIONS.MODEL_DEPLOY,
          noPermissionBehavior: 'hide'
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
          permissions: [PERMISSIONS.MODEL_DEPLOY, PERMISSIONS.SYSTEM_MONITOR],
          noPermissionBehavior: 'hide'
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
      permission: PERMISSIONS.DATASET_READ,
      noPermissionBehavior: 'hide'
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
          permission: PERMISSIONS.DATASET_READ,
          noPermissionBehavior: 'hide'
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
          permission: PERMISSIONS.DATASET_CREATE,
          noPermissionBehavior: 'hide'
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
      requiresAuth: true,
      permission: PERMISSIONS.DATASOURCE_READ,
      noPermissionBehavior: 'hide'
    },
    children: [
      {
        path: 'list',
        name: 'DatasourceList',
        component: () => import('@/views/datasources/index.vue'),
        meta: {
          title: '数据源列表',
          icon: 'List',
          requiresAuth: true,
          permission: PERMISSIONS.DATASOURCE_READ,
          noPermissionBehavior: 'hide'
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
      permission: PERMISSIONS.PROJECT_READ,
      noPermissionBehavior: 'hide'
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
          permission: PERMISSIONS.PROJECT_READ,
          noPermissionBehavior: 'hide'
        }
      }
    ]
  },
  // Governance routes removed
  {
    path: '/agents',
    component: Layout,
    redirect: '/agents/list',
    meta: {
      title: '智能体管理',
      icon: 'Robot',
      requiresAuth: true,
      permission: PERMISSIONS.AGENT_READ,
      noPermissionBehavior: 'hide'
    },
    children: [
      {
        path: 'list',
        name: 'AgentList',
        component: () => import('@/views/agents/index.vue'),
        meta: {
          title: '智能体列表',
          icon: 'List',
          requiresAuth: true,
          permission: PERMISSIONS.AGENT_READ,
          noPermissionBehavior: 'hide'
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
          hideInMenu: true,
          permission: PERMISSIONS.AGENT_CREATE,
          noPermissionBehavior: 'hide'
        }
      },
      {
        path: 'detail/:id',
        name: 'AgentDetail',
        component: () => import('@/views/agents/index.vue'),
        meta: {
          title: '智能体详情',
          hidden: true,
          requiresAuth: true,
          permission: PERMISSIONS.AGENT_READ,
          noPermissionBehavior: 'hide'
        }
      },
      {
        path: 'skills',
        name: 'AgentSkills',
        component: () => import('@/views/agent-skills/index.vue'),
        meta: {
          title: '技能管理',
          icon: 'Tools',
          requiresAuth: true,
          permission: PERMISSIONS.AGENT_READ,
          noPermissionBehavior: 'hide'
        }
      },
      {
        path: 'skills/edit/:id?',
        name: 'AgentSkillEdit',
        component: () => import('@/views/agent-skills/edit.vue'),
        meta: {
          title: '编辑技能',
          hidden: true,
          requiresAuth: true,
          permission: PERMISSIONS.AGENT_UPDATE,
          noPermissionBehavior: 'hide'
        }
      },
      {
        path: 'skills/test-runner',
        name: 'AgentSkillTestRunner',
        component: () => import('@/views/agent-skills/test-runner.vue'),
        meta: {
          title: '技能测试',
          hidden: true,
          requiresAuth: true,
          permission: PERMISSIONS.AGENT_READ,
          noPermissionBehavior: 'hide'
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
      requiresAuth: true,
      permission: PERMISSIONS.TRAINING_READ,
      noPermissionBehavior: 'hide'
    },
    children: [
      {
        path: 'jobs',
        name: 'FineTuningJobs',
        component: () => import('@/views/training/index.vue'),
        meta: {
          title: '微调任务',
          icon: 'List',
          requiresAuth: true,
          permission: PERMISSIONS.TRAINING_READ,
          noPermissionBehavior: 'hide'
        }
      },
      {
        path: 'create',
        name: 'FineTuningCreate',
        component: () => import('@/views/training/index.vue'),
        meta: {
          title: '创建微调',
          icon: 'Plus',
          requiresAuth: true,
          permission: PERMISSIONS.TRAINING_CREATE,
          noPermissionBehavior: 'hide'
        }
      }
    ]
  },
  {
    path: '/applications',
    component: Layout,
    redirect: '/applications/market',
    meta: {
      title: '应用管理',
      icon: 'App',
      requiresAuth: true,
      permission: PERMISSIONS.SYSTEM_MONITOR, // TODO: Add specific permission
      noPermissionBehavior: 'hide'
    },
    children: [
      {
        path: 'market',
        name: 'AppMarket',
        component: () => import('@/views/applications/market/index.vue'),
        meta: {
          title: '应用市场',
          icon: 'Shop',
          requiresAuth: true,
          permission: PERMISSIONS.SYSTEM_MONITOR,
          noPermissionBehavior: 'hide'
        }
      },
      {
        path: 'instances',
        name: 'AppInstances',
        component: () => import('@/views/applications/instances/index.vue'),
        meta: {
          title: '已安装应用',
          icon: 'Box',
          requiresAuth: true,
          permission: PERMISSIONS.SYSTEM_MONITOR,
          noPermissionBehavior: 'hide'
        }
      },
      {
        path: 'harbor',
        name: 'HarborConfig',
        component: () => import('@/views/applications/harbor/index.vue'),
        meta: {
          title: 'Harbor配置',
          icon: 'Setting',
          requiresAuth: true,
          permission: PERMISSIONS.SYSTEM_MONITOR,
          noPermissionBehavior: 'hide'
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
      permission: PERMISSIONS.SYSTEM_MONITOR,
      noPermissionBehavior: 'hide'
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
          permission: PERMISSIONS.SYSTEM_MONITOR,
          noPermissionBehavior: 'hide'
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
          permission: PERMISSIONS.SYSTEM_MONITOR,
          noPermissionBehavior: 'hide'
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
      role: ROLES.ADMIN,
      noPermissionBehavior: 'hide'
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
          permission: PERMISSIONS.USER_READ,
          noPermissionBehavior: 'hide'
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
          permission: PERMISSIONS.ROLE_READ,
          noPermissionBehavior: 'hide'
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
          permission: PERMISSIONS.PERMISSION_READ,
          noPermissionBehavior: 'hide'
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
          permission: PERMISSIONS.SYSTEM_UPDATE,
          noPermissionBehavior: 'hide'
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
          permission: PERMISSIONS.SYSTEM_MONITOR,
          noPermissionBehavior: 'hide'
        }
      },
      {
        path: 'environments',
        name: 'SystemEnvironments',
        component: () => import('@/views/environments/index.vue'),
        meta: {
          title: '环境管理',
          icon: 'Setting',
          requiresAuth: true,
          permission: PERMISSIONS.SYSTEM_UPDATE,
          noPermissionBehavior: 'hide'
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
      requiresAdmin: true,
      permission: PERMISSIONS.SYSTEM_MONITOR,
      noPermissionBehavior: 'hide'
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
          requiresAdmin: true,
          permission: PERMISSIONS.SYSTEM_MONITOR,
          noPermissionBehavior: 'hide'
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
      permission: PERMISSIONS.INSTRUCTION_SET_READ,
      noPermissionBehavior: 'hide'
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
          permission: PERMISSIONS.INSTRUCTION_SET_READ,
          noPermissionBehavior: 'hide'
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
      permission: PERMISSIONS.INSTRUCTION_SET_READ,
      noPermissionBehavior: 'hide'
    },
    children: [
      {
        path: '',
        name: 'InstructionSetDetail',
        component: () => import('@/views/instruction-sets/detail.vue'),
        meta: {
          title: '指令集详情',
          requiresAuth: true,
          permission: PERMISSIONS.INSTRUCTION_SET_READ,
          noPermissionBehavior: 'hide'
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
      permission: PERMISSIONS.INSTRUCTION_SET_TEST,
      noPermissionBehavior: 'hide'
    },
    children: [
      {
        path: '',
        name: 'InstructionSetTest',
        component: () => import('@/views/instruction-sets/test.vue'),
        meta: {
          title: '指令集测试',
          requiresAuth: true,
          permission: PERMISSIONS.INSTRUCTION_SET_TEST,
          noPermissionBehavior: 'hide'
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
  history: createWebHistory('/ai/'),
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