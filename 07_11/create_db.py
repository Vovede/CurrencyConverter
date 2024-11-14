import sqlite3

conn = sqlite3.connect('bd.db')
cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS history 
        (ID INTEGER PRIMARY KEY AUTOINCREMENT,
        Amount FLOAT,
        "From" TEXT NOT NULL,
        "To" TEXT NOT NULL,
        Rate FLOAT,
        Converted_amount FLOAT)
""")

conn.commit()
