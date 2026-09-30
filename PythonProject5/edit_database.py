import sqlite3
from werkzeug.security import generate_password_hash

connection = sqlite3.connect("SQLite.db", check_same_thread=False)
cursor = connection.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL
)
""")

try:
    cursor.execute("ALTER TABLE user ADD COLUMN email text")
except sqlite3.OperationalError:
    print("email already exists")

try:
    cursor.execute("ALTER TABLE post ADD COLUMN author_id INTEGER")
except sqlite3.OperationalError:
    print("author_id already exists")

cursor.execute("""
INSERT OR IGNORE INTO user (id, username, password_hash)
VALUES (?, ?, ?)
""", (1, "Rocket", generate_password_hash("qwerty123")))

cursor.execute("UPDATE user SET email = ? WHERE username = ?", ("rocket@example.com", "Rocket"))
cursor.execute("UPDATE post SET author_id = 1 WHERE author_id IS NULL")

connection.commit()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
print(cursor.fetchall())

connection.close()

print("Database fixed successfully")