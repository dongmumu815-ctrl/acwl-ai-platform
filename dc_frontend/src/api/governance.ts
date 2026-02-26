import { request } from '@/utils/request'
import type {
  GovernanceTable,
  GovernanceTableListQuery,
  GovernanceTableUpdate,
  GovernanceColumnUpdate
} from '@/types/governance'

export const governanceApi = {
  /**
   * 获取数据治理表列表
   */
  getTables(params: GovernanceTableListQuery) {
    return request<any, { items: GovernanceTable[]; total: number }>({
      url: '/governance/tables',
      method: 'GET',
      params
    })
  },

  /**
   * 获取数据治理表详情
   */
  getTable(id: number) {
    return request<any, GovernanceTable>({
      url: `/governance/tables/${id}`,
      method: 'GET'
    })
  },

  /**
   * 更新数据治理表信息
   */
  updateTable(id: number, data: GovernanceTableUpdate) {
    return request<any, GovernanceTable>({
      url: `/governance/tables/${id}`,
      method: 'PUT',
      data
    })
  },

  /**
   * 更新数据治理字段信息
   */
  updateColumn(id: number, data: GovernanceColumnUpdate) {
    return request<any, GovernanceTable['columns'][0]>({
      url: `/governance/columns/${id}`,
      method: 'PUT',
      data
    })
  }
}
