from aiogram import types, Router, F
from aiogram.types import LabeledPrice, InlineKeyboardButton, PreCheckoutQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

CURRENCY = 'XTR'

router = Router()


@router.pre_checkout_query()
async def command_refund_handler(pre_checkout_query=PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)


@router.message(F.successful_payment)
async def process_successful_payment(message: types.Message) -> None:
    await message.answer("Платеж успешен!", message_effect_id='5104841245755180586')

    admin_message = (
        f"Платеж успешен!\n"
        f"Telegram Payment Charge ID: {message.successful_payment.telegram_payment_charge_id}\n"
        f"Сумма: {message.successful_payment.total_amount / 100} {message.successful_payment.currency}"
    )
    # await bot.send_message(ADMIN_ID, admin_message)


def payment_kb():
    builder = InlineKeyboardBuilder()

    pay_button = InlineKeyboardButton(text="⭐️ PAY NOW ⭐️", pay=True)
    builder.add(pay_button)

    back_button = InlineKeyboardButton(text="BACK", callback_data='back_to_main')
    builder.add(back_button)

    return builder.as_markup()


async def handle_donate_amphetamine(message: types.Message):
    prices = [LabeledPrice(label='', amount=1)]
    await message.answer_invoice(
        title='Payment',
        description='##',
        prices=prices,
        provider_token="",
        payload="channel_support",
        currency=CURRENCY,
        reply_markup=payment_kb(),
    )
