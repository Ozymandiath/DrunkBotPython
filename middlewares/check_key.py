# middlewares/date_check.py
from typing import Any, Awaitable, Callable, Dict
from aiogram.types import TelegramObject
from datetime import datetime
from aiogram import BaseMiddleware

from sqlalchemy import select
from database.models import User


class KeyCheckMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any],
    ) -> Any:

        commands = ["Статистика 📊", "Начать бой ⚔️", "Найти Соперника", "Дуэль", "Таверна (Будет позже)", "Назад на главную",
                    "Здоровье", "Сила", "Ловкость", "Назад"]

        if event.message is not None and event.message.text in commands:
            session = data.get('session')
            query = select(User).where(User.user_id == event.message.from_user.id)
            result = await session.execute(query)
            user = result.scalar()
            last_update = user.drunk_date

            if (datetime.now().date() - last_update).days >= 1:
                user.drunkenness = 0
                user.drunk_date = datetime.now().date()
                await session.commit()
            await data.get('state').clear()
        # if event.callback_query is not None:
        #     print(event.callback_query.data)

        result = await handler(event, data)

        return result
