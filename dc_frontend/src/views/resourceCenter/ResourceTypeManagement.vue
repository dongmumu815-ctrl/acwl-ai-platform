<template>
  <div class="resource-type-page">
    <div class="page-header">
      <h2>资源类型管理</h2>
      <p class="desc">维护资源类型的基础信息与字段配置</p>
    </div>

    <div class="toolbar">
      <el-input
        v-model="keyword"
        placeholder="搜索名称或描述"
        clearable
        class="toolbar-input"
        @keyup.enter="fetchList"
      />
      <el-button type="primary" @click="fetchList">
        <el-icon><Search /></el-icon>
        搜索
      </el-button>
      <el-button type="primary" @click="openCreateDialog">新建类型</el-button>
    </div>

    <el-card class="list-card">
      <el-table v-loading="loading" :data="items" stripe>
        <el-table-column prop="id" label="ID" min-width="220" />
        <el-table-column prop="name" label="名称" min-width="160" />
        <el-table-column prop="describe" label="描述" min-width="220" />
        <el-table-column label="操作" width="260" fixed="right">
          <template #default="{ row }">
            <el-button
              size="small"
              type="primary"
              link
              @click="openEditDialog(row)"
              >编辑</el-button
            >
            <el-divider direction="vertical" />
            <el-button
              size="small"
              type="primary"
              link
              @click="openFieldsDialog(row)"
              >字段管理</el-button
            >
            <el-divider direction="vertical" />
            <el-popconfirm
              title="确认删除该类型？"
              @confirm="handleDelete(row)"
            >
              <template #reference>
                <el-button size="small" type="danger" link>删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination">
        <el-pagination
          background
          layout="prev, pager, next, jumper"
          :total="total"
          :page-size="size"
          :current-page="page"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>

    <!-- 新建/编辑类型 -->
    <el-dialog
      v-model="typeDialog.visible"
      :title="typeDialog.isEdit ? '编辑类型' : '新建类型'"
      width="700px"
    >
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
        <!-- 字段管理区块已移除：编辑弹窗仅保留基本信息 -->
      </el-form>
      <template #footer>
        <el-button @click="typeDialog.visible = false">取消</el-button>
        <el-button type="primary" @click="submitType">保存</el-button>
      </template>
    </el-dialog>

    <!-- 字段管理 -->
    <el-drawer
      v-model="fieldsDialog.visible"
      title="字段管理"
      direction="rtl"
      size="1000px"
    >
      <div class="field-editor-container">
        <!-- 单面板：中心表字段勾选即为该资源类型所需字段 -->
        <div class="left-panel">
          <div class="panel-header">
            <h4>中心表字段 (cpc_dw_publication)</h4>
            <p class="panel-desc">勾选为该资源类型所需字段，保存后提交</p>
            <el-button
              :loading="centerFieldsLoading"
              size="small"
              @click="loadCenterTableFields"
            >
              <el-icon><Refresh /></el-icon>
              刷新字段
            </el-button>
          </div>

          <div class="center-fields-list">
            <el-table
              ref="centerFieldsTableRef"
              v-loading="centerFieldsLoading"
              :data="sortedCenterTableFields"
              row-key="column_name"
              size="small"
            >
              <el-table-column label="必选" width="80">
                <template #default="{ row }">
                  <el-checkbox
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
                  {{ row.column_comment || row.comment || "-" }}
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="fieldsDialog.visible = false">取消</el-button>
        <el-button type="primary" @click="saveFields">保存</el-button>
      </template>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, nextTick, computed } from "vue";
import { ElMessage } from "element-plus";
import {
  listResourceTypes,
  createResourceType,
  updateResourceType,
  deleteResourceType,
} from "@/api/resourceType";
import { dataInsightAPI } from "@/api/dataInsight";
import type { ResourceTypeItem, ResourceField } from "@/types/resourceType";

interface CenterTableField {
  column_name: string;
  data_type: string;
  column_comment: string;
  is_nullable: boolean;
}

const loading = ref(false);
const items = ref<ResourceTypeItem[]>([]);
const page = ref(1);
const size = ref(10);
const total = ref(0);
const keyword = ref("");

const typeDialog = reactive({
  visible: false,
  isEdit: false,
  form: {
    name: "",
    describe: "",
    metadata: [] as ResourceField[],
  } as Partial<ResourceTypeItem>,
});

const fieldsDialog = reactive({
  visible: false,
  form: {
    id: "",
    name: "",
    describe: "",
    metadata: [] as ResourceField[],
  } as Partial<ResourceTypeItem>,
});

// 中心表字段管理相关数据
const centerTableFields = ref<CenterTableField[]>([]);
// 勾选的字段 key（使用小写，避免大小写差异）
const checkedKeys = ref<string[]>([]);
const centerFieldsLoading = ref(false);
const centerFieldsTableRef = ref<any>(null);

