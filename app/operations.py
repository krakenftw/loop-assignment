from sqlalchemy.ext.asyncio import AsyncSession
from . import models

async def create_report(db: AsyncSession):
    report = models.Report()
    db.add(report)
    await db.commit()
    await db.refresh(report)
    return report

async def get_report(db: AsyncSession, report_id: str):
    return await db.get(models.Report, report_id)
