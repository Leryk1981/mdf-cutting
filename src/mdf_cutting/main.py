"""
Главный модуль приложения.

Запускает GUI приложение для оптимизации раскроя МДФ.
"""

import tkinter as tk

from mdf_cutting.ui.desktop_app import CuttingApp


def main():
    """Главная функция приложения."""
    root = tk.Tk()
    CuttingApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