// 计算属性：将已勾选（选中）的字段排到列表顶部，保持其他顺序不变
const sortedCenterTableFields = computed(() => {
  const selectedSet = new Set(checkedKeys.value);
  // 稳定排序：选中的在前，未选中的在后；同组内保持原始相对顺序
  const arr = centerTableFields.value.slice();
  return arr.sort((a, b) => {
    const aSel = selectedSet.has(String(a.column_name).toLowerCase()) ? 1 : 0;
    const bSel = selectedSet.has(String(b.column_name).toLowerCase()) ? 1 : 0;
    return bSel - aSel;
  });
});

// 计算：当前已勾选的中心表字段对象列表（用于保存）
const selectedCenterFields = computed<CenterTableField[]>(() => {
  const set = new Set(checkedKeys.value);
  return centerTableFields.value.filter((f) =>
    set.has(String(f.column_name).toLowerCase()),
  );
});

// 勾选状态相关方法
const isFieldChecked = (key: string) =>
  checkedKeys.value.includes(String(key).toLowerCase());
const onFieldCheckChange = (row: CenterTableField, checked: boolean) => {
  const key = String(row.column_name).toLowerCase();
  const set = new Set(checkedKeys.value);
  if (checked) {
    set.add(key);
  } else {
    set.delete(key);
  }
  checkedKeys.value = Array.from(set);
};

// 硬编码的数据源和表信息（与中心表管理保持一致）
const HARDCODED_DATASOURCE = {
  id: 8,
  name: "10.20.1.201",
  db_type: "oracle",
  host: "10.20.1.201",
};
const HARDCODED_SCHEMA = "cepiec-warehouse";
const HARDCODED_TABLE = "cpc_dw_publication";

const fetchList = async () => {
  loading.value = true;
  try {
    const res = await listResourceTypes({
      page: page.value,
      page_size: size.value,
      name: keyword.value || undefined,
    });
    if (res.success) {
      const data = res.data;
      items.value = (data.items || []) as ResourceTypeItem[];
      total.value = data.total || 0;
      page.value = data.page || 1;
      size.value = data.page_size || 10;
    } else {
      ElMessage.error(res.message || "获取列表失败");
    }
  } catch (e: any) {
    ElMessage.error(e?.message || "请求失败");
  } finally {
    loading.value = false;
  }
};

const handlePageChange = (p: number) => {
  page.value = p;
  fetchList();
};

const openCreateDialog = () => {
  typeDialog.visible = true;
  typeDialog.isEdit = false;
  typeDialog.form = { name: "", describe: "", metadata: [] };
};

const openEditDialog = (row: ResourceTypeItem) => {
  typeDialog.visible = true;
  typeDialog.isEdit = true;
  typeDialog.form = {
    id: row.id,
    name: row.name,
    describe: row.describe,
    metadata: (row.metadata || []).map((f) => ({ ...f })),
  };
};

const submitType = async () => {
  if (!typeDialog.form.name) {
    ElMessage.warning("请填写名称");
    return;
  }
  try {
    if (typeDialog.isEdit && typeDialog.form.id) {
      const res = await updateResourceType(typeDialog.form.id as string, {
        name: typeDialog.form.name,
        describe: typeDialog.form.describe,
        metadata: typeDialog.form.metadata as ResourceField[],
      });
      if (!res.success) throw new Error(res.message);
      ElMessage.success("更新成功");
    } else {
      const res = await createResourceType({
        name: typeDialog.form.name!,
        describe: typeDialog.form.describe,
        metadata: typeDialog.form.metadata as ResourceField[],
      });
      if (!res.success) throw new Error(res.message);
      ElMessage.success("创建成功");
    }
    typeDialog.visible = false;
    fetchList();
  } catch (e: any) {
    ElMessage.error(e?.message || "保存失败");
  }
};

const openFieldsDialog = async (row: ResourceTypeItem) => {
  fieldsDialog.visible = true;
  fieldsDialog.form = {
    id: row.id,
    name: row.name,
    describe: row.describe,
    metadata: (row.metadata || []).map((f) => ({ ...f })),
  };
  // 重置中心表字段相关数据
  centerTableFields.value = [];
  checkedKeys.value = [];
  // 加载固定表的字段
  await loadCenterTableFields();
  // 加载完成后根据现有metadata预选中对应字段
  await nextTick();
  try {
    const existingKeys = new Set(
      (fieldsDialog.form.metadata || []).map((f) =>
        String(f.key).toLowerCase(),
      ),
    );
    const preset: string[] = [];
    centerTableFields.value.forEach((rowItem) => {
      const colKey = String(rowItem.column_name).toLowerCase();
      if (existingKeys.has(colKey)) preset.push(colKey);
    });
    checkedKeys.value = preset;
  } catch (e) {
    // 兜底：忽略表格引用异常，保证不影响使用
    console.warn("预选字段失败：", e);
  }
};

