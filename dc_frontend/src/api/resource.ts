/**
 * 数据资源相关的API接口
 */

import { request } from "@/utils/request";
import type {
  DataResource,
  ResourceCategory,
  ResourceField,
  ResourceQuery,
  ResourceCreateData,
  ResourceUpdateData,
  ResourceTestConnection,
  ResourceSyncData,
  ResourcePreviewData,
  ResourceAccessRecord,
  ResourcePermission,
  ResourceTag,
  ResourceVersion,
  ResourceBackup,
  ResourceMetrics,
  ResourceValidation,
  ResourceTemplate,
  ResourceImportData,
  ResourceExportData,
  ResourceBatchOperation,
  ResourceResponse,
  PaginatedResourceResponse,
} from "@/types/resource";

// 数据资源基础API

/**
 * 获取数据资源列表
 */
export const getResources = (
  params: ResourceQuery,
): Promise<PaginatedResourceResponse<DataResource>> => {
  return request({
    url: "/api/resources",
    method: "get",
    params,
    permission: "data:resource:view",
  });
};

/**
 * 获取数据资源详情
 */
export const getResourceById = (
  id: string,
): Promise<ResourceResponse<DataResource>> => {
  return request({
    url: `/api/resources/${id}`,
    method: "get",
    permission: "data:resource:view",
  });
};

/**
 * 创建数据资源
 */
export const createResource = (
  data: ResourceCreateData,
): Promise<ResourceResponse<DataResource>> => {
  return request({
    url: "/api/resources",
    method: "post",
    data,
    permission: "data:resource:create",
  });
};

/**
 * 更新数据资源
 */
export const updateResource = (
  id: string,
  data: ResourceUpdateData,
): Promise<ResourceResponse<DataResource>> => {
  return request({
    url: `/api/resources/${id}`,
    method: "put",
    data,
    permission: "data:resource:edit",
  });
};

/**
 * 删除数据资源
 */
export const deleteResource = (id: string): Promise<ResourceResponse<void>> => {
  return request({
    url: `/api/resources/${id}`,
    method: "delete",
    permission: "data:resource:delete",
  });
};

/**
 * 批量删除数据资源
 */
export const batchDeleteResources = (
  ids: string[],
): Promise<ResourceResponse<void>> => {
  return request({
    url: "/api/resources/batch-delete",
    method: "post",
    data: { ids },
    permission: "data:resource:delete",
  });
};

/**
 * 复制数据资源
 */
export const copyResource = (
  id: string,
  data: { name: string; description?: string },
): Promise<ResourceResponse<DataResource>> => {
  return request({
    url: `/api/resources/${id}/copy`,
    method: "post",
    data,
    permission: "data:resource:create",
  });
};

/**
 * 启用/禁用数据资源
 */
export const toggleResource = (
  id: string,
  enabled: boolean,
): Promise<ResourceResponse<void>> => {
  return request({
    url: `/api/resources/${id}/toggle`,
    method: "patch",
    data: { enabled },
    permission: "data:resource:edit",
  });
};

// 连接测试相关API

/**
 * 测试数据资源连接
 */
export const testConnection = (
  data: ResourceTestConnection,
): Promise<
  ResourceResponse<{ success: boolean; message: string; details?: any }>
> => {
  return request({
    url: "/api/resources/test-connection",
    method: "post",
    data,
    permission: "data:resource:test",
  });
};

/**
 * 测试现有资源连接
 */
export const testResourceConnection = (
  id: string,
): Promise<
  ResourceResponse<{ success: boolean; message: string; details?: any }>
> => {
  return request({
    url: `/api/resources/${id}/test-connection`,
    method: "post",
    permission: "data:resource:test",
  });
};

// 数据同步相关API

/**
 * 同步数据资源结构
 */
export const syncResourceStructure = (
  id: string,
  data?: ResourceSyncData,
): Promise<
  ResourceResponse<{ success: boolean; message: string; changes?: any }>
> => {
  return request({
    url: `/api/resources/${id}/sync`,
    method: "post",
    data,
    permission: "data:resource:sync",
  });
};

/**
 * 获取同步历史
 */
export const getSyncHistory = (
  id: string,
  params?: { page?: number; size?: number },
): Promise<PaginatedResourceResponse<any>> => {
  return request({
    url: `/api/resources/${id}/sync-history`,
    method: "get",
    params,
    permission: "data:resource:sync:view",
  });
};

