import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, Router
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv

from handlers.admin.admin_panel import router as admin_router
from handlers.admin.add_product import router as add_product_router
from handlers.admin.add_category import router as add_category_router
from handlers.user.catalog import router as user_router
from handlers.admin.edit_images import router as edit_images_router
from handlers.user.about_us import router as user_about_us_router
from handlers.user.support import router as user_support_router
from handlers.user.payments import router as user_payments_router
from helpers.payments.pay_pal import router as pay_pal_router
from helpers.payments.stars import router as pay_stars_router

from database.admin.menu_images import get_menu_images_from_db
from database.db import create_tables
from helpers.admin.admin import is_admin
from helpers.user.load_photos import load_product_photo

load_dotenv()

TOKEN = os.getenv('TOKEN')
router = Router()

logging.basicConfig(level=logging.INFO)


@router.message(CommandStart())
async def start_handler(message: Message):
    user_id = message.from_user.id

    if await is_admin(user_id):
        main_menu_kb = InlineKeyboardBuilder()
        main_menu_kb.row(InlineKeyboardButton(text='Admin Panel', callback_data='admin_panel'))
        main_menu_kb.row(InlineKeyboardButton(text='Go shopping!', callback_data='catalog'))
        main_menu_kb.row(InlineKeyboardButton(text='About Us & FAQ', callback_data='about'))
        main_menu_kb.add(InlineKeyboardButton(text='Support', callback_data='help'))
    else:
        main_menu_kb = InlineKeyboardBuilder()
        main_menu_kb.row(InlineKeyboardButton(text='Go shopping!', callback_data='catalog'))
        main_menu_kb.row(
            InlineKeyboardButton(text='About Us & FAQ', callback_data='about'),
            InlineKeyboardButton(text='Support', callback_data='help')
        )

    menu_images = get_menu_images_from_db()

    if not menu_images:
        await message.answer("Изображения меню не найдены. Пожалуйста, добавьте их в настройках бота.")
        return

    for menu_image in menu_images:
        image_path = menu_image[1]
        button_text = menu_image[2]

        if button_text == "Стартовое меню":
            try:
                photo = await load_product_photo(image_path)

                await message.answer_photo(
                    photo, caption="Here is your shopping menu!", parse_mode="Markdown",
                    reply_markup=main_menu_kb.as_markup()
                )

            except Exception as e:
                logging.error(f"Ошибка при отправке фото: {str(e)}")
                await message.answer("Ошибка при отправке картинки для меню.")

        # else:
        #     await message.answer("Menu:", reply_markup=main_menu_kb.as_markup())


async def main():
    create_tables()

    bot = Bot(token=TOKEN)
    dp = Dispatcher()

    dp.include_router(router)

    dp.include_router(admin_router)
    dp.include_router(user_router)

    dp.include_router(add_product_router)
    dp.include_router(add_category_router)
    dp.include_router(edit_images_router)
    dp.include_router(user_about_us_router)
    dp.include_router(user_support_router)
    dp.include_router(user_payments_router)
    dp.include_router(pay_pal_router)
    dp.include_router(pay_stars_router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
