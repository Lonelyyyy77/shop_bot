from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram import F, Router

import os

from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.admin.products import add_product_to_db, get_categories_from_db
from states.admin import ProductForm

router = Router()


@router.callback_query(lambda c: c.data == 'add_product')
async def start_adding_product(c: CallbackQuery, state: FSMContext):
    await c.message.delete()
    await state.set_state(ProductForm.name)
    await c.message.answer("Введите название товара:")


@router.message(ProductForm.name)
async def process_product_name(message: Message, state: FSMContext):
    product_name = message.text
    await state.update_data(product_name=product_name)

    await message.answer("Введите цену товара:")
    await state.set_state(ProductForm.price)


@router.message(ProductForm.price)
async def process_product_price(message: Message, state: FSMContext):
    try:
        product_price = float(message.text)
        await state.update_data(product_price=product_price)
    except ValueError:
        await message.answer("Неверный формат цены. Введите число.")
        return

    await message.answer("Введите описание товара:")
    await state.set_state(ProductForm.desc)


@router.message(ProductForm.desc)
async def process_product_description(message: Message, state: FSMContext):
    product_desc = message.text
    await state.update_data(product_desc=product_desc)

    await message.answer("Отправьте фото товара:")
    await state.set_state(ProductForm.image_path)


@router.message(ProductForm.image_path, F.photo)
async def process_product_image(message: Message, state: FSMContext):
    file_id = message.photo[-1].file_id
    file = await message.bot.get_file(file_id)

    photo_path = os.path.join('product_photos', f"{file_id}.jpg")

    await message.bot.download_file(file.file_path, photo_path)

    await state.update_data(product_image_path=photo_path)

    categories = get_categories_from_db()

    category_kb = InlineKeyboardBuilder()
    for category in categories:
        category_kb.add(InlineKeyboardButton(text=category['name'], callback_data=f"category_{category['id']}"))

    await message.answer("Выберите категорию товара:", reply_markup=category_kb.as_markup())

    await state.set_state(ProductForm.category)


@router.callback_query(lambda c: c.data.startswith('category_'))
async def process_category_selection(callback_query: CallbackQuery, state: FSMContext):
    category_id = int(callback_query.data.split('_')[1])

    category_name = next((category['name'] for category in get_categories_from_db() if category['id'] == category_id),
                         None)

    await state.update_data(product_category=category_name)

    user_data = await state.get_data()

    add_product_to_db(
        user_data['product_name'],
        user_data['product_price'],
        user_data['product_desc'],
        user_data['product_image_path'],
        user_data['product_category']
    )

    await callback_query.message.answer("Товар успешно добавлен!")
    await state.clear()
