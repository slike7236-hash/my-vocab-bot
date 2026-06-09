import sqlite3
import json

DB_NAME = "lms_system.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # 1. Foydalanuvchilar jadvali (Premium yoki bepul foydalanayotganini ajratadi)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            full_name TEXT,
            is_premium_user INTEGER DEFAULT 0,
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 2. Kitoblar jadvali (Masalan: Cambridge IELTS)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL DEFAULT 0.0
        )
    ''')
    
    # 3. Unitlar (Bo'limlar) jadvali (Masalan: Unit 1, Unit 2)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS units (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id INTEGER,
            name TEXT NOT NULL,
            is_premium INTEGER DEFAULT 1,
            FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE
        )
    ''')
    
    # 4. Mavzular va Web App (Wordwall) o'yinlari jadvali
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS themes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            unit_id INTEGER,
            name TEXT NOT NULL,
            content_text TEXT,
            video_url TEXT,
            key_words TEXT,
            game_flashcard TEXT,
            game_fill_gap TEXT,
            game_match TEXT,
            game_wheel TEXT,
            game_definition TEXT,
            is_premium INTEGER DEFAULT 1,
            FOREIGN KEY (unit_id) REFERENCES units(id) ON DELETE CASCADE
        )
    ''')
    
    # 5. Xarid qilingan kitoblar jadvali
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS purchases (
            user_id INTEGER,
            book_id INTEGER,
            PRIMARY KEY (user_id, book_id)
        )
    ''')
    
    conn.commit()
    
    # --- BAZAGA SINOV UCHUN "CAMBRIDGE IELTS" MA'LUMOTLARINI QO'SHISH ---
    cursor.execute("SELECT id FROM books WHERE name = 'Cambridge IELTS'")
    if not cursor.fetchone():
        # Kitob qo'shish
        cursor.execute("INSERT INTO books (name, price) VALUES ('Cambridge IELTS', 0.0)")
        book_id = cursor.lastrowid
        
        # Bepul sinov uchun Unit 1 qo'shish
        cursor.execute("INSERT INTO units (book_id, name, is_premium) VALUES (?, 'Unit 1', 0)", (book_id,))
        unit_id = cursor.lastrowid
        
        # Wordwall Web App uchun tayyor lug'at tarkibi
        sample_vocabulary = [
            {"en": "Develop", "uz": "rivojlantirmoq"},
            {"en": "Improve", "uz": "yaxshilamoq"},
            {"en": "Success", "uz": "muvaffaqiyat"},
            {"en": "Challenge", "uz": "qiyinchilik"},
            {"en": "Knowledge", "uz": "bilim"}
        ]
        
        # Mavzu va unga biriktirilgan Wordwall Web App o'yin havolalari
        cursor.execute("""
            INSERT INTO themes (
                unit_id, name, content_text, video_url, key_words,
                game_flashcard, game_fill_gap, game_match, game_wheel, game_definition, is_premium
            ) VALUES (?, 'Reading 1', ?, ?, ?, ?, ?, ?, ?, ?, 0)
        """, (
            unit_id,
            "How tennis rackets have changed\n\nIn 2016, the British professional tennis player Andy Murray...",
            "https://www.w3schools.com/html/mov_bbb.mp4",
            json.dumps(sample_vocabulary),
            "https://wordwall.net/embed/flashcard", # Flashcard Web App
            "https://wordwall.net/embed/fillgap",   # Fill in the gaps Web App
            "https://wordwall.net/embed/match",     # Match Web App
            "https://wordwall.net/embed/wheel",     # Wheel Web App
            "https://wordwall.net/embed/definition" # Definition Web App
        ))
        
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Ma'lumotlar bazasi muvaffaqiyatli yaratildi va sinov darslari yuklandi!")
