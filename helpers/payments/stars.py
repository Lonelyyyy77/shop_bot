import sqlite3

from aiogram import types, Router, F
from aiogram.types import LabeledPrice, InlineKeyboardButton, PreCheckoutQuery, CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.db import DB_NAME

CURRENCY = 'XTR'

router = Router()


@router.pre_checkout_query()
async def command_refund_handler(pre_checkout_query=PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)


@router.message(F.successful_payment)
async def process_successful_payment(message: types.Message) -> None:
    await message.answer("Платеж успешен!", message_effect_id='5104841245755180586')

    # admin_message = (
    #     f"Платеж успешен!\n"
    #     f"Telegram Payment Charge ID: {message.successful_payment.telegram_payment_charge_id}\n"
    #     f"Сумма: {message.successful_payment.total_amount / 100} {message.successful_payment.currency}"
    # )
    # await bot.send_message(get_all_admins(), admin_message)


def payment_kb():
    builder = InlineKeyboardBuilder()

    pay_button = InlineKeyboardButton(text="⭐️ PAY NOW ⭐️", pay=True)
    builder.row(pay_button)

    return builder.as_markup()


@router.callback_query(lambda c: c.data.startswith('stars_payment_'))
async def stars_payment(callback_query: CallbackQuery):
    await handle_donate_stars(callback_query.message, callback_query.data)


async def handle_donate_stars(message: Message, callback_data: str):
    data = callback_data.split("_")
    product_id = data[2]
    price = int(float(data[3]) * 100)

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM catalog_products WHERE id = ?", (product_id,))
    product = cursor.fetchone()
    conn.close()

    if not product:
        await message.answer("Товар не найден.")
        return

    product_name = product[0]

    labeled_price = [LabeledPrice(label=product_name, amount=price)]

    await message.answer_invoice(
        title=f'Оплата через Telegram звезды для {product_name}',
        description=f'Оплата товара #{product_id}: {product_name}',
        payload=f'payment_{product_id}',
        provider_token='',
        currency=CURRENCY,
        prices=labeled_price,
        reply_markup=payment_kb(),
    )
