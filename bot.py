import asyncio
import logging
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

# Включаем логирование
logging.basicConfig(level=logging.INFO)


BOT_TOKEN = '8733679614:AAHqsEDL7_EGfEdd-fpiFhn80QksDg2np0s'
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# В реальном проекте используйте базу данных (PostgreSQL/SQLite).
# Для примера храним стоп-слова в оперативной памяти: {user_id: [список_слов]}
USER_KEYWORDS = {}

# Состояния для ввода ключевых слов
class SpoilerStates(StatesGroup):
    waiting_for_keywords = State()


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 Привет! Я бот-антиспойлер.\n\n"
        "Используй команду /add, чтобы добавить ключевые слова (названия сериалов, имена персонажей, "
        "которые ты не хочешь случайно увидеть).\n"
        "Если я замечу эти слова в сообщениях, я скрою их под специальный блюр-фильтр!" \
        "Используй команду /list чтобы посмотреть список ключевых слов." \
        "Используй команду /clear чтобы очистить список ключевых слов." \
        "Приятного пользования!"
    )


@dp.message(Command("add"))
async def cmd_add(message: types.Message, state: FSMContext):
    await message.answer("Введите ключевые слова через запятую (например: <i>Братья, Джон Сноу, финал</i>):")
    await state.set_state(SpoilerStates.waiting_for_keywords)


@dp.message(SpoilerStates.waiting_for_keywords)
async def process_keywords(message: types.Message, state: FSMContext):
    user_id = message.from_user.id

    keywords = [word.strip().lower() for word in message.text.split(",") if word.strip()]
    
    if not keywords:
        await message.answer("Пожалуйста, введите хотя бы одно валидное слово.")
        return

    if user_id not in USER_KEYWORDS:
        USER_KEYWORDS[user_id] = []
    
    USER_KEYWORDS[user_id].extend(keywords)

    USER_KEYWORDS[user_id] = list(set(USER_KEYWORDS[user_id]))
    
    await state.clear()
    await message.answer(
        f"✅ Успешно добавлено слов: {len(keywords)}.\n"
        f"Ваш текущий список: {', '.join(USER_KEYWORDS[user_id])}"
    )


@dp.message(Command("list"))
async def cmd_list(message: types.Message):
    user_id = message.from_user.id
    keywords = USER_KEYWORDS.get(user_id, [])
    if not keywords:
        await message.answer("Ваш список стоп-слов пока пуст. Используйте /add")
    else:
        await message.answer(f"📋 Ваши стоп-слова: {', '.join(keywords)}")


@dp.message(Command("clear"))
async def cmd_clear(message: types.Message):
    user_id = message.from_user.id
    USER_KEYWORDS[user_id] = []
    await message.answer("🗑 Ваш список стоп-слов полностью очищен.")


@dp.message(F.text)
async def check_spoilers(message: types.Message):
    user_id = message.from_user.id
    text_lower = message.text.lower()
    

    keywords = USER_KEYWORDS.get(user_id, [])
    

    contains_spoiler = any(word in text_lower for word in keywords)
    
    if contains_spoiler:

        try:
            await message.delete()
        except Exception as e:
            logging.error(f"Не удалось удалить сообщение: {e}")



        await message.answer(
            f"⚠️ <b>Внимание, обнаружен спойлер от @{message.from_user.username}!</b>\n\n"
            f"<tg-spoiler>{message.text}</tg-spoiler>\n\n"
            f"<i>Нажмите на текст выше, чтобы открыть его на свой страх и риск.</i>"
        )


async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
