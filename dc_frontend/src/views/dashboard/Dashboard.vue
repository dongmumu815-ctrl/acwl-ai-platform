<template>
  <div class="dashboard-container">
    <!-- 欢迎区域 -->
    <div class="welcome-section">
      <div class="welcome-content">
        <h1 class="welcome-title">
          <el-icon><Odometer /></el-icon>
          欢迎使用 CEPIEC 数据中台
        </h1>
        <p class="welcome-subtitle">智能数据管理，助力业务决策</p>
      </div>
      <div class="welcome-actions">
        <!-- <el-button type="primary" size="large" @click="goToDataCenter">
          <el-icon><DataBoard /></el-icon>
          进入数据中心
        </el-button>
        <el-button size="large" @click="viewQuickStart">
          <el-icon><Guide /></el-icon>
          快速开始
        </el-button> -->
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-grid">
      <div v-for="stat in stats" :key="stat.key" class="stat-card">
        <div class="stat-icon" :style="{ backgroundColor: stat.color }">
          <el-icon :size="24">
            <component :is="stat.icon" />
          </el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-label">{{ stat.label }}</div>
          <div class="stat-value">{{ stat.value }}</div>

          <div class="stat-trend" :class="stat.trend.type">
            <!-- <el-icon>
              <component :is="stat.trend.icon" />
            </el-icon>
            <span>{{ stat.trend.value }}</span> -->
          </div>
        </div>
      </div>
    </div>

    <!-- 图表区域 -->
    <div class="charts-section">
      <div class="chart-row">
        <!-- 数据趋势图 -->
        <div class="chart-card">
          <div class="chart-header">
            <h3>数据增长趋势</h3>
            <el-button-group size="small">
              <el-button
                :type="trendPeriod === '7d' ? 'primary' : ''"
                @click="changeTrendPeriod('7d')"
                >7天</el-button
              >
              <el-button
                :type="trendPeriod === '30d' ? 'primary' : ''"
                @click="changeTrendPeriod('30d')"
                >30天</el-button
              >
              <el-button
                :type="trendPeriod === '90d' ? 'primary' : ''"
                @click="changeTrendPeriod('90d')"
                >90天</el-button
              >
            </el-button-group>
          </div>
          <div ref="trendChartRef" class="chart-content">
            <v-chart class="chart" :option="trendChartOption" autoresize />
          </div>
        </div>

        <!-- 数据分布图 -->
        <div class="chart-card">
          <div class="chart-header">
            <h3>数据类型分布</h3>
            <el-button size="small" @click="refreshDistribution">
              <el-icon><Refresh /></el-icon>
            </el-button>
          </div>
          <div ref="distributionChartRef" class="chart-content">
            <v-chart
              class="chart"
              :option="distributionChartOption"
              autoresize
            />
          </div>
        </div>
      </div>
    </div>

    <!-- 快捷操作 -->
    <div class="quick-actions">
      <h3 class="section-title">
        <el-icon><Lightning /></el-icon>
        快捷操作
      </h3>
      <div class="actions-grid">
        <div
          v-for="action in quickActions"
          :key="action.key"
          class="action-item"
          @click="handleAction(action)"
        >
          <div class="action-icon" :style="{ backgroundColor: action.color }">
            <el-icon :size="20">
              <component :is="action.icon" />
            </el-icon>
          </div>
          <div class="action-content">
            <div class="action-title">{{ action.title }}</div>
            <div class="action-desc">{{ action.description }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 最近活动 -->
    <div class="recent-activities">
      <h3 class="section-title">
        <el-icon><Clock /></el-icon>
        最近活动
      </h3>
      <div class="activity-list">
        <div
          v-for="activity in recentActivities"
          :key="activity.id"
          class="activity-item"
        >
          <div
            class="activity-icon"
            :style="{ backgroundColor: activity.color }"
          >
            <el-icon>
              <component :is="activity.icon" />
            </el-icon>
          </div>
          <div class="activity-content">
            <div class="activity-title">{{ activity.title }}</div>
            <div class="activity-time">{{ formatTime(activity.time) }}</div>
          </div>
          <div class="activity-status">
            <el-tag :type="activity.status.type" size="small">{{
              activity.status.text
            }}</el-tag>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick, computed, watch } from "vue";
