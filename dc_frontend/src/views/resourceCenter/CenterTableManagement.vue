<template>
  <div class="center-table-management">
    <!-- 页面头部 -->
    <div class="page-header">
      <!-- <h2>中心表管理</h2> -->
      <!-- <p class="page-description">数据源: 10.20.1.201 | 模式: cepiec-warehouse | 表: cpc_dw_publication</p> -->
    </div>

    <!-- 主要内容：左右两栏布局 -->
    <div class="content-wrapper">
      <div
        class="two-column-layout"
        :class="{ 'is-collapsed': isLeftCollapsed }"
      >
        <!-- 左侧：中心表结构 -->
        <el-card
          v-loading="tableDetailLoading"
          class="main-card left-col"
          :class="{ 'collapsed-card': isLeftCollapsed }"
          element-loading-text="加载表结构..."
          element-loading-background="rgba(255,255,255,0.7)"
        >
          <template v-if="!isLeftCollapsed" #header>
            <div class="card-header">
              <span>中心表结构详情</span>
              <div class="header-actions">
                <el-button
                  link
                  title="折叠面板"
                  @click="isLeftCollapsed = true"
                >
                  <el-icon><Fold /></el-icon>
                </el-button>
                <el-button
                  :loading="tableDetailLoading"
                  size="small"
                  @click="loadTableDetail"
                >
                  <el-icon><Refresh /></el-icon>
                  刷新数据
                </el-button>
                <el-button
                  size="small"
                  type="primary"
                  @click="showAddFieldDialog"
                >
                  <el-icon><Plus /></el-icon>
                  新增字段
                </el-button>
                <!--  <el-button type="primary" @click="loadTableData" :loading="tableDataLoading">
                <el-icon><Search /></el-icon>
                查看数据
              </el-button> -->
              </div>
            </div>
          </template>

          <!-- 折叠后的显示内容 -->
          <div
            v-if="isLeftCollapsed"
            class="collapsed-view"
            title="点击展开"
            @click="isLeftCollapsed = false"
          >
            <div class="collapsed-content">
              <el-icon size="16"><Expand /></el-icon>
              <span class="vertical-text">中心表结构详情</span>
            </div>
          </div>

          <div v-else>
            <!-- 表基本信息 -->
            <!-- <div v-if="tableDetail" class="table-info-section" style="margin-bottom: 20px;">
          <el-descriptions :column="3" border>
            <el-descriptions-item label="表名称">{{ tableDetail.table_name }}</el-descriptions-item>
            <el-descriptions-item label="表类型">{{ tableDetail.table_type }}</el-descriptions-item>
            <el-descriptions-item label="行数">{{ tableDetail.row_count || 'N/A' }}</el-descriptions-item>
            <el-descriptions-item label="表注释" :span="3">{{ tableDetail.table_comment || '无注释' }}</el-descriptions-item>
          </el-descriptions>
        </div> -->

            <!-- 列信息表格 -->
            <div v-if="tableDetail" class="columns-section">
              <!-- <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
            <h3 style="margin: 0;">字段信息 ({{ filteredColumns?.length || 0 }} 个字段)</h3>
            <el-button size="small" type="primary" @click="showAddFieldDialog">
              <el-icon><Plus /></el-icon>
              新增字段
            </el-button>
          </div> -->
              <el-table
                :data="filteredColumns"
                border
                stripe
                style="width: 100%"
                size="small"
                :loading="tableDetailLoading"
              >
                <el-table-column
                  prop="column_name"
                  label="字段名"
                  width="180"
                />
                <el-table-column
                  prop="data_type"
                  label="数据类型"
                  width="130"
                />
                <el-table-column prop="is_nullable" label="允许空值" width="90">
                  <template #default="{ row }">
                    <el-tag :type="row.is_nullable ? 'success' : 'danger'">
                      {{ row.is_nullable ? "是" : "否" }}
                    </el-tag>
                  </template>
                </el-table-column>
                <!-- <el-table-column prop="is_primary_key" label="主键" width="80">
              <template #default="{ row }">
                <el-icon v-if="row.is_primary_key" color="#f56c6c"><Key /></el-icon>
              </template>
            </el-table-column> -->
            <el-table-column prop="column_default" label="默认值" width="120" show-overflow-tooltip />
            <!-- <el-table-column prop="column_comment" label="字段注释" min-width="300" show-overflow-tooltip /> -->
            <el-table-column label="操作" width="155" fixed="right">
              <template #default="{ row }">
                <el-button size="small" @click="showEditFieldDialog(row)">
                  <el-icon><Edit /></el-icon>
                  编辑
                </el-button>
                <el-button 
                  size="small" 
                  type="danger" 
                  @click="showDeleteFieldDialog(row)"
                  :disabled="row.is_primary_key"
                  style="margin-left: 8px;"
                >
                  <el-icon><Delete /></el-icon>
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>

            <!-- 加载状态 -->
            <div v-if="!tableDetail && !tableDetailLoading" class="empty-state">
              <el-empty description="点击刷新数据按钮加载表详情" />
            </div>
          </div>
        </el-card>

        <!-- 右侧：资源类型与字段勾选管理 -->
        <el-card
          v-loading="resourceTypesLoading"
          class="main-card right-col"
          element-loading-text="加载资源类型..."
          element-loading-background="rgba(255,255,255,0.7)"
        >
          <template #header>
            <div class="card-header">
              <span>资源类型字段管理</span>
              <div class="header-actions">
                <el-button
                  :loading="resourceTypesLoading"
                  size="small"
                  @click="loadResourceTypesList"
                >
                  <el-icon><Refresh /></el-icon>
                  刷新类型
                </el-button>
                <el-button
                  type="primary"
                  size="small"
                  @click="openCreateTypeDialog"
                >
                  <el-icon><Plus /></el-icon>
                  新建类型
                </el-button>
              </div>
            </div>
            <!-- 资源类型卡片列表 -->
            <div
              class="resource-type-cards"
              style="height: 90px; overflow-y: auto"
            >
              <template v-if="resourceTypes.length">
                <el-card
                  v-for="rt in resourceTypes"
                  :key="rt.id"
                  class="type-card"
                  :class="{ active: String(rt.id) === String(activeTypeId) }"
                  shadow="hover"
                  @click="selectResourceType(rt)"
                >
                  <div class="type-card-title">{{ rt.name }}</div>
                  <div class="type-card-desc">
                    {{ rt.describe || "无描述" }}
                  </div>
                  <div class="type-card-actions">
                    <el-button
                      size="small"
                      text
                      @click.stop="openEditTypeDialog(rt)"
                    >
                      编辑
                    </el-button>
                    <el-button
                      size="small"
                      text
                      type="danger"
                      @click.stop="confirmDeleteType(rt)"
                    >
                      删除
                    </el-button>
                  </div>
                </el-card>
              </template>
              <div
                v-else
                style="
                  margin-left: 40%;
                  display: flex;
                  align-items: center;
                  gap: 8px;
                "
              >
                <el-icon class="is-loading" :size="20"><Loading /></el-icon>
                <span>加载资源类型...</span>
              </div>
            </div>
            <div
              class="actions"
              style="
                margin-top: 12px;
                display: flex;
                gap: 8px;
                align-items: center;
              "
            >
              <!-- <el-button size="small" @click="clearChecked" :disabled="!activeTypeId">清空勾选</el-button> -->
              <span
                v-if="activeTypeId"
                class="save-status"
                style="
                  color: var(--el-text-color-secondary);
                  font-size: 12px;
                  display: inline-flex;
                  align-items: center;
                  gap: 6px;
                "
              >
                <el-icon v-if="isAutoSaving" class="is-loading"
                  ><Loading
                /></el-icon>
                <span>{{
                  isAutoSaving
                    ? "自动保存中…"
                    : saveStatusText || "勾选将自动保存"
                }}</span>
              </span>
            </div>
          </template>

          <!-- 资源类型卡片列表 -->
          <!-- <div class="resource-type-cards" style="height: 90px; overflow-y: auto;">
            <template v-if="resourceTypes.length">
              <el-card
                v-for="rt in resourceTypes"
                :key="rt.id"
                class="type-card"
                :class="{ active: String(rt.id) === String(activeTypeId) }"
                @click="selectResourceType(rt)"
                shadow="hover"
              >
                <div class="type-card-title">{{ rt.name }}</div>
                <div class="type-card-desc">{{ rt.describe || '无描述' }}</div>
                <div class="type-card-actions">
                  <el-button size="small" text @click.stop="openEditTypeDialog(rt)">
                    <el-icon><Edit /></el-icon>
                    编辑
                  </el-button>
                  <el-button size="small" text type="danger" @click.stop="confirmDeleteType(rt)">
                    <el-icon><Delete /></el-icon>
                    删除
                  </el-button>
                </div>
              </el-card>
            </template>
            <el-empty v-else description="暂无资源类型" />
          </div>
          <div class="actions" style="margin-top: 12px; display: flex; gap: 8px; align-items: center;">
            <el-button size="small" @click="clearChecked" :disabled="!activeTypeId">清空勾选</el-button>
            <span v-if="activeTypeId" class="save-status" style="color: var(--el-text-color-secondary); font-size: 12px; display: inline-flex; align-items: center; gap: 6px;">
              <el-icon v-if="isAutoSaving" class="is-loading"><Loading /></el-icon>
              <span>{{ isAutoSaving ? '自动保存中…' : (saveStatusText || '勾选将自动保存') }}</span>
            </span>
          </div> -->
          <!-- 字段勾选区：显示中心表字段，勾选即为该资源类型所需字段 -->
          <div
            v-loading="isAutoSaving"
            class="center-fields-list"
            style="margin-top: 12px"
            element-loading-text="保存中..."
            element-loading-background="rgba(255,255,255,0.4)"
          >
            <div class="panel-header" style="margin-bottom: 8px">
              <!-- <h4 style="margin: 0;">中心表字段 ({{ HARDCODED_TABLE }})</h4> -->
              <!-- <p class="panel-desc" style="margin: 4px 0 0 0; color: var(--el-text-color-secondary);">勾选为该资源类型所需字段，点击保存提交</p> -->
            </div>
            <el-table
              :data="sortedRightPanelFields"
              border
              stripe
              style="width: 100%"
              size="small"
              :loading="tableDetailLoading || resourceTypesLoading"
            >
              <el-table-column label="必选" width="80">
                <template #default="{ row }">
                  <el-checkbox
                    :disabled="!activeTypeId"
                    :model-value="isFieldChecked(row.column_name)"
                    @change="onFieldCheckChange(row, $event)"
                  />
                </template>
              </el-table-column>
              <el-table-column prop="column_name" label="字段名" width="180" />
              <el-table-column prop="data_type" label="数据类型" width="140" />
              <el-table-column
                prop="column_comment"
                label="字段说明"
                show-overflow-tooltip
              >
                <template #default="{ row }">
                  <el-input
                    :model-value="getFieldDesc(row.column_name)"
                    size="small"
                    placeholder="请输入字段说明"
                    @update:model-value="val => setFieldDesc(row.column_name, val)"
                    clearable
                  />
                </template>
              </el-table-column>
            </el-table>

            <!-- <div class="actions" style="margin-top: 12px; display: flex; gap: 8px;">
              <el-button @click="clearChecked" :disabled="!activeTypeId">清空勾选</el-button>
              <el-button type="primary" @click="saveResourceTypeFields" :disabled="!activeTypeId">保存</el-button>
            </div> -->
          </div>
        </el-card>
      </div>

      <!-- 表数据对话框 -->
      <el-dialog
        v-model="dataDialogVisible"
        title="表数据预览"
        width="90%"
        :close-on-click-modal="false"
      >
        <div
          v-loading="tableDataLoading"
          class="dialog-loading-wrap"
          element-loading-text="加载数据..."
          element-loading-background="rgba(255,255,255,0.7)"
        >
          <div class="data-toolbar">
            <div class="data-info">
              <span>共 {{ tableData.length }} 条记录</span>
            </div>
            <div>
              <el-button :loading="tableDataLoading" @click="loadTableData">
                <el-icon><Refresh /></el-icon>
                刷新
              </el-button>
            </div>
          </div>

          <el-table
            :data="paginatedTableData"
            border
            stripe
            style="width: 100%; margin-top: 16px"
            :loading="tableDataLoading"
            max-height="400"
          >
            <el-table-column
              v-for="column in tableDataColumns"
              :key="column"
              :prop="column"
              :label="column"
              min-width="120"
              show-overflow-tooltip
            />
          </el-table>

          <div class="pagination-section" style="margin-top: 16px">
            <el-pagination
              v-model:current-page="dataTablePagination.currentPage"
              v-model:page-size="dataTablePagination.pageSize"
              :page-sizes="[10, 20, 50, 100]"
              :total="tableData.length"
              layout="total, sizes, prev, pager, next, jumper"
              @size-change="handleDataSizeChange"
              @current-change="handleDataCurrentChange"
            />
          </div>
        </div>
      </el-dialog>

      <!-- 字段编辑对话框 -->
      <el-dialog
        v-model="editFieldDialogVisible"
        title="编辑字段"
        width="600px"
        :close-on-click-modal="false"
      >
        <el-form
          ref="editFieldFormRef"
          :model="editFieldForm"
          :rules="editFieldRules"
          label-width="120px"
        >
          <el-form-item label="字段名称" prop="column_name">
            <el-input
              v-model="editFieldForm.column_name"
              placeholder="字段名称不可修改"
              disabled
            />
          </el-form-item>
          <el-form-item label="数据类型">
            <el-input v-model="editFieldForm.data_type" disabled />
          </el-form-item>
          <el-form-item label="字段注释" prop="column_comment">
            <el-input
              v-model="editFieldForm.column_comment"
              type="textarea"
              :rows="3"
              placeholder="请输入字段注释"
            />
          </el-form-item>
          <el-form-item label="默认值" prop="column_default">
            <el-input
              v-model="editFieldForm.column_default"
              placeholder="请输入默认值"
            />
          </el-form-item>
          <el-form-item label="允许空值">
            <el-switch
              v-model="editFieldForm.is_nullable"
              active-text="是"
              inactive-text="否"
            />
          </el-form-item>
        </el-form>

        <template #footer>
          <div class="dialog-footer">
            <el-button @click="editFieldDialogVisible = false">取消</el-button>
            <el-button
              type="primary"
              :loading="editFieldLoading"
              @click="submitEditField"
            >
              保存
            </el-button>
          </div>
        </template>
      </el-dialog>

      <!-- 删除字段确认对话框 -->
      <el-dialog
        v-model="deleteFieldDialogVisible"
        title="删除字段确认"
        width="500px"
        :close-on-click-modal="false"
      >
        <div class="delete-confirmation">
          <el-icon color="#f56c6c" size="48px" style="margin-bottom: 16px">
            <WarningFilled />
          </el-icon>
          <p style="font-size: 16px; margin-bottom: 16px">
            确定要删除字段
            <strong>{{ deleteFieldInfo.column_name }}</strong> 吗？
          </p>
          <p style="color: #f56c6c; font-size: 14px; margin-bottom: 0">
            此操作不可逆，删除后该字段的所有数据将丢失！
          </p>
        </div>

        <template #footer>
          <div class="dialog-footer">
            <el-button @click="deleteFieldDialogVisible = false"
              >取消</el-button
            >
            <el-button
              type="danger"
              :loading="deleteFieldLoading"
              @click="submitDeleteField"
            >
              确认删除
            </el-button>
          </div>
        </template>
      </el-dialog>

      <!-- 新增字段对话框 -->
      <el-dialog
        v-model="addFieldDialogVisible"
        title="新增字段"
        width="600px"
        :close-on-click-modal="false"
      >
        <el-form
          ref="addFieldFormRef"
          :model="addFieldForm"
          :rules="addFieldRules"
          label-width="120px"
        >
          <el-form-item label="字段名称" prop="column_name">
            <el-input
              v-model="addFieldForm.column_name"
              placeholder="请输入字段名称"
            />
          </el-form-item>
          <el-form-item label="数据类型" prop="data_type">
            <el-select
              v-model="addFieldForm.data_type"
              placeholder="请选择数据类型"
              style="width: 100%"
            >
              <el-option label="VARCHAR(255)" value="VARCHAR(255)" />
              <el-option label="INT" value="INT" />
              <el-option label="BIGINT" value="BIGINT" />
              <el-option label="DECIMAL(10,2)" value="DECIMAL(10,2)" />
              <el-option label="TEXT" value="TEXT" />
              <el-option label="DATE" value="DATE" />
              <el-option label="DATETIME" value="DATETIME" />
              <el-option label="TIMESTAMP" value="TIMESTAMP" />
              <el-option label="BOOLEAN" value="BOOLEAN" />
            </el-select>
          </el-form-item>
          <el-form-item label="字段注释" prop="column_comment">
            <el-input
              v-model="addFieldForm.column_comment"
              type="textarea"
              :rows="3"
              placeholder="请输入字段注释"
            />
          </el-form-item>
          <el-form-item label="默认值" prop="column_default">
            <el-input
              v-model="addFieldForm.column_default"
              placeholder="请输入默认值（可选）"
            />
          </el-form-item>
          <el-form-item label="允许空值">
            <el-switch
              v-model="addFieldForm.is_nullable"
              active-text="是"
              inactive-text="否"
            />
          </el-form-item>
        </el-form>

        <template #footer>
          <div class="dialog-footer">
            <el-button @click="addFieldDialogVisible = false">取消</el-button>
            <el-button
              type="primary"
              :loading="addFieldLoading"
              @click="submitAddField"
            >
              保存
            </el-button>
          </div>
        </template>
      </el-dialog>

      <!-- 新建类型对话框（复制资源类型管理中的实现） -->
      <el-dialog v-model="typeDialog.visible" title="新建类型" width="700px">
        <el-form :model="typeDialog.form" label-width="100px">
          <el-form-item label="名称">
            <el-input
              v-model="typeDialog.form.name"
              placeholder="请输入类型名称"
            />
          </el-form-item>
          <el-form-item label="描述">
            <el-input
              v-model="typeDialog.form.describe"
              type="textarea"
              :autosize="{ minRows: 4, maxRows: 10 }"
              placeholder="请输入描述"
            />
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="typeDialog.visible = false">取消</el-button>
          <el-button type="primary" @click="submitType">保存</el-button>
        </template>
      </el-dialog>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted, computed, nextTick } from "vue";
