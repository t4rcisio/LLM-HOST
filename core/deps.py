import subprocess
import requests
import time

from openai import OpenAI
from core.configs import Settings


_model_client = None  # cache do modelo



BASE_URL = "http://localhost:8000"

def check_vllm():
    try:
        # Verifica o health endpoint
        health = requests.get(f"{BASE_URL}/health", timeout=5)
        if health.status_code == 200:
            print("✅ vLLM está rodando!")
        else:
            print("⚠️ vLLM respondeu, mas com erro:", health.text)
            return

        # Lista os modelos carregados
        models = requests.get(f"{BASE_URL}/v1/models", timeout=5)
        if models.status_code == 200:
            data = models.json()
            print("📦 Modelos carregados:")
            for m in data.get("data", []):
                print(" -", m.get("id"))
        else:
            print("⚠️ Erro ao listar modelos:", models.text)

    except requests.exceptions.ConnectionError:
        print("❌ Não consegui conectar ao vLLM. Ele está rodando na porta 8000?")
    except Exception as e:
        print("⚠️ Erro inesperado:", e)

def get_model():
    """
    Dependência que inicializa o cliente OpenAI/vLLM
    apenas uma vez e retorna sempre o mesmo objeto.
    """

    global _model_client
    if _model_client is None:
        _model_client = OpenAI(api_key=Settings.VLLM_API_KEY, base_url=Settings.VLLM_API_BASE)
    return _model_client

def is_ollama_ready():
    try:
        res = requests.get("http://127.0.0.1:11434")
        return res.status_code == 200
    except:
        return False

def start_ollama():
    if is_ollama_ready():
        print("Ollama já está rodando.")
        return "OK"

    print("Iniciando Ollama...")
    try:
        subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
    except Exception as e:
        print("Erro ao iniciar Ollama:", e)
        return "ERRO"

    for i in range(15):
        if is_ollama_ready():
            print("Ollama iniciado com sucesso!")
            return "OK"
        time.sleep(1)

    print("Timeout ao iniciar Ollama")
    return "TIMEOUT"


def decodeResponse(res):

   try:
      return res.decode('utf-8')
   except:
       return res


check_vllm()