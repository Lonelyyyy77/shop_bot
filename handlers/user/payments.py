import logging
import sqlite3

from aiogram import Router
from aiogram.types import CallbackQuery, InputFile

from database.db import DB_NAME
from helpers.payments.pay_pal import pp_kb
from helpers.user.load_photos import load_product_photo

router = Router()


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
            # Логируем путь фото
            logging.info(f"Попытка загрузить фото с пути: {photo_paths[0]}")

            # Загружаем фото с помощью вашей функции
            photo = await load_product_photo(photo_paths[0])  # Функция возвращает FSInputFile
            logging.info(f"Фото загружено с пути: {photo_paths[0]}")

            await callback_query.message.delete()
            await callback_query.message.answer_photo(
                photo, caption=message_text,
                parse_mode="Markdown",
                # reply_markup=pp_kb(amount=price, product_id=product_id, photo_paths=image_paths)
            )
            ## проблема выше, в выводе, само фото выводится

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


