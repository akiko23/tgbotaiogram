import random
import time
import types

import requests
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text

from bs4 import BeautifulSoup
from pyqiwip2p.p2p_types import QiwiError

import States.states
from Practice_Bot import valutes
from aiogram.utils import executor
import Practice_Bot.markups as nav
from Bots.fsmBot.test import Test
from Utils.set_bot_commands import set_default_commands
from Practice_Bot.db import Database
from pyqiwip2p import QiwiP2P
from Practice_Bot.config import QIWI_API_TOKEN
from functions.Payments import qiwi_pay, qiwi_buy_subscribe
from req_to_payUrl import parse_url
from States.states import FSMAdmin, RegistrationSteps
from States import states

TOKEN = '5418428043:AAEWqhzqka8Hs9JihfrM5yrIySeVaR9Ae4U'
URL = 'https://api.telegram.org/bot'

bot = Bot(TOKEN, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot, storage=MemoryStorage())
db = Database("database.db")
p2p = QiwiP2P(auth_key=QIWI_API_TOKEN)

dp.middleware.setup(LoggingMiddleware())

user_data = {}
commands = ['USD']
arr = []

def days_to_seconds(days):
    return days * 60 * 60 * 24


async def update_num_text(message: types.Message, new_value: int):
    # Общая функция для обновления текста с отправкой той же клавиатуры
    await message.edit_text(f"Укажите число валют: {new_value}", reply_markup=nav.get_keyboard())


def parse_telegram_updates(url):
    req = requests.get(url)

    soup = BeautifulSoup(req.text, "html.parser")
    result = soup.findAll('pre')

    return result


@dp.message_handler(commands=['start'])
async def start_bot(message: types.Message):
    if not db.user_exists(message.from_user.id):
        db.add_user(message.from_user.id)
        if db.get_nickname(message.from_user.id) == 'nul' and db.get_password(message.from_user.id) == 'nul':
            await bot.send_message(message.from_user.id, 'Push /regist')

    else:
        if db.user_exists(message.from_user.id) and (
                db.get_nickname(message.from_user.id) != 'nul' and db.get_password(message.from_user.id) != 'nul'):
            if db.user_money(message.from_user.id) >= 1000:
                await bot.send_message(message.from_user.id,
                                       f'Привет, {message.from_user.first_name + message.from_user.last_name}\nЧтобы конвертировать валюты, нажми /convert\n'
                                       'Ввести координаты /location\nОстальные команды в /menu',
                                       reply_markup=nav.ToAutorMenu)
                await set_default_commands(dp)
            elif 5 < db.user_money(message.from_user.id) < 1000:
                await bot.send_message(message.from_user.id,
                                       f'Вы положили на счет {db.user_money(message.from_user.id)} рублей. Вам не хватает еще {1000 - db.user_money(message.from_user.id)}',
                                       reply_markup=nav.topUpMenu)

            else:
                await bot.send_message(message.from_user.id,
                                       'Для использования бота необходимо положить на него 1000 рублей',
                                       reply_markup=nav.topUpMenu)


@dp.message_handler(commands=['convert'])
async def start_converter(message: types.Message):
    await bot.send_message(message.from_user.id,
                           'Может конвертировать любое количество валюты, которое пожелаешь(пока только в рублях, а uah это гривны)',
                           reply_markup=nav.valutes_reply)


@dp.callback_query_handler(Text(startswith='num_'))
async def callbacks_num(call: types.CallbackQuery):
    # Получаем текущее значение для пользователя, либо считаем его равным 0
    user_value = user_data.get(call.from_user.id, 0)
    # Парсим строку и извлекаем действие, например `num_incr` -> `incr`
    action = call.data.split("_")[1]
    if action == 'incr':
        user_data[call.from_user.id] = user_value + 1
        await update_num_text(call.message, user_value + 1)
    elif action == 'decr':
        user_data[call.from_user.id] = user_value - 1
        await update_num_text(call.message, user_value - 1)

    elif action == 'incr10000':
        user_data[call.from_user.id] = user_value + 10000
        await update_num_text(call.message, user_value + 10000)

    elif action == 'incr100000':
        user_data[call.from_user.id] = user_value + 100000
        await update_num_text(call.message, user_value + 100000)

    elif action == 'finish':
        global mess
        # Если бы мы не меняли сообщение, то можно было бы просто удалить клавиатуру
        # вызовом await call.message.delete_reply_markup().
        # Но т.к. мы редактируем сообщение и не отправляем новую клавиатуру,
        # то она будет удалена и так.
        if len(value) > 0:
            await call.message.edit_text(f'{user_value} {text2}: {user_value * value[0]}{text}')

        else:
            await call.message.edit_text(f'{user_value} {text2}: {user_value * value[0]}{text}')

    # Не забываем отчитаться о получении колбэка
    await call.answer()