// 加载中心表字段（固定表：cpc_dw_publication）
const loadCenterTableFields = async () => {
  try {
    centerFieldsLoading.value = true;
    const response = await dataInsightAPI.explorer.getTableDetail(
      HARDCODED_DATASOURCE.id,
      HARDCODED_TABLE,
      HARDCODED_SCHEMA,
    );

    if (response && response.columns) {
      // 过滤掉 batch_id 和 batch_code 字段，与中心表管理保持一致
      centerTableFields.value = response.columns
        .filter(
          (column) =>
            column.column_name !== "batch_id" &&
            column.column_name !== "batch_code",
        )
        .map((column) => ({
          column_name: column.column_name,
          data_type: column.data_type,
          column_comment: column.column_comment || column.comment || "",
          is_nullable: column.is_nullable,
        }));
    }
  } catch (error) {
    console.error("加载中心表字段失败:", error);
    ElMessage.error("加载中心表字段失败");
  } finally {
    centerFieldsLoading.value = false;
  }
};

// 下方逻辑改为：勾选即为保存目标，不再进行“添加/删除”操作

// 将数据库字段类型映射为资源字段类型
const mapDataTypeToFieldType = (dataType: string): string => {
  const type = dataType.toLowerCase();
  if (
    type.includes("int") ||
    type.includes("bigint") ||
    type.includes("smallint")
  ) {
    return "int";
  } else if (
    type.includes("decimal") ||
    type.includes("float") ||
    type.includes("double") ||
    type.includes("numeric")
  ) {
    return "number";
  } else if (type.includes("bool")) {
    return "boolean";
  } else if (type.includes("date") || type.includes("time")) {
    return "datetime";
  } else {
    return "string";
  }
};

const saveFields = async () => {
  if (!fieldsDialog.form.id) return;
  try {
    // 将当前勾选的中心表字段保存为资源类型的metadata
    const selected = selectedCenterFields.value;
    const newMetadata: ResourceField[] = selected.map((field) => ({
      key: field.column_name,
      type: mapDataTypeToFieldType(field.data_type),
      // 需求：勾选即为该资源类型所需字段（必填）
      required: true,
      description: field.column_comment || "",
    }));
    const res = await updateResourceType(fieldsDialog.form.id as string, {
      metadata: newMetadata,
    });
    if (!res.success) throw new Error(res.message);
    ElMessage.success("字段保存成功");
    fieldsDialog.visible = false;
    fetchList();
  } catch (e: any) {
    ElMessage.error(e?.message || "保存失败");
  }
};

// 新增：删除资源类型
const handleDelete = async (row: ResourceTypeItem) => {
  if (!row?.id) {
    ElMessage.warning("无法获取类型ID");
    return;
  }
  try {
    const res = await deleteResourceType(String(row.id));
    if (!res.success) throw new Error(res.message);
    ElMessage.success("删除成功");
    fetchList();
  } catch (e: any) {
    ElMessage.error(e?.message || "删除失败");
  }
};

onMounted(() => {
  fetchList();
});
</script>

<style scoped>
.resource-type-page {
  padding: 16px;
}
.page-header {
  margin-bottom: 16px;
}
.page-header h2 {
  margin: 0 0 8px;
  font-size: 20px;
}
.page-header .desc {
  margin: 0;
  color: var(--el-text-color-secondary);
}
.toolbar {
  display: flex;
  gap: 12px;
  align-items: center;
  margin-bottom: 12px;
}
.toolbar-input {
  width: 280px;
}
.list-card {
  border-radius: 8px;
}
.pagination {
  display: flex;
  justify-content: flex-end;
  padding: 12px 8px 0;
}
.field-editor-container {
  display: flex;
  gap: 20px;
  height: 100%;
}

.left-panel,
.right-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  border: 1px solid var(--el-border-color-light);
  border-radius: 8px;
  overflow: hidden;
}

.panel-header {
  padding: 16px;
  background: var(--el-bg-color-page);
  border-bottom: 1px solid var(--el-border-color-light);
}

.panel-header h4 {
  margin: 0 0 4px;
  font-size: 16px;
  font-weight: 600;
}

.panel-desc {
  margin: 0;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.center-fields-list {
  flex: 1;
  padding: 16px;
  overflow: auto;
}

.panel-actions {
  padding: 16px;
  border-top: 1px solid var(--el-border-color-light);
  background: var(--el-bg-color-page);
}

.right-panel .panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.right-panel .panel-header h4 {
  margin: 0;
}

.field-toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
}

.right-panel .el-table {
  margin: 16px;
  flex: 1;
}
</style>
