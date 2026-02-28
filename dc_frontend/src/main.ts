import { createApp } from "vue";
import { createPinia } from "pinia";
import ElementPlus from "element-plus";
import "element-plus/dist/index.css";
import "element-plus/theme-chalk/dark/css-vars.css";
import * as ElementPlusIconsVue from "@element-plus/icons-vue";
import zhCn from "element-plus/dist/locale/zh-cn.mjs";

import App from "./App.vue";
import router from "./router";
import { useUserStore } from "@/stores/user";
import "./styles/index.scss";
import { initUITracker } from "@/utils/uiTracker";

/**
 * 初始化应用
 */
async function initApp() {
  const app = createApp(App);

  // 注册Element Plus图标
  for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
    app.component(key, component);
  }

  // 初始化Pinia
  app.use(createPinia());

  // 恢复用户状态
  const userStore = useUserStore();
  userStore.restoreFromStorage();
  await userStore.refreshPermissions();

  // 初始化路由
  app.use(router);

  // 初始化Element Plus
  app.use(ElementPlus, {
    locale: zhCn,
  });

  // 初始化全局埋点（路由与点击）
  initUITracker(router);

  app.mount("#app");
}

// 启动应用
initApp().catch(console.error);
