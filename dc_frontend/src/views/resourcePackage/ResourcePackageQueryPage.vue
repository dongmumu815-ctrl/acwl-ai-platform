<template>
  <div class="resource-package-query-page">
    <!-- 页面标题 -->
    <!-- <div class="page-header">
      <div class="header-left">
        <el-button @click="goBack" type="text" class="back-button">
          <el-icon><ArrowLeft /></el-icon>
          返回列表
        </el-button>
        <div class="title-section">
          <h2>{{ packageData?.name || '资源包查询' }}</h2>
          <p class="page-description">{{ packageData?.description || '执行资源包查询操作' }}</p>
        </div>
      </div>
      <div class="header-right">
        <el-tag :type="packageData?.type === 'sql' ? 'primary' : 'success'" size="large">
          {{ packageData?.type === 'sql' ? 'SQL查询' : 'Elasticsearch' }}
        </el-tag>
      </div>
    </div> -->

    <div v-loading="loading" class="page-content">
      <!-- 资源包信息卡片 -->
      <el-card v-if="packageData" class="package-info-card">
        <template #header>
          <div class="card-header">
            <span class="card-title">资源包信息</span>
            <div class="package-tags">
              <el-tag
                v-for="tag in packageData.tags"
                :key="tag.tag_name"
                class="tag-item"
                size="small"
                :style="getTagStyle(tag.tag_color)"
              >
                {{ tag.tag_name }}
              </el-tag>
            </div>
          </div>
        </template>

        <!-- 基础配置信息 -->
        <div class="base-config">
          <div class="config-info">
            <el-descriptions :column="4">
              <el-descriptions-item label="数据源：">{{
                getDatasourceName(packageData.datasource_id)
              }}</el-descriptions-item>
              <el-descriptions-item label="查询类型：">{{
                packageData.type?.toUpperCase() || "未知"
              }}</el-descriptions-item>
              <el-descriptions-item label="模板类型：">{{
                packageData.template_type || "未知"
              }}</el-descriptions-item>
              <el-descriptions-item label="模板ID：">{{
                packageData.template_id || "无"
              }}</el-descriptions-item>
            </el-descriptions>
          </div>
        </div>
      </el-card>

      <!-- 调试信息 -->
      <!-- <el-card class="debug-info-card" v-if="packageData" style="margin-bottom: 20px; border: 2px dashed #409eff;">
        <template #header>
          <span class="card-title" style="color: #409eff;">🐛 调试信息</span>
        </template>
        <div style="font-family: monospace; font-size: 12px;">
          <p><strong>资源包ID:</strong> {{ route.params.id }}</p>
          <p><strong>资源包数据:</strong> {{ packageData ? '已加载' : '未加载' }}</p>
          <p><strong>模板类型:</strong> {{ packageData?.template_type || '未知' }}</p>
          <p><strong>模板ID:</strong> {{ packageData?.template_id || '无' }}</p>
          <p><strong>动态参数:</strong> {{ packageData?.dynamic_params ? `存在 (${Object.keys(packageData.dynamic_params).length} 个)` : '不存在' }}</p>
          <div v-if="packageData?.dynamic_params && Object.keys(packageData.dynamic_params).length">
            <p><strong>参数详情:</strong></p>
            <ul style="margin: 0; padding-left: 20px;">
              <li v-for="(value, key) in packageData.dynamic_params" :key="key" style="margin: 5px 0;">
                参数: {{ key }} = {{ value }}
              </li>
            </ul>
          </div>
        </div>
      </el-card> -->

      <!-- 基于查询类型渲染组件 -->
      <SqlPackageQueryPanel
        v-if="packageData?.type === 'sql' && packageData"
        :package-data="packageData"
      />
      <EsPackageQueryPanel
        v-else-if="packageData?.type === 'elasticsearch' && packageData"
        :package-data="packageData"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { ArrowLeft } from "@element-plus/icons-vue";
import {
  resourcePackageApi,
  type ResourcePackage,
} from "@/api/resourcePackage";
import { datasourceApi } from "@/api/datasource";
import { type DataSource } from "@/types/datasource";
import { getSQLTemplate, type SQLTemplateResponse } from "@/api/sqlQuery";
import { templateApi } from "@/api/template";
import SqlPackageQueryPanel from "@/views/resourcePackage/components/SqlPackageQueryPanel.vue";
import EsPackageQueryPanel from "@/views/resourcePackage/components/EsPackageQueryPanel.vue";

// 扩展ResourcePackage接口以包含模板条件
interface ExtendedResourcePackage extends ResourcePackage {
  template_conditions?: any[];
  query?: string;
}

