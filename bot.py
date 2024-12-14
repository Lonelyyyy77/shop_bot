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
from handlers.user import router as user_router

from database.db import create_tables
from helpers.admin import is_admin

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
        main_menu_kb.add(InlineKeyboardButton(text='About Us & FAQ', callback_data='about'))
        main_menu_kb.add(InlineKeyboardButton(text='Support', callback_data='help'))
    else:
        main_menu_kb = InlineKeyboardBuilder()
        main_menu_kb.row(InlineKeyboardButton(text='Go shopping!', callback_data='catalog'))
        main_menu_kb.row(
            InlineKeyboardButton(text='About Us & FAQ', callback_data='about'),
            InlineKeyboardButton(text='Support', callback_data='help')
        )

    await message.answer("Menu:", reply_markup=main_menu_kb.as_markup())


async def main():
    create_tables()

    bot = Bot(token=TOKEN)
    dp = Dispatcher()

    dp.include_router(router)

    dp.include_router(admin_router)
    dp.include_router(user_router)

    dp.include_router(add_product_router)
    dp.include_router(add_category_router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
