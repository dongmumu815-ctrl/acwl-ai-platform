<template>
  <div class="login-container">
    <div class="login-box">
      <div class="login-header">
        <h1 class="title">
          <el-icon class="title-icon"><DataBoard /></el-icon>
          ACWL AI 数据平台
        </h1>
        <p class="subtitle">数据资源中心管理系统</p>
      </div>

      <el-form
        ref="loginFormRef"
        :model="loginForm"
        :rules="loginRules"
        class="login-form"
        @keyup.enter="handleLogin"
      >
        <el-form-item prop="account">
          <el-input
            v-model="loginForm.account"
            placeholder="请输入用户名或邮箱"
            size="large"
            prefix-icon="User"
            clearable
          />
        </el-form-item>

        <el-form-item prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="请输入密码"
            size="large"
            prefix-icon="Lock"
            show-password
            clearable
          />
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            size="large"
            class="login-button"
            :loading="userStore.loading"
            @click="handleLogin"
          >
            {{ userStore.loading ? "登录中..." : "登录" }}
          </el-button>
        </el-form-item>
        <!--         
        <el-form-item>
          <el-button
            type="success"
            size="large"
            class="test-login-button"
            :loading="userStore.loading"
            @click="handleTestLogin"
            plain
          >
            测试登录 (admin)
          </el-button>
        </el-form-item> -->
      </el-form>

      <div class="login-footer">
        <p class="tips">默认邮箱：admin@acwl.ai / password</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from "vue";
import { useRouter } from "vue-router";
import { ElMessage, type FormInstance, type FormRules } from "element-plus";
import { useUserStore } from "@/stores/user";
import type { LoginRequest } from "@/types/user";

const router = useRouter();
const userStore = useUserStore();
const loginFormRef = ref<FormInstance>();

/**
 * 登录表单视图数据（用户名或邮箱 + 密码）
 */
const loginForm = reactive({
  account: "admin",
  password: "password",
});

/**
 * 表单验证规则
 */
const loginRules: FormRules = {
  account: [{ required: true, message: "请输入用户名或邮箱", trigger: "blur" }],
  password: [
    { required: true, message: "请输入密码", trigger: "blur" },
    { min: 6, max: 20, message: "密码长度在 6 到 20 个字符", trigger: "blur" },
  ],
};

/**
 * 提交登录
 * 将单一输入的“用户名或邮箱”映射为后端所需的 `username` 或 `email` 字段
 */
const handleLogin = async () => {
  if (!loginFormRef.value) return;

  try {
    const valid = await loginFormRef.value.validate();
    if (!valid) return;

    const isEmail = /.+@.+\..+/.test(loginForm.account);
    const payload: LoginRequest = {
      password: loginForm.password,
      ...(isEmail
        ? { email: loginForm.account }
        : { username: loginForm.account }),
    };

    await userStore.login(payload);

    // 跳转到仪表盘或之前访问的页面
    const redirect = router.currentRoute.value.query.redirect as string;
    router.push(redirect || "/dashboard");
  } catch (error: any) {
    console.error("登录失败:", error);
    // 错误消息已在store中处理
  }
};

/**
 * 处理测试登录
 */
/**
 * 处理测试登录
 */
const handleTestLogin = async () => {
  try {
    // 使用默认的测试账号
    const testLoginData: LoginRequest = {
      username: "admin",
      password: "password",
    };

    await userStore.login(testLoginData);

    // 跳转到仪表盘
    router.push("/dashboard");
  } catch (error: any) {
    console.error("测试登录失败:", error);
    // 错误消息已在store中处理
  }
};
</script>

<style lang="scss" scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.login-box {
  width: 100%;
  max-width: 400px;
  background: var(--el-bg-color);
  border-radius: 12px;
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.1);
  padding: 40px;

  .login-header {
    text-align: center;
    margin-bottom: 32px;

    .title {
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 24px;
      font-weight: 600;
      color: var(--el-text-color-primary);
      margin: 0 0 8px 0;

      .title-icon {
        margin-right: 8px;
        color: var(--el-color-primary);
        font-size: 28px;
      }
    }

    .subtitle {
      color: var(--el-text-color-regular);
      font-size: 14px;
      margin: 0;
    }
  }

  .login-form {
    .login-button {
      width: 100%;
      height: 44px;
      font-size: 16px;
      font-weight: 500;
    }

    .test-login-button {
      width: 100%;
      height: 44px;
      font-size: 16px;
      font-weight: 500;
      margin-top: 8px;
    }
  }

  .login-footer {
    text-align: center;
    margin-top: 24px;

    .tips {
      color: var(--el-text-color-placeholder);
      font-size: 12px;
      margin: 0;
    }
  }
}

// 响应式设计
@media (max-width: 480px) {
  .login-container {
    padding: 16px;
  }

  .login-box {
    padding: 24px;

    .login-header {
      margin-bottom: 24px;

      .title {
        font-size: 20px;
      }
    }
  }
}
</style>
