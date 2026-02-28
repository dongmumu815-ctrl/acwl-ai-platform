import { createRouter, createWebHistory } from 'vue-router'
import Cookies from 'js-cookie'

/**
 * 路由配置
 */
const routes = [
  {
    path: '/',
    component: () => import('@/components/Layout.vue'),
    redirect: '/dashboard',
    meta: {
      requiresAuth: true
    },
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue'),
        meta: {
          title: '工作流概览',
          requiresAuth: true
        }
      },
       {
         path: 'workflows',
         name: 'WorkflowList',
         component: () => import('@/views/workflows/WorkflowList.vue'),
         meta: {
           title: '工作流管理',
           requiresAuth: true
         }
       },
       {
         path: 'workflows/create',
         name: 'WorkflowCreate',
         component: () => import('@/views/workflows/WorkflowCreate.vue'),
         meta: {
           title: '创建工作流',
           requiresAuth: true
         }
       },
       {
         path: 'workflows/instances',
         name: 'WorkflowInstanceList',
         component: () => import('@/views/workflows/WorkflowInstanceList.vue'),
         meta: {
           title: '工作流实例',
           requiresAuth: true
         }
       },
        {
          path: 'workflows/:id',
          name: 'WorkflowDetail',
          component: () => import('@/views/workflows/WorkflowDetail.vue'),
          meta: {
            title: '工作流详情',
            requiresAuth: true
          }
        },
        {
          path: 'workflows/:id/edit',
          name: 'WorkflowEdit',
          component: () => import('@/views/workflows/WorkflowEdit.vue'),
          meta: {
            title: '编辑工作流',
            requiresAuth: true
          }
        },
        {
          path: 'workflows/:id/executions',
          name: 'WorkflowExecutions',
          component: () => import('@/views/workflows/WorkflowExecutions.vue'),
          meta: {
            title: '执行历史',
            requiresAuth: true
          }
        },
        {
          path: 'workflows/:id/executions/:executionId',
          name: 'WorkflowExecutionDetail',
          component: () => import('@/views/workflows/WorkflowExecutionDetail.vue'),
          meta: {
            title: '执行详情',
            requiresAuth: true
          }
        },
        {
          path: 'tasks/instances',
          name: 'TaskInstanceList',
          component: () => import('@/views/tasks/TaskInstanceList.vue'),
          meta: {
            title: '任务实例',
            requiresAuth: true
          }
        },
        {
          path: 'tasks',
          name: 'TaskList',
          component: () => import('@/views/tasks/TaskList.vue'),
          meta: {
            title: '任务管理',
            requiresAuth: true
          }
        },
        {
          path: 'tasks/create',
          name: 'TaskCreate',
          component: () => import('@/views/tasks/TaskCreate.vue'),
          meta: {
            title: '创建任务',
            requiresAuth: true
          }
        },
        {
          path: 'tasks/:id',
          name: 'TaskDetail',
          component: () => import('@/views/tasks/TaskDetail.vue'),
          meta: {
            title: '任务详情',
            requiresAuth: true
          }
        },
        {
          path: 'tasks/:id/edit',
          name: 'TaskEdit',
          component: () => import('@/views/tasks/TaskEdit.vue'),
          meta: {
            title: '编辑任务',
            requiresAuth: true
          }
        },
        {
          path: 'projects',
          name: 'ProjectList',
          component: () => import('@/views/projects/ProjectList.vue'),
          meta: {
            title: '项目管理',
            requiresAuth: true
          }
        },
        {
          path: 'projects/create',
          name: 'ProjectCreate',
          component: () => import('@/views/projects/ProjectCreate.vue'),
          meta: {
            title: '创建项目',
            requiresAuth: true
          }
        },
        {
          path: 'projects/:id',
          name: 'ProjectDetail',
          component: () => import('@/views/projects/ProjectDetail.vue'),
          meta: {
            title: '项目详情',
            requiresAuth: true
          }
        },
        {
          path: 'projects/:id/edit',
          name: 'ProjectEdit',
          component: () => import('@/views/projects/ProjectEdit.vue'),
          meta: {
            title: '编辑项目',
            requiresAuth: true
          }
        },
        
        {
          path: 'resources',
          redirect: '/resources/executor-groups',
          meta: {
            title: '资源管理',
            requiresAuth: true
          },
          children: [
            {
              path: 'executor-groups',
              name: 'ExecutorGroupList',
              component: () => import('@/views/resources/ExecutorGroupList.vue'),
              meta: {
                title: '执行器分组',
                requiresAuth: true
              }
            },
            {
              path: 'environments',
              name: 'EnvironmentList',
              component: () => import('@/views/resources/EnvironmentList.vue'),
              meta: {
                title: '环境管理',
                requiresAuth: true
              }
            }
          ]
        },

        {
          path: 'monitoring',
          name: 'Monitoring',
          component: () => import('@/views/Monitoring.vue'),
          meta: {
            title: '实时监控',
            requiresAuth: true
          }
        },
        {
           path: 'settings',
           name: 'Settings',
           component: () => import('@/views/Settings.vue'),
           meta: {
             title: '系统设置',
             requiresAuth: true
           }
         },
         {
           path: 'code-editor-test',
           name: 'CodeEditorTest',
           component: () => import('@/views/CodeEditorTest.vue'),
           meta: {
             title: '代码编辑器测试',
             requiresAuth: true
           }
         },
         {
           path: 'advanced-code-editor-demo',
           name: 'AdvancedCodeEditorDemo',
           component: () => import('@/views/AdvancedCodeEditorDemo.vue'),
           meta: {
             title: '高级代码编辑器演示',
             requiresAuth: true
           }
         }
      ]
    },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: {
      title: '登录',
      requiresAuth: false
    }
  },
  {
    path: '/admin/login',
    name: 'AdminLogin',
    component: () => import('@/views/Login.vue'),
    meta: {
      title: '管理员登录',
      requiresAuth: false
    }
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFound.vue'),
    meta: {
      title: '页面不存在',
      requiresAuth: false
    }
  }
]

/**
 * 创建路由实例
 */
const router = createRouter({
  history: createWebHistory('/taskflow/'),
  routes,
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
 */
router.beforeEach((to, from, next) => {
  // 设置页面标题
  if (to.meta.title) {
    document.title = `${to.meta.title} - ACWL AI工作流管理`
  }
  
  // 检查认证状态
  if (to.meta.requiresAuth) {
    const token = Cookies.get('token')
    if (!token) {
      // 未登录，跳转到登录页面
      next({ name: 'Login', query: { redirect: to.fullPath } })
      return
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