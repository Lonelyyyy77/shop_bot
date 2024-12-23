import logging
import sqlite3
from collections import defaultdict
from itertools import product

from aiogram import Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InputMediaPhoto
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.admin.menu_images import get_menu_images_from_db
from database.admin.products import get_categories_from_db, get_products_by_category
from database.db import DB_NAME
from helpers.user.load_photos import load_product_photo

user_cart = defaultdict(list)

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
        # Кодировка кавычек и пробелов в product_name
        product_name_encoded = product_name.replace(" ", "_").replace("'", "''")
        product_kb.add(
            InlineKeyboardButton(text=product_name, callback_data=f"product_{product_id}_{product_name_encoded}")
            # передаем имя товара
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
        await callback_query.message.edit_media(
            InputMediaPhoto(media=photo, caption=f"Товары в категории *{category_name}*: 👇"),
            reply_markup=product_kb.as_markup()
        )
    else:
        await callback_query.message.answer(
            f"Товары в категории *{category_name}*: 👇",
            parse_mode="Markdown", reply_markup=product_kb.as_markup()
        )

    await callback_query.answer()


@router.callback_query(lambda c: c.data.startswith("product_"))
async def show_product_details(callback_query: CallbackQuery):
    data = callback_query.data.split("_")
    product_id = int(data[1])

    product_name = " ".join(data[2:]).replace("_", " ")

    logging.info(f"Получен запрос на отображение товара с ID: {product_id} и названием {product_name}")

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

    # Инициализируем корзину пользователя, если она не существует
    user_id = callback_query.from_user.id
    cart = user_cart[user_id]

    # Проверяем, есть ли уже этот товар в корзине
    existing_item = next((item for item in cart if item['product_id'] == product_id), None)
    quantity = existing_item[
        'quantity'] if existing_item else 1  # Если товар уже в корзине, берем его количество, иначе 1

    # Обновляем текст сообщения
    message_text = f"*{product_name}*\n\n{description}\n💰 *Цена:* {price * quantity} руб.\n\nКоличество: {quantity}"

    # Создаем кнопки для управления количеством
    kb = InlineKeyboardBuilder()
    if quantity > 1:
        kb.row(InlineKeyboardButton(text="➖ Отнять 1", callback_data=f"decrease_{product_id}"))
    kb.row(InlineKeyboardButton(text="🛒 Buy", callback_data=f"p_ch_buy_{product_id}_{price}_{product_name}_{quantity}"))
    kb.row(InlineKeyboardButton(text="➕ Добавить 1", callback_data=f"increase_{product_id}"))
    kb.row(InlineKeyboardButton(text="🔙 Back to catalogue", callback_data='catalog'))

    # Если есть фото, показываем его
    if photo_paths:
        try:
            photo = await load_product_photo(photo_paths[0])
            await callback_query.message.answer_photo(
                photo, caption=message_text, parse_mode="Markdown", reply_markup=kb.as_markup()
            )
        except Exception as e:
            logging.error(f"Ошибка загрузки фото: {e}")
            await callback_query.message.answer(
                f"{message_text}\n\n❗ Фото отсутствует.", parse_mode="Markdown", reply_markup=kb.as_markup()
            )
    else:
        await callback_query.message.answer(
            f"{message_text}\n\n❗ Фото отсутствует.", parse_mode="Markdown", reply_markup=kb.as_markup()
        )

    await callback_query.answer()


@router.callback_query(lambda c: c.data.startswith("increase_"))
async def increase_quantity(callback_query: CallbackQuery):
    data = callback_query.data.split("_")
    product_id = int(data[1])

    user_id = callback_query.from_user.id
    cart = user_cart[user_id]

    # Проверяем, есть ли этот товар в корзине
    existing_item = next((item for item in cart if item['product_id'] == product_id), None)

    # Если товар не найден в корзине, добавляем его с количеством 1
    if existing_item is None:
        cart.append({'product_id': product_id, 'quantity': 1})
        existing_item = cart[-1]  # Получаем добавленный товар

    existing_item['quantity'] += 1  # Увеличиваем количество

    # Обновляем информацию о товаре
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

    quantity = existing_item['quantity']  # Получаем обновленное количество товара
    message_text = f"*{product_name}*\n\n{description}\n💰 *Цена:* {price * quantity} руб.\n\nКоличество: {quantity}"

    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="➖ Отнять 1", callback_data=f"decrease_{product_id}"))
    kb.row(InlineKeyboardButton(text="🛒 Buy", callback_data=f"p_ch_buy_{product_id}_{price}_{product_name}_{quantity}"))
    kb.row(InlineKeyboardButton(text="➕ Добавить 1", callback_data=f"increase_{product_id}"))
    kb.row(InlineKeyboardButton(text="🔙 Back to catalogue", callback_data='catalog'))

    # Если есть фото, показываем его
    if photo_paths:
        # message_text = f"*{product_name}*\n\n{description}\n💰 *Цена:* {price * quantity} руб.\n\nКоличество: {quantity}"

        try:
            photo = await load_product_photo(photo_paths[0])
            await callback_query.message.answer_photo(photo,
                                                      text=message_text, parse_mode="Markdown",
                                                      reply_markup=kb.as_markup()
                                                      )
        except Exception as e:
            logging.error(f"Ошибка загрузки фото: {e}")
            await callback_query.message.delete()

            await callback_query.message.answer(
                text=f"{message_text}\n\n❗ Фото отсутствует.", parse_mode="Markdown", reply_markup=kb.as_markup()
            )
    else:
        await callback_query.message.answer(
            text=f"{message_text}\n\n❗ Фото отсутствует.", parse_mode="Markdown", reply_markup=kb.as_markup()
        )

    await callback_query.answer()


