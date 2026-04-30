import { request } from '@/utils/request'

export enum FineTuningMethod {
  LORA = 'lora',
  QLORA = 'qlora',
  FULL = 'full',
  ADAPTOR = 'adaptor'
}

export enum FineTuningStatus {
  PENDING = 'pending',
  QUEUED = 'queued',
  RUNNING = 'running',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled',
  PREPARING = 'preparing'
}

export interface FineTuningJob {
  id: number
  job_id: string
  job_name: string
  base_model_name: string
  model_type?: string
  template?: string
  fine_tuned_model_name?: string
  method: FineTuningMethod
  dataset_name: string
  dataset_path?: string
  training_params?: string
  server_id?: number
  server_ip?: string
  ssh_port: number
  ssh_username?: string
  ssh_password?: string
  conda_env: string
  total_epochs: number
  output_path?: string
  remarks?: string
  status: FineTuningStatus
  progress: number
  current_epoch?: number
  started_at?: string
  completed_at?: string
  log_file?: string
  error_message?: string
  model_size?: number
  torch_dtype?: string
  max_length?: number
  split_dataset_ratio?: number
  gradient_accumulation_steps?: number
  learning_rate?: number
  eval_steps?: number
  lora_rank?: number
  lora_alpha?: number
  use_chat_template?: boolean
  task_type?: string
  num_labels?: number
  cuda_devices?: string
  model_status?: string
  model_service_port?: number
  model_service_pid?: number
  created_at: string
  updated_at: string
  created_by?: number
}

export interface FineTuningJobCreate {
  job_name: string
  base_model_name: string
  model_type?: string
  template?: string
  fine_tuned_model_name?: string
  method: FineTuningMethod
  dataset_name: string
  dataset_path?: string
  training_params?: string
  server_id?: number
  server_ip?: string
  ssh_port?: number
  ssh_username?: string
  ssh_password?: string
  conda_env?: string
  total_epochs?: number
  output_path?: string
  remarks?: string
  torch_dtype?: string
  max_length?: number
  gradient_accumulation_steps?: number
  learning_rate?: number
  eval_steps?: number
  use_chat_template?: boolean
  task_type?: string
  num_labels?: number
  cuda_devices?: string
}

export interface FineTuningJobUpdate {
  job_name?: string
  base_model_name?: string
  model_type?: string
  template?: string
  fine_tuned_model_name?: string
  method?: FineTuningMethod
  dataset_name?: string
  dataset_path?: string
  training_params?: string
  server_id?: number
  server_ip?: string
  ssh_port?: number
  ssh_username?: string
  ssh_password?: string
  conda_env?: string
  total_epochs?: number
  output_path?: string
  remarks?: string
  torch_dtype?: string
  max_length?: number
  gradient_accumulation_steps?: number
  learning_rate?: number
  eval_steps?: number
  use_chat_template?: boolean
  task_type?: string
  num_labels?: number
  cuda_devices?: string
  status?: FineTuningStatus
}

export interface FineTuningStats {
  total_jobs: number
  pending_jobs: number
  running_jobs: number
  completed_jobs: number
  failed_jobs: number
  cancelled_jobs: number
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  size: number
  pages: number
}

export const fineTuningApi = {
  getJobs(params?: {
    skip?: number
    limit?: number
    status?: FineTuningStatus
    method?: FineTuningMethod
    base_model_id?: number
    search?: string
  }) {
    return request.get<PaginatedResponse<FineTuningJob>>('/fine-tuning/', params)
  },

  getJob(jobId: number) {
    return request.get<FineTuningJob>(`/fine-tuning/${jobId}`)
  },

  getJobByJobId(jobId: string) {
    return request.get<FineTuningJob>(`/fine-tuning/job/${jobId}`)
  },

  createJob(data: FineTuningJobCreate) {
    return request.post<FineTuningJob>('/fine-tuning/', data)
  },

  updateJob(jobId: number, data: FineTuningJobUpdate) {
    return request.put<FineTuningJob>(`/fine-tuning/${jobId}`, data)
  },

  deleteJob(jobId: number) {
    return request.delete<void>(`/fine-tuning/${jobId}`)
  },

  startJob(jobId: number) {
    return request.post<{ message: string; job_id: string }>('/fine-tuning/start', { job_id: jobId })
  },

  cancelJob(jobId: number) {
    return request.post<{ message: string }>(`/fine-tuning/${jobId}/cancel`)
  },

  getJobLogs(jobId: string) {
    return request.get<{ log_content: string }>(`/fine-tuning/${jobId}/logs`)
  },

  getJobCurves(jobId: string) {
    return request.get<{
      job_id: string
      curves: {
        loss: { step: number; value: number }[]
        acc: { step: number; value: number }[]
        learning_rate: { step: number; value: number }[]
        grad_norm: { step: number; value: number }[]
        epoch: { step: number; value: number }[]
      }
    }>(`/fine-tuning/${jobId}/curves`)
  },

  getJobProgress(jobId: number) {
    return request.get<{
      job_id: string
      status: FineTuningStatus
      progress: number
      current_epoch?: number
      total_epochs: number
    }>(`/fine-tuning/${jobId}/progress`)
  },

  getStats() {
    return request.get<FineTuningStats>('/fine-tuning/stats')
  },

  uploadDataset(data: {
    server_ip: string
    ssh_port: number
    ssh_username: string
    ssh_password: string
    dataset_id: number
    target_filename?: string
  }) {
    return request.post<{
      success: boolean
      dataset_path: string
      filename: string
      file_size: number
    }>('/fine-tuning/upload-dataset', data)
  },

  startModelService(jobId: number, port?: number) {
    return request.post<{
      message: string
      model_status: string
      port: number
      pid?: number
      log_file?: string
    }>(`/fine-tuning/${jobId}/start-model`, { port: port })
  },

  stopModelService(jobId: number) {
    return request.post<{
      message: string
      model_status: string
    }>(`/fine-tuning/${jobId}/stop-model`)
  },

  chatWithModel(jobId: number, message: string, systemPrompt?: string) {
    return request.post<{
      response: string
      usage: {
        prompt_tokens: number
        completion_tokens: number
        total_tokens: number
      }
      model_status: string
    }>(`/fine-tuning/${jobId}/chat`, {
      message,
      system_prompt: systemPrompt
    })
  }
}