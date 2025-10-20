from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship 
from database import Base

#aq usamos o sqlalchemy para traduzir as classes Python em tabelas no PostgreSQL

class Questions(Base):
    __tablename__="questions"

    id = Column(Integer,primary_key=True,index=True)
    question_text=Column(String, index=True)

    #aqui e setado e relacionamento entre a classe questions e a choices, o backpopulates serve pra conseguir acessar um elemento atraves do outro
    choices = relationship("Choices", back_populates="question") 


class Choices(Base):
    __tablename__="choices"

    id=Column(Integer,primary_key=True, index=True)
    choice_text=Column(String,index=True)
    is_correct=Column(Boolean,default=True)
    #o cascade faz com que se uma linha da tabela pai for apagada todas as linhas filhas devem ser apagadas tbm
    question_id = Column(Integer,ForeignKey("questions.id",ondelete="CASCADE")) 
    #relacionamento inverso do que foi feito acima
    question = relationship("Questions", back_populates="choices")
