<template>
  <div class="sql-template-manager">
    <!-- 页面头部 -->
    <div class="page-header">
      <h2 class="page-title">
        <el-icon><Document /></el-icon>
        SQL查询模板管理
      </h2>
      <p class="page-description">管理和使用SQL查询模板，提高查询效率</p>
    </div>

    <!-- 搜索和筛选 -->
    <el-card class="filter-card">
      <el-row :gutter="20">
        <el-col :span="8">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索模板名称或描述"
            clearable
            @input="onSearchChange"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-col>
        <el-col :span="6">
          <el-select
            v-model="filterDatasourceId"
            placeholder="选择数据源"
            clearable
            filterable
            @change="onFilterChange"
          >
            <el-option
              v-for="ds in datasources"
              :key="ds.id"
              :label="ds.name"
              :value="ds.id"
            />
          </el-select>
        </el-col>
        <el-col :span="6">
          <el-select
            v-model="filterTags"
            placeholder="选择标签"
            multiple
            clearable
            filterable
            @change="onFilterChange"
          >
            <el-option
              v-for="tag in availableTags"
              :key="tag"
              :label="tag"
              :value="tag"
            />
          </el-select>
        </el-col>
        <el-col :span="4">
          <el-button type="primary" @click="loadTemplates">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </el-col>
      </el-row>
    </el-card>

    <!-- 模板列表 -->
    <el-card class="template-list-card">
      <template #header>
        <div class="card-header">
          <span>SQL查询模板 ({{ templates.length }} 个)</span>
          <div class="header-actions">
            <el-button @click="showCreateDialog">
              <el-icon><Plus /></el-icon>
              新建模板
            </el-button>
          </div>
        </div>
      </template>

      <div v-loading="loading" class="template-list">
        <div
          v-for="template in filteredTemplates"
          :key="template.id"
          class="template-item"
          :class="{ active: selectedTemplate?.id === template.id }"
          @click="selectTemplate(template)"
        >
          <div class="template-header">
            <div class="template-title">
              <h4>{{ template.name }}</h4>
              <el-tag
                :type="template.isTemplate ? 'success' : 'info'"
                size="small"
              >
                {{ template.isTemplate ? "模板" : "实例" }}
              </el-tag>
            </div>
            <div class="template-actions">
              <el-button
                size="small"
                type="primary"
                @click.stop="useTemplate(template)"
              >
                <el-icon><CaretRight /></el-icon>
                使用
              </el-button>
              <el-button size="small" @click.stop="editTemplate(template)">
                <el-icon><Edit /></el-icon>
                编辑
              </el-button>
              <el-button
                size="small"
                type="danger"
                @click.stop="deleteTemplate(template)"
              >
                <el-icon><Delete /></el-icon>
                删除
              </el-button>
            </div>
          </div>

          <div class="template-content">
            <p class="template-description">
              {{ template.description || "暂无描述" }}
            </p>
            <div class="template-meta">
              <div class="template-tags">
                <el-tag
                  v-for="tag in template.tags"
                  :key="tag"
                  size="small"
                  style="margin-right: 4px"
                >
                  {{ tag }}
                </el-tag>
              </div>
              <div class="template-info">
                <span class="created-by">创建者: {{ template.createdBy }}</span>
                <span class="created-at">{{
                  formatDate(template.createdAt)
                }}</span>
              </div>
            </div>
          </div>

          <!-- 查询预览 -->
          <div
            v-if="selectedTemplate?.id === template.id"
            class="template-query"
          >
            <div class="query-header">
              <span>SQL查询:</span>
              <el-button size="small" @click="copyQuery(template.query)">
                <el-icon><CopyDocument /></el-icon>
                复制
              </el-button>
            </div>
            <pre class="query-content">{{ template.query }}</pre>
          </div>
        </div>

        <div
          v-if="filteredTemplates.length === 0 && !loading"
          class="empty-state"
        >
          <el-empty description="暂无SQL查询模板" />
        </div>
      </div>
    </el-card>

    <!-- 创建/编辑模板对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEditing ? '编辑SQL查询模板' : '创建SQL查询模板'"
      width="800px"
      @close="resetForm"
    >
      <el-form
        ref="formRef"
        :model="templateForm"
        :rules="formRules"
        label-width="100px"
      >
        <el-form-item label="模板名称" prop="name">
          <el-input
            v-model="templateForm.name"
            placeholder="请输入模板名称"
            maxlength="50"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="描述" prop="description">
          <el-input
            v-model="templateForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入模板描述"
            maxlength="200"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="数据源" prop="datasourceId">
          <el-select
            v-model="templateForm.datasourceId"
            placeholder="请选择数据源"
            style="width: 100%"
            filterable
          >
            <el-option
              v-for="ds in datasources"
              :key="ds.id"
              :label="ds.name"
              :value="ds.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="SQL查询" prop="query">
          <el-input
            v-model="templateForm.query"
            type="textarea"
            :rows="10"
            placeholder="请输入SQL查询语句"
            class="sql-textarea"
          />
        </el-form-item>

        <el-form-item label="标签">
          <el-select
            v-model="templateForm.tags"
            multiple
            filterable
            allow-create
            placeholder="请选择或输入标签"
            style="width: 100%"
          >
            <el-option
              v-for="tag in availableTags"
              :key="tag"
              :label="tag"
              :value="tag"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="类型">
          <el-radio-group v-model="templateForm.isTemplate">
            <el-radio :label="true">查询模板</el-radio>
            <el-radio :label="false">查询实例</el-radio>
          </el-radio-group>
          <div class="type-hint">
            <el-text size="small" type="info">
              查询模板：可重复使用的查询结构；查询实例：具体的查询记录
            </el-text>
          </div>
        </el-form-item>
      </el-form>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="saving" @click="saveTemplate">
            {{ isEditing ? "更新" : "创建" }}
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 使用模板对话框 -->
    <el-dialog v-model="useDialogVisible" title="使用SQL查询模板" width="900px">
      <div v-if="currentTemplate" class="use-template-content">
        <div class="template-info">
          <h3>{{ currentTemplate.name }}</h3>
          <p>{{ currentTemplate.description }}</p>
        </div>

        <div class="query-editor">
          <div class="editor-header">
            <span>SQL查询:</span>
            <div class="editor-actions">
              <el-button size="small" @click="formatSQL">
                <el-icon><Tools /></el-icon>
                格式化
              </el-button>
              <el-button size="small" @click="copyQuery(editableQuery)">
                <el-icon><CopyDocument /></el-icon>
                复制
              </el-button>
            </div>
          </div>
          <el-input
            v-model="editableQuery"
            type="textarea"
            :rows="12"
            class="sql-textarea"
          />
        </div>

        <div v-if="queryParams.length > 0" class="query-params">
          <h4>查询参数:</h4>
          <el-row :gutter="20">
            <el-col v-for="param in queryParams" :key="param.name" :span="12">
              <el-form-item :label="param.name">
                <el-input
                  v-model="param.value"
                  :placeholder="param.placeholder"
                />
              </el-form-item>
            </el-col>
          </el-row>
        </div>
      </div>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="useDialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="executing" @click="executeQuery">
            <el-icon><CaretRight /></el-icon>
            执行查询
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import {
  Document,
  Search,
  Refresh,
  Plus,
  CaretRight,
  Edit,
  Delete,
  CopyDocument,
  Tools,
} from "@element-plus/icons-vue";
import {
  getSQLTemplates,
  saveSQLTemplate,
  updateSQLTemplate,
  deleteSQLTemplate,
  executeSQLQuery,
  type SQLTemplateResponse,
  type SQLTemplateRequest,
} from "@/api/sqlQuery";
import { getDatasources } from "@/api/datasource";

