import { defineStore } from "pinia";
import { ref, computed } from "vue";

/**
 * 主题类型
 */
export type Theme = "light" | "dark" | "auto";

/**
 * 语言类型
 */
export type Language = "zh-CN" | "en-US";

/**
 * 侧边栏状态
 */
interface SidebarState {
  collapsed: boolean;
  withoutAnimation: boolean;
}

/**
 * 应用设置
 */
interface AppSettings {
  theme: Theme;
  language: Language;
  showBreadcrumb: boolean;
  showFooter: boolean;
  showSettings: boolean;
  fixedHeader: boolean;
  sidebarLogo: boolean;
  tagsView: boolean;
  pageSize: number;
}

/**
 * 应用状态管理
 * 管理全局应用状态，包括主题、语言、侧边栏等
 */
export const useAppStore = defineStore("app", () => {
  // 状态
  const sidebar = ref<SidebarState>({
    collapsed: false,
    withoutAnimation: false,
  });

  const settings = ref<AppSettings>({
    theme: "light",
    language: "zh-CN",
    showBreadcrumb: true,
    showFooter: true,
    showSettings: false,
    fixedHeader: true,
    sidebarLogo: true,
    tagsView: false,
    pageSize: 20,
  });

  const cachedViews = ref<string[]>([]);
  const visitedViews = ref<any[]>([]);
  const loading = ref(false);
  const device = ref<"desktop" | "mobile">("desktop");

  // 计算属性
  const theme = computed(() => settings.value.theme);
  const language = computed(() => settings.value.language);
  const isDark = computed(() => {
    if (settings.value.theme === "auto") {
      return window.matchMedia("(prefers-color-scheme: dark)").matches;
    }
    return settings.value.theme === "dark";
  });
  const isMobile = computed(() => device.value === "mobile");

  /**
   * 切换侧边栏折叠状态
   * @param withoutAnimation 是否禁用动画
   */
  const toggleSidebar = (withoutAnimation = false): void => {
    sidebar.value.collapsed = !sidebar.value.collapsed;
    sidebar.value.withoutAnimation = withoutAnimation;

    // 保存到本地存储
    localStorage.setItem(
      "sidebar-collapsed",
      sidebar.value.collapsed.toString(),
    );
  };

  /**
   * 关闭侧边栏
   * @param withoutAnimation 是否禁用动画
   */
  const closeSidebar = (withoutAnimation = false): void => {
    sidebar.value.collapsed = true;
    sidebar.value.withoutAnimation = withoutAnimation;

    localStorage.setItem("sidebar-collapsed", "true");
  };

  /**
   * 打开侧边栏
   * @param withoutAnimation 是否禁用动画
   */
  const openSidebar = (withoutAnimation = false): void => {
    sidebar.value.collapsed = false;
    sidebar.value.withoutAnimation = withoutAnimation;

    localStorage.setItem("sidebar-collapsed", "false");
  };

  /**
   * 切换主题
   * @param newTheme 新主题
   */
  const toggleTheme = (newTheme?: Theme): void => {
    if (newTheme) {
      settings.value.theme = newTheme;
    } else {
      settings.value.theme =
        settings.value.theme === "light" ? "dark" : "light";
    }

    // 应用主题
    applyTheme();

    // 保存到本地存储
    localStorage.setItem("app-theme", settings.value.theme);
  };

  /**
   * 应用主题
   */
  const applyTheme = (): void => {
    const html = document.documentElement;

    if (isDark.value) {
      html.classList.add("dark");
      html.setAttribute("data-theme", "dark");
    } else {
      html.classList.remove("dark");
      html.setAttribute("data-theme", "light");
    }
  };

  /**
   * 切换语言
   * @param newLanguage 新语言
   */
  const toggleLanguage = (newLanguage: Language): void => {
    settings.value.language = newLanguage;

    // 保存到本地存储
    localStorage.setItem("app-language", newLanguage);

    // TODO: 更新i18n语言
  };

  /**
   * 更新应用设置
   * @param newSettings 新设置
   */
  const updateSettings = (newSettings: Partial<AppSettings>): void => {
    Object.assign(settings.value, newSettings);

    // 保存到本地存储
    localStorage.setItem("app-settings", JSON.stringify(settings.value));

    // 如果主题发生变化，应用主题
    if (newSettings.theme) {
      applyTheme();
    }
  };

  /**
   * 设置设备类型
   * @param deviceType 设备类型
   */
  const setDevice = (deviceType: "desktop" | "mobile"): void => {
    device.value = deviceType;

    // 移动端自动折叠侧边栏
    if (deviceType === "mobile" && !sidebar.value.collapsed) {
      closeSidebar(true);
    }
  };

  /**
   * 添加缓存视图
   * @param viewName 视图名称
   */
  const addCachedView = (viewName: string): void => {
    if (!cachedViews.value.includes(viewName)) {
      cachedViews.value.push(viewName);
    }
  };

  /**
   * 删除缓存视图
   * @param viewName 视图名称
   */
  const deleteCachedView = (viewName: string): void => {
    const index = cachedViews.value.indexOf(viewName);
    if (index > -1) {
      cachedViews.value.splice(index, 1);
    }
  };

  /**
   * 清空缓存视图
   */
  const clearCachedViews = (): void => {
    cachedViews.value = [];
  };

  /**
   * 添加访问视图
   * @param view 视图信息
   */
  const addVisitedView = (view: any): void => {
    const existingView = visitedViews.value.find((v) => v.path === view.path);
    if (!existingView) {
      visitedViews.value.push({
        name: view.name,
        path: view.path,
        title: view.meta?.title || view.name,
        meta: view.meta,
      });
    }
  };

  /**
   * 删除访问视图
   * @param view 视图信息
   */
  const deleteVisitedView = (view: any): void => {
    const index = visitedViews.value.findIndex((v) => v.path === view.path);
    if (index > -1) {
      visitedViews.value.splice(index, 1);
    }
  };

  /**
   * 清空访问视图
   */
  const clearVisitedViews = (): void => {
    visitedViews.value = [];
  };

  /**
   * 设置加载状态
   * @param isLoading 是否加载中
   */
  const setLoading = (isLoading: boolean): void => {
    loading.value = isLoading;
  };

  /**
   * 从本地存储恢复状态
   */
  const restoreFromStorage = (): void => {
    try {
      // 恢复侧边栏状态
      const sidebarCollapsed = localStorage.getItem("sidebar-collapsed");
      if (sidebarCollapsed !== null) {
        sidebar.value.collapsed = sidebarCollapsed === "true";
      }

      // 恢复主题
      const theme = localStorage.getItem("app-theme") as Theme;
      if (theme) {
        settings.value.theme = theme;
      }

      // 恢复语言
      const language = localStorage.getItem("app-language") as Language;
      if (language) {
        settings.value.language = language;
      }

      // 恢复应用设置
      const appSettings = localStorage.getItem("app-settings");
      if (appSettings) {
        const parsedSettings = JSON.parse(appSettings);
        Object.assign(settings.value, parsedSettings);
      }

      // 应用主题
      applyTheme();
    } catch (error) {
      console.error("恢复应用状态失败:", error);
    }
  };

  /**
   * 重置应用状态
   */
  const reset = (): void => {
    sidebar.value = {
      collapsed: false,
      withoutAnimation: false,
    };

    settings.value = {
      theme: "light",
      language: "zh-CN",
      showBreadcrumb: true,
      showFooter: true,
      showSettings: false,
      fixedHeader: true,
      sidebarLogo: true,
      tagsView: false,
      pageSize: 20,
    };

    cachedViews.value = [];
    visitedViews.value = [];
    loading.value = false;
    device.value = "desktop";

    // 清除本地存储
    localStorage.removeItem("sidebar-collapsed");
    localStorage.removeItem("app-theme");
    localStorage.removeItem("app-language");
    localStorage.removeItem("app-settings");
  };

  /**
   * 监听系统主题变化
   */
  const watchSystemTheme = (): void => {
    if (window.matchMedia) {
      const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");

      const handleChange = () => {
        if (settings.value.theme === "auto") {
          applyTheme();
        }
      };

      mediaQuery.addEventListener("change", handleChange);

      // 返回清理函数
      return () => {
        mediaQuery.removeEventListener("change", handleChange);
      };
    }
  };

  // 初始化时从本地存储恢复状态
  restoreFromStorage();

  // 监听系统主题变化
  watchSystemTheme();

  return {
    // 状态
    sidebar,
    settings,
    cachedViews,
    visitedViews,
    loading,
    device,

    // 计算属性
    theme,
    language,
    isDark,
    isMobile,

    // 方法
    toggleSidebar,
    closeSidebar,
    openSidebar,
    toggleTheme,
    applyTheme,
    toggleLanguage,
    updateSettings,
    setDevice,
    addCachedView,
    deleteCachedView,
    clearCachedViews,
    addVisitedView,
    deleteVisitedView,
    clearVisitedViews,
    setLoading,
    restoreFromStorage,
    reset,
    watchSystemTheme,
  };
});

/**
 * 应用状态管理类型定义
 */
export type AppStore = ReturnType<typeof useAppStore>;
