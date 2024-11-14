import sys

from PyQt6 import uic
from PyQt6.QtWidgets import (QApplication,
                             QMainWindow,
                             QTableWidgetItem,
                             QHeaderView,
                             QDialog)

import datetime
import requests
import yfinance as yf
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import change_db, get_data


# Основной класс
class CurrencyConverter(QMainWindow):
    def __init__(self):
        super().__init__()

        # Инициализация основного интерфейса
        self.analyseWindow = None
        uic.loadUi("mainUI.ui", self)
        self.setWindowTitle("Конвертер валют")

        # Добавление валют для выбора
        self.convertFrom.addItems(['USD', 'EUR', 'RUB', 'JPY', 'CNY'])
        self.convertTo.addItems(['RUB', 'USD', 'EUR', 'JPY', 'CNY'])

        self.convertButton.clicked.connect(self.convert_currency)
        self.clearButton.clicked.connect(self.clear_fields)
        self.historyButton.clicked.connect(self.showHistoryWindow)
        self.analyseButton.clicked.connect(self.showAnalyseWindow)

        self.historyWindow = None
        self.historyData = {}
        self.db = change_db.historyDB()

    # Функция для очистки полей
    def clear_fields(self):
        self.convertBox.clear()
        self.convertedBox.clear()
        self.rateBox.clear()

    # Основная функция конвертации
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

            # Вычисление курса и конвертация
            fromUSD = data["rates"][f"{currencyFrom}"]
            toUSD = data["rates"][f"{currencyTo}"]
            ratio = toUSD / fromUSD

            convertedAmount = amount * ratio

            # Вывод результата
            self.convertedBox.setText(f'{amount} {currencyFrom} = {convertedAmount:.2f} {currencyTo}')
            self.rateBox.setText(f'1 {currencyFrom} = {ratio:.2f} {currencyTo}')

            # Сохранение данных в историю
            self.historyData = {"Amount": amount,
                                "From": currencyFrom,
                                "To": currencyTo,
                                "Rate": f"{ratio:.2f}",
                                "Converted Amount": f"{convertedAmount:.2f}"}

            self.db.add(self.historyData)

        except Exception as e:
            print(f"Ошибка: {e}")

    # Функции для вывода дополнительных окон
    def showHistoryWindow(self):
        self.historyWindow = HistoryWindow(self.db)
        self.historyWindow.show()
        self.historyWindow.raise_()

    def showAnalyseWindow(self):
        self.analyseWindow = AnalyseWindow()
        self.analyseWindow.show()
        self.analyseWindow.raise_()


# Класс окна истории
class HistoryWindow(QDialog):
    def __init__(self, db, parent=None):
        super().__init__(parent)

        # Инициализация интерфейса для окна истории
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

    # Функция для обновления истории
    def update_history(self):
        self.historyData = get_data.get()
        self.load_table()

    # Функция для очистки истории
    def clear_history(self):
        self.db.clear()
        self.update_history()


# Класс окна анализа
class AnalyseWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Инициализация интерфейса для окна анализа
        uic.loadUi("analyseUI.ui", self)
        self.setWindowTitle("Анализ курса")

        # Добавление валют для выбора
        self.fromCurrency.addItems(['USD', 'EUR', 'RUB', 'JPY', 'CNY'])
        self.toCurrency.addItems(['RUB', 'USD', 'EUR', 'JPY', 'CNY'])

        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        self.graphLayout.addWidget(self.canvas)

        self.dayButton.clicked.connect(self.showDay)
        self.weekButton.clicked.connect(self.showWeek)
        self.monthButton.clicked.connect(self.showMonth)
        self.yearButton.clicked.connect(self.showYear)
        self.setTimeButton.clicked.connect(self.setTime)

    # Функция для построения графика
    def setGraph(self, timeStart, timeEnd, hour=False):
        fromCurrency = self.fromCurrency.currentText()
        toCurrency = self.toCurrency.currentText()

        ticker = f"{fromCurrency}{toCurrency}=X"

        try:
            if hour:
                data = yf.download(ticker, start=timeStart, end=timeEnd, interval="1h")
            else:
                data = yf.download(ticker, start=timeStart, end=timeEnd, interval="1d")

            if data.empty:
                print("Данные не найдены. Проверьте правильность ввода валют или измените интервал анализа.")
                return

            self.figure.clear()
            ax = self.figure.add_subplot(111)

            # Построение графика
            ax.plot(data.index, data['Close'])
            ax.set_title(f'Изменение курса {fromCurrency} к {toCurrency}')
            ax.set_xlabel('Дата')
            ax.set_ylabel('Курс')
            ax.grid(True)
            self.canvas.draw()

            api_key = '5de6ce78176646539decff349cd90fb1'
            url = f'https://openexchangerates.org/api/latest.json?app_id={api_key}'
            response = requests.get(url)
            data = response.json()

            fromCurrency = data["rates"][f"{fromCurrency}"]
            toCurrency = data["rates"][f"{toCurrency}"]
            ratio = toCurrency / fromCurrency

            self.currentRatio.setText(str(ratio))
        except Exception as e:
            print(f"Ошибка:{e}")

    # Предустановленные временные промежутки
    def showDay(self):
        delta = datetime.timedelta(days=1)
        timeEnd = datetime.datetime.today()
        timeStart = timeEnd - delta

        timeStart = str(timeStart)[:10]
        timeEnd = str(timeEnd)[:10]

        self.setGraph(timeStart, timeEnd, hour=True)

    def showWeek(self):
        delta = datetime.timedelta(days=7)
        timeEnd = datetime.datetime.today()
        timeStart = timeEnd - delta

        timeStart = str(timeStart)[:10]
        timeEnd = str(timeEnd)[:10]

        self.setGraph(timeStart, timeEnd, hour=True)

    def showMonth(self):
        delta = datetime.timedelta(days=30)
        timeEnd = datetime.datetime.today()
        timeStart = timeEnd - delta

        timeStart = str(timeStart)[:10]
        timeEnd = str(timeEnd)[:10]

        self.setGraph(timeStart, timeEnd)

    def showYear(self):
        delta = datetime.timedelta(days=365)
        timeEnd = datetime.datetime.today()
        timeStart = timeEnd - delta

        timeStart = str(timeStart)[:10]
        timeEnd = str(timeEnd)[:10]

        self.setGraph(timeStart, timeEnd)

    # Выбор пользовательского промежутка времени
    def setTime(self):
        self.setTimeWindow = SetTimeWindow(self)
        self.setTimeWindow.show()
        self.setTimeWindow.raise_()


class SetTimeWindow(QDialog):
    def __init__(self, analyseWindow, parent=None):
        super().__init__(parent)
        uic.loadUi("setTimeUI.ui", self)

        self.setWindowTitle("Выберите промежуток времени")

        self.analyseWindow = analyseWindow

        today = datetime.datetime.today()
        self.startDate.setDate(today - datetime.timedelta(days=30))
        self.endDate.setDate(today)

        self.applyButton.clicked.connect(self.apply)
        self.cancelButton.clicked.connect(self.close)

    def apply(self):
        timeStart = self.startDate.date().toPyDate()
        timeEnd = self.endDate.date().toPyDate()

        self.analyseWindow.setGraph(timeStart, timeEnd)
        self.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    converter = CurrencyConverter()
    converter.show()
    sys.exit(app.exec())
