import logging

from aiogram import Router
from aiogram.types import CallbackQuery

from database.admin.menu_images import get_menu_images_from_db
from helpers.user.load_photos import load_product_photo

router = Router()

@router.callback_query(lambda c: c.data == 'about')
async def about(c: CallbackQuery):
    menu_images = get_menu_images_from_db()

    photo = None

    for menu_image in menu_images:
        image_path = menu_image[1]
        button_text = menu_image[2]

        if button_text == "Про нас":
            try:
                photo = await load_product_photo(image_path)
                break
            except Exception as e:
                logging.error(f"Ошибка при отправке фото для 'Про нас': {e}")
                break

    if photo:
        await c.message.delete()

        await c.message.answer_photo(
            photo,
            caption="О нашем боте:\n- Простой и удобный интерфейс\n- Находится в разработке",
            parse_mode="Markdown"
        )
    else:
        await c.message.edit_text(
            "О нашем боте:\n- Простой и удобный интерфейс\n- Находится в разработке\nФото отсутствует.",
            reply_markup=None
        )
