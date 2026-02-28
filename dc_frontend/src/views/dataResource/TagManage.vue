<template>
  <div class="tag-manage-container">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1 class="page-title">
        <el-icon><PriceTag /></el-icon>
        标签管理
      </h1>
      <p class="page-description">管理数据资源的标签体系</p>
    </div>

    <!-- 操作栏 -->
    <div class="action-bar">
      <div class="left-actions">
        <el-button type="primary" @click="showCreateDialog">
          <el-icon><Plus /></el-icon>
          新建标签
        </el-button>
        <el-button :disabled="selectedTags.length === 0" @click="batchDelete">
          <el-icon><Delete /></el-icon>
          批量删除
        </el-button>
        <el-button @click="exportTags">
          <el-icon><Download /></el-icon>
          导出标签
        </el-button>
        <el-button @click="importTags">
          <el-icon><Upload /></el-icon>
          导入标签
        </el-button>
      </div>

      <div class="right-actions">
        <el-select
          v-model="filterStatus"
          placeholder="状态筛选"
          style="width: 120px"
          clearable
          @change="handleFilter"
        >
          <el-option label="启用" value="active" />
          <el-option label="禁用" value="disabled" />
        </el-select>

        <el-select
          v-model="sortBy"
          placeholder="排序方式"
          style="width: 150px"
          @change="handleSort"
        >
          <el-option label="创建时间" value="created_at" />
          <el-option label="使用次数" value="usage_count" />
          <el-option label="标签名称" value="name" />
        </el-select>

        <el-input
          v-model="searchKeyword"
          placeholder="搜索标签名称"
          style="width: 250px"
          clearable
          @input="handleSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>

        <el-button @click="refreshTags">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <!-- 标签统计 -->
    <div class="stats-section">
      <el-row :gutter="20">
        <el-col :span="6">
          <el-card class="stats-card">
            <div class="stats-content">
              <div class="stats-icon">
                <el-icon color="#409EFF"><PriceTag /></el-icon>
              </div>
              <div class="stats-info">
                <div class="stats-number">{{ totalTags }}</div>
                <div class="stats-label">总标签数</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stats-card">
            <div class="stats-content">
              <div class="stats-icon">
                <el-icon color="#67C23A"><CircleCheck /></el-icon>
              </div>
              <div class="stats-info">
                <div class="stats-number">{{ activeTags }}</div>
                <div class="stats-label">启用标签</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stats-card">
            <div class="stats-content">
              <div class="stats-icon">
                <el-icon color="#E6A23C"><Warning /></el-icon>
              </div>
              <div class="stats-info">
                <div class="stats-number">{{ disabledTags }}</div>
                <div class="stats-label">禁用标签</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stats-card">
            <div class="stats-content">
              <div class="stats-icon">
                <el-icon color="#F56C6C"><Link /></el-icon>
              </div>
              <div class="stats-info">
                <div class="stats-number">{{ usedTags }}</div>
                <div class="stats-label">已使用标签</div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 标签列表 -->
    <div class="tag-list-section">
      <el-card>
        <template #header>
          <div class="card-header">
            <span>标签列表</span>
            <div class="header-actions">
              <el-button size="small" @click="toggleView">
                <el-icon><Grid /></el-icon>
                {{ viewMode === "table" ? "卡片视图" : "表格视图" }}
              </el-button>
            </div>
          </div>
        </template>

        <!-- 表格视图 -->
        <div v-if="viewMode === 'table'" class="table-view">
          <el-table
            v-loading="loading"
            :data="filteredTags"
            stripe
            border
            style="width: 100%"
            @selection-change="handleSelectionChange"
          >
            <el-table-column type="selection" width="55" />

            <el-table-column prop="name" label="标签名称" min-width="150">
              <template #default="{ row }">
                <div class="tag-name-cell">
                  <el-tag
                    :color="row.color"
                    :style="{ color: getTextColor(row.color) }"
                    size="small"
                  >
                    {{ row.name }}
                  </el-tag>
                </div>
              </template>
            </el-table-column>

            <el-table-column
              prop="description"
              label="描述"
              min-width="200"
              show-overflow-tooltip
            />

            <el-table-column
              prop="usage_count"
              label="使用次数"
              width="100"
              sortable
            >
              <template #default="{ row }">
                <el-link
                  type="primary"
                  :disabled="row.usage_count === 0"
                  @click="viewTagUsage(row)"
                >
                  {{ row.usage_count }}
                </el-link>
              </template>
            </el-table-column>

            <el-table-column prop="status" label="状态" width="80">
              <template #default="{ row }">
                <el-tag
                  :type="row.status === 'active' ? 'success' : 'danger'"
                  size="small"
                >
                  {{ row.status === "active" ? "启用" : "禁用" }}
                </el-tag>
              </template>
            </el-table-column>

            <el-table-column prop="created_at" label="创建时间" width="180">
              <template #default="{ row }">
                {{ formatDate(row.created_at) }}
              </template>
            </el-table-column>

            <el-table-column label="操作" width="200" fixed="right">
              <template #default="{ row }">
                <el-button
                  size="small"
                  type="primary"
                  link
                  @click="showEditDialog(row)"
                >
                  <el-icon><Edit /></el-icon>
                  编辑
                </el-button>
                <el-button
                  size="small"
                  :type="row.status === 'active' ? 'warning' : 'success'"
                  link
                  @click="toggleTagStatus(row)"
                >
                  <el-icon><Switch /></el-icon>
                  {{ row.status === "active" ? "禁用" : "启用" }}
                </el-button>
                <el-button
                  size="small"
                  type="danger"
                  link
                  :disabled="row.usage_count > 0"
                  @click="deleteTag(row)"
                >
                  <el-icon><Delete /></el-icon>
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>

          <!-- 分页 -->
          <div class="pagination-wrapper">
            <el-pagination
              v-model:current-page="currentPage"
              v-model:page-size="pageSize"
              :page-sizes="[10, 20, 50, 100]"
              :total="totalCount"
              layout="total, sizes, prev, pager, next, jumper"
              @size-change="handleSizeChange"
              @current-change="handleCurrentChange"
            />
          </div>
        </div>

        <!-- 卡片视图 -->
        <div v-else class="card-view">
          <div class="tag-cards">
            <div
              v-for="tag in filteredTags"
              :key="tag.id"
              class="tag-card"
              :class="{ selected: selectedTags.includes(tag) }"
              @click="toggleTagSelection(tag)"
            >
              <div class="tag-card-header">
                <el-tag
                  :color="tag.color"
                  :style="{ color: getTextColor(tag.color) }"
                  size="large"
                >
                  {{ tag.name }}
                </el-tag>
                <el-dropdown @command="handleTagCommand">
                  <el-button size="small" type="primary" link>
                    <el-icon><MoreFilled /></el-icon>
                  </el-button>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item
                        :command="{ action: 'edit', data: tag }"
                      >
                        <el-icon><Edit /></el-icon>
                        编辑
                      </el-dropdown-item>
                      <el-dropdown-item
                        :command="{ action: 'toggle', data: tag }"
                      >
                        <el-icon><Switch /></el-icon>
                        {{ tag.status === "active" ? "禁用" : "启用" }}
                      </el-dropdown-item>
                      <el-dropdown-item
                        :command="{ action: 'delete', data: tag }"
                        divided
                        :disabled="tag.usage_count > 0"
                      >
                        <el-icon><Delete /></el-icon>
                        删除
                      </el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </div>

              <div class="tag-card-content">
                <div class="tag-info">
                  <div class="tag-description">
                    {{ tag.description || "暂无描述" }}
                  </div>
                </div>

                <div class="tag-stats">
                  <div class="stat-item">
                    <span class="stat-label">使用次数:</span>
                    <span class="stat-value">{{ tag.usage_count }}</span>
                  </div>
                  <div class="stat-item">
                    <span class="stat-label">状态:</span>
                    <el-tag
                      :type="tag.status === 'active' ? 'success' : 'danger'"
                      size="small"
                    >
                      {{ tag.status === "active" ? "启用" : "禁用" }}
                    </el-tag>
                  </div>
                </div>

                <div class="tag-meta">
                  <span class="create-time">{{
                    formatDate(tag.created_at)
                  }}</span>
                </div>
              </div>
            </div>
          </div>

          <div v-if="filteredTags.length === 0" class="empty-cards">
            <el-empty description="暂无标签数据">
              <el-button type="primary" @click="showCreateDialog">
                创建第一个标签
              </el-button>
            </el-empty>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 创建/编辑标签对话框 -->
    <el-dialog
      v-model="tagDialogVisible"
      :title="isEditMode ? '编辑标签' : '新建标签'"
      width="500px"
      @close="resetTagForm"
    >
      <el-form
        ref="tagFormRef"
        :model="tagForm"
        :rules="tagRules"
        label-width="80px"
      >
        <el-form-item label="标签名称" prop="name">
          <el-input
            v-model="tagForm.name"
            placeholder="请输入标签名称"
            maxlength="20"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="标签颜色" prop="color">
          <div class="color-selector">
            <el-color-picker
              v-model="tagForm.color"
              :predefine="colorPresets"
              show-alpha
            />
            <div class="color-preview">
              <el-tag
                :color="tagForm.color"
                :style="{ color: getTextColor(tagForm.color) }"
                size="large"
              >
                {{ tagForm.name || "预览" }}
              </el-tag>
            </div>
          </div>
        </el-form-item>

        <el-form-item label="状态" prop="status">
          <el-radio-group v-model="tagForm.status">
            <el-radio value="active">启用</el-radio>
            <el-radio value="disabled">禁用</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="描述" prop="description">
          <el-input
            v-model="tagForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入标签描述"
            maxlength="100"
            show-word-limit
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="tagDialogVisible = false">取消</el-button>
          <el-button
            type="primary"
            :loading="submitting"
            @click="submitTagForm"
          >
            {{ isEditMode ? "更新" : "创建" }}
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 标签使用详情对话框 -->
    <el-dialog v-model="usageDialogVisible" title="标签使用详情" width="800px">
      <div v-if="currentTag" class="usage-content">
        <div class="usage-header">
          <el-tag
            :color="currentTag.color"
            :style="{ color: getTextColor(currentTag.color) }"
            size="large"
          >
            {{ currentTag.name }}
          </el-tag>
          <span class="usage-count"
            >共被 {{ currentTag.usage_count }} 个资源使用</span
          >
        </div>

        <el-table
          :data="tagUsageList"
          stripe
          style="width: 100%"
          max-height="400"
        >
          <el-table-column
            prop="resourceName"
            label="资源名称"
            min-width="200"
          />
          <el-table-column prop="resourceType" label="资源类型" width="120">
            <template #default="{ row }">
              <el-tag type="info" size="small">
                {{ getResourceTypeLabel(row.resourceType) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="categoryName" label="所属分类" width="150" />
          <el-table-column prop="created_at" label="关联时间" width="180">
            <template #default="{ row }">
              {{ formatDate(row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="100">
            <template #default="{ row }">
              <el-button
                size="small"
                type="primary"
                link
                @click="viewResource(row)"
              >
                查看
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import type { FormInstance } from "element-plus";
import {
  PriceTag,
  Plus,
  Delete,
  Download,
  Upload,
  Search,
  Refresh,
  CircleCheck,
  Warning,
  Link,
  Grid,
  Edit,
  Switch,
  MoreFilled,
} from "@element-plus/icons-vue";
import { useRouter } from "vue-router";
import { tagApi } from "@/api/dataResource";
import type {
  DataResourceTag,
  TagCreateRequest,
  TagUpdateRequest,
  TagListQuery,
  TagUsageStats,
  TagBatchDeleteRequest,
  DropdownCommand,
  TagStatus,
} from "@/types/dataResource";

/**
 * 类型定义
 */
interface Tag extends DataResourceTag {}

interface TagForm {
  id: number | string;
  name: string;
  color: string;
  status: TagStatus;
  description: string;
}

interface TagUsage {
  id: number;
  resourceName: string;
  resourceType: string;
  categoryName?: string;
  created_at: string;
}

// 路由
const router = useRouter();

// 响应式数据
const tagFormRef = ref();
const uploadRef = ref();
const loading = ref(false);
const submitting = ref(false);
const importing = ref(false);
const tagDialogVisible = ref(false);
const usageDialogVisible = ref(false);
const importDialogVisible = ref(false);
const isEditMode = ref(false);
const viewMode = ref("table"); // table | card
const searchKeyword = ref("");
const filterStatus = ref("");
const sortBy = ref("created_at");
const currentPage = ref(1);
const pageSize = ref(20);
const totalCount = ref(0);
const selectedTags = ref([]);
const currentTag = ref<Tag | null>(null);
const importPreview = ref<TagCreateRequest[]>([]);

// 标签表单
const tagForm = reactive({
  id: "",
  name: "",
  color: "#409EFF",
  status: "active",
  description: "",
});

// 表单验证规则
const tagRules = {
  name: [
    { required: true, message: "请输入标签名称", trigger: "blur" },
    { min: 2, max: 20, message: "长度在 2 到 20 个字符", trigger: "blur" },
  ],
  color: [{ required: true, message: "请选择标签颜色", trigger: "change" }],
};

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
  "#FFD700",
  "#FF4500",
  "#9370DB",
  "#20B2AA",
];

// 标签数据
const tags = ref<Tag[]>([]);

// 标签使用详情数据
const tagUsageList = ref<TagUsage[]>([]);

// 注意：loading、totalCount、currentPage、pageSize 已在上面声明过了

/**
 * 计算属性
 */
const totalTags = computed(() => totalCount.value);
const activeTags = computed(
  () => tags.value.filter((tag) => tag.status === "active").length,
);
const disabledTags = computed(
  () => tags.value.filter((tag) => tag.status === "disabled").length,
);
const usedTags = computed(
  () => tags.value.filter((tag) => (tag.usage_count || 0) > 0).length,
);

const filteredTags = computed(() => {
  let result = [...tags.value];

  // 状态筛选
  if (filterStatus.value) {
    result = result.filter((tag) => tag.status === filterStatus.value);
  }

  // 关键词搜索
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase();
    result = result.filter(
      (tag) =>
        tag.name.toLowerCase().includes(keyword) ||
        tag.description.toLowerCase().includes(keyword),
    );
  }

  // 排序
  result.sort((a, b) => {
    switch (sortBy.value) {
      case "name":
        return a.name.localeCompare(b.name);
      case "usage_count":
        return b.usage_count - a.usage_count;
      default:
        return (
          new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
        );
    }
  });

  totalCount.value = result.length;

  // 分页
  const start = (currentPage.value - 1) * pageSize.value;
  const end = start + pageSize.value;
  return result.slice(start, end);
});

/**
 * 获取资源类型标签
 */
const getResourceTypeLabel = (type: string) => {
  const typeMap: Record<string, string> = {
    database: "数据库",
    api: "API",
    file: "文件",
    cache: "缓存",
  };
  return typeMap[type] || type;
};

/**
 * API调用方法
 */

/**
 * 获取标签列表
 */
const fetchTagList = async (): Promise<void> => {
  try {
    loading.value = true;
    const params: TagListQuery = {
      page: currentPage.value,
      page_size: pageSize.value,
      search: searchKeyword.value || undefined,
      status: filterStatus.value || undefined,
    };

    const response = await tagApi.getTagList(params);
    if (response.success) {
      tags.value = response.data.list || [];
      totalCount.value = response.data.total || 0;
    } else {
      ElMessage.error("获取标签列表失败");
    }
  } catch (error) {
    console.error("获取标签列表失败:", error);
    ElMessage.error("获取标签列表失败");
  } finally {
    loading.value = false;
  }
};

/**
 * 创建标签
 */
const createTag = async (data: TagCreateRequest): Promise<boolean> => {
  try {
    const response = await tagApi.createTag(data);
    if (response.success) {
      ElMessage.success("标签创建成功");
      await fetchTagList();
      return true;
    } else {
      ElMessage.error("标签创建失败");
      return false;
    }
  } catch (error) {
    console.error("创建标签失败:", error);
    ElMessage.error("创建标签失败");
    return false;
  }
};

/**
 * 更新标签
 */
const updateTag = async (
  id: number,
  data: TagUpdateRequest,
): Promise<boolean> => {
  try {
    const response = await tagApi.updateTag(id, data);
    if (response.success) {
      ElMessage.success("标签更新成功");
      await fetchTagList();
      return true;
    } else {
      ElMessage.error("标签更新失败");
      return false;
    }
  } catch (error) {
    console.error("更新标签失败:", error);
    ElMessage.error("更新标签失败");
    return false;
  }
};

/**
 * 删除单个标签
 */
const deleteTagById = async (id: number): Promise<boolean> => {
  try {
    const response = await tagApi.deleteTag(id);
    if (response.success) {
      ElMessage.success("标签删除成功");
      await fetchTagList();
      return true;
    } else {
      ElMessage.error("标签删除失败");
      return false;
    }
  } catch (error) {
    console.error("删除标签失败:", error);
    ElMessage.error("删除标签失败");
    return false;
  }
};

/**
 * 切换标签状态
 */
const toggleTagStatusById = async (id: number): Promise<boolean> => {
  try {
    const response = await tagApi.toggleTagStatus(id);
    if (response.success) {
      ElMessage.success("标签状态切换成功");
      await fetchTagList();
      return true;
    } else {
      ElMessage.error("标签状态切换失败");
      return false;
    }
  } catch (error) {
    console.error("切换标签状态失败:", error);
    ElMessage.error("切换标签状态切换失败");
    return false;
  }
};

/**
 * 批量删除标签
 */
const batchDeleteTagsByIds = async (ids: number[]): Promise<boolean> => {
  try {
    const response = await tagApi.batchDeleteTags(ids);
    if (response.success) {
      const { success_count, failed_count } = response.data;
      if (failed_count > 0) {
        ElMessage.warning(
          `删除完成，成功 ${success_count} 个，失败 ${failed_count} 个`,
        );
      } else {
        ElMessage.success(`成功删除 ${success_count} 个标签`);
      }
      await fetchTagList();
      return true;
    } else {
      ElMessage.error("批量删除失败");
      return false;
    }
  } catch (error) {
    console.error("批量删除标签失败:", error);
    ElMessage.error("批量删除标签失败");
    return false;
  }
};

/**
 * 获取标签使用统计
 */
const getTagUsageStats = async (id: number): Promise<TagUsageStats | null> => {
  try {
    const response = await tagApi.getTagUsageStats(id);
    if (response.success) {
      return response.data;
    } else {
      ElMessage.error("获取标签使用统计失败");
      return null;
    }
  } catch (error) {
    console.error("获取标签使用统计失败:", error);
    ElMessage.error("获取标签使用统计失败");
    return null;
  }
};

/**
 * 根据背景色获取文字颜色
 */
const getTextColor = (backgroundColor: string) => {
  // 简单的颜色对比度计算
  const color = backgroundColor.replace("#", "");
  const r = parseInt(color.substr(0, 2), 16);
  const g = parseInt(color.substr(2, 2), 16);
  const b = parseInt(color.substr(4, 2), 16);
  const brightness = (r * 299 + g * 587 + b * 114) / 1000;
  return brightness > 128 ? "#000000" : "#FFFFFF";
};

/**
 * 格式化日期
 */
const formatDate = (dateStr: string) => {
  if (!dateStr) return "-";
  return new Date(dateStr).toLocaleString("zh-CN");
};

/**
 * 切换视图模式
 */
const toggleView = (): void => {
  viewMode.value = viewMode.value === "table" ? "card" : "table";
};

/**
 * 处理筛选
 */
const handleFilter = async (): Promise<void> => {
  currentPage.value = 1;
  await fetchTagList();
};

/**
 * 处理排序
 */
const handleSort = async (): Promise<void> => {
  currentPage.value = 1;
  await fetchTagList();
};

/**
 * 处理搜索
 */
const handleSearch = async (): Promise<void> => {
  currentPage.value = 1;
  await fetchTagList();
};

/**
 * 刷新标签
 */
const refreshTags = async (): Promise<void> => {
  await fetchTagList();
  ElMessage.success("标签数据已刷新");
};

/**
 * 处理选择变化
 */
const handleSelectionChange = (selection: Tag[]): void => {
  selectedTags.value = selection;
};

/**
 * 切换标签选择（卡片视图）
 */
const toggleTagSelection = (tag: Tag): void => {
  const index = selectedTags.value.findIndex((item) => item.id === tag.id);
  if (index > -1) {
    selectedTags.value.splice(index, 1);
  } else {
    selectedTags.value.push(tag);
  }
};

/**
 * 处理分页大小变化
 */
const handleSizeChange = async (size: number): Promise<void> => {
  pageSize.value = size;
  currentPage.value = 1;
  await fetchTagList();
};

/**
 * 处理当前页变化
 */
const handleCurrentChange = async (page: number): Promise<void> => {
  currentPage.value = page;
  await fetchTagList();
};

/**
 * 显示创建对话框
 */
const showCreateDialog = (): void => {
  isEditMode.value = false;
  resetTagForm();
  tagDialogVisible.value = true;
};

/**
 * 显示编辑对话框
 */
const showEditDialog = (tag: Tag): void => {
  isEditMode.value = true;

  Object.assign(tagForm, {
    id: tag.id,
    name: tag.name,
    color: tag.color,
    status: tag.status,
    description: tag.description,
  });

  tagDialogVisible.value = true;
};

/**
 * 重置表单
 */
const resetTagForm = (): void => {
  Object.assign(tagForm, {
    id: "",
    name: "",
    color: "#409EFF",
    status: "active",
    description: "",
  });

  tagFormRef.value?.clearValidate();
};

/**
 * 提交表单
 */
const submitTagForm = (): void => {
  tagFormRef.value?.validate(async (valid: boolean) => {
    if (!valid) return;

    submitting.value = true;

    try {
      if (isEditMode.value) {
        // 更新标签
        const success = await updateTag(Number(tagForm.id), {
          name: tagForm.name,
          color: tagForm.color,
          description: tagForm.description,
        });
        if (success) {
          tagDialogVisible.value = false;
        }
      } else {
        // 创建新标签
        const success = await createTag({
          name: tagForm.name,
          color: tagForm.color,
          description: tagForm.description,
        });
        if (success) {
          tagDialogVisible.value = false;
        }
      }
    } finally {
      submitting.value = false;
    }
  });
};

/**
 * 处理标签命令（卡片视图）
 */
const handleTagCommand = (command: DropdownCommand): void => {
  const { action, data } = command;

  switch (action) {
    case "edit":
      showEditDialog(data);
      break;
    case "toggle":
      toggleTagStatus(data);
      break;
    case "delete":
      deleteTag(data);
      break;
  }
};

/**
 * 切换标签状态
 */
const toggleTagStatus = (tag: Tag): void => {
  const action = tag.status === "active" ? "禁用" : "启用";

  ElMessageBox.confirm(`确定要${action}标签 "${tag.name}" 吗？`, "确认操作", {
    confirmButtonText: "确定",
    cancelButtonText: "取消",
    type: "warning",
  })
    .then(async () => {
      await toggleTagStatusById(Number(tag.id));
    })
    .catch(() => {
      // 取消操作
    });
};

/**
 * 删除标签
 */
const deleteTag = (tag: Tag): void => {
  if ((tag.usage_count || 0) > 0) {
    ElMessage.warning("该标签正在被使用，无法删除");
    return;
  }

  ElMessageBox.confirm(
    `确定要删除标签 "${tag.name}" 吗？此操作不可恢复。`,
    "确认删除",
    {
      confirmButtonText: "确定删除",
      cancelButtonText: "取消",
      type: "error",
    },
  )
    .then(async () => {
      await deleteTagById(Number(tag.id));
    })
    .catch(() => {
      // 取消删除
    });
};

/**
 * 批量删除
 */
const batchDelete = (): void => {
  const canDeleteTags = selectedTags.value.filter(
    (tag) => (tag.usage_count || 0) === 0,
  );

  if (canDeleteTags.length === 0) {
    ElMessage.warning("所选标签都在使用中，无法删除");
    return;
  }

  if (canDeleteTags.length < selectedTags.value.length) {
    ElMessage.warning(`只能删除 ${canDeleteTags.length} 个未使用的标签`);
  }

  ElMessageBox.confirm(
    `确定要删除选中的 ${canDeleteTags.length} 个标签吗？此操作不可恢复。`,
    "确认批量删除",
    {
      confirmButtonText: "确定删除",
      cancelButtonText: "取消",
      type: "error",
    },
  )
    .then(async () => {
      const tagIds = canDeleteTags.map((tag) => Number(tag.id));
      const success = await batchDeleteTagsByIds(tagIds);
      if (success) {
        selectedTags.value = [];
      }
    })
    .catch(() => {
      // 取消删除
    });
};

/**
 * 导出标签
 */
const exportTags = (): void => {
  const exportData = tags.value.map((tag) => ({
    name: tag.name,
    color: tag.color,
    status: tag.status,
    description: tag.description,
    usage_count: tag.usage_count,
    created_at: tag.created_at,
  }));

  const blob = new Blob([JSON.stringify(exportData, null, 2)], {
    type: "application/json",
  });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `tags_export_${new Date().toISOString().split("T")[0]}.json`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);

  ElMessage.success("标签数据已导出");
};

/**
 * 导入标签
 */
const importTags = (): void => {
  importDialogVisible.value = true;
};

/**
 * 处理文件变化
 */
const handleFileChange = (file: any): void => {
  const reader = new FileReader();
  reader.onload = (e) => {
    try {
      const content = e.target?.result as string;
      let data: any[];

      if (file.name.endsWith(".json")) {
        data = JSON.parse(content);
      } else if (file.name.endsWith(".csv")) {
        // 简单的CSV解析
        const lines = content.split("\n");
        const headers = lines[0].split(",");
        data = lines
          .slice(1)
          .map((line) => {
            const values = line.split(",");
            const obj: any = {};
            headers.forEach((header, index) => {
              obj[header.trim()] = values[index]?.trim();
            });
            return obj;
          })
          .filter((item) => item.name);
      } else {
        throw new Error("不支持的文件格式");
      }

      importPreview.value = data.map((item) => ({
        name: item.name,
        color: item.color || "#409EFF",
        description: item.description || "",
        status: item.status === "disabled" ? "disabled" : "active",
      }));

      ElMessage.success(`成功解析 ${importPreview.value.length} 条标签数据`);
    } catch (error) {
      ElMessage.error("文件解析失败，请检查文件格式");
      importPreview.value = [];
    }
  };
  reader.readAsText(file.raw);
};

/**
 * 确认导入
 */
const confirmImport = (): void => {
  importing.value = true;

  setTimeout(() => {
    let successCount = 0;
    importPreview.value.forEach((item) => {
      if (item.name && !tags.value.some((tag) => tag.name === item.name)) {
        const newTag: Tag = {
          id: Date.now() + Math.random(),
          name: item.name,
          color: item.color || "#409EFF",
          status: item.status || "active",
          description: item.description || "",
          usage_count: 0,
          created_at: new Date().toISOString(),
        };
        tags.value.unshift(newTag);
        successCount++;
      }
    });

    importing.value = false;
    importDialogVisible.value = false;
    importPreview.value = [];

    ElMessage.success(`成功导入 ${successCount} 个标签`);
  }, 1500);
};

/**
 * 查看标签使用情况
 */
const viewTagUsage = async (tag: Tag): Promise<void> => {
  currentTag.value = tag;

  // 获取标签使用统计
  const stats = await getTagUsageStats(Number(tag.id));
  if (stats) {
    // 这里可以根据需要显示更详细的使用情况
    // 目前API只返回统计数据，如果需要详细的资源列表，需要后端提供相应的接口
    tagUsageList.value = [];
    ElMessage.info(`标签 "${tag.name}" 被 ${stats.resource_count} 个资源使用`);
  }

  usageDialogVisible.value = true;
};

/**
 * 查看资源
 */
const viewResource = (resource: TagUsage): void => {
  router.push({
    name: "ResourceDetail",
    params: { id: resource.id },
  });
};

/**
 * 组件挂载时初始化
 */
onMounted(async () => {
  // 初始化加载标签列表
  await fetchTagList();
});
</script>

<style lang="scss" scoped>
.tag-manage-container {
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

.stats-section {
  margin-bottom: 20px;

  .stats-card {
    .stats-content {
      display: flex;
      align-items: center;
      gap: 16px;

      .stats-icon {
        font-size: 32px;
      }

      .stats-info {
        .stats-number {
          font-size: 24px;
          font-weight: 600;
          color: var(--el-text-color-primary);
          line-height: 1;
        }

        .stats-label {
          font-size: 14px;
          color: var(--el-text-color-secondary);
          margin-top: 4px;
        }
      }
    }
  }
}

.tag-list-section {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .table-view {
    .tag-name-cell {
      display: flex;
      align-items: center;
    }

    .pagination-wrapper {
      margin-top: 20px;
      text-align: center;
    }
  }

  .card-view {
    .tag-cards {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
      gap: 16px;

      .tag-card {
        border: 1px solid var(--el-border-color-lighter);
        border-radius: 8px;
        padding: 16px;
        background: var(--el-bg-color);
        cursor: pointer;
        transition: all 0.2s;

        &:hover {
          border-color: var(--el-color-primary);
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }

        &.selected {
          border-color: var(--el-color-primary);
          background: var(--el-color-primary-light-9);
        }

        .tag-card-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 12px;
        }

        .tag-card-content {
          .tag-info {
            margin-bottom: 12px;

            .tag-category {
              margin-bottom: 8px;
            }

            .tag-description {
              font-size: 14px;
              color: var(--el-text-color-secondary);
              line-height: 1.4;
            }
          }

          .tag-stats {
            display: flex;
            justify-content: space-between;
            margin-bottom: 12px;

            .stat-item {
              display: flex;
              align-items: center;
              gap: 4px;
              font-size: 12px;

              .stat-label {
                color: var(--el-text-color-secondary);
              }

              .stat-value {
                font-weight: 600;
                color: var(--el-text-color-primary);
              }
            }
          }

          .tag-meta {
            .create-time {
              font-size: 12px;
              color: var(--el-text-color-placeholder);
            }
          }
        }
      }
    }

    .empty-cards {
      padding: 60px 0;
      text-align: center;
    }
  }
}

.color-selector {
  display: flex;
  align-items: center;
  gap: 16px;

  .color-preview {
    display: flex;
    align-items: center;
  }
}

.usage-content {
  .usage-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 20px;

    .usage-count {
      font-size: 14px;
      color: var(--el-text-color-secondary);
    }
  }
}

.import-content {
  .import-preview {
    margin-top: 20px;

    h4 {
      margin-bottom: 12px;
      color: var(--el-text-color-primary);
    }

    .more-tip {
      margin-top: 8px;
      font-size: 12px;
      color: var(--el-text-color-secondary);
      text-align: center;
    }
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
      flex-wrap: wrap;
    }
  }

  .stats-section {
    .el-col {
      margin-bottom: 16px;
    }
  }

  .tag-cards {
    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)) !important;
  }
}

@media (max-width: 768px) {
  .tag-manage-container {
    padding: 16px;
  }

  .action-bar {
    .left-actions,
    .right-actions {
      gap: 8px;
    }

    .el-input,
    .el-select {
      width: 100% !important;
    }
  }

  .stats-section {
    .el-col {
      span: 12 !important;
    }
  }

  .tag-cards {
    grid-template-columns: 1fr !important;
  }

  .table-view {
    .el-table {
      font-size: 12px;
    }
  }
}
</style>
