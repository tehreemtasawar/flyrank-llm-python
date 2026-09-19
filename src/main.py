import os
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from enum import Enum
from dotenv import load_dotenv
from openai import OpenAI

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

def call_model(title: str) -> str:
    with open("prompts/classify-v1.md", "r", encoding="utf-8") as f:
        system_prompt = f.read()

    client = OpenAI(base_url=os.environ["LLM_BASE_URL"], api_key=os.environ["LLM_API_KEY"])
    res = client.chat.completions.create(
        model=os.environ["LLM_MODEL"],
        temperature=0,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": title}
        ],
    )
    return res.choices[0].message.content

@app.post("/classify")
def classify(req: ClassifyRequest):
    if os.environ.get("LLM_STUB") == "1":
        return ClassifyResponse(category=Category.other, confidence=0.5, reason="Stub response").model_dump()

    raw = call_model(req.title)
    return {"raw": raw}