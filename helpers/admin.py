from database.admin.admin import get_all_admins
import os


def create_photo_folder():
    if not os.path.exists("C:/Users/G5/PycharmProjects/white_bot/"):
        os.makedirs('product_photos')


async def is_admin(tg_id: int):
    admins = get_all_admins()
    return any(admin[1] == tg_id for admin in admins)