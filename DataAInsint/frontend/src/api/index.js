import axios from 'axios'
import { ElMessage } from 'element-plus'
import { getToken, logout } from './auth'
import router from '@/router'

// 创建axios实例
const api = axios.create({
  baseURL: '/dataainsight/api',
  timeout: 600000, // 10分钟超时
  headers: {
    'Content-Type': 'application/json'
  }
});

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // 添加认证token
    const token = getToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    const status = error.response?.status
    const message = error.response?.data?.detail || error.message || '请求失败'
    
    // 处理401未授权错误
    if (status === 401) {
      ElMessage.error('登录已过期，请重新登录')
      logout()
      router.push('./login')
      return Promise.reject(error)
    }
    
    ElMessage.error(message)
    return Promise.reject(error)
  }
)

// 数据源相关API
export const datasourceAPI = {
  // 测试连接
  testConnection: (data) => api.post('/datasource/test-connection', data),
  
  // 创建数据源
  create: (data) => api.post('/datasource/', data),
  
  // 获取所有数据源
  getList: () => api.get('/datasource/'),
  
  // 获取指定数据源
  getById: (id) => api.get(`/datasource/${id}`),
  
  // 更新数据源
  update: (id, data) => api.put(`/datasource/${id}`, data),
  
  // 删除数据源
  delete: (id) => api.delete(`/datasource/${id}`)
}

// 数据探查相关API
export const explorerAPI = {
  // 获取表列表
  getTables: (datasource) => api.get(`/explorer/tables/${datasource.id}`),
  
  // 获取模式列表
  getSchemas: (datasource) => api.get(`/explorer/schemas/${datasource.id}`),
  
  // 根据模式获取表列表
  getTablesBySchema: (datasource, schema) => api.get(`/explorer/tables/${datasource.id}/${schema}`),
  
  // 获取表详情
  getTableDetail: (datasource, tableName, schema = null) => {
    const url = `/explorer/table-detail/${datasource.id}/${tableName}`
    const params = schema ? { schema } : {}
    return api.get(url, { params })
  },
  
  // 获取表数据
  getTableData: (params) => api.post('/explorer/table-data', params),
  
  // 执行SQL
  executeSQL: (params) => api.post('/explorer/execute-sql', params),
  
  // 保存SQL历史
  saveSQLHistory: (data) => api.post('/explorer/sql-history', data),
  
  // 获取SQL历史
  getSQLHistory: (datasourceId) => api.get(`/explorer/sql-history/${datasourceId}`),
  
  // 获取SQL历史详情
  getSQLHistoryDetail: (historyId) => api.get(`/explorer/sql-history-detail/${historyId}`),
  
  // 删除SQL历史
  deleteSQLHistory: (historyId) => api.delete(`/explorer/sql-history/${historyId}`),
  
  // 导出SQL结果
  exportSQLResult: (data) => {
    return axios({
      method: 'post',
      url: '/dataainsight/api/explorer/export-sql-result',
      data: data,
      responseType: 'blob',
      timeout: 600000, // 10分钟超时
      headers: {
        'Authorization': `Bearer ${getToken()}`
      }
    })
  },
  
  // 修改表结构
  modifyTableStructure: (data) => {
    return api.post('/explorer/table-structure/modify', data)
  },
  
  // 创建表（向导模式）
  createTable: (data) => {
    return api.post('/explorer/table/create', data)
  },
  
  // 执行DDL语句
  executeDDL: (data) => {
    return api.post('/explorer/table/create-by-ddl', data)
  },
  
  // 获取表结构变更日志
  getTableChangeLog: (datasourceId, tableName) => {
    const params = tableName ? { table_name: tableName } : {}
    return api.get(`/explorer/table-change-log/${datasourceId}`, { params })
  }
}

export default api