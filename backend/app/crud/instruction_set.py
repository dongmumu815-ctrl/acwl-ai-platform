from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, or_, select, func
from app.models.instruction_set import InstructionSet, InstructionNode, InstructionExecution
from app.schemas.instruction_set import (
    InstructionSetCreate, InstructionSetUpdate,
    InstructionNodeCreate, InstructionNodeUpdate,
    InstructionExecutionCreate
)


class CRUDInstructionSet:
    """指令集CRUD操作类"""

    async def get(self, db: AsyncSession, id: int) -> Optional[InstructionSet]:
        """根据ID获取指令集"""
        result = await db.execute(
            select(InstructionSet).where(InstructionSet.id == id)
        )
        return result.scalar_one_or_none()

    async def get_multi(
        self, 
        db: AsyncSession, 
        *, 
        skip: int = 0, 
        limit: int = 100,
        status: Optional[str] = None,
        created_by: Optional[int] = None
    ) -> List[InstructionSet]:
        """获取指令集列表"""
        query = select(InstructionSet)
        
        if status:
            query = query.where(InstructionSet.status == status)
        if created_by:
            query = query.where(InstructionSet.created_by == created_by)
            
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    async def get_count(
        self,
        db: AsyncSession,
        *,
        status: Optional[str] = None,
        created_by: Optional[int] = None
    ) -> int:
        """获取指令集总数"""
        query = select(func.count(InstructionSet.id))
        
        if status:
            query = query.where(InstructionSet.status == status)
        if created_by:
            query = query.where(InstructionSet.created_by == created_by)
            
        result = await db.execute(query)
        return result.scalar() or 0

    async def create(self, db: AsyncSession, *, obj_in: InstructionSetCreate) -> InstructionSet:
        """创建指令集"""
        db_obj = InstructionSet(**obj_in.model_dump())
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self, 
        db: AsyncSession, 
        *, 
        db_obj: InstructionSet, 
        obj_in: InstructionSetUpdate
    ) -> InstructionSet:
        """更新指令集"""
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def remove(self, db: AsyncSession, *, id: int) -> InstructionSet:
        """删除指令集"""
        result = await db.execute(
            select(InstructionSet).where(InstructionSet.id == id)
        )
        obj = result.scalar_one_or_none()
        if obj:
            await db.delete(obj)
            await db.commit()
        return obj

    async def get_with_nodes(self, db: AsyncSession, id: int) -> Optional[InstructionSet]:
        """获取指令集及其所有节点"""
        result = await db.execute(
            select(InstructionSet).where(InstructionSet.id == id)
        )
        return result.scalar_one_or_none()

    async def get_root_nodes(self, db: AsyncSession, instruction_set_id: int) -> List[InstructionNode]:
        """获取指令集的根节点"""
        result = await db.execute(
            select(InstructionNode).where(
                and_(
                    InstructionNode.instruction_set_id == instruction_set_id,
                    InstructionNode.parent_id.is_(None)
                )
            ).order_by(InstructionNode.sort_order)
        )
        return result.scalars().all()


