import asyncio
import logging
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from telethon import TelegramClient

# Настройки
TOKEN = "8126215351:AAGOeoRejXzVOYk5n1R1BBOOevz4fbZHm9E"  # Укажите свой токен
API_ID = "27128533"
API_HASH = "98e674b2f11b7a6f1ca10a5e1595cc44"

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
            await tg_client.connect()  # Обеспечиваем соединение
            user = await tg_client.get_entity(username)
            return str(user.id)
        except Exception as e:
            logging.warning(f"Ошибка при получении ID для {username}: {e}")
            return None
        finally:
            if tg_client.is_connected():
                await tg_client.disconnect()  # Отключаемся после использования

def check_user_folder(tg_id):
    """Проверка наличия данных на двух источниках"""
    urls = [f"{BASE_URL}{tg_id}", f"{RESERVE_URL}{tg_id}"]
    results = []
    
    for url in urls:
        retries = 3
        for _ in range(retries):
            try:
                response = requests.head(url)
                if response.status_code != 404:
                    results.append(url)
                break  # Если успешно, выходим из цикла
            except requests.RequestException as e:
                logging.warning(f"Ошибка при проверке {url}: {e}")
                time.sleep(2)  # Задержка перед повторной попыткой
                    
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
        keyboard = InlineKeyboardMarkup(inline_keyboard=[])

        for folder in existing_folders:
            text += f"🔗 [{folder}]({folder})\n"
            keyboard.inline_keyboard.append([InlineKeyboardButton(text="📂 Открыть", url=folder)])

        return text, keyboard if keyboard.inline_keyboard else None
    
    return f"⚠️ *{username}* (ID: `{tg_id}`) - _данные не найдены_", None


async def send_welcome(message: Message):
    """Обработчик команды /start"""
    await message.answer("👋 *Привет!*\nОтправь мне username (или список в столбик), и я проверю их наличие.")

async def handle_usernames(message: Message):
    """Обрабатывает введённые username"""
    usernames = message.text.split("\n")  # Разделяем список

    results = []
    # Обрабатываем пользователей по очереди
    for username in usernames:
        if username.strip():
            result = await process_user(username)
            if isinstance(result, tuple):
                text, keyboard = result
                results.append(f"{text}\n")
            else:
                results.append(result + "\n")
    
    # Отправляем общий результат
    await message.answer("\n".join(results), parse_mode="Markdown")


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
