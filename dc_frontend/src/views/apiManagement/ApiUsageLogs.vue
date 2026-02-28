<template>
  <div class="api-usage-logs">
    <div class="page-header">
      <div class="header-content">
        <div class="header-left">
          <h1 class="page-title">
            <el-icon><Document /></el-icon>
            API使用日志
          </h1>
          <p class="page-description">查看并筛选指定API的调用日志</p>
        </div>
        <div class="header-right">
          <el-button @click="goBack">
            <el-icon><Back /></el-icon>
            返回
          </el-button>
          <el-button @click="loadLogs">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </div>
    </div>

    <el-card shadow="never" class="filter-card">
      <el-form inline>
        <el-form-item label="状态码">
          <el-input-number
            v-model="filters.status_code"
            :min="100"
            :max="599"
            controls-position="right"
            placeholder="HTTP状态码"
          />
        </el-form-item>
        <el-form-item label="搜索">
          <el-input
            v-model="filters.search"
            placeholder="搜索请求/响应/错误"
            clearable
            style="width: 280px"
          />
        </el-form-item>
        <el-form-item label="时间范围">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="applyFilters">
            <el-icon><Search /></el-icon>
            查询
          </el-button>
          <el-button @click="resetFilters"> 重置 </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <div class="page-card">
      <div class="card-header">
        <h3>日志列表</h3>
        <div class="list-actions">
          <span class="total">共 {{ pagination.total }} 条</span>
        </div>
      </div>
      <el-table v-loading="loading" :data="logs" style="width: 100%">
        <el-table-column prop="created_at" label="时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="status_code" label="状态码" width="110">
          <template #default="{ row }">
            <el-tag :type="getStatusTagType(row.status_code)" size="small">{{
              row.status_code
            }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="response_time" label="耗时(ms)" width="110" />
        <el-table-column prop="ip_address" label="IP" width="150" />
        <el-table-column prop="customer" label="客户" width="180">
          <template #default="{ row }">
            {{ row.customer?.name || "-" }}
          </template>
        </el-table-column>
        <el-table-column prop="api" label="API" width="220">
          <template #default="{ row }">
            {{ row.api?.api_name || "-" }} ({{ row.api?.api_code || "-" }})
          </template>
        </el-table-column>
        <el-table-column
          prop="error_message"
          label="错误"
          min-width="220"
          show-overflow-tooltip
        />
        <el-table-column
          prop="request_data"
          label="请求数据"
          min-width="240"
          show-overflow-tooltip
        />
        <el-table-column
          prop="response_data"
          label="响应数据"
          min-width="240"
          show-overflow-tooltip
        />
      </el-table>
      <div class="pagination">
        <el-pagination
          background
          layout="prev, pager, next"
          :total="pagination.total"
          :page-size="pagination.pageSize"
          :current-page="pagination.page"
          @current-change="handlePageChange"
        />
      </div>
      <div v-if="logs.length === 0 && !loading" class="empty-logs">
        <el-empty description="暂无日志记录" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { getApiUsageLogs } from "@/api/apiManagement";
import type { ApiUsageLog, PaginatedResponse } from "@/types/apiManagement";

const route = useRoute();
const router = useRouter();
const apiId = Number(route.params.id);

const loading = ref(false);
const logs = ref<ApiUsageLog[]>([]);
const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0,
});

const filters = reactive<{
  status_code?: number;
  search?: string;
  start_date?: string;
  end_date?: string;
}>({});
const dateRange = ref<string[] | null>(null);

const formatDate = (iso?: string) => {
  if (!iso) return "-";
  const d = new Date(iso);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")} ${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}:${String(d.getSeconds()).padStart(2, "0")}`;
};

const getStatusTagType = (code?: number) => {
  if (!code) return "info";
  if (code >= 200 && code < 300) return "success";
  if (code >= 400 && code < 500) return "warning";
  if (code >= 500) return "danger";
  return "info";
};

const loadLogs = async () => {
  try {
    loading.value = true;
    const params: any = {
      page: pagination.page,
      page_size: pagination.pageSize,
      api_id: apiId,
    };
    if (filters.status_code) params.status_code = filters.status_code;
    if (filters.search) params.search = filters.search;
    if (dateRange.value && dateRange.value.length === 2) {
      params.start_date = dateRange.value[0];
      params.end_date = dateRange.value[1];
    }

    const response = await getApiUsageLogs(params);
    if (response.success) {
      const data = response.data as PaginatedResponse<ApiUsageLog>;
      logs.value = data.items;
      pagination.total = data.total;
      pagination.page = data.page;
      pagination.pageSize = data.page_size || pagination.pageSize;
    } else {
      ElMessage.error(response.message || "加载日志失败");
    }
  } catch (error) {
    console.error("加载API使用日志失败:", error);
  } finally {
    loading.value = false;
  }
};

const handlePageChange = (page: number) => {
  pagination.page = page;
  loadLogs();
};

const applyFilters = () => {
  pagination.page = 1;
  loadLogs();
};

const resetFilters = () => {
  filters.status_code = undefined;
  filters.search = "";
  dateRange.value = null;
  applyFilters();
};

const goBack = () => {
  router.push("/api-management/apis");
};

onMounted(() => {
  loadLogs();
});
</script>

<style scoped>
.api-usage-logs .page-header {
  margin-bottom: 16px;
}
.page-title {
  display: flex;
  align-items: center;
  gap: 8px;
}
.filter-card {
  margin-bottom: 16px;
}
.page-card {
  background: var(--el-bg-color);
  padding: 16px;
  border-radius: 8px;
}
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}
.list-actions .total {
  color: var(--el-text-color-secondary);
}
.pagination {
  display: flex;
  justify-content: flex-end;
  padding: 12px 0;
}
.empty-logs {
  padding: 24px 0;
}
</style>
