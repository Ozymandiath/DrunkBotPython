from aiogram import Router, types, F
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.markdown import hbold

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
        [types.KeyboardButton(text="Статистика")],
        [types.KeyboardButton(text="Поединок")]
    ]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    return keyboard

def kb_duel():
    kb = [
        [types.KeyboardButton(text="Найти Соперника")],
        [types.KeyboardButton(text="Вызвать на Дуэль")],
        [types.KeyboardButton(text="Таверна")],
    ]
    key_duel = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    return key_duel

@private_router.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await message.answer(f"Hello, {hbold(message.from_user.full_name)}!", reply_markup=kb_start())


@private_router.message((F.text.lower().contains("статистик")) | (F.text.lower().contains("характеристик")))
async def static_handler(message: types.Message) -> None:
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(
        text="Тренироваться",
        callback_data="train")
    )

    await message.answer(f"{hbold("Уровень:")}\t0\tlvl\n"
                         f"{hbold("Опыт:")}\t0\txp\n"
                         f"{hbold("Здоровье:")}\t0\thp\n"
                         f"{hbold("Сила:")}\t0\n"
                         f"{hbold("Ловкость:")}\t0\n"
                         f"{hbold("Опьянение:")}\t0\t%\n", reply_markup=builder.as_markup())


@private_router.callback_query(F.data == "train")
async def train_action(callback: types.CallbackQuery):
    await callback.message.answer_animation(
        "CgACAgQAAxkBAANsZhQYQ06lFdzzuYgTPEkrKmWTrU4AAuUCAAJCJxVTCtjm5Yaz5A80BA",
        reply_markup=kb_train()
    )  # Скала-ГИФ

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
async def skills_up_handler(message: Message) -> None:
    if False:
        await message.answer("Прокачка недоступна", reply_markup=kb_start())
    if message.text == "Здоровье":
        # Отправка в базу
        await message.answer("Здоровье прокачено!", reply_markup=kb_start())
    if message.text == "Сила":
        # Отправка в базу
        await message.answer("Сила прокачена!", reply_markup=kb_start())
    if message.text == "Ловкость":
        # Отправка в базу
        await message.answer("Ловкость прокачена!", reply_markup=kb_start())


@private_router.message(F.text == "Поединок")
async def duel_handler(message: Message) -> None:
    await message.answer("Накажи их всех!", reply_markup=kb_duel())

@private_router.message(F.animation)
async def echo_gif(message: Message):
    await message.answer(f"{message.animation.file_id}")


@private_router.message()
async def echo_handler(message: types.Message) -> None:
    try:
        await message.send_copy(chat_id=message.chat.id)
    except TypeError:
        await message.answer("Nice try!")
