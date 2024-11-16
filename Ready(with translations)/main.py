import sys
import os

from PyQt6 import uic
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import (QApplication,
                             QMainWindow,
                             QTableWidgetItem,
                             QHeaderView,
                             QDialog)

import datetime
import requests
import json
import yfinance as yf
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import change_db
import get_data


# Основной класс
class CurrencyConverter(QMainWindow):
    def __init__(self):
        super().__init__()

        # Инициализация основного интерфейса
        self.analyseWindow = None
        uic.loadUi("mainUI.ui", self)

        self.translation_manager = TranslationManager()
        self.translation_manager.subscribe(self)
        self.translation_manager.change_language()

        # Добавление валют для выбора
        self.convertFrom.addItems(['USD', 'EUR', 'RUB', 'JPY', 'CNY'])
        self.convertTo.addItems(['RUB', 'USD', 'EUR', 'JPY', 'CNY'])

        self.convertButton.clicked.connect(self.convert_currency)
        self.clearButton.clicked.connect(self.clear_fields)
        self.historyButton.clicked.connect(self.showHistoryWindow)
        self.analyseButton.clicked.connect(self.showAnalyseWindow)
        self.settingsButton.clicked.connect(self.showSettingsWindow)

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

    def retranslate_ui(self):
        self.setWindowTitle(self.translation_manager.get_translation("titlem"))
        self.convertBox.setText("")
        QTimer.singleShot(50, lambda: self.convertBox.setPlaceholderText(
            self.translation_manager.get_translation("convertBox")))
        self.label_2.setText(self.translation_manager.get_translation("label_from"))
        self.label.setText(self.translation_manager.get_translation("label_to"))
        self.label_4.setText(self.translation_manager.get_translation("label_ratio"))
        self.label_3.setText(self.translation_manager.get_translation("label_result"))
        self.convertButton.setText(self.translation_manager.get_translation("convertButton"))
        self.settingsButton.setText(self.translation_manager.get_translation("settingsButton"))
        self.analyseButton.setText(self.translation_manager.get_translation("analyseButton"))
        self.historyButton.setText(self.translation_manager.get_translation("historyButton"))
        self.clearButton.setText(self.translation_manager.get_translation("clearButton"))

    # Функции для вывода дополнительных окон
    def showHistoryWindow(self):
        self.historyWindow = HistoryWindow(self.db)
        self.historyWindow.show()
        self.historyWindow.raise_()

    def showAnalyseWindow(self):
        self.analyseWindow = AnalyseWindow()
        self.analyseWindow.show()
        self.analyseWindow.raise_()

    def showSettingsWindow(self):
        self.settingsWindow = SettingsWindow()
        self.settingsWindow.show()
        self.settingsWindow.raise_()


# Класс окна истории
class HistoryWindow(QDialog):
    def __init__(self, db):
        super().__init__()

        # Инициализация интерфейса для окна истории
        uic.loadUi("historyUI.ui", self)

        self.translation_manager = TranslationManager()
        self.translation_manager.subscribe(self)
        self.translation_manager.change_language()
        self.language = self.translation_manager.load_settings()

        self.historyData = get_data.get()
        self.db = db

        self.load_table()

        self.clearHistoryButton.clicked.connect(self.clear_history)
        self.updateHistoryButton.clicked.connect(self.update_history)

    # Загрузка данных из базы данных в таблицу
    def load_table(self):
        try:
            if self.language == "ru":
                titles = ["Количество", "Из", "В", "Курс", "Результат"]
            else:
                titles = ["Amount", "From", "To", "Ratio", "Result"]
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

    def retranslate_ui(self):
        self.setWindowTitle(self.translation_manager.get_translation("titleh"))
        self.updateHistoryButton.setText(self.translation_manager.get_translation("updateHistoryButton"))
        self.clearHistoryButton.setText(self.translation_manager.get_translation("clearHistoryButton"))


