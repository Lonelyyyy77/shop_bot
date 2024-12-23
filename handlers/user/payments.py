import logging
import sqlite3

from aiogram import Router
from aiogram.types import CallbackQuery, InputFile, InlineKeyboardButton, InlineQueryResult
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.db import DB_NAME
from helpers.user.load_photos import load_product_photo

router = Router()


def pp_kb(amount, product_name):
    keyboard = InlineKeyboardBuilder()
    keyboard.add(
        InlineKeyboardButton(
            text=f"${amount}",
            callback_data=f"generate_payment_{amount}_for_{product_name}"
        )
    )
    return keyboard


@router.callback_query(lambda c: c.data.startswith('p_ch_buy_'))
async def payment_choose(callback_query: CallbackQuery):
    data = callback_query.data.split("_")
    product_id = data[3]
    price = data[4]
    product_name = " ".join(data[5:]).replace("_", " ")

    logging.info(f"Выбор метода оплаты для товара ID: {product_id}, сумма: {price}, название: {product_name}")

    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text='💳 Оплатить через PayPal',
                                callback_data=f'generate_payment_{product_id}_{price}_{product_name}'))
    kb.row(InlineKeyboardButton(text='Оплатить через телеграм звезды',
                                callback_data=f'stars_payment_{product_id}_{price}_{product_name}'))
    kb.row(InlineKeyboardButton(text='🔙 Назад к товару', callback_data=f'product_{product_id}_{product_name}'))

    await callback_query.message.answer(
        text=f"Выберите метод оплаты для товара *{product_name}*:",
        reply_markup=kb.as_markup()
    )

    await callback_query.answer()


@router.callback_query(lambda c: c.data.startswith("buy_"))
async def buy_product(callback_query: CallbackQuery):
    product_id = int(callback_query.data.split("_")[1])
    logging.info(f"Получен запрос на покупку товара с ID: {product_id}")

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT name, price, image_path FROM catalog_products WHERE id = ?", (product_id,))
    product = cursor.fetchone()
    conn.close()

    if not product:
        await callback_query.message.answer("Информация о товаре не найдена.")
        await callback_query.answer()
        return

    product_name, price, image_paths = product
    photo_paths = image_paths.split('|')

    message_text = f"🛒 *{product_name}*\n💰 *Price:* {price} 💲"

    if photo_paths:
        try:
            logging.info(f"Попытка загрузить фото с пути: {photo_paths[0]}")

            photo = await load_product_photo(photo_paths[0])
            logging.info(f"Фото загружено с пути: {photo_paths[0]}")

            await callback_query.message.delete()
            await callback_query.message.answer_photo(
                photo,
                caption=message_text,
                parse_mode="Markdown",
                reply_markup=pp_kb(amount=price, product_name=product_name).as_markup()
            )

        except Exception as e:
            logging.error(f"Ошибка загрузки фото для товара {product_name}: {e}")
            await callback_query.message.answer(
                f"{message_text}\n\n❗ Фото отсутствует.", parse_mode="Markdown"
            )
    else:
        await callback_query.message.answer(
            f"{message_text}\n\n❗ Фото отсутствует.", parse_mode="Markdown"
        )

    await callback_query.answer()
