import asyncio
import random

from aiogram import Router, F, types
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User
from database.orm_query import orm_get_user_stat, orm_check_duel_availability, orm_get_duel, orm_get_user_status, \
    orm_update_duel_status, orm_update_level, orm_update_user_status, orm_update_duel_win, orm_check_user, orm_add_duel

chDuel_router = Router()


def kb_start():
    kb = [
        [types.KeyboardButton(text="Статистика 📊")],
        [types.KeyboardButton(text="Начать бой ⚔️")]
    ]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    return keyboard


class DuelStates(StatesGroup):
    opponent_name = State()


@chDuel_router.message(F.text == "Дуэль")
async def find_opponent_handler(message: Message, session: AsyncSession, state: FSMContext):
    user = await orm_get_user_stat(session, message.from_user.id)
    session.expunge(user)
    if user:
        # await orm_check_duel_availability(session, user.user_id, message.text)
        await get_duel(message, session)
        cancel_builder = InlineKeyboardBuilder()
        cancel_builder.row(InlineKeyboardButton(text='Отмена', callback_data='cancel_duel'))

        await state.set_state(DuelStates.opponent_name)
        await message.answer("Введите имя пользователя кому отправим вызов:", reply_markup=cancel_builder.as_markup())


@chDuel_router.message(DuelStates.opponent_name)
async def duel_state(message: Message, session: AsyncSession, state: FSMContext):
    opponent_username = message.text.strip()

    if opponent_username.startswith('@'):
        opponent_username = opponent_username[1:]  # Удаление символа @, если он есть

    user_duel = await orm_check_user(session, opponent_username)
    if user_duel is None:
        await message.answer("Такого Username не найдено!")
        await state.clear()
        return
    await orm_add_duel(session, message.from_user.id, user_duel.user_id, "pending")
    await message.answer("Вызов на дуэль отправлен!")
    await message.bot.send_message(user_duel.user_id, "Вам отправлен вызов на дуэль, перейдите в дуэли!")
    await state.clear()

@chDuel_router.callback_query(F.data == "cancel_duel")
async def cancel_duel_handler(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()  # Завершение состояния FSM
    await callback.answer(show_alert=False)
    await callback.message.answer("Вызов на дуэль отменен", reply_markup=kb_start())


@chDuel_router.callback_query(F.data.startswith("duel_cancel_"))
async def duel_cancel_handler(callback: types.CallbackQuery, session: AsyncSession):
    # await state.clear()  # Завершение состояния FSM
    id_opponent = callback.data.split('_')[-1]
    await callback.message.delete()
    await orm_update_duel_status(session, callback.from_user.id, int(id_opponent), "rejected")
    await callback.answer(show_alert=False)
    await callback.message.answer(f"Вызов на дуэль отменен")


@chDuel_router.callback_query(F.data.startswith("duel_accept_"))
async def duel_accept_handler(callback: types.CallbackQuery, session: AsyncSession, state: FSMContext):
    # await state.clear()  # Завершение состояния FSM
    id_opponent = callback.data.split('_')[-1]
    await callback.message.delete()

    user = await orm_get_user_stat(session, callback.from_user.id)
    session.expunge(user)
    opponent = await orm_get_user_stat(session, int(id_opponent))
    session.expunge(opponent)

    await orm_update_duel_status(session, callback.from_user.id, int(id_opponent), "accepted")
    await callback.answer(show_alert=False)

    await orm_update_user_status(session, user.user_id, True, False)
    await start_duel(user, opponent, callback, session)
    await orm_update_user_status(session, user.user_id, False, False)


async def get_duel(message: Message, session: AsyncSession):
    list_duel = await orm_get_duel(session, message.from_user.id)
    for info in list_duel:
        opponent = await orm_get_user_status(session, info[0].challenger_id)
        cancel_builder = InlineKeyboardBuilder()
        cancel_builder.row(InlineKeyboardButton(text='Отмена', callback_data=f'duel_cancel_{info[0].challenger_id}'),
                           InlineKeyboardButton(text='Принять', callback_data=f'duel_accept_{info[0].challenger_id}')
                           )
        await message.answer(f"Вас вызвали на дуэль!\n"
                             f"Игрок: {opponent.username}", reply_markup=cancel_builder.as_markup())


async def start_duel(user, opponent, callback: CallbackQuery, session: AsyncSession) -> None:
    health_message = await callback.message.answer(
        f"Здоровье игрока: {user.health}\nЗдоровье противника: {opponent.health}")
    await asyncio.sleep(0.8)
    user.strength, user.agility = apply_intoxication_effects(user)
    opponent.strength, opponent.agility = apply_intoxication_effects(opponent)

    status = await orm_get_user_status(session, user.user_id)
    if not status.is_searching:  # Если поиск был отменен, выходим
        return

    await orm_update_user_status(session, user.user_id, False, True)
    while user.health > 0 and opponent.health > 0:
        damage = await calculate_damage(user, opponent, callback.message)
        opponent.health -= damage

        await asyncio.sleep(0.8)
        try:
            await callback.bot.edit_message_text(
                f"Здоровье игрока: {int(user.health)}\nЗдоровье противника: {int(opponent.health)}",
                callback.from_user.id, health_message.message_id)
        except Exception as e:
            print(e)

        if opponent.health <= 0:
            await callback.message.answer(f"{user.username} победил!")
            await orm_update_duel_win(session, user.user_id, opponent.user_id, user.user_id)
            await level_up(user.user_id, session, callback.message)
            break

        damage = await calculate_damage(opponent, user, callback.message)
        user.health -= damage

        await asyncio.sleep(0.8)
        try:
            await callback.bot.edit_message_text(
                f"Здоровье игрока: {int(user.health)}\nЗдоровье противника: {int(opponent.health)}",
                callback.from_user.id, health_message.message_id)
        except Exception as e:
            print(e)

        if user.health <= 0:
            await callback.message.answer(f"{opponent.username} победил!")
            await orm_update_duel_win(session, user.user_id, opponent.user_id, opponent.user_id)
            await level_up(opponent.user_id, session, callback.message)
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
