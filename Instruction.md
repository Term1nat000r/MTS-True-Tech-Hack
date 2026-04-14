# 🐳 Docker + Ollama + Qwen2.5-Coder:7B Setup Guide (Cross-Platform)

Это инструкция по установке Docker, Ollama, загрузке модели **qwen2.5-coder:7b**, проверке работы и запуску **реального проекта через Docker Compose + FastAPI + Ollama**.

---

# 📦 1. Установка Docker (Windows / macOS / Linux)

## Windows

Скачать Docker Desktop:
[https://www.docker.com/products/docker-desktop/](https://www.docker.com/products/docker-desktop/)

Проверка:

```bash
docker --version
docker run hello-world
```

---

## 🍎 macOS

```bash
brew install --cask docker
```

или Docker Desktop:
[https://www.docker.com/products/docker-desktop/](https://www.docker.com/products/docker-desktop/)

Проверка:

```bash
docker --version
docker run hello-world
```

---

## 🐧 Linux

```bash
sudo apt update
sudo apt install -y ca-certificates curl gnupg lsb-release
```

```bash
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
```

```bash
echo \
"deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
$(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
```

```bash
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

---

# 🧠 2. Установка Ollama

## Windows / macOS

[https://ollama.com/download](https://ollama.com/download)

## Linux

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

Проверка:

```bash
ollama --version
```

---

# 🤖 3. Установка модели

```bash
ollama pull qwen2.5-coder:7b
```

Запуск:

```bash
ollama run qwen2.5-coder:7b
```

Проверка API:

```bash
curl http://localhost:11434/api/generate -d '{
  "model": "qwen2.5-coder:7b",
  "prompt": "Write a hello world in C++"
}'
```

---

# 🐳 4. Docker проект

## 📁 Структура проекта

```
project/
│── Dockerfile
│── docker-compose.yml
│── requirements.txt
│── src/
│   └── api/main.py
│── data/
```

---

# 🚀 7. Запуск проекта

## 7.1 Сборка и запуск

```bash
docker-compose up --build
```

## 7.2 Запуск в фоне

```bash
docker-compose up -d --build
```

## 7.3 Остановка

```bash
docker-compose down
```

---

# ✅ Готово