/**
 * 路由和导航
 */
const route = useRoute();
const router = useRouter();

/**
 * 响应式数据
 */
const loading = ref(false);
const packageData = ref<ExtendedResourcePackage | null>(null);
const datasources = ref<DataSource[]>([]);
// 查询相关状态交由子组件管理

// 表单验证规则交由子组件管理

/**
 * 计算属性
 */
// 查询结果相关计算由子组件管理

const getDatasourceName = computed(() => {
  return (datasourceId: number) => {
    const ds = datasources.value.find((d: DataSource) => d.id === datasourceId);
    return ds ? ds.name : "未知数据源";
  };
});

// 计算标签的可读文本颜色，避免文字与背景同色
const getTagStyle = (bg: string) => {
  const hexToRgb = (
    hex: string,
  ): { r: number; g: number; b: number } | null => {
    try {
      let h = hex.trim();
      if (h.startsWith("#")) h = h.slice(1);
      if (h.length === 3) {
        h = h
          .split("")
          .map((c) => c + c)
          .join("");
      }
      if (h.length !== 6) return null;
      const r = parseInt(h.slice(0, 2), 16);
      const g = parseInt(h.slice(2, 4), 16);
      const b = parseInt(h.slice(4, 6), 16);
      return { r, g, b };
    } catch {
      return null;
    }
  };
  const rgb = hexToRgb(bg);
  // YIQ 对比度算法：数值越大越亮
  const yiq = rgb ? (rgb.r * 299 + rgb.g * 587 + rgb.b * 114) / 1000 : 255;
  const textColor = yiq >= 186 ? "#111" : "#fff";
  return {
    backgroundColor: bg,
    color: textColor,
    borderColor: bg,
  };
};

// 条件标签与信息交由子组件处理

/**
 * 方法定义
 */
// 表单交互由子组件处理

/**
 * 返回列表页面
 */
const goBack = () => {
  router.push("/data-resources/packages");
};

/**
 * 加载资源包详情
 */
const loadPackageData = async () => {
  const packageId = route.params.id as string;
  console.log("📦 开始加载资源包详情, ID:", packageId);

  if (!packageId) {
    console.error("❌ 资源包ID为空");
    ElMessage.error("资源包ID不能为空");
    goBack();
    return;
  }

  try {
    loading.value = true;
    console.log("🔄 正在请求资源包API...");
    const response = await resourcePackageApi.get(Number(packageId));
    console.log("✅ API响应:", response);

    // 检查响应格式并提取数据
    if (response && typeof response === "object" && "data" in response) {
      // 如果是ApiResponse格式，提取data字段
      packageData.value = response.data;
      console.log(
        "✅ 资源包数据加载成功 (从response.data):",
        packageData.value,
      );
    } else {
      // 如果直接是数据对象
      packageData.value = response as any;
      console.log(
        "✅ 资源包数据加载成功 (直接使用response):",
        packageData.value,
      );
    }

    console.log("🔍 资源包数据:", packageData.value);
    console.log("🔍 模板ID:", packageData.value?.template_id);
    console.log("🔍 模板类型:", packageData.value?.template_type);

    // 如果有模板信息，加载参数配置
    if (packageData.value?.template_id && packageData.value?.template_type) {
      console.log("✅ 满足模板加载条件，开始加载模板参数...");
      await loadTemplateParams();
    } else {
      console.warn("⚠️ 不满足模板加载条件:", {
        template_id: packageData.value?.template_id,
        template_type: packageData.value?.template_type,
      });
    }

    // 查询表单初始化由子组件管理
  } catch (error) {
    console.error("❌ 加载资源包详情失败:", error);
    ElMessage.error("加载资源包详情失败");
    goBack();
  } finally {
    loading.value = false;
  }
};

/**
 * 根据模板类型加载参数配置
 */