import { useRoute } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import type { FormInstance } from "element-plus";
import {
  Search,
  Refresh,
  Plus,
  Delete,
  Key,
  Edit,
  WarningFilled,
  Loading,
  Fold,
  Expand,
} from "@element-plus/icons-vue";
import { dataInsightAPI } from "@/api/dataInsight";
import type {
  DataSource,
  TableInfo,
  TableDetail,
  TableColumn,
  TableDataRequest,
  FieldUpdateRequest,
} from "@/api/dataInsight";
import {
  listResourceTypes,
  createResourceType,
  updateResourceType,
  deleteResourceType,
} from "@/api/resourceType";
import type { ResourceTypeItem, ResourceField } from "@/types/resourceType";

const route = useRoute();

// 硬编码的数据源信息
const HARDCODED_DATASOURCE = {
  id: 8, // 使用整数ID而不是IP地址
  name: "10.20.1.201",
  db_type: "oracle",
  host: "10.20.1.201",
} as DataSource;

const HARDCODED_SCHEMA = "cepiec-warehouse";
const HARDCODED_TABLE = "cpc_dw_publication";

// 响应式数据
const loading = ref(false);
const tableDetailLoading = ref(false);
const tableDataLoading = ref(false);
const editFieldLoading = ref(false);
const deleteFieldLoading = ref(false);
const addFieldLoading = ref(false);

