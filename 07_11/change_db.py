import sqlite3

conn = sqlite3.connect('bd.db')
cursor = conn.cursor()


class historyDB():
    def __init__(self):
        self.conn = sqlite3.connect('bd.db')
        self.cursor = self.conn.cursor()

    def add(self, data):
        self.cursor.execute("""
            INSERT INTO history (Amount, "From", "To", Rate, Converted_amount)
            VALUES (?, ?, ?, ?, ?)
        """, (data["Amount"], data["From"], data["To"], data["Rate"], data["Converted Amount"]))
        self.conn.commit()

    def clear(self):
        self.cursor.execute("""DELETE FROM history""")
        self.conn.commit()
