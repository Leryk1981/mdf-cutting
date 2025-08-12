import tkinter as tk

from packer.config import setup_logging
from packer.gui import CuttingAppGUI


def main():
    """Основная функция запуска приложения"""
    # Настраиваем логирование
    setup_logging()

    # Запускаем интерфейс
    root = tk.Tk()
    CuttingAppGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