// 左侧面板折叠状态
const isLeftCollapsed = ref(false);

// 表相关
const tableDetail = ref<TableDetail | null>(null);

// 表数据相关
const tableData = ref<any[]>([]);
const tableDataColumns = ref<string[]>([]);

// 对话框状态
const dataDialogVisible = ref(false);
const editFieldDialogVisible = ref(false);
const deleteFieldDialogVisible = ref(false);
const addFieldDialogVisible = ref(false);

// 新建/编辑资源类型对话框（复制资源类型管理中的结构）
const typeDialog = reactive({
  visible: false,
  form: {
    name: "",
    describe: "",
    metadata: [] as ResourceField[],
  } as Partial<ResourceTypeItem>,
  mode: "create" as "create" | "edit",
  editId: null as null | string | number,
});

// 字段编辑相关
const editFieldFormRef = ref<FormInstance>();
const editFieldForm = reactive({
  // 原始列名用于重命名时定位旧列
  original_name: "",
  column_name: "",
  data_type: "",
  column_comment: "",
  column_default: "",
  is_nullable: false,
});

// 删除字段相关
const deleteFieldInfo = reactive({
  column_name: "",
  data_type: "",
});

// 新增字段相关
const addFieldFormRef = ref<FormInstance>();
const addFieldForm = reactive({
  column_name: "",
  data_type: "",
  column_comment: "",
  column_default: "",
  is_nullable: true,
});