# Обработчик для уменьшения количества товара в корзине
@router.callback_query(lambda c: c.data.startswith("decrease_"))
async def decrease_quantity(callback_query: CallbackQuery):
    data = callback_query.data.split("_")
    product_id = int(data[1])

    user_id = callback_query.from_user.id
    cart = user_cart[user_id]

    # Проверяем, есть ли этот товар в корзине
    existing_item = next((item for item in cart if item['product_id'] == product_id), None)
    if existing_item:
        if existing_item['quantity'] > 1:
            existing_item['quantity'] -= 1  # Уменьшаем количество
        else:
            cart.remove(existing_item)  # Удаляем товар, если его количество стало 0

    # Обновляем информацию о товаре
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

    quantity = existing_item['quantity'] if existing_item else 0
    message_text = f"*{product_name}*\n\n{description}\n💰 *Цена:* {price * quantity} руб.\n\nКоличество: {quantity}"

    kb = InlineKeyboardBuilder()
    if quantity > 1:
        kb.row(InlineKeyboardButton(text="➖ Отнять 1", callback_data=f"decrease_{product_id}"))
    kb.row(InlineKeyboardButton(text="🛒 Buy", callback_data=f"p_ch_buy_{product_id}_{price}_{product_name}_{quantity}"))
    kb.row(InlineKeyboardButton(text="➕ Добавить 1", callback_data=f"increase_{product_id}"))
    kb.row(InlineKeyboardButton(text="🔙 Back to catalogue", callback_data='catalog'))

    # Если есть фото, показываем его
    if photo_paths:
        try:
            photo = await load_product_photo(photo_paths[0])
            await callback_query.message.edit_text(
                text=message_text, parse_mode="Markdown", reply_markup=kb.as_markup()
            )
        except Exception as e:
            logging.error(f"Ошибка загрузки фото: {e}")
            await callback_query.message.edit_text(
                text=f"{message_text}\n\n❗ Фото отсутствует.", parse_mode="Markdown", reply_markup=kb.as_markup()
            )
    else:
        await callback_query.message.edit_text(
            text=f"{message_text}\n\n❗ Фото отсутствует.", parse_mode="Markdown", reply_markup=kb.as_markup()
        )

    await callback_query.answer()