import { useRouter, useRoute } from "vue-router";
import { ElMessage } from "element-plus";
import {
  getESClusterStats,
  getESDatasources,
  getESAggregations,
  getESIndexStats,
} from "@/api/esQuery";
import { getSystemStats, getTypeCountTrend } from "@/api/apiManagement";
import { useUserStore } from "@/stores/user";
import VChart from "vue-echarts";
import { use } from "echarts/core";
import { CanvasRenderer } from "echarts/renderers";
import { LineChart, BarChart, PieChart } from "echarts/charts";
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
} from "echarts/components";
import {
  userOperationLogsApi,
  type UserOperationLog,
} from "@/api/userOperationLogs";

// 重新注册 ECharts 必需组件，避免页面空白
use([
  CanvasRenderer,
  LineChart,
  BarChart,
  PieChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
]);

const router = useRouter();
const route = useRoute();
const userStore = useUserStore();

// 图表引用
const trendChartRef = ref<HTMLElement>();
const distributionChartRef = ref<HTMLElement>();

// 响应式数据
const trendPeriod = ref("90d");

// 数据增长趋势（动态）
const trendDates = ref<string[]>([]);
const trendSeries = ref<Record<string, number[]>>({});
const trendLoading = ref(false);

// 统计数据
const stats = ref([
  {
    key: "totalData",
    label: "总数据量",
    value: "",
    icon: "DataBoard",
    color: "#409EFF",
    trend: { type: "up", value: "+12.5%", icon: "ArrowUp" },
  },
  {
    key: "activeUsers",
    label: "活跃平台",
    value: "",
    icon: "User",
    color: "#67C23A",
    trend: { type: "up", value: "+8.2%", icon: "ArrowUp" },
  },
  {
    key: "apiCalls",
    label: "API调用",
    value: "",
    icon: "Connection",
    color: "#E6A23C",
    trend: { type: "down", value: "-2.1%", icon: "ArrowDown" },
  },
  {
    key: "storage",
    label: "存储使用",
    value: "",
    icon: "Coin",
    color: "#F56C6C",
    trend: { type: "up", value: "+15.3%", icon: "ArrowUp" },
  },
]);

// ES 集群统计
const esDatasourceId = ref<number | null>(null);
const esClusterStats = ref<any | null>(null);
// 指定用于统计展示的主索引名称
const primaryIndexName = "cpc_dw_publication";

const loadEsClusterStats = async () => {
  try {
    const res = await getESDatasources();
    const list = Array.isArray(res?.data?.items)
      ? res.data.items
      : Array.isArray(res?.data)
        ? res.data
        : [];
    const esList = Array.isArray(list)
      ? list.filter((d: any) => {
          const t = d?.datasource_type || d?.type;
          return t === "elasticsearch" || t === "ELASTICSEARCH";
        })
      : [];
    const first = esList[0] || (Array.isArray(list) ? list[0] : null);
    if (!first) return;
    esDatasourceId.value = first.id;
    const statsRes = await getESClusterStats(first.id);
    const data = statsRes?.data;
    esClusterStats.value = data;

    const formatCount = (n: number) => {
      if (!Number.isFinite(n)) return `${n}`;
      if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
      if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
      return `${n}`;
    };

    const totalDataIdx = stats.value.findIndex((s) => s.key === "totalData");
    if (totalDataIdx >= 0 && data?.indices?.docsCount != null) {
      stats.value[totalDataIdx].value = formatCount(
        Number(data.indices.docsCount),
      );
    }

    const storageIdx = stats.value.findIndex((s) => s.key === "storage");
    if (storageIdx >= 0 && data?.indices?.storeSize) {
      stats.value[storageIdx].value = String(data.indices.storeSize);
    }

    // 使用主索引的统计覆盖展示（与服务器 cat indices 结果一致）
    await loadEsIndexStats(primaryIndexName);
  } catch (e) {
    console.error("加载ES集群统计失败", e);
  }
};

