import { createRouter, createWebHistory, RouterView } from 'vue-router'
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
      requiresAuth: true,
      // 分组访问权限：概览访问
      permission: 'data:overview:view',
      strictPermission: true
    },
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/dashboard/Dashboard.vue'),
        meta: {
          title: '仪表盘',
          icon: 'Monitor',
          requiresAuth: true,
          // 页面访问权限：仪表盘查看
          permission: 'data:dashboard:view',
          strictPermission: true,
          keepAlive: true
        }
      },
      // {
      //   path: 'statistics',
      //   name: 'Statistics',
      //   component: () => import('@/views/statistics/Statistics.vue'),
      //   meta: {
      //     title: '数据统计',
      //     icon: 'TrendCharts',
      //     requiresAuth: true
      //   }
      // }
    ]
  },
  {
    path: '/data-resources',
    component: Layout,
    redirect: '/data-resources/list',
    meta: {
      title: '数据资源管理',
      icon: 'FolderOpened',
      requiresAuth: true,
      // 分组访问权限：数据资源查看
      permission: 'data:resource:view',
      strictPermission: true
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
          // 访问资源列表需要查看权限
          permission: 'data:resource:view',
          strictPermission: true,
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
          // 创建资源需要创建权限
          permission: 'data:resource:create',
          strictPermission: true,
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
          // 查看资源详情需要查看权限
          permission: 'data:resource:view',
          strictPermission: true,
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
          // 数据查询页需要查询权限
          permission: 'data:resource:query',
          strictPermission: true,
          hideInMenu: true,
          activeMenu: '/data-resources/list'
        }
      },
      // {
      //   path: 'categories',
      //   name: 'CategoryManage',
      //   component: () => import('@/views/dataResource/CategoryManage.vue'),
      //   meta: {
      //     title: '资源分类1',
      //     icon: 'FolderAdd',
      //     requiresAuth: true
      //   }
      // },
      // {
      //   path: 'tags',
      //   name: 'TagManage',
      //   component: () => import('@/views/dataResource/TagManage.vue'),
      //   meta: {
      //     title: '标签管理',
      //     icon: 'PriceTag',
      //     requiresAuth: true
      //   }
      // },
      {
        path: 'packages',
        name: 'ResourcePackageList',
        component: () => import('@/views/resourcePackage/ResourcePackageList.vue'),
        meta: {
          title: '资源包管理',
          icon: 'Box',
          requiresAuth: true,
          // 资源包列表页至少需要查询权限
          permission: 'data:resource:query'
        }
      },
      {
        path: 'packages/:id/query',
        name: 'ResourcePackageQuery',
        component: () => import('@/views/resourcePackage/ResourcePackageQueryPage.vue'),
        meta: {
          title: '资源包查询',
          requiresAuth: true,
          // 资源包查询页需要查询权限
          permission: 'data:resource:query',
          hideInMenu: true,
          activeMenu: '/data-resources/packages'
        }
      }
    ]
  },
  // {
  //   path: '/datasources',
  //   component: Layout,
  //   redirect: '/datasources/list',
  //   meta: {
  //     title: '数据源管理',
  //     icon: 'Connection',
  //     requiresAuth: true,
  //     // 分组访问权限：数据源查看
  //     permission: 'data:datasource:view',
  //     strictPermission: true
  //   },
  //   children: [
  //     {
  //       path: 'list',
  //       name: 'DatasourceList',
  //       component: () => import('@/views/datasources/index.vue'),
  //       meta: {
  //         title: '数据源列表',
  //         icon: 'List',
  //         requiresAuth: true,
  //         // 查看数据源列表需要查看权限
  //         permission: 'data:datasource:view',
  //         strictPermission: true
  //       }
  //     }
  //   ]
  // },
  // {
  //   path: '/users',
  //   component: Layout,
  //   redirect: '/users/list',
  //   meta: {
  //     title: '权限与用户',
  //     icon: 'User',
  //     requiresAuth: true
  //   },
  //   children: [
  //     {
  //       path: 'list',
  //       name: 'UserList',
  //       component: () => import('@/views/user/UserList.vue'),
  //       meta: {
  //         title: '用户管理',
  //         icon: 'UserFilled',
  //         requiresAuth: true
  //       }
  //     },
  //     {
  //       path: 'create',
  //       name: 'UserCreate',
  //       component: () => import('@/views/user/UserForm.vue'),
  //       meta: {
  //         title: '新建用户',
  //         requiresAuth: true,
  //         hideInMenu: true
  //       }
  //     },
  //     {
  //       path: ':id/edit',
  //       name: 'UserEdit',
  //       component: () => import('@/views/user/UserForm.vue'),
  //       meta: {
  //         title: '编辑用户',
  //         requiresAuth: true,
  //         hideInMenu: true
  //       }
  //     },
  //     {
  //       path: 'roles',
  //       name: 'RoleManagement',
  //       component: () => import('@/views/user/RoleManagement.vue'),
  //       meta: {
  //         title: '角色管理',
  //         icon: 'Avatar',
  //         requiresAuth: true
  //       }
  //     },
  //     {
  //       path: 'permissions',
  //       name: 'UserPermissionManagement',
  //       component: () => import('@/views/user/PermissionManagement.vue'),
  //       meta: {
  //         title: '权限配置',
  //         icon: 'Key',
  //         requiresAuth: true
  //       }
  //     },
  //     {
  //       path: 'resource-permissions',
  //       name: 'ResourcePermissionManage',
  //       component: () => import('@/views/dataResource/PermissionManage.vue'),
  //       meta: {
  //         title: '访问控制',
  //         icon: 'Lock',
  //         requiresAuth: true
  //       }
  //     }
  //   ]
  // },
  // {
  //   path: '/system',
  //   component: Layout,
  //   redirect: '/system/settings',
  //   meta: {
  //     title: '系统管理',
  //     icon: 'Setting',
  //     requiresAuth: true
  //   },
  //   children: [
  //     {
  //       path: 'settings',
  //       name: 'SystemSettings',
  //       component: () => import('@/views/settings/Settings.vue'),
  //       meta: {
  //         title: '系统设置',
  //         icon: 'Tools',
  //         requiresAuth: true
  //       }
  //     },
  //     {
  //       path: 'monitor',
  //       name: 'SystemMonitor',
  //       component: () => import('@/views/system/Monitor.vue'),
  //       meta: {
  //         title: '系统监控',
  //         icon: 'Monitor',
  //         requiresAuth: true
  //       }
  //     },
  //     {
  //       path: 'logs',
  //       name: 'SystemLogs',
  //       component: () => import('@/views/system/Logs.vue'),
  //       meta: {
  //         title: '日志管理',
  //         icon: 'Document',
  //         requiresAuth: true
  //       }
  //     },
  //     {
  //       path: 'backup',
  //       name: 'SystemBackup',
  //       component: () => import('@/views/system/Backup.vue'),
  //       meta: {
  //         title: '备份管理',
  //         icon: 'FolderAdd',
  //         requiresAuth: true
  //       }
  //     },
  //     {
  //       path: 'update',
  //       name: 'SystemUpdate',
  //       component: () => import('@/views/system/Update.vue'),
  //       meta: {
  //         title: '系统更新',
  //         icon: 'Upload',
  //         requiresAuth: true
  //       }
  //     },
  //     {
  //       path: 'datasources',
  //       name: 'DataSourceList',
  //       component: () => import('@/views/datasource/DataSourceList.vue'),
  //       meta: {
  //         title: '数据源管理',
  //         icon: 'Connection',
  //         requiresAuth: true
  //       }
  //     },
  //     {
  //       path: 'auth-error-test',
  //       name: 'AuthErrorTest',
  //       component: () => import('@/views/test/AuthErrorTest.vue'),
  //       meta: {
  //         title: '认证错误测试',
  //         icon: 'Warning',
  //         requiresAuth: true
  //       }
  //     }
  //   ]
  // },
  {
    path: '/resource-center',
    component: Layout,
    redirect: '/resource-center/table-management',
    meta: {
      title: '资源中心管理',
      icon: 'Setting',
      requiresAuth: true,
      // 分组访问权限：资源中心查看
      permission: 'data:resource_center:view',
      strictPermission: true
    },
    children: [
      {
        path: 'table-management',
        name: 'CenterTableManagement',
        component: () => import('@/views/resourceCenter/CenterTableManagement.vue'),
        meta: {
          title: '中心表管理',
          icon: 'Grid',
          requiresAuth: true,
          // 页面访问权限：资源中心-表管理查看
          permission: 'data:resource_center:manage',
          strictPermission: true,
          hideFooter: true
        }
      },
      {
        path: 'table-query',
        name: 'CenterTableQuery',
        component: () => import('@/views/resourceCenter/CenterTableQuery.vue'),
        meta: {
          title: '资源中心',
          icon: 'Search',
          requiresAuth: true,
          // 页面访问权限：资源中心查询
          permission: 'data:resource_center:query',
          strictPermission: true,
          hideFooter: true
        }
      },
      {
        path: 'type-management',
        name: 'ResourceTypeManagement',
        component: () => import('@/views/resourceCenter/ResourceTypeManagement.vue'),
        meta: {
          title: '资源类型管理',
          icon: 'Collection',
          requiresAuth: true,
          // 页面访问权限：资源中心-类型查看
          permission: 'data:resource_center:type',
          strictPermission: true
        }
      }
    ]
  },
  {
    path: '/api-management',
    component: Layout,
    redirect: '/api-management/customers',
    meta: {
      title: 'API接口管理',
      icon: 'Connection',
      requiresAuth: true,
      // 分组访问权限：API查看
      permission: 'data:api:view',
      strictPermission: true
    },
    children: [
      {
        path: 'customers',
        name: 'CustomerManagement',
        component: () => import('@/views/apiManagement/CustomerList.vue'),
        meta: {
          title: '平台管理',
          icon: 'UserFilled',
          requiresAuth: true,
          // 页面访问权限：客户平台查看
          permission: 'data:customer:view',
          strictPermission: true
        }
      },
      {
        path: 'apis',
        name: 'ApiManagement',
        component: () => import('@/views/apiManagement/ApiList.vue'),
        meta: {
          title: 'API管理',
          icon: 'Connection',
          requiresAuth: true,
          // 页面访问权限：API列表查看
          permission: 'data:api:view',
          strictPermission: true
        }
      },
      {
        path: 'apis/:id/fields',
        name: 'ApiFields',
        component: () => import('@/views/apiManagement/ApiFields.vue'),
        meta: {
          title: 'API字段配置',
          requiresAuth: true,
          // API字段配置页需要查询权限（用于编辑字段前校验）
          permission: 'data:resource:query',
          strictPermission: true,
          hideInMenu: true,
          activeMenu: '/api-management/apis'
        }
      },
      {
        path: 'apis/:id/logs',
        name: 'ApiUsageLogs',
        component: () => import('@/views/apiManagement/ApiUsageLogs.vue'),
        meta: {
          title: 'API日志',
          requiresAuth: true,
          // API日志页需要查询权限（用于查看调用记录）
          permission: 'data:resource:query',
          strictPermission: true,
          hideInMenu: true,
          activeMenu: '/api-management/apis'
        }
      },
      // {
      //   path: 'batches',
      //   name: 'BatchManagement',
      //   component: () => import('@/views/apiManagement/BatchList.vue'),
      //   meta: {
      //     title: '批次管理',
      //     icon: 'DataBoard',
      //     requiresAuth: true
      //   }
      // },
      // {
      //   path: 'batches/:id',
      //   name: 'BatchDetail',
      //   component: () => import('@/views/apiManagement/BatchDetail.vue'),
      //   meta: {
      //     title: '批次详情',
      //     requiresAuth: true,
      //     hideInMenu: true,
      //     activeMenu: '/api-management/batches'
      //   }
      // },
      // {
      //   path: 'dashboard',
      //   name: 'ApiDashboard',
      //   component: () => import('@/views/apiManagement/Dashboard.vue'),
      //   meta: {
      //     title: 'API仪表板',
      //     icon: 'Monitor',
      //     requiresAuth: true
      //   }
      // }
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
      // 分组访问权限：用户中心查看
      permission: 'data:user:view',
      strictPermission: true,
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
          // 页面访问权限：用户资料查看
          permission: 'data:user:profile:view',
          strictPermission: true,
          hideInMenu: true
        }
      }
    ]
  }
]

