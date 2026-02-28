import axios from "axios";
import type {
  AxiosInstance,
  AxiosRequestConfig,
  AxiosResponse,
  AxiosError,
} from "axios";
import { ElMessage, ElMessageBox } from "element-plus";
import { useUserStore } from "@/stores/user";
import router from "@/router";

/**
 * 请求配置接口
 */
export interface RequestConfig extends AxiosRequestConfig {
  skipAuth?: boolean;
  skipErrorHandler?: boolean;
  showLoading?: boolean;
  showSuccessMessage?: boolean;
  // 权限码，用于前端权限收集与后端鉴权提示
  permission?: string | string[];
}

/**
 * API响应数据结构
 */
export interface ApiResponse<T = any> {
  success: boolean;
  message?: string;
  data: T;
  code?: number;
}

/**
 * 创建axios实例
 */
const createAxiosInstance = (): AxiosInstance => {
  const instance = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL || "/api/v1",
    timeout: 120000, // 默认超时提升至120秒，适配生成Excel等长耗时请求
    headers: {
      "Content-Type": "application/json",
    },
  });

  // 请求拦截器
  instance.interceptors.request.use(
    (config: any) => {
      const userStore = useUserStore();

      // 添加认证token
      if (!config.skipAuth && userStore.token) {
        config.headers.Authorization = `Bearer ${userStore.token}`;
      }

      // 注入权限码到请求头，并记录使用情况
      if (config.permission) {
        const perms = Array.isArray(config.permission)
          ? config.permission
          : [config.permission];
        // 记录到用户store，便于后续收集与配置
        try {
          if (typeof userStore.recordUsedPermission === "function") {
            userStore.recordUsedPermission(perms);
          }
        } catch {}
        // 设置请求头供后端可选使用（不强制要求后端读取）
        config.headers["X-Permission-Code"] = perms.join(",");
      }

      // 添加请求ID用于追踪
      config.headers["X-Request-ID"] = generateRequestId();

      // 添加时间戳防止缓存
      if (config.method === "get") {
        config.params = {
          ...config.params,
          _t: Date.now(),
        };
      }

      console.log(
        `[API Request] ${config.method?.toUpperCase()} ${config.url}`,
        {
          params: config.params,
          data: config.data,
        },
      );

      return config;
    },
    (error: AxiosError) => {
      console.error("[API Request Error]", error);
      return Promise.reject(error);
    },
  );

  // 响应拦截器
  instance.interceptors.response.use(
    async (response: AxiosResponse) => {
      const config = response.config as RequestConfig;
      const data = response.data;

      console.log(
        `[API Response] ${config.method?.toUpperCase()} ${config.url}`,
        {
          status: response.status,
          data: data,
        },
      );

      // 检测成功响应中包含的认证错误对象（某些服务可能返回200+错误体）
      if (
        data &&
        typeof data === "object" &&
        (data as any).error === "AUTHENTICATION_ERROR"
      ) {
        ElMessage.error((data as any)?.message || "无效的认证令牌");

        // 防止无限循环：如果正在登出过程中，直接清除本地状态
        if (isLoggingOut) {
          console.warn("检测到logout过程中的认证错误，直接清除本地状态");
          localStorage.removeItem("token");
          localStorage.removeItem("user");
          localStorage.removeItem("permissions");
          localStorage.removeItem("roles");
          window.location.href = "/login";
          return Promise.reject(new Error("AUTHENTICATION_ERROR"));
        }

        // 设置登出标志
        isLoggingOut = true;

        try {
          const userStore = useUserStore();
          // 直接清除本地状态，不调用logout API
          userStore.reset();
          localStorage.removeItem("token");
          localStorage.removeItem("user");
          localStorage.removeItem("permissions");
          localStorage.removeItem("roles");
          router.push({
            name: "Login",
            query: { redirect: router.currentRoute.value.fullPath },
          });
        } catch (error) {
          console.error("清除用户状态失败:", error);
          localStorage.removeItem("token");
          localStorage.removeItem("user");
          localStorage.removeItem("permissions");
          localStorage.removeItem("roles");
          window.location.href = "/login";
        } finally {
          // 重置标志
          isLoggingOut = false;
        }
        // 中断后续处理，向上抛出错误以便调用方感知
        return Promise.reject(new Error("AUTHENTICATION_ERROR"));
      }

      // 显示成功消息
      if (config.showSuccessMessage && data.success && data.message) {
        ElMessage.success(data.message);
      }

      return response;
    },
    async (error: AxiosError) => {
      const config = error.config as RequestConfig;
      const response = error.response;

      console.error(
        `[API Response Error] ${config?.method?.toUpperCase()} ${config?.url}`,
        {
          status: response?.status,
          data: response?.data,
          message: error.message,
        },
      );

      // 跳过错误处理
      if (config?.skipErrorHandler) {
        return Promise.reject(error);
      }

      // 处理不同的错误状态
      await handleApiError(error);

      return Promise.reject(error);
    },
  );

  return instance;
};

