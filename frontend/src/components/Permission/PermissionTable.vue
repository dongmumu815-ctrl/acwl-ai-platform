<template>
  <el-table v-bind="$attrs" v-on="$listeners">
    <slot />
    
    <!-- 权限控制的操作列 -->
    <el-table-column
      v-if="showActionColumn"
      :label="actionColumnLabel"
      :width="actionColumnWidth"
      :fixed="actionColumnFixed"
      align="center"
    >
      <template #default="{ row, $index }">
        <div class="table-actions">
          <template v-for="action in visibleActions" :key="action.key">
            <PermissionButton
              v-if="shouldShowAction(action, row, $index)"
              v-bind="action.buttonProps"
              :permission="action.permission"
              :permissions="action.permissions"
              :role="action.role"
              :roles="action.roles"
              :mode="action.mode"
              :behavior="action.behavior || 'hide'"
              :no-permission-message="action.noPermissionMessage"
              @click="handleActionClick(action, row, $index)"
              @no-permission="handleNoPermission(action, row, $index)"
            >
              {{ action.label }}
            </PermissionButton>
          </template>
        </div>
      </template>
    </el-table-column>
  </el-table>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import PermissionButton from './PermissionButton.vue'
import type { ButtonProps } from 'element-plus'

/**
 * 权限表格组件
 * 提供带权限控制的表格操作列
 */

interface TableAction {
  /** 操作唯一标识 */
  key: string
  /** 操作标签 */
  label: string
  /** 权限代码 */
  permission?: string
  /** 权限代码数组 */
  permissions?: string[]
  /** 角色代码 */
  role?: string
  /** 角色代码数组 */
  roles?: string[]
  /** 权限检查模式 */
  mode?: 'any' | 'all'
  /** 无权限时的行为 */
  behavior?: 'hide' | 'disable'
  /** 无权限时的提示信息 */
  noPermissionMessage?: string
  /** 按钮属性 */
  buttonProps?: Partial<ButtonProps>
  /** 显示条件函数 */
  show?: (row: any, index: number) => boolean
  /** 点击处理函数 */
  handler?: (row: any, index: number) => void
}

interface Props {
  /** 表格操作配置 */
  actions?: TableAction[]
  /** 操作列标签 */
  actionColumnLabel?: string
  /** 操作列宽度 */
  actionColumnWidth?: string | number
  /** 操作列是否固定 */
  actionColumnFixed?: boolean | string
  /** 是否显示操作列 */
  showActionColumn?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  actions: () => [],
  actionColumnLabel: '操作',
  actionColumnWidth: 200,
  actionColumnFixed: 'right',
  showActionColumn: true
})

const emit = defineEmits<{
  actionClick: [action: TableAction, row: any, index: number]
  noPermission: [action: TableAction, row: any, index: number]
}>()

// 可见的操作
const visibleActions = computed(() => {
  return props.actions.filter(action => action.show !== false)
})

// 判断是否显示操作
const shouldShowAction = (action: TableAction, row: any, index: number): boolean => {
  if (typeof action.show === 'function') {
    return action.show(row, index)
  }
  return true
}

// 处理操作点击
const handleActionClick = (action: TableAction, row: any, index: number) => {
  if (typeof action.handler === 'function') {
    action.handler(row, index)
  }
  emit('actionClick', action, row, index)
}

// 处理无权限
const handleNoPermission = (action: TableAction, row: any, index: number) => {
  emit('noPermission', action, row, index)
}
</script>

<style scoped>
.table-actions {
  display: flex;
  gap: 8px;
  justify-content: center;
  align-items: center;
  flex-wrap: wrap;
}

.table-actions .el-button {
  margin: 0;
}
</style>