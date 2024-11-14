import sys

from PyQt6 import uic
from PyQt6.QtWidgets import (QApplication,
                             QWidget,
                             QMainWindow,
                             QTableWidgetItem,
                             QHeaderView,
                             QDialog)

import requests
import change_db, get_data


class CurrencyConverter(QMainWindow):
    def __init__(self):
        super().__init__()

        # Инициализация интерфейса
        uic.loadUi("mainUI.ui", self)
        self.setWindowTitle("Конвертер валют")

        # Добавление валют для выбора
        self.convertFrom.addItems(['USD', 'EUR', 'RUB', 'JPY', 'CNY'])
        self.convertTo.addItems(['USD', 'EUR', 'RUB', 'JPY', 'CNY'])

        self.convertButton.clicked.connect(self.convert_currency)
        self.clearButton.clicked.connect(self.clear_fields)
        self.historyButton.clicked.connect(self.show_history)

        self.historyWindow = None
        self.historyData = {}
        self.db = change_db.historyDB()

    # Функция очистки полей
    def clear_fields(self):
        self.convertBox.clear()
        self.convertedBox.clear()
        self.rateBox.clear()

    #  Функция конвертации
    def convert_currency(self):
        if not self.convertBox.text():
            print("Введите сумму для конвертации.")
            return

        try:
            amount = float(self.convertBox.text())
            currencyFrom = self.convertFrom.currentText()
            currencyTo = self.convertTo.currentText()

            # Подключение к OpenExchangeRates с помощью API
            api_key = '5de6ce78176646539decff349cd90fb1'
            url = f'https://openexchangerates.org/api/latest.json?app_id={api_key}'

            response = requests.get(url)
            data = response.json()

            # Вычисление курса
            fromUSD = data["rates"][f"{currencyFrom}"]
            toUSD = data["rates"][f"{currencyTo}"]
            ratio = toUSD / fromUSD

            convertedAmount = amount * ratio

            # Вывод результата
            self.convertedBox.setText(f'{amount} {currencyFrom} = {convertedAmount:.2f} {currencyTo}')
            self.rateBox.setText(f'1 {currencyFrom} = {ratio:.2f} {currencyTo}')

            self.historyData = {"Amount": amount,
                                "From": currencyFrom,
                                "To": currencyTo,
                                "Rate": f"{ratio:.2f}",
                                "Converted Amount": f"{convertedAmount:.2f}"}

            self.db.add(self.historyData)

        except Exception as e:
            print(f"Ошибка: {e}")

    def show_history(self):
        self.historyWindow = HistoryWindow(self.db)
        self.historyWindow.show()
        self.historyWindow.raise_()


class HistoryWindow(QDialog):
    def __init__(self, db, parent=None):
        super().__init__(parent)

        # Загрузка интерфейса для окна истории
        uic.loadUi("historyUI.ui", self)
        self.setWindowTitle("История конвертаций")

        self.historyData = get_data.get()
        self.db = db

        self.load_table()

        self.clearHistoryButton.clicked.connect(self.clear_history)
        self.updateHistoryButton.clicked.connect(self.update_history)

    # Загрузка данных из базы данных в таблицу
    def load_table(self):
        try:
            titles = ["Количество", "Из", "В", "Курс", "Результат"]
            self.tableWidget.setColumnCount(len(titles))
            self.tableWidget.setHorizontalHeaderLabels(titles)

            header = self.tableWidget.horizontalHeader()
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)

            self.tableWidget.setRowCount(0)
            for i, row in enumerate(self.historyData):
                self.tableWidget.setRowCount(self.tableWidget.rowCount() + 1)
                for j, elem in enumerate(row):
                    self.tableWidget.setItem(i, j, QTableWidgetItem(str(elem)))

            self.tableWidget.resizeColumnsToContents()

        except Exception as e:
            print(f"Не удалось загрузить историю: {e}")

    # Обновление истории
    def update_history(self):
        self.historyData = get_data.get()
        self.load_table()

    # Очистка истории
    def clear_history(self):
        self.db.clear()
        self.update_history()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    converter = CurrencyConverter()
    converter.show()
    sys.exit(app.exec())