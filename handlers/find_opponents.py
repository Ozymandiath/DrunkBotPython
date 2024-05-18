import asyncio
import random

from aiogram import Router, F, types
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User
from database.orm_query import orm_get_user_stat, orm_get_opponent, orm_update_level, orm_update_user_status, \
    orm_get_user_status, orm_update_fails

fDuel_router = Router()


def kb_start():
    kb = [
        [types.KeyboardButton(text="Статистика")],
        [types.KeyboardButton(text="Начать бой")]
    ]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    return keyboard


@fDuel_router.message(F.text == "Найти Соперника")
async def find_opponent_handler(message: Message, session: AsyncSession):
    user = await orm_get_user_stat(session, message.from_user.id)
    session.expunge(user)
    if user:
        if user.is_searching or user.is_in_duel:
            # Если пользователь уже ищет соперника или находится в битве, сообщаем об этом
            await message.bot.delete_message(message.from_user.id, message.message_id)
            await asyncio.sleep(0.5)
            msg_del = await message.answer(
                "Поиск соперника уже начат или битва в процессе.\nДождитесь завершения.")
            await asyncio.sleep(2)
            await msg_del.delete()
            return

        await orm_update_user_status(session, user.user_id, True, False)
        cancel_builder = InlineKeyboardBuilder()
        cancel_builder.row(InlineKeyboardButton(text='Отмена', callback_data='cancel_search'))

        msg_serch = await message.answer("Поиск соперника!\nОжидание 0 сек.",
                                         reply_markup=cancel_builder.as_markup())

        for i in range(5):
            try:
                await message.bot.edit_message_text(
                    f"Поиск соперника!\nОжидание {i + 1} сек.",
                    message.from_user.id, msg_serch.message_id,
                    reply_markup=cancel_builder.as_markup()
                )
                await asyncio.sleep(1)
            except Exception as e:
                ...

        # Поиск соперника
        opponent = await find_suitable_opponent(user, session)
        if opponent is None:
            opponent = False
        else:
            opponent = opponent[0]
        status = await orm_get_user_status(session, user.user_id)
        if opponent and status.is_searching and user.fails < 3:
            session.expunge(opponent)
            # Начать бой
            await start_duel(user, opponent, message, session)
        elif status.is_searching:
            # Создать вымышленного противника
            opponent = create_virtual_opponent(user)
            await start_duel(user, opponent, message, session)

        await orm_update_user_status(session, user.user_id, False, False)
    else:
        await message.answer("Произошла ошибка, попробуйте позже", reply_markup=kb_start())


@fDuel_router.callback_query(F.data == 'cancel_search')
async def cancel_search_handler(callback: CallbackQuery, session: AsyncSession):
    status = await orm_get_user_status(session, callback.from_user.id)
    if status.is_searching and not status.is_in_duel:
        await orm_update_user_status(session, callback.from_user.id, False, False)
        await callback.bot.delete_message(callback.from_user.id, callback.message.message_id)
        await callback.message.answer("Поиск соперника отменен.", reply_markup=kb_start())
        await callback.answer(show_alert=False)
    else:
        await callback.answer(
            "Поиск уже не отменить.", show_alert=True)


async def find_suitable_opponent(user, session: AsyncSession):
    # Поиск соперника по уровню
    level_range = 2  # Диапазон уровней для поиска соперника
    opponents = await orm_get_opponent(session, user, level_range)
    if len(opponents) > 0:
        # Выбрать случайного соперника из списка
        return random.choice(opponents)
    else:
        return None


def create_virtual_opponent(user) -> User:
    # Создание вымышленного противника с примерно равными характеристиками
    opponent_health = random.randint(int(user.health - (user.health / 100 * 20)),
                                     int(user.health + (user.health / 100 * 20)))

    opponent_strength = random.randint(max(user.strength - 2, 1), user.strength + 2)
    opponent_agility = random.randint(max(user.agility - 2, 1), user.agility + 2)

    return User(
        user_id=-1,
        username="Враг из космоса",
        level=user.level,
        health=opponent_health,
        strength=opponent_strength,
        agility=opponent_agility,
        drunkenness=user.drunkenness
    )


