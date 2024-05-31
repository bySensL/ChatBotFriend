import asyncio
import json

from ai import gen_text, getOtherNames, isName

import datetime

import g4f.models
from aiogram import Bot, Dispatcher, F
from aiogram.enums import ChatAction
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters import Command, state
from aiogram.types import Message, URLInputFile, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, \
    KeyboardButton, ReplyKeyboardRemove, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from owm import OWMClient


class botChats(StatesGroup):
    rename = State()
    name = State()
    bot_name = State()
    chatting = State()
    input_country = State()
    input_city = State()
    choose_city = State()


with open('config.json') as config_file:
    cfg = json.load(config_file)

bot = Bot(cfg['token'])
dp = Dispatcher()

owm_client = OWMClient(cfg['owm'])

@dp.message(botChats.rename)
async def name(msg: Message, state: FSMContext):
    print(9)
    if await isName(msg.text):
        await state.update_data(name=msg.text)
        await state.update_data(list_names=await getOtherNames(msg.text))
        data = await state.get_data()
        await msg.answer(f'Отлично! Ваше имя {msg.text}. Настройки изменены.')
        # await bot.send_message(msg.chat.id, f"Отлично! В данный момент вашего друга зовут {data.get('bot_name')}. Можете начинать общаться.\n\nЕсли захотите изменить настройки, то пропишите комманду /menu")
        await state.set_state(botChats.chatting)
        # await state.set_state(botChats.chatting)
    else:
        await bot.send_message(msg.chat.id, "Извините, имя введено неверно. Попробуйте ввести другую форму имени.")
        await state.set_state(botChats.rename)
@dp.message(botChats.input_country)
async def input_country(msg: Message, state: FSMContext):
    if len(msg.text) != 2:
        await msg.answer("Код страны должен содержать два символа")
        return None

    await state.update_data(country=msg.text)
    await state.set_state(botChats.input_city)
    await msg.answer("Код записан. Введите ваш город")
@dp.message(botChats.input_city)
async def input_city(msg: Message, state: FSMContext):
    await state.update_data(city=msg.text)
    await state.set_state(botChats.choose_city)
    await msg.answer("Запрашиваю список городов по вашему запросу, выберите свой город")

    state_data = await state.get_data()
    resp = await owm_client.geocode_cities(state_data["city"], state_data["country"])
    await state.update_data(available_cities=resp)  # сохраняем доступные города в состояние

    reply_text = ""
    kb = ReplyKeyboardBuilder()
    for i in range(len(resp)):
        kb.add(KeyboardButton(text=str(i)))
        reply_text += str(i) + ". " + resp[i]["name"] + "\n"

    kb.adjust(1)
    await state.set_state(botChats.choose_city)
    await msg.answer(reply_text, reply_markup=kb.as_markup(resize_keyboard=True))
@dp.message(botChats.choose_city)
async def choose_city(msg: Message, state: FSMContext):
    state_data = await state.get_data()
    if not msg.text.isdigit():
        await msg.answer("Вы должны выбрать номер вашего города")
        return

    # берем ответы API, которые получили на предыдущем шаге
    cities = state_data["available_cities"]

    # берем город, который выбрали
    city_num = int(msg.text)
    user_city = cities[city_num]

    await state.update_data(user_city=user_city)
    await state.set_state(botChats.chatting)
    await msg.answer("Отлично! Все необходимые данные записаны, если хотите что-либо изменить, то пропишите команду /menu", reply_markup=ReplyKeyboardRemove())

@dp.message(botChats.name)
async def name(msg: Message, state: FSMContext):
    print(9)
    if await isName(msg.text):
        await state.update_data(name=msg.text)
        await state.update_data(list_names=await getOtherNames(msg.text))
        data = await state.get_data()
        await msg.answer(f'Отлично! Ваше имя {msg.text}. Введите код страны (например RU)')
        # await bot.send_message(msg.chat.id, f"Отлично! В данный момент вашего друга зовут {data.get('bot_name')}. Можете начинать общаться.\n\nЕсли захотите изменить настройки, то пропишите комманду /menu")
        await state.set_state(botChats.input_country)
        # await state.set_state(botChats.chatting)
    else:
        await bot.send_message(msg.chat.id, "Извините, имя введено неверно. Попробуйте ввести другую форму имени.")
        await state.set_state(botChats.name)
@dp.message(botChats.bot_name)
async def bot_name(msg: Message, state: FSMContext):
    if await isName(msg.text):
        await state.update_data(bot_name=msg.text)
        data = await state.get_data()
        await bot.send_message(msg.chat.id, f"Отлично! В данный момент вашего друга зовут {data.get('bot_name')}. Можете начинать общаться.\n\nЕсли захотите изменить настройки, то пропишите комманду /menu")
        await state.set_state(botChats.chatting)
    else:
        await bot.send_message(msg.chat.id, "Извините, имя введено неверно. Попробуйте ввести другую форму имени.")
        await state.set_state(botChats.bot_name)

