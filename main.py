
import asyncio
import logging
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from telethon import TelegramClient

# Настройки
TOKEN = "8126215351:AAGOeoRejXzVOYk5n1R1BBOOevz4fbZHm9E" # 🔴 Укажите свой токен бота
API_ID = "22027112"
API_HASH = "b5a2066fdf4618c019aa8e0ac7912b2c"

BASE_URL = "https://fakedocs.online/"
RESERVE_URL = "https://fakedocs.online/rezerv/"

# Включаем логирование
logging.basicConfig(level=logging.INFO)

# Создаём объект бота и диспетчер
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Инициализируем Telethon-клиент (для получения Telegram ID)
tg_client = TelegramClient('session', API_ID, API_HASH)

async def get_telegram_id(username):
    """Преобразование username в Telegram ID"""
    async with tg_client:
        try:
            user = await tg_client.get_entity(username)
            return str(user.id)
        except Exception as e:
            logging.warning(f"Ошибка при получении ID для {username}: {e}")
            return None

def check_user_folder(tg_id):
    """Проверка наличия данных на двух источниках"""
    urls = [f"{BASE_URL}{tg_id}", f"{RESERVE_URL}{tg_id}"]
    results = []
    
    for url in urls:
        try:
            response = requests.head(url)
            if response.status_code != 404:
                results.append(url)
        except requests.RequestException as e:
            logging.warning(f"Ошибка при проверке {url}: {e}")

    return results

async def process_user(username):
    """Обрабатывает одного пользователя"""
    username = username.strip().replace('@', '')
    tg_id = await get_telegram_id(f"@{username}")

    if not tg_id:
        return f"❌ *{username}* - _не найден или ошибка ID_"

    existing_folders = check_user_folder(tg_id)
    
    if existing_folders:
        text = f"✅ *{username}* (ID: `{tg_id}`) найден:\n"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[])  # Пустая клавиатура

        for folder in existing_folders:
            text += f"🔗 [{folder}]({folder})\n"
            keyboard.inline_keyboard.append([InlineKeyboardButton(text="📂 Открыть", url=folder)])

        return text, keyboard if keyboard.inline_keyboard else None  # Проверка, есть ли кнопки
    
    return f"⚠️ *{username}* (ID: `{tg_id}`) - _данные не найдены_", None


async def send_welcome(message: Message):
    """Обработчик команды /start"""
    await message.answer("👋 *Привет!*\nОтправь мне username (или список в столбик), и я проверю их наличие.")

async def handle_usernames(message: Message):
    """Обрабатывает введённые username"""
    usernames = message.text.split("\n")  # Разделяем список

    tasks = [process_user(username) for username in usernames if username.strip()]
    results = await asyncio.gather(*tasks)  # Выполняем все запросы одновременно

    for result in results:
        if isinstance(result, tuple):
            text, keyboard = result
            await message.answer(text, parse_mode="Markdown", reply_markup=keyboard)
        else:
            await message.answer(result, parse_mode="Markdown")

async def main():
    """Запуск бота"""
    await tg_client.start()  # Запуск Telethon-клиента

    # Регистрация обработчиков (aiogram 3.x)
    dp.message.register(send_welcome, Command("start", "help"))
    dp.message.register(handle_usernames)

    # Запуск бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
