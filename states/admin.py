from aiogram.fsm.state import StatesGroup, State


class ProductForm(StatesGroup):
    name = State()
    price = State()
    desc = State()
    image_path = State()
    category = State()


class Categories(StatesGroup):
    name = State()


class MenuButtons(StatesGroup):
    waiting_for_button = State()
    waiting_for_image = State()
