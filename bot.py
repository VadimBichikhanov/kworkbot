import asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import Message
import logging
import aiohttp
import aiosqlite
from os import getenv

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Получение переменных окружения и конфигурации
TELEGRAM_TOKEN = getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = getenv('TELEGRAM_CHAT_ID')
API_URL = getenv('API_URL')

# Проверка наличия переменных окружения и конфигурации
if not all([TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, API_URL]):
    logger.error("Одна или несколько переменных окружения или конфигурации не установлены.")
    exit(1)

# Инициализация бота и диспетчера
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher(bot)

async def init_db():
    """Инициализация базы данных."""
    async with aiosqlite.connect('requests.db') as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS requests (
                id INTEGER PRIMARY KEY,
                name TEXT,
                contact TEXT,
                text TEXT,
                datetime TEXT
            )
        ''')
        await db.commit()

async def get_new_requests():
    """Получение новых заявок с API сайта."""
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(API_URL) as response:
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientError as e:
            logger.error(f"Ошибка при получении заявок: {e}")
            return []

async def send_request_to_telegram(request):
    """Отправка заявки в Telegram."""
    try:
        message = (
            f"Новая заявка:\n"
            f"Имя: {request['name']}\n"
            f"Контактные данные: {request['contact']}\n"
            f"Текст заявки: {request['text']}\n"
            f"Дата и время: {request['datetime']}"
        )
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logger.info(f"Заявка отправлена в Telegram: {request['id']}")
    except Exception as e:
        logger.error(f"Ошибка при отправке заявки в Telegram: {e}")

async def save_request_to_db(request):
    """Сохранение заявки в базу данных."""
    async with aiosqlite.connect('requests.db') as db:
        await db.execute('''
            INSERT INTO requests (id, name, contact, text, datetime)
            VALUES (?, ?, ?, ?, ?)
        ''', (request['id'], request['name'], request['contact'], request['text'], request['datetime']))
        await db.commit()

async def is_request_sent(request_id):
    """Проверка, была ли заявка уже отправлена."""
    async with aiosqlite.connect('requests.db') as db:
        cursor = await db.execute('SELECT id FROM requests WHERE id = ?', (request_id,))
        row = await cursor.fetchone()
        return row is not None

@dp.message(commands=['start'])
async def start_command(message: Message):
    """Обработчик команды /start."""
    await message.reply("Привет! Я бот, который отправляет новые заявки в этот чат.")

async def main():
    """Основная асинхронная функция для получения и отправки заявок."""
    logger.info("Запуск бота...")
    await init_db()
    while True:
        requests = await get_new_requests()
        for request in requests:
            if not await is_request_sent(request['id']):
                await send_request_to_telegram(request)
                await save_request_to_db(request)
        # Пауза перед следующей проверкой
        await asyncio.sleep(5)

async def start_bot():
    """Запуск диспетчера и основной функции параллельно."""
    await dp.start_polling(bot)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(start_bot())
    loop.create_task(main())
    loop.run_forever()