/**
 * 获取同步状态
 */
export const getSyncStatus = (
  id: string,
): Promise<
  ResourceResponse<{ status: string; progress?: number; message?: string }>
> => {
  return request({
    url: `/api/resources/${id}/sync-status`,
    method: "get",
    permission: "data:resource:sync:view",
  });
};

// 数据预览相关API

/**
 * 预览数据资源数据
 */
export const previewResourceData = (
  id: string,
  params?: {
    table?: string;
    limit?: number;
    offset?: number;
    filters?: Record<string, any>;
  },
): Promise<ResourceResponse<ResourcePreviewData>> => {
  return request({
    url: `/api/resources/${id}/preview`,
    method: "get",
    params,
    permission: "data:resource:preview",
  });
};

/**
 * 查询数据资源数据
 */
export const queryResourceData = (
  id: string,
  data: {
    sql?: string;
    table?: string;
    fields?: string[];
    filters?: Record<string, any>;
    orderBy?: string;
    limit?: number;
    offset?: number;
  },
): Promise<ResourceResponse<ResourcePreviewData>> => {
  return request({
    url: `/api/resources/${id}/query`,
    method: "post",
    data,
    permission: "data:resource:query",
  });
};

// 字段结构相关API

/**
 * 获取资源字段结构
 */
export const getResourceFields = (
  id: string,
  table?: string,
): Promise<ResourceResponse<ResourceField[]>> => {
  return request({
    url: `/data-resources/${id}/schema`,
    method: "get",
    params: { table },
    permission: "data:resource:fields:view",
  });
};

/**
 * 更新字段描述
 */
export const updateFieldDescription = (
  id: string,
  fieldId: string,
  description: string,
): Promise<ResourceResponse<void>> => {
  return request({
    url: `/api/resources/${id}/fields/${fieldId}`,
    method: "patch",
    data: { description },
    permission: "data:resource:fields:edit",
  });
};

/**
 * 批量更新字段描述
 */
export const batchUpdateFieldDescriptions = (
  id: string,
  fields: { fieldId: string; description: string }[],
): Promise<ResourceResponse<void>> => {
  return request({
    url: `/api/resources/${id}/fields/batch-update`,
    method: "patch",
    data: { fields },
    permission: "data:resource:fields:edit",
  });
};

// 访问记录相关API

/**
 * 获取资源访问记录
 */
export const getResourceAccessRecords = (
  id: string,
  params?: {
    page?: number;
    size?: number;
    startDate?: string;
    endDate?: string;
    userId?: string;
    operation?: string;
  },
): Promise<PaginatedResourceResponse<ResourceAccessRecord>> => {
  return request({
    url: `/api/resources/${id}/access-records`,
    method: "get",
    params,
    permission: "data:resource:logs:view",
  });
};

/**
 * 记录资源访问
 */
export const recordResourceAccess = (
  id: string,
  data: {
    operation: string;
    details?: any;
    ip?: string;
    userAgent?: string;
  },
): Promise<ResourceResponse<void>> => {
  return request({
    url: `/api/resources/${id}/access`,
    method: "post",
    data,
    permission: "data:resource:logs:create",
  });
};

// 权限管理相关API

/**
 * 获取资源权限列表
 */
export const getResourcePermissions = (
  id: string,
): Promise<ResourceResponse<ResourcePermission[]>> => {
  return request({
    url: `/api/resources/${id}/permissions`,
    method: "get",
    permission: "data:resource:permission:view",
  });
};

/**
 * 添加资源权限
 */
export const addResourcePermission = (
  id: string,
  data: {
    userId?: string;
    roleId?: string;
    permissions: string[];
  },
): Promise<ResourceResponse<ResourcePermission>> => {
  return request({
    url: `/api/resources/${id}/permissions`,
    method: "post",
    data,
    permission: "data:resource:permission:grant",
  });
};

/**
 * 更新资源权限
 */
export const updateResourcePermission = (
  id: string,
  permissionId: string,
  data: {
    permissions: string[];
  },
): Promise<ResourceResponse<ResourcePermission>> => {
  return request({
    url: `/api/resources/${id}/permissions/${permissionId}`,
    method: "put",
    data,
    permission: "data:resource:permission:edit",
  });
};

/**
 * 删除资源权限
 */
