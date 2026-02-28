/**
 * 外部API配置文件
 * 用于配置外部系统的接口地址
 */

// DataAInsint项目的API配置
export const DATA_INSIGHT_CONFIG = {
  // 基础URL - 可以根据环境进行配置
  baseURL:
    process.env.NODE_ENV === "production"
      ? "http://10.20.1.200:8001/dataainsight/api" // 生产环境地址
      : "http://10.20.1.200:8001/dataainsight/api", // 开发环境地址

  // 请求超时时间
  timeout: 600000, // 10分钟

  // API端点
  endpoints: {
    // 数据源相关
    datasource: {
      testConnection: "/datasource/test-connection",
      create: "/datasource/",
      getList: "/datasource/",
      getById: (id: number) => `/datasource/${id}`,
      update: (id: number) => `/datasource/${id}`,
      delete: (id: number) => `/datasource/${id}`,
    },

    // 数据探索相关
    explorer: {
      // 获取模式列表
      getSchemas: (datasourceId: number) => `/explorer/schemas/${datasourceId}`,

      // 获取表列表
      getTables: (datasourceId: number) => `/explorer/tables/${datasourceId}`,

      // 根据模式获取表列表
      getTablesBySchema: (datasourceId: number, schema: string) =>
        `/explorer/tables/${datasourceId}/${schema}`,

      // 获取表详情
      getTableDetail: (datasourceId: number, tableName: string) =>
        `/explorer/table-detail/${datasourceId}/${tableName}`,

      // 获取表数据
      getTableData: "/explorer/table-data",

      // 执行SQL
      executeSQL: "/explorer/execute-sql",

      // SQL历史相关
      saveSQLHistory: "/explorer/sql-history",
      getSQLHistory: (datasourceId: number) =>
        `/explorer/sql-history/${datasourceId}`,
      getSQLHistoryDetail: (historyId: number) =>
        `/explorer/sql-history-detail/${historyId}`,
      deleteSQLHistory: (historyId: number) =>
        `/explorer/sql-history/${historyId}`,

      // 导出相关
      exportSQLResult: "/explorer/export-sql-result",

      // 表结构操作
      modifyTableStructure: "/explorer/table-structure/modify",
      updateField: "/explorer/table-structure/modify",
      createTable: "/explorer/table/create",
      createTableByDDL: "/explorer/table/create-by-ddl",

      // 表变更日志
      getTableChangeLog: (datasourceId: number) =>
        `/explorer/table-change-log/${datasourceId}`,
    },
  },
};

// 其他外部系统配置可以在这里添加
export const OTHER_SYSTEM_CONFIG = {
  // 示例：其他系统的配置
  // baseURL: 'http://other-system-api.com',
  // endpoints: { ... }
};