const loadTemplateParams = async () => {
  if (!packageData.value?.template_id || !packageData.value?.template_type) {
    console.warn("模板ID或类型不存在，无法加载参数");
    return;
  }

  try {
    console.log(
      "🔄 开始加载模板参数，模板ID:",
      packageData.value.template_id,
      "类型:",
      packageData.value.template_type,
    );

    let templateData: SQLTemplateResponse | any = null;

    if (packageData.value.template_type === "sql") {
      // 调用SQL模板API
      const response = await getSQLTemplate(packageData.value.template_id);
      templateData = response.data;
    } else if (packageData.value.template_type === "elasticsearch") {
      // 调用ES模板API
      const response = await templateApi.getByType(
        packageData.value.template_id,
        "es",
      );
      templateData = (response as any)?.data || response;
    }

    if (templateData && templateData.config) {
      console.log("✅ 模板参数加载成功:", templateData.config);
      // 从模板配置中解析条件参数，过滤掉锁定的条件
      const conditions = templateData.config.conditions || [];
      const unlockedConditions = conditions.filter(
        (condition: any) => !condition.locked,
      );

      // 将未锁定的条件转换为动态参数格式
      const dynamicParams: Record<string, any> = {};
      unlockedConditions.forEach((condition: any) => {
        dynamicParams[condition.name] = condition.default_value || "";
      });

      if (packageData.value) {
        packageData.value.dynamic_params = dynamicParams;
        packageData.value.template_conditions = unlockedConditions;
      }
    } else {
      console.warn("⚠️ 模板配置中没有找到参数信息");
    }
  } catch (error) {
    console.error("❌ 加载模板参数失败:", error);
  }
};

/**
 * 加载数据源列表
 */
const loadDatasources = async () => {
  try {
    console.log("🔄 开始加载数据源列表...");
    const response = await datasourceApi.getDataSourceList();
    datasources.value = response.data?.items || [];
    console.log("✅ 数据源列表加载成功:", datasources.value);
  } catch (error) {
    console.error("❌ 加载数据源列表失败:", error);
  }
};

// 初始化查询表单交由子组件管理

// 表单重置与主动查询由子组件管理

// 查询执行由子组件管理

// 分页处理由子组件管理

// 导出功能由子组件管理

/**
 * 生命周期
 */
onMounted(() => {
  console.log("🔄 ResourcePackageQueryPage 组件已挂载");
  console.log("📍 当前路由参数:", route.params);
  loadDatasources();
  loadPackageData();
});

// 监听路由参数变化
watch(
  () => route.params.id,
  () => {
    console.log("🔄 路由参数变化:", route.params.id);
    if (route.params.id) {
      loadPackageData();
    }
  },
);
</script>

<style scoped lang="scss">
.resource-package-query-page {
  padding: 13px;
  min-height: 100vh;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
  padding: 20px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.header-left {
  display: flex;
  align-items: flex-start;
  gap: 16px;
}

.back-button {
  padding: 8px;
  font-size: 16px;
  color: #606266;
}

.back-button:hover {
  color: #409eff;
}

.title-section h2 {
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

.header-right {
  display: flex;
  align-items: center;
}

.page-content {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.package-info-card,
.query-form-card,
.query-options-card,
.query-results-card {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  font-weight: 600;
  color: #303133;
  font-size: 16px;
}

.package-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.tag-item {
  margin: 0;
}

.locked-conditions,
.base-config {
  margin-top: 12px;
}

.locked-conditions h4,
.base-config h4,
.template-info h4 {
  margin: 0 0 8px 0;
  color: #303133;
  font-size: 13px;
  font-weight: 600;
}

.condition-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.condition-tag {
  margin: 0;
}

.config-info {
  margin-top: 6px;
}

.query-form {
  padding: 0;
}

.condition-info {
  margin-top: 4px;
}

.query-actions {
  display: flex;
  gap: 12px;
}

.results-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.results-meta {
  display: flex;
  gap: 16px;
  align-items: center;
}

.pagination-wrapper {
  margin-top: 16px;
  text-align: center;
}

.no-data {
  text-align: center;
  padding: 40px;
}

:deep(.el-card__header) {
  padding: 12px 16px;
  border-bottom: 1px solid #e4e7ed;
}

:deep(.el-card__body) {
  padding: 14px;
}

:deep(.el-form-item) {
  margin-bottom: 18px;
}

:deep(.el-input-number) {
  width: 100%;
}

:deep(.el-table) {
  font-size: 12px;
}

:deep(.el-table th) {
  background-color: #fafafa;
}

:deep(.el-descriptions__label) {
  // font-weight: 600;
}

.package-info-card .template-details {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.package-info-card {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
  padding: 5px;

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    .card-title {
      font-size: 16px;
      font-weight: 600;
      color: #303133;
    }
    .package-tags {
      display: flex;
      gap: 6px;
    }
  }

  .info-section {
    margin-top: 16px;

    .section-title {
      font-size: 14px;
      font-weight: 600;
      color: #409eff;
      margin-bottom: 8px;
      border-left: 3px solid #409eff;
      padding-left: 8px;
    }

    .section-content {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }

    .config-descriptions {
      background: #fafafa;
      border-radius: 6px;
      padding: 8px 12px;
    }
  }
}
</style>