/**
 * 组件属性定义
 */
interface Props {
  /** 初始数据源ID */
  initialDatasourceId?: number;
  /** 初始数据资源ID */
  initialDataResourceId?: number;
}

/**
 * 组件事件定义
 */
interface Emits {
  /** 执行查询事件 */
  (e: "execute-query", query: string, datasourceId: number): void;
  /** 模板选择事件 */
  (e: "template-selected", template: SQLTemplateResponse): void;
}

const props = withDefaults(defineProps<Props>(), {
  initialDatasourceId: 0,
  initialDataResourceId: 0,
});

const emit = defineEmits<Emits>();

// 响应式数据
const loading = ref(false);
const saving = ref(false);
const executing = ref(false);
const dialogVisible = ref(false);
const useDialogVisible = ref(false);
const isEditing = ref(false);

// 模板数据
const templates = ref<SQLTemplateResponse[]>([]);
const selectedTemplate = ref<SQLTemplateResponse | null>(null);
const currentTemplate = ref<SQLTemplateResponse | null>(null);
const datasources = ref<any[]>([]);

// 搜索和筛选
const searchKeyword = ref("");
const filterDatasourceId = ref<number | undefined>();
const filterTags = ref<string[]>([]);
const availableTags = ref<string[]>([
  "常用查询",
  "报表查询",
  "数据分析",
  "业务查询",
  "统计查询",
]);

// 表单数据
const formRef = ref();
const templateForm = reactive<SQLTemplateRequest>({
  name: "",
  description: "",
  datasourceId: 0,
  query: "",
  tags: [],
  isTemplate: true,
});

// 使用模板相关
const editableQuery = ref("");
const queryParams = ref<
  Array<{
    name: string;
    value: string;
    placeholder: string;
  }>
