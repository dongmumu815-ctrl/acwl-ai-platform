<template>
  <div class="center-table-query-page">
    <!-- <div class="page-header">
      <h2>资源中心</h2>
      <el-tag :type="packageData?.type === 'sql' ? 'primary' : 'success'">
        {{ packageData?.type === 'sql' ? 'SQL查询' : 'Elasticsearch' }}
      </el-tag>
    </div> 
    -->

    <div
      v-loading="loading"
      :class="['page-content', { 'loading-center': loading }]"
    >
      <!-- 
      <el-card class="package-info-card" v-if="packageData">
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
        <div class="template-info">
          <h4>模板信息</h4>
          <div class="template-details">
            <el-tag type="primary" class="template-tag" size="small">
              类型: {{ packageData.template_type || '未知' }}
            </el-tag>
            <el-tag v-if="packageData.template_id" type="info" class="template-tag" size="small">
              模板ID: {{ packageData.template_id }}
            </el-tag>
          </div>
        </div>
        <div class="base-config">
          <h4>查询配置</h4>
          <div class="config-info">
            <el-descriptions :column="3" size="small">
              <el-descriptions-item label="数据源">{{ getDatasourceName(packageData.datasource_id) }}</el-descriptions-item>
              <el-descriptions-item label="查询类型">{{ packageData.type?.toUpperCase() || '未知' }}</el-descriptions-item>
              <el-descriptions-item label="模板类型">{{ packageData.template_type || '未知' }}</el-descriptions-item>
              <el-descriptions-item label="模板ID">{{ packageData.template_id || '无' }}</el-descriptions-item>
            </el-descriptions>
          </div>
        </div>
      </el-card> 
      -->

      <!-- 查询面板（基于包类型） -->
      <SqlPackageQueryPanel
        v-if="packageData?.type === 'sql' && packageData"
        ref="panelRef"
        :packageData="packageData"
      />
      <EsPackageQueryPanel
        v-else-if="packageData?.type === 'elasticsearch' && packageData"
        ref="panelRef"
        :packageData="packageData"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch, nextTick } from "vue";
import { ElMessage } from "element-plus";
import {
  resourcePackageApi,
  type ResourcePackage
} from "@/api/resourcePackage";
import { datasourceApi } from "@/api/datasource";
import type { DataSource } from "@/types/datasource";
import { getSQLTemplate, type SQLTemplateResponse } from "@/api/sqlQuery";
import { templateApi } from "@/api/template";
import SqlPackageQueryPanel from "@/views/resourcePackage/components/SqlPackageQueryPanel.vue";
import EsPackageQueryPanel from "@/views/resourcePackage/components/EsPackageQueryPanel.vue";

interface ExtendedResourcePackage extends ResourcePackage {
  template_conditions?: any[];
  query?: string;
}

const FIXED_PACKAGE_ID = 2;
const loading = ref(false);
const packageData = ref<ExtendedResourcePackage | null>(null);
const datasources = ref<DataSource[]>([]);
// 子面板引用，用于触发默认查询
const panelRef = ref<any>(null);

const getDatasourceName = computed(() => {
  return (datasourceId: number) => {
    const ds = datasources.value.find((d: DataSource) => d.id === datasourceId);
    return ds ? ds.name : "未知数据源";
  };
});

const getTagStyle = (bg: string) => {
  const hexToRgb = (
    hex: string
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
  const yiq = rgb ? (rgb.r * 299 + rgb.g * 587 + rgb.b * 114) / 1000 : 255;
  const textColor = yiq >= 186 ? "#111" : "#fff";
  return { backgroundColor: bg, color: textColor, borderColor: bg };
};

const loadFixedPackageData = async () => {
  try {
    loading.value = true;
    const response = await resourcePackageApi.get(FIXED_PACKAGE_ID);
    packageData.value =
      response && "data" in response
        ? (response as any).data
        : (response as any);
    if (packageData.value?.template_id && packageData.value?.template_type) {
      await loadTemplateParams();
    }
  } catch (error) {
    console.error("加载资源包详情失败:", error);
    ElMessage.error("加载资源包详情失败");
  } finally {
    loading.value = false;
  }
};

const loadTemplateParams = async () => {
  if (!packageData.value?.template_id || !packageData.value?.template_type)
    return;
  try {
    let templateData: SQLTemplateResponse | any = null;
    if (packageData.value.template_type === "sql") {
      const response = await getSQLTemplate(packageData.value.template_id);
      templateData = response.data;
    } else if (packageData.value.template_type === "elasticsearch") {
      const response = await templateApi.getByType(
        packageData.value.template_id,
        "es"
      );
      templateData = (response as any)?.data || response;
    }
    if (templateData && templateData.config) {
      const conditions = templateData.config.conditions || [];
      const unlockedConditions = conditions.filter(
        (condition: any) => !condition.locked
      );
      const dynamicParams: Record<string, any> = {};
      unlockedConditions.forEach((condition: any) => {
        dynamicParams[condition.name] = condition.default_value || "";
      });
      if (packageData.value) {
        packageData.value.dynamic_params = dynamicParams;
        packageData.value.template_conditions = unlockedConditions;
      }
    }
  } catch (error) {
    console.error("加载模板参数失败:", error);
  }
};

const loadDatasources = async () => {
  try {
    const response = await datasourceApi.getDataSourceList();
    datasources.value = response.data?.items || [];
  } catch (error) {
    console.error("加载数据源列表失败:", error);
  }
};

onMounted(() => {
  loadDatasources();
  loadFixedPackageData();
});

// 包数据加载完成后，自动触发一次查询
watch(packageData, async (val) => {
  if (val) {
    await nextTick();
    try {
      if (val.type === "sql") {
        if (panelRef.value?.handleUserQuery) {
          panelRef.value.handleUserQuery();
        } else if (panelRef.value?.executeQuery) {
          panelRef.value.executeQuery();
        }
      } else if (val.type === "elasticsearch") {
        // 仅在索引就绪后触发查询，避免“缺少索引信息”提示
        if (panelRef.value?.isIndicesReady) {
          panelRef.value?.executeQuery?.();
        } else {
          const unwatch = watch(
            () => panelRef.value?.isIndicesReady,
            (ready) => {
              if (ready) {
                panelRef.value?.executeQuery?.();
                unwatch();
              }
            },
            { immediate: false }
          );
        }
      }
    } catch (e) {
      console.warn("进入资源中心默认查询触发失败:", e);
    }
  }
});
</script>

<style scoped>

.center-table-query-page {
  padding: 10px;
  /* min-height: 100vh; */
  /* height: calc(100vh - 175px); */
  background-color: white;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 20px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.page-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
  /* min-height: calc(100vh - 40px);  */
  height: calc(100vh - 80px);
}

/* 当处于加载状态时，内容居中显示 */
.page-content.loading-center {
  justify-content: center;
  align-items: center;
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
  font-weight: 600;
}

.package-info-card .template-details {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
</style>