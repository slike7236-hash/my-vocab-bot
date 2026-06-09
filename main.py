import os
import logging
from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message
import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager

# Ma'lumotlar bazasini majburiy ulash (Siz boya yaratgan fayl)
from database import init_db

# Bot sozlamalari (Tokeningizni Railway Environment Variables'dan oladi)
TOKEN = os.getenv("BOT_TOKEN", "8948766026:AAHs9HWcPVzzdFzTsUAFOMKiVfxzwU-bdmA")

# Logging (Xatoliklarni ko'rib turish uchun)
logging.basicConfig(level=logging.INFO)

# Baza jadvalini bot o'qilishidan oldin yaratish
init_db()

# Aiogram va FastAPI ni sozlash
dp = Dispatcher()
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
app = FastAPI()

@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """ /start buyrug'i berilganda foydalanuvchini kutib olish """
    await message.answer(f"Salom, {html.bold(message.from_user.full_name)}!\n'My Vocabularies' botiga xush kelibsiz!")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Botni ishga tushirish (Polling)
    logging.info("Bot ishga tushmoqda...")
    import asyncio
    asyncio.create_task(dp.start_polling(bot))
    yield
    # Botni to'xtatish
    await bot.session.close()

# FastAPI ni lifespan bilan yangilash
app = FastAPI(lifespan=lifespan)

@app.get("/")
async def root():
    return {"status": "Bot is running"}

if __name__ == "__main__":
    # Railway 8080 portida uvicorn serverini yurgizadi
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