const addFieldRules = {
  column_name: [
    { required: true, message: "请输入字段名称", trigger: "blur" },
    {
      pattern: /^[a-zA-Z_][a-zA-Z0-9_]*$/,
      message: "字段名称只能包含字母、数字和下划线，且不能以数字开头",
      trigger: "blur",
    },
    { max: 64, message: "字段名称长度不能超过64个字符", trigger: "blur" },
  ],
  data_type: [{ required: true, message: "请选择数据类型", trigger: "change" }],
  column_comment: [
    { max: 500, message: "字段注释长度不能超过500个字符", trigger: "blur" },
  ],
};

// 编辑校验：允许修改字段名，并做唯一性与命名规范校验
const validateEditColumnNameUnique = (
  _rule: any,
  value: string,
  callback: any,
) => {
  const name = String(value || "").toLowerCase();
  const original = String(editFieldForm.original_name || "").toLowerCase();
  // 命名规范：与新增一致
  const pattern = /^[a-zA-Z_][a-zA-Z0-9_]*$/;
  if (!value) return callback(new Error("请输入字段名称"));
  if (!pattern.test(value))
    return callback(
      new Error("字段名称只能包含字母、数字和下划线，且不能以数字开头"),
    );
  if (value.length > 64)
    return callback(new Error("字段名称长度不能超过64个字符"));
  // 唯一性（排除当前原始名）
  const exists = (tableDetail.value?.columns || []).some(
    (col) =>
      String(col.column_name).toLowerCase() === name &&
      String(col.column_name).toLowerCase() !== original,
  );
  if (exists) return callback(new Error("字段名称已存在"));
  callback();
};

