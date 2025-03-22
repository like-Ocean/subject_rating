from sqlalchemy.ext.asyncio import AsyncSession
from database import AsyncSessionLocal
from service import init_db_data_service


async def init_db():
    async with AsyncSessionLocal() as session:
        await init_db_data_service.init_roles(session)
        await init_db_data_service.init_super_admin(session)
