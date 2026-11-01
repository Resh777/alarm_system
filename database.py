import sqlite3
from datetime import datetime

DB_NAME = 'alarms.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS alarms (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 title TEXT,
                 time TEXT,
                 priority INTEGER,
                 condition TEXT,
                 status TEXT DEFAULT 'pending')''')
    c.execute('''CREATE TABLE IF NOT EXISTS logs (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 alarm_id INTEGER,
                 timestamp TEXT,
                 action TEXT)''')
    conn.commit()
    conn.close()

def add_alarm(title, time_str, priority, condition=None):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO alarms (title, time, priority, condition) VALUES (?, ?, ?, ?)",
              (title, time_str, priority, condition))
    conn.commit()
    conn.close()

def get_pending_alarms():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, title, time, priority, condition FROM alarms WHERE status='pending'")
    alarms = c.fetchall()
    conn.close()
    return alarms

def update_alarm_status(alarm_id, status):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE alarms SET status=? WHERE id=?", (status, alarm_id))
    conn.commit()
    conn.close()

def log_action(alarm_id, action):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO logs (alarm_id, timestamp, action) VALUES (?, ?, ?)",
              (alarm_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), action))
    conn.commit()
    conn.close()
def get_connection():
    # Adding a 10 second timeout helps prevent crashes during simultaneous access
    return sqlite3.connect(DB_NAME, timeout=10)