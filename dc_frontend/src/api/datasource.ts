import { request } from "@/utils/request";
import type {
  DataSource,
  DataSourceCreateRequest,
  DataSourceUpdateRequest,
  DataSourceTestRequest,
  DataSourceListQuery,
  DataSourceConnectionStatus,
  DataSourceStats,
  ApiResponse,
  PaginatedResponse,
} from "@/types/datasource";

/**
 * 数据源管理相关API接口
 */
export const datasourceApi = {
  /**
   * 获取数据源列表
   * @param params 查询参数
   */
  getDataSourceList(
    params?: DataSourceListQuery,
  ): Promise<ApiResponse<PaginatedResponse<DataSource>>> {
    return request({
      url: "/datasources/",
      method: "GET",
      params,
      permission: "data:datasource:view",
    });
  },

  /**
   * 获取数据源详情
   * @param id 数据源ID
   */
  getDataSourceDetail(id: number): Promise<ApiResponse<DataSource>> {
    return request({
      url: `/datasources/${id}`,
      method: "GET",
      permission: "data:datasource:view",
    });
  },

  /**
   * 创建数据源
   * @param data 创建数据
   */
  createDataSource(
    data: DataSourceCreateRequest,
  ): Promise<ApiResponse<DataSource>> {
    return request({
      url: "/datasources/",
      method: "POST",
      data,
      permission: "data:datasource:create",
    });
  },

  /**
   * 更新数据源
   * @param id 数据源ID
   * @param data 更新数据
   */
  updateDataSource(
    id: number,
    data: DataSourceUpdateRequest,
  ): Promise<ApiResponse<DataSource>> {
    return request({
      url: `/datasources/${id}`,
      method: "PUT",
      data,
      permission: "data:datasource:update",
    });
  },

  /**
   * 删除数据源
   * @param id 数据源ID
   */
  deleteDataSource(id: number): Promise<ApiResponse<void>> {
    return request({
      url: `/datasources/${id}`,
      method: "DELETE",
      permission: "data:datasource:delete",
    });
  },

  /**
   * 测试数据源连接
   * @param data 测试连接数据
   */
  testConnection(
    data: DataSourceTestRequest,
  ): Promise<ApiResponse<DataSourceConnectionStatus>> {
    return request({
      url: "/datasources/test-connection/",
      method: "POST",
      data,
      permission: "data:datasource:test",
    });
  },

  /**
   * 测试现有数据源连接
   * @param id 数据源ID
   */
  testDataSourceConnection(
    id: number,
  ): Promise<ApiResponse<DataSourceConnectionStatus>> {
    return request({
      url: `/datasources/${id}/test-connection`,
      method: "POST",
      permission: "data:datasource:test",
    });
  },

  /**
   * 获取数据源统计信息
   */
  getDataSourceStats(): Promise<ApiResponse<DataSourceStats>> {
    return request({
      url: "/datasources/stats/",
      method: "GET",
      permission: "data:datasource:stats:view",
    });
  },

  /**
   * 获取数据源类型列表
   */
  getDataSourceTypes(): Promise<ApiResponse<string[]>> {
    return request({
      url: "/datasources/types/",
      method: "GET",
      permission: "data:datasource:type:view",
    });
  },

  /**
   * 批量删除数据源
   * @param ids 数据源ID列表
   */
  batchDeleteDataSources(ids: number[]): Promise<ApiResponse<void>> {
    return request({
      url: "/datasources/batch-delete/",
      method: "POST",
      data: { ids },
      permission: "data:datasource:delete",
    });
  },

  /**
   * 启用/禁用数据源
   * @param id 数据源ID
   * @param enabled 是否启用
   */
  toggleDataSource(id: number, enabled: boolean): Promise<ApiResponse<void>> {
    return request({
      url: `/datasources/${id}/toggle`,
      method: "PATCH",
      data: { enabled },
      permission: "data:datasource:update",
    });
  },

  /**
   * 同步数据源元数据
   * @param id 数据源ID
   */
  syncMetadata(id: number): Promise<ApiResponse<void>> {
    return request({
      url: `/datasources/${id}/sync-metadata`,
      method: "POST",
      permission: "data:datasource:sync",
    });
  },

  /**
   * 获取数据源健康状态
   * @param id 数据源ID
   */
  getHealthStatus(
    id: number,
  ): Promise<ApiResponse<DataSourceConnectionStatus>> {
    return request({
      url: `/datasources/${id}/health`,
      method: "GET",
      permission: "data:datasource:health:view",
    });
  },

  /**
   * 获取数据源的表/视图/索引列表
   * @param id 数据源ID
   */
  getDataSourceTables(
    id: number,
  ): Promise<
    ApiResponse<Array<{ name: string; type: string; schema?: string }>>
  > {
    return request({
      url: `/datasources/${id}/tables/`,
      method: "GET",
      permission: "data:datasource:tables:view",
    });
  },

  /**
   * 获取数据源的Schema列表
   * @param id 数据源ID
   */
  getDataSourceSchemas(
    id: number,
  ): Promise<ApiResponse<Array<{ name: string }>>> {
    return request({
      url: `/datasources/${id}/schemas/`,
      method: "GET",
      permission: "data:datasource:schemas:view",
    });
  },

  /**
   * 获取数据源指定Schema下的表列表
   * @param id 数据源ID
   * @param schema Schema名称
   */
  getDataSourceTablesWithSchema(
    id: number,
    schema: string,
  ): Promise<ApiResponse<Array<{ name: string; type: string }>>> {
    return request({
      url: `/datasources/${id}/schemas/${schema}/tables/`,
      method: "GET",
      permission: "data:datasource:tables:view",
    });
  },

  /**
   * 获取数据源指定Schema下指定表的字段列表
   * @param id 数据源ID
   * @param schema Schema名称
   * @param table 表名称
   */
  getDataSourceTableFields(
    id: number,
    schema: string,
    table: string,
  ): Promise<
    ApiResponse<
      Array<{
        name: string;
        type: string;
        nullable?: boolean;
        comment?: string;
      }>
    >
  > {
    return request({
      url: `/datasources/${id}/schemas/${schema}/tables/${table}/fields/`,
      method: "GET",
      permission: "data:datasource:fields:view",
    });
  },
};

/**
 * 获取数据源列表的简化函数
 * @returns Promise<DataSource[]>
 */
export const getDatasources = async (): Promise<DataSource[]> => {
  const response = await datasourceApi.getDataSourceList();
  return response.data?.items || [];
};

export default datasourceApi;
