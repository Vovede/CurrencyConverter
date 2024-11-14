import sqlite3

conn = sqlite3.connect("bd.db")
cursor = conn.cursor()


def get():
    cursor.execute("""SELECT Amount, "From", "To", Rate, Converted_amount FROM history """)
    res = cursor.fetchall()
    return res
