import logging

import paypalrestsdk
import os

from aiogram import Router
from aiogram.types import InlineKeyboardButton, CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv

load_dotenv()

router = Router()

paypalrestsdk.configure({
    "mode": "sandbox",
    "client_id": os.getenv("PAYPAL_CLIENT_ID"),
    "client_secret": os.getenv("PAYPAL_CLIENT_SECRET"),
})


@router.callback_query(lambda callback: callback.data.startswith("generate_payment_"))
async def generate_payment(callback: CallbackQuery):
    data = callback.data.split("_")
    product_id = data[2]
    price = data[3]
    product_name = " ".join(data[4:]).replace("_", " ")

    logging.info(f"Инициализация платежа на сумму {price} для товара '{product_name}'")

    message_text = f"*{product_name}*\n\n💰 *Цена:* {price} руб."

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
                    "price": price,
                    "currency": "USD",
                    "quantity": 1
                }]
            },
            "amount": {
                "total": price,
                "currency": "USD"
            },
            "description": f"Оплата за товар {product_name} на сумму ${price}"
        }]
    })

    if payment.create():
        payment_link = next(link["href"] for link in payment.links if link["rel"] == "approval_url")

        payment_keyboard = InlineKeyboardBuilder()
        payment_keyboard.add(InlineKeyboardButton(text="💳 Оплатить через PayPal", url=payment_link))
        payment_keyboard.add(
            InlineKeyboardButton(text="🔗 Зарегистрироваться в PayPal", url="https://www.paypal.com/signup"))

        await callback.message.answer(
            message_text,
            parse_mode="Markdown",
            reply_markup=payment_keyboard.as_markup()
        )
    else:
        logging.error(f"Ошибка создания платежа: {payment.error}")
        await callback.message.answer("❗ Произошла ошибка при создании платежа. Попробуйте позже.")
        await callback.answer()