// 加载单个索引统计并更新“总数据量/存储使用”卡片
const loadEsIndexStats = async (indexName: string) => {
  try {
    if (!esDatasourceId.value) return;
    const res = await getESIndexStats(
      esDatasourceId.value as number,
      indexName,
    );
    const data = res?.data;
    if (!data) return;

    const formatCount = (n: number) => {
      if (!Number.isFinite(n)) return `${n}`;
      if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
      if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
      return `${n}`;
    };

    const totalDataIdx = stats.value.findIndex((s) => s.key === "totalData");
    if (totalDataIdx >= 0 && data?.docsCount != null) {
      stats.value[totalDataIdx].value = formatCount(Number(data.docsCount));
    }

    const storageIdx = stats.value.findIndex((s) => s.key === "storage");
    if (storageIdx >= 0 && data?.storeSize) {
      // 直接展示 cat indices 的字符串（例如 27.1gb）
      stats.value[storageIdx].value = String(data.storeSize);
    }
  } catch (e) {
    // 若索引统计失败，保持集群统计的显示作为回退
    console.warn("加载索引统计失败，使用集群统计作为回退", e);
  }
};

const loadSystemStats = async () => {
  try {
    const res = await getSystemStats();
    const data = res?.data;

    const formatCount = (n: number) => {
      if (!Number.isFinite(n)) return `${n}`;
      if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
      if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
      return `${n}`;
    };

    const activeIdx = stats.value.findIndex((s) => s.key === "activeUsers");
    if (activeIdx >= 0 && data?.activeCustomers != null) {
      stats.value[activeIdx].value = formatCount(Number(data.activeCustomers));
    }

    const callsIdx = stats.value.findIndex((s) => s.key === "apiCalls");
    if (callsIdx >= 0 && data?.totalApiCalls != null) {
      stats.value[callsIdx].value = formatCount(Number(data.totalApiCalls));
    }
  } catch (e) {
    console.error("加载系统统计失败", e);
  }
};

// 数据类型分布（ES聚合）
const distributionData = ref<Array<{ name: string; value: number }>>([]);
const distributionLoading = ref(false);

const loadDistribution = async () => {
  try {
    if (!esDatasourceId.value) {
      await loadEsClusterStats();
      if (!esDatasourceId.value) return;
    }
    distributionLoading.value = true;

    // 为避免同时查询别名与通配造成重复计数，仅在两者之间择一尝试
    const indexSets: string[][] = [
      [primaryIndexName],
      [primaryIndexName + "*"],
    ];
    const fieldsToTry = [
      "publication_category",
      "category",
      "publication_type",
    ];

    const ensureKeywordField = (field: string) =>
      field && field.endsWith(".keyword") ? field : `${field}.keyword`;

    const tryAgg = async (field: string) => {
      const rawField = field;
      const keywordField = ensureKeywordField(field);

      const callAggOnIndices = async (
        indices: string[],
        aggField: string,
        existsField: string,
      ) => {
        const res = await getESAggregations(
          esDatasourceId.value as number,
          indices,
          {
            category_terms: {
              terms: {
                field: aggField,
                size: 20,
                order: { _count: "desc" },
                min_doc_count: 1,
              },
            },
          },
          { exists: { field: existsField } },
        );
        const ok = Boolean((res as any)?.success);
        const agg = (res as any)?.data?.aggregations?.category_terms;
        const buckets = Array.isArray(agg?.buckets) ? agg.buckets : [];
        return { ok, buckets };
      };

      // 优先尝试 keyword 子字段，exists 过滤使用原始字段
      let ok = false;
      let buckets: any[] = [];
      // 先尝试主索引；若无数据或失败，再回退到通配索引
      for (const indices of indexSets) {
        // 优先尝试 keyword 子字段，exists 过滤使用原始字段
        const r1 = await callAggOnIndices(indices, keywordField, rawField);
        ok = r1.ok;
        buckets = r1.buckets;
        if (ok && buckets.length > 0) break;
        // 回退尝试原始字段（适配字段本身即为 keyword 的情况）
        const r2 = await callAggOnIndices(indices, rawField, rawField);
        ok = r2.ok;
        buckets = r2.buckets;
        if (ok && buckets.length > 0) break;
      }

      const filtered = Array.isArray(buckets)
        ? buckets.filter((b: any) => String(b.key) !== "未分类")
        : [];
      return filtered.map((b: any) => ({
        name: String(b.key),
        value: Number(b.doc_count),
      }));
    };

    // 尝试多个字段以获取有效聚合结果
    let found: Array<{ name: string; value: number }> = [];
    for (const f of fieldsToTry) {
      const data = await tryAgg(f);
      if (data.length > 0) {
        found = data;
        break;
      }
    }

    distributionData.value = found;
    if (found.length === 0) {
      ElMessage.warning("未获取到数据类型分布，请检查索引/字段配置");
    }
  } catch (e) {
    console.error("加载数据类型分布失败", e);
    ElMessage.error("加载数据类型分布失败");
  } finally {
    distributionLoading.value = false;
  }
};

