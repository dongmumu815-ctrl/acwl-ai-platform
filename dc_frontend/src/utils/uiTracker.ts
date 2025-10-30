import type { Router } from 'vue-router'
import { post } from '@/utils/request'
import { useUserStore } from '@/stores/user'

interface UIEventPayload {
  event_type: 'route_change' | 'click' | 'custom';
  page_path: string;
  page_title?: string;
  timestamp: number;
  // 用户信息（可选，后端中间件也会从token解码）
  user_id?: number | null;
  username?: string | null;
  // 路由信息
  route_name?: string | null;
  route_params?: Record<string, any> | null;
  route_query?: Record<string, any> | null;
  // 元信息
  user_agent?: string;
  screen?: { width: number; height: number };
  // 点击元素信息
  element?: {
    tag?: string;
    id?: string;
    class?: string;
    text?: string;
    href?: string | null;
    dataset?: Record<string, any>;
  } | null;
  // 额外扩展数据
  extra?: Record<string, any> | null;
}

// 轻量去噪：限制点击文本长度
const sanitizeText = (t?: string | null, max = 120): string | undefined => {
  if (!t) return undefined
  const s = t.replace(/\s+/g, ' ').trim()
  return s.length > max ? s.slice(0, max) + '…' : s
}

// 将 dataset 转为普通对象
const datasetToObject = (el: HTMLElement): Record<string, any> => {
  const obj: Record<string, any> = {}
  const ds = (el as any).dataset || {}
  for (const k of Object.keys(ds)) {
    obj[k] = ds[k]
  }
  return obj
}

const sendEvent = async (payload: UIEventPayload) => {
  try {
    // 走统一 request 封装，自动带 token、请求ID
    await post('/user-operation-logs/ui-event', payload, {
      skipErrorHandler: true,
      showSuccessMessage: false
    })
  } catch (e) {
    // 静默失败避免影响用户操作
    // 可选：在页面关闭时用 sendBeacon 兜底
    try {
      if (navigator.sendBeacon) {
        const url = (import.meta.env.VITE_API_BASE_URL || '/api/v1') + '/user-operation-logs/ui-event'
        const blob = new Blob([JSON.stringify(payload)], { type: 'application/json' })
        navigator.sendBeacon(url, blob)
      }
    } catch {}
  }
}

export const initUITracker = (router: Router) => {
  const userStore = useUserStore()

  // 路由变化埋点
  router.afterEach((to, from) => {
    const payload: UIEventPayload = {
      event_type: 'route_change',
      page_path: to.fullPath,
      page_title: document.title,
      timestamp: Date.now(),
      user_id: (userStore.user?.id as any) ?? null,
      username: userStore.user?.username ?? null,
      route_name: (to.name as string) || null,
      route_params: to.params ? { ...to.params } : null,
      route_query: to.query ? { ...to.query } : null,
      user_agent: navigator.userAgent,
      screen: { width: window.screen.width, height: window.screen.height },
      element: null,
      extra: {
        from: from.fullPath || null
      }
    }
    void sendEvent(payload)
  })

  // 全局点击埋点（捕获阶段）
  const onClick = (ev: Event) => {
    const target = ev.target as HTMLElement | null
    if (!target) return

    // 仅采集可见元素的基本信息
    const el = target.closest('[data-track], button, a, [role="button"], .el-button, .el-link') as HTMLElement | null
    const text = sanitizeText((el?.innerText || target.innerText || '').trim())
    const href = (el as HTMLAnchorElement)?.href || null

    const payload: UIEventPayload = {
      event_type: 'click',
      page_path: router.currentRoute.value.fullPath,
      page_title: document.title,
      timestamp: Date.now(),
      user_id: (userStore.user?.id as any) ?? null,
      username: userStore.user?.username ?? null,
      route_name: (router.currentRoute.value.name as string) || null,
      route_params: router.currentRoute.value.params ? { ...router.currentRoute.value.params } : null,
      route_query: router.currentRoute.value.query ? { ...router.currentRoute.value.query } : null,
      user_agent: navigator.userAgent,
      screen: { width: window.screen.width, height: window.screen.height },
      element: el ? {
        tag: el.tagName,
        id: el.id || undefined,
        class: el.className || undefined,
        text,
        href,
        dataset: datasetToObject(el)
      } : null,
      extra: null
    }

    // 节流：避免同一秒内密集点击造成大量上报
    // 简单节流：如果文本和路径相同且在500ms内，忽略（可继续优化）
    const now = Date.now()
    if ((window as any).__lastClick) {
      const last = (window as any).__lastClick as { t: number; path: string; text?: string }
      if (now - last.t < 500 && last.path === payload.page_path && last.text === text) {
        return
      }
    }
    ;(window as any).__lastClick = { t: now, path: payload.page_path, text }

    void sendEvent(payload)
  }

  document.addEventListener('click', onClick, true)

  // 页面关闭兜底：发送最后的停留信息
  const onBeforeUnload = () => {
    const payload: UIEventPayload = {
      event_type: 'custom',
      page_path: router.currentRoute.value.fullPath,
      page_title: document.title,
      timestamp: Date.now(),
      user_id: (userStore.user?.id as any) ?? null,
      username: userStore.user?.username ?? null,
      route_name: (router.currentRoute.value.name as string) || null,
      route_params: router.currentRoute.value.params ? { ...router.currentRoute.value.params } : null,
      route_query: router.currentRoute.value.query ? { ...router.currentRoute.value.query } : null,
      user_agent: navigator.userAgent,
      screen: { width: window.screen.width, height: window.screen.height },
      element: null,
      extra: { reason: 'beforeunload' }
    }

    try {
      if (navigator.sendBeacon) {
        const url = (import.meta.env.VITE_API_BASE_URL || '/api/v1') + '/user-operation-logs/ui-event'
        const blob = new Blob([JSON.stringify(payload)], { type: 'application/json' })
        navigator.sendBeacon(url, blob)
      }
    } catch {}
  }

  window.addEventListener('beforeunload', onBeforeUnload)
}