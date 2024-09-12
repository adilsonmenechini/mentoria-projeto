# Dockerfile
FROM python:3.10-slim

# Definindo variáveis de ambiente
ENV RABBITMQ_VHOST /
ENV RABBITMQ_HOST rabbitmq
ENV RABBITMQ_PASSWORD user
ENV RABBITMQ_USER user
ENV RABBITMQ_PORT 5672

RUN apt-get update -qq && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiando arquivos de requisitos
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiando o código da aplicação
COPY . .

# Comando para executar a aplicação
CMD ["python", "main.py"]