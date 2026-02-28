<template>
  <div class="batch-management">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-left">
          <h1 class="page-title">
            <el-icon><DataBoard /></el-icon>
            批次管理
          </h1>
          <p class="page-description">管理和监控数据批次处理任务</p>
        </div>
        <div class="header-right">
          <el-button type="primary" @click="showCreateDialog">
            <el-icon><Plus /></el-icon>
            创建批次
          </el-button>
          <el-button @click="loadBatches">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-section">
      <el-row :gutter="20">
        <el-col :xs="12" :sm="6">
          <div class="stat-card">
            <div class="stat-icon total">
              <el-icon><DataBoard /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.total }}</div>
              <div class="stat-label">总批次</div>
            </div>
          </div>
        </el-col>

        <el-col :xs="12" :sm="6">
          <div class="stat-card">
            <div class="stat-icon pending">
              <el-icon><Clock /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.pending }}</div>
              <div class="stat-label">待处理</div>
            </div>
          </div>
        </el-col>

        <el-col :xs="12" :sm="6">
          <div class="stat-card">
            <div class="stat-icon processing">
              <el-icon><Loading /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.processing }}</div>
              <div class="stat-label">处理中</div>
            </div>
          </div>
        </el-col>

        <el-col :xs="12" :sm="6">
          <div class="stat-card">
            <div class="stat-icon completed">
              <el-icon><Check /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.completed }}</div>
              <div class="stat-label">已完成</div>
            </div>
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- 搜索和筛选 -->
    <div class="page-card">
      <div class="search-section">
        <el-row :gutter="20">
          <el-col :span="6">
            <el-input
              v-model="searchQuery"
              placeholder="搜索批次名称"
              clearable
              @input="handleSearch"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
          </el-col>
          <el-col :span="6">
            <el-select
              v-model="customerFilter"
              placeholder="按客户筛选"
              clearable
              filterable
              @change="handleSearch"
            >
              <el-option
                v-for="customer in customers"
                :key="customer.id"
                :label="`${customer.name} (${customer.company || ''})`"
                :value="customer.id"
              />
            </el-select>
          </el-col>
          <el-col :span="4">
            <el-select
              v-model="statusFilter"
              placeholder="状态筛选"
              clearable
              @change="handleSearch"
            >
              <el-option label="全部" value="" />
              <el-option label="待处理" value="pending" />
              <el-option label="处理中" value="processing" />
              <el-option label="已完成" value="completed" />
              <el-option label="失败" value="failed" />
            </el-select>
          </el-col>
          <el-col :span="8">
            <el-date-picker
              v-model="dateRange"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              format="YYYY-MM-DD"
              value-format="YYYY-MM-DD"
              @change="handleSearch"
            />
          </el-col>
        </el-row>
      </div>
    </div>

    <!-- 批次表格 -->
    <div class="page-card">
      <el-table
        v-loading="loading"
        :data="filteredBatches"
        style="width: 100%"
        @sort-change="handleSortChange"
      >
        <el-table-column prop="id" label="ID" width="80" sortable />
        <el-table-column
          prop="batch_name"
          label="批次名称"
          width="150"
          sortable
        />
        <el-table-column prop="customer.name" label="客户" width="120">
          <template #default="{ row }">
            {{ row.customer?.name || "-" }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusTagType(row.status)">
              {{ getStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column
          prop="total_records"
          label="总记录数"
          width="100"
          sortable
        />
        <el-table-column
          prop="processed_records"
          label="已处理"
          width="100"
          sortable
        />
        <el-table-column
          prop="failed_records"
          label="失败数"
          width="100"
          sortable
        />
        <el-table-column label="进度" width="120">
          <template #default="{ row }">
            <el-progress
              :percentage="getProgress(row)"
              :status="getProgressStatus(row.status)"
              :stroke-width="8"
            />
          </template>
        </el-table-column>
        <el-table-column prop="started_at" label="开始时间" width="150">
          <template #default="{ row }">
            {{ row.started_at ? formatDate(row.started_at) : "-" }}
          </template>
        </el-table-column>
        <el-table-column prop="completed_at" label="完成时间" width="150">
          <template #default="{ row }">
            {{ row.completed_at ? formatDate(row.completed_at) : "-" }}
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="150">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="250" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="viewDetail(row)">
              <el-icon><View /></el-icon>
              详情
            </el-button>
            <el-button
              v-if="row.status === 'pending'"
              size="small"
              type="success"
              @click="startProcessing(row)"
            >
              <el-icon><VideoPlay /></el-icon>
              开始
            </el-button>
            <el-button
              v-if="row.status === 'processing'"
              size="small"
              type="warning"
              @click="stopProcessing(row)"
            >
              <el-icon><VideoPause /></el-icon>
              停止
            </el-button>
            <el-button
              v-if="row.status === 'completed' && row.result_file_path"
              size="small"
              type="info"
              @click="downloadResult(row)"
            >
              <el-icon><Download /></el-icon>
              下载
            </el-button>
            <el-button size="small" type="danger" @click="deleteBatch(row)">
              <el-icon><Delete /></el-icon>
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </div>

    <!-- 创建批次对话框 -->
    <el-dialog
      v-model="dialogVisible"
      title="创建批次"
      width="600px"
      @close="resetForm"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="formRules"
        label-width="120px"
      >
        <el-form-item label="批次名称" prop="batch_name">
          <el-input v-model="form.batch_name" placeholder="请输入批次名称" />
        </el-form-item>

        <el-form-item label="所属平台" prop="customer_id">
          <el-select
            v-model="form.customer_id"
            placeholder="请选择客户"
            style="width: 100%"
            filterable
          >
            <el-option
              v-for="customer in customers"
              :key="customer.id"
              :label="`${customer.name} (${customer.company || ''})`"
              :value="customer.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="描述" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            placeholder="请输入批次描述"
          />
        </el-form-item>

        <el-form-item label="数据文件" prop="file">
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :limit="1"
            :on-change="handleFileChange"
            :on-remove="handleFileRemove"
            accept=".csv,.xlsx,.xls,.json"
          >
            <el-button>
              <el-icon><Upload /></el-icon>
              选择文件
            </el-button>
            <template #tip>
              <div class="el-upload__tip">
                支持 CSV、Excel、JSON 格式文件，文件大小不超过 100MB
              </div>
            </template>
          </el-upload>
        </el-form-item>
      </el-form>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="submitting" @click="submitForm">
            创建
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from "vue";
import { useRouter } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import type { FormInstance, FormRules, UploadFile } from "element-plus";
import { formatDate } from "@/utils/date";
import {
  getBatches,
  createBatch,
  deleteBatch as deleteBatchRequest,
  startBatchProcessing,
  stopBatchProcessing,
  downloadBatchResult,
} from "@/api/apiManagement";
import { getCustomers } from "@/api/apiManagement";
import type {
  DataBatch,
  DataBatchCreate,
  Customer,
} from "@/types/apiManagement";

/**
 * 路由
 */
const router = useRouter();

/**
 * 响应式数据
 */
const loading = ref(false);
const batches = ref<DataBatch[]>([]);
const customers = ref<Customer[]>([]);
const searchQuery = ref("");
const customerFilter = ref<number | "">("");
const statusFilter = ref("");
const dateRange = ref<[string, string] | null>(null);
const dialogVisible = ref(false);
const submitting = ref(false);
const formRef = ref<FormInstance>();
const uploadRef = ref();

// 统计数据
const stats = reactive({
  total: 0,
  pending: 0,
  processing: 0,
  completed: 0,
  failed: 0,
});

// 分页数据
const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0,
});

// 表单数据
const form = reactive<DataBatchCreate>({
  customer_id: 0,
  batch_name: "",
  description: "",
  file: undefined,
});

// 表单验证规则
const formRules: FormRules = {
  batch_name: [
    { required: true, message: "请输入批次名称", trigger: "blur" },
    { min: 2, max: 50, message: "长度在 2 到 50 个字符", trigger: "blur" },
  ],
  customer_id: [{ required: true, message: "请选择客户", trigger: "change" }],
};

/**
 * 计算属性
 */
const filteredBatches = computed(() => {
  let result = batches.value;

  // 搜索过滤
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase();
    result = result.filter((batch) =>
      batch.batch_name.toLowerCase().includes(query),
    );
  }

  // 客户过滤
  if (customerFilter.value) {
    result = result.filter(
      (batch) => batch.customer_id === customerFilter.value,
    );
  }

  // 状态过滤
  if (statusFilter.value) {
    result = result.filter((batch) => batch.status === statusFilter.value);
  }

  // 日期过滤
  if (dateRange.value && dateRange.value.length === 2) {
    const [startDate, endDate] = dateRange.value;
    result = result.filter((batch) => {
      const createdDate = batch.created_at.split("T")[0];
      return createdDate >= startDate && createdDate <= endDate;
    });
  }

  return result;
});

