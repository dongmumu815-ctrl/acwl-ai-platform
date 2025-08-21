import { api } from './request'

/**
 * 数据源相关API
 */
export const datasourceApi = {
  /**
   * 获取数据源列表
   * @param {Object} params - 查询参数
   * @param {number} params.page - 页码
   * @param {number} params.size - 每页大小
   * @param {string} params.search - 搜索关键词
   * @param {string} params.datasource_type - 数据源类型
   * @param {string} params.status - 数据源状态
   * @param {boolean} params.is_enabled - 是否启用
   * @param {number} params.created_by - 创建者ID
   * @returns {Promise} 数据源列表响应
   */
  getDatasources(params = {}) {
    return api.get('/datasources/', params)
  },

  /**
   * 获取数据源详情
   * @param {number} id - 数据源ID
   * @returns {Promise} 数据源详情
   */
  getDatasourceDetail(id) {
    return api.get(`/datasources/${id}`)
  },

  /**
   * 创建数据源
   * @param {Object} data - 数据源数据
   * @returns {Promise} 创建结果
   */
  createDatasource(data) {
    return api.post('/datasources/', data)
  },

  /**
   * 更新数据源
   * @param {number} id - 数据源ID
   * @param {Object} data - 更新数据
   * @returns {Promise} 更新结果
   */
  updateDatasource(id, data) {
    return api.put(`/datasources/${id}`, data)
  },

  /**
   * 删除数据源
   * @param {number} id - 数据源ID
   * @returns {Promise} 删除结果
   */
  deleteDatasource(id) {
    return api.delete(`/datasources/${id}`)
  },

  /**
   * 测试数据源连接
   * @param {number} id - 数据源ID
   * @returns {Promise} 测试结果
   */
  testDatasourceConnection(id) {
    return api.post(`/datasources/${id}/test`)
  },

  /**
   * 获取启用的数据源列表（用于下拉选择）
   * @returns {Promise} 启用的数据源列表
   */
  getEnabledDatasources() {
    return api.get('/datasources/', {
      is_enabled: true,
      size: 100 // 获取所有启用的数据源
    })
  }
}

export default datasourceApi