import type { App } from 'vue'
import { permission, permissionAny, permissionAll, role } from './permission'

/**
 * 注册所有自定义指令
 * @param app Vue应用实例
 */
export function setupDirectives(app: App) {
  // 注册权限指令
  app.directive('permission', permission)
  app.directive('permission-any', permissionAny)
  app.directive('permission-all', permissionAll)
  app.directive('role', role)
}

/**
 * 导出所有指令
 */
export {
  permission,
  permissionAny,
  permissionAll,
  role
}

export default setupDirectives