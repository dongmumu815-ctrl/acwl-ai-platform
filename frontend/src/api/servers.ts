// import request from '@/utils/request'
import { request } from '@/utils/request'


export interface ServerForm {
  name: string
  ip_address: string
  ssh_port: number
  ssh_username: string
  ssh_password: string
  server_type: string
  os_info: string
  total_memory: string
  total_storage: string
  total_cpu_cores: number | null
}

export function createServer(data: ServerForm) {
  return request({
    url: '/servers',
    method: 'post',
    data
  })
}

export function updateServer(id: number, data: ServerForm) {
  return request({
    url: `/servers/${id}`,
    method: 'put',
    data
  })
}

export function getServers() {
  return request({
    url: '/servers',
    method: 'get'
  })
}


// import request from '@/utils/request'

// // 创建服务器
// export const createServer = data => request.post('/servers', data)

// // 更新服务器
// export const updateServer = (id, data) => request.put(`/servers/${id}`, data)
