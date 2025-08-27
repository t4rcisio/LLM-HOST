#!/bin/bash

# Atualiza o sistema
sudo apt update && sudo apt upgrade -y

# Instala Python 3.13 venv
sudo apt install python3.13-venv -y

# Instala Git
sudo apt install git -y

# Instala Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Clona o repositório
git clone https://github.com/t4rcisio/LLM-HOST.git
cd LLM-HOST/

# Cria e ativa o ambiente virtual
python3 -m venv venv
source venv/bin/activate

# Instala dependências
pip3 install --upgrade pip
pip3 install -r requirements.txt

# Baixa o modelo
ollama pull qwen3:1.7b

# Roda o script principal
nohup python main.py &
