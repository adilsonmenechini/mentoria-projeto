from fastapi import FastAPI, HTTPException, status
from psycopg2 import connect, OperationalError, sql, pool
from pydantic import BaseModel, Field
import os
import time
import logging

app = FastAPI()

# Configurações de conexão com PostgreSQL
psql_user = os.getenv('POSTGRES_USER', 'postgres')
psql_password = os.getenv('POSTGRES_PASSWORD', 'admin')
psql_db = os.getenv('POSTGRES_DB', 'meu_projeto')
psql_host = os.getenv('POSTGRES_HOST', 'localhost')  # Adicionado host
psql_port = int(os.getenv('POSTGRES_PORT', 5432))
psql_connect = {
    "dbname": psql_db,
    "user": psql_user,
    "password": psql_password,
    "host": psql_host,
    "port": psql_port
}

# Configuração do logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Criação de um pool de conexões
conn_pool = None
while True:
    try:
        conn_pool = pool.SimpleConnectionPool(1, 10, **psql_connect)
        if conn_pool:
            logger.info(f"Pool de conexões criado com sucesso {psql_connect}")
            break
    except OperationalError as e:
        logger.error(f"Tentando conectar ao PostgreSQL novamente em 5 segundos... Erro: {e}")
        time.sleep(5)

# Fechar o pool de conexões na saída
@app.on_event("shutdown")
def close_connection_pool():
    if conn_pool:
        conn_pool.closeall()
        logger.info("Pool de conexões fechado.")

# Modelo de dados para produtos
class Produto(BaseModel):
    nome: str
    preco: float = Field(gt=0, description="O preço deve ser maior que zero")
    quantidade: int = Field(ge=0, description="A quantidade não pode ser negativa")

# Função auxiliar para obter conexão do pool
def get_db_connection():
    try:
        conn = conn_pool.getconn()
        if conn:
            return conn
    except OperationalError as e:
        logger.error(f"Erro ao obter conexão: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro de conexão com o banco de dados")

# Rota para listar todos os produtos
@app.get("/produtos")
async def listar_produtos():
    conn = get_db_connection()
    if conn is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro ao obter conexão com o banco de dados.")
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, nome, preco, quantidade FROM produtos")
            produtos = cursor.fetchall()
        return [{"id": produto[0], "nome": produto[1], "preco": produto[2], "quantidade": produto[3]} for produto in produtos]
    except Exception as e:
        logger.error(f"Erro ao listar produtos: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro ao listar produtos: {str(e)}")
    finally:
        conn_pool.putconn(conn)

# Rota para criar um novo produto
@app.post("/produtos", status_code=status.HTTP_201_CREATED)
async def criar_produto(produto: Produto):
    conn = get_db_connection()
    if conn is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro ao obter conexão com o banco de dados.")
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                sql.SQL("INSERT INTO produtos (nome, preco, quantidade) VALUES (%s, %s, %s) RETURNING id"),
                (produto.nome, produto.preco, produto.quantidade)
            )
            produto_id = cursor.fetchone()[0]
            conn.commit()
        return {**produto.dict(), "id": produto_id}
    except Exception as e:
        logger.error(f"Erro ao criar produto: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro ao criar produto: {str(e)}")
    finally:
        conn_pool.putconn(conn)

# Rota para atualizar um produto existente
@app.put("/produtos/{id}")
async def atualizar_produto(id: int, produto: Produto):
    conn = get_db_connection()
    if conn is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro ao obter conexão com o banco de dados.")
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                sql.SQL("UPDATE produtos SET nome=%s, preco=%s, quantidade=%s WHERE id=%s"),
                (produto.nome, produto.preco, produto.quantidade, id)
            )
            if cursor.rowcount == 0:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Produto {id} não encontrado.")
            conn.commit()
        return {"message": f"Produto {id} atualizado com sucesso."}
    except Exception as e:
        logger.error(f"Erro ao atualizar produto: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro ao atualizar produto: {str(e)}")
    finally:
        conn_pool.putconn(conn)

# Rota para excluir um produto
@app.delete("/produtos/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def excluir_produto(id: int):
    conn = get_db_connection()
    if conn is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro ao obter conexão com o banco de dados.")    
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql.SQL("DELETE FROM produtos WHERE id=%s"), (id,))
            if cursor.rowcount == 0:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Produto {id} não encontrado.")
            conn.commit()
        return {"message": f"Produto {id} excluído com sucesso."}
    except Exception as e:
        logger.error(f"Erro ao excluir produto: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro ao excluir produto: {str(e)}")
    finally:
        conn_pool.putconn(conn)
