from datetime import datetime

from aiogram import Router, types, F
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardButton, FSInputFile, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.markdown import hbold
from sqlalchemy.ext.asyncio import AsyncSession

from database.orm_query import orm_add_user, orm_get_user_stat, orm_update_stat

private_router = Router()

key_back = types.ReplyKeyboardMarkup(keyboard=[[types.KeyboardButton(text="Назад")]], resize_keyboard=True)


def kb_train():
    kb = [
        [types.KeyboardButton(text="Здоровье")],
        [types.KeyboardButton(text="Сила")],
        [types.KeyboardButton(text="Ловкость")],
    ]
    key_train = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    return key_train


def kb_start():
    kb = [
        [types.KeyboardButton(text="Статистика 📊")],
        [types.KeyboardButton(text="Начать бой ⚔️")]
    ]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    return keyboard


def kb_duel():
    kb = [
        [types.KeyboardButton(text="Найти Соперника")],
        [types.KeyboardButton(text="Дуэль")],
        [types.KeyboardButton(text="Таверна (Будет позже)")],
        [types.KeyboardButton(text="Назад на главную")],
    ]
    key_duel = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    return key_duel


@private_router.message(CommandStart())
async def start_command(message: types.Message, session: AsyncSession):
    check_user = await orm_get_user_stat(session, message.from_user.id)
    if check_user is not None:
        await message.answer("Вы уже зарегистрированы!", reply_markup=kb_start())
        return
    obj = {
        'user_id': message.from_user.id,
        'username': message.from_user.username
    }
    try:
        await orm_add_user(session, obj)
        await message.answer("Вы стали новым участником!")
    except Exception as e:
        await message.answer(f'Ошибка: \n{str(e)}\nОтправь эту ошибку в поддержку, пускай работают')

    await message.answer(f'Привет, {message.from_user.full_name}!', reply_markup=kb_start())


@private_router.message((F.text.lower().contains("статистик")) | (F.text.lower().contains("характеристик")))
async def static_handler(message: types.Message, session: AsyncSession) -> None:
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(
        text="Тренироваться",
        callback_data="train")
    )

    user_stat = await orm_get_user_stat(session, message.from_user.id)

    # await message.answer(
    await message.answer_photo(FSInputFile("static/1.png"),
                               f'{hbold("Уровень:")}\t{user_stat.level}\tlvl\n'
                               f'{hbold("Опыт:")}\t{user_stat.experience}\txp\n'
                               f'{hbold("Здоровье:")}\t{user_stat.health}\thp\n'
                               f'{hbold("Сила:")}\t{user_stat.strength}\n'
                               f'{hbold("Ловкость:")}\t{user_stat.agility}\n'
                               f'{hbold("Опьянение:")}\t{user_stat.drunkenness}\t%\n', reply_markup=builder.as_markup())


@private_router.callback_query(F.data == "train")
async def train_action(callback: types.CallbackQuery, session: AsyncSession) -> None:
    check_user = await orm_get_user_stat(session, callback.from_user.id)
    if datetime.now().date() == check_user.update_stat:
        await callback.answer("Тренироваться много нельзя!", show_alert=True)
        return

    await callback.message.answer_animation(
        FSInputFile("static/pushups-intense.gif"),
        reply_markup=kb_train()
    )
    # await callback.message.answer("qwert", reply_markup=kb_train())

    cancel_builder = InlineKeyboardBuilder()
    cancel_builder.row(InlineKeyboardButton(text='Отмена', callback_data='cancel'))

    await callback.message.answer("Какой параметр будем тренировать ?", reply_markup=cancel_builder.as_markup())
    await callback.answer(show_alert=False)


@private_router.callback_query(F.data == "cancel")
async def cancel_action(callback_query: types.CallbackQuery):
    await callback_query.bot.delete_message(callback_query.from_user.id, callback_query.message.message_id - 1)
    await callback_query.message.delete()

    await callback_query.answer(show_alert=False)
    await callback_query.message.answer("Мог бы и подкачаться!", reply_markup=kb_start())


@private_router.message(F.text == "Здоровье")
@private_router.message(F.text == "Сила")
@private_router.message(F.text == "Ловкость")
async def skills_up_handler(message: Message, session: AsyncSession) -> None:
    user_stat = await orm_get_user_stat(session, message.from_user.id)

    if datetime.now().date() == user_stat.update_stat:
        await message.answer("Тренироваться много нельзя!", reply_markup=kb_start())
        return
    if user_stat:
        if message.text == "Здоровье":
            user_stat.health += 10
            await orm_update_stat(session, message.from_user.id, user_stat)
            await message.answer("Здоровье прокачено!", reply_markup=kb_start())
        elif message.text == "Сила":
            user_stat.strength += 0.5
            await orm_update_stat(session, message.from_user.id, user_stat)
            await message.answer("Сила прокачена!", reply_markup=kb_start())
        elif message.text == "Ловкость":
            user_stat.agility += 0.5
            await orm_update_stat(session, message.from_user.id, user_stat)
            await message.answer("Ловкость прокачена!", reply_markup=kb_start())
    else:
        await message.answer("Произошла ошибка, попробуйте позже", reply_markup=kb_start())


@private_router.message(F.text == "Начать бой ⚔️")
async def duel_handler(message: Message) -> None:
    await message.answer("Накажи их всех!", reply_markup=kb_duel())


@private_router.message(F.text == "Назад на главную")
async def duel_handler(message: Message) -> None:
    await message.answer("Выбери свой путь!", reply_markup=kb_start())

@private_router.message(F.text == "Таверна (Будет позже)")
async def duel_handler(message: Message) -> None:
    test_builder = InlineKeyboardBuilder()
    web_info = WebAppInfo(url='https://ru.stackoverflow.com')  # ссылка для приложения
    button1 = InlineKeyboardButton(text="Веб", web_app=web_info)
    test_builder.add(button1)
    await message.answer("Написано же будет позже, зачем нажимать!", reply_markup=test_builder.as_markup())


@private_router.message(F.animation)
async def echo_gif(message: Message):
    await message.answer(f'{message.animation.file_id}')


# @private_router.message()
# async def echo_handler(message: types.Message) -> None:
#     try:
#         await message.send_copy(chat_id=message.chat.id)
#     except TypeError:
#         await message.answer("Nice try!")