async def start_duel(user, opponent, message: Message, session: AsyncSession) -> None:
    health_message = await message.answer(f"Здоровье игрока: {user.health}\nЗдоровье противника: {opponent.health}")
    await asyncio.sleep(0.8)
    user.strength, user.agility = apply_intoxication_effects(user)
    opponent.strength, opponent.agility = apply_intoxication_effects(opponent)

    status = await orm_get_user_status(session, user.user_id)
    if not status.is_searching:  # Если поиск был отменен, выходим
        return

    await orm_update_user_status(session, user.user_id, False, True)
    while user.health > 0 and opponent.health > 0:
        damage = await calculate_damage(user, opponent, message)
        opponent.health -= damage

        await asyncio.sleep(0.8)
        try:
            await message.bot.edit_message_text(
                f"Здоровье игрока: {int(user.health)}\nЗдоровье противника: {int(opponent.health)}",
                message.from_user.id, health_message.message_id)
        except Exception as e:
            ...

        if opponent.health <= 0:
            await message.answer(f"{user.username} победил!")
            await orm_update_fails(session, user.user_id, 0)
            await level_up(user.user_id, session, message)
            break

        damage = await calculate_damage(opponent, user, message)
        user.health -= damage

        await asyncio.sleep(0.8)
        try:
            await message.bot.edit_message_text(
                f"Здоровье игрока: {int(user.health)}\nЗдоровье противника: {int(opponent.health)}",
                message.from_user.id, health_message.message_id)
        except Exception as e:
            ...

        if user.health <= 0:
            await message.answer(f"{opponent.username} победил!")
            await orm_update_fails(session, user.user_id, user.fails + 1)
            break


async def level_up(user_id, session, message):
    # await session.rollback()
    user = await orm_get_user_stat(session, user_id)
    if user.drunkenness < 40:
        user.drunkenness += 5
    user.experience += 50
    while user.experience >= 100 * (user.level ** 1.5):
        user.level += 1
        user.health += 20
        user.strength += 2
        user.agility += 2
        user.experience -= int(100 * ((user.level - 1) ** 1.5))

    # user_dict = {
    #     'id': user.id,
    #     'user_id': user.user_id,
    #     'username': user.username,
    #     'level': user.level,
    #     'experience': user.experience,
    #     'health': user.health,
    #     'strength': user.strength,
    #     'agility': user.agility,
    #     'drunkenness': user.drunkenness,
    #     'is_searching': user.is_searching,
    #     'created': user.created.isoformat() if user.created else None,
    #     'updated': user.updated.isoformat() if user.updated else None,
    # }

    # await message.answer(f"{user_dict} тест!")
    await orm_update_level(session, user)


def apply_intoxication_effects(self):
    # Увеличение силы и уменьшение ловкости от опьянения
    effective_strength = self.strength * (1 + min(self.drunkenness * 0.005, 0.25))
    effective_agility = self.agility * (1 - min(self.drunkenness * 0.003, 0.15))

    return effective_strength, effective_agility


async def calculate_damage(attacker, defender, message):
    # Проверка уклонения
    if random.random() < calculate_dodge_reduction(defender.agility):
        await asyncio.sleep(1)
        await message.answer(f"{defender.username} избежал атаки!")
        return 0  # Урон не наносится

    base_damage = attacker.strength
    if random.random() < 0.1:  # 10% шанс на спецудар
        base_damage *= 2
        await asyncio.sleep(1)
        await message.answer(f"{attacker.username} наносит спецудар с уроном {base_damage:.2f}!")
    return base_damage


def calculate_dodge_reduction(agility):
    reduction = 0
    if agility > 200:
        reduction += (agility - 200) * 0.01
        agility = 200
    if agility > 100:
        reduction += (agility - 100) * 0.02
        agility = 100
    if agility > 20:
        reduction += (agility - 20) * 0.025
        agility = 20
    reduction += agility * 0.1
    return reduction / 100
