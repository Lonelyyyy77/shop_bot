from aiogram import Router
from aiogram.types import InlineKeyboardButton, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder


router = Router()


@router.callback_query(lambda c: c.data == 'admin_panel')
async def admin_panel(c: CallbackQuery):
    admin_kb = InlineKeyboardBuilder()
    admin_kb.row(InlineKeyboardButton(text='Добавить товар', callback_data='add_product'))
    admin_kb.row(InlineKeyboardButton(text='Добавить категорию товара', callback_data='add_category'))

    await c.message.edit_text(text='Admin panel', reply_markup=admin_kb.as_markup())

