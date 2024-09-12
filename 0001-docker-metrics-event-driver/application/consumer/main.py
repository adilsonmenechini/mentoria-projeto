import pika
import json
import psycopg2
import os
import time
import logging

# Configurando o logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configurações de conexão com PostgreSQL
psql_user = os.getenv('POSTGRES_USER', 'postgres')
psql_password = os.getenv('POSTGRES_PASSWORD', 'admin')
psql_db = os.getenv('POSTGRES_DB', 'meu_projeto')
psql_host = os.getenv('POSTGRES_HOST', 'localhost')
psql_port = int(os.getenv('POSTGRES_PORT', 5432))
psql_connect = f"dbname={psql_db} user={psql_user} password={psql_password} host={psql_host} port={psql_port}"

def connect_to_postgresql():
    """Tenta conectar ao PostgreSQL com tentativas de reconexão."""
    while True:
        try:
            conn = psycopg2.connect(psql_connect)
            logging.info("Conexão estabelecida com o PostgreSQL.")
            return conn
        except psycopg2.OperationalError:
            logging.warning("Tentando conectar ao PostgreSQL novamente em 5 segundos...")
            time.sleep(5)

def create_table(cursor):
    """Cria a tabela 'produtos' no PostgreSQL se ela não existir."""
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS produtos (
        id SERIAL PRIMARY KEY,
        nome VARCHAR(100),
        preco DECIMAL,
        quantidade INT
    );
    """)

def connect_to_rabbitmq():
    """Estabelece conexão com RabbitMQ."""
    rabbitmq_host = os.getenv('RABBITMQ_HOST', 'localhost')
    rabbitmq_port = int(os.getenv('RABBITMQ_PORT', 15000))
    credentials = pika.PlainCredentials(
        username=os.getenv('RABBITMQ_USER', 'guest'),
        password=os.getenv('RABBITMQ_PASSWORD', 'guest')
    )
    conn_params = pika.ConnectionParameters(
        host=rabbitmq_host,
        port=rabbitmq_port,
        credentials=credentials,
        heartbeat=600,  # 10 minutos de heartbeat
    )
    while True:
        try:
            connection = pika.BlockingConnection(conn_params)
            logging.info("Conexão estabelecida com o RabbitMQ.")
            return connection
        except (pika.exceptions.AMQPConnectionError, pika.exceptions.StreamLostError) as e:
            logging.error(f"Erro ao conectar ao RabbitMQ: {e}. Tentando reconectar em 5 segundos...")
            time.sleep(5)

def persist_to_postgresql(cursor, produto):
    """Persiste o produto recebido no PostgreSQL."""
    cursor.execute("""
    INSERT INTO produtos (id, nome, preco, quantidade) 
    VALUES (%s, %s, %s, %s)
    """, (produto['id'], produto['nome'], produto['preco'], produto['quantidade']))

def callback(ch, method, properties, body):
    """Callback para processar mensagens recebidas do RabbitMQ."""
    produto = json.loads(body)
    logging.info(f'Received: {produto}')
    try:
        persist_to_postgresql(cursor, produto)
        conn.commit()
        logging.info("Produto persistido no PostgreSQL.")
    except Exception as e:
        logging.error(f"Erro ao persistir no PostgreSQL: {e}")
        conn.rollback()

def main():
    global conn, cursor, connection, channel
    conn = connect_to_postgresql()
    cursor = conn.cursor()
    create_table(cursor)
    conn.commit()
    
    connection = connect_to_rabbitmq()
    channel = connection.channel()
    channel.queue_declare(queue='produtos', durable=True)
    channel.basic_consume(queue='produtos', on_message_callback=callback, auto_ack=True)

    logging.info('Waiting for messages. To exit press CTRL+C')
    try:
        while True:
            try:
                channel.start_consuming()
            except pika.exceptions.StreamLostError:
                logging.warning("Conexão com RabbitMQ perdida. Tentando reconectar...")
                connection = connect_to_rabbitmq()
                channel = connection.channel()
                channel.queue_declare(queue='produtos', durable=True)
                channel.basic_consume(queue='produtos', on_message_callback=callback, auto_ack=True)
    except KeyboardInterrupt:
        logging.warning('Execução interrompida pelo usuário.')
    finally:
        if connection.is_open:
            connection.close()
        if conn:
            cursor.close()
            conn.close()
        logging.info('Conexões fechadas.')

if __name__ == "__main__":
    main()
