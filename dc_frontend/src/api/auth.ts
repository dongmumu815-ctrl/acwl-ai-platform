import { request } from "@/utils/request";
import type {
  LoginRequest,
  LoginResponse,
  RegisterRequest,
  ForgotPasswordRequest,
  ResetPasswordRequest,
  PasswordChangeRequest,
  UserUpdateRequest,
  User,
  UserPermission,
  UserRole,
  ApiResponse,
  MyPermissionsResponse,
} from "@/types/user";

/**
 * 认证相关API接口
 */
export const authApi = {
  /**
   * 用户登录
   * @param data 登录数据
   */
  login(data: LoginRequest): Promise<ApiResponse<LoginResponse>> {
    return request({
      url: "/auth/login/json",
      method: "POST",
      data,
      permission: "auth:login",
    });
  },

  /**
   * 用户登出
   */
  logout(): Promise<ApiResponse<void>> {
    return request({
      url: "/auth/logout",
      method: "POST",
      permission: "auth:logout",
    });
  },

  /**
   * 用户注册
   * @param data 注册数据
   */
  register(data: RegisterRequest): Promise<ApiResponse<User>> {
    return request({
      url: "/auth/register",
      method: "POST",
      data,
      permission: "auth:register",
    });
  },

  /**
   * 忘记密码
   * @param data 忘记密码数据
   */
  forgotPassword(data: ForgotPasswordRequest): Promise<ApiResponse<void>> {
    return request({
      url: "/auth/forgot-password",
      method: "POST",
      data,
      permission: "auth:password:forgot",
    });
  },

  /**
   * 重置密码
   * @param data 重置密码数据
   */
  resetPassword(data: ResetPasswordRequest): Promise<ApiResponse<void>> {
    return request({
      url: "/auth/reset-password",
      method: "POST",
      data,
      permission: "auth:password:reset",
    });
  },

  /**
   * 修改密码
   * @param data 修改密码数据
   */
  changePassword(data: PasswordChangeRequest): Promise<ApiResponse<void>> {
    return request({
      url: "/auth/change-password",
      method: "POST",
      data,
      permission: "auth:password:change",
    });
  },

  /**
   * 获取当前用户信息
   */
  getCurrentUser(): Promise<
    ApiResponse<{
      user: User;
      permissions: string[];
      roles: string[];
    }>
  > {
    return request({
      url: "/auth/me",
      method: "GET",
      permission: "auth:me:view",
    });
  },

  /**
   * 更新用户信息
   * @param data 用户更新数据
   */
  updateProfile(data: UserUpdateRequest): Promise<ApiResponse<User>> {
    return request({
      url: "/auth/profile",
      method: "PUT",
      data,
      permission: "auth:profile:edit",
    });
  },

  /**
   * 上传用户头像
   * @param file 头像文件
   */
  uploadAvatar(file: File): Promise<ApiResponse<{ avatar_url: string }>> {
    const formData = new FormData();
    formData.append("avatar", file);

    return request({
      url: "/auth/avatar",
      method: "POST",
      data: formData,
      headers: {
        "Content-Type": "multipart/form-data",
      },
      permission: "auth:profile:avatar",
    });
  },

  /**
   * 获取用户权限
   */
  getUserPermissions(): Promise<
    ApiResponse<{
      permissions: string[];
      roles: string[];
    }>
  > {
    return request({
      url: "/auth/permissions",
      method: "GET",
      permission: "auth:permissions:view",
    });
  },

  /**
   * 获取当前认证用户权限（基于认证信息）
   *
   * - 调用后端 `/permissions/me`，无需传入用户ID
   * - 返回字段包含：`permissions`、`permission_codes`、`role_codes`
   */
  getMyPermissions(): Promise<ApiResponse<MyPermissionsResponse>> {
    return request({
      url: "/permissions/me",
      method: "GET",
      permission: "auth:permissions:view",
    });
  },

  /**
   * 刷新Token
   */
  refreshToken(): Promise<ApiResponse<{ token: string; expires_in: number }>> {
    return request({
      url: "/auth/refresh",
      method: "POST",
      permission: "auth:token:refresh",
    });
  },

  /**
   * 验证Token
   */
  verifyToken(): Promise<ApiResponse<{ valid: boolean }>> {
    return request({
      url: "/auth/verify",
      method: "GET",
      permission: "auth:token:verify",
    });
  },

  /**
   * 获取用户会话列表
   */
  getUserSessions(): Promise<ApiResponse<any[]>> {
    return request({
      url: "/auth/sessions",
      method: "GET",
      permission: "auth:sessions:view",
    });
  },

  /**
   * 终止指定会话
   * @param sessionId 会话ID
   */
  terminateSession(sessionId: string): Promise<ApiResponse<void>> {
    return request({
      url: `/auth/sessions/${sessionId}`,
      method: "DELETE",
      permission: "auth:sessions:terminate",
    });
  },

  /**
   * 终止所有其他会话
   */
  terminateOtherSessions(): Promise<ApiResponse<void>> {
    return request({
      url: "/auth/sessions/others",
      method: "DELETE",
      permission: "auth:sessions:terminate_others",
    });
  },

  /**
   * 获取用户活动日志
   * @param params 查询参数
   */
  getUserActivities(params?: {
    page?: number;
    page_size?: number;
    action?: string;
    start_date?: string;
    end_date?: string;
  }): Promise<ApiResponse<any>> {
    return request({
      url: "/auth/activities",
      method: "GET",
      params,
      permission: "auth:activities:view",
    });
  },

  /**
   * 获取用户偏好设置
   */
  getUserPreferences(): Promise<ApiResponse<any>> {
    return request({
      url: "/auth/preferences",
      method: "GET",
      permission: "auth:preferences:view",
    });
  },

  /**
   * 更新用户偏好设置
   * @param data 偏好设置数据
   */
  updateUserPreferences(data: any): Promise<ApiResponse<any>> {
    return request({
      url: "/auth/preferences",
      method: "PUT",
      data,
      permission: "auth:preferences:edit",
    });
  },

  /**
   * 获取用户统计信息
   */
  getUserStats(): Promise<ApiResponse<any>> {
    return request({
      url: "/auth/stats",
      method: "GET",
      permission: "auth:stats:view",
    });
  },

  /**
   * 启用两步验证
   */
  enableTwoFactor(): Promise<ApiResponse<{ qr_code: string; secret: string }>> {
    return request({
      url: "/auth/2fa/enable",
      method: "POST",
      permission: "auth:2fa:enable",
    });
  },

  /**
   * 确认两步验证
   * @param code 验证码
   */
  confirmTwoFactor(
    code: string,
  ): Promise<ApiResponse<{ backup_codes: string[] }>> {
    return request({
      url: "/auth/2fa/confirm",
      method: "POST",
      data: { code },
      permission: "auth:2fa:confirm",
    });
  },

  /**
   * 禁用两步验证
   * @param code 验证码
   */
  disableTwoFactor(code: string): Promise<ApiResponse<void>> {
    return request({
      url: "/auth/2fa/disable",
      method: "POST",
      data: { code },
      permission: "auth:2fa:disable",
    });
  },

  /**
   * 验证两步验证码
   * @param code 验证码
   */
  verifyTwoFactor(code: string): Promise<ApiResponse<{ valid: boolean }>> {
    return request({
      url: "/auth/2fa/verify",
      method: "POST",
      data: { code },
      permission: "auth:2fa:verify",
    });
  },

  /**
   * 生成新的备份码
   */
  generateBackupCodes(): Promise<ApiResponse<{ backup_codes: string[] }>> {
    return request({
      url: "/auth/2fa/backup-codes",
      method: "POST",
      permission: "auth:2fa:backup_codes",
    });
  },
};

/**
 * 导出默认对象
 */
export default authApi;
