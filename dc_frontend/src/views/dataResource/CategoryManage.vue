<template>
  <div class="category-manage-container">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1 class="page-title">
        <el-icon><FolderOpened /></el-icon>
        分类管理
      </h1>
      <p class="page-description">管理数据资源的分类体系</p>
    </div>

    <!-- 操作栏 -->
    <div class="action-bar">
      <div class="left-actions">
        <el-button type="primary" @click="showCreateDialog">
          <el-icon><Plus /></el-icon>
          新建分类
        </el-button>
        <el-button @click="expandAll">
          <el-icon><Expand /></el-icon>
          展开全部
        </el-button>
        <el-button @click="collapseAll">
          <el-icon><Fold /></el-icon>
          收起全部
        </el-button>
      </div>

      <div class="right-actions">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索分类名称"
          style="width: 250px"
          clearable
          @input="handleSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-button @click="refreshCategories">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <!-- 分类树 -->
    <div class="category-tree-section">
      <el-card>
        <div class="tree-container">
          <el-tree
            ref="categoryTreeRef"
            :data="filteredCategories"
            :props="treeProps"
            :expand-on-click-node="false"
            :default-expand-all="false"
            node-key="id"
            draggable
            @node-drop="handleNodeDrop"
            @node-click="handleNodeClick"
          >
            <template #default="{ node, data }">
              <div class="tree-node">
                <div class="node-content">
                  <el-icon
                    class="node-icon"
                    :style="{ color: data.color || '#409EFF' }"
                  >
                    <component :is="data.icon || 'Folder'" />
                  </el-icon>
                  <span class="node-label">{{ data.name }}</span>
                  <el-tag
                    v-if="data.resourceCount > 0"
                    size="small"
                    type="info"
                  >
                    {{ data.resourceCount }}
                  </el-tag>
                  <el-tag
                    v-if="data.status === 'disabled'"
                    size="small"
                    type="danger"
                  >
                    已禁用
                  </el-tag>
                </div>

                <div class="node-actions" @click.stop>
                  <el-button
                    size="small"
                    type="primary"
                    link
                    @click="showCreateDialog(data)"
                  >
                    <el-icon><Plus /></el-icon>
                  </el-button>
                  <el-button
                    size="small"
                    type="primary"
                    link
                    @click="showEditDialog(data)"
                  >
                    <el-icon><Edit /></el-icon>
                  </el-button>
                  <el-dropdown @command="handleNodeCommand">
                    <el-button size="small" type="primary" link>
                      <el-icon><MoreFilled /></el-icon>
                    </el-button>
                    <template #dropdown>
                      <el-dropdown-menu>
                        <el-dropdown-item :command="{ action: 'move', data }">
                          <el-icon><Rank /></el-icon>
                          移动
                        </el-dropdown-item>
                        <el-dropdown-item :command="{ action: 'copy', data }">
                          <el-icon><CopyDocument /></el-icon>
                          复制
                        </el-dropdown-item>
                        <el-dropdown-item :command="{ action: 'toggle', data }">
                          <el-icon><Switch /></el-icon>
                          {{ data.status === "active" ? "禁用" : "启用" }}
                        </el-dropdown-item>
                        <el-dropdown-item
                          :command="{ action: 'delete', data }"
                          divided
                          :disabled="data.resourceCount > 0"
                        >
                          <el-icon><Delete /></el-icon>
                          删除
                        </el-dropdown-item>
                      </el-dropdown-menu>
                    </template>
                  </el-dropdown>
                </div>
              </div>
            </template>
          </el-tree>

          <div v-if="filteredCategories.length === 0" class="empty-tree">
            <el-empty description="暂无分类数据">
              <el-button type="primary" @click="showCreateDialog">
                创建第一个分类
              </el-button>
            </el-empty>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 分类详情面板 -->
    <div v-if="selectedCategory" class="category-detail-section">
      <el-card>
        <template #header>
          <div class="detail-header">
            <span>分类详情</span>
            <el-button size="small" @click="selectedCategory = null">
              <el-icon><Close /></el-icon>
            </el-button>
          </div>
        </template>

        <div class="detail-content">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="分类名称">
              {{ selectedCategory.name }}
            </el-descriptions-item>
            <el-descriptions-item label="分类编码">
              {{ selectedCategory.code }}
            </el-descriptions-item>
            <el-descriptions-item label="父级分类">
              {{ selectedCategory.parentName || "根分类" }}
            </el-descriptions-item>
            <el-descriptions-item label="状态">
              <el-tag
                :type="
                  selectedCategory.status === 'active' ? 'success' : 'danger'
                "
              >
                {{ selectedCategory.status === "active" ? "启用" : "禁用" }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="资源数量">
              {{ selectedCategory.resourceCount }}
            </el-descriptions-item>
            <el-descriptions-item label="排序">
              {{ selectedCategory.sort }}
            </el-descriptions-item>
            <el-descriptions-item label="创建时间" span="2">
              {{ formatDate(selectedCategory.createdAt) }}
            </el-descriptions-item>
            <el-descriptions-item label="描述" span="2">
              {{ selectedCategory.description || "暂无描述" }}
            </el-descriptions-item>
          </el-descriptions>

          <div class="detail-actions">
            <el-button type="primary" @click="showEditDialog(selectedCategory)">
              <el-icon><Edit /></el-icon>
              编辑分类
            </el-button>
            <el-button @click="viewCategoryResources(selectedCategory)">
              <el-icon><View /></el-icon>
              查看资源
            </el-button>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 创建/编辑分类对话框 -->
    <el-dialog
      v-model="categoryDialogVisible"
      :title="isEditMode ? '编辑分类' : '新建分类'"
      width="600px"
      @close="resetCategoryForm"
    >
      <el-form
        ref="categoryFormRef"
        :model="categoryForm"
        :rules="categoryRules"
        label-width="100px"
      >
        <el-form-item label="分类名称" prop="name">
          <el-input
            v-model="categoryForm.name"
            placeholder="请输入分类名称"
            maxlength="50"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="分类编码" prop="code">
          <el-input
            v-model="categoryForm.code"
            placeholder="请输入分类编码（英文字母、数字、下划线）"
            maxlength="50"
            show-word-limit
            :disabled="isEditMode"
          />
        </el-form-item>

        <el-form-item label="父级分类" prop="parentId">
          <el-tree-select
            v-model="categoryForm.parentId"
            :data="parentCategoryOptions"
            :props="treeSelectProps"
            placeholder="请选择父级分类（不选择则为根分类）"
            clearable
            check-strictly
            style="width: 100%"
          />
        </el-form-item>

        <el-form-item label="分类图标" prop="icon">
          <div class="icon-selector">
            <el-select
              v-model="categoryForm.icon"
              placeholder="请选择图标"
              style="width: 200px"
            >
              <el-option
                v-for="icon in iconOptions"
                :key="icon.value"
                :label="icon.label"
                :value="icon.value"
              >
                <div class="icon-option">
                  <el-icon><component :is="icon.value" /></el-icon>
                  <span>{{ icon.label }}</span>
                </div>
              </el-option>
            </el-select>

            <el-color-picker
              v-model="categoryForm.color"
              style="margin-left: 12px"
              :predefine="colorPresets"
            />
          </div>
        </el-form-item>

        <el-form-item label="排序" prop="sort">
          <el-input-number
            v-model="categoryForm.sort"
            :min="0"
            :max="9999"
            style="width: 150px"
            placeholder="数字越小越靠前"
          />
        </el-form-item>

        <el-form-item label="状态" prop="status">
          <el-radio-group v-model="categoryForm.status">
            <el-radio value="active">启用</el-radio>
            <el-radio value="disabled">禁用</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="描述" prop="description">
          <el-input
            v-model="categoryForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入分类描述"
            maxlength="200"
            show-word-limit
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="categoryDialogVisible = false">取消</el-button>
          <el-button
            type="primary"
            :loading="submitting"
            @click="submitCategoryForm"
          >
            {{ isEditMode ? "更新" : "创建" }}
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 移动分类对话框 -->
    <el-dialog v-model="moveDialogVisible" title="移动分类" width="500px">
      <div class="move-content">
        <p>
          将分类 <strong>{{ moveCategory?.name }}</strong> 移动到：
        </p>
        <el-tree-select
          v-model="moveTargetId"
          :data="parentCategoryOptions"
          :props="treeSelectProps"
          placeholder="请选择目标父级分类"
          clearable
          check-strictly
          style="width: 100%"
        />
      </div>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="moveDialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="submitting" @click="confirmMove">
            确认移动
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, nextTick } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { useRouter } from "vue-router";