>([]);

// 表单验证规则
const formRules = {
  name: [
    { required: true, message: "请输入模板名称", trigger: "blur" },
    { min: 2, max: 50, message: "长度在 2 到 50 个字符", trigger: "blur" },
  ],
  datasourceId: [
    { required: true, message: "请选择数据源", trigger: "change" },
  ],
  query: [{ required: true, message: "请输入SQL查询语句", trigger: "blur" }],
};

/**
 * 过滤后的模板列表
 */
const filteredTemplates = computed(() => {
  let result = templates.value;

  // 关键词搜索
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase();
    result = result.filter(
      (template) =>
        template.name.toLowerCase().includes(keyword) ||
        template.description.toLowerCase().includes(keyword),
    );
  }

  // 数据源筛选
  if (filterDatasourceId.value) {
    result = result.filter(
      (template) => template.datasourceId === filterDatasourceId.value,
    );
  }

  // 标签筛选
  if (filterTags.value.length > 0) {
    result = result.filter((template) =>
      filterTags.value.some((tag) => template.tags.includes(tag)),
    );
  }

  return result;
});

/**
 * 加载模板列表
 */
const loadTemplates = async () => {
  // 如果没有数据资源ID，不加载模板
  if (!props.initialDataResourceId) {
    templates.value = [];
    return;
  }

  loading.value = true;
  try {
    const response = await getSQLTemplates({
      dataResourceId: props.initialDataResourceId,
      tags: filterTags.value.length > 0 ? filterTags.value : undefined,
      search: searchKeyword.value || undefined,
    });
    templates.value = response.data || [];

    // 收集所有标签
    const allTags = new Set<string>();
    templates.value.forEach((template) => {
      template.tags.forEach((tag) => allTags.add(tag));
    });
    availableTags.value = [...new Set([...availableTags.value, ...allTags])];
  } catch (error) {
    console.error("加载模板列表失败:", error);
    ElMessage.error("加载模板列表失败");
  } finally {
    loading.value = false;
  }
};

/**
 * 加载数据源列表
 */
const loadDatasources = async () => {
  try {
    const response = await getDatasources();
    datasources.value = response.data || [];
  } catch (error) {
    console.error("加载数据源失败:", error);
    ElMessage.error("加载数据源失败");
  }
};

/**
 * 搜索变化处理
 */
const onSearchChange = () => {
  // 防抖处理可以在这里添加
};

/**
 * 筛选变化处理
 */
const onFilterChange = () => {
  loadTemplates();
};

/**
 * 选择模板
 */
const selectTemplate = (template: SQLTemplateResponse) => {
  selectedTemplate.value =
    selectedTemplate.value?.id === template.id ? null : template;
  emit("template-selected", template);
};

/**
 * 显示创建对话框
 */
const showCreateDialog = () => {
  isEditing.value = false;
  resetForm();
  dialogVisible.value = true;
};

/**
 * 编辑模板
 */
const editTemplate = (template: SQLTemplateResponse) => {
  isEditing.value = true;
  Object.assign(templateForm, {
    name: template.name,
    description: template.description,
    datasourceId: template.datasourceId,
    query: template.query,
    tags: [...template.tags],
    isTemplate: template.isTemplate,
  });
  currentTemplate.value = template;
  dialogVisible.value = true;
};

/**
 * 使用模板
 */
const useTemplate = (template: SQLTemplateResponse) => {
  currentTemplate.value = template;
  editableQuery.value = template.query;

  // 解析查询参数（简单的参数解析，查找 :param 格式的参数）
  const paramMatches = template.query.match(/:([a-zA-Z_][a-zA-Z0-9_]*)/g);
  if (paramMatches) {
    queryParams.value = paramMatches.map((match) => ({
      name: match.substring(1),
      value: "",
      placeholder: `请输入${match.substring(1)}的值`,
    }));
  } else {
    queryParams.value = [];
  }

  useDialogVisible.value = true;
};

/**
 * 删除模板
 */