/**
 * 创建路由实例
 */
// 添加日志管理 - 用户操作日志菜单
authRoutes.push({
  path: '/logs',
  component: Layout,
  redirect: '/logs/user-operation-logs',
  meta: {
    title: '日志管理',
    icon: 'Document',
    requiresAuth: true,
    // 分组访问权限：日志查看
    permission: 'data:logs:view',
    strictPermission: true
  },
  children: [
    {
      path: 'user-operation-logs',
      name: 'UserOperationLogs',
      component: () => import('@/views/userOperationLogs/index.vue'),
      meta: {
        title: '用户操作日志',
        icon: 'List',
        requiresAuth: true,
        // 页面访问权限：用户操作日志查看
        permission: 'data:logs:user_operation:view',
        strictPermission: true
      }
    },
    {
      path: 'data-upload-logs',
      name: 'DataUploadLogs',
      component: () => import('@/views/dataUploadLogs/index.vue'),
      meta: {
        title: '数据上传日志',
        icon: 'UploadFilled',
        requiresAuth: true,
        // 页面访问权限：数据上传日志查看
        permission: 'data:logs:data_upload:view',
        strictPermission: true
      }
    }
  ]
})

// 添加数据治理模块路由
// authRoutes.push({
//   path: '/governance',
//   component: Layout,
//   redirect: '/governance/dashboard',
//   meta: {
//     title: '数据治理',
//     icon: 'Files',
//     requiresAuth: true,
//     // 分组访问权限：数据治理查看
//     permission: 'data:governance:view',
//     strictPermission: true
//   },
//   children: [
//     {
//       path: 'dashboard',
//       name: 'GovernanceDashboard',
//       component: () => import('@/views/governance/dashboard/index.vue'),
//       meta: {
//         title: '治理概览',
//         icon: 'DataAnalysis',
//         requiresAuth: true,
//         permission: 'data:governance:dashboard:view',
//         strictPermission: true
//       }
//     },
//     {
//       path: 'metadata',
//       name: 'MetadataManagement',
//       component: RouterView,
//       redirect: '/governance/metadata/catalog',
//       meta: {
//         title: '元数据管理',
//         icon: 'Collection',
//         requiresAuth: true,
//         permission: 'data:governance:metadata:view',
//         strictPermission: true
//       },
//       children: [
//         {
//           path: 'catalog',
//           name: 'DataCatalog',
//           component: () => import('@/views/governance/metadata/catalog/index.vue'),
//           meta: {
//             title: '数据地图',
//             requiresAuth: true,
//             permission: 'data:governance:metadata:catalog:view',
//             strictPermission: true
//           }
//         },
//         {
//           path: 'lineage',
//           name: 'DataLineage',
//           component: () => import('@/views/governance/metadata/lineage/index.vue'),
//           meta: {
//             title: '全链路血缘',
//             requiresAuth: true,
//             permission: 'data:governance:metadata:lineage:view',
//             strictPermission: true
//           }
//         }
//       ]
//     },
//     {
//       path: 'quality',
//       name: 'QualityManagement',
//       component: RouterView,
//       redirect: '/governance/quality/rules',
//       meta: {
//         title: '数据质量',
//         icon: 'CircleCheck',
//         requiresAuth: true,
//         permission: 'data:governance:quality:view',
//         strictPermission: true
//       },
//       children: [
//         {
//           path: 'rules',
//           name: 'QualityRules',
//           component: () => import('@/views/governance/quality/rules/index.vue'),
//           meta: {
//             title: '规则库',
//             requiresAuth: true,
//             permission: 'data:governance:quality:rules:view',
//             strictPermission: true
//           }
//         },
//         {
//           path: 'tasks',
//           name: 'QualityTasks',
//           component: () => import('@/views/governance/quality/tasks/index.vue'),
//           meta: {
//             title: '质检任务',
//             requiresAuth: true,
//             permission: 'data:governance:quality:tasks:view',
//             strictPermission: true
//           }
//         }
//       ]
//     },
//     {
//       path: 'standard',
//       name: 'DataStandard',
//       component: () => import('@/views/governance/standard/index.vue'),
//       meta: {
//         title: '数据标准',
//         icon: 'Notebook',
//         requiresAuth: true,
//         permission: 'data:governance:standard:view',
//         strictPermission: true
//       }
//     },
//     {
//       path: 'security',
//       name: 'DataSecurity',
//       component: () => import('@/views/governance/security/index.vue'),
//       meta: {
//         title: '数据安全',
//         icon: 'Lock',
//         requiresAuth: true,
//         permission: 'data:governance:security:view',
//         strictPermission: true
//       }
//     }
//   ]
// })

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
 *
 * 权限元信息支持：
 * - meta.permission: string，要求具备该单个权限码
 * - meta.permissionsAny: string[]，要求具备列表中的任一权限
 * - meta.permissionsAll: string[]，要求具备列表中的所有权限
 * - meta.roles: string[]，要求具备任一角色
 * - meta.requiresAuth: boolean，需要登录
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

    // 首次进入时初始化权限：避免本地存储为空导致权限误判
    try {
      if ((userStore.userPermissions?.length ?? 0) === 0) {
        await userStore.loadPermissions()
      }
    } catch (e) {
      console.warn('初始化权限失败，继续使用现有权限')
    }
    
    // 检查角色权限（任一匹配）
    if (to.meta.roles) {
      const roles = to.meta.roles as string[]
      if (!roles.some(role => userStore.hasRole(role))) {
        ElMessage.error('没有访问权限')
        next('/404')
        return
      }
    }

    // 检查单个权限码（支持 strictPermission 忽略管理员直通）
    if (to.meta.permission) {
      const perm = to.meta.permission as string
      const useStrict = Boolean((to.meta as any)?.strictPermission)
      const ok = useStrict ? userStore.hasPermissionStrict(perm) : userStore.hasPermission(perm)
      if (!ok) {
        ElMessage.error('没有访问权限')
        next('/404')
        return
      }
    }

    // 检查任一权限满足（支持 strictPermission）
    if (to.meta.permissionsAny) {
      const permsAny = to.meta.permissionsAny as string[]
      const useStrict = Boolean((to.meta as any)?.strictPermission)
      const ok = useStrict
        ? permsAny.some(p => userStore.hasPermissionStrict(p))
        : userStore.hasAnyPermission(permsAny)
      if (!ok) {
        ElMessage.error('没有访问权限')
        next('/404')
        return
      }
    }

    // 检查所有权限满足（支持 strictPermission）
    if (to.meta.permissionsAll) {
      const permsAll = to.meta.permissionsAll as string[]
      const useStrict = Boolean((to.meta as any)?.strictPermission)
      const ok = useStrict
        ? permsAll.every(p => userStore.hasPermissionStrict(p))
        : userStore.hasAllPermissions(permsAll)
      if (!ok) {
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