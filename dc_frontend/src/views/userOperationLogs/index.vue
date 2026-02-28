<template>
  <div class="user-operation-logs">
    <el-card class="mb-3" shadow="never">
      <template #header>
        <div class="card-header">
          <span>用户操作日志</span>
          
        </div>
      </template>

      <el-form :model="filters" label-width="100px" inline>
        <!-- <el-form-item label="关键字">
          <el-input v-model="filters.search" placeholder="用户名、路径、请求ID" clearable style="width: 240px" />
        </el-form-item> -->
        <el-form-item label="业务模块">
          <el-input
            v-model="filters.module"
            placeholder="业务模块"
            clearable
            style="width: 180px"
          />
        </el-form-item>
        <el-form-item label="方法">
          <el-select
            v-model="filters.method"
            placeholder="HTTP 方法"
            clearable
            style="width: 160px"
          >
            <el-option v-for="m in methods" :key="m" :label="m" :value="m" />
          </el-select>
        </el-form-item>
        <!-- <el-form-item label="路径">
          <el-input v-model="filters.path" placeholder="请求路径" clearable style="width: 260px" />
        </el-form-item> -->
        <!-- <el-form-item label="状态码">
          <el-input-number v-model="filters.status_code" :min="100" :max="599" :step="1" :controls="false" placeholder="200" style="width: 120px" />
        </el-form-item> -->
        <el-form-item label="结果">
          <el-select
            v-model="filters.success"
            placeholder="是否成功"
            clearable
            style="width: 140px"
          >
            <el-option label="成功" :value="true" />
            <el-option label="失败" :value="false" />
          </el-select>
        </el-form-item>
        <el-form-item label="时间范围">
          <el-date-picker
            v-model="dateRange"
            type="datetimerange"
            range-separator="至"
            start-placeholder="开始时间"
            end-placeholder="结束时间"
            :unlink-panels="true"
            value-format="YYYY-MM-DD HH:mm:ss"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="onSearch" :loading="loading" style="margin-left: 25px">查询</el-button>
            <el-button type="primary" @click="loadLogs" :loading="loading">刷新</el-button>
            <el-button @click="resetFilters" :disabled="loading">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card shadow="never">
      <el-table :data="logs" v-loading="loading" stripe height="500px">
        <el-table-column prop="created_at" label="时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="module" label="业务模块" width="160" />
        <el-table-column prop="method" label="方法" width="110">
          <template #default="{ row }">
            <el-tag :type="methodTagType(row.method)" effect="plain">{{
              row.method
            }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column
          prop="path"
          label="路径"
          min-width="240"
          show-overflow-tooltip
        />
        <el-table-column prop="status_code" label="状态码" width="120">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.status_code)" effect="plain">{{
              row.status_code
            }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="result_status" label="结果" width="110">
          <template #default="{ row }">
            <el-tag
              :type="row.result_status === 'success' ? 'success' : 'danger'"
              effect="plain"
            >
              {{ row.result_status === "success" ? "成功" : "失败" }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="duration_ms" label="耗时(ms)" width="120" />
        <el-table-column prop="request_id" label="请求ID" width="200" />
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="openDetail(row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="mt-3">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :page-sizes="[10, 20, 30, 50]"
          layout="total, sizes, prev, pager, next, jumper"
          :total="pagination.total"
          @size-change="onPageSizeChange"
          @current-change="onPageChange"
        />
      </div>
    </el-card>

    <el-drawer v-model="detailVisible" title="日志详情" size="50%">
      <template v-if="currentDetail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="时间">{{ formatDateTime(currentDetail.created_at) }}</el-descriptions-item>
          <el-descriptions-item label="业务模块">{{ currentDetail.module || '-' }}</el-descriptions-item>
          <el-descriptions-item label="方法">{{ currentDetail.method }}</el-descriptions-item>
          <el-descriptions-item label="路径">{{ currentDetail.path }}</el-descriptions-item>
          <el-descriptions-item label="状态码">{{ currentDetail.status_code }}</el-descriptions-item>
          <el-descriptions-item label="结果">{{ currentDetail.success ? '成功' : '失败' }}</el-descriptions-item>
          <el-descriptions-item label="耗时(ms)">{{ currentDetail.duration_ms ?? '-' }}</el-descriptions-item>
          <el-descriptions-item label="请求ID" :span="2">{{ currentDetail.request_id || '-' }}</el-descriptions-item>
        </el-descriptions>

        <el-collapse class="mt-3">
          <el-collapse-item title="请求头" name="headers">
            <pre class="code-block">{{
              pretty(currentDetail.request_headers)
            }}</pre>
          </el-collapse-item>
          <el-collapse-item title="查询参数" name="query">
            <pre class="code-block">{{
              pretty(currentDetail.query_params)
            }}</pre>
          </el-collapse-item>
          <el-collapse-item title="请求体" name="req">
            <pre class="code-block">{{
              pretty(currentDetail.request_body)
            }}</pre>
          </el-collapse-item>
          <el-collapse-item title="响应体" name="res">
            <pre class="code-block">{{
              pretty(currentDetail.response_body)
            }}</pre>
          </el-collapse-item>
          <el-collapse-item
            v-if="currentDetail.error_message"
            title="错误信息"
            name="error"
          >
            <pre class="code-block">{{ currentDetail.error_message }}</pre>
          </el-collapse-item>
          <el-collapse-item
            v-if="currentDetail.stack_trace"
            title="堆栈"
            name="stack"
          >
            <pre class="code-block">{{ currentDetail.stack_trace }}</pre>
          </el-collapse-item>
        </el-collapse>
      </template>
      <template v-else>
        <el-empty description="暂无数据" />
      </template>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { userOperationLogsApi } from '@/api/userOperationLogs'
import type { UserOperationLog, UserOperationLogDetail } from '@/api/userOperationLogs'
import dayjs from 'dayjs'

const methods = ["GET", "POST", "PUT", "DELETE", "PATCH"];

const filters = reactive({
  search: "",
  module: "",
  method: "",
  path: "",
  status_code: undefined as number | undefined,
  success: undefined as boolean | undefined,
});

const dateRange = ref<string[] | null>(null);

const logs = ref<UserOperationLog[]>([]);
const loading = ref(false);

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0,
});