const editFieldRules = {
  column_name: [{ validator: validateEditColumnNameUnique, trigger: "blur" }],
  column_comment: [
    { max: 500, message: "字段注释长度不能超过500个字符", trigger: "blur" },
  ],
};

// 表数据分页
const dataTablePagination = reactive({
  currentPage: 1,
  pageSize: 20,
});

// 计算属性
const filteredColumns = computed(() => {
  if (!tableDetail.value?.columns) return [];
  // 过滤掉列名为 batch_id 和 batch_code 的列
  return tableDetail.value.columns.filter(
    (column) =>
      column.column_name !== "batch_id" && column.column_name !== "batch_code",
  );
});

// ====== 右侧资源类型与字段勾选逻辑 ======
const resourceTypesLoading = ref(false);
const resourceTypes = ref<ResourceTypeItem[]>([]);
const activeTypeId = ref<string | number | null>(null);
// 勾选的字段 key（小写）
const checkedKeys = ref<string[]>([])
const fieldDescriptions = reactive<Record<string, string>>({})
// 自动保存状态
const isAutoSaving = ref(false);
const saveStatusText = ref("");
let autoSaveTimer: any = null;

// 右侧面板字段数据（来自左侧已加载的 filteredColumns）
const rightPanelFields = computed(() => filteredColumns.value);
// 已勾选字段置顶
const sortedRightPanelFields = computed(() => {
  const set = new Set(checkedKeys.value);
  const arr = rightPanelFields.value.slice();
  return arr.sort((a, b) => {
    const aSel = set.has(String(a.column_name).toLowerCase()) ? 1 : 0;
    const bSel = set.has(String(b.column_name).toLowerCase()) ? 1 : 0;
    return bSel - aSel;
  });
});

const getFieldDesc = (key: string) => fieldDescriptions[String(key).toLowerCase()] || ''
const setFieldDesc = (key: string, val: string) => {
  fieldDescriptions[String(key).toLowerCase()] = val || ''
  if (activeTypeId.value) scheduleAutoSave()
}

// 勾选状态方法
const isFieldChecked = (key: string) =>
  checkedKeys.value.includes(String(key).toLowerCase());
const onFieldCheckChange = (row: TableColumn, checked: boolean) => {
  const key = String(row.column_name).toLowerCase();
  const set = new Set(checkedKeys.value);
  if (checked) set.add(key);
  else set.delete(key);
  checkedKeys.value = Array.from(set);
  scheduleAutoSave();
};
const clearChecked = () => {
  checkedKeys.value = [];
  scheduleAutoSave();
};

// 防抖自动保存
const scheduleAutoSave = () => {
  if (!activeTypeId.value) return;
  isAutoSaving.value = true;
  saveStatusText.value = "自动保存中…";
  if (autoSaveTimer) clearTimeout(autoSaveTimer);
  autoSaveTimer = setTimeout(async () => {
    await saveResourceTypeFields(true);
  }, 500);
};

// 数据类型映射到资源字段类型
const mapDataTypeToFieldType = (dataType: string): string => {
  const type = (dataType || "").toLowerCase();
  if (
    type.includes("int") ||
    type.includes("bigint") ||
    type.includes("smallint")
  )
    return "int";
  if (
    type.includes("decimal") ||
    type.includes("float") ||
    type.includes("double") ||
    type.includes("numeric")
  )
    return "number";
  if (type.includes("bool")) return "boolean";
  if (type.includes("date") || type.includes("time")) return "datetime";
  return "string";
};

// 根据当前选中的资源类型，预选勾选字段
const refreshPreselection = async () => {
  await nextTick()
  if (!activeTypeId.value) { checkedKeys.value = []; return }
  const current = resourceTypes.value.find(rt => String(rt.id) === String(activeTypeId.value))
  const existingKeys = new Set((current?.metadata || []).map(f => String(f.key).toLowerCase()))
  const existingDescMap = new Map((current?.metadata || []).map(f => [String(f.key).toLowerCase(), f.description || '']))
  const preset: string[] = []
  rightPanelFields.value.forEach(col => {
    const colKey = String(col.column_name).toLowerCase()
    if (existingKeys.has(colKey)) preset.push(colKey)
    fieldDescriptions[colKey] = existingDescMap.get(colKey) ?? (col.column_comment || '')
  })
  checkedKeys.value = preset
}

const loadResourceTypesList = async () => {
  try {
    resourceTypesLoading.value = true;
    const res = await listResourceTypes({ page: 1, page_size: 100 });
    if (!res.success) throw new Error(res.message);
    resourceTypes.value = (res.data?.items || []) as ResourceTypeItem[];
    // 默认选中第一个
    if (resourceTypes.value.length && !activeTypeId.value) {
      activeTypeId.value = resourceTypes.value[0].id as any;
    }
    await refreshPreselection();
  } catch (e: any) {
    ElMessage.error(e?.message || "加载资源类型失败");
  } finally {
    resourceTypesLoading.value = false;
  }
};

const selectResourceType = async (rt: ResourceTypeItem) => {
  activeTypeId.value = rt.id as any;
  await refreshPreselection();
};

