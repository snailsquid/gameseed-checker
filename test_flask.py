"""
Minimal Flask server test - demonstrates Flask port=0 auto-assignment.
"""

from flask import Flask
import threading
import socket
import time
import requests


def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


def create_app():
    app = Flask(__name__)

    @app.route('/')
    def index():
        return 'OK'

    return app


def test_port_zero_works():
    app = Flask(__name__)

    @app.route('/')
    def index():
        return 'OK'

    error_msg = [None]

    def run():
        try:
            app.run(host='127.0.0.1', port=0, threaded=True, use_reloader=False)
        except Exception as e:
            error_msg[0] = str(e)

    t = threading.Thread(target=run, daemon=True)
    t.start()
    time.sleep(0.5)

    return error_msg[0] is None


def test_capture_port_pattern():
    app = create_app()
    port = find_free_port()

    def run():
        app.run(host='127.0.0.1', port=port, threaded=True, use_reloader=False)

    t = threading.Thread(target=run, daemon=True)
    t.start()
    time.sleep(0.5)

    try:
        resp = requests.get(f'http://127.0.0.1:{port}/')
        return resp.text == 'OK'
    except requests.exceptions.ConnectionError:
        return False


if __name__ == '__main__':
    print("Flask port=0 test")
    print("port=0 works:", test_port_zero_works())
    print("capture pattern:", test_capture_port_pattern())