// 路由
const router = useRouter();

// 响应式数据
const categoryTreeRef = ref();
const categoryFormRef = ref();
const searchKeyword = ref("");
const categoryDialogVisible = ref(false);
const moveDialogVisible = ref(false);
const isEditMode = ref(false);
const submitting = ref(false);
const selectedCategory = ref(null);
const moveCategory = ref(null);
const moveTargetId = ref("");

// 分类表单
const categoryForm = reactive({
  id: "",
  name: "",
  code: "",
  parentId: "",
  icon: "Folder",
  color: "#409EFF",
  sort: 0,
  status: "active",
  description: "",
});

// 表单验证规则
const categoryRules = {
  name: [
    { required: true, message: "请输入分类名称", trigger: "blur" },
    { min: 2, max: 50, message: "长度在 2 到 50 个字符", trigger: "blur" },
  ],
  code: [
    { required: true, message: "请输入分类编码", trigger: "blur" },
    {
      pattern: /^[a-zA-Z0-9_]+$/,
      message: "只能包含字母、数字和下划线",
      trigger: "blur",
    },
    { min: 2, max: 50, message: "长度在 2 到 50 个字符", trigger: "blur" },
  ],
  sort: [{ type: "number", message: "排序必须为数字", trigger: "blur" }],
};

