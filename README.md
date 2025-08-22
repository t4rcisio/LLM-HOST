
# 🧠 API OLLAMA HOST

Uma API RESTful construída com **FastAPI** para hospedar e interagir com modelos via **Ollama**, com suporte a chamadas síncronas, assíncronas (streaming) e registro de uso.

---

## 📦 Requisitos

- Python 3.13.5+
- pip (gerenciador de pacotes Python)
- `ollama` instalado e rodando localmente
- Dependências listadas no `requirements.txt`

---

1. Crie um ambiente virtual e ative-o:

```bash
python -m venv venv
source venv/bin/activate     # Linux/macOS
venv\Scripts\activate      # Windows
```

2. Instale as dependências:

```bash
pip install -r requirements.txt
```

---

## 🚀 Execução

Execute o servidor FastAPI com:

```bash
python .\main.py
```


Execute o servidor FastAPI como serviço com:

```bash
python .\launcher.py
```

A aplicação será iniciada em:

```
http://127.0.0.1:5000
```

A documentação Swagger estará disponível em:

```
http://127.0.0.1:5000/docs
```

Ou a documentação ReDoc:

```
http://127.0.0.1:5000/redoc
```

---

## 📚 Endpoints

### 🔁 /api/v1/ai/models [GET]

Retorna a lista de modelos Ollama disponíveis no host.

**Exemplo de resposta:**
```json
["llama3", "qwen", "mistral", "custom-model"]
```

---

### 💬 /api/v1/ai/ask_sync [POST]

Envia uma pergunta e aguarda a resposta completa (modo síncrono).

**Body JSON:**
```json
{
  "agent": "llama3",
  "content": "Explique a teoria da relatividade.",
  "template": "Você é um assistente educado e técnico.",
  "user_key": "111111122",
  "project": "projeto1",
  "process_id": "001",
  "subprocess_id": "001"
}
```
user_key, project, process_id, subprocess_id são parâmetros opcionais.

**Resposta:**
```text
Texto completo da resposta gerada pelo modelo.
```

---

### 📡 /api/v1/ai/ask_async [POST]

Envia uma pergunta com resposta em streaming (modo assíncrono).

**Mesmo body JSON** do endpoint `/ask_sync`.

A resposta será transmitida em partes (`text/plain`) à medida que for gerada.

---

### 📊 /api/v1/admin/dashboard [GET]

Retorna os logs de uso dos modelos, incluindo tempo de resposta, tokens e identificadores de projeto/processo.

**Exemplo de resposta:**
```json
[
  {
    "date": "2025-08-04T11:05:00",
    "total_seconds": 1500000000,
    "total_tokens": 123,
    "input_tokens": 23,
    "output_tokens": 100,
    "model_name": "qwen",
    "input": [{"role": "user", "content": "exemplo"}],
    "output": "resposta gerada",
    "project": "projeto1",
    "process_id": "p001",
    "subprocess_id": "s001"
  }
]
```

---

## 🛠 Estrutura do Projeto

- `main.py`: ponto de entrada da aplicação
- `requirements.txt`: dependências do projeto
- `core/`: módulo com funções utilitárias, armazenamento e controle de uso
- `schema/`: módulo com os esquemas de input e output da api
- `api/`: módulo com a configuração dos endpoints

---

## 👤 Autor

tarcisio.b.prates