// 防止无限循环的标志
let isLoggingOut = false;

/**
 * 处理API错误
 * @param error axios错误对象
 */
const handleApiError = async (error: AxiosError): Promise<void> => {
  const userStore = useUserStore();
  const response = error.response;
  const data = response?.data as any;

  // 检查特定的认证错误码
  if (data?.error === "AUTHENTICATION_ERROR") {
    ElMessage.error(data?.message || "无效的认证令牌");

    // 防止无限循环：如果正在登出过程中，直接清除本地状态
    if (isLoggingOut) {
      console.warn("检测到logout过程中的认证错误，直接清除本地状态");
      localStorage.removeItem("token");
      localStorage.removeItem("user");
      localStorage.removeItem("permissions");
      localStorage.removeItem("roles");
      window.location.href = "/login";
      return;
    }

    // 设置登出标志
    isLoggingOut = true;

    try {
      // 直接清除本地状态，不调用logout API
      userStore.reset();
      localStorage.removeItem("token");
      localStorage.removeItem("user");
      localStorage.removeItem("permissions");
      localStorage.removeItem("roles");
      router.push({
        name: "Login",
        query: { redirect: router.currentRoute.value.fullPath },
      });
    } catch (error) {
      console.error("清除用户状态失败:", error);
      // 如果清除状态失败，强制跳转
      window.location.href = "/login";
    } finally {
      // 重置标志
      isLoggingOut = false;
    }
    return;
  }

  switch (response?.status) {
    case 400:
      ElMessage.error(data?.message || "请求参数错误");
      break;

    case 401:
      // 未认证或token过期
      ElMessage.error("登录已过期，请重新登录");

      // 防止无限循环：如果正在登出过程中，直接清除本地状态
      if (isLoggingOut) {
        console.warn("检测到logout过程中的401错误，直接清除本地状态");
        localStorage.removeItem("token");
        localStorage.removeItem("user");
        localStorage.removeItem("permissions");
        localStorage.removeItem("roles");
        window.location.href = "/login";
        break;
      }

      // 设置登出标志
      isLoggingOut = true;

      try {
        // 直接清除本地状态，不调用logout API
        userStore.reset();
        localStorage.removeItem("token");
        localStorage.removeItem("user");
        localStorage.removeItem("permissions");
        localStorage.removeItem("roles");
        router.push({
          name: "Login",
          query: { redirect: router.currentRoute.value.fullPath },
        });
      } catch (error) {
        console.error("清除用户状态失败:", error);
        window.location.href = "/login";
      } finally {
        // 重置标志
        isLoggingOut = false;
      }
      break;

    case 403:
      ElMessage.error(data?.message || "没有权限访问此资源");
      break;

    case 404:
      ElMessage.error(data?.message || "请求的资源不存在");
      break;

    case 409:
      ElMessage.error(data?.message || "资源冲突");
      break;

    case 422:
      // 表单验证错误
      if (data?.errors && Array.isArray(data.errors)) {
        const errorMessages = data.errors
          .map((err: any) => err.message || err)
          .join("\n");
        ElMessage.error(errorMessages);
      } else {
        ElMessage.error(data?.message || "数据验证失败");
      }
      break;

    case 429:
      ElMessage.error("请求过于频繁，请稍后再试");
      break;

    case 500:
      ElMessage.error("服务器内部错误，请稍后再试");
      break;

    case 502:
    case 503:
    case 504:
      ElMessage.error("服务暂时不可用，请稍后再试");
      break;

    default:
      if (error.code === "ECONNABORTED") {
        ElMessage.error("请求超时，请检查网络连接");
      } else if (error.code === "ERR_NETWORK") {
        ElMessage.error("网络连接失败，请检查网络设置");
      } else {
        ElMessage.error(
          data?.message || error.message || "网络错误，请稍后再试",
        );
      }
  }
};

/**
 * 生成请求ID
 */
const generateRequestId = (): string => {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
};

/**
 * 创建请求实例
 */
const axiosInstance = createAxiosInstance();

/**
 * 通用请求方法
 * @param config 请求配置
 */