const deleteTemplate = async (template: SQLTemplateResponse) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除模板 "${template.name}" 吗？`,
      "确认删除",
      {
        confirmButtonText: "确定",
        cancelButtonText: "取消",
        type: "warning",
      },
    );

    await deleteSQLTemplate(template.id);
    ElMessage.success("模板删除成功");
    await loadTemplates();
  } catch (error) {
    if (error !== "cancel") {
      console.error("删除模板失败:", error);
      ElMessage.error("删除模板失败");
    }
  }
};

/**
 * 保存模板
 */
const saveTemplate = async () => {
  if (!formRef.value) return;

  try {
    await formRef.value.validate();
    saving.value = true;

    if (isEditing.value && currentTemplate.value) {
      await updateSQLTemplate(currentTemplate.value.id, templateForm);
      ElMessage.success("模板更新成功");
    } else {
      await saveSQLTemplate(templateForm);
      ElMessage.success("模板创建成功");
    }

    dialogVisible.value = false;
    await loadTemplates();
  } catch (error) {
    console.error("保存模板失败:", error);
    ElMessage.error("保存模板失败");
  } finally {
    saving.value = false;
  }
};

/**
 * 执行查询
 */
const executeQuery = async () => {
  if (!currentTemplate.value) return;

  let finalQuery = editableQuery.value;

  // 替换查询参数
  queryParams.value.forEach((param) => {
    if (param.value) {
      finalQuery = finalQuery.replace(
        new RegExp(`:${param.name}`, "g"),
        param.value,
      );
    }
  });

  executing.value = true;
  try {
    emit("execute-query", finalQuery, currentTemplate.value.datasourceId);
    useDialogVisible.value = false;
    ElMessage.success("查询已提交执行");
  } catch (error) {
    console.error("执行查询失败:", error);
    ElMessage.error("执行查询失败");
  } finally {
    executing.value = false;
  }
};

/**
 * 重置表单
 */
const resetForm = () => {
  Object.assign(templateForm, {
    name: "",
    description: "",
    datasourceId: props.initialDatasourceId || 0,
    query: "",
    tags: [],
    isTemplate: true,
  });
  currentTemplate.value = null;
  if (formRef.value) {
    formRef.value.clearValidate();
  }
};

/**
 * 复制查询
 */
const copyQuery = async (query: string) => {
  try {
    await navigator.clipboard.writeText(query);
    ElMessage.success("SQL已复制到剪贴板");
  } catch (error) {
    ElMessage.error("复制失败");
  }
};

/**
 * 格式化SQL
 */
const formatSQL = () => {
  // 简单的SQL格式化
  editableQuery.value = editableQuery.value
    .replace(/\s+/g, " ")
    .replace(/\s*,\s*/g, ",\n  ")
    .replace(/\s+(FROM|WHERE|GROUP BY|ORDER BY|HAVING|LIMIT)\s+/gi, "\n$1 ")
    .replace(/\s+(AND|OR)\s+/gi, "\n  $1 ")
    .trim();
};

/**
 * 格式化日期
 */
const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleString("zh-CN");
};

// 监听初始数据源ID变化
watch(
  () => props.initialDatasourceId,
  (newVal) => {
    if (newVal) {
      filterDatasourceId.value = newVal;
    }
  },
  { immediate: true },
);

// 监听初始数据资源ID变化
watch(
  () => props.initialDataResourceId,
  (newVal) => {
    if (newVal) {
      loadTemplates();
    }
  },
  { immediate: true },
);

/**
 * 组件挂载时初始化
 */
onMounted(async () => {
  await loadDatasources();

  // 如果传入了初始数据源ID，设置为筛选条件
  if (props.initialDatasourceId) {
    filterDatasourceId.value = props.initialDatasourceId;
  }

  // 模板加载现在通过watch监听器处理
});
</script>

<style scoped>
.sql-template-manager {
  padding: 20px;
}

.page-header {
  margin-bottom: 24px;
}

.page-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 8px 0;
  font-size: 24px;
  font-weight: 600;
  color: #303133;
}

.page-description {
  margin: 0;
  color: #606266;
  font-size: 14px;
}

.filter-card {
  margin-bottom: 20px;
}

.template-list-card {
  min-height: 500px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.template-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.template-item {
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.2s;
}

.template-item:hover {
  border-color: #409eff;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.1);
}

.template-item.active {
  border-color: #409eff;
  background-color: #f0f9ff;
}

.template-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.template-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.template-title h4 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.template-actions {
  display: flex;
  gap: 8px;
}

.template-content {
  margin-bottom: 12px;
}

.template-description {
  margin: 0 0 12px 0;
  color: #606266;
  font-size: 14px;
  line-height: 1.5;
}

.template-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.template-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.template-info {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: #909399;
}

.template-query {
  margin-top: 16px;
  border-top: 1px solid #ebeef5;
  padding-top: 16px;
}

.query-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.query-content {
  background-color: #f8f9fa;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  padding: 12px;
  font-family: "Courier New", monospace;
  font-size: 13px;
  line-height: 1.5;
  color: #303133;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 200px;
  overflow-y: auto;
}

.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 200px;
}

.sql-textarea {
  font-family: "Courier New", monospace;
}

.type-hint {
  margin-top: 8px;
}

.use-template-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.template-info h3 {
  margin: 0 0 8px 0;
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.template-info p {
  margin: 0;
  color: #606266;
  font-size: 14px;
}

.query-editor {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.editor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.editor-actions {
  display: flex;
  gap: 8px;
}

.query-params h4 {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
</style>
