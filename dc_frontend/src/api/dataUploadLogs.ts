import { request } from "@/utils/request";
import type { ApiResponse } from "@/utils/request";
import type {
  PaginationParams,
  PaginatedResponse,
} from "@/types/apiManagement";

export interface DataUploadLog {
  id: number;
  batch_id: string;
  data_source_name: string;
  platform_name: string;
  target_table_name: string;
  target_table_desc?: string;
  need_review: number;
  resource_type: string;
  sync_start_time: string;
  sync_end_time?: string;
  total_data_count?: number;
  success_data_count?: number;
  failed_data_count?: number;
  sync_status: string;
  failure_reason?: string;
  retry_upload?: number;
  encryption_method?: string;
  operator: string;
  sync_log?: string;
  create_time: string;
  update_time?: string;
}

export interface DataUploadLogsQuery extends PaginationParams {
  sort_by?: string;
  order?: "asc" | "desc";
  /** 按批次号过滤（后端若支持则生效） */
  batch_id?: string;
  /** 按时间范围过滤：开始时间 */
  start_time?: string;
  /** 按时间范围过滤：结束时间 */
  end_time?: string;
  /** 排除的数据源名称（后端支持则生效） */
  exclude_data_source_name?: string;
  /** 排除的数据平台名称 */
  exclude_platform_name?: string;
}

export const dataUploadLogsApi = {
  getLogs(
    params?: DataUploadLogsQuery,
  ): Promise<ApiResponse<PaginatedResponse<DataUploadLog>>> {
    return request({
      url: "/data-upload-logs/",
      method: "get",
      params: {
        page: params?.page ?? 1,
        size: params?.page_size ?? 20,
        sort_by: params?.sort_by ?? "sync_start_time",
        order: params?.order ?? "desc",
        // 透传批次号查询参数（如果存在）
        batch_id: params?.batch_id,
        // 透传时间范围查询参数（如果存在）
        start_time: params?.start_time,
        end_time: params?.end_time,
        // 透传数据平台名称查询参数（如果存在）
        exclude_platform_name: params?.exclude_platform_name,
      },
    });
  },

  getBatchDetails(
    batchId: string,
    params?: { limit?: number; offset?: number; q?: string },
  ): Promise<ApiResponse<any>> {
    return request({
      url: `/data-upload-logs/details/${batchId}`,
      method: "get",
      params,
    });
  },
};
