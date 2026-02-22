import request from './request'

// ==========================================
// 执行器分组管理
// ==========================================

export function getExecutorGroups(params) {
  return request({
    url: '/tasks/executor-groups',
    method: 'get',
    params
  })
}

export function createExecutorGroup(data) {
  return request({
    url: '/tasks/executor-groups',
    method: 'post',
    data
  })
}

export function updateExecutorGroup(id, data) {
  return request({
    url: `/tasks/executor-groups/${id}`,
    method: 'put',
    data
  })
}

export function deleteExecutorGroup(id) {
  return request({
    url: `/tasks/executor-groups/${id}`,
    method: 'delete'
  })
}

export function getExecutorNodes(params) {
  return request({
    url: '/executors/nodes',
    method: 'get',
    params
  })
}

export function getExecutorGroupNodes(groupId, params) {
  return request({
    url: `/tasks/executor-groups/${groupId}/nodes`,
    method: 'get',
    params
  })
}

// ==========================================
// 环境配置管理
// ==========================================

export function getEnvironments(params) {
  return request({
    url: '/environments/',
    method: 'get',
    params
  })
}

export function getEnvironment(id) {
  return request({
    url: `/environments/${id}`,
    method: 'get'
  })
}

export function createEnvironment(data) {
  return request({
    url: '/environments/',
    method: 'post',
    data
  })
}

export function updateEnvironment(id, data) {
  return request({
    url: `/environments/${id}`,
    method: 'put',
    data
  })
}

export function deleteEnvironment(id) {
  return request({
    url: `/environments/${id}`,
    method: 'delete'
  })
}