export const deleteResourcePermission = (
  id: string,
  permissionId: string,
): Promise<ResourceResponse<void>> => {
  return request({
    url: `/api/resources/${id}/permissions/${permissionId}`,
    method: "delete",
    permission: "data:resource:permission:revoke",
  });
};

/**
 * 检查用户对资源的权限
 */
export const checkResourcePermission = (
  id: string,
  permission: string,
): Promise<ResourceResponse<{ hasPermission: boolean }>> => {
  return request({
    url: `/api/resources/${id}/check-permission`,
    method: "get",
    params: { permission },
    permission: "data:resource:permission:check",
  });
};

// 标签管理相关API

/**
 * 获取资源标签
 */
export const getResourceTags = (
  id: string,
): Promise<ResourceResponse<ResourceTag[]>> => {
  return request({
    url: `/api/resources/${id}/tags`,
    method: "get",
    permission: "data:resource:tags:view",
  });
};

/**
 * 添加资源标签
 */
export const addResourceTags = (
  id: string,
  tags: string[],
): Promise<ResourceResponse<void>> => {
  return request({
    url: `/api/resources/${id}/tags`,
    method: "post",
    data: { tags },
    permission: "data:resource:tags:edit",
  });
};

/**
 * 删除资源标签
 */
export const removeResourceTags = (
  id: string,
  tags: string[],
): Promise<ResourceResponse<void>> => {
  return request({
    url: `/api/resources/${id}/tags`,
    method: "delete",
    data: { tags },
    permission: "data:resource:tags:edit",
  });
};

/**
 * 获取所有可用标签
 */
export const getAvailableTags = (): Promise<
  ResourceResponse<ResourceTag[]>
> => {
  return request({
    url: "/api/resources/tags",
    method: "get",
    permission: "data:resource:tags:view",
  });
};

// 版本管理相关API

/**
 * 获取资源版本列表
 */
export const getResourceVersions = (
  id: string,
): Promise<ResourceResponse<ResourceVersion[]>> => {
  return request({
    url: `/api/resources/${id}/versions`,
    method: "get",
    permission: "data:resource:version:view",
  });
};

/**
 * 创建资源版本
 */
export const createResourceVersion = (
  id: string,
  data: {
    version: string;
    description?: string;
    changes?: string;
  },
): Promise<ResourceResponse<ResourceVersion>> => {
  return request({
    url: `/api/resources/${id}/versions`,
    method: "post",
    data,
    permission: "data:resource:version:create",
  });
};

/**
 * 恢复到指定版本
 */
export const restoreResourceVersion = (
  id: string,
  versionId: string,
): Promise<ResourceResponse<void>> => {
  return request({
    url: `/api/resources/${id}/versions/${versionId}/restore`,
    method: "post",
    permission: "data:resource:version:restore",
  });
};

/**
 * 比较版本差异
 */
export const compareResourceVersions = (
  id: string,
  fromVersion: string,
  toVersion: string,
): Promise<ResourceResponse<any>> => {
  return request({
    url: `/api/resources/${id}/versions/compare`,
    method: "get",
    params: { fromVersion, toVersion },
    permission: "data:resource:version:view",
  });
};

// 备份恢复相关API

/**
 * 创建资源备份
 */
export const createResourceBackup = (
  id: string,
  data: {
    name: string;
    description?: string;
    includeData?: boolean;
  },
): Promise<ResourceResponse<ResourceBackup>> => {
  return request({
    url: `/api/resources/${id}/backups`,
    method: "post",
    data,
    permission: "data:resource:backup:create",
  });
};

/**
 * 获取资源备份列表
 */
export const getResourceBackups = (
  id: string,
): Promise<ResourceResponse<ResourceBackup[]>> => {
  return request({
    url: `/api/resources/${id}/backups`,
    method: "get",
    permission: "data:resource:backup:view",
  });
};

/**
 * 恢复资源备份
 */
export const restoreResourceBackup = (
  id: string,
  backupId: string,
): Promise<ResourceResponse<void>> => {
  return request({
    url: `/api/resources/${id}/backups/${backupId}/restore`,
    method: "post",
    permission: "data:resource:backup:restore",
  });
};

/**
 * 删除资源备份
 */
export const deleteResourceBackup = (
  id: string,
  backupId: string,
): Promise<ResourceResponse<void>> => {
  return request({
    url: `/api/resources/${id}/backups/${backupId}`,
    method: "delete",
    permission: "data:resource:backup:delete",
  });
};

