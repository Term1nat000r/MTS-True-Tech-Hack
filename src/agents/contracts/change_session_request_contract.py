# Контракт вывода от агента-уточнителя
from typing import List

from pydantic import BaseModel

class Payload(BaseModel):
    session_id: str

class ChangeSessionRequest(BaseModel):
    payload: Payload