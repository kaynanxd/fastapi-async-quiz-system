from pydantic import BaseModel
from typing import List,Optional


#a clase schemas garante a padronizacao dos dados de entrada e saida da nossa api, garantindo que não exponha dados internos do SQLAlchemy que não deveriam ser públicos.

# SCHEMAS DE ENTRADA 

class ChoiceBase(BaseModel):
    choice_text: str
    is_correct: bool

class QuestionCreate(BaseModel):
    question_text: str
    choices: List[ChoiceBase]

class QuestionUpdate(BaseModel):
    question_text: Optional[str] = None
    choices: Optional[List[ChoiceBase]] = None

class VerificationResult(BaseModel):
    choice_id: int
    is_correct: bool
    message: str

# SCHEMAS DE SAÍDA 

class ChoiceResponse(ChoiceBase):
    id: int
    #esse config que permite que você retorne o objeto ORM e o FastAPI o converta automaticamente para JSON.
    class Config:
        from_attributes = True

class QuestionResponse(BaseModel):
    id: int
    question_text: str
    choices: List[ChoiceResponse]
    
    class Config:
        from_attributes = True

        

