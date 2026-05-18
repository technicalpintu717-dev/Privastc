import sqlite3
import json

DB_PATH = "mailer.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        chat_id INTEGER PRIMARY KEY,
        accounts TEXT,
        target TEXT,
        subject TEXT,
        body TEXT,
        running INTEGER DEFAULT 0
    )''')
    conn.commit()
    conn.close()
    print("✅ Database initialized")

def save_user_data(chat_id, data):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''INSERT OR REPLACE INTO users 
        (chat_id, accounts, target, subject, body, running)
        VALUES (?, ?, ?, ?, ?, ?)''',
        (chat_id, json.dumps(data['accounts']), data.get('target'), 
         data.get('subj'), data.get('body'), 1 if data.get('running') else 0))
    conn.commit()
    conn.close()

def load_user_data(chat_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT accounts, target, subject, body, running FROM users WHERE chat_id = ?', (chat_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return {
            'accounts': json.loads(row[0]),
            'target': row[1],
            'subj': row[2],
            'body': row[3],
            'running': bool(row[4])
        }
    return None

def load_all_users():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT chat_id FROM users')
    rows = c.fetchall()
    conn.close()
    return [row[0] for row in rows]