const saveResourceTypeFields = async (silent = false) => {
  if (!activeTypeId.value) return;
  try {
    const set = new Set(checkedKeys.value);
    const selected = rightPanelFields.value.filter((f) =>
      set.has(String(f.column_name).toLowerCase()),
    );
    const newMetadata: ResourceField[] = selected.map((field) => ({
      key: field.column_name,
      type: mapDataTypeToFieldType(field.data_type),
      required: true,
      description: getFieldDesc(field.column_name) || ''
    }))
    const res = await updateResourceType(String(activeTypeId.value), { metadata: newMetadata })
    if (!res.success) throw new Error(res.message)
    if (!silent) ElMessage.success('字段保存成功')
    // 更新本地资源类型数据中的 metadata
    const idx = resourceTypes.value.findIndex(
      (rt) => String(rt.id) === String(activeTypeId.value),
    );
    if (idx >= 0) resourceTypes.value[idx].metadata = newMetadata;
    await refreshPreselection();
    isAutoSaving.value = false;
    saveStatusText.value = "已保存";
    setTimeout(() => {
      saveStatusText.value = "";
    }, 1500);
  } catch (e: any) {
    if (!silent) ElMessage.error(e?.message || "保存失败");
    isAutoSaving.value = false;
    saveStatusText.value = "保存失败";
  }
};

onUnmounted(() => {
  if (autoSaveTimer) clearTimeout(autoSaveTimer);
});

// 打开“新建类型”对话框
const openCreateTypeDialog = () => {
  typeDialog.visible = true;
  typeDialog.mode = "create";
  typeDialog.editId = null;
  typeDialog.form = { name: "", describe: "", metadata: [] };
};

// 打开“编辑类型”对话框
const openEditTypeDialog = (rt: ResourceTypeItem) => {
  typeDialog.visible = true;
  typeDialog.mode = "edit";
  typeDialog.editId = rt.id as any;
  typeDialog.form = {
    id: rt.id,
    name: rt.name,
    describe: rt.describe,
    metadata: (rt.metadata || []).map((f) => ({ ...f })),
  };
};

// 提交创建/编辑资源类型
const submitType = async () => {
  if (!typeDialog.form?.name) {
    ElMessage.warning("请填写名称");
    return;
  }
  try {
    if (typeDialog.mode === "edit" && typeDialog.editId) {
      const res = await updateResourceType(String(typeDialog.editId), {
        name: typeDialog.form.name!,
        describe: typeDialog.form.describe,
        metadata: typeDialog.form.metadata as ResourceField[],
      });
      if (!res.success) throw new Error(res.message);
      ElMessage.success("更新成功");
      typeDialog.visible = false;
      // 更新本地列表项
      const idx = resourceTypes.value.findIndex(
        (rt) => String(rt.id) === String(typeDialog.editId),
      );
      if (idx >= 0) {
        resourceTypes.value[idx].name = typeDialog.form.name!;
        resourceTypes.value[idx].describe = typeDialog.form.describe || "";
      }
      activeTypeId.value = typeDialog.editId as any;
      await refreshPreselection();
    } else {
      const res = await createResourceType({
        name: typeDialog.form.name!,
        describe: typeDialog.form.describe,
        metadata: [],
      });
      if (!res.success) throw new Error(res.message);
      ElMessage.success("创建成功");
      typeDialog.visible = false;
      // 刷新资源类型列表，并优先选中新创建的类型
      await loadResourceTypesList();
      const newId = res.data?.id;
      if (newId) {
        activeTypeId.value = newId as any;
        await refreshPreselection();
      }
    }
  } catch (e: any) {
    ElMessage.error(e?.message || "保存失败");
  }
};

// 删除资源类型
const confirmDeleteType = async (rt: ResourceTypeItem) => {
  if (!rt?.id) {
    ElMessage.warning("无法获取类型ID");
    return;
  }
  try {
    await ElMessageBox.confirm(`确认删除类型 “${rt.name}”？`, "删除确认", {
      type: "warning",
    });
    const res = await deleteResourceType(String(rt.id));
    if (!res.success) throw new Error(res.message);
    ElMessage.success("删除成功");
    // 从本地列表移除并处理选中状态
    resourceTypes.value = resourceTypes.value.filter(
      (t) => String(t.id) !== String(rt.id),
    );
    if (String(activeTypeId.value) === String(rt.id)) {
      activeTypeId.value = resourceTypes.value[0]?.id ?? null;
    }
    await refreshPreselection();
  } catch (e: any) {
    // 取消不提示错误
    if (e && e !== "cancel") {
      ElMessage.error(e?.message || "删除失败");
    }
  }
};

const paginatedTableData = computed(() => {
  const start =
    (dataTablePagination.currentPage - 1) * dataTablePagination.pageSize;
  const end = start + dataTablePagination.pageSize;
  return tableData.value.slice(start, end);
});

// 方法定义
const loadTableDetail = async () => {
  try {
    tableDetailLoading.value = true;
    const response = await dataInsightAPI.explorer.getTableDetail(
      HARDCODED_DATASOURCE.id,
      HARDCODED_TABLE,
      HARDCODED_SCHEMA,
    );
    tableDetail.value = response;
    ElMessage.success("表详情加载成功");
    // 同步加载资源类型并进行预选
    if (!resourceTypes.value.length) await loadResourceTypesList();
    await refreshPreselection();
  } catch (error) {
    console.error("获取表详情失败:", error);
    ElMessage.error("获取表详情失败");
  } finally {
    tableDetailLoading.value = false;
  }
};

