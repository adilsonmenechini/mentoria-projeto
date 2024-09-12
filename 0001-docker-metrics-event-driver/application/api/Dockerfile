# Dockerfile
FROM python:3.10-slim

# Definindo o diretório de trabalho
WORKDIR /app

# Definindo variáveis de ambiente
ENV POSTGRES_HOST localhost
ENV POSTGRES_DB meu_projeto
ENV POSTGRES_USER postgres
ENV POSTGRES_PASSWORD admin
ENV POSTGRES_PORT 5432


RUN apt-get update -qq && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiando o arquivo de requisitos
COPY requirements.txt .

# Instalando as dependências
RUN pip install --no-cache-dir -r requirements.txt

# Copiando o código da aplicação
COPY . .

# Expondo a porta que o Uvicorn usará
EXPOSE 8000

# Comando para executar a aplicação
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]