watch(esDatasourceId, (id) => {
  if (id) loadDistribution();
});

// 加载数据增长趋势（从后端接口）
const loadTypeCountTrend = async () => {
  const dayMap = { "7d": 7, "30d": 30, "90d": 90 };
  trendLoading.value = true;
  try {
    const res = await getTypeCountTrend({
      days: dayMap[trendPeriod.value as "7d" | "30d" | "90d"],
    });
    const data = res?.data;
    trendDates.value = Array.isArray(data?.dates) ? data.dates : [];
    trendSeries.value =
      data?.series && typeof data.series === "object" ? data.series : {};
  } catch (e) {
    console.error("加载数据增长趋势失败", e);
    ElMessage.error("加载数据增长趋势失败");
    trendDates.value = [];
    trendSeries.value = {};
  } finally {
    trendLoading.value = false;
  }
};

onMounted(() => {
  loadEsClusterStats();
  loadSystemStats();
  loadTypeCountTrend();
  loadRecentActivities();
});

// 快捷操作
const quickActions = ref([
  {
    key: "upload",
    title: "字段管理",
    description: "对中心表字段进行管理",
    icon: "Upload",
    color: "#409EFF",
  },
  {
    key: "query",
    title: "数据查询",
    description: "快速查询数据",
    icon: "Search",
    color: "#67C23A",
  },
  {
    key: "export",
    title: "导出报表",
    description: "下载数据资源包",
    icon: "Download",
    color: "#E6A23C",
  },
  {
    key: "settings",
    title: "系统日志",
    description: "日志查询",
    icon: "Setting",
    color: "#909399",
  },
]);

// 最近活动
const recentActivities = ref<Activity[]>([]);
const recentActivitiesLoading = ref(false);

type Activity = {
  id: number;
  title: string;
  time: Date;
  icon: string;
  color: string;
  status: { type: "success" | "danger" | "warning" | "info"; text: string };
};

const statusTypeFromCode = (
  code?: number,
): "success" | "warning" | "danger" | "info" => {
  if (code == null) return "info";
  if (code >= 200 && code < 300) return "success";
  if (code >= 400 && code < 500) return "warning";
  if (code >= 500) return "danger";
  return "info";
};

const statusTextFromType = (
  type: "success" | "warning" | "danger" | "info",
) => {
  switch (type) {
    case "success":
      return "成功";
    case "warning":
      return "警告";
    case "danger":
      return "失败";
    default:
      return "已记录";
  }
};

// 为不同状态类型提供对应的颜色（用于图标背景）
const colorForStatusType = (
  type: "success" | "warning" | "danger" | "info",
) => {
  switch (type) {
    case "success":
      return "#67C23A"; // 绿色
    case "warning":
      return "#E6A23C"; // 橙色
    case "danger":
      return "#F56C6C"; // 红色
    default:
      return "#909399"; // 灰色
  }
};
const iconForLog = (method?: string) => {
  const m = (method || "").toUpperCase();
  if (m === "GET") return "Search";
  if (m === "POST") return "Upload";
  if (m === "PUT" || m === "PATCH") return "Edit";
  if (m === "DELETE") return "Delete";
  return "Connection";
};

