from aiogram.dispatcher.filters.state import StatesGroup, State


class FSMAdmin(StatesGroup):
    photo = State()
    name = State()
    description = State()
    price = State()


class Convert(StatesGroup):
    S1 = State()
    S2 = State()


class Send(StatesGroup):
    S1 = State()
    S2 = State()


class RegistrationSteps(StatesGroup):
    nickname = State()
    password = State()

class Subscribe(StatesGroup):
    shoosing_choice_of_payment = State()
    qiwi = State()
    sber_pay = State()
    Umoney_pay = State()

