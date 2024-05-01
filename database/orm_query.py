from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User


async def orm_add_user(session: AsyncSession, data: dict):
    obj = User(
        user_id=data["user_id"],
        username=data["username"],
        # level=data["level"],
        # experience=data["experience"],
        # health=data["health"],
        # strength=data["strength"],
        # agility=data["agility"],
        # drunkenness=float(data["drunkenness"]),
        # is_searching=bool(data["is_searching"]),
    )
    session.add(obj)
    await session.commit()


async def orm_get_user_stat(session: AsyncSession, user_id: int):
    query = select(User).where(User.user_id == user_id)
    result = await session.execute(query)
    return result.scalar()


async def orm_update_stat(session: AsyncSession, user_id: int, data):
    query = update(User).where(User.user_id == user_id).values(
        health=data.health,
        strength=data.strength,
        agility=data.agility,
        update_stat=func.current_date()
    )
    await session.execute(query)
    await session.commit()


async def orm_get_opponent(session: AsyncSession, user, diff: int):
    query = (select(User)
             .where(User.level >= user.level - diff)
             .where(User.level <= user.level + diff)
             # .where(User.is_searching == True)
             .where(User.user_id != user.user_id))

    result = await session.execute(query)
    return result.all()


async def orm_update_level(session: AsyncSession, user_data):
    query = update(User).where(User.user_id == user_data.user_id).values(
        level=user_data.level,
        experience=user_data.experience,
        health=user_data.health,
        strength=user_data.strength,
        agility=user_data.agility,
        drunkenness=float(user_data.drunkenness)
    )
    await session.execute(query)
    await session.commit()


async def orm_get_user_status(session: AsyncSession, user_id: int):
    query = select(User).where(User.user_id == user_id)
    result = await session.execute(query)
    return result.scalar()


async def orm_update_user_status(session: AsyncSession, user_id: int, is_searching: bool, is_in_duel: bool):
    query = update(User).where(User.user_id == user_id).values(
        is_searching=is_searching,
        is_in_duel=is_in_duel
    )
    await session.execute(query)
    await session.commit()