// 树形组件配置
const treeProps = {
  children: "children",
  label: "name",
  disabled: (data: any) => data.status === "disabled",
};

const treeSelectProps = {
  children: "children",
  label: "name",
  value: "id",
  disabled: "disabled",
};

// 图标选项
const iconOptions = [
  { label: "文件夹", value: "Folder" },
  { label: "数据库", value: "Coin" },
  { label: "文档", value: "Document" },
  { label: "图片", value: "Picture" },
  { label: "视频", value: "VideoPlay" },
  { label: "音频", value: "Headphone" },
  { label: "代码", value: "DocumentCopy" },
  { label: "设置", value: "Setting" },
  { label: "用户", value: "User" },
  { label: "标签", value: "PriceTag" },
];

// 颜色预设
const colorPresets = [
  "#409EFF",
  "#67C23A",
  "#E6A23C",
  "#F56C6C",
  "#909399",
  "#C71585",
  "#FF6347",
  "#32CD32",
  "#1E90FF",
  "#FF69B4",
  "#8A2BE2",
  "#00CED1",
];

// 分类数据
const categories = ref([
  {
    id: 1,
    name: "数据库资源",
    code: "database",
    parentId: null,
    parentName: null,
    icon: "Coin",
    color: "#409EFF",
    sort: 1,
    status: "active",
    resourceCount: 15,
    description: "各类数据库资源",
    createdAt: "2024-01-15 10:30:00",
    children: [
      {
        id: 11,
        name: "MySQL数据库",
        code: "mysql",
        parentId: 1,
        parentName: "数据库资源",
        icon: "Coin",
        color: "#E6A23C",
        sort: 1,
        status: "active",
        resourceCount: 8,
        description: "MySQL数据库实例",
        createdAt: "2024-01-15 10:35:00",
        children: [],
      },
      {
        id: 12,
        name: "PostgreSQL数据库",
        code: "postgresql",
        parentId: 1,
        parentName: "数据库资源",
        icon: "Coin",
        color: "#67C23A",
        sort: 2,
        status: "active",
        resourceCount: 5,
        description: "PostgreSQL数据库实例",
        createdAt: "2024-01-15 10:40:00",
        children: [],
      },
      {
        id: 13,
        name: "Redis缓存",
        code: "redis",
        parentId: 1,
        parentName: "数据库资源",
        icon: "Coin",
        color: "#F56C6C",
        sort: 3,
        status: "active",
        resourceCount: 2,
        description: "Redis缓存实例",
        createdAt: "2024-01-15 10:45:00",
        children: [],
      },
    ],
  },
  {
    id: 2,
    name: "API接口",
    code: "api",
    parentId: null,
    parentName: null,
    icon: "DocumentCopy",
    color: "#67C23A",
    sort: 2,
    status: "active",
    resourceCount: 12,
    description: "各类API接口资源",
    createdAt: "2024-01-15 11:00:00",
    children: [
      {
        id: 21,
        name: "REST API",
        code: "rest_api",
        parentId: 2,
        parentName: "API接口",
        icon: "DocumentCopy",
        color: "#409EFF",
        sort: 1,
        status: "active",
        resourceCount: 8,
        description: "RESTful API接口",
        createdAt: "2024-01-15 11:05:00",
        children: [],
      },
      {
        id: 22,
        name: "GraphQL API",
        code: "graphql_api",
        parentId: 2,
        parentName: "API接口",
        icon: "DocumentCopy",
        color: "#E6A23C",
        sort: 2,
        status: "active",
        resourceCount: 4,
        description: "GraphQL API接口",
        createdAt: "2024-01-15 11:10:00",
        children: [],
      },
    ],
  },
  {
    id: 3,
    name: "文件资源",
    code: "file",
    parentId: null,
    parentName: null,
    icon: "Document",
    color: "#E6A23C",
    sort: 3,
    status: "active",
    resourceCount: 25,
    description: "各类文件资源",
    createdAt: "2024-01-15 11:15:00",
    children: [
      {
        id: 31,
        name: "文档文件",
        code: "document",
        parentId: 3,
        parentName: "文件资源",
        icon: "Document",
        color: "#409EFF",
        sort: 1,
        status: "active",
        resourceCount: 10,
        description: "Word、PDF等文档文件",
        createdAt: "2024-01-15 11:20:00",
        children: [],
      },
      {
        id: 32,
        name: "图片文件",
        code: "image",
        parentId: 3,
        parentName: "文件资源",
        icon: "Picture",
        color: "#67C23A",
        sort: 2,
        status: "active",
        resourceCount: 15,
        description: "JPG、PNG等图片文件",
        createdAt: "2024-01-15 11:25:00",
        children: [],
      },
    ],
  },
  {
    id: 4,
    name: "已禁用分类",
    code: "disabled",
    parentId: null,
    parentName: null,
    icon: "Folder",
    color: "#909399",
    sort: 999,
    status: "disabled",
    resourceCount: 0,
    description: "已禁用的分类示例",
    createdAt: "2024-01-15 12:00:00",
    children: [],
  },
]);