/**
 * 生命周期钩子
 */
onMounted(() => {
  loadBatches();
  loadCustomers();
});

/**
 * 方法定义
 */

/**
 * 加载批次列表
 */
const loadBatches = async () => {
  try {
    loading.value = true;
    const response = await getBatches({
      page: pagination.page,
      page_size: pagination.pageSize,
    });

    if (response.success) {
      batches.value = response.data.items;
      pagination.total = response.data.total;

      // 更新统计数据
      updateStats();
    } else {
      ElMessage.error(response.message || "加载批次列表失败");
    }
  } catch (error) {
    console.error("加载批次列表失败:", error);
    ElMessage.error("加载批次列表失败");
  } finally {
    loading.value = false;
  }
};

/**
 * 加载客户列表
 */
const loadCustomers = async () => {
  try {
    const response = await getCustomers({ page_size: 1000 });
    if (response.success) {
      customers.value = response.data.items;
    }
  } catch (error) {
    console.error("加载客户列表失败:", error);
  }
};

/**
 * 更新统计数据
 */
const updateStats = () => {
  stats.total = batches.value.length;
  stats.pending = batches.value.filter((b) => b.status === "pending").length;
  stats.processing = batches.value.filter(
    (b) => b.status === "processing",
  ).length;
  stats.completed = batches.value.filter(
    (b) => b.status === "completed",
  ).length;
  stats.failed = batches.value.filter((b) => b.status === "failed").length;
};

