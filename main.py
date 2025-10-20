from fastapi import FastAPI, HTTPException, Depends
from typing import Annotated, AsyncGenerator,List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import models
from schemas import QuestionCreate, QuestionResponse, ChoiceResponse, ChoiceBase, VerificationResult
from database import AsyncSessionLocal, create_db_and_tables
from sqlalchemy import select, update, delete,func

app = FastAPI()

# garante a criacao das tabelas antes de comecar as requisicoes, chamando a def que foi criada na database.py,
@app.on_event("startup")
async def on_startup():
    await create_db_and_tables() 

#pega uma sessao assincrona no bd e garante o fechamento indepedente do que ocorra
async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as db:
        yield db

# faz com que o fastapi use o get_async_db em cada requisição, assim que as rotas recebem a sessao do bd, annotated serve para nao precisar escrever todo o comando sempre que for chamado
db_depedency = Annotated[AsyncSession, Depends(get_async_db)]

#lista todas questoes do bd
@app.get("/questao/listar/", response_model=List[QuestionResponse])
async def listar_todas_questoes(db: db_depedency):

    stmt = (
        select(models.Questions)
        .options(selectinload(models.Questions.choices)) 
    )
    
    result = await db.execute(stmt)
    
    questions = result.scalars().unique().all()
    
    if not questions:
        raise HTTPException(status_code=404, detail="Nenhuma questao encontrada no bd.")
        
    return questions

# Busca uma questao por ID
@app.get("/questao/buscar/{question_id}", response_model=QuestionResponse)
async def ler_questao(question_id: int, db: db_depedency):
    
    stmt = (
        select(models.Questions)
        .options(selectinload(models.Questions.choices))
        .where(models.Questions.id == question_id)
    )
    
    result = await db.execute(stmt)
    question = result.scalar_one_or_none()
    
    if not question:
        raise HTTPException(status_code=404, detail="questao nao encontrada")
        
    return question


# Busca items de uma questao
@app.get("/questao/items/{question_id}", response_model=List[ChoiceResponse])
async def ler_item(question_id: int, db: db_depedency):
    
    stmt = select(models.Choices).where(models.Choices.question_id == question_id)
    
    result = await db.execute(stmt)
    choices = result.scalars().all() 
    
    if not choices:
        raise HTTPException(status_code=404, detail="item nao encontrado pra essa questao")
        
    return choices


# A rota pra devolver 5 questoes aleatorias para o quiz
@app.get("/questao/quiz/aleatorio", response_model=List[QuestionResponse])
async def get_questoes_aleatorias(db: db_depedency, count: int = 5):
    
    stmt = (
        select(models.Questions)
        .options(selectinload(models.Questions.choices)) 
        .order_by(func.random())
        .limit(count)
    )
    
    result = await db.execute(stmt)
    
    questions = result.scalars().all()
    
    if not questions:
        raise HTTPException(status_code=404, detail="Nenhuma questão encontrada no banco de dados.")
        
    return questions

#retorna se o item esta correto ou nao
@app.get("/questao/{choice_id}/verificar", response_model=VerificationResult)
async def verificar_resposta(choice_id: int, db: db_depedency):
    
    stmt = select(models.Choices).where(models.Choices.id == choice_id)

    result = await db.execute(stmt)
    choice = result.scalar_one_or_none()
    
    if not choice:
        raise HTTPException(status_code=404, detail=f"Opção com ID {choice_id} não encontrada.")
        
    is_correct = choice.is_correct
    
    if is_correct:
        message = "Resposta Correta! Parabéns."
    else:
        message = "Resposta Incorreta. Tente novamente."
        
    return VerificationResult(
        choice_id=choice_id,
        is_correct=is_correct,
        message=message
    )

# Cria a questao e as Opções
@app.post("/questao/criar", response_model=QuestionResponse)
async def criar_questao(question: QuestionCreate, db: db_depedency):
    
    db_question = models.Questions(question_text=question.question_text)
    
    for choice in question.choices:
        db_question.choices.append(
            models.Choices(choice_text=choice.choice_text, is_correct=choice.is_correct)
        )
        
    db.add(db_question)
    
    await db.commit()
    await db.refresh(db_question, attribute_names=['choices']) 
    
    return db_question

#rota para atualizar uma questao
@app.post("/questao/{question_id}/update", response_model=QuestionResponse)
async def atualizar_questao(question_id: int, question_data: QuestionCreate, db: db_depedency):
    
    stmt = (
        select(models.Questions)
        .options(selectinload(models.Questions.choices))
        .where(models.Questions.id == question_id)
    )
    result = await db.execute(stmt)
    db_question = result.scalar_one_or_none()
    
    if not db_question:
        raise HTTPException(status_code=404, detail="questao nao encontrada")
        
    if question_data.question_text is not None:
        db_question.question_text = question_data.question_text
        
    # Atualiza as opções,Deleta e Insere Novas
    if question_data.choices is not None:
        
        await db.execute(
            delete(models.Choices).where(models.Choices.question_id == question_id)
        )
        
        for choice in question_data.choices:
            db_question.choices.append(
                models.Choices(
                    choice_text=choice.choice_text, 
                    is_correct=choice.is_correct
                )
            )
    
    await db.commit()
    await db.refresh(db_question, attribute_names=['choices'])
    
    return db_question

# Rota para atualizar uma opção
@app.post("/questao/items/{choice_id}/update", response_model=ChoiceResponse)
async def atualizar_item(choice_id: int, choice_data: ChoiceBase, db: db_depedency):
    
    stmt_select = select(models.Choices).where(models.Choices.id == choice_id)
    result = await db.execute(stmt_select)
    db_choice = result.scalar_one_or_none()
    
    if not db_choice:
        raise HTTPException(status_code=404, detail="item nao encontrado")
    
    db_choice.choice_text = choice_data.choice_text
    db_choice.is_correct = choice_data.is_correct
    
    await db.commit()
    await db.refresh(db_choice)
    
    return db_choice

# Rota para deletar uma questao
@app.post("/questao/{question_id}/deletar")
async def deletar_questao(question_id: int, db: db_depedency):
    
    stmt = delete(models.Questions).where(models.Questions.id == question_id)
    
    # Executa a remocao e retorna o número de linhas excluídas
    result = await db.execute(stmt)
    
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="questao nao encontrada")
        
    await db.commit()
    
    return {"message": f"Questao com ID {question_id} foi excluída com sucesso."}

# Rota para deletar um item
@app.post("/items/{choice_id}/deletar")
async def deletar_item(choice_id: int, db: db_depedency):

    stmt = delete(models.Choices).where(models.Choices.id == choice_id)
    
    result = await db.execute(stmt)
    
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="item nao encontrado")
        
    await db.commit()
    
    return {"message": f"item com ID {choice_id} foi excluída com sucesso."}