// 监控指标相关API

/**
 * 获取资源监控指标
 */
export const getResourceMetrics = (
  id: string,
  params?: {
    startDate?: string;
    endDate?: string;
    metrics?: string[];
  },
): Promise<ResourceResponse<ResourceMetrics>> => {
  return request({
    url: `/api/resources/${id}/metrics`,
    method: "get",
    params,
    permission: "data:resource:metrics:view",
  });
};

/**
 * 获取资源健康状态
 */
export const getResourceHealth = (
  id: string,
): Promise<ResourceResponse<{ status: string; details: any }>> => {
  return request({
    url: `/api/resources/${id}/health`,
    method: "get",
    permission: "data:resource:health:view",
  });
};

// 数据验证相关API

/**
 * 验证资源数据质量
 */
export const validateResourceData = (
  id: string,
  data?: {
    rules?: string[];
    sample?: boolean;
    sampleSize?: number;
  },
): Promise<ResourceResponse<ResourceValidation>> => {
  return request({
    url: `/api/resources/${id}/validate`,
    method: "post",
    data,
    permission: "data:resource:validate",
  });
};

/**
 * 获取数据质量报告
 */
export const getDataQualityReport = (
  id: string,
): Promise<ResourceResponse<any>> => {
  return request({
    url: `/api/resources/${id}/quality-report`,
    method: "get",
    permission: "data:resource:quality:view",
  });
};

// 模板相关API

/**
 * 获取资源模板列表
 */
export const getResourceTemplates = (
  type?: string,
): Promise<ResourceResponse<ResourceTemplate[]>> => {
  return request({
    url: "/api/resources/templates",
    method: "get",
    params: { type },
    permission: "data:resource:template:view",
  });
};

/**
 * 从模板创建资源
 */
export const createResourceFromTemplate = (
  templateId: string,
  data: {
    name: string;
    description?: string;
    categoryId?: string;
    config?: Record<string, any>;
  },
): Promise<ResourceResponse<DataResource>> => {
  return request({
    url: `/api/resources/templates/${templateId}/create`,
    method: "post",
    data,
    permission: "data:resource:template:create",
  });
};

/**
 * 将资源保存为模板
 */
export const saveResourceAsTemplate = (
  id: string,
  data: {
    name: string;
    description?: string;
    isPublic?: boolean;
  },
): Promise<ResourceResponse<ResourceTemplate>> => {
  return request({
    url: `/api/resources/${id}/save-as-template`,
    method: "post",
    data,
    permission: "data:resource:template:create",
  });
};

// 导入导出相关API

/**
 * 导出资源配置
 */
export const exportResourceConfig = (
  id: string,
  format: "json" | "yaml" | "xml",
): Promise<ApiResponse<Blob>> => {
  return request({
    url: `/api/resources/${id}/export`,
    method: "get",
    params: { format },
    responseType: "blob",
    permission: "data:resource:export",
  });
};

/**
 * 导入资源配置
 */
export const importResourceConfig = (
  file: File,
): Promise<ResourceResponse<DataResource>> => {
  const formData = new FormData();
  formData.append("file", file);
  return request({
    url: "/api/resources/import",
    method: "post",
    data: formData,
    headers: {
      "Content-Type": "multipart/form-data",
    },
    permission: "data:resource:import",
  });
};

/**
 * 批量导入资源
 */
export const batchImportResources = (
  data: ResourceImportData[],
): Promise<
  ResourceResponse<{ success: number; failed: number; errors: any[] }>
> => {
  return request({
    url: "/api/resources/batch-import",
    method: "post",
    data: { resources: data },
    permission: "data:resource:import",
  });
};

/**
 * 批量导出资源
 */
export const batchExportResources = (
  ids: string[],
  format: "json" | "yaml" | "xml" | "excel",
): Promise<ApiResponse<Blob>> => {
  return request({
    url: "/api/resources/batch-export",
    method: "post",
    data: { ids, format },
    responseType: "blob",
    permission: "data:resource:export",
  });
};

// 批量操作相关API

/**
 * 批量更新资源
 */
export const batchUpdateResources = (
  operations: ResourceBatchOperation[],
): Promise<
  ResourceResponse<{ success: number; failed: number; errors: any[] }>
