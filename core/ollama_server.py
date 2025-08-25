import os
import time
import socket
import subprocess
import requests
from contextlib import closing
from typing import Optional, Dict
from ollama import Client
import psutil
import signal

class OllamaQueue:
    def __init__(
        self,
        ports=None,
        host="127.0.0.1",
        models_dir: Optional[str] = None,
        http_timeout: float = 60.0,
    ):
        self.host = host
        self.ports = ports or [11434, 11435, 11436, 11437, 11438]
        self.models_dir = models_dir
        self.http_timeout = http_timeout


        if os.name == "nt":
            self.models_dir = f"C:\\Users\\{os.getlogin()}\\.ollama\\models"
        else:
            self.models_dir = f"/home/{os.getlogin()}/.ollama/models"


        print(os.listdir(self.models_dir))

        # {proc_id: {"PROCESS": Popen, "PORT": int, "CLIENT": Client}}
        self.processes: Dict[int, dict] = {}

    # ---------------- utilitários ----------------
    def _port_free(self, port: int) -> bool:
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
            s.settimeout(0.5)
            return s.connect_ex((self.host, port)) != 0

    def _health(self, port: int) -> bool:
        try:
            r = requests.get(f"http://{self.host}:{port}/api/tags", timeout=2)
            return r.status_code == 200
        except Exception:
            return False

    def _get_free_port(self) -> int:
        for port in self.ports:
            if self._port_free(port):
                return port
        raise RuntimeError("Nenhuma porta disponível")

    def _get_pid_from_port(self, port: int):
        for conn in psutil.net_connections(kind='inet'):
            if conn.laddr.port == port:
                return conn.pid
        return None

    # ---------------- ciclo de vida ----------------
    def start(self, wait_ready: float = 15.0):
        port = self._get_free_port()
        env = os.environ.copy()
        env["OLLAMA_HOST"] = f"{self.host}:{port}"
        if self.models_dir:
            os.makedirs(self.models_dir, exist_ok=True)
            env["OLLAMA_MODELS"] = self.models_dir

        self.ollama_logs_dir = ".\\ollama_logs"
        os.makedirs(self.ollama_logs_dir, exist_ok=True)

        log_file = f"{self.ollama_logs_dir}\\ollama_{port}.log"
        log_fh = open(log_file, "ab")

        creationflags = 0
        if os.name == "nt":
            creationflags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS

        proc = subprocess.Popen(
            ["ollama", "serve"],
            env=env,
            stdout=log_fh,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            creationflags=creationflags,
            close_fds=False,
        )

        proc_id = proc.pid
        self.processes[proc_id] = {"PROCESS": proc, "PORT": port, "CLIENT": None, "ID": proc_id}

        # aguarda healthcheck
        deadline = time.time() + wait_ready
        while time.time() < deadline:
            if proc.poll() is not None:
                raise RuntimeError(f"ollama serve saiu prematuramente (código {proc.returncode}). Veja {log_file}")
            if self._health(port):
                client = Client(host=f"http://{self.host}:{port}", timeout=self.http_timeout)
                self.processes[proc_id]["CLIENT"] = client
                return self.processes[proc_id]
            time.sleep(0.5)

        raise TimeoutError(f"Ollama não ficou pronto em {wait_ready}s. Veja logs em {log_file}")

    def ensure_model(self, proc_id: int, model: str, force_pull: bool = False):
        client = self.processes[proc_id].get("CLIENT")
        if not client:
            raise RuntimeError("Servidor não iniciado")

        if not force_pull:
            try:
                client.show(model)
                return
            except Exception:
                pass

        for status in client.pull(model, stream=True):
            pass  # logs do servidor já mostram detalhes

    def chat(self, proc_id: int, model: str, content: str, stream: bool = True) -> str:
        client = self.processes[proc_id].get("CLIENT")
        if not client:
            raise RuntimeError("Servidor não iniciado")

        self.ensure_model(proc_id, model)

        if stream:
            chunks = client.chat(model=model, messages=[{"role": "user", "content": content}], stream=True)
            text = []
            for part in chunks:
                piece = part["message"]["content"]
                text.append(piece)
                print(piece, end="", flush=True)
            print()
            return "".join(text)
        else:
            resp = client.chat(model=model, messages=[{"role": "user", "content": content}])
            return resp.message.content

    def stop(self, proc_id: int):
        if proc_id not in self.processes:
            return

        proc_info = self.processes[proc_id]
        proc = proc_info.get("PROCESS")
        port = proc_info.get("PORT")

        if proc:
            try:
                parent = psutil.Process(proc.pid)
                for child in parent.children(recursive=True):
                    try:
                        print(f"Matando servidor real pid={child.pid}")
                        child.kill()
                    except:
                        pass
                print(f"Matando launcher pid={parent.pid}")
                parent.kill()
            except psutil.NoSuchProcess:
                pass

        pid = self._get_pid_from_port(port)
        if pid:
            try:
                os.kill(pid, signal.SIGTERM)
            except Exception:
                pass

        del self.processes[proc_id]

    def is_alive(self, proc_id: int) -> bool:
        if proc_id not in self.processes:
            return False
        proc_info = self.processes[proc_id]
        proc = proc_info.get("PROCESS")
        port = proc_info.get("PORT")
        if not proc or proc.poll() is not None:
            return False
        return self._health(port)