from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.base import Recommendation, RecommendationStatus, User


async def upsert_user(session: AsyncSession, tg_user) -> User:
    user = await session.get(User, tg_user.id)
    now = datetime.now(timezone.utc)
    if user is None:
        user = User(
            id=tg_user.id,
            username=tg_user.username,
            first_name=tg_user.first_name,
            created_at=now,
            last_activity_at=now,
        )
        session.add(user)
    else:
        user.username = tg_user.username
        user.first_name = tg_user.first_name
        user.last_activity_at = now
    await session.commit()
    return user


async def create_recommendation(
    session: AsyncSession,
    *,
    user_id: int,
    title: str,
    author: str,
    reason: str,
    photo_file_id: str | None,
) -> Recommendation:
    recommendation = Recommendation(
        user_id=user_id,
        title=title,
        author=author,
        reason=reason,
        photo_file_id=photo_file_id,
    )
    session.add(recommendation)
    await session.commit()
    await session.refresh(recommendation)
    return await get_recommendation(session, recommendation.id)  # eager-load user


async def set_admin_message_id(
    session: AsyncSession,
    recommendation_id: int,
    admin_message_id: int,
) -> None:
    await session.execute(
        update(Recommendation)
        .where(Recommendation.id == recommendation_id)
        .values(admin_message_id=admin_message_id)
    )
    await session.commit()


async def get_recommendation(session: AsyncSession, recommendation_id: int) -> Recommendation | None:
    stmt = (
        select(Recommendation)
        .options(selectinload(Recommendation.user))
        .where(Recommendation.id == recommendation_id)
    )
    return await session.scalar(stmt)


async def claim_for_approval(session: AsyncSession, recommendation_id: int, reviewer_id: int) -> bool:
    result = await session.execute(
        update(Recommendation)
        .where(
            Recommendation.id == recommendation_id,
            Recommendation.status == RecommendationStatus.PENDING,
        )
        .values(
            status=RecommendationStatus.PUBLISHING,
            reviewed_by=reviewer_id,
        )
        .returning(Recommendation.id)
    )
    claimed = result.scalar_one_or_none() is not None
    if claimed:
        await session.commit()
    else:
        await session.rollback()
    return claimed


async def finalize_approval(
    session: AsyncSession,
    recommendation_id: int,
    channel_message_id: int,
) -> Recommendation | None:
    result = await session.execute(
        update(Recommendation)
        .where(
            Recommendation.id == recommendation_id,
            Recommendation.status == RecommendationStatus.PUBLISHING,
        )
        .values(
            status=RecommendationStatus.APPROVED,
            reviewed_at=func.now(),
            channel_message_id=channel_message_id,
        )
        .returning(Recommendation.id)
    )
    rec_id = result.scalar_one_or_none()
    if rec_id is None:
        await session.rollback()
        return None
    await session.commit()
    return await get_recommendation(session, recommendation_id)


async def revert_publish_claim(session: AsyncSession, recommendation_id: int) -> None:
    await session.execute(
        update(Recommendation)
        .where(
            Recommendation.id == recommendation_id,
            Recommendation.status == RecommendationStatus.PUBLISHING,
        )
        .values(status=RecommendationStatus.PENDING, reviewed_by=None)
    )
    await session.commit()


async def reject_recommendation(
    session: AsyncSession,
    recommendation_id: int,
    reviewer_id: int,
) -> Recommendation | None:
    result = await session.execute(
        update(Recommendation)
        .where(
            Recommendation.id == recommendation_id,
            Recommendation.status == RecommendationStatus.PENDING,
        )
        .values(
            status=RecommendationStatus.REJECTED,
            reviewed_by=reviewer_id,
            reviewed_at=func.now(),
        )
        .returning(Recommendation.id)
    )
    rec_id = result.scalar_one_or_none()
    if rec_id is None:
        await session.rollback()
        return None
    await session.commit()
    return await get_recommendation(session, recommendation_id)


async def pending_count(session: AsyncSession) -> int:
    value = await session.scalar(
        select(func.count(Recommendation.id)).where(Recommendation.status == RecommendationStatus.PENDING)
    )
    return int(value or 0)