@dp.message_handler(commands=['admin_menu'])
async def admin_command(mes: types.Message):
    if db.get_user_status(mes.from_user.id) == "admin":
        await bot.send_message(mes.from_user.id, 'Вы админ, добро пожаловать')
    else:
        await bot.send_message(mes.from_user.id, 'У вас нет прав для использования этой команды')


@dp.message_handler(commands=['menu'])
async def menu(mes: types.Message):
    await bot.send_message(mes.from_user.id, 'Вы вошли в меню', reply_markup=nav.menu_markup)


@dp.message_handler(commands=['regist'], state=None)
async def start_registration(message: types.Message):
    if db.get_nickname(message.from_user.id) and db.get_password(message.from_user.id) == 'nul':
        await bot.send_message(message.from_user.id, 'Set your nickname')
        await RegistrationSteps.nickname.set()
    else:
        await bot.send_message(message.from_user.id, 'Вы уже зарегестрированы')


@dp.message_handler(content_types=['text'], state=RegistrationSteps.nickname)
async def get_nickname(message: types.Message):
    db.set_nickname(message.from_user.id, message.text)
    await RegistrationSteps.next()
    await bot.send_message(message.from_user.id, 'Теперь введите пароль')


@dp.message_handler(content_types=['text'], state=RegistrationSteps.password)
async def get_password(message: types.Message, state: FSMContext):
    db.set_password(message.from_user.id, message.text)
    await bot.send_message(message.from_user.id, 'Регистрация завершена')
    await bot.send_message(message.from_user.id,
                           f"Ваш ник: {db.get_nickname(message.from_user.id)}\nВаш пароль: {db.get_password(message.from_user.id)}")
    await state.finish()


@dp.message_handler(commands=['load'], state=None)
async def cm_start(message: types.Message):
    await FSMAdmin.photo.set()
    await message.reply('Загрузи фото', reply_markup=nav.Cancel_Menu)


