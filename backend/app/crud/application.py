from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, update, delete
from sqlalchemy.orm import selectinload

from app.models.application import (
    HarborConfig, AppTemplate, AppInstance, AppDeployment, AppStatus
)
from app.schemas.application import (
    HarborConfigCreate, HarborConfigUpdate,
    AppTemplateCreate, AppTemplateUpdate,
    AppInstanceCreate, AppInstanceUpdate,
    AppDeploymentCreate
)

class CRUDHarborConfig:
    async def get(self, db: AsyncSession, id: int) -> Optional[HarborConfig]:
        result = await db.execute(select(HarborConfig).where(HarborConfig.id == id))
        return result.scalar_one_or_none()

    async def get_multi(
        self, db: AsyncSession, skip: int = 0, limit: int = 100
    ) -> Tuple[List[HarborConfig], int]:
        query = select(HarborConfig).order_by(HarborConfig.created_at.desc())
        total = await db.scalar(select(func.count(HarborConfig.id)))
        
        result = await db.execute(query.offset(skip).limit(limit))
        return result.scalars().all(), total

    async def create(self, db: AsyncSession, obj_in: HarborConfigCreate, user_id: int) -> HarborConfig:
        db_obj = HarborConfig(**obj_in.model_dump(), created_by=user_id, updated_by=user_id)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self, db: AsyncSession, db_obj: HarborConfig, obj_in: HarborConfigUpdate, user_id: int
    ) -> HarborConfig:
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db_obj.updated_by = user_id
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def delete(self, db: AsyncSession, id: int) -> bool:
        db_obj = await self.get(db, id)
        if db_obj:
            await db.delete(db_obj)
            await db.commit()
            return True
        return False

class CRUDAppTemplate:
    async def get(self, db: AsyncSession, id: int) -> Optional[AppTemplate]:
        result = await db.execute(select(AppTemplate).where(AppTemplate.id == id))
        return result.scalar_one_or_none()

    async def get_multi(
        self, db: AsyncSession, skip: int = 0, limit: int = 100
    ) -> Tuple[List[AppTemplate], int]:
        query = select(AppTemplate).order_by(AppTemplate.created_at.desc())
        total = await db.scalar(select(func.count(AppTemplate.id)))
        
        result = await db.execute(query.offset(skip).limit(limit))
        return result.scalars().all(), total

    async def create(self, db: AsyncSession, obj_in: AppTemplateCreate, user_id: int) -> AppTemplate:
        db_obj = AppTemplate(**obj_in.model_dump(), created_by=user_id, updated_by=user_id)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self, db: AsyncSession, db_obj: AppTemplate, obj_in: AppTemplateUpdate, user_id: int
    ) -> AppTemplate:
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db_obj.updated_by = user_id
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def delete(self, db: AsyncSession, id: int) -> bool:
        db_obj = await self.get(db, id)
        if db_obj:
            await db.delete(db_obj)
            await db.commit()
            return True
        return False

class CRUDAppInstance:
    async def get(self, db: AsyncSession, id: int) -> Optional[AppInstance]:
        query = select(AppInstance).options(
            selectinload(AppInstance.deployments).selectinload(AppDeployment.server),
            selectinload(AppInstance.template)
        ).where(AppInstance.id == id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_multi(
        self, db: AsyncSession, skip: int = 0, limit: int = 100
    ) -> Tuple[List[AppInstance], int]:
        query = select(AppInstance).options(
            selectinload(AppInstance.template),
            selectinload(AppInstance.deployments).selectinload(AppDeployment.server)
        ).order_by(AppInstance.created_at.desc())
        
        total = await db.scalar(select(func.count(AppInstance.id)))
        
        result = await db.execute(query.offset(skip).limit(limit))
        return result.scalars().all(), total

    async def create(
        self, db: AsyncSession, obj_in: AppInstanceCreate, user_id: int
    ) -> AppInstance:
        # 1. Create Instance
        instance_data = obj_in.model_dump(exclude={"deployments"})
        db_instance = AppInstance(
            **instance_data,
            status=AppStatus.installing,
            created_by=user_id,
            updated_by=user_id
        )
        db.add(db_instance)
        await db.flush() # Get ID

        # 2. Create Deployments
        for deploy_in in obj_in.deployments:
            db_deploy = AppDeployment(
                instance_id=db_instance.id,
                **deploy_in.model_dump()
            )
            db.add(db_deploy)
        
        await db.commit()
        await db.refresh(db_instance)
        
        # Load relationships
        query = select(AppInstance).options(
            selectinload(AppInstance.deployments).selectinload(AppDeployment.server),
            selectinload(AppInstance.template)
        ).where(AppInstance.id == db_instance.id)
        result = await db.execute(query)
        return result.scalar_one()

    async def update(
        self, db: AsyncSession, db_obj: AppInstance, obj_in: AppInstanceUpdate, user_id: int
    ) -> AppInstance:
        update_data = obj_in.model_dump(exclude_unset=True)
        
        # Handle deployments update
        if "deployments" in update_data:
            deployments_in = update_data.pop("deployments")
            
            # Current deployments map: {(server_id, role): deployment_obj}
            existing_map = {(d.server_id, d.role): d for d in db_obj.deployments}
            incoming_keys = set()
            
            for deploy_data in deployments_in:
                key = (deploy_data["server_id"], deploy_data.get("role", "default"))
                incoming_keys.add(key)
                
                if key in existing_map:
                    # Update existing
                    existing_obj = existing_map[key]
                    for k, v in deploy_data.items():
                        setattr(existing_obj, k, v)
                else:
                    # Add new
                    new_deploy = AppDeployment(
                        instance_id=db_obj.id,
                        **deploy_data
                    )
                    db.add(new_deploy)
            
            # Delete removed
            for key, obj in existing_map.items():
                if key not in incoming_keys:
                    await db.delete(obj)
        
        for field, value in update_data.items():
            setattr(db_obj, field, value)
            
        db_obj.updated_by = user_id
        await db.commit()
        
        # Reload with relationships
        query = select(AppInstance).options(
            selectinload(AppInstance.deployments).selectinload(AppDeployment.server),
            selectinload(AppInstance.template)
        ).where(AppInstance.id == db_obj.id)
        result = await db.execute(query)
        return result.scalar_one()
    
    async def delete(self, db: AsyncSession, id: int) -> bool:
        db_obj = await self.get(db, id)
        if db_obj:
            await db.delete(db_obj)
            await db.commit()
            return True
        return False

# Instantiate
harbor_config = CRUDHarborConfig()
app_template = CRUDAppTemplate()
app_instance = CRUDAppInstance()
