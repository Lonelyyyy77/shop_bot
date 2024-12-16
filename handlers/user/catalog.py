import logging
import sqlite3
from itertools import product

from aiogram import Router
from aiogram.types import CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.admin.menu_images import get_menu_images_from_db
from database.admin.products import get_categories_from_db, get_products_by_category
from database.db import DB_NAME
from helpers.user.load_photos import load_product_photo

router = Router()


@router.callback_query(lambda c: c.data == 'catalog')
async def start_adding_category(c: CallbackQuery):
    await c.message.delete()

    categories = get_categories_from_db()
    menu_images = get_menu_images_from_db()

    image_path = None
    for menu_image in menu_images:
        if menu_image[2] == "Каталог":
            image_path = menu_image[1]
            break

    category_kb = InlineKeyboardBuilder()
    for category in categories:
        category_kb.add(
            InlineKeyboardButton(
                text=category['name'],
                callback_data=f"choose_category_{category['name']}"
            )
        )

    if image_path:
        try:
            photo = await load_product_photo(image_path)
            await c.message.answer_photo(
                photo, caption="Каталог", parse_mode="Markdown", reply_markup=category_kb.as_markup()
            )
        except Exception as e:
            logging.error(f"Ошибка загрузки фото: {e}")
            await c.message.answer("Выберите категорию товара:", reply_markup=category_kb.as_markup())
    else:
        await c.message.answer("Выберите категорию товара:", reply_markup=category_kb.as_markup())


@router.callback_query(lambda c: c.data.startswith("choose_category_"))
async def catalog(callback_query: CallbackQuery):
    category_name = callback_query.data.split("_", maxsplit=2)[2]

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM catalog_products WHERE category = ?", (category_name,))
    products = cursor.fetchall()
    conn.close()

    if not products:
        await callback_query.message.answer(f"Каталог категории '{category_name}' пуст. ❌")
        await callback_query.answer()
        return

    product_kb = InlineKeyboardBuilder()
    for product_id, product_name in products:
        product_kb.add(
            InlineKeyboardButton(text=product_name, callback_data=f"product_{product_id}")
        )

    menu_images = get_menu_images_from_db()
    photo = None
    for menu_image in menu_images:
        if menu_image[2] == "Каталог":
            try:
                photo = await load_product_photo(menu_image[1])
                break
            except Exception as e:
                logging.error(f"Ошибка загрузки фото для каталога: {e}")

    if photo:
        await callback_query.message.answer_photo(
            photo, caption=f"Товары в категории *{category_name}*: 👇",
            parse_mode="Markdown", reply_markup=product_kb.as_markup()
        )
    else:
        await callback_query.message.answer(
            f"Товары в категории *{category_name}*: 👇",
            parse_mode="Markdown", reply_markup=product_kb.as_markup()
        )

    await callback_query.answer()


@router.callback_query(lambda c: c.data.startswith("product_"))
async def show_product_details(callback_query: CallbackQuery):
    product_id = int(callback_query.data.split("_")[1])
    logging.info(f"Получен запрос на отображение товара с ID: {product_id}")

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT name, desc, price, image_path FROM catalog_products WHERE id = ?", (product_id,))
    product = cursor.fetchone()
    conn.close()

    if not product:
        await callback_query.message.answer("Товар не найден.")
        await callback_query.answer()
        return

    product_name, description, price, image_paths = product
    photo_paths = image_paths.split('|')

    message_text = f"*{product_name}*\n\n{description}\n💰 *Цена:* {price} руб."

    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text='Back to catalogue', callback_data='catalog'))

    kb.row(InlineKeyboardButton(text='Buy', callback_data=f'buy_{product_id}_{price}'))
    kb = kb.as_markup()

    if photo_paths:
        for photo_path in photo_paths:
            try:
                photo = await load_product_photo(photo_path)
                await callback_query.message.answer_photo(
                    photo, caption=message_text, parse_mode="Markdown", reply_markup=kb
                )
                break
            except Exception as e:
                logging.error(f"Ошибка загрузки фото для товара {product_name}: {e}")
                await callback_query.message.answer(
                    f"{message_text}\n\n❗ Фото отсутствует.", parse_mode="Markdown", reply_markup=kb
                )
                break
    else:
        await callback_query.message.answer(
            f"{message_text}\n\n❗ Фото отсутствует.", parse_mode="Markdown", reply_markup=kb
        )

    await callback_query.answer()