const moduleLabelFromPath = (path?: string) => {
  if (!path) return "未知模块";
  const p = path.replace(/^\//, "");
  const parts = p.split("/");
  let key = parts[0];
  if (key === "api" && parts.length >= 3 && parts[1] === "v1") {
    key = parts[2];
  }
  const mapping: Record<string, string> = {
    auth: "用户认证",
    users: "用户管理",
    user_operation_logs: "操作日志",
    "user-operation-logs": "操作日志",
    data_resources: "数据资源",
    "data-resources": "数据资源",
    datasources: "数据源管理",
    templates: "模板管理",
    tags: "标签管理",
    permissions: "权限管理",
    system: "系统管理",
    dashboard: "仪表盘",
    reports: "报表管理",
    analytics: "数据分析",
    settings: "系统设置",
    es: "搜索引擎",
    apis: "接口管理",
    customers: "平台管理",
    logs: "操作日志",
  };
  return mapping[key] || key || "未知模块";
};

const titleForLog = (log: UserOperationLog) => {
  const moduleLabel = moduleLabelFromPath(log.path);
  return moduleLabel;
};

const loadRecentActivities = async () => {
  try {
    recentActivitiesLoading.value = true;
    const res = await userOperationLogsApi.getLogs({ page: 1, size: 4 });
    const paginated = res?.data;
    const items = Array.isArray((paginated as any)?.items)
      ? ((paginated as any).items as UserOperationLog[])
      : [];
    recentActivities.value = items.map((log) => {
      const type = statusTypeFromCode(log.status_code);
      return {
        id: Number(log.id),
        title: titleForLog(log),
        time: log.created_at ? new Date(log.created_at) : new Date(),
        icon: iconForLog(log.method),
        color: colorForStatusType(type),
        status: { type, text: statusTextFromType(type) },
      };
    });
  } catch (e) {
    console.error("加载最近活动失败", e);
  } finally {
    recentActivitiesLoading.value = false;
  }
};

/**
 * 生成静态数据 - 从2025年9月开始的日增量数据
 */

/**
 * 根据时间周期获取数据
 */
const getTrendData = computed(() => {
  const dates = trendDates.value;
  const series = trendSeries.value || {};
  const erpData = series.erp || series.ERP || [];
  const aixueshuData = series["爱学术"] || series.aixueshu || [];
  const processingData = series["资源加工平台"] || series.processing || [];
  return { dates, erpData, aixueshuData, processingData };
});

/**
 * 趋势图表配置
 */
const trendChartOption = computed(() => {
  const data = getTrendData.value;

  return {
    tooltip: {
      trigger: "axis",
      axisPointer: {
        type: "cross",
        label: {
          backgroundColor: "#6a7985",
        },
      },
    },
    legend: {
      data: ["爱学术平台", "资源加工平台"],
      top: 10,
    },
    grid: {
      left: "3%",
      right: "4%",
      bottom: "3%",
      containLabel: true,
    },
    xAxis: [
      {
        type: "category",
        boundaryGap: false,
        data: data.dates,
        axisLabel: {
          rotate: 45,
        },
      },
    ],
    yAxis: [
      {
        type: "value",
        name: "数据增量",
        axisLabel: {
          formatter: "{value}",
        },
      },
    ],
    series: [
      // {
      //   name: 'ERP系统',
      //   type: 'line',
      //   stack: 'Total',
      //   smooth: true,
      //   lineStyle: {
      //     width: 3
      //   },
      //   areaStyle: {
      //     opacity: 0.3
      //   },
      //   emphasis: {
      //     focus: 'series'
      //   },
      //   data: data.erpData,
      //   itemStyle: {
      //     color: '#409EFF'
      //   }
      // },
      {
        name: "爱学术平台",
        type: "bar",
        data: data.aixueshuData,
        itemStyle: {
          color: "#67C23A",
        },
      },
      {
        name: "资源加工平台",
        type: "line",
        smooth: true,
        lineStyle: {
          width: 2,
          type: "dashed",
        },
        emphasis: {
          focus: "series",
        },
        data: data.processingData,
        itemStyle: {
          color: "#E6A23C",
        },
      },
    ],
  };
});

/**
 * 数据分布图表配置
 */
/**
 * 计算数据类型分布的配置
 * @returns {Object} ECharts饼图配置对象
 */
// 英文类型到中文标签的映射
const typeLabelMap: Record<string, string> = {
  BOOK: "图书",
  JOURNAL_ARTICLE: "期刊文章",
  CONFERENCE_PAPER: "会议论文",
  REPORT: "报告",
  THESIS: "学位论文",
  STANDARD: "标准",
  PATENT: "专利",
  OTHER: "其他",
};

// 计算后的中文映射数据（未匹配的保留原值）
const mappedDistributionData = computed(() =>
  (distributionData.value || []).map((d) => ({
    ...d,
    name: typeLabelMap[d.name] || d.name,
  })),
);

const distributionChartOption = computed(() => {
  return {
    title: {
      text: "数据类型分布",
      left: "center",
      textStyle: {
        fontSize: 16,
        fontWeight: "bold",
      },
    },
    tooltip: {
      trigger: "item",
      formatter: "{a} <br/>{b}: {c} ({d}%)",
    },
    legend: {
      orient: "vertical",
      left: "left",
      top: "middle",
    },
    series: [
      {
        name: "数据类型",
        type: "pie",
        radius: ["40%", "70%"],
        center: ["60%", "50%"],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 10,
          borderColor: "#fff",
          borderWidth: 2,
        },
        label: {
          show: false,
          position: "center",
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 20,
            fontWeight: "bold",
          },
        },
        labelLine: {
          show: false,
        },
        data: mappedDistributionData.value,
      },
    ],
  };
});