const loadTableData = async () => {
  try {
    tableDataLoading.value = true;
    const params: TableDataRequest = {
      datasource_id: HARDCODED_DATASOURCE.id,
      table_name: HARDCODED_TABLE,
      schema: HARDCODED_SCHEMA,
      limit: 100,
    };

    const response = await dataInsightAPI.explorer.getTableData(params);
    tableData.value = response.data || [];
    tableDataColumns.value = response.columns || [];
    dataTablePagination.currentPage = 1;
    dataDialogVisible.value = true;
    ElMessage.success(`成功加载 ${tableData.value.length} 条记录`);
  } catch (error) {
    console.error("获取表数据失败:", error);
    ElMessage.error("获取表数据失败");
  } finally {
    tableDataLoading.value = false;
  }
};

// 字段编辑相关方法
const showEditFieldDialog = (column: TableColumn) => {
  console.log("showEditFieldDialog called with:", column);
  editFieldForm.original_name = column.column_name;
  editFieldForm.column_name = column.column_name;
  editFieldForm.data_type = column.data_type;
  editFieldForm.column_comment = column.column_comment || "";
  editFieldForm.column_default = column.column_default || "";
  editFieldForm.is_nullable = column.is_nullable;
  editFieldDialogVisible.value = true;
};

const submitEditField = async () => {
  if (!editFieldFormRef.value) return;

  try {
    await editFieldFormRef.value.validate();
    editFieldLoading.value = true;

    // 构建表结构修改请求（符合后端TableStructureRequest格式）
    const updateRequest = {
      datasource_id: HARDCODED_DATASOURCE.id,
      table_name: tableDetail.value?.table_name || "",
      schema: HARDCODED_SCHEMA,
      operation_type: "modify_column",
      column_data: {
        original_name: editFieldForm.original_name,
        name: editFieldForm.original_name, // 禁止重命名：与原始名保持一致
        type: editFieldForm.data_type,
        comment: editFieldForm.column_comment,
        default: editFieldForm.column_default,
        nullable: editFieldForm.is_nullable,
      },
    };

    // 调用API更新字段
    const response = await dataInsightAPI.explorer.updateField(updateRequest);

    if (response.success) {
      ElMessage.success("字段更新成功");

      // 更新本地数据
      if (tableDetail.value && tableDetail.value.columns) {
        const originalKey = String(editFieldForm.original_name).toLowerCase();
        const newKey = String(editFieldForm.column_name).toLowerCase();
        const columnIndex = tableDetail.value.columns.findIndex(
          (col) => String(col.column_name).toLowerCase() === originalKey,
        );
        if (columnIndex !== -1) {
          tableDetail.value.columns[columnIndex] = {
            ...tableDetail.value.columns[columnIndex],
            column_comment: editFieldForm.column_comment,
            column_default: editFieldForm.column_default,
            is_nullable: editFieldForm.is_nullable,
          };
        }
      }

      // 关闭编辑对话框
      editFieldDialogVisible.value = false;
    } else {
      ElMessage.error(response.message || "字段更新失败");
    }
  } catch (error) {
    console.error("字段更新失败:", error);
    ElMessage.error("字段更新失败，请稍后重试");
  } finally {
    editFieldLoading.value = false;
  }
};

// 显示删除字段对话框
const showDeleteFieldDialog = (column: TableColumn) => {
  deleteFieldInfo.column_name = column.column_name;
  deleteFieldInfo.data_type = column.data_type;
  deleteFieldDialogVisible.value = true;
};

// 提交删除字段
const submitDeleteField = async () => {
  try {
    deleteFieldLoading.value = true;

    // 构建表结构删除请求（符合后端TableStructureRequest格式）
    const deleteRequest = {
      datasource_id: HARDCODED_DATASOURCE.id,
      table_name: tableDetail.value?.table_name || "",
      schema: HARDCODED_SCHEMA,
      operation_type: "drop_column",
      column_data: {
        name: deleteFieldInfo.column_name,
      },
    };

    // 调用API删除字段
    const response = await dataInsightAPI.explorer.updateField(deleteRequest);

    if (response.success) {
      ElMessage.success("字段删除成功");

      // 更新本地数据 - 从列表中移除删除的字段
      if (tableDetail.value && tableDetail.value.columns) {
        tableDetail.value.columns = tableDetail.value.columns.filter(
          (col) => col.column_name !== deleteFieldInfo.column_name,
        );
      }

      // 关闭删除对话框
      deleteFieldDialogVisible.value = false;
    } else {
      ElMessage.error(response.message || "字段删除失败");
    }
  } catch (error) {
    console.error("字段删除失败:", error);
    ElMessage.error("字段删除失败，请稍后重试");
  } finally {
    deleteFieldLoading.value = false;
  }
};

// 显示新增字段对话框
const showAddFieldDialog = () => {
  // 重置表单
  addFieldForm.column_name = "";
  addFieldForm.data_type = "";
  addFieldForm.column_comment = "";
  addFieldForm.column_default = "";
  addFieldForm.is_nullable = true;
  addFieldDialogVisible.value = true;
};

// 提交新增字段
const submitAddField = async () => {
  if (!addFieldFormRef.value) return;

  try {
    await addFieldFormRef.value.validate();
    addFieldLoading.value = true;

    // 构建表结构新增请求（符合后端TableStructureRequest格式）
    const addRequest = {
      datasource_id: HARDCODED_DATASOURCE.id,
      table_name: tableDetail.value?.table_name || "",
      schema: HARDCODED_SCHEMA,
      operation_type: "add_column",
      column_data: {
        name: addFieldForm.column_name,
        type: addFieldForm.data_type,
        comment: addFieldForm.column_comment,
        default: addFieldForm.column_default || null,
        nullable: addFieldForm.is_nullable,
      },
    };

    // 调用API新增字段
    const response = await dataInsightAPI.explorer.updateField(addRequest);

    if (response.success) {
      ElMessage.success("字段新增成功");

      // 更新本地数据 - 添加新字段到列表
      if (tableDetail.value && tableDetail.value.columns) {
        const newColumn = {
          column_name: addFieldForm.column_name,
          data_type: addFieldForm.data_type,
          column_comment: addFieldForm.column_comment,
          column_default: addFieldForm.column_default,
          is_nullable: addFieldForm.is_nullable,
          is_primary_key: false,
        };
        tableDetail.value.columns.push(newColumn);
      }

      // 关闭新增对话框
      addFieldDialogVisible.value = false;
    } else {
      ElMessage.error(response.message || "字段新增失败");
    }
  } catch (error) {
    console.error("字段新增失败:", error);
    ElMessage.error("字段新增失败，请稍后重试");
  } finally {
    addFieldLoading.value = false;
  }
};


