import logging
import sqlite3

import paypalrestsdk
import os

from aiogram import Router
from aiogram.types import InlineKeyboardButton, CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv

from database.db import DB_NAME
from helpers.user.load_photos import load_product_photo

load_dotenv()


router = Router()

paypalrestsdk.configure({
    "mode": "sandbox",
    "client_id": os.getenv("PAYPAL_CLIENT_ID"),
    "client_secret": os.getenv("PAYPAL_CLIENT_SECRET"),
})


def pp_kb(amount, product_id, photo_paths):
    keyboard = InlineKeyboardBuilder()
    photo_paths_str = '|'.join(photo_paths)
    keyboard.add(
        InlineKeyboardButton(text=f"${amount}", callback_data=f"generate_payment_{product_id}_{amount}_{photo_paths_str}")
    )
    return keyboard



@router.callback_query(lambda callback: callback.data.startswith("generate_payment_"))
async def generate_payment(callback: CallbackQuery):
    data = callback.data.split("_")
    product_id = data[1]
    amount = data[2]
    image_paths = data[3]

    logging.info(f"Инициализация платежа на сумму ${amount} для товара с ID {product_id}")

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT name, desc FROM catalog_products WHERE id = ?", (product_id,))
    product = cursor.fetchone()
    conn.close()

    if not product:
        await callback.message.answer("Товар не найден.")
        await callback.answer()
        return

    product_name, description = product
    message_text = f"*{product_name}*\n\n{description}\n💰 *Цена:* {amount} руб."

    payment = paypalrestsdk.Payment({
        "intent": "sale",
        "payer": {"payment_method": "paypal"},
        "redirect_urls": {
            "return_url": "http://example.com/success",
            "cancel_url": "http://example.com/cancel"
        },
        "transactions": [{
            "item_list": {
                "items": [{
                    "name": product_name,
                    "sku": product_id,
                    "price": amount,
                    "currency": "USD",
                    "quantity": 1
                }]
            },
            "amount": {
                "total": amount,
                "currency": "USD"
            },
            "description": f"Оплата за товар {product_name} на сумму ${amount}"
        }]
    })

    if payment.create():
        payment_link = next(link["href"] for link in payment.links if link["rel"] == "approval_url")

        payment_keyboard = InlineKeyboardBuilder()
        payment_keyboard.add(InlineKeyboardButton(text=f"У меня есть PayPal", url=payment_link))
        payment_keyboard.add(InlineKeyboardButton(text="У меня нету PayPal", url="https://www.paypal.com/signup"))

        photo_paths = image_paths.split('|')
        if photo_paths:
            for photo_path in photo_paths:
                try:
                    photo = await load_product_photo(photo_path)
                    await callback.message.delete()
                    await callback.message.answer_photo(
                        photo, caption=message_text, parse_mode="Markdown", reply_markup=payment_keyboard.as_markup()
                    )
                    break
                except Exception as e:
                    logging.error(f"Ошибка загрузки фото для товара {product_name}: {e}")
                    await callback.message.answer(
                        f"{message_text}\n\n❗ Фото отсутствует.", parse_mode="Markdown", reply_markup=payment_keyboard.as_markup()
                    )
                    break
        else:
            await callback.message.delete()
            await callback.message.answer(
                f"{message_text}\n\n❗ Фото отсутствует.", parse_mode="Markdown", reply_markup=payment_keyboard.as_markup()
            )
    else:
        logging.error(payment.error)
        await callback.message.answer("Ошибка при создании платежа. Попробуйте позже.")
        await callback.answer()