import os
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from enum import Enum
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

class Category(str, Enum):
    shopping = "shopping"
    work = "work"
    health = "health"
    personal = "personal"
    other = "other"

class ClassifyRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)

class ClassifyResponse(BaseModel):
    category: Category
    confidence: float = Field(..., ge=0.0, le=1.0)
    reason: str

@app.post("/classify")
def classify(req: ClassifyRequest):
    if os.environ.get("LLM_STUB") == "1":
        return ClassifyResponse(category=Category.other, confidence=0.5, reason="Stub response").model_dump()

    return {"error": "not implemented yet"}