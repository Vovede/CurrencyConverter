import sys

from PyQt6 import uic
from PyQt6.QtWidgets import (QApplication,
                             QMainWindow, )

import requests


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

        self.data = []

    # Функция очистки полей
    def clear_fields(self):
        self.convertBox.clear()
        self.convertedBox.clear()
        self.rateBox.clear()

    #  Функция конвертации
    def convert_currency(self):
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
            rate = toUSD / fromUSD

            convertedAmount = amount * rate

            # Вывод результата
            self.convertedBox.setText(f'{amount} {currencyFrom} = {convertedAmount:.2f} {currencyTo}')
            self.rateBox.setText(f'1 {currencyFrom} = {rate:.2f} {currencyTo}')

        except Exception as e:
            print(f"Ошибка: {e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    converter = CurrencyConverter()
    converter.show()
    sys.exit(app.exec())