/**
 * 切换趋势周期
 */
const changeTrendPeriod = (period: string) => {
  trendPeriod.value = period;
  ElMessage.success(
    `已切换到${period === "7d" ? "7天" : period === "30d" ? "30天" : "90天"}视图`,
  );
  loadTypeCountTrend();
};

/**
 * 格式化时间
 */
const formatTime = (time: Date) => {
  const now = new Date();
  const diff = now.getTime() - time.getTime();
  const minutes = Math.floor(diff / (1000 * 60));

  if (minutes < 1) return "刚刚";
  if (minutes < 60) return `${minutes}分钟前`;

  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}小时前`;

  const days = Math.floor(hours / 24);
  return `${days}天前`;
};

/**
 * 跳转到数据中心
 */
const goToDataCenter = () => {
  console.log("=== 跳转数据中心调试信息 ===");
  console.log("当前路由:", route.path);
  console.log("用户权限:", userStore.userPermissions);
  console.log("准备跳转到数据中心页面");
  console.log("目标路由:", "/data-center");
  console.log("========================");
  router.push("/data-center");
};

/**
 * 查看快速开始
 */
const viewQuickStart = () => {
  console.log("=== 快速开始调试信息 ===");
  console.log("当前路由:", route.path);
  console.log("用户信息:", userStore.userInfo);
  console.log("点击快速开始按钮");
  console.log("========================");
  ElMessage.info("快速开始指南即将推出");
};

/**
 * 处理快捷操作
 */
const handleAction = (action: any) => {
  console.log("=== 快捷操作调试信息 ===");
  console.log("点击的操作:", action);
  console.log("操作key:", action.key);
  console.log("操作标题:", action.title);
  console.log("当前路由:", route.path);
  console.log("用户权限:", userStore.userPermissions);
  console.log("========================");

  switch (action.key) {
    case "upload":
      console.log("准备跳转到字段管理页面");
      router.push("/resource-center/table-management");
      ElMessage.success("在该页面可进行字段管理");
      break;
    case "query":
      console.log("准备跳转到数据查询页面");
      router.push("/resource-center/table-query");
      ElMessage.success("在该页面可进行数据查询");
      break;
    case "export":
      console.log("准备跳转到资源包管理页面");
      router.push("/data-resources/packages");
      ElMessage.success("在该页面可进行报表导出");
      break;
    case "settings":
      console.log("准备跳转到系统日志页面");
      router.push("/logs/user-operation-logs");
      ElMessage.info("在该页面可查看系统日志");
      break;
    default:
      console.log("执行默认操作:", action.title);
      ElMessage.info(`执行操作: ${action.title}`);
  }
};

/**
 * 刷新分布图
 */
const refreshDistribution = () => {
  loadDistribution();
  ElMessage.success("数据分布图已刷新");
  // 这里应该重新加载图表数据
};

/**
 * 初始化图表
 */
const initCharts = () => {
  // 这里应该使用实际的图表库（如 ECharts）来初始化图表
  // 由于没有引入图表库，这里只是占位
  console.log("初始化图表");
};

/**
 * 组件挂载时初始化
 */
onMounted(() => {
  nextTick(() => {
    initCharts();
  });
});
</script>

<style lang="scss" scoped>
.dashboard-container {
  padding: 20px;
  background: var(--el-bg-color-page);
  min-height: 100vh;
}

.welcome-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 32px;
  background: linear-gradient(135deg, #409eff 0%, #67c23a 100%);
  border-radius: 12px;
  color: white;
  margin-bottom: 24px;

  .welcome-content {
    .welcome-title {
      display: flex;
      align-items: center;
      font-size: 28px;
      font-weight: 600;
      margin: 0 0 8px 0;

      .el-icon {
        margin-right: 12px;
      }
    }

    .welcome-subtitle {
      font-size: 16px;
      opacity: 0.9;
      margin: 0;
    }
  }

  .welcome-actions {
    display: flex;
    gap: 12px;
  }
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin-bottom: 24px;

  .stat-card {
    display: flex;
    align-items: center;
    padding: 24px;
    background: var(--el-bg-color);
    border-radius: 8px;
    border: 1px solid var(--el-border-color-light);
    transition: all 0.3s;

    &:hover {
      transform: translateY(-2px);
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    }

    .stat-icon {
      width: 48px;
      height: 48px;
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      color: white;
      margin-right: 16px;
    }

    .stat-content {
      flex: 1;

      .stat-value {
        font-size: 24px;
        font-weight: 600;
        color: var(--el-text-color-primary);
        margin-bottom: 4px;
      }

      .stat-label {
        font-size: 14px;
        color: var(--el-text-color-secondary);
        margin-bottom: 8px;
      }

      .stat-trend {
        display: flex;
        align-items: center;
        font-size: 12px;

        &.up {
          color: var(--el-color-success);
        }

        &.down {
          color: var(--el-color-danger);
        }

        .el-icon {
          margin-right: 4px;
        }
      }
    }
  }
}

.charts-section {
  margin-bottom: 24px;

  .chart-row {
    display: grid;
    grid-template-columns: 2fr 1fr;
    gap: 20px;

    .chart-card {
      background: var(--el-bg-color);
      border-radius: 8px;
      border: 1px solid var(--el-border-color-light);
      overflow: hidden;

      .chart-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 20px 24px 16px;
        border-bottom: 1px solid var(--el-border-color-light);

        h3 {
          margin: 0;
          font-size: 16px;
          font-weight: 600;
          color: var(--el-text-color-primary);
        }
      }

      .chart-content {
        height: 300px;
        padding: 20px;

        .chart {
          width: 100%;
          height: 100%;
        }
      }
    }
  }
}

.quick-actions,
.recent-activities {
  background: var(--el-bg-color);
  border-radius: 8px;
  border: 1px solid var(--el-border-color-light);
  padding: 24px;
  margin-bottom: 24px;

  .section-title {
    display: flex;
    align-items: center;
    font-size: 18px;
    font-weight: 600;
    color: var(--el-text-color-primary);
    margin: 0 0 20px 0;

    .el-icon {
      margin-right: 8px;
      color: var(--el-color-primary);
    }
  }
}

.actions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;

  .action-item {
    display: flex;
    align-items: center;
    padding: 16px;
    border: 1px solid var(--el-border-color-light);
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.3s;

    &:hover {
      border-color: var(--el-color-primary);
      background: var(--el-color-primary-light-9);
    }

    .action-icon {
      width: 40px;
      height: 40px;
      border-radius: 6px;
      display: flex;
      align-items: center;
      justify-content: center;
      color: white;
      margin-right: 12px;
    }

    .action-content {
      .action-title {
        font-size: 14px;
        font-weight: 500;
        color: var(--el-text-color-primary);
        margin-bottom: 4px;
      }

      .action-desc {
        font-size: 12px;
        color: var(--el-text-color-secondary);
      }
    }
  }
}

.activity-list {
  .activity-item {
    display: flex;
    align-items: center;
    padding: 12px 0;
    border-bottom: 1px solid var(--el-border-color-lighter);

    &:last-child {
      border-bottom: none;
    }

    .activity-icon {
      width: 32px;
      height: 32px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      color: white;
      margin-right: 12px;
    }

    .activity-content {
      flex: 1;

      .activity-title {
        font-size: 14px;
        color: var(--el-text-color-primary);
        margin-bottom: 4px;
      }

      .activity-time {
        font-size: 12px;
        color: var(--el-text-color-secondary);
      }
    }
  }
}

// 响应式设计
@media (max-width: 768px) {
  .dashboard-container {
    padding: 16px;
  }

  .welcome-section {
    flex-direction: column;
    text-align: center;
    gap: 20px;

    .welcome-actions {
      justify-content: center;
    }
  }

  .charts-section .chart-row {
    grid-template-columns: 1fr;
  }

  .stats-grid {
    grid-template-columns: 1fr;
  }

  .actions-grid {
    grid-template-columns: 1fr;
  }
}
</style>
