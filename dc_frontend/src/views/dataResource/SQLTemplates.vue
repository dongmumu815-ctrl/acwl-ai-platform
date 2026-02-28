<template>
  <div class="sql-templates-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-section">
          <h1 class="page-title">
            <el-icon><Document /></el-icon>
            SQL查询模板
          </h1>
          <p class="page-description">
            管理和使用SQL查询模板，提高数据查询效率
          </p>
        </div>
        <div class="header-actions">
          <el-button type="primary" @click="showCreateDialog">
            <el-icon><Plus /></el-icon>
            新建模板
          </el-button>
        </div>
      </div>
    </div>

    <!-- 主要内容区域 -->
    <div class="page-content">
      <el-row :gutter="20">
        <!-- 左侧：模板管理 -->
        <el-col :span="16">
          <SQLTemplateManager
            ref="templateManagerRef"
            :initial-datasource-id="selectedDatasourceId"
            @execute-query="onExecuteQuery"
            @template-selected="onTemplateSelected"
          />
        </el-col>

        <!-- 右侧：查询执行和结果 -->
        <el-col :span="8">
          <!-- 查询执行面板 -->
          <el-card v-if="selectedTemplate" class="query-panel">
            <template #header>
              <div class="panel-header">
                <span>查询执行</span>
                <el-button size="small" @click="clearSelection">
                  <el-icon><Close /></el-icon>
                  清空
                </el-button>
              </div>
            </template>

            <div class="selected-template">
              <h4>{{ selectedTemplate.name }}</h4>
              <p class="template-desc">{{ selectedTemplate.description }}</p>

              <div class="template-meta">
                <div class="meta-item">
                  <span class="label">数据源:</span>
                  <span class="value">{{
                    getDatasourceName(selectedTemplate.datasourceId)
                  }}</span>
                </div>
                <div class="meta-item">
                  <span class="label">类型:</span>
                  <el-tag
                    :type="selectedTemplate.isTemplate ? 'success' : 'info'"
                    size="small"
                  >
                    {{ selectedTemplate.isTemplate ? "模板" : "实例" }}
                  </el-tag>
                </div>
                <div class="meta-item">
                  <span class="label">标签:</span>
                  <div class="tags">
                    <el-tag
                      v-for="tag in selectedTemplate.tags"
                      :key="tag"
                      size="small"
                      style="margin-right: 4px"
                    >
                      {{ tag }}
                    </el-tag>
                  </div>
                </div>
              </div>

              <div class="query-preview">
                <div class="preview-header">
                  <span>SQL预览:</span>
                  <el-button size="small" @click="copyQuery">
                    <el-icon><CopyDocument /></el-icon>
                    复制
                  </el-button>
                </div>
                <pre class="query-content">{{ selectedTemplate.query }}</pre>
              </div>

              <div class="action-buttons">
                <el-button
                  type="primary"
                  :loading="executing"
                  @click="executeTemplate"
                >
                  <el-icon><CaretRight /></el-icon>
                  执行查询
                </el-button>
                <el-button @click="editTemplate">
                  <el-icon><Edit /></el-icon>
                  编辑模板
                </el-button>
              </div>
            </div>
          </el-card>

          <!-- 查询结果面板 -->
          <el-card
            v-if="queryResults.length > 0 || executing"
            class="results-panel"
          >
            <template #header>
              <div class="panel-header">
                <span>查询结果 ({{ queryResults.length }} 条)</span>
                <div class="result-actions">
                  <el-button
                    size="small"
                    :disabled="queryResults.length === 0"
                    @click="exportResults"
                  >
                    <el-icon><Download /></el-icon>
                    导出
                  </el-button>
                  <el-button
                    size="small"
                    :loading="executing"
                    @click="refreshQuery"
                  >
                    <el-icon><Refresh /></el-icon>
                    刷新
                  </el-button>
                </div>
              </div>
            </template>

            <div v-loading="executing" class="results-content">
              <el-table
                v-if="queryResults.length > 0"
                :data="queryResults"
                stripe
                border
                style="width: 100%"
                max-height="400"
              >
                <el-table-column
                  v-for="column in resultColumns"
                  :key="column.prop"
                  :prop="column.prop"
                  :label="column.label"
                  :width="column.width"
                  show-overflow-tooltip
                >
                  <template #default="{ row }">
                    <span v-if="column.type === 'date'">
                      {{ formatDate(row[column.prop]) }}
                    </span>
                    <span v-else-if="column.type === 'number'">
                      {{ formatNumber(row[column.prop]) }}
                    </span>
                    <span v-else>
                      {{ row[column.prop] }}
                    </span>
                  </template>
                </el-table-column>
              </el-table>

              <div
                v-if="queryResults.length === 0 && !executing"
                class="empty-results"
              >
                <el-empty description="暂无查询结果" />
              </div>
            </div>
          </el-card>

          <!-- 快速操作面板 -->
          <el-card v-if="!selectedTemplate" class="quick-actions">
            <template #header>
              <span>快速操作</span>
            </template>

            <div class="actions-grid">
              <div class="action-item" @click="showCreateDialog">
                <el-icon><Plus /></el-icon>
                <span>新建模板</span>
              </div>
              <div class="action-item" @click="importTemplate">
                <el-icon><Upload /></el-icon>
                <span>导入模板</span>
              </div>
              <div class="action-item" @click="showHelp">
                <el-icon><QuestionFilled /></el-icon>
                <span>使用帮助</span>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 创建/编辑模板对话框 -->
    <el-dialog
      v-model="createDialogVisible"
      :title="isEditing ? '编辑SQL查询模板' : '创建SQL查询模板'"
      width="900px"
      @close="resetCreateForm"
    >
      <el-form
        ref="createFormRef"
        :model="createForm"
        :rules="createFormRules"
        label-width="100px"
      >
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="模板名称" prop="name">
              <el-input
                v-model="createForm.name"
                placeholder="请输入模板名称"
                maxlength="50"
                show-word-limit
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="数据源" prop="datasourceId">
              <el-select
                v-model="createForm.datasourceId"
                placeholder="请选择数据源"
                style="width: 100%"
              >
                <el-option
                  v-for="ds in datasources"
                  :key="ds.id"
                  :label="ds.name"
                  :value="ds.id"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="描述">
          <el-input
            v-model="createForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入模板描述"
            maxlength="200"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="SQL查询" prop="query">
          <div class="sql-editor">
            <div class="editor-toolbar">
              <el-button size="small" @click="formatSQL">
                <el-icon><MagicStick /></el-icon>
                格式化
              </el-button>
              <el-button size="small" @click="validateSQL">
                <el-icon><Check /></el-icon>
                验证语法
              </el-button>
              <el-button size="small" @click="insertTemplate">
                <el-icon><DocumentAdd /></el-icon>
                插入模板
              </el-button>
            </div>
            <el-input
              v-model="createForm.query"
              type="textarea"
              :rows="12"
              placeholder="请输入SQL查询语句"
              class="sql-textarea"
            />
          </div>
        </el-form-item>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="标签">
              <el-select
                v-model="createForm.tags"
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
          </el-col>
          <el-col :span="12">
            <el-form-item label="类型">
              <el-radio-group v-model="createForm.isTemplate">
                <el-radio :label="true">查询模板</el-radio>
                <el-radio :label="false">查询实例</el-radio>
              </el-radio-group>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="createDialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="saving" @click="saveTemplate">
            {{ isEditing ? "更新" : "创建" }}
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 帮助对话框 -->
    <el-dialog
      v-model="helpDialogVisible"
      title="SQL查询模板使用帮助"
      width="700px"
    >
      <div class="help-content">
        <h3>功能介绍</h3>
        <p>
          SQL查询模板功能帮助您管理和重复使用常用的SQL查询语句，提高数据查询效率。
        </p>

        <h3>主要功能</h3>
        <ul>
          <li><strong>模板管理：</strong>创建、编辑、删除SQL查询模板</li>
          <li><strong>模板使用：</strong>快速加载和执行已保存的查询模板</li>
          <li>
            <strong>参数化查询：</strong>支持使用参数占位符，如 :param_name
          </li>
          <li><strong>标签分类：</strong>使用标签对模板进行分类管理</li>
          <li><strong>搜索筛选：</strong>快速查找所需的查询模板</li>
        </ul>

        <h3>使用技巧</h3>
        <ul>
          <li>使用有意义的模板名称和描述，便于后续查找</li>
          <li>合理使用标签对模板进行分类</li>
          <li>对于需要动态参数的查询，使用 :参数名 格式</li>
          <li>定期整理和更新模板，删除不再使用的模板</li>
        </ul>

        <h3>参数化查询示例</h3>
        <pre class="code-example">
