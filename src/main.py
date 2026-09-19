import os
import json
import re
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ValidationError
from enum import Enum
from dotenv import load_dotenv
from openai import OpenAI
from datetime import datetime, timezone

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

def extract_json(text: str) -> dict:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("No JSON object found in model output")
    return json.loads(match.group())

def call_model_with_message(title: str, extra_message: str = None) -> str:
    with open("prompts/classify-v1.md", "r", encoding="utf-8") as f:
        system_prompt = f.read()

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": title}
    ]
    if extra_message:
        messages.append({"role": "user", "content": extra_message})

    client = OpenAI(base_url=os.environ["LLM_BASE_URL"], api_key=os.environ["LLM_API_KEY"])
    res = client.chat.completions.create(
        model=os.environ["LLM_MODEL"],
        temperature=0,
        messages=messages,
    )
    return res.choices[0].message.content

def quarantine(title, error, prompt_version="v1"):
    os.makedirs("logs", exist_ok=True)
    entry = {
        "input": title,
        "error": str(error),
        "prompt_version": prompt_version,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    with open("logs/quarantine.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

@app.post("/classify")
def classify(req: ClassifyRequest):
    if os.environ.get("LLM_STUB") == "1":
        return ClassifyResponse(category=Category.other, confidence=0.5, reason="Stub response").model_dump()

    raw = call_model_with_message(req.title)
    try:
        parsed = extract_json(raw)
        validated = ClassifyResponse(**parsed)
        return validated.model_dump()
    except (ValueError, ValidationError, json.JSONDecodeError) as e:
        repair_msg = f"Your previous answer was rejected for this reason: {e}. Return only corrected JSON matching the schema."
        raw2 = call_model_with_message(req.title, extra_message=repair_msg)
        try:
            parsed2 = extract_json(raw2)
            validated2 = ClassifyResponse(**parsed2)
            return validated2.model_dump()
        except (ValueError, ValidationError, json.JSONDecodeError) as e2:
            quarantine(req.title, e2)
            return JSONResponse(status_code=422, content={"error": "Could not get a valid classification"})