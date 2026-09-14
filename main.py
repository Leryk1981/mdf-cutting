import sys
import threading
import webbrowser

from packer.config import setup_logging


def main():
    """Launch the browser UI, retaining Tkinter behind ``--legacy-tk``."""
    setup_logging()
    if "--legacy-tk" in sys.argv:
        import tkinter as tk
        from packer.gui import CuttingAppGUI

        root = tk.Tk()
        CuttingAppGUI(root)
        root.mainloop()
        return

    import uvicorn
    from web_app import app

    url = "http://127.0.0.1:8765"
    threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    uvicorn.run(app, host="127.0.0.1", port=8765)


if __name__ == "__main__":
    main()
