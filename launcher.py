# launcher.py
import threading
import subprocess
import sys
import webbrowser

import pystray
from PIL import Image

from core.configs import settings
url = 'http://127.0.0.1' + ":" +settings.PORT

uvicorn_process = None

def create_image():
    return Image.open("./sources/logo_llm_host.ico")

def start_uvicorn():
    global uvicorn_process
    uvicorn_process = subprocess.Popen([sys.executable, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", settings.PORT, "--workers", "5"])

def open_server_url(icon, item):
    webbrowser.open(url)


def open_documentation_url(icon, item):
    webbrowser.open(url+"/redoc")

def open_documentation_url_docs(icon, item):
    webbrowser.open(url+"/docs")

def stop_uvicorn(icon, item):
    global uvicorn_process
    if uvicorn_process:
        uvicorn_process.terminate()
        uvicorn_process.wait()
    icon.stop()

def setup_tray():
    icon = pystray.Icon("AI HOST")
    icon.icon = create_image()
    icon.menu = pystray.Menu(
        pystray.MenuItem("Abrir no navegador", open_server_url),
        pystray.MenuItem("Abrir redoc no navegador", open_documentation_url),
        pystray.MenuItem("Abrir docs no navegador", open_documentation_url_docs),
        pystray.MenuItem("Encerrar servidor", stop_uvicorn)
    )
    icon.run()

if __name__ == "__main__":
    t = threading.Thread(target=start_uvicorn, daemon=True)
    t.start()
    setup_tray()