/**
 * 过滤后的分类数据
 */
const filteredCategories = computed(() => {
  if (!searchKeyword.value) {
    return categories.value;
  }

  const filterTree = (nodes: any[]): any[] => {
    return nodes.filter((node) => {
      const matchesKeyword = node.name
        .toLowerCase()
        .includes(searchKeyword.value.toLowerCase());
      const hasMatchingChildren =
        node.children && filterTree(node.children).length > 0;

      if (hasMatchingChildren) {
        node.children = filterTree(node.children);
      }

      return matchesKeyword || hasMatchingChildren;
    });
  };

  return filterTree(categories.value);
});

/**
 * 父级分类选项
 */
const parentCategoryOptions = computed(() => {
  const buildOptions = (nodes: any[], excludeId?: string): any[] => {
    return nodes
      .filter((node) => node.id !== excludeId)
      .map((node) => ({
        id: node.id,
        name: node.name,
        disabled: node.status === "disabled",
        children: node.children ? buildOptions(node.children, excludeId) : [],
      }));
  };

  return buildOptions(categories.value, categoryForm.id);
});

/**
 * 格式化日期
 */
const formatDate = (dateStr: string) => {
  if (!dateStr) return "-";
  return new Date(dateStr).toLocaleString("zh-CN");
};

/**
 * 搜索处理
 */
const handleSearch = () => {
  // 搜索时自动展开所有节点
  if (searchKeyword.value) {
    nextTick(() => {
      categoryTreeRef.value?.setExpandedKeys(
        getAllNodeKeys(filteredCategories.value),
      );
    });
  }
};

/**
 * 获取所有节点的key
 */
const getAllNodeKeys = (nodes: any[]): string[] => {
  const keys: string[] = [];
  const traverse = (nodeList: any[]) => {
    nodeList.forEach((node) => {
      keys.push(node.id);
      if (node.children && node.children.length > 0) {
        traverse(node.children);
      }
    });
  };
  traverse(nodes);
  return keys;
};

/**
 * 展开全部
 */
