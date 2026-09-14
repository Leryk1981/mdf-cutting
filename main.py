import threading
import webbrowser

from packer.config import setup_logging


def main():
    """Launch the browser-based MDF cutting workspace."""
    setup_logging()
    import uvicorn
    from web_app import app

    url = "http://127.0.0.1:8765"
    threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    uvicorn.run(app, host="127.0.0.1", port=8765)


if __name__ == "__main__":
    main()