const handleDataSizeChange = (size: number) => {
  dataTablePagination.pageSize = size;
  dataTablePagination.currentPage = 1;
};

const handleDataCurrentChange = (page: number) => {
  dataTablePagination.currentPage = page;
};

// 生命周期 - 页面加载时自动获取表详情
onMounted(() => {
  loadTableDetail();
});
</script>

<style scoped lang="scss">
.center-table-management {
  padding: 6px;
  /* 去掉不必要的底部留白，避免出现外部滚动条 */
  padding-bottom: 0;
  /* 与上层布局内容区保持一致高度，避免 100vh 引起溢出 */
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden; /* 禁止页面外部滚动，使用内部滚动 */

  .page-header {
    margin-bottom: 6px;

    h2 {
      margin: 0 0 8px 0;
      color: #303133;
      font-size: 24px;
      font-weight: 600;
    }

    .page-description {
      margin: 0;
      color: #606266;
      font-size: 14px;
    }
  }

  .content-wrapper {
    flex: 1; /* 占满剩余空间 */
    min-height: 0; /* 允许子元素在高度上收缩以启用滚动 */
    overflow: hidden; /* 避免包裹层产生外部滚动 */
    padding-bottom: 5px;

    .two-column-layout {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 16px;
      height: 100%; /* 填满内容区高度 */
      min-height: 0; /* 使网格子项可在高度上收缩以使用内部滚动 */
      transition: grid-template-columns 0.3s ease;

      &.is-collapsed {
        grid-template-columns: 48px 1fr;
      }

      // .right-col, .el-card__body {
      //   padding: 8px !important;
      // }
    }

    .main-card {
      height: 100%;
      display: flex;
      flex-direction: column;
      .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        min-height: 42px; /* 统一左右标题高度 */

        .header-actions {
          display: flex;
          gap: 12px;
        }
      }

      /* 卡片主体区域启用内部滚动，填满剩余空间 */
      :deep(.el-card__body) {
        flex: 1;
        min-height: 0;
        padding: 12px;
        overflow-y: auto;

        .el-scrollbar__bar.is-vertical {
          display: none !important;
        }
      }

      /* 折叠状态样式 */
      .collapsed-view {
        height: 100%;
        display: flex;
        flex-direction: column;
        align-items: center;
        padding-top: 16px;
        cursor: pointer;
        color: #606266;
        transition: all 0.3s;

        &:hover {
          color: var(--el-color-primary);
          background-color: var(--el-fill-color-light);
        }

        .collapsed-content {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 8px;
        }

        .vertical-text {
          writing-mode: vertical-rl;
          letter-spacing: 4px;
          font-size: 14px;
          font-weight: 600;
        }
      }

      /* 折叠时移除卡片内边距 */
      &.collapsed-card :deep(.el-card__body) {
        padding: 0 !important;
        overflow: hidden;
      }

      /* 网格子项需要可收缩以启用卡片内部滚动 */
      .left-col,
      .right-col {
        min-height: 0;
      }

      .datasource-section {
        padding: 16px;
        background-color: #f8f9fa;
        border-radius: 6px;
      }

      .search-section {
        margin-bottom: 20px;
        padding: 16px;
        background-color: #f8f9fa;
        border-radius: 6px;
      }

      .table-section {
        margin-bottom: 20px;
      }

      .pagination-section {
        display: flex;
        justify-content: flex-end;
      }

      .empty-state {
        text-align: center;
        padding: 40px 0;
      }

      // 右侧资源类型卡片样式
      .resource-type-cards {
        display: flex;
        gap: 12px;
        overflow-x: auto;
        white-space: nowrap;
        -webkit-overflow-scrolling: touch;
        padding-bottom: 6px; /* 给滚动条留一点空间 */
        scroll-snap-type: x proximity;
      }

      .resource-type-cards::-webkit-scrollbar {
        height: 8px;
      }
      .resource-type-cards::-webkit-scrollbar-thumb {
        background-color: rgba(0, 0, 0, 0.2);
        border-radius: 4px;
      }

      .type-card {
        cursor: pointer;
        flex: 0 0 auto;
        width: 185px;
        scroll-snap-align: start;
        position: relative;
      }
      .type-card.active {
        border-color: var(--el-color-primary);
      }
      .type-card-title {
        font-weight: 600;
        margin-bottom: 6px;
      }
      .type-card-desc {
        color: var(--el-text-color-secondary);
        font-size: 12px;
      }
      .type-card-actions {
        position: absolute;
        right: 8px;
        bottom: 8px;
        display: flex;
        gap: 4px;
        opacity: 0;
        transition: opacity 0.2s ease;
      }
      .type-card:hover .type-card-actions {
        opacity: 1;
      }
    }
  }

  .data-toolbar {
    display: flex;
    justify-content: space-between;
    align-items: center;

    .data-info {
      color: #606266;
      font-size: 14px;
    }
  }
}
</style>
