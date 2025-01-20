# main.py
from aiogram import Bot, Dispatcher, types, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command, CommandStart
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import aiosqlite
import asyncio
import logging
import advice
import chat

# Логирование
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
TOKEN = "TOKEN"
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())

message_history = []

# FSM для регистрации
class RegistrationForm(StatesGroup):
    name = State()

@dp.message(Command(commands=["menu"]))
async def menu_command(message: types.Message):
    await message.answer(
        "Привет! Выберите действие из меню ниже:",
        reply_markup=main_menu()
    )

# Состояние для диалога
class ChatState(StatesGroup):
    chatting = State()

# Команда /chat
@dp.message(Command(commands=["chat"]))
async def start_chat(message: types.Message, state: FSMContext):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Стоп")]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await state.set_state(ChatState.chatting)
    message_history = []
    await message.answer(
        "Диалог начался! Напишите что-нибудь. Для завершения нажмите 'Стоп' или введите /stop.",
        reply_markup=keyboard
    )

# Завершение чата (команда /stop или кнопка "Стоп")
@dp.message(F.text == "Стоп")
@dp.message(Command(commands=["stop"]))
async def stop_chat(message: types.Message, state: FSMContext):
    if await state.get_state() == ChatState.chatting.state:
        await state.clear()
        await message.answer(
            "Диалог завершен. Возвращаю основное меню.",
            reply_markup=main_menu()
        )
    else:
        await message.answer("Вы не находитесь в режиме диалога.")

# Основное меню
def main_menu():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📰 Последние статьи"), KeyboardButton(text="📍 Сортировка мусора")],
            [KeyboardButton(text="💡 Советы"), KeyboardButton(text="🌱 Очки утилизации")],
        ],
        resize_keyboard=True
    )
    return keyboard


# Inline клавиатура для статей
def articles_inline_keyboard():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Последние статьи", url="https://aif.ru/tag/plastik")]
        ]
    )
    return keyboard


# Создание базы данных
async def init_db():
    async with aiosqlite.connect("users.db") as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            name TEXT,
            points INTEGER DEFAULT 0
        )
        """)
        await db.commit()


# Проверка регистрации пользователя
async def is_user_registered(user_id: int) -> bool:
    async with aiosqlite.connect("users.db") as db:
        async with db.execute("SELECT 1 FROM users WHERE id = ?", (user_id,)) as cursor:
            return await cursor.fetchone() is not None


# Регистрация пользователя
@dp.message(CommandStart())
async def start_command(message: types.Message, state: FSMContext):
    if await is_user_registered(message.from_user.id):
        await message.answer("Вы уже зарегистрированы!", reply_markup=main_menu())

    else:
        await message.answer("Добро пожаловать! Как вас зовут?", reply_markup=types.ReplyKeyboardRemove())
        await state.set_state(RegistrationForm.name)

# FSM: ввод имени
@dp.message(RegistrationForm.name)
async def process_name(message: types.Message, state: FSMContext):
    async with aiosqlite.connect("users.db") as db:
        await db.execute(
            "INSERT INTO users (id, name, points) VALUES (?, ?, ?)",
            (message.from_user.id, message.text, 0)
        )
        await db.commit()
    await message.answer(
        f"Спасибо за регистрацию, {message.text}! Используйте меню ниже для взаимодействия.",
        reply_markup=main_menu()
    )
    await state.clear()


# Обработка команды для статей
@dp.message(F.text == "📰 Последние статьи")
async def send_articles(message: types.Message):
    await message.answer(
        "Вот последние статьи о вреде пластика:", 
        reply_markup=articles_inline_keyboard()
    )


# Обработка команды для сортировки мусора
@dp.message(F.text == "📍 Сортировка мусора")
async def sorting_info(message: types.Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Карта сортировки", url="https://recyclemap.ru/")]
        ]
    )
    await message.answer(
        "Вы можете найти ближайшие пункты сортировки мусора на этой карте:", 
        reply_markup=keyboard
    )


# Обработка команды для советов
@dp.message(F.text == "💡 Советы")
async def eco_tips(message: types.Message):
    await message.answer(f"Совет: {advice.advice()}")


# Inline клавиатура для очков
def points_inline_keyboard():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Количество очков", callback_data="check_points")],
            [InlineKeyboardButton(text="Получить очки", callback_data="earn_points")],
        ]
    )
    return keyboard


# Обработка команды "🌱 Очки утилизации"
@dp.message(F.text == "🌱 Очки утилизации")
async def handle_points_button(message: types.Message):
    await message.answer("Выберите действие:", reply_markup=points_inline_keyboard())


# Обработчик для кнопки "Количество очков"
@dp.callback_query(F.data == "check_points")
async def check_points(callback: types.CallbackQuery):
    async with aiosqlite.connect("users.db") as db:
        async with db.execute("SELECT points FROM users WHERE id = ?", (callback.from_user.id,)) as cursor:
            row = await cursor.fetchone()
            if row: 
                points = row[0]
                await callback.message.answer(f"У вас {points} очков утилизации!")

            else:
                await callback.message.answer("Вы не зарегистрированы! пропишите /start")
    await callback.answer()  # Закрыть всплывающее уведомление


# Обработчик для кнопки "Получить очки"
@dp.callback_query(F.data == "earn_points")
async def earn_points(callback: types.CallbackQuery):
    async with aiosqlite.connect("users.db") as db:
        async with db.execute("SELECT points FROM users WHERE id = ?", (callback.from_user.id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                current_points = row[0]
                new_points = current_points + 10  # Начисление очков
                await db.execute("UPDATE users SET points = ? WHERE id = ?", (new_points, callback.from_user.id))
                await db.commit()
                await callback.message.answer(f"Вам начислено 10 очков! Теперь у вас {new_points} очков. \n не забывайте, очки - лишь мотивация \n для помощи планете!")

            else:
                await callback.message.answer("Вы не зарегистрированы! пропишите /start")
    await callback.answer()  # Закрыть всплывающее уведомление


# Планировщик напоминаний
async def send_reminders():
    async with aiosqlite.connect("users.db") as db:
        async with db.execute("SELECT id FROM users") as cursor:
            async for row in cursor:
                await bot.send_message(row[0], "Напоминание: Сократите использование пластика и сортируйте мусор!")


@dp.message(F.text)
async def unknown_message(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state == ChatState.chatting.state:
        # Если пользователь в режиме чата
        user_message = message.text

        message_history.append({"role": "user", "content": user_message})
        bot_answer = chat.chat(message_history)
        message_history.append({"role": "assistant", "content": bot_answer})

        await message.answer(bot_answer)

    else:
        # Если пользователь не в режиме чата
        await message.answer(
            "Извините, я не понимаю этот запрос. Попробуйте воспользоваться командой из меню или выберите кнопку.",
            reply_markup=main_menu()
        )


async def main():
    # Инициализация БД
    await init_db()

    # Настройка планировщика
    scheduler = AsyncIOScheduler()
    scheduler.add_job(send_reminders, "interval", hours=6)
    scheduler.start()

    # Запуск бота
    print("Бот запущен...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
