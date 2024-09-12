import pika
import json
import time
import random
import os
import logging
from faker import Faker

# Inicializando o Faker
fake = Faker()

# Configurando o logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configurações de conexão com RabbitMQ
RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'localhost')
RABBITMQ_PORT = int(os.getenv('RABBITMQ_PORT', 5672))
RABBITMQ_USER = os.getenv('RABBITMQ_USER', 'guest')
RABBITMQ_PASSWORD = os.getenv('RABBITMQ_PASSWORD', 'guest')

# Parâmetros de conexão
conn_params = pika.ConnectionParameters(
    host=RABBITMQ_HOST,
    port=RABBITMQ_PORT,
    credentials=pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD),
    connection_attempts=3,  # Número de tentativas de conexão
    retry_delay=5  # Tempo entre as tentativas de conexão
)

def connect_to_rabbitmq():
    """Estabelece conexão com RabbitMQ com tentativas de reconexão."""
    while True:
        try:
            connection = pika.BlockingConnection(conn_params)
            channel = connection.channel()
            logging.info("Conexão estabelecida com sucesso.")
            return connection, channel
        except pika.exceptions.AMQPConnectionError as e:
            logging.error(f"Erro ao conectar ao RabbitMQ: {e}. Tentando reconectar em 5 segundos...")
            time.sleep(5)

def setup_channel(channel):
    """Configura a exchange e a fila no RabbitMQ."""
    channel.exchange_declare(exchange='my_topic_exchange', exchange_type='topic', durable=True)
    channel.queue_declare(queue='produtos', durable=True)
    channel.queue_bind(exchange='my_topic_exchange', queue='produtos', routing_key='my.routing.key')
    logging.info("Exchange e fila configuradas.")

def gerar_produto():
    """Gera um produto fake usando Faker."""
    return {
        "id": random.randint(1, 1000),
        "nome": fake.name(),
        "preco": round(random.uniform(1.0, 100.0), 2),
        "quantidade": random.randint(1, 100)
    }

def run_producer(channel):
    """Produz e envia mensagens para o RabbitMQ."""
    for _ in range(10):
        produto = gerar_produto()
        channel.basic_publish(exchange='my_topic_exchange', routing_key='my.routing.key', body=json.dumps(produto))
        logging.info(f'Sent: {produto}')
        time.sleep(1)

def main():
    connection, channel = connect_to_rabbitmq()
    setup_channel(channel)
    try:
        run_producer(channel)
    except KeyboardInterrupt:
        logging.warning('Execução interrompida pelo usuário.')
    except Exception as e:
        logging.error(f'Erro durante a execução do produtor: {e}')
    finally:
        if not connection.is_closed:
            connection.close()
            logging.info('Conexão fechada.')

if __name__ == "__main__":
    main()
