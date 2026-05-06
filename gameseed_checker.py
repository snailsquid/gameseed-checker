import socket
import threading
import sys
import webview
from pathlib import Path

from backend import app as flask_app

if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys._MEIPASS)
else:
    BASE_DIR = Path(__file__).parent


def get_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


def start_flask(port):
    flask_app.run(host='127.0.0.1', port=port, debug=False, use_reloader=False)


class Api:
    def open_file_dialog(self):
        window = webview.windows[0]
        result = window.create_file_dialog(
            webview.FileDialog.OPEN,
            file_types=['CSV files (*.csv)']
        )
        return result


if __name__ == '__main__':
    port = get_free_port()

    flask_thread = threading.Thread(target=start_flask, args=(port,), daemon=True)
    try:
        flask_thread.start()
    except Exception as e:
        print(f"Flask startup error: {e}")
        sys.exit(1)

    window = webview.create_window(
        'GAMESEED 2026 — Participant Checker',
        f'http://127.0.0.1:{port}',
        width=960,
        height=640,
        min_size=(820, 540),
        js_api=Api()
    )

    webview.start()