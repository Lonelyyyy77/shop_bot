from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from states.admin import Categories
from database.admin.products import add_category_to_db

router = Router()


@router.callback_query(lambda c: c.data == 'add_category')
async def start_adding_category(c: CallbackQuery, state: FSMContext):
    await state.set_state(Categories.name)
    await c.message.edit_text("Введите название категории товара:")


@router.message(Categories.name)
async def process_category_name(message: Message, state: FSMContext):
    category_name = message.text
    await state.update_data(category_name=category_name)

    add_category_to_db(category_name)

    await message.answer("Категория успешно добавлена!")
    await state.clear()