@dp.message_handler(content_types=['photo', 'text'], state=FSMAdmin.photo)
async def load_photo(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        try:
            data['photo'] = message.photo[0].file_id
            arr.append("photo")
            await FSMAdmin.next()
            await message.reply('Теперь введи название', reply_markup=nav.Cancel_Menu)
        except IndexError:
            await message.reply(
                'Я не понимаю вас. Если вы хотите отменить загрузку и воспользоваться другой командой, нажмите ОТМЕНА')


@dp.message_handler(state=FSMAdmin.name)
async def load_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['name'] = message.text
        arr.append("name")
        await FSMAdmin.next()
        await message.reply('Теперь введи описание', reply_markup=nav.Cancel_Menu)


@dp.message_handler(state=FSMAdmin.description)
async def load_description(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['description'] = message.text
        arr.append("description")
        await FSMAdmin.next()
        await message.reply('Теперь укажи цену', reply_markup=nav.Cancel_Menu)

        if '/' in message.text:
            await message.reply(
                'Если вы хотите отменить загрузку и воспользоваться другой командой, нажмите ОТМЕНА')


@dp.message_handler(state=FSMAdmin.price)
async def load_price(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['price'] = float(message.text)
        arr.append("price")
        async with state.proxy():
            with open("tele_photo.png", "w") as f:
                f.write(data['photo'])
                time.sleep(5)
            with open("tele_photo.png") as f:
                file = f.read()

            await bot.send_photo(message.from_user.id, file)
            await bot.send_message(message.from_user.id, "Фото: " + str(data["photo"]) + "\n" + "Имя: " + str(
                data["name"]) + "\n" + "Описание: " + data[
                                       "description"] + "\n" + "Цена: " + str(data['price']))

            time.sleep(3)
            f.close()
        await state.finish()


@dp.callback_query_handler(Text(startswith='cancel_'))
async def cancel_load(call: types.CallbackQuery, state: FSMContext):
    action = call.data.split('_')[1]
    if action == 'load':
        await state.finish()
        await call.message.reply('Вы отменили загрузку обьявления')


@dp.message_handler(content_types=['text'])
async def cmd_numbers(message: types.Message):
    if message.text == '👤ПРОФИЛЬ':
        await bot.send_message(message.from_user.id, f'Ваш баланс: {db.user_money(message.from_user.id)} руб.',
                               reply_markup=nav.topUpMenu)

    elif message.text == 'ПОДПИСКА':
        if db.get_podpiska(message.from_user.id) == 'not_paid':
            await bot.send_message(message.from_user.id, 'Выберите способ оплаты', reply_markup=nav.pay_menu())
        else:
            await bot.send_message(message.from_user.id, 'У вас уже есть подписка')


@dp.callback_query_handler(Text('top_up'), state=None)
async def top_up_money(call: types.CallbackQuery):
    await bot.delete_message(call.from_user.id, call.message.message_id)
    await bot.send_message(call.from_user.id, 'Введите сумму для пополнения')
    await Test.D1.set()


@dp.callback_query_handler(Text(startswith='pay_'), state=None)
async def buy_subscribe(call: types.CallbackQuery):
    action = call.data.split('_')[1]

    if action == 'qiwi':
        if call.message.chat.type == 'private':
            message_money = 100

            comment = str(call.from_user.id) + "_" + str(random.randint(1000, 9999))
            bill = p2p.bill(amount=message_money, lifetime=15, comment=comment)

            db.add_check(call.from_user.id, message_money, bill.bill_id)
            url = bill.pay_url

            await bot.send_message(call.from_user.id,
                                   f"Вам нужно отправить {message_money} рублей на наш счет киви\nСсылка: {url}\nКомментарий к оплате:{comment}",
                                   reply_markup=nav.buy_menu(url=bill.pay_url, bill=bill.bill_id))
            await Test.D2.set()

    elif action == 'sber':
        pass

    elif action == 'umoney':
        pass


@dp.message_handler(content_types=['text'], state=Test.D1)
async def bot_mess(message: types.Message):
    if await qiwi_pay(message):
        await Test.next()


@dp.callback_query_handler(Text(contains="check"), state=Test.D2)
async def check(callback: types.CallbackQuery, state: FSMContext):
    bill = str(callback.data[6:])
    info = db.get_check(bill)
    if info:
        if str(p2p.check(bill_id=bill).status) == "PAID":
            user_money = db.user_money(callback.from_user.id)
            money = int(info[2])
            db.set_money(callback.from_user.id, user_money + money)
            await bot.send_message(callback.from_user.id,
                                   f'Спасибо, пупсик. У тебя теперю на балансе {money} рублей. Нажми /start')
            await bot.send_sticker(callback.from_user.id,
                                   'CAACAgIAAxkBAAEE4lVillPfpjSxJSOjSjMob6AVe4lYwQACdhYAAudweUkUQJvaPY6GxSQE')
            await state.finish()

        else:
            await bot.send_message(callback.from_user.id, 'Вы не оплатили счет:(',
                                   reply_markup=nav.buy_menu(False, bill=bill))
    else:
        await bot.send_message(callback.from_user.id, 'Счет не найден :(')


@dp.callback_query_handler(Text("cancel"), state=Test.D2)
async def cancel(call: types.CallbackQuery, state: FSMContext):
    await call.message.reply("Оплата отменена :(")
    await state.finish()


@dp.message_handler(commands=['admin_menu'])
async def admin_panel(message: types.Message):
    await bot.send_message(message.from_user.id, "Вы вошли в панель админа", reply_markup=nav.admin_panel())


@dp.message_handler(content_types=['text'])
async def convert(message: types.Message):
    global value
    global text
    global text2
    if not '/' in message.text:
        if message.text == 'USD':
            user_data[message.from_user.id] = 0
            value = [valutes.convert_usd_to_rub_text]
            text = ' RUB'
            text2 = ' USD'
            await message.answer('Укажите число: 0', reply_markup=nav.get_keyboard())

        elif message.text == 'UAH':
            user_data[message.from_user.id] = 0
            value = [valutes.convert_uah_to_rub_text]
            text = ' RUB'
            text2 = ' грив.'
            await message.answer('Укажите число: 0', reply_markup=nav.get_keyboard())

        elif message.text == 'SUM':
            user_data[message.from_user.id] = 0
            value = [valutes.convert_sum_to_rub_text, valutes.convert_uzs_to_amd_text]
            text2 = ' SUM'
            text = ' RUB'
            await message.answer('Укажите число: 0', reply_markup=nav.get_keyboard())


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