SELECT * FROM users 
WHERE created_at &gt;= :start_date 
  AND created_at &lt;= :end_date 
  AND status = :status</pre
        >
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import {
  Document,
  Plus,
  Close,
  CopyDocument,
  CaretRight,
  Edit,
  Download,
  Refresh,
  Upload,
  QuestionFilled,
  MagicStick,
  Check,
  DocumentAdd,
} from "@element-plus/icons-vue";
import SQLTemplateManager from "@/components/SQLTemplateManager.vue";
import {
  saveSQLTemplate,
  updateSQLTemplate,
  executeSQLQuery,
  type SQLTemplateResponse,
  type SQLTemplateRequest,
} from "@/api/sqlQuery";
import { getDatasources } from "@/api/datasource";

// 响应式数据
const templateManagerRef = ref();
const createFormRef = ref();
const createDialogVisible = ref(false);
const helpDialogVisible = ref(false);
const isEditing = ref(false);
const saving = ref(false);
const executing = ref(false);

// 选中的模板和查询结果
const selectedTemplate = ref<SQLTemplateResponse | null>(null);
const selectedDatasourceId = ref<number>(0);
const queryResults = ref<any[]>([]);
const resultColumns = ref<any[]>([]);
const datasources = ref<any[]>([]);

// 创建表单
const createForm = reactive<SQLTemplateRequest>({
  name: "",
  description: "",
  datasourceId: 0,
  query: "",
  tags: [],
  isTemplate: true,
});

