from pydantic import BaseModel
from typing import List

class Message(BaseModel):
    role: str
    content: str

class ConversationCreate(BaseModel):
    user_id: str

class MessageCreate(BaseModel):
    conversation_id: str
    role: str
    content: str

class ConversationRename(BaseModel):
    conversation_id: str
    title: str 