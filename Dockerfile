# Dockerfile para FastAPI + dependências do projeto
FROM python:3.11-slim

# Diretório de trabalho
WORKDIR /app

# Instala dependências do sistema (opcional, para SQLite, MQTT, etc)
RUN apt-get update && apt-get install -y gcc libsqlite3-dev && rm -rf /var/lib/apt/lists/*

# Copia requirements.txt e instala dependências Python
COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copia o código da aplicação
COPY ./app /app/app

# Comando padrão (pode ser sobrescrito pelo docker-compose)
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