// 可用标签
const availableTags = ref<string[]>([
  "常用查询",
  "报表查询",
  "数据分析",
  "业务查询",
  "统计查询",
  "用户数据",
  "订单数据",
  "日志分析",
  "性能监控",
  "数据清洗",
]);

// 表单验证规则
const createFormRules = {
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
 * 获取数据源名称
 */
const getDatasourceName = (datasourceId: number) => {
  const datasource = datasources.value.find((ds) => ds.id === datasourceId);
  return datasource ? datasource.name : "未知数据源";
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
 * 模板选择事件处理
 */
const onTemplateSelected = (template: SQLTemplateResponse) => {
  selectedTemplate.value = template;
  // 清空之前的查询结果
  queryResults.value = [];
  resultColumns.value = [];
};

/**
 * 执行查询事件处理
 */
const onExecuteQuery = async (query: string, datasourceId: number) => {
  executing.value = true;
  try {
    const response = await executeSQLQuery({
      datasourceId,
      query,
      limit: 1000,
    });

    // 处理查询结果
    const { columns, data } = response.data;
    resultColumns.value = columns.map((col) => ({
      prop: col.name,
      label: col.name,
      type: col.type,
      width: 150,
    }));

    // 转换数据格式
    queryResults.value = data.map((row) => {
      const obj: any = {};
      columns.forEach((col, index) => {
        obj[col.name] = row[index];
      });
      return obj;
    });

    ElMessage.success(`查询执行成功，返回 ${queryResults.value.length} 条记录`);
  } catch (error) {
    console.error("执行查询失败:", error);
    ElMessage.error("执行查询失败");
  } finally {
    executing.value = false;
  }
};

/**
 * 清空选择
 */
const clearSelection = () => {
  selectedTemplate.value = null;
  queryResults.value = [];
  resultColumns.value = [];
};

/**
 * 复制查询
 */
const copyQuery = async () => {
  if (!selectedTemplate.value) return;

  try {
    await navigator.clipboard.writeText(selectedTemplate.value.query);
    ElMessage.success("SQL已复制到剪贴板");
  } catch (error) {
    ElMessage.error("复制失败");
  }
};

/**
 * 执行模板
 */
const executeTemplate = () => {
  if (!selectedTemplate.value) return;
  onExecuteQuery(
    selectedTemplate.value.query,
    selectedTemplate.value.datasourceId,
  );
};

/**
 * 编辑模板
 */
const editTemplate = () => {
  if (!selectedTemplate.value) return;

  isEditing.value = true;
  Object.assign(createForm, {
    name: selectedTemplate.value.name,
    description: selectedTemplate.value.description,
    datasourceId: selectedTemplate.value.datasourceId,
    query: selectedTemplate.value.query,
    tags: [...selectedTemplate.value.tags],
    isTemplate: selectedTemplate.value.isTemplate,
  });
  createDialogVisible.value = true;
};

/**
 * 显示创建对话框
 */
const showCreateDialog = () => {
  isEditing.value = false;
  resetCreateForm();
  createDialogVisible.value = true;
};

/**
 * 保存模板
 */
const saveTemplate = async () => {
  if (!createFormRef.value) return;

  try {
    await createFormRef.value.validate();
    saving.value = true;

    if (isEditing.value && selectedTemplate.value) {
      await updateSQLTemplate(selectedTemplate.value.id, createForm);
      ElMessage.success("模板更新成功");
    } else {
      await saveSQLTemplate(createForm);
      ElMessage.success("模板创建成功");
    }

    createDialogVisible.value = false;

    // 刷新模板列表
    if (templateManagerRef.value) {
      templateManagerRef.value.loadTemplates();
    }
  } catch (error) {
    console.error("保存模板失败:", error);
    ElMessage.error("保存模板失败");
  } finally {
    saving.value = false;
  }
};

/**
 * 重置创建表单
 */
const resetCreateForm = () => {
  Object.assign(createForm, {
    name: "",
    description: "",
    datasourceId: 0,
    query: "",
    tags: [],
    isTemplate: true,
  });
  if (createFormRef.value) {
    createFormRef.value.clearValidate();
  }
};

/**
 * 导出结果
 */
const exportResults = () => {
  if (queryResults.value.length === 0) {
    ElMessage.warning("没有可导出的数据");
    return;
  }

  // 这里可以实现导出功能
  ElMessage.info("导出功能开发中...");
};

/**
 * 刷新查询
 */
const refreshQuery = () => {
  if (selectedTemplate.value) {
    executeTemplate();
  }
};

/**
 * 导入模板
 */
const importTemplate = () => {
  ElMessage.info("导入功能开发中...");
};

/**
 * 显示帮助
 */
const showHelp = () => {
  helpDialogVisible.value = true;
};

/**
 * 格式化SQL
 */
const formatSQL = () => {
  createForm.query = createForm.query
    .replace(/\s+/g, " ")
    .replace(/\s*,\s*/g, ",\n  ")
    .replace(/\s+(FROM|WHERE|GROUP BY|ORDER BY|HAVING|LIMIT)\s+/gi, "\n$1 ")
    .replace(/\s+(AND|OR)\s+/gi, "\n  $1 ")
    .trim();
};

/**
 * 验证SQL语法
 */
const validateSQL = () => {
  // 简单的SQL语法验证
  const sql = createForm.query.trim().toUpperCase();
  if (!sql) {
    ElMessage.warning("请输入SQL语句");
    return;
  }

  if (!sql.startsWith("SELECT") && !sql.startsWith("WITH")) {
    ElMessage.warning("目前只支持SELECT查询语句");
    return;
  }

  ElMessage.success("SQL语法验证通过");
};

/**
 * 插入模板
 */
const insertTemplate = () => {
  const templates = [
    "SELECT * FROM table_name WHERE condition",
    "SELECT COUNT(*) FROM table_name",
    "SELECT column1, column2 FROM table_name ORDER BY column1",
    "SELECT * FROM table_name WHERE date_column >= :start_date AND date_column <= :end_date",
  ];

  ElMessageBox.prompt("选择要插入的SQL模板", "插入模板", {
    confirmButtonText: "插入",
    cancelButtonText: "取消",
    inputType: "textarea",
    inputValue: templates[0],
    inputPlaceholder: "选择或输入SQL模板",
  })
    .then(({ value }) => {
      if (value) {
        createForm.query = value;
      }
    })
    .catch(() => {});
};

/**
 * 格式化日期
 */
const formatDate = (dateString: string) => {
  if (!dateString) return "";
  return new Date(dateString).toLocaleString("zh-CN");
};

/**
 * 格式化数字
 */
const formatNumber = (value: any) => {
  if (value === null || value === undefined) return "";
  if (typeof value === "number") {
    return value.toLocaleString();
  }
  return value;
};

/**
 * 组件挂载时初始化
 */
onMounted(async () => {
  await loadDatasources();
});
</script>

<style scoped>
.sql-templates-page {
  padding: 20px;
  background-color: #f5f7fa;
  min-height: calc(100vh - 60px);
}

.page-header {
  margin-bottom: 24px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  background: white;
  padding: 24px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.title-section {
  flex: 1;
}

.page-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 8px 0;
  font-size: 28px;
  font-weight: 600;
  color: #303133;
}

.page-description {
  margin: 0;
  color: #606266;
  font-size: 16px;
  line-height: 1.5;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.page-content {
  min-height: 600px;
}

.query-panel,
.results-panel,
.quick-actions {
  margin-bottom: 20px;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.result-actions {
  display: flex;
  gap: 8px;
}

.selected-template {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.selected-template h4 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.template-desc {
  margin: 0;
  color: #606266;
  font-size: 14px;
  line-height: 1.5;
}

.template-meta {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.meta-item .label {
  font-weight: 600;
  color: #303133;
  min-width: 60px;
}

.meta-item .value {
  color: #606266;
}

.tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.query-preview {
  border: 1px solid #ebeef5;
  border-radius: 4px;
  overflow: hidden;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background-color: #f8f9fa;
  border-bottom: 1px solid #ebeef5;
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.query-content {
  padding: 12px;
  margin: 0;
  font-family: "Courier New", monospace;
  font-size: 13px;
  line-height: 1.5;
  color: #303133;
  background-color: #fafafa;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 200px;
  overflow-y: auto;
}

.action-buttons {
  display: flex;
  gap: 8px;
}

.results-content {
  min-height: 200px;
}

.empty-results {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 200px;
}

.actions-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 12px;
}

.action-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 16px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
  color: #606266;
}

.action-item:hover {
  border-color: #409eff;
  color: #409eff;
  background-color: #f0f9ff;
}

.sql-editor {
  border: 1px solid #ebeef5;
  border-radius: 4px;
  overflow: hidden;
}

.editor-toolbar {
  display: flex;
  gap: 8px;
  padding: 8px 12px;
  background-color: #f8f9fa;
  border-bottom: 1px solid #ebeef5;
}

.sql-textarea {
  font-family: "Courier New", monospace;
  border: none;
}

.sql-textarea :deep(.el-textarea__inner) {
  border: none;
  border-radius: 0;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.help-content {
  line-height: 1.6;
}

.help-content h3 {
  margin: 20px 0 10px 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.help-content h3:first-child {
  margin-top: 0;
}

.help-content ul {
  margin: 10px 0;
  padding-left: 20px;
}

.help-content li {
  margin: 8px 0;
}

.code-example {
  background-color: #f8f9fa;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  padding: 12px;
  font-family: "Courier New", monospace;
  font-size: 13px;
  line-height: 1.5;
  color: #303133;
  margin: 10px 0;
}
</style>