> => {
  return request({
    url: "/api/resources/batch-update",
    method: "post",
    data: { operations },
    permission: "data:resource:edit",
  });
};

/**
 * 批量移动资源到分类
 */
export const batchMoveResources = (
  ids: string[],
  categoryId: string,
): Promise<ResourceResponse<void>> => {
  return request({
    url: "/api/resources/batch-move",
    method: "post",
    data: { ids, categoryId },
    permission: "data:resource:edit",
  });
};

/**
 * 批量添加标签
 */
export const batchAddTags = (
  ids: string[],
  tags: string[],
): Promise<ResourceResponse<void>> => {
  return request({
    url: "/api/resources/batch-add-tags",
    method: "post",
    data: { ids, tags },
    permission: "data:resource:tags:edit",
  });
};

/**
 * 批量删除标签
 */
export const batchRemoveTags = (
  ids: string[],
  tags: string[],
): Promise<ResourceResponse<void>> => {
  return request({
    url: "/api/resources/batch-remove-tags",
    method: "post",
    data: { ids, tags },
    permission: "data:resource:tags:edit",
  });
};

// 搜索相关API

/**
 * 全文搜索资源
 */
export const searchResources = (params: {
  keyword: string;
  type?: string;
  categoryId?: string;
  tags?: string[];
  page?: number;
  size?: number;
  sortBy?: string;
  sortOrder?: "asc" | "desc";
}): Promise<PaginatedResourceResponse<DataResource>> => {
  return request({
    url: "/api/resources/search",
    method: "get",
    params,
    permission: "data:resource:search",
  });
};

/**
 * 高级搜索资源
 */
export const advancedSearchResources = (query: {
  filters: Record<string, any>;
  fullText?: string;
  fuzzy?: boolean;
  page?: number;
  size?: number;
  sortBy?: string;
  sortOrder?: "asc" | "desc";
}): Promise<PaginatedResourceResponse<DataResource>> => {
  return request({
    url: "/api/resources/advanced-search",
    method: "post",
    data: query,
    permission: "data:resource:search",
  });
};

/**
 * 获取搜索建议
 */
export const getSearchSuggestions = (
  keyword: string,
): Promise<ResourceResponse<string[]>> => {
  return request({
    url: "/api/resources/search-suggestions",
    method: "get",
    params: { keyword },
  });
};

// 分类管理相关API

/**
 * 获取资源分类树
 */
export const getResourceCategories = (): Promise<
  ResourceResponse<ResourceCategory[]>
> => {
  return request({
    url: "/api/resource-categories",
    method: "get",
  });
};

/**
 * 获取分类详情
 */
export const getCategoryById = (
  id: string,
): Promise<ResourceResponse<ResourceCategory>> => {
  return request({
    url: `/api/resource-categories/${id}`,
    method: "get",
  });
};

/**
 * 创建资源分类
 */
export const createCategory = (data: {
  name: string;
  description?: string;
  parentId?: string;
  icon?: string;
  color?: string;
  sortOrder?: number;
}): Promise<ResourceResponse<ResourceCategory>> => {
  return request({
    url: "/api/resource-categories",
    method: "post",
    data,
  });
};

/**
 * 更新资源分类
 */
export const updateCategory = (
  id: string,
  data: {
    name?: string;
    description?: string;
    parentId?: string;
    icon?: string;
    color?: string;
    sortOrder?: number;
  },
): Promise<ResourceResponse<ResourceCategory>> => {
  return request({
    url: `/api/resource-categories/${id}`,
    method: "put",
    data,
  });
};

/**
 * 删除资源分类
 */
export const deleteCategory = (
  id: string,
  moveToId?: string,
): Promise<ResourceResponse<void>> => {
  return request({
    url: `/api/resource-categories/${id}`,
    method: "delete",
    params: { moveToId },
  });
};

/**
 * 移动分类
 */
export const moveCategory = (
  id: string,
  parentId: string,
  sortOrder?: number,
): Promise<ResourceResponse<void>> => {
  return request({
    url: `/api/resource-categories/${id}/move`,
    method: "patch",
    data: { parentId, sortOrder },
  });
};

/**
 * 获取分类下的资源数量
 */
export const getCategoryResourceCount = (
  id: string,
): Promise<ResourceResponse<{ count: number }>> => {
  return request({
    url: `/api/resource-categories/${id}/resource-count`,
    method: "get",
  });
};
