from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User, Duel


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


async def orm_check_duel_availability(session: AsyncSession, user_id: int, opponent_username: str):
    query = select(User).where(User.username == opponent_username)
    opponent = (await session.execute(query)).first()

    if not opponent:
        raise ValueError("Пользователь с таким username не найден.")

    existing_challenges = select(Duel).where(
        Duel.challenger_id == user_id,
        Duel.opponent_id == opponent.user_id,
        Duel.status == 'pending'
    )
    result_challenges = (await session.execute(existing_challenges)).first()

    existing_opponent = select(Duel).where(
        Duel.challenger_id == opponent.user_id,
        Duel.opponent_id == user_id,
        Duel.status == 'pending'
    )
    result_opponent = (await session.execute(existing_opponent)).first()

    # Если вызов уже существует, возвращаем False
    if result_challenges or result_opponent:
        return False

    # Если вызова нет, возвращаем True
    return True


async def orm_get_duel(session: AsyncSession, user_id: int):
    query = select(Duel).where(
        Duel.opponent_id == user_id,
        Duel.status == 'pending'
    )
    result = await session.execute(query)
    return result.all()


async def orm_update_duel_status(session: AsyncSession, user_id: int, opponent_id: int, status: str):
    query = update(Duel).where(Duel.opponent_id == user_id, Duel.challenger_id == opponent_id).values(
        status=status,
    )
    await session.execute(query)
    await session.commit()


async def orm_update_duel_win(session: AsyncSession, user_id: int, opponent_id: int, win_id: int):
    query = update(Duel).where(Duel.opponent_id == user_id, Duel.challenger_id == opponent_id).values(
        winner_id=win_id,
    )
    await session.execute(query)
    await session.commit()


async def orm_check_user(session: AsyncSession, username: str):
    query = select(User).where(User.username == username)
    result = await session.execute(query)
    return result.scalar()


async def orm_add_duel(session: AsyncSession, user_id: int, opponent_id: int, status: str):
    obj = Duel(
        challenger_id=user_id,
        opponent_id=opponent_id,
        status=status,
    )
    session.add(obj)
    await session.commit()


async def orm_update_fails(session: AsyncSession, user_id: int, number: int):
    query = update(User).where(User.user_id == user_id).values(
        fails=number,
    )
    await session.execute(query)
    await session.commit()