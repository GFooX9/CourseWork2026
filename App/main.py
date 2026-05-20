import sys
from PyQt6.QtWidgets import QApplication
from App.UI.main_window import MainWindow


def main():
    # Создаем экземпляр приложения Qt
    app = QApplication(sys.argv)

    # Инициализируем и отображаем наше главное лавандово-графитовое окно
    window = MainWindow()
    window.show()

    # Запускаем бесконечный цикл обработки событий Qt
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
