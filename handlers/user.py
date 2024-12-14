import logging
import sqlite3

from aiogram import Router
from aiogram.types import CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.admin.products import get_categories_from_db, get_products_by_category, get_catalog_products_from_db
from database.db import DB_NAME
from helpers.user import load_product_photo

router = Router()


@router.callback_query(lambda c: c.data == 'catalog')
async def start_adding_category(c: CallbackQuery):
    categories = get_categories_from_db()

    category_kb = InlineKeyboardBuilder()

    for category in categories:
        category_kb.add(
            InlineKeyboardButton(text=category['name'], callback_data=f"choose_category_{category['name']}"))

    await c.message.edit_text("Выберите категорию товара:", reply_markup=category_kb.as_markup())


@router.callback_query(lambda c: c.data.startswith("choose_category_"))
async def catalog(callback_query: CallbackQuery):
    logging.info("Получен запрос на просмотр каталога.")

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, image_path FROM catalog_products")
    products = cursor.fetchall()
    conn.close()

    if not products:
        await callback_query.message.answer("Каталог пуст. ❌")
        await callback_query.answer()
        return

    for product in products:
        product_id = product[0]
        product_name = product[1]
        photo_paths = product[2].split('|')

        message_text = f"*Товар ID {product_id}:*\nName: {product_name}"

        details_button = InlineKeyboardButton(
            text="Подробнее", callback_data=f"catalog_{product_id}"
        )
        markup = InlineKeyboardBuilder()
        markup.add(details_button)

        if photo_paths:
            for photo_path in photo_paths:
                try:
                    logging.info(f"Попытка отправить фото для товара: {product_name}")

                    photo = await load_product_photo(photo_path)

                    await callback_query.message.answer_photo(
                        photo, caption=message_text, parse_mode="Markdown", reply_markup=markup.as_markup()
                    )
                    break

                except FileNotFoundError:
                    logging.error(f"Фото не найдено для товара: {product_name}.")
                    await callback_query.message.answer(
                        f"Фото для товара {product_name} отсутствует.\n\n{message_text}",
                        parse_mode="Markdown",
                        reply_markup=markup.as_markup()
                    )
                    break

                except Exception as e:
                    logging.error(f"Ошибка при загрузке фото для товара {product_name}: {e}")
                    await callback_query.message.answer(
                        f"Ошибка при отображении товара {product_name}: {str(e)}\n\n{message_text}",
                        parse_mode="Markdown",
                        reply_markup=markup.as_markup()
                    )
                    break
        else:
            await callback_query.message.answer(
                f"{message_text}\nФото отсутствует.", parse_mode="Markdown", reply_markup=markup.as_markup()
            )

    await callback_query.answer()