const expandAll = () => {
  const allKeys = getAllNodeKeys(categories.value);
  categoryTreeRef.value?.setExpandedKeys(allKeys);
};

/**
 * 收起全部
 */
const collapseAll = () => {
  categoryTreeRef.value?.setExpandedKeys([]);
};

/**
 * 刷新分类
 */
const refreshCategories = () => {
  // 模拟刷新
  ElMessage.success("分类数据已刷新");
};

/**
 * 节点点击处理
 */
const handleNodeClick = (data: any) => {
  console.log("=== 分类节点点击调试信息 ===");
  console.log("点击的分类节点:", data);
  console.log("分类ID:", data.id);
  console.log("分类名称:", data.name);
  console.log("分类状态:", data.status);
  console.log("当前路由:", route.path);
  console.log("========================");

  selectedCategory.value = data;
};

/**
 * 节点拖拽处理
 */
const handleNodeDrop = (draggingNode: any, dropNode: any, dropType: string) => {
  if (dropType === "inner") {
    ElMessage.success(
      `已将 "${draggingNode.data.name}" 移动到 "${dropNode.data.name}" 下`,
    );
  } else {
    ElMessage.success(`已调整 "${draggingNode.data.name}" 的位置`);
  }
};

/**
 * 节点命令处理
 */
const handleNodeCommand = (command: any) => {
  const { action, data } = command;

  switch (action) {
    case "move":
      showMoveDialog(data);
      break;
    case "copy":
      copyCategory(data);
      break;
    case "toggle":
      toggleCategoryStatus(data);
      break;
    case "delete":
      deleteCategory(data);
      break;
  }
};

/**
 * 显示创建对话框
 */
const showCreateDialog = (parentCategory?: any) => {
  console.log("=== 创建分类调试信息 ===");
  console.log("父级分类:", parentCategory);
  console.log("当前路由:", route.path);
  console.log("用户权限:", userStore.userPermissions);
  console.log("准备打开创建分类对话框");
  console.log("========================");

  isEditMode.value = false;
  resetCategoryForm();

  if (parentCategory) {
    categoryForm.parentId = parentCategory.id;
  }

  categoryDialogVisible.value = true;
};

/**
 * 显示编辑对话框
 */
const showEditDialog = (category: any) => {
  console.log("=== 编辑分类调试信息 ===");
  console.log("要编辑的分类:", category);
  console.log("分类ID:", category.id);
  console.log("分类名称:", category.name);
  console.log("当前路由:", route.path);
  console.log("用户权限:", userStore.userPermissions);
  console.log("准备打开编辑分类对话框");
  console.log("========================");

  isEditMode.value = true;

  Object.assign(categoryForm, {
    id: category.id,
    name: category.name,
    code: category.code,
    parentId: category.parentId || "",
    icon: category.icon,
    color: category.color,
    sort: category.sort,
    status: category.status,
    description: category.description,
  });

  categoryDialogVisible.value = true;
};

/**
 * 显示移动对话框
 */
const showMoveDialog = (category: any) => {
  moveCategory.value = category;
  moveTargetId.value = "";
  moveDialogVisible.value = true;
};

/**
 * 重置表单
 */
const resetCategoryForm = () => {
  Object.assign(categoryForm, {
    id: "",
    name: "",
    code: "",
    parentId: "",
    icon: "Folder",
    color: "#409EFF",
    sort: 0,
    status: "active",
    description: "",
  });

  categoryFormRef.value?.clearValidate();
};

/**
 * 提交表单
 */
const submitCategoryForm = () => {
  categoryFormRef.value?.validate((valid: boolean) => {
    if (!valid) return;

    submitting.value = true;

    // 模拟提交
    setTimeout(() => {
      if (isEditMode.value) {
        ElMessage.success("分类更新成功");
      } else {
        ElMessage.success("分类创建成功");
      }

      categoryDialogVisible.value = false;
      submitting.value = false;

      // 这里应该刷新分类数据
      refreshCategories();
    }, 1000);
  });
};

/**
 * 确认移动
 */
const confirmMove = () => {
  if (!moveCategory.value) return;

  submitting.value = true;

  // 模拟移动
  setTimeout(() => {
    ElMessage.success(`已将 "${moveCategory.value.name}" 移动成功`);
    moveDialogVisible.value = false;
    submitting.value = false;

    // 这里应该刷新分类数据
    refreshCategories();
  }, 1000);
};

