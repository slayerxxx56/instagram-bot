#!/usr/bin/env python3
"""
Instagram Auto Welcome Bot
"""

from instagrapi import Client
import sqlite3
from datetime import date
import time
import os
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

WELCOME_TEMPLATE = "@{username} انزع اريد اشوف اغراضك يا ورد🙈🎀"
DB_FILE = "welcome_state.db"
CHECK_DELAY = 30

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS welcomes (
            user_id TEXT,
            thread_id TEXT,
            day TEXT,
            PRIMARY KEY (user_id, thread_id, day)
        )
    """)
    conn.commit()
    conn.close()
    logger.info("✅ تم تهيئة قاعدة البيانات")

def already_welcomed(user_id, thread_id):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute(
        "SELECT 1 FROM welcomes WHERE user_id=? AND thread_id=? AND day=?",
        (user_id, thread_id, date.today().isoformat())
    )
    row = cur.fetchone()
    conn.close()
    return row is not None

def mark_welcomed(user_id, thread_id):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute(
        "INSERT OR IGNORE INTO welcomes (user_id, thread_id, day) VALUES (?, ?, ?)",
        (user_id, thread_id, date.today().isoformat())
    )
    conn.commit()
    conn.close()
    logger.info(f"✅ تم تسجيل الترحيب بالمستخدم {user_id}")

def main():
    logger.info("🚀 بدء تشغيل بوت الترحيب...")
    
    init_db()
    
    cl = Client()
    
    try:
        logger.info("🔐 جاري تسجيل الدخول...")
        username = os.getenv('INSTAGRAM_USERNAME')
        password = os.getenv('INSTAGRAM_PASSWORD')
        
        if username and password:
            cl.login(username, password)
        else:
            cl.login("test", "test")
        
        logger.info("✅ تم تسجيل الدخول بنجاح!")
    except Exception as e:
        logger.error(f"❌ فشل تسجيل الدخول: {e}")
        return
    
    last_seen = {}
    
    while True:
        try:
            threads = cl.direct_threads(amount=20)
            
            for thread in threads:
                if not thread.is_group:
                    continue
                
                thread_id = thread.id
                messages = cl.direct_messages(thread_id, amount=20)
                messages = list(reversed(messages))
                
                for msg in messages:
                    if thread_id in last_seen and msg.id <= last_seen[thread_id]:
                        continue
                    
                    user_id = str(msg.user_id)
                    username = msg.user.username
                    
                    if not already_welcomed(user_id, thread_id):
                        text = WELCOME_TEMPLATE.format(username=username)
                        logger.info(f"👋 جاري الترحيب بـ @{username}")
                        cl.direct_send(text, thread_ids=[thread_id])
                        mark_welcomed(user_id, thread_id)
                    
                    last_seen[thread_id] = msg.id
            
            time.sleep(CHECK_DELAY)
            
        except Exception as e:
            logger.error(f"❌ حدث خطأ: {e}")
            time.sleep(CHECK_DELAY)

if __name__ == "__main__":
    main()
