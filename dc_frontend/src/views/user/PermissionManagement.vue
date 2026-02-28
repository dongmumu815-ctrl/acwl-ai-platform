<template>
  <div class="permission-management-container">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1 class="page-title">
        <el-icon><Lock /></el-icon>
        权限管理
      </h1>
      <p class="page-description">管理系统权限和用户访问控制</p>
    </div>

    <!-- 权限树和详情 -->
    <div class="permission-content">
      <!-- 左侧权限树 -->
      <div class="permission-tree-panel">
        <div class="panel-header">
          <h3>权限树</h3>
          <div class="header-actions">
            <el-button size="small" @click="expandAll">
              <el-icon><Plus /></el-icon>
              展开全部
            </el-button>
            <el-button size="small" @click="collapseAll">
              <el-icon><Minus /></el-icon>
              收起全部
            </el-button>
            <el-button
              size="small"
              :loading="syncing"
              @click="syncFrontendPermissions"
            >
              <el-icon><Connection /></el-icon>
              同步前端权限
            </el-button>
            <el-button type="primary" size="small" @click="addPermission">
              <el-icon><Plus /></el-icon>
              新增权限
            </el-button>
          </div>
        </div>

        <div class="tree-search">
          <el-input
            v-model="treeSearchKeyword"
            placeholder="搜索权限..."
            clearable
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </div>

        <div class="tree-container">
          <el-tree
            ref="permissionTreeRef"
            :data="filteredPermissionTree"
            :props="treeProps"
            :filter-node-method="filterNode"
            node-key="id"
            show-checkbox
            default-expand-all
            @node-click="handleNodeClick"
            @check-change="handleCheckChange"
          >
            <template #default="{ node, data }">
              <div class="tree-node">
                <el-icon
                  class="node-icon"
                  :style="{ color: getPermissionTypeColor(data.type) }"
                >
                  <component :is="getPermissionTypeIcon(data.type)" />
                </el-icon>
                <span class="node-label">{{ data.name }}</span>
                <span class="node-code">({{ data.code }})</span>
                <div class="node-actions">
                  <el-button
                    type="primary"
                    size="small"
                    text
                    @click.stop="editPermission(data)"
                  >
                    编辑
                  </el-button>
                  <el-button
                    type="danger"
                    size="small"
                    text
                    @click.stop="deletePermission(data)"
                  >
                    删除
                  </el-button>
                </div>
              </div>
            </template>
          </el-tree>
        </div>
      </div>

      <!-- 右侧权限详情 -->
      <div class="permission-detail-panel">
        <div class="panel-header">
          <h3>权限详情</h3>
          <div v-if="selectedPermission" class="header-actions">
            <el-button size="small" @click="editPermission(selectedPermission)">
              <el-icon><Edit /></el-icon>
              编辑
            </el-button>
            <el-button
              type="danger"
              size="small"
              @click="deletePermission(selectedPermission)"
            >
              <el-icon><Delete /></el-icon>
              删除
            </el-button>
          </div>
        </div>

        <div v-if="selectedPermission" class="detail-content">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="权限名称">
              {{ selectedPermission.name }}
            </el-descriptions-item>
            <el-descriptions-item label="权限代码">
              <el-tag>{{ selectedPermission.code }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="权限类型">
              <el-tag :type="getPermissionTypeTagType(selectedPermission.type)">
                {{ getPermissionTypeLabel(selectedPermission.type) }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="状态">
              <el-tag :type="selectedPermission.enabled ? 'success' : 'danger'">
                {{ selectedPermission.enabled ? "启用" : "禁用" }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="创建时间" span="2">
              {{ formatDate(selectedPermission.createdAt) }}
            </el-descriptions-item>
            <el-descriptions-item label="描述" span="2">
              {{ selectedPermission.description || "暂无描述" }}
            </el-descriptions-item>
          </el-descriptions>

          <!-- 关联角色 -->
          <div
            v-if="
              selectedPermission.roles && selectedPermission.roles.length > 0
            "
            class="related-roles"
          >
            <h4>关联角色</h4>
            <div class="role-tags">
              <el-tag
                v-for="role in selectedPermission.roles"
                :key="role.id"
                class="role-tag"
                @click="viewRole(role)"
              >
                {{ role.name }}
              </el-tag>
            </div>
          </div>

          <!-- 关联用户 -->
          <div
            v-if="
              selectedPermission.users && selectedPermission.users.length > 0
            "
            class="related-users"
          >
            <h4>直接授权用户</h4>
            <div class="user-list">
              <div
                v-for="user in selectedPermission.users"
                :key="user.id"
                class="user-item"
                @click="viewUser(user)"
              >
                <el-avatar :size="32" :src="user.avatar">
                  {{ user.name.charAt(0) }}
                </el-avatar>
                <span class="user-name">{{ user.name }}</span>
              </div>
            </div>
          </div>
        </div>

        <div v-else class="empty-state">
          <el-empty description="请选择一个权限查看详情" />
        </div>
      </div>
    </div>

    <!-- 权限编辑对话框 -->
    <el-dialog
      v-model="permissionDialogVisible"
      :title="isEditMode ? '编辑权限' : '新增权限'"
      width="600px"
      @close="resetPermissionForm"
    >
      <el-form
        ref="permissionFormRef"
        :model="permissionForm"
        :rules="permissionRules"
        label-width="100px"
      >
        <el-form-item label="权限名称" prop="name">
          <el-input
            v-model="permissionForm.name"
            placeholder="请输入权限名称"
          />
        </el-form-item>

        <el-form-item label="权限代码" prop="code">
          <el-input
            v-model="permissionForm.code"
            placeholder="请输入权限代码"
          />
        </el-form-item>

        <el-form-item label="权限类型" prop="type">
          <el-select v-model="permissionForm.type" placeholder="请选择权限类型">
            <el-option label="菜单" value="menu" />
            <el-option label="按钮" value="button" />
            <el-option label="接口" value="api" />
            <el-option label="数据" value="data" />
          </el-select>
        </el-form-item>

        <el-form-item label="父级权限" prop="parentId">
          <el-tree-select
            v-model="permissionForm.parentId"
            :data="permissionTreeOptions"
            :props="treeSelectProps"
            placeholder="请选择父级权限"
            clearable
            check-strictly
          />
        </el-form-item>

        <el-form-item label="排序" prop="sort">
          <el-input-number v-model="permissionForm.sort" :min="0" :max="9999" />
        </el-form-item>

        <el-form-item label="状态" prop="enabled">
          <el-switch v-model="permissionForm.enabled" />
        </el-form-item>

        <el-form-item label="描述" prop="description">
          <el-input
            v-model="permissionForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入权限描述"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="permissionDialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="saving" @click="savePermission">
            {{ isEditMode ? "更新" : "创建" }}
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch, nextTick } from "vue";
import { ElMessage, ElMessageBox, ElTree } from "element-plus";
import {
  getPermissions,
  createPermission,
  updatePermission,
  deletePermission,
  getPermissionTree,
  batchCreatePermissions,
} from "@/api/user";
import { useUserStore } from "@/stores/user";

// 响应式数据
const permissionTreeRef = ref<InstanceType<typeof ElTree>>();
const permissionFormRef = ref();
const treeSearchKeyword = ref("");
const selectedPermission = ref<any>(null);
const permissionDialogVisible = ref(false);
const isEditMode = ref(false);
const saving = ref(false);
const syncing = ref(false);
const loadingTree = ref(false);
const userStore = useUserStore();

// 已存在与缺失的权限码收集
const existingPermissionCodes = ref<string[]>([]);
const missingPermissionCodes = ref<string[]>([]);

// 树形组件配置
const treeProps = {
  children: "children",
  label: "name",
  disabled: (data: any) => !data.enabled,
};

const treeSelectProps = {
  children: "children",
  label: "name",
  value: "id",
};

// 权限表单
const permissionForm = ref({
  id: null,
  name: "",
  code: "",
  type: "menu",
  parentId: null,
  sort: 0,
  enabled: true,
  description: "",
});

// 表单验证规则
const permissionRules = {
  name: [{ required: true, message: "请输入权限名称", trigger: "blur" }],
  code: [
    { required: true, message: "请输入权限代码", trigger: "blur" },
    {
      pattern: /^[a-zA-Z0-9:_-]+$/,
      message: "权限代码只能包含字母、数字、冒号、下划线和横线",
      trigger: "blur",
    },
  ],
  type: [{ required: true, message: "请选择权限类型", trigger: "change" }],
};

// 权限树数据（从后端加载）
const permissionTree = ref<any[]>([]);

/**
 * 依据后端权限树响应构建前端展示树
 */
const transformPermissionTreeResponse = (
  modules: Array<{ module: string; permissions: any[] }>,
): any[] => {
  const result: any[] = [];
  for (const mod of modules) {
    const moduleNode: any = {
      id: `module:${mod.module}`,
      name: mod.module,
      code: mod.module,
      type: "menu",
      enabled: true,
      sort: 0,
      description: `${mod.module} 模块`,
      createdAt: new Date().toISOString(),
      children: [],
    };
    // 按 resource 分组
    const resourceGroups: Record<string, any[]> = {};
    for (const perm of mod.permissions) {
      const resourceKey = String(perm.resource || "common");
      if (!resourceGroups[resourceKey]) resourceGroups[resourceKey] = [];
      resourceGroups[resourceKey].push(perm);
    }
    for (const [resource, perms] of Object.entries(resourceGroups)) {
      const resourceNode: any = {
        id: `module:${mod.module}:resource:${resource}`,
        name: resource === "common" ? "通用" : resource,
        code:
          resource === "common" ? `${mod.module}` : `${mod.module}:${resource}`,
        type: "menu",
        enabled: true,
        sort: 0,
        description: `${mod.module}:${resource} 权限`,
        createdAt: new Date().toISOString(),
        children: [],
      };
      for (const p of perms) {
        resourceNode.children.push({
          id: p.id,
          name: p.name,
          code: p.code,
          type: getTypeByAction(p.action),
          enabled: Boolean(p.status),
          sort: Number(p.sort_order || 0),
          description: `${p.module}${p.resource ? ":" + p.resource : ""}:${p.action}`,
          createdAt: new Date().toISOString(),
        });
      }
      moduleNode.children.push(resourceNode);
    }
    result.push(moduleNode);
  }
  return result;
};

/**
 * 根据后端 action 字段推断显示类型
 */
const getTypeByAction = (action: string): string => {
  const apiActions = [
    "query",
    "export",
    "download",
    "upload",
    "check",
    "assign",
    "remove",
  ];
  if (apiActions.includes(action)) return "api";
  const buttonActions = [
    "view",
    "create",
    "edit",
    "delete",
    "enable",
    "disable",
  ];
  if (buttonActions.includes(action)) return "button";
  return "data";
};

/**
 * 加载后端权限树并渲染
 */
const loadPermissionTree = async (): Promise<void> => {
  try {
    loadingTree.value = true;
    const resp = await getPermissionTree();
    if (!resp.success) throw new Error(resp.message || "获取权限树失败");
    const modules = (resp.data?.modules || []) as Array<{
      module: string;
      permissions: any[];
    }>;
    permissionTree.value = transformPermissionTreeResponse(modules);
  } catch (error: any) {
    ElMessage.error(error.message || "加载权限树失败");
  } finally {
    loadingTree.value = false;
  }
};

/**
 * 过滤后的权限树
 */
const filteredPermissionTree = computed(() => {
  if (!treeSearchKeyword.value) {
    return permissionTree.value;
  }
  return filterTreeData(permissionTree.value, treeSearchKeyword.value);
});

/**
 * 权限树选择器选项
 */
const permissionTreeOptions = computed(() => {
  return buildTreeSelectOptions(permissionTree.value);
});

/**
 * 过滤树形数据
 */
const filterTreeData = (data: any[], keyword: string): any[] => {
  const result: any[] = [];

  for (const item of data) {
    const match =
      item.name.toLowerCase().includes(keyword.toLowerCase()) ||
      item.code.toLowerCase().includes(keyword.toLowerCase());

    if (match) {
      result.push({ ...item });
    } else if (item.children && item.children.length > 0) {
      const filteredChildren = filterTreeData(item.children, keyword);
      if (filteredChildren.length > 0) {
        result.push({
          ...item,
          children: filteredChildren,
        });
      }
    }
  }

  return result;
};

/**
 * 构建树形选择器选项
 */
const buildTreeSelectOptions = (data: any[]): any[] => {
  return data.map((item) => ({
    id: item.id,
    name: item.name,
    children: item.children ? buildTreeSelectOptions(item.children) : undefined,
  }));
};

/**
 * 获取权限类型图标
 */
const getPermissionTypeIcon = (type: string) => {
  const iconMap: Record<string, string> = {
    menu: "Menu",
    button: "Mouse",
    api: "Connection",
    data: "Coin",
  };
  return iconMap[type] || "Document";
};

/**
 * 获取权限类型颜色
 */
const getPermissionTypeColor = (type: string) => {
  const colorMap: Record<string, string> = {
    menu: "#409EFF",
    button: "#67C23A",
    api: "#E6A23C",
    data: "#F56C6C",
  };
  return colorMap[type] || "#909399";
};

/**
 * 获取权限类型标签类型
 */
const getPermissionTypeTagType = (type: string) => {
  const tagMap: Record<string, string> = {
    menu: "primary",
    button: "success",
    api: "warning",
    data: "danger",
  };
  return tagMap[type] || "info";
};

/**
 * 获取权限类型标签文本
 */
const getPermissionTypeLabel = (type: string) => {
  const labelMap: Record<string, string> = {
    menu: "菜单",
    button: "按钮",
    api: "接口",
    data: "数据",
  };
  return labelMap[type] || type;
};

/**
 * 格式化日期
 */
const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleString("zh-CN");
};

/**
 * 树节点过滤方法
 */
const filterNode = (value: string, data: any) => {
  if (!value) return true;
  return (
    data.name.toLowerCase().includes(value.toLowerCase()) ||
    data.code.toLowerCase().includes(value.toLowerCase())
  );
};

/**
 * 处理节点点击
 */
const handleNodeClick = (data: any) => {
  selectedPermission.value = data;
};

/**
 * 处理复选框变化
 */
const handleCheckChange = (data: any, checked: boolean) => {
  console.log("权限选择变化:", data.name, checked);
};

/**
 * 展开全部节点
 */
const expandAll = () => {
  permissionTreeRef.value?.setExpandedKeys(
    getAllNodeKeys(permissionTree.value),
  );
};

/**
 * 收起全部节点
 */
const collapseAll = () => {
  permissionTreeRef.value?.setExpandedKeys([]);
};

/**
 * 获取所有节点的key
 */
const getAllNodeKeys = (data: any[]): string[] => {
  const keys: string[] = [];

  const traverse = (nodes: any[]) => {
    nodes.forEach((node) => {
      keys.push(node.id.toString());
      if (node.children && node.children.length > 0) {
        traverse(node.children);
      }
    });
  };

  traverse(data);
  return keys;
};

/**
 * 新增权限
 */
const addPermission = () => {
  isEditMode.value = false;
  permissionDialogVisible.value = true;
  resetPermissionForm();
};

/**
 * 编辑权限
 */
const editPermission = (permission: any) => {
  isEditMode.value = true;
  permissionDialogVisible.value = true;

  nextTick(() => {
    Object.assign(permissionForm.value, {
      id: permission.id,
      name: permission.name,
      code: permission.code,
      type: permission.type,
      parentId: permission.parentId || null,
      sort: permission.sort || 0,
      enabled: permission.enabled,
      description: permission.description || "",
    });
  });
};

/**
 * 删除权限
 */
const deletePermission = (permission: any) => {
  ElMessageBox.confirm(`确定要删除权限 "${permission.name}" 吗？`, "确认删除", {
    confirmButtonText: "确定",
    cancelButtonText: "取消",
    type: "warning",
  })
    .then(() => {
      // 这里应该调用删除API
      ElMessage.success("权限删除成功");

      // 如果删除的是当前选中的权限，清空选中状态
      if (
        selectedPermission.value &&
        selectedPermission.value.id === permission.id
      ) {
        selectedPermission.value = null;
      }
    })
    .catch(() => {
      // 用户取消删除
    });
};

/**
 * 保存权限
 */
const savePermission = () => {
  permissionFormRef.value?.validate((valid: boolean) => {
    if (valid) {
      saving.value = true;

      // 模拟保存
      setTimeout(() => {
        saving.value = false;
        permissionDialogVisible.value = false;

        ElMessage.success(isEditMode.value ? "权限更新成功" : "权限创建成功");

        // 这里应该重新加载权限树数据
      }, 1000);
    }
  });
};

/**
 * 同步前端 API 权限到后端（静态扫描 src/api 目录）
 * - 使用 Vite 的 import.meta.glob 以原始文本方式载入所有 API 文件
 * - 正则提取 "permission:" 标注的权限码
 * - 与后端现有权限对比，批量创建缺失项
 */
const syncFrontendPermissions = async (): Promise<void> => {
  try {
    syncing.value = true;
    // 1) 静态扫描前端 API 代码，提取权限码
    const codes = await collectAllFrontendPermissions();
    const uniqueCodes = Array.from(new Set(codes)).filter(Boolean);
    // 2) 拉取后端现有权限码
    const existingResp = await getPermissions({ limit: 5000, skip: 0 });
    const existingCodes = existingResp.success
      ? (existingResp.data.items || []).map((i: any) => i.code)
      : [];
    existingPermissionCodes.value = existingCodes;
    // 3) 计算缺失并批量创建
    const toCreateCodes = uniqueCodes.filter((c) => !existingCodes.includes(c));
    missingPermissionCodes.value = toCreateCodes;
    if (toCreateCodes.length === 0) {
      ElMessage.success("前端权限已与后端同步，无需创建");
      return;
    }
    const payload = toCreateCodes.map((code) =>
      buildPermissionCreateFromCode(code),
    );
    const createResp = await batchCreatePermissions(payload);
    if (!createResp.success)
      throw new Error(createResp.message || "批量创建权限失败");
    ElMessage.success(`已创建 ${payload.length} 个缺失权限`);
    await loadPermissionTree();
  } catch (error: any) {
    ElMessage.error(error.message || "同步前端权限失败");
  } finally {
    syncing.value = false;
  }
};

/**
 * 收集 src/api/*.ts 内所有权限码
 */
const collectAllFrontendPermissions = async (): Promise<string[]> => {
  const modules: Record<string, () => Promise<string>> = import.meta.glob(
    "@/api/*.ts",
    {
      as: "raw",
    },
  ) as any;
  const codes: string[] = [];
  const permissionRegex = /permission\s*:\s*(["'`])([^"'`]+)\1/g;
  for (const loader of Object.values(modules)) {
    try {
      const content = await loader();
      let match: RegExpExecArray | null;
      while ((match = permissionRegex.exec(content)) !== null) {
        const code = match[2];
        if (code) codes.push(code);
      }
    } catch {}
  }
  return codes;
};

/**
 * 将权限码解析为后端创建所需结构
 */
const buildPermissionCreateFromCode = (
  code: string,
): {
  name: string;
  code: string;
  description?: string;
  module: string;
  resource?: string;
  action: string;
  status?: boolean;
  sort_order?: number;
} => {
  const parts = code.split(":");
  const module = parts[0] || "system";
  const resource =
    parts.length > 2 ? parts[1] : parts.length === 2 ? parts[1] : undefined;
  const action = parts[parts.length - 1] || "view";
  const actionNameMap: Record<string, string> = {
    view: "查看",
    create: "创建",
    edit: "编辑",
    delete: "删除",
    export: "导出",
    download: "下载",
    query: "查询",
    assign: "分配",
    remove: "移除",
    enable: "启用",
    disable: "禁用",
  };
  const resLabel = resource ? resource : "通用";
  const name = `${actionNameMap[action] || action}${resLabel === "通用" ? "" : resLabel}`;
  return {
    name,
    code,
    description: "由前端API自动收集导入",
    module,
    resource,
    action,
    status: true,
    sort_order: 0,
  };
};

/**
 * 重置权限表单
 */
const resetPermissionForm = () => {
  permissionForm.value = {
    id: null,
    name: "",
    code: "",
    type: "menu",
    parentId: null,
    sort: 0,
    enabled: true,
    description: "",
  };

  nextTick(() => {
    permissionFormRef.value?.clearValidate();
  });
};

/**
 * 查看角色
 */
const viewRole = (role: any) => {
  ElMessage.info(`查看角色: ${role.name}`);
};

/**
 * 查看用户
 */
const viewUser = (user: any) => {
  ElMessage.info(`查看用户: ${user.name}`);
};

// 监听搜索关键词变化
watch(treeSearchKeyword, (val) => {
  permissionTreeRef.value?.filter(val);
});

/**
 * 组件挂载时初始化
 */
onMounted(() => {
  // 加载后端权限树
  loadPermissionTree().then(() => {
    nextTick(() => {
      const firstLevelKeys = permissionTree.value.map((item) =>
        String(item.id),
      );
      permissionTreeRef.value?.setExpandedKeys(firstLevelKeys);
    });
  });
});
</script>

<style lang="scss" scoped>
.permission-management-container {
  padding: 20px;
  background: var(--el-bg-color-page);
  min-height: 100vh;
}

.page-header {
  margin-bottom: 24px;

  .page-title {
    display: flex;
    align-items: center;
    font-size: 24px;
    font-weight: 600;
    color: var(--el-text-color-primary);
    margin: 0 0 8px 0;

    .el-icon {
      margin-right: 8px;
      color: var(--el-color-primary);
    }
  }

  .page-description {
    color: var(--el-text-color-secondary);
    margin: 0;
  }
}

.permission-content {
  display: flex;
  gap: 20px;
  height: calc(100vh - 140px);
}

.permission-tree-panel {
  flex: 0 0 400px;
  background: var(--el-bg-color);
  border-radius: 8px;
  border: 1px solid var(--el-border-color-light);
  display: flex;
  flex-direction: column;

  .panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px;
    border-bottom: 1px solid var(--el-border-color-lighter);

    h3 {
      margin: 0;
      color: var(--el-text-color-primary);
    }

    .header-actions {
      display: flex;
      gap: 8px;
    }
  }

  .tree-search {
    padding: 16px;
    border-bottom: 1px solid var(--el-border-color-lighter);
  }

  .tree-container {
    flex: 1;
    padding: 16px;
    overflow-y: auto;

    .tree-node {
      display: flex;
      align-items: center;
      width: 100%;

      .node-icon {
        margin-right: 8px;
        font-size: 16px;
      }

      .node-label {
        flex: 1;
        font-weight: 500;
      }

      .node-code {
        color: var(--el-text-color-secondary);
        font-size: 12px;
        margin-left: 8px;
      }

      .node-actions {
        margin-left: 12px;
        opacity: 0;
        transition: opacity 0.2s;

        .el-button {
          padding: 4px 8px;
        }
      }

      &:hover .node-actions {
        opacity: 1;
      }
    }
  }
}

.permission-detail-panel {
  flex: 1;
  background: var(--el-bg-color);
  border-radius: 8px;
  border: 1px solid var(--el-border-color-light);
  display: flex;
  flex-direction: column;

  .panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px;
    border-bottom: 1px solid var(--el-border-color-lighter);

    h3 {
      margin: 0;
      color: var(--el-text-color-primary);
    }

    .header-actions {
      display: flex;
      gap: 8px;
    }
  }

  .detail-content {
    flex: 1;
    padding: 20px;
    overflow-y: auto;

    .related-roles,
    .related-users {
      margin-top: 24px;

      h4 {
        margin: 0 0 12px 0;
        color: var(--el-text-color-primary);
      }
    }

    .role-tags {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;

      .role-tag {
        cursor: pointer;
        transition: all 0.2s;

        &:hover {
          transform: translateY(-1px);
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }
      }
    }

    .user-list {
      display: flex;
      flex-wrap: wrap;
      gap: 12px;

      .user-item {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 8px 12px;
        background: var(--el-bg-color-page);
        border-radius: 6px;
        cursor: pointer;
        transition: all 0.2s;

        &:hover {
          background: var(--el-color-primary-light-9);
          transform: translateY(-1px);
        }

        .user-name {
          font-size: 14px;
          color: var(--el-text-color-primary);
        }
      }
    }
  }

  .empty-state {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
  }
}

.dialog-footer {
  text-align: right;
}

// 响应式设计
@media (max-width: 1200px) {
  .permission-content {
    flex-direction: column;
    height: auto;
  }

  .permission-tree-panel {
    flex: none;
    height: 400px;
  }

  .permission-detail-panel {
    flex: none;
    min-height: 400px;
  }
}

@media (max-width: 768px) {
  .permission-management-container {
    padding: 16px;
  }

  .permission-tree-panel {
    .panel-header {
      flex-direction: column;
      gap: 12px;
      align-items: stretch;

      .header-actions {
        justify-content: center;
        flex-wrap: wrap;
      }
    }
  }

  .permission-detail-panel {
    .panel-header {
      flex-direction: column;
      gap: 12px;
      align-items: stretch;

      .header-actions {
        justify-content: center;
      }
    }
  }
}
</style>