/**
 * 复制分类
 */
const copyCategory = (category: any) => {
  ElMessage.success(`已复制分类 "${category.name}"`);
};

/**
 * 切换分类状态
 */
const toggleCategoryStatus = (category: any) => {
  const newStatus = category.status === "active" ? "disabled" : "active";
  const action = newStatus === "active" ? "启用" : "禁用";

  ElMessageBox.confirm(
    `确定要${action}分类 "${category.name}" 吗？`,
    "确认操作",
    {
      confirmButtonText: "确定",
      cancelButtonText: "取消",
      type: "warning",
    },
  )
    .then(() => {
      // 模拟状态切换
      category.status = newStatus;
      ElMessage.success(`已${action}分类 "${category.name}"`);
    })
    .catch(() => {
      // 取消操作
    });
};

/**
 * 删除分类
 */
const deleteCategory = (category: any) => {
  if (category.resourceCount > 0) {
    ElMessage.warning("该分类下还有资源，无法删除");
    return;
  }

  ElMessageBox.confirm(
    `确定要删除分类 "${category.name}" 吗？此操作不可恢复。`,
    "确认删除",
    {
      confirmButtonText: "确定删除",
      cancelButtonText: "取消",
      type: "error",
    },
  )
    .then(() => {
      ElMessage.success(`已删除分类 "${category.name}"`);
      // 这里应该刷新分类数据
      refreshCategories();
    })
    .catch(() => {
      // 取消删除
    });
};

/**
 * 查看分类资源
 */
const viewCategoryResources = (category: any) => {
  router.push({
    name: "ResourceList",
    query: {
      categoryId: category.id,
      categoryName: category.name,
    },
  });
};

/**
 * 组件挂载时初始化
 */
onMounted(() => {
  // 初始化数据
});
</script>

<style lang="scss" scoped>
.category-manage-container {
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

.action-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 16px;
  background: var(--el-bg-color);
  border-radius: 8px;
  border: 1px solid var(--el-border-color-lighter);

  .left-actions,
  .right-actions {
    display: flex;
    gap: 12px;
    align-items: center;
  }
}

.category-tree-section {
  margin-bottom: 20px;

  .tree-container {
    min-height: 400px;

    .tree-node {
      display: flex;
      justify-content: space-between;
      align-items: center;
      width: 100%;
      padding: 4px 8px;

      .node-content {
        display: flex;
        align-items: center;
        gap: 8px;
        flex: 1;

        .node-icon {
          font-size: 16px;
        }

        .node-label {
          font-size: 14px;
          font-weight: 500;
        }
      }

      .node-actions {
        display: flex;
        gap: 4px;
        opacity: 0;
        transition: opacity 0.2s;
      }

      &:hover {
        .node-actions {
          opacity: 1;
        }
      }
    }

    .empty-tree {
      display: flex;
      justify-content: center;
      align-items: center;
      height: 300px;
    }
  }
}

.category-detail-section {
  .detail-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .detail-content {
    .detail-actions {
      margin-top: 20px;
      text-align: center;

      .el-button {
        margin: 0 8px;
      }
    }
  }
}

.icon-selector {
  display: flex;
  align-items: center;

  .icon-option {
    display: flex;
    align-items: center;
    gap: 8px;
  }
}

.move-content {
  padding: 20px 0;

  p {
    margin-bottom: 16px;
    color: var(--el-text-color-primary);
  }
}

.dialog-footer {
  text-align: right;
}

// 响应式设计
@media (max-width: 1200px) {
  .action-bar {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;

    .left-actions,
    .right-actions {
      justify-content: center;
    }
  }
}

@media (max-width: 768px) {
  .category-manage-container {
    padding: 16px;
  }

  .action-bar {
    .left-actions,
    .right-actions {
      flex-wrap: wrap;
      gap: 8px;
    }

    .el-input {
      width: 100% !important;
    }
  }

  .tree-node {
    .node-actions {
      opacity: 1 !important;
    }
  }

  .category-detail-section {
    .el-descriptions {
      :deep(.el-descriptions__body) {
        .el-descriptions__table {
          .el-descriptions__cell {
            padding: 8px !important;
          }
        }
      }
    }
  }
}
</style>
