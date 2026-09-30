import sqlite3

connection = sqlite3.connect('SQLite.db')
cursor = connection.cursor()

cursor.execute("""CREATE TABLE IF NOT EXISTS comments (
id INTEGER PRIMARY KEY AUTOINCREMENT,
post_id INTEGER NOT NULL,
user_id INTEGER NOT NULL,
comment TEXT NOT NULL,
FOREIGN KEY (post_id) REFERENCES post(id),
FOREIGN KEY (user_id) REFERENCES user(id)
)
    """)

connection.commit()
connection.close()