/**
 * 获取状态标签类型
 */
const getStatusTagType = (status: string) => {
  const types: Record<string, string> = {
    pending: "info",
    processing: "warning",
    completed: "success",
    failed: "danger",
  };
  return types[status] || "info";
};

/**
 * 获取状态标签
 */
const getStatusLabel = (status: string) => {
  const labels: Record<string, string> = {
    pending: "待处理",
    processing: "处理中",
    completed: "已完成",
    failed: "失败",
  };
  return labels[status] || status;
};

/**
 * 获取进度百分比
 */
const getProgress = (batch: DataBatch) => {
  if (batch.total_records === 0) return 0;
  return Math.round((batch.processed_records / batch.total_records) * 100);
};

/**
 * 获取进度状态
 */
const getProgressStatus = (status: string) => {
  if (status === "completed") return "success";
  if (status === "failed") return "exception";
  return undefined;
};

/**
 * 显示创建对话框
 */
const showCreateDialog = () => {
  dialogVisible.value = true;
  resetForm();
};

/**
 * 重置表单
 */
const resetForm = () => {
  if (formRef.value) {
    formRef.value.resetFields();
  }

  Object.assign(form, {
    customer_id: 0,
    batch_name: "",
    description: "",
    file: undefined,
  });

  if (uploadRef.value) {
    uploadRef.value.clearFiles();
  }
};

/**
 * 文件选择处理
 */
const handleFileChange = (file: UploadFile) => {
  form.file = file.raw;
};

/**
 * 文件移除处理
 */
const handleFileRemove = () => {
  form.file = undefined;
};

/**
 * 提交表单
 */
const submitForm = async () => {
  if (!formRef.value) return;

  try {
    await formRef.value.validate();

    if (!form.file) {
      ElMessage.error("请选择数据文件");
      return;
    }

    submitting.value = true;

    const response = await createBatch(form);
    if (response.success) {
      ElMessage.success("批次创建成功");
      dialogVisible.value = false;
      loadBatches();
    } else {
      ElMessage.error(response.message || "批次创建失败");
    }
  } catch (error) {
    console.error("提交表单失败:", error);
  } finally {
    submitting.value = false;
  }
};

/**
 * 查看详情
 */
const viewDetail = (batch: DataBatch) => {
  router.push(`/api-management/batches/${batch.id}`);
};

/**
 * 开始处理
 */