# Класс окна анализа
class AnalyseWindow(QDialog):
    def __init__(self):
        super().__init__()

        # Инициализация интерфейса для окна анализа
        uic.loadUi("analyseUI.ui", self)

        self.translation_manager = TranslationManager()
        self.translation_manager.subscribe(self)
        self.translation_manager.change_language()

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
            ax.set_title(self.tr(f'Изменение курса {fromCurrency} к {toCurrency}'))
            ax.set_xlabel(self.tr('Дата'))
            ax.set_ylabel(self.tr('Курс'))
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

    def retranslate_ui(self):
        self.setWindowTitle(self.translation_manager.get_translation("titlea"))
        self.label.setText(self.translation_manager.get_translation("label_from"))
        self.label_2.setText(self.translation_manager.get_translation("label_to"))
        self.label_3.setText(self.translation_manager.get_translation("label_currentRatio"))
        self.dayButton.setText(self.translation_manager.get_translation("dayButton"))
        self.weekButton.setText(self.translation_manager.get_translation("weekButton"))
        self.monthButton.setText(self.translation_manager.get_translation("monthButton"))
        self.yearButton.setText(self.translation_manager.get_translation("yearButton"))
        self.setTimeButton.setText(self.translation_manager.get_translation("setTimeButton"))


class SetTimeWindow(QDialog):
    def __init__(self, analyseWindow):
        super().__init__()
        uic.loadUi("setTimeUI.ui", self)

        self.translation_manager = TranslationManager()
        self.translation_manager.subscribe(self)
        self.translation_manager.change_language()

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

    def retranslate_ui(self):
        self.setWindowTitle(self.translation_manager.get_translation("titlei"))
        self.label.setText(self.translation_manager.get_translation("label"))
        self.label_2.setText(self.translation_manager.get_translation("label_2"))
        self.applyButton.setText(self.translation_manager.get_translation("applyButton"))
        self.cancelButton.setText(self.translation_manager.get_translation("cancelButton"))


class SettingsWindow(QDialog):
    def __init__(self):
        super().__init__()

        uic.loadUi("settingsUI.ui", self)

        self.translation_manager = TranslationManager()
        self.translation_manager.subscribe(self)
        self.translation_manager.change_language()

        self.languages.addItems(['Русский', 'English'])

        self.cancelChangesButton.clicked.connect(self.close)
        self.applyChangesButton.clicked.connect(self.apply)

    def apply(self):
        selected_language = self.languages.currentText()
        if selected_language == "Русский":
            language_code = "ru"
        else:
            language_code = "en"
        self.translation_manager.save_settings(language_code)
        self.translation_manager.change_language()
        self.close()

    def retranslate_ui(self):
        self.setWindowTitle(self.translation_manager.get_translation("titles"))
        self.label_5.setText(self.translation_manager.get_translation("label_changeLanguage"))
        self.applyChangesButton.setText(self.translation_manager.get_translation("applyChangesButton"))
        self.cancelChangesButton.setText(self.translation_manager.get_translation("cancelChangesButton"))


class TranslationManager:
    _instance = None
    _subscribers = []

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.current_language = "ru"
            cls._instance.translations = {}
            cls._instance.load_settings()
            cls._instance.load_translation(cls._instance.current_language)
        return cls._instance

    def load_settings(self):
        with open("settings.txt", "r", encoding="utf-8") as f:
            return f.read().split("=")[1].strip()

    def save_settings(self, current_language):
        with open("settings.txt", "w", encoding="utf-8") as f:
            f.write(f"language={current_language}")

    def load_translation(self, language):
        try:
            with open(f"translations/{language}.json", "r", encoding="utf-8") as trf:
                self.translations = json.load(trf)
        except FileNotFoundError:
            print("Файл перевода не найден.")
            self.translations = {}

    def get_translation(self, key):
        return self.translations.get(key, key)

    def change_language(self):
        language = self.load_settings()
        self.load_translation(language)
        self.notify_subscribers()

    def subscribe(self, window):
        if window not in self._subscribers:
            self._subscribers.append(window)

    def notify_subscribers(self):
        for window in self._subscribers:
            window.retranslate_ui()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    converter = CurrencyConverter()
    converter.show()
    sys.exit(app.exec())
