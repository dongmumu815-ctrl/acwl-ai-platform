/**
 * 指令集相关的API服务
 */

import { request } from '@/utils/request';
import type {
  InstructionSet,
  InstructionSetCreate,
  InstructionSetUpdate,
  InstructionSetQuery,
  InstructionNode,
  InstructionNodeCreate,
  InstructionNodeUpdate,
  InstructionNodeQuery,
  InstructionExecution,
  InstructionExecutionQuery,
  InstructionExecuteRequest,
  InstructionExecuteResponse,
  InstructionTreeNode,
  InstructionSetStatistics,
  ApiResponse,
  PaginatedResponse,
  InstructionSetListResponse
} from '@/types/instruction-set';

const API_PREFIX = '/instruction-sets';

/**
 * 指令集相关API
 */
export const instructionSetApi = {
  /**
   * 获取指令集列表
   */
  getInstructionSets: (params?: InstructionSetQuery): Promise<InstructionSetListResponse> => {
    return request.get(API_PREFIX, { params });
  },

  /**
   * 创建指令集
   */
  createInstructionSet: (data: InstructionSetCreate): Promise<ApiResponse<InstructionSet>> => {
    return request.post(API_PREFIX, data);
  },

  /**
   * 获取指令集详情
   */
  getInstructionSet: (id: number): Promise<ApiResponse<InstructionSet>> => {
    return request.get(`${API_PREFIX}/${id}`);
  },

  /**
   * 更新指令集
   */
  updateInstructionSet: (id: number, data: InstructionSetUpdate): Promise<ApiResponse<InstructionSet>> => {
    return request.put(`${API_PREFIX}/${id}`, data);
  },

  /**
   * 删除指令集
   */
  deleteInstructionSet: (id: number): Promise<ApiResponse<void>> => {
    return request.delete(`${API_PREFIX}/${id}`);
  },

  /**
   * 获取指令集树形结构
   */
  getInstructionSetTree: (id: number): Promise<ApiResponse<InstructionTreeNode[]>> => {
    return request.get(`${API_PREFIX}/${id}/tree`);
  },

  /**
   * 获取指令集统计信息
   */
  getInstructionSetStatistics: (id: number): Promise<ApiResponse<InstructionSetStatistics>> => {
    return request.get(`${API_PREFIX}/${id}/statistics`);
  }
};

/**
 * 指令节点相关API
 */
export const instructionNodeApi = {
  /**
   * 获取指令节点列表
   */
  getInstructionNodes: (instructionSetId: number, params?: InstructionNodeQuery): Promise<ApiResponse<InstructionNode[]>> => {
    return request.get(`${API_PREFIX}/${instructionSetId}/nodes`, { params });
  },

  /**
   * 获取指令集树结构
   */
  getInstructionTree: (instructionSetId: number): Promise<ApiResponse<InstructionTreeNode[]>> => {
    return request.get(`${API_PREFIX}/${instructionSetId}/tree`);
  },

  /**
   * 创建指令节点
   */
  createInstructionNode: (instructionSetId: number, data: InstructionNodeCreate): Promise<ApiResponse<InstructionNode>> => {
    return request.post(`${API_PREFIX}/${instructionSetId}/nodes`, data);
  },

  /**
   * 获取指令节点详情
   */
  getInstructionNode: (nodeId: number): Promise<ApiResponse<InstructionNode>> => {
    return request.get(`${API_PREFIX}/nodes/${nodeId}`);
  },

  /**
   * 更新指令节点
   */
  updateInstructionNode: (nodeId: number, data: InstructionNodeUpdate): Promise<ApiResponse<InstructionNode>> => {
    return request.put(`${API_PREFIX}/nodes/${nodeId}`, data);
  },

  /**
   * 删除指令节点
   */
  deleteInstructionNode: (nodeId: number): Promise<ApiResponse<void>> => {
    return request.delete(`${API_PREFIX}/nodes/${nodeId}`);
  },

  /**
   * 移动指令节点
   */
  moveInstructionNode: (nodeId: number, newParentId?: number, newSortOrder?: number): Promise<ApiResponse<void>> => {
    return request.put(`${API_PREFIX}/nodes/${nodeId}/move`, {
      new_parent_id: newParentId,
      new_sort_order: newSortOrder
    });
  }
};

/**
 * 指令执行相关API
 */
