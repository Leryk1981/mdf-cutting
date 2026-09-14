import os
import threading
import webbrowser

from packer.config import setup_logging


def main():
    """Launch the browser-based MDF cutting workspace."""
    setup_logging()
    import uvicorn
    from web_app import app

    port = int(os.environ.get("MDF_CUTTING_PORT", "8765"))
    url = f"http://127.0.0.1:{port}"
    threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=port,
        log_config=None,
        access_log=False,
    )


if __name__ == "__main__":
    main()
