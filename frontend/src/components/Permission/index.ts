/**
 * 权限组件库
 * 提供统一的权限控制组件
 */

import PermissionWrapper from './PermissionWrapper.vue'
import PermissionButton from './PermissionButton.vue'
import PermissionTable from './PermissionTable.vue'
import PermissionMenu from './PermissionMenu.vue'
import type { App } from 'vue'

// 组件列表
const components = [
  PermissionWrapper,
  PermissionButton,
  PermissionTable,
  PermissionMenu
]

/**
 * 安装权限组件
 * @param app Vue应用实例
 */
export function setupPermissionComponents(app: App) {
  components.forEach(component => {
    app.component(component.name || component.__name, component)
  })
}

// 导出组件
export {
  PermissionWrapper,
  PermissionButton,
  PermissionTable,
  PermissionMenu
}

// 默认导出
export default {
  install: setupPermissionComponents
}