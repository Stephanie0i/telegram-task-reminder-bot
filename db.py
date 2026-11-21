import sqlite3

DB_FILE = "bot.db"

def connect():
    return sqlite3.connect(DB_FILE)

def init_db():
    conn = connect()
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, task TEXT, status TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS users (user_id TEXT PRIMARY KEY, remind_time TEXT, ai_date TEXT, ai_count INTEGER DEFAULT 0)")
    conn.commit()
    conn.close()

def add_task(user_id, task):
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT id FROM tasks WHERE user_id = ? AND task = ? AND status = ?", (user_id, task, "todo"))
    if cur.fetchone() is not None:
        conn.close()
        return False
    cur.execute("INSERT INTO tasks (user_id, task, status) VALUES (?, ?, ?)", (user_id, task, "todo"))
    conn.commit()
    conn.close()
    return True

def get_tasks(user_id, status):
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT id, task FROM tasks WHERE user_id = ? AND status = ?", (user_id, status))
    rows = cur.fetchall()
    conn.close()
    return rows

def mark_done(user_id, task):
    conn = connect()
    cur = conn.cursor()
    cur.execute("UPDATE tasks SET status = ? WHERE user_id = ? AND task = ? AND status = ?", ("done", user_id, task, "todo"))
    conn.commit()
    changed = cur.rowcount
    conn.close()
    return changed > 0

def remove_task(user_id, task):
    conn = connect()
    cur = conn.cursor()
    cur.execute("DELETE FROM tasks WHERE user_id = ? AND task = ?", (user_id, task))
    conn.commit()
    changed = cur.rowcount
    conn.close()
    return changed > 0

def count_tasks(user_id, status):
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM tasks WHERE user_id = ? AND status = ?", (user_id, status))
    number = cur.fetchone()[0]
    conn.close()
    return number

def mark_done_by_id(user_id, task_id):
    conn = connect()
    cur = conn.cursor()
    cur.execute("UPDATE tasks SET status = ? WHERE id = ? AND user_id = ? AND status = ?", ("done", task_id, user_id, "todo"))
    conn.commit()
    changed = cur.rowcount
    conn.close()
    return changed > 0

def remove_by_id(user_id, task_id):
    conn = connect()
    cur = conn.cursor()
    cur.execute("DELETE FROM tasks WHERE id = ? AND user_id = ?", (task_id, user_id))
    conn.commit()
    changed = cur.rowcount
    conn.close()
    return changed > 0

def ensure_user(cur, user_id):
    cur.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))

def set_reminder(user_id, remind_time):
    conn = connect()
    cur = conn.cursor()
    ensure_user(cur, user_id)
    cur.execute("UPDATE users SET remind_time = ? WHERE user_id = ?", (remind_time, user_id))
    conn.commit()
    conn.close()

def get_reminders():
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT user_id, remind_time FROM users WHERE remind_time IS NOT NULL")
    rows = cur.fetchall()
    conn.close()
    return rows

def use_ai(user_id, limit, today):
    conn = connect()
    cur = conn.cursor()
    ensure_user(cur, user_id)
    cur.execute("SELECT ai_date, ai_count FROM users WHERE user_id = ?", (user_id,))
    ai_date, ai_count = cur.fetchone()
    if ai_date != today:
        ai_count = 0
    if ai_count >= limit:
        conn.close()
        return False
    cur.execute("UPDATE users SET ai_date = ?, ai_count = ? WHERE user_id = ?", (today, ai_count + 1, user_id))
    conn.commit()
    conn.close()
    return True
