import sqlite3

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.admin.menu_images import get_menu_images_from_db
from database.db import DB_NAME
from states.admin import MenuButtons

router = Router()


def get_available_buttons():
    return ["Стартовое меню", "Каталог", "Админ панель", "Про нас", "Поддержка"]


@router.callback_query(lambda c: c.data == 'edit_images')
async def add_image_to_menu(callback_query: CallbackQuery):
    await callback_query.message.delete()

    available_buttons = get_available_buttons()

    menu_kb = InlineKeyboardBuilder()

    for button_text in available_buttons:
        menu_images = get_menu_images_from_db()
        has_image = False
        for menu_image in menu_images:
            if menu_image[2] == button_text:
                has_image = True
                break

        emoji = "✅" if has_image else "❌"
        menu_kb.row(InlineKeyboardButton(text=f"{button_text} {emoji}", callback_data=f"select_button_{button_text}"))

    await callback_query.message.answer("Выберите кнопку для привязки изображения:", reply_markup=menu_kb.as_markup())


@router.callback_query(lambda c: c.data.startswith("select_button_"))
async def select_button_for_image(callback_query: CallbackQuery, state: FSMContext):
    button_text = callback_query.data.split("_")[2]

    await state.update_data(button_text=button_text)

    await callback_query.message.edit_text("Отправьте картинку для этой кнопки.")
    await state.set_state(MenuButtons.waiting_for_image)


@router.message(MenuButtons.waiting_for_image, F.photo)
async def save_image(message: Message, state: FSMContext):
    user_data = await state.get_data()
    file_id = message.photo[-1].file_id
    button_text = user_data['button_text']

    photo = await message.bot.get_file(file_id)

    photo_path = f'menu_photos/{button_text}-{file_id}.jpg'

    await message.bot.download_file(photo.file_path, photo_path)

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM menu_images WHERE button_text = ?", (button_text,))
    existing_image = cursor.fetchone()

    if existing_image:
        cursor.execute("UPDATE menu_images SET image_path = ? WHERE button_text = ?", (photo_path, button_text))
    else:
        cursor.execute("INSERT INTO menu_images (button_text, image_path) VALUES (?, ?)", (button_text, photo_path))

    conn.commit()
    conn.close()

    await message.answer(f"Картинка успешно добавлена для кнопки '{button_text}'!")

    await state.clear()

