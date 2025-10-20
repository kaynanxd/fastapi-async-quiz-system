from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.ext.declarative import declarative_base

from dotenv import load_dotenv
import os

#carrega o que esta no env
load_dotenv()
URL_DATABASE = os.getenv("DATABASE_URL") 
if not URL_DATABASE:
    raise ValueError("A variável de ambiente DATABASE_URL não foi definida.")

#aqui criamos o motor assincrono da nossa api
engine = create_async_engine(URL_DATABASE)
AsyncSessionLocal = async_sessionmaker(
    bind= engine, 
    class_= AsyncSession, 
    expire_on_commit= False
)

#Todos os modelos devem herdar desta Base para serem reconhecidos pelo SQLAlchemy
Base = declarative_base()

#garante que a estrutura do bd esteja criada e pronta para uso e chamado no inicio de main
async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)