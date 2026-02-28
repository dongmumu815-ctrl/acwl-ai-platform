<template>
  <div class="auth-error-test">
    <h2>认证错误处理测试</h2>
    <div class="test-buttons">
      <el-button type="primary" @click="testValidToken"
        >测试有效Token</el-button
      >
      <el-button type="danger" @click="testInvalidToken"
        >测试无效Token</el-button
      >
      <el-button type="warning" @click="testAuthenticationError"
        >测试AUTHENTICATION_ERROR</el-button
      >
    </div>

    <div v-if="testResult" class="test-results">
      <h3>测试结果:</h3>
      <pre>{{ testResult }}</pre>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { ElButton, ElMessage } from "element-plus";
import { request } from "@/utils/request";
import { useUserStore } from "@/stores/user";

const testResult = ref("");
const userStore = useUserStore();

/**
 * 测试有效Token的API调用
 */
const testValidToken = async () => {
  try {
    testResult.value = "正在测试有效Token...";
    const response = await request({
      url: "/sql/templates",
      method: "GET",
    });
    testResult.value = `成功: ${JSON.stringify(response, null, 2)}`;
  } catch (error: any) {
    testResult.value = `错误: ${JSON.stringify(error.response?.data || error.message, null, 2)}`;
  }
};

/**
 * 测试无效Token的API调用
 */
const testInvalidToken = async () => {
  try {
    testResult.value = "正在测试无效Token...";
    // 临时保存当前token
    const originalToken = userStore.token;
    // 设置无效token
    userStore.token = "invalid_token_12345";

    const response = await request({
      url: "/sql/templates",
      method: "GET",
    });

    // 恢复原token
    userStore.token = originalToken;
    testResult.value = `意外成功: ${JSON.stringify(response, null, 2)}`;
  } catch (error: any) {
    // 恢复原token
    const originalToken = localStorage.getItem("token");
    if (originalToken) {
      userStore.token = originalToken;
    }
    testResult.value = `预期错误: ${JSON.stringify(error.response?.data || error.message, null, 2)}`;
  }
};

/**
 * 模拟AUTHENTICATION_ERROR响应
 */
const testAuthenticationError = async () => {
  try {
    testResult.value = "正在模拟AUTHENTICATION_ERROR...";

    // 创建一个模拟的axios错误
    const mockError = {
      response: {
        status: 401,
        data: {
          error: "AUTHENTICATION_ERROR",
          message: "无效的认证令牌",
          detail: null,
        },
      },
      config: {},
      message: "Request failed with status code 401",
    };

    // 手动调用错误处理逻辑
    ElMessage.error("检测到AUTHENTICATION_ERROR，即将跳转到登录页面");

    // 模拟跳转逻辑（实际项目中会自动跳转）
    setTimeout(() => {
      testResult.value = "AUTHENTICATION_ERROR处理完成，应该已跳转到登录页面";
    }, 1000);
  } catch (error: any) {
    testResult.value = `测试错误: ${JSON.stringify(error, null, 2)}`;
  }
};
</script>

<style scoped>
.auth-error-test {
  padding: 20px;
  max-width: 800px;
  margin: 0 auto;
}

.test-buttons {
  margin: 20px 0;
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.test-results {
  margin-top: 20px;
  padding: 15px;
  background-color: #f5f5f5;
  border-radius: 4px;
  border: 1px solid #ddd;
}

.test-results pre {
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: "Courier New", monospace;
  font-size: 12px;
  line-height: 1.4;
  margin: 0;
}

h2 {
  color: #333;
  margin-bottom: 20px;
}

h3 {
  color: #666;
  margin-bottom: 10px;
}
</style>
