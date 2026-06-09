import os
import logging
import sqlite3
import json
from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, WebAppInfo
import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager

# database.py faylimizdan bazani ulash
from database import init_db, DB_NAME

# ⚠️ O'ZINGIZNING HAQIQIY TELEGRAM BOT TOKENINGIZNI SHU YERGA QO'YING ⚠️
TOKEN = "BU_YERGA_O'Z_TOKENINGIZNI_QO'YING"

logging.basicConfig(level=logging.INFO)

# Bot ishga tushishidan oldin bazani tekshirish/yaratish
init_db()

dp = Dispatcher()
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

# --- YORDAMCHI FUNKSIYALAR (BAZA BILAN ISHLASH) ---
def get_books():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM books")
    books = cursor.fetchall()
    conn.close()
    return books

def get_units(book_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM units WHERE book_id = ?", (book_id,))
    units = cursor.fetchall()
    conn.close()
    return units

def get_themes(unit_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM themes WHERE unit_id = ?", (unit_id,))
    themes = cursor.fetchall()
    conn.close()
    return themes

def get_theme_details(theme_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT name, content_text, video_url, key_words, 
               game_flashcard, game_fill_gap, game_match, game_wheel, game_definition 
        FROM themes WHERE id = ?
    """, (theme_id,))
    row = cursor.fetchone()
    conn.close()
    return row

# --- BOT COMMANDS & HANDLERS ---

# /start bosilganda kutib olish va Kitoblarni chiqarish
@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    # Foydalanuvchini bazaga qo'shib qo'yish (yoki yangilash)
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO users (user_id, username, full_name) 
        VALUES (?, ?, ?) 
        ON CONFLICT(user_id) DO UPDATE SET full_name=excluded.full_name
    """, (message.from_user.id, message.from_user.username, message.from_user.full_name))
    conn.commit()
    conn.close()

    welcome_text = (
        f"👋 Salom, {html.bold(message.from_user.full_name)}!\n\n"
        f"📚 {html.italic('LMS Vocabulary & WebApp Platformasiga')} xush kelibsiz!\n"
        f"Quyidagi ro'yxatdan o'zingizga kerakli darslikni tanlang:"
    )
    
    # Kitoblarni tugma qilib chiqarish
    books = get_books()
    keyboard_buttons = []
    for b_id, b_name in books:
        keyboard_buttons.append([InlineKeyboardButton(text=f"📘 {b_name}", callback_data=f"book_{b_id}")])
        
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    await message.answer(welcome_text, reply_markup=reply_markup)

# Kitob tanlanganda Unitlarni chiqarish
@dp.callbackQuery(lambda c: c.data.startswith('book_'))
async def process_book_select(callback_query: CallbackQuery):
    book_id = int(callback_query.data.split('_')[1])
    units = get_units(book_id)
    
    keyboard_buttons = []
    for u_id, u_name in units:
        keyboard_buttons.append([InlineKeyboardButton(text=f"📂 {u_name}", callback_data=f"unit_{u_id}")])
    
    # Orqaga qaytish tugmasi
    keyboard_buttons.append([InlineKeyboardButton(text="⬅️ Bosh sahifa", callback_data="back_to_books")])
    
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    await callback_query.message.edit_text(text="🎯 Bo'limni (Unit) tanlang:", reply_markup=reply_markup)

# Unit tanlanganda Mavzularni (Themes/Readings) chiqarish
@dp.callbackQuery(lambda c: c.data.startswith('unit_'))
async def process_unit_select(callback_query: CallbackQuery):
    unit_id = int(callback_query.data.split('_')[1])
    themes = get_themes(unit_id)
    
    keyboard_buttons = []
    for t_id, t_name in themes:
        keyboard_buttons.append([InlineKeyboardButton(text=f"📝 {t_name}", callback_data=f"theme_{t_id}")])
        
    keyboard_buttons.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="back_to_books")])
    
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    await callback_query.message.edit_text(text="📖 Mavzuni tanlang:", reply_markup=reply_markup)

# Mavzu tanlanganda ichidagi matn va Wordwall Web App o'yin tugmalarini ko'rsatish
@dp.callbackQuery(lambda c: c.data.startswith('theme_'))
async def process_theme_select(callback_query: CallbackQuery):
    theme_id = int(callback_query.data.split('_')[1])
    theme = get_theme_details(theme_id)
    
    if not theme:
        await callback_query.answer("Mavzu topilmadi!")
        return
        
    t_name, content_text, video_url, key_words, f_card, f_gap, match, wheel, definition = theme
    
    # Telegram ekranida dars kontentini ko'rsatish
    page_text = f"🎯 {html.bold(t_name)}\n\n{content_text}\n\n🎬 Video darslik havolasi: {video_url}"
    
    # Web App tugmalarini yaratish (Wordwall o'yinlari to'g'ridan-to'g'ri Telegramda ochiladi)
    keyboard_buttons = []
    if f_card:
        keyboard_buttons.append([InlineKeyboardButton(text="🎮 O'yin: Flashcards (Web App)", web_app=WebAppInfo(url=f_card))])
    if f_gap:
        keyboard_buttons.append([InlineKeyboardButton(text="🎮 O'yin: Fill Gaps (Web App)", web_app=WebAppInfo(url=f_gap))])
    if match:
        keyboard_buttons.append([InlineKeyboardButton(text="🎮 O'yin: Match Words (Web App)", web_app=WebAppInfo(url=match))])
        
    keyboard_buttons.append([InlineKeyboardButton(text="⬅️ Mavzular ro'yxatiga qaytish", callback_data="back_to_books")])
    
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    await callback_query.message.answer(page_text, reply_markup=reply_markup)
    await callback_query.answer()

# Bosh sahifaga qaytish handlerlari
@dp.callbackQuery(lambda c: c.data == 'back_to_books')
async def back_to_start(callback_query: CallbackQuery):
    books = get_books()
    keyboard_buttons = []
    for b_id, b_name in books:
        keyboard_buttons.append([InlineKeyboardButton(text=f"📘 {b_name}", callback_data=f"book_{b_id}")])
        
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    await callback_query.message.edit_text(text="📚 Kitoblar ro'yxati:", reply_markup=reply_markup)

# --- FASTAPI & LIFESPAN (RAILWAY UCHUN DOIMIYLIK) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.info("Bot ishga tushmoqda...")
    import asyncio
    asyncio.create_task(dp.start_polling(bot))
    yield
    await bot.session.close()

app = FastAPI(lifespan=lifespan)

@app.get("/")
async def root():
    return {"status": "LMS Bot is running successfully"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
