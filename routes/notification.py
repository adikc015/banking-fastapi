from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.notification import Notification
from models.user import User
from schemas.notification import NotificationOut
from utils.security import get_current_user

router = APIRouter()


@router.get("/", response_model=list[NotificationOut])
async def my_notifications(
	db: AsyncSession = Depends(get_db),
	current_user: User = Depends(get_current_user),
) -> list[Notification]:
	rows = await db.execute(
		select(Notification).where(Notification.user_id == current_user.id).order_by(Notification.id.desc())
	)
	return list(rows.scalars().all())


@router.post("/{notification_id}/read", response_model=NotificationOut)
async def mark_notification_read(
	notification_id: int,
	db: AsyncSession = Depends(get_db),
	current_user: User = Depends(get_current_user),
) -> Notification:
	notification = await db.get(Notification, notification_id)
	if notification is None or notification.user_id != current_user.id:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")

	notification.is_read = True
	await db.commit()
	await db.refresh(notification)
	return notification