class CRUDInstructionNode:
    """指令节点CRUD操作类"""

    async def get(self, db: AsyncSession, id: int) -> Optional[InstructionNode]:
        """根据ID获取指令节点"""
        result = await db.execute(
            select(InstructionNode).where(InstructionNode.id == id)
        )
        return result.scalar_one_or_none()

    async def get_multi(
        self, 
        db: AsyncSession, 
        *, 
        instruction_set_id: int,
        parent_id: Optional[int] = None,
        skip: int = 0, 
        limit: int = 100
    ) -> List[InstructionNode]:
        """获取指令节点列表"""
        query = select(InstructionNode).where(
            InstructionNode.instruction_set_id == instruction_set_id
        )
        
        if parent_id is not None:
            query = query.where(InstructionNode.parent_id == parent_id)
        else:
            query = query.where(InstructionNode.parent_id.is_(None))
            
        query = query.order_by(InstructionNode.sort_order).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    async def create(self, db: AsyncSession, *, obj_in: InstructionNodeCreate) -> InstructionNode:
        """创建指令节点"""
        db_obj = InstructionNode(**obj_in.model_dump())
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self, 
        db: AsyncSession, 
        *, 
        db_obj: InstructionNode, 
        obj_in: InstructionNodeUpdate
    ) -> InstructionNode:
        """更新指令节点"""
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def remove(self, db: AsyncSession, *, id: int) -> InstructionNode:
        """删除指令节点"""
        result = await db.execute(
            select(InstructionNode).where(InstructionNode.id == id)
        )
        obj = result.scalar_one_or_none()
        if obj:
            await db.delete(obj)
            await db.commit()
        return obj

    async def get_children(self, db: AsyncSession, parent_id: int) -> List[InstructionNode]:
        """获取子节点"""
        result = await db.execute(
            select(InstructionNode).where(
                InstructionNode.parent_id == parent_id
            ).order_by(InstructionNode.sort_order)
        )
        return result.scalars().all()

    async def get_tree(self, db: AsyncSession, instruction_set_id: int) -> List[InstructionNode]:
        """获取完整的节点树"""
        # 获取所有节点
        result = await db.execute(
            select(InstructionNode).where(
                InstructionNode.instruction_set_id == instruction_set_id
            ).order_by(InstructionNode.sort_order)
        )
        all_nodes = result.scalars().all()
        
        # 构建节点映射
        node_map = {node.id: node for node in all_nodes}
        root_nodes = []
        
        # 构建树结构
        for node in all_nodes:
            if node.parent_id is None:
                root_nodes.append(node)
            else:
                parent = node_map.get(node.parent_id)
                if parent:
                    if not hasattr(parent, 'children'):
                        parent.children = []
                    parent.children.append(node)
        
        return root_nodes

    async def get_parents(self, db: AsyncSession, node_id: int) -> List[InstructionNode]:
        """
        获取节点的所有父节点
        
        Args:
            db: 数据库会话
            node_id: 节点ID
            
        Returns:
            父节点列表
        """
        # 首先获取当前节点
        current_node = await self.get(db, node_id)
        if not current_node or current_node.parent_id is None:
            return []
        
        parents = []
        parent_id = current_node.parent_id
        
        # 递归获取所有父节点
        while parent_id is not None:
            parent_node = await self.get(db, parent_id)
            if parent_node:
                parents.append(parent_node)
                parent_id = parent_node.parent_id
            else:
                break
        
        return parents

    async def move_node(
        self, 
        db: AsyncSession, 
        *, 
        node_id: int, 
        new_parent_id: Optional[int], 
        new_sort_order: int
    ) -> InstructionNode:
        """移动节点到新位置"""
        node = await self.get(db, node_id)
        if node:
            node.parent_id = new_parent_id
            node.sort_order = new_sort_order
            db.add(node)
            await db.commit()
            await db.refresh(node)
        return node


class CRUDInstructionExecution:
    """指令执行CRUD操作类"""

    async def get(self, db: AsyncSession, id: int) -> Optional[InstructionExecution]:
        """根据ID获取执行记录"""
        result = await db.execute(
            select(InstructionExecution).where(InstructionExecution.id == id)
        )
        return result.scalar_one_or_none()

    async def get_multi(
        self, 
        db: AsyncSession, 
        *, 
        instruction_set_id: Optional[int] = None,
        skip: int = 0, 
        limit: int = 100
    ) -> List[InstructionExecution]:
        """获取执行记录列表"""
        query = select(InstructionExecution)
        
        if instruction_set_id:
            query = query.where(InstructionExecution.instruction_set_id == instruction_set_id)
            
        query = query.order_by(InstructionExecution.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    async def create(self, db: AsyncSession, *, obj_in: InstructionExecutionCreate) -> InstructionExecution:
        """创建执行记录"""
        db_obj = InstructionExecution(**obj_in.model_dump())
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_statistics(
        self, 
        db: AsyncSession, 
        instruction_set_id: int
    ) -> Dict[str, Any]:
        """获取执行统计信息"""
        
        # 总执行次数
        total_result = await db.execute(
            select(func.count(InstructionExecution.id)).where(
                InstructionExecution.instruction_set_id == instruction_set_id
            )
        )
        total_executions = total_result.scalar()
        
        # 成功执行次数
        success_result = await db.execute(
            select(func.count(InstructionExecution.id)).where(
                and_(
                    InstructionExecution.instruction_set_id == instruction_set_id,
                    InstructionExecution.status == 'SUCCESS'
                )
            )
        )
        success_executions = success_result.scalar()
        
        # 平均执行时间
        avg_time_result = await db.execute(
            select(func.avg(InstructionExecution.execution_time_ms)).where(
                InstructionExecution.instruction_set_id == instruction_set_id
            )
        )
        avg_execution_time = avg_time_result.scalar()
        
        # 平均置信度
        avg_conf_result = await db.execute(
            select(func.avg(InstructionExecution.confidence_score)).where(
                InstructionExecution.instruction_set_id == instruction_set_id
            )
        )
        avg_confidence = avg_conf_result.scalar()
        
        return {
            "total_executions": total_executions or 0,
            "success_executions": success_executions or 0,
            "success_rate": (success_executions / total_executions * 100) if total_executions > 0 else 0,
            "avg_execution_time_ms": float(avg_execution_time) if avg_execution_time else 0,
            "avg_confidence_score": float(avg_confidence) if avg_confidence else 0
        }


# 创建CRUD实例
instruction_set = CRUDInstructionSet()
instruction_node = CRUDInstructionNode()
instruction_execution = CRUDInstructionExecution()