function methodTagType(method: string) {
  switch (method) {
    case "GET":
      return "info";
    case "POST":
      return "success";
    case "PUT":
      return "warning";
    case "DELETE":
      return "danger";
    default:
      return "";
  }
}

function statusTagType(code: number) {
  if (code >= 200 && code < 300) return "success";
  if (code >= 300 && code < 400) return "info";
  if (code >= 400 && code < 500) return "warning";
  return "danger";
}

function isSuccessFlag(v: any): boolean | undefined {
  if (v === undefined || v === null) return undefined;
  if (typeof v === "boolean") return v;
  if (typeof v === "number") return v === 1;
  if (typeof v === "string") return v === "1" || v.toLowerCase() === "true";
  return !!v;
}

async function loadLogs() {
  loading.value = true;
  try {
    const params: any = {
      page: pagination.page,
      size: pagination.pageSize,
      keyword: filters.search || undefined,
      method: filters.method || undefined,
      path: filters.path || undefined,
      status_code: filters.status_code || undefined,
      result_status:
        typeof filters.success === "boolean"
          ? filters.success
            ? "success"
            : "failure"
          : undefined,
      module: filters.module || undefined,
    };
    if (dateRange.value && dateRange.value.length === 2) {
      params.start_date = dateRange.value[0];
      params.end_date = dateRange.value[1];
    }

    const res = await userOperationLogsApi.getLogs(params);

    // Prefer standard ApiResponse<PaginatedResponse<T>>; fall back gracefully
    const data = (res as any).data ?? res;
    const rawItems = data?.items ?? data?.data?.items ?? [];
    const total = data?.total ?? data?.data?.total ?? 0;
    const page = data?.page ?? data?.data?.page ?? params.page;
    const size = data?.size ?? data?.data?.size ?? params.size;

    logs.value = rawItems.map((it: any) => {
      return {
        ...it,
        // 保持原始的result_status字段，不需要额外转换
      };
    });
    pagination.total = total;
    pagination.page = page;
    pagination.pageSize = size;
  } catch (err: any) {
    ElMessage.error(err?.message || "加载日志失败");
  } finally {
    loading.value = false;
  }
}

function onSearch() {
  pagination.page = 1;
  loadLogs();
}

function onPageChange(page: number) {
  pagination.page = page;
  loadLogs();
}

function onPageSizeChange(size: number) {
  pagination.pageSize = size;
  pagination.page = 1;
  loadLogs();
}

const detailVisible = ref(false);
const currentDetail = ref<UserOperationLogDetail | null>(null);

async function openDetail(row: UserOperationLog) {
  try {
    const res = await userOperationLogsApi.getLogDetail(row.id);
    const payload = (res as any).data ?? res;
    const flat = payload?.log
      ? {
          ...payload.log,
          ...(payload.detail || {}),
          success: (() => {
            const flag = isSuccessFlag(payload?.log?.success);
            return flag !== undefined
              ? flag
              : payload?.log?.result_status === "success";
          })(),
        }
      : payload || {};
    currentDetail.value = flat;
    detailVisible.value = true;
  } catch (err: any) {
    ElMessage.error(err?.message || "获取详情失败");
  }
}

function resetFilters() {
  filters.search = "";
  filters.module = "";
  filters.method = "";
  filters.path = "";
  filters.status_code = undefined;
  filters.success = undefined;
  dateRange.value = null;
  pagination.page = 1;
  loadLogs();
}

function pretty(obj: any) {
  try {
    if (!obj) return "-";
    return JSON.stringify(obj, null, 2);
  } catch {
    return String(obj);
  }
}

function formatDateTime(v: any) {
  if (!v) return '-'
  const d = dayjs(v)
  return d.isValid() ? d.format('YYYY-MM-DD HH:mm:ss') : String(v)
}

onMounted(loadLogs)
</script>

<style scoped>
.user-operation-logs {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.code-block {
  background: var(--el-color-info-light-9);
  border: 1px solid var(--el-border-color);
  border-radius: 4px;
  padding: 12px;
  white-space: pre-wrap;
  word-break: break-word;
}
.mb-3 { margin-bottom: 12px; }
.mt-3 { margin-top: 12px; }
</style>
