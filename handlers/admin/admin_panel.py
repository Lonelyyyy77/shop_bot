import logging

from aiogram import Router
from aiogram.types import InlineKeyboardButton, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from pyexpat.errors import messages

from database.admin.menu_images import get_menu_images_from_db
from helpers.user.load_photos import load_product_photo

router = Router()


@router.callback_query(lambda c: c.data == 'admin_panel')
async def admin_panel(c: CallbackQuery):
    admin_kb = InlineKeyboardBuilder()
    admin_kb.row(InlineKeyboardButton(text='Добавить товар', callback_data='add_product'))
    admin_kb.row(InlineKeyboardButton(text='Добавить категорию товара', callback_data='add_category'))
    admin_kb.row(InlineKeyboardButton(text='Редактировать картинки в менюшках', callback_data='edit_images'))

    menu_images = get_menu_images_from_db()

    for menu_image in menu_images:
        image_path = menu_image[1]
        button_text = menu_image[2]

        if button_text == "Админ панель":
            try:
                photo = await load_product_photo(image_path)

                await c.message.delete()

                await c.message.answer_photo(
                    photo,
                    caption="Админ панель",
                    parse_mode="Markdown",
                    reply_markup=admin_kb.as_markup()
                )

                break
            except Exception as e:
                logging.error(f"Ошибка при отправке фото для админ панели: {e}")
                await c.message.answer(
                    text='Admin panel',
                    reply_markup=admin_kb.as_markup()
                )
                break


