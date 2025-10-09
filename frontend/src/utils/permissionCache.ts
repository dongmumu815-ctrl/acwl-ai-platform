/**
 * 权限缓存机制
 * 提供权限检查结果的缓存功能，提高性能
 */

import { ref, computed } from 'vue'
import type { PermissionConfig } from '@/types/router'

// 缓存接口
interface CacheItem {
  result: boolean
  timestamp: number
  ttl: number
}

interface PermissionCacheConfig {
  /** 默认缓存时间（毫秒） */
  defaultTTL: number
  /** 最大缓存条目数 */
  maxSize: number
  /** 是否启用缓存 */
  enabled: boolean
}

// 默认配置
const DEFAULT_CONFIG: PermissionCacheConfig = {
  defaultTTL: 5 * 60 * 1000, // 5分钟
  maxSize: 1000,
  enabled: true
}

/**
 * 权限缓存类
 */
class PermissionCache {
  private cache = new Map<string, CacheItem>()
  private config: PermissionCacheConfig
  private hitCount = 0
  private missCount = 0

  constructor(config: Partial<PermissionCacheConfig> = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config }
  }

  /**
   * 生成缓存键
   * @param userId 用户ID
   * @param config 权限配置
   * @returns 缓存键
   */
  private generateKey(userId: string, config: PermissionConfig): string {
    const parts = [
      userId,
      config.permission || '',
      Array.isArray(config.permission) ? config.permission.join(',') : '',
      config.role || '',
      Array.isArray(config.role) ? config.role.join(',') : '',
      config.mode || 'any'
    ]
    return parts.join('|')
  }

  /**
   * 检查缓存项是否过期
   * @param item 缓存项
   * @returns 是否过期
   */
  private isExpired(item: CacheItem): boolean {
    return Date.now() - item.timestamp > item.ttl
  }

  /**
   * 清理过期缓存
   */
  private cleanup(): void {
    const now = Date.now()
    for (const [key, item] of this.cache.entries()) {
      if (now - item.timestamp > item.ttl) {
        this.cache.delete(key)
      }
    }
  }

  /**
   * 限制缓存大小
   */
  private limitSize(): void {
    if (this.cache.size > this.config.maxSize) {
      // 删除最旧的条目
      const entries = Array.from(this.cache.entries())
      entries.sort((a, b) => a[1].timestamp - b[1].timestamp)
      
      const deleteCount = this.cache.size - this.config.maxSize + 100 // 多删除一些，避免频繁清理
      for (let i = 0; i < deleteCount && i < entries.length; i++) {
        this.cache.delete(entries[i][0])
      }
    }
  }

  /**
   * 获取缓存结果
   * @param userId 用户ID
   * @param config 权限配置
   * @returns 缓存的权限检查结果，如果不存在或过期则返回null
   */
  get(userId: string, config: PermissionConfig): boolean | null {
    if (!this.config.enabled) {
      return null
    }

    const key = this.generateKey(userId, config)
    const item = this.cache.get(key)

    if (!item) {
      this.missCount++
      return null
    }

    if (this.isExpired(item)) {
      this.cache.delete(key)
      this.missCount++
      return null
    }

    this.hitCount++
    return item.result
  }

  /**
   * 设置缓存结果
   * @param userId 用户ID
   * @param config 权限配置
   * @param result 权限检查结果
   * @param ttl 缓存时间（可选）
   */
  set(userId: string, config: PermissionConfig, result: boolean, ttl?: number): void {
    if (!this.config.enabled) {
      return
    }

    const key = this.generateKey(userId, config)
    const item: CacheItem = {
      result,
      timestamp: Date.now(),
      ttl: ttl || this.config.defaultTTL
    }

    this.cache.set(key, item)

    // 定期清理和限制大小
    if (this.cache.size % 100 === 0) {
      this.cleanup()
      this.limitSize()
    }
  }

  /**
   * 清除指定用户的所有缓存
   * @param userId 用户ID
   */
  clearUser(userId: string): void {
    const keysToDelete: string[] = []
    for (const key of this.cache.keys()) {
      if (key.startsWith(userId + '|')) {
        keysToDelete.push(key)
      }
    }
    keysToDelete.forEach(key => this.cache.delete(key))
  }

  /**
   * 清除所有缓存
   */
  clear(): void {
    this.cache.clear()
    this.hitCount = 0
    this.missCount = 0
  }

  /**
   * 获取缓存统计信息
   */
  getStats() {
    return {
      size: this.cache.size,
      hitCount: this.hitCount,
      missCount: this.missCount,
      hitRate: this.hitCount + this.missCount > 0 ? this.hitCount / (this.hitCount + this.missCount) : 0,
      config: this.config
    }
  }

  /**
   * 更新配置
   * @param config 新配置
   */
  updateConfig(config: Partial<PermissionCacheConfig>): void {
    this.config = { ...this.config, ...config }
    
    if (!this.config.enabled) {
      this.clear()
    }
  }
}

// 全局缓存实例
const permissionCache = new PermissionCache()

// 响应式缓存统计
const cacheStats = ref(permissionCache.getStats())

// 更新统计信息
const updateStats = () => {
  cacheStats.value = permissionCache.getStats()
}

// 定期更新统计信息
setInterval(updateStats, 10000) // 每10秒更新一次

/**
 * 权限缓存组合式函数
 */
export function usePermissionCache() {
  return {
    cache: permissionCache,
    stats: computed(() => cacheStats.value),
    
    /**
     * 获取缓存结果
     */
    getCached: (userId: string, config: PermissionConfig) => {
      return permissionCache.get(userId, config)
    },
    
    /**
     * 设置缓存结果
     */
    setCached: (userId: string, config: PermissionConfig, result: boolean, ttl?: number) => {
      permissionCache.set(userId, config, result, ttl)
      updateStats()
    },
    
    /**
     * 清除用户缓存
     */
    clearUserCache: (userId: string) => {
      permissionCache.clearUser(userId)
      updateStats()
    },
    
    /**
     * 清除所有缓存
     */
    clearAllCache: () => {
      permissionCache.clear()
      updateStats()
    },
    
    /**
     * 更新缓存配置
     */
    updateCacheConfig: (config: Partial<PermissionCacheConfig>) => {
      permissionCache.updateConfig(config)
      updateStats()
    }
  }
}

// 导出缓存实例和配置类型
export { permissionCache, type PermissionCacheConfig }