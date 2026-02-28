import { request } from "@/utils/request";

/**
 * SQL查询模板请求参数
 */
export interface SQLTemplateRequest {
  name: string;
  description?: string;
  datasourceId: number;
  dataResourceId?: number;
  query: string;
  tags?: string[];
  config?: any; // 配置信息
  isTemplate: boolean;
}

/**
 * SQL查询模板响应数据
 */
export interface SQLTemplateResponse {
  id: number;
  name: string;
  description: string;
  datasourceId: number;
  dataResourceId?: number;
  query: string;
  tags: string[];
  config?: any; // 配置信息
  isTemplate: boolean;
  createdBy: string;
  createdAt: string;
  updatedAt: string;
}

/**
 * SQL查询执行请求参数
 */
export interface SQLQueryRequest {
  datasourceId: number;
  query: string;
  limit?: number;
  offset?: number;
}

/**
 * SQL查询响应接口
 */
export interface SQLQueryResponse {
  success: boolean;
  columns?: string[];
  data?: any[][];
  row_count: number;
  execution_time: number;
  message: string;
  error_details?: string;
}

/**
 * 保存SQL查询模板
 * @param template 模板数据
 * @returns 保存结果
 */
export function saveSQLTemplate(
  template: SQLTemplateRequest,
): Promise<{ data: SQLTemplateResponse }> {
  return request({
    url: "/sql/templates",
    method: "post",
    data: template,
    permission: "data:sql:templates:create",
  });
}

/**
 * 获取SQL查询模板列表
 * @param datasourceId 数据源ID（可选）
 * @param dataResourceId 数据资源ID（可选）
 * @param tags 标签过滤（可选）
 * @param search 搜索关键词（可选）
 * @returns 模板列表
 */
export function getSQLTemplates(params?: {
  datasourceId?: number;
  dataResourceId?: number;
  tags?: string[];
  search?: string;
  isTemplate?: boolean;
}): Promise<{ data: SQLTemplateResponse[] }> {
  // 转换参数名以匹配后端API期望的格式
  const apiParams: any = {};
  if (params) {
    if (params.datasourceId !== undefined) {
      apiParams.datasource_id = params.datasourceId;
    }
    if (params.dataResourceId !== undefined) {
      apiParams.data_resource_id = params.dataResourceId;
    }
    if (params.tags !== undefined) {
      apiParams.tags = params.tags;
    }
    if (params.search !== undefined) {
      apiParams.search = params.search;
    }
    if (params.isTemplate !== undefined) {
      apiParams.isTemplate = params.isTemplate;
    }
  }

  return request({
    url: "/sql/templates",
    method: "get",
    params: apiParams,
    permission: "data:sql:templates:view",
  });
}

/**
 * 获取SQL查询模板详情
 * @param templateId 模板ID
 * @returns 模板详情
 */
export function getSQLTemplate(
  templateId: number,
): Promise<{ data: SQLTemplateResponse }> {
  return request({
    url: `/sql/templates/${templateId}`,
    method: "get",
    permission: "data:sql:templates:view",
  });
}

/**
 * 更新SQL查询模板
 * @param templateId 模板ID
 * @param template 模板数据
 * @returns 更新结果
 */
export function updateSQLTemplate(
  templateId: number,
  template: Partial<SQLTemplateRequest>,
): Promise<{ data: SQLTemplateResponse }> {
  return request({
    url: `/sql/templates/${templateId}`,
    method: "put",
    data: template,
    permission: "data:sql:templates:edit",
  });
}

/**
 * 删除SQL查询模板
 * @param templateId 模板ID
 * @returns 删除结果
 */
export function deleteSQLTemplate(
  templateId: number,
): Promise<{ data: { success: boolean } }> {
  return request({
    url: `/sql/templates/${templateId}`,
    method: "delete",
    permission: "data:sql:templates:delete",
  });
}

/**
 * 执行SQL查询
 * @param queryRequest 查询请求
 * @returns 查询结果
 */
export function executeSQLQuery(
  queryRequest: SQLQueryRequest,
): Promise<{ data: SQLQueryResponse }> {
  const { datasourceId, ...requestData } = queryRequest;

  return request({
    url: `/datasources/${datasourceId}/query`,
    method: "post",
    data: {
      query: requestData.query,
      limit: requestData.limit || 1000,
      timeout: 30,
    },
    permission: "data:sql:query",
  });
}

/**
 * 导出SQL查询结果
 * @param queryRequest 查询请求
 * @returns 导出任务ID
 */
export function exportSQLQueryResult(
  queryRequest: SQLQueryRequest,
): Promise<{ data: { taskId: string } }> {
  return request({
    url: "/sql/export",
    method: "post",
    data: queryRequest,
    permission: "data:sql:export",
  });
}

/**
 * 搜索SQL查询模板
 * @param keyword 搜索关键词
 * @param datasourceId 数据源ID（可选）
 * @returns 搜索结果
 */
export function searchSQLTemplates(
  keyword: string,
  datasourceId?: number,
): Promise<{ data: SQLTemplateResponse[] }> {
  // 转换参数名以匹配后端API期望的格式
  const apiParams: any = { keyword };
  if (datasourceId !== undefined) {
    apiParams.datasource_id = datasourceId;
  }

  return request({
    url: "/sql/templates/search",
    method: "get",
    params: apiParams,
    permission: "data:sql:templates:view",
  });
}