@dp.message(Command('start'))
async def start(msg: Message, state: FSMContext):
    await msg.answer("Пожалуйста введите своё имя")
    await state.update_data(bot_name="Тима")
    await state.set_state(botChats.name)
@dp.message(Command('menu'))
async def menu(msg: Message, state: FSMContext):
    await state.set_state(botChats.chatting)
    kb = InlineKeyboardBuilder()
    kb.add(InlineKeyboardButton(text="Изменить ваше имя", callback_data="change_name"))
    kb.add(InlineKeyboardButton(text="Изменить имя друга", callback_data="change_bot_name"))
    kb.add(InlineKeyboardButton(text="Изменить страну и город", callback_data="change_geo"))
    kb.add(InlineKeyboardButton(text="Очистить диалог", callback_data="clear_dialog"))
    kb.adjust(2, 1, 1)
    keyboard = kb.as_markup(resize_keyboard=True)
    data = await state.get_data()

    await bot.send_message(msg.chat.id, f'''Меню настроек.
    
    Ваше имя: {data.get('name')}
    Имя вашего друга: {data.get('bot_name')}
    Ваше местоположение: {data.get('user_city')['country']}, {data.get('user_city')['name']}''', reply_markup=keyboard)

@dp.callback_query(F.data == "back_to_menu")
async def menu(callback: CallbackQuery, state: FSMContext):
    await state.set_state(botChats.chatting)
    kb = InlineKeyboardBuilder()
    kb.add(InlineKeyboardButton(text="Изменить ваше имя", callback_data="change_name"))
    kb.add(InlineKeyboardButton(text="Изменить имя друга", callback_data="change_bot_name"))
    kb.add(InlineKeyboardButton(text="Изменить страну и город", callback_data="change_geo"))
    kb.add(InlineKeyboardButton(text="Очистить диалог", callback_data="clear_dialog"))
    kb.adjust(2, 1, 1)
    keyboard = kb.as_markup(resize_keyboard=True)
    data = await state.get_data()

    await bot.send_message(callback.chat.id, f'''Меню настроек.
    
    Ваше имя: {data.get('name')}
    Имя вашего друга: {data.get('bot_name')}
    Ваше местоположение: {await data.get('country')}, {await data.get('user_city')}''', reply_markup=keyboard)
@dp.callback_query(F.data == "change_geo")
async def change_name(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    kb = InlineKeyboardBuilder()
    kb.add(InlineKeyboardButton(text="Назад", callback_data="back_to_menu"))
    keyboard = kb.as_markup(resize_keyboard=True)
    await bot.send_message(callback.from_user.id, "Введите код страны (например RU)", reply_markup=keyboard)
    await state.set_state(botChats.input_country)
@dp.callback_query(F.data == "change_name")
async def change_name(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    kb = InlineKeyboardBuilder()
    kb.add(InlineKeyboardButton(text="Назад", callback_data="back_to_menu"))
    keyboard = kb.as_markup(resize_keyboard=True)
    await bot.send_message(callback.from_user.id, "Введите новое имя", reply_markup=keyboard)
    await state.set_state(botChats.rename)
@dp.callback_query(F.data == "change_bot_name")
async def change_name(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await bot.send_message(callback.from_user.id, "Введите новое имя")
    await state.set_state(botChats.bot_name)
@dp.callback_query(F.data == "clear_dialog")
async def clear_dialog(callback: CallbackQuery, state: FSMContext):
    await state.update_data(dialogue=None)
    await bot.send_message(callback.from_user.id, "Диалог очищен")

@dp.message(F.text, botChats.chatting)
async def advice(msg: Message, state: FSMContext):
    data = await state.get_data()
    if not (data.get('name') is None):
        await bot.send_chat_action(msg.chat.id, ChatAction.TYPING)
        user_city = data["user_city"]
        resp = await owm_client.get_current_data(user_city['lat'], user_city['lon'])
        print(resp)
        result, dialogue = await gen_text(msg.text, state, resp, data.get('dialogue'))
        await state.update_data(dialogue=dialogue)
        print(dialogue)
        await msg.answer(result)
    else:
        if (data.get('bot_name') is None): await state.update_data(bot_name="Тима")
        await bot.send_message(msg.chat.id, "Пожалуйста, задайте ваше имя")
        print(7)
        await state.set_state(botChats.name)
        print(8)



async def main():
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())