const startProcessing = async (batch: DataBatch) => {
  try {
    const response = await startBatchProcessing(batch.id);
    if (response.success) {
      ElMessage.success("批次处理已开始");
      loadBatches();
    } else {
      ElMessage.error(response.message || "开始处理失败");
    }
  } catch (error) {
    console.error("开始处理失败:", error);
    ElMessage.error("开始处理失败");
  }
};

/**
 * 停止处理
 */
const stopProcessing = async (batch: DataBatch) => {
  try {
    await ElMessageBox.confirm(
      `确定要停止批次 "${batch.batch_name}" 的处理吗？`,
      "确认停止",
      {
        confirmButtonText: "确定",
        cancelButtonText: "取消",
        type: "warning",
      },
    );

    const response = await stopBatchProcessing(batch.id);
    if (response.success) {
      ElMessage.success("批次处理已停止");
      loadBatches();
    } else {
      ElMessage.error(response.message || "停止处理失败");
    }
  } catch (error) {
    if (error !== "cancel") {
      console.error("停止处理失败:", error);
      ElMessage.error("停止处理失败");
    }
  }
};

/**
 * 下载结果
 */
const downloadResult = async (batch: DataBatch) => {
  try {
    const blob = await downloadBatchResult(batch.id);

    // 创建下载链接
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `batch_${batch.id}_result.xlsx`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);

    ElMessage.success("文件下载成功");
  } catch (error) {
    console.error("下载结果失败:", error);
    ElMessage.error("下载结果失败");
  }
};

/**
 * 删除批次
 */
const deleteBatch = async (batch: DataBatch) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除批次 "${batch.batch_name}" 吗？此操作不可恢复。`,
      "确认删除",
      {
        confirmButtonText: "确定",
        cancelButtonText: "取消",
        type: "warning",
      },
    );

    const response = await deleteBatchRequest(batch.id);
    if (response.success) {
      ElMessage.success("批次删除成功");
      loadBatches();
    } else {
      ElMessage.error(response.message || "批次删除失败");
    }
  } catch (error) {
    if (error !== "cancel") {
      console.error("删除批次失败:", error);
      ElMessage.error("批次删除失败");
    }
  }
};

/**
 * 搜索处理
 */
const handleSearch = () => {
  // 搜索逻辑已在计算属性中处理
};

/**
 * 排序处理
 */
const handleSortChange = ({ prop, order }: { prop: string; order: string }) => {
  console.log("排序:", prop, order);
};

/**
 * 分页大小改变
 */
const handleSizeChange = (size: number) => {
  pagination.pageSize = size;
  pagination.page = 1;
  loadBatches();
};

/**
 * 当前页改变
 */
const handleCurrentChange = (page: number) => {
  pagination.page = page;
  loadBatches();
};
</script>

<style scoped lang="scss">
.batch-management {
  .page-header {
    margin-bottom: 20px;

    .header-content {
      display: flex;
      justify-content: space-between;
      align-items: center;

      .header-left {
        .page-title {
          display: flex;
          align-items: center;
          gap: 8px;
          margin: 0 0 8px 0;
          font-size: 24px;
          font-weight: 600;
          color: var(--el-text-color-primary);
        }

        .page-description {
          margin: 0;
          color: var(--el-text-color-regular);
        }
      }

      .header-right {
        display: flex;
        gap: 12px;
      }
    }
  }

  .stats-section {
    margin-bottom: 20px;

    .stat-card {
      display: flex;
      align-items: center;
      padding: 20px;
      background: white;
      border-radius: 8px;
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);

      .stat-icon {
        width: 48px;
        height: 48px;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-right: 16px;
        font-size: 24px;

        &.total {
          background: #e3f2fd;
          color: #1976d2;
        }

        &.pending {
          background: #fff3e0;
          color: #f57c00;
        }

        &.processing {
          background: #f3e5f5;
          color: #7b1fa2;
        }

        &.completed {
          background: #e8f5e8;
          color: #388e3c;
        }
      }

      .stat-content {
        .stat-value {
          font-size: 24px;
          font-weight: 600;
          color: var(--el-text-color-primary);
          margin-bottom: 4px;
        }

        .stat-label {
          font-size: 14px;
          color: var(--el-text-color-regular);
        }
      }
    }
  }

  .search-section {
    padding: 20px;
  }

  .pagination-wrapper {
    display: flex;
    justify-content: center;
    margin-top: 20px;
    padding: 20px;
  }
}
</style>
