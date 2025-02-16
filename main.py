import asyncio
import logging
import json
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from datetime import datetime

# --- Настройки ---
TOKEN = "Bot Token"
MODELS_FILE = "models.json"
PERSONS_FILE = "persons.json"
DATA_FOLDER = "data"  # Папка для хранения JSON-файлов

# --- Логирование ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# --- Инициализация бота ---
bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- Функции загрузки данных ---
def load_json(filename, default_value):
    """ Загружает JSON-файл, если он существует, иначе возвращает значение по умолчанию. """
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    return default_value

def save_json(filename, data):
    """ Сохраняет данные в JSON-файл. """
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# Загружаем данные из файлов
model_names = load_json(MODELS_FILE, ["Kira", "Stacey", "Ayrin"])
persons = load_json(PERSONS_FILE, {})

# --- Создание клавиатуры с model_name ---
def get_model_keyboard():
    """ Создает клавиатуру с кнопками model_name. """
    buttons = [KeyboardButton(text=name) for name in model_names]
    keyboard = ReplyKeyboardMarkup(keyboard=[buttons], resize_keyboard=True)
    return keyboard

# --- Обработчик команды /start ---
@dp.message(Command("start"))
async def start_handler(message: Message):
    await message.answer("Выберите модель из списка:", reply_markup=get_model_keyboard())

# --- Обработчик выбора model_name ---
@dp.message()
async def message_handler(message: Message):
    user_id = str(message.from_user.id)
    text = message.text.strip()

    # Проверяем, выбрал ли пользователь model_name
    if text in model_names:
        await message.answer(f"Вы выбрали: {text}\nОтправьте данные для обработки.")
        dp["selected_model"] = text  # Сохраняем выбранную модель
        return

    # Проверяем, был ли ранее выбран model_name
    model_name = dp.get("selected_model")
    if not model_name:
        await message.answer("Сначала выберите модель с помощью кнопок.")
        return

    # Парсим сообщение
    parts = text.split("  ")  # Разделяем по двойному пробелу
    if len(parts) < 5:
        await message.answer("Ошибка! Сообщение не соответствует формату.")
        return

    date, total_amount, fee, net_amount, description = parts[0], parts[1], parts[2], parts[3], parts[4]

    # Убираем символы $
    total_amount = total_amount.replace("$", "").strip()
    fee = fee.replace("$", "").strip()
    net_amount = net_amount.replace("$", "").strip()

    # Преобразуем ID пользователя в имя, если есть в persons.json
    person_name = persons.get(user_id, user_id)

    # Создаем JSON
    data = {
        "model_name": model_name,
        "date": date,
        "total_amount": total_amount,
        "fee": fee,
        "net_amount": net_amount,
        "description": description,
        "person": person_name
    }

    # Создаем папку, если её нет
    if not os.path.exists(DATA_FOLDER):
        os.makedirs(DATA_FOLDER)

    # Имя файла = model_name.json
    file_path = os.path.join(DATA_FOLDER, f"{model_name}.json")

    # Загружаем старые данные, если файл существует
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            old_data = json.load(f)
            if isinstance(old_data, list):
                old_data.append(data)
            else:
                old_data = [old_data, data]
    else:
        old_data = [data]

    # Сохраняем JSON
    save_json(file_path, old_data)

    # Подтверждаем сохранение
    await message.answer(f"✅ Данные сохранены в файл `{model_name}.json`")

# --- Запуск бота ---
async def main():
    logger.info("🚀 Бот запущен и ожидает сообщения...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
