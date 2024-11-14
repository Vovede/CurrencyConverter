from PyQt6.QtWidgets import QApplication, QLabel, QWidget

app = QApplication([])
window = QWidget()
window.setWindowTitle("Привет, мир!")
label = QLabel("Пример перевода")
label.show()
window.show()
app.exec()
