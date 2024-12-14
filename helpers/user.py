import logging
import os

from aiogram.types import FSInputFile


async def load_product_photo(photo_path: str) -> FSInputFile:
    try:
        logging.info(f"Попытка загрузить фото с пути: {photo_path}")

        absolute_path = os.path.join(photo_path)

        if os.path.exists(absolute_path):
            if os.path.getsize(absolute_path) > 0:
                logging.info(f"Фото найдено по пути: {absolute_path}")
                return FSInputFile(absolute_path)
            else:
                logging.error(f"Размер файла слишком мал или файл поврежден: {absolute_path}")
                raise FileNotFoundError(f"Фото с размером меньше допустимого или повреждено: {absolute_path}")
        else:
            logging.error(f"Фото не найдено по пути: {absolute_path}")
            raise FileNotFoundError(f"Фото не найдено: {absolute_path}")

    except Exception as e:
        logging.error(f"Ошибка при загрузке фото: {str(e)}")
        raise e