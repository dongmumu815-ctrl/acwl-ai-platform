import request from '@/utils/request'

export interface ServerGroup {
  id: number
  name: str
  description?: str
  server_count: number
  created_at: str
  updated_at: str
}

export interface CreateServerGroupParams {
  name: str
  description?: str
}

export interface UpdateServerGroupParams {
  name?: str
  description?: str
}

export function getServerGroups(params?: any) {
  return request({
    url: '/server-groups/',
    method: 'get',
    params
  })
}

export function createServerGroup(data: CreateServerGroupParams) {
  return request({
    url: '/server-groups/',
    method: 'post',
    data
  })
}

export function updateServerGroup(id: number, data: UpdateServerGroupParams) {
  return request({
    url: `/server-groups/${id}`,
    method: 'put',
    data
  })
}

export function deleteServerGroup(id: number) {
  return request({
    url: `/server-groups/${id}`,
    method: 'delete'
  })
}