export const instructionExecutionApi = {
  /**
   * 执行指令集
   */
  executeInstructionSet: (data: InstructionExecuteRequest): Promise<ApiResponse<InstructionExecuteResponse>> => {
    return request.post(`${API_PREFIX}/execute`, data);
  },

  /**
   * 获取指令执行历史
   */
  getInstructionExecutions: (instructionSetId: number, params?: InstructionExecutionQuery): Promise<ApiResponse<InstructionExecution[]>> => {
    return request.get(`${API_PREFIX}/${instructionSetId}/executions`, { params });
  }
};

/**
 * 为了向后兼容，在instructionSetApi中也添加executeInstructionSet方法
 */
instructionSetApi.executeInstructionSet = (instructionSetId: number, data: { content: string; mode?: string; timeout?: number }): Promise<ApiResponse<InstructionExecuteResponse>> => {
  return instructionExecutionApi.executeInstructionSet({
    instruction_set_id: instructionSetId,
    input_text: data.content,
    save_execution: true
  });
};

/**
 * 组合API - 提供更高级的操作
 */
export const instructionSetCompositeApi = {
  /**
   * 复制指令集（包含所有节点）
   */
  cloneInstructionSet: async (sourceId: number, newName: string): Promise<ApiResponse<InstructionSet>> => {
    // 获取源指令集
    const sourceSet = await instructionSetApi.getInstructionSet(sourceId);
    const sourceTree = await instructionNodeApi.getInstructionTree(sourceId);

    // 创建新指令集
    const newSet = await instructionSetApi.createInstructionSet({
      name: newName,
      description: `复制自: ${sourceSet.data.name}`,
      version: '1.0.0',
      created_by: sourceSet.data.created_by
    });

    // 递归复制节点
    const cloneNodes = async (nodes: InstructionTreeNode[], parentId?: number) => {
      for (const node of nodes) {
        const newNode = await instructionNodeApi.createInstructionNode(newSet.data.id, {
          parent_id: parentId,
          title: node.title,
          node_type: node.node_type,
          sort_order: node.sort_order,
          is_active: node.is_active
        });

        if (node.children && node.children.length > 0) {
          await cloneNodes(node.children, newNode.data.id);
        }
      }
    };

    await cloneNodes(sourceTree.data);
    return newSet;
  },

  /**
   * 批量更新节点状态
   */
  batchUpdateNodeStatus: async (nodeIds: number[], isActive: boolean): Promise<void> => {
    const promises = nodeIds.map(nodeId => 
      instructionNodeApi.updateInstructionNode(nodeId, { is_active: isActive })
    );
    await Promise.all(promises);
  },

  /**
   * 获取指令集的完整信息（包含树结构和统计）
   */
  getInstructionSetFullInfo: async (id: number) => {
    const [setInfo, tree, statistics] = await Promise.all([
      instructionSetApi.getInstructionSet(id),
      instructionNodeApi.getInstructionTree(id),
      instructionSetApi.getInstructionSetStatistics(id)
    ]);

    return {
      instructionSet: setInfo.data,
      tree: tree.data,
      statistics: statistics.data
    };
  },

  /**
   * 验证指令集完整性
   */
  validateInstructionSet: async (id: number): Promise<{ isValid: boolean; errors: string[] }> => {
    const tree = await instructionNodeApi.getInstructionTree(id);
    const errors: string[] = [];

    // 检查是否有根节点
    if (tree.data.length === 0) {
      errors.push('指令集没有根节点');
    }

    // 递归检查节点
    const validateNode = (node: InstructionTreeNode) => {
      // 检查条件节点是否有子节点
      if (node.node_type === 'CONDITION' && (!node.children || node.children.length === 0)) {
        errors.push(`条件节点 "${node.title}" 没有子节点`);
      }

      // 检查动作节点不应该有子节点
      if (node.node_type === 'ACTION' && node.children && node.children.length > 0) {
        errors.push(`动作节点 "${node.title}" 不应该有子节点`);
      }

      // 递归检查子节点
      if (node.children) {
        node.children.forEach(validateNode);
      }
    };

    tree.data.forEach(validateNode);

    return {
      isValid: errors.length === 0,
      errors
    };
  }
};

// 导出所有API
export default {
  instructionSet: instructionSetApi,
  instructionNode: instructionNodeApi,
  instructionExecution: instructionExecutionApi,
  composite: instructionSetCompositeApi
};