export const request = async <T = any>(
  config: RequestConfig,
): Promise<ApiResponse<T>> => {
  try {
    const response = await axiosInstance.request<T>(config);

    /**
     * 处理带有服务端标准字段的响应
     * 只要响应体包含 `success` 字段，即视为标准响应并按该字段解析；`data` 允许缺省
     */
    if (
      response.data &&
      typeof response.data === "object" &&
      "success" in response.data
    ) {
      const rd: any = response.data;
      return {
        success: Boolean(rd.success),
        data: (rd.data ?? undefined) as T,
        message: typeof rd.message === "string" ? rd.message : undefined,
        code: typeof rd.code === "number" ? rd.code : undefined,
      } as ApiResponse<T>;
    }

    // 如果不是ApiResponse格式，包装成ApiResponse格式
    return {
      success: true,
      message: "请求成功",
      data: response.data,
    } as ApiResponse<T>;
  } catch (error) {
    // 如果是axios错误且有响应数据，返回响应数据
    if (axios.isAxiosError(error) && error.response?.data) {
      /**
       * 处理服务端返回的错误格式
       * 只要包含 `success` 字段，即按标准响应解析；`data` 可缺省
       */
      if (
        typeof error.response.data === "object" &&
        "success" in error.response.data
      ) {
        const rd: any = error.response.data;
        return {
          success: Boolean(rd.success),
          data: (rd.data ?? undefined) as T,
          message: typeof rd.message === "string" ? rd.message : undefined,
          code: typeof rd.code === "number" ? rd.code : undefined,
        } as ApiResponse<T>;
      }

      // 包装错误响应
      return {
        success: false,
        message:
          (error.response.data &&
            (error.response.data.message || error.response.data.detail)) ||
          "请求失败",
        data: error.response.data,
      } as ApiResponse<T>;
    }

    // 否则抛出错误
    throw error;
  }
};

/**
 * GET请求
 * @param url 请求地址
 * @param params 请求参数
 * @param config 请求配置
 */
export const get = <T = any>(
  url: string,
  params?: any,
  config?: RequestConfig,
): Promise<ApiResponse<T>> => {
  return request<T>({
    url,
    method: "GET",
    params,
    ...config,
  });
};

/**
 * POST请求
 * @param url 请求地址
 * @param data 请求数据
 * @param config 请求配置
 */
export const post = <T = any>(
  url: string,
  data?: any,
  config?: RequestConfig,
): Promise<ApiResponse<T>> => {
  return request<T>({
    url,
    method: "POST",
    data,
    ...config,
  });
};

/**
 * PUT请求
 * @param url 请求地址
 * @param data 请求数据
 * @param config 请求配置
 */
export const put = <T = any>(
  url: string,
  data?: any,
  config?: RequestConfig,
): Promise<ApiResponse<T>> => {
  return request<T>({
    url,
    method: "PUT",
    data,
    ...config,
  });
};

/**
 * DELETE请求
 * @param url 请求地址
 * @param config 请求配置
 */
export const del = <T = any>(
  url: string,
  config?: RequestConfig,
): Promise<ApiResponse<T>> => {
  return request<T>({
    url,
    method: "DELETE",
    ...config,
  });
};

/**
 * PATCH请求
 * @param url 请求地址
 * @param data 请求数据
 * @param config 请求配置
 */
export const patch = <T = any>(
  url: string,
  data?: any,
  config?: RequestConfig,
): Promise<ApiResponse<T>> => {
  return request<T>({
    url,
    method: "PATCH",
    data,
    ...config,
  });
};

/**
 * 文件上传
 * @param url 请求地址
 * @param file 文件对象
 * @param config 请求配置
 */
export const upload = <T = any>(
  url: string,
  file: File,
  config?: RequestConfig & {
    onUploadProgress?: (progressEvent: any) => void;
  },
): Promise<ApiResponse<T>> => {
  const formData = new FormData();
  formData.append("file", file);

  return request<T>({
    url,
    method: "POST",
    data: formData,
    headers: {
      "Content-Type": "multipart/form-data",
    },
    ...config,
  });
};

/**
 * 文件下载
 * @param url 请求地址
 * @param params 请求参数
 * @param filename 文件名
 * @param config 请求配置
 */
export const download = async (
  url: string,
  params?: any,
  filename?: string,
  config?: RequestConfig,
): Promise<void> => {
  try {
    const response = await axiosInstance.request({
      url,
      method: "GET",
      params,
      responseType: "blob",
      ...config,
    });

    // 创建下载链接
    const blob = new Blob([response.data]);
    const downloadUrl = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = downloadUrl;

    // 从响应头获取文件名
    const contentDisposition = response.headers["content-disposition"];
    if (contentDisposition && !filename) {
      const filenameMatch = contentDisposition.match(/filename="?([^"]+)"?/);
      if (filenameMatch) {
        filename = filenameMatch[1];
      }
    }

    link.download = filename || "download";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(downloadUrl);

    ElMessage.success("文件下载成功");
  } catch (error) {
    console.error("文件下载失败:", error);
    ElMessage.error("文件下载失败");
  }
};

/**
 * 取消请求的token
 */
export const CancelToken = axios.CancelToken;

/**
 * 判断是否为取消请求的错误
 */
export const isCancel = axios.isCancel;

/**
 * 导出axios实例
 */
export { axiosInstance };

/**
 * 导出默认请求方法
 */
export default request;
