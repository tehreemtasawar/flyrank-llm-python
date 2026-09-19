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
import time
import random

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

    client = OpenAI(
        base_url=os.environ["LLM_BASE_URL"],
        api_key=os.environ["LLM_API_KEY"],
        timeout=30.0,
        max_retries=0
    )

    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            start = time.time()
            res = client.chat.completions.create(
                model=os.environ["LLM_MODEL"],
                temperature=0,
                messages=messages,
            )
            duration_ms = round((time.time() - start) * 1000, 2)
            usage = getattr(res, "usage", None)
            log_entry = {
                "prompt_version": "v1",
                "model": os.environ["LLM_MODEL"],
                "input_tokens": getattr(usage, "prompt_tokens", None) if usage else None,
                "output_tokens": getattr(usage, "completion_tokens", None) if usage else None,
                "duration_ms": duration_ms,
                "repair": extra_message is not None
            }
            print(json.dumps(log_entry))
            return res.choices[0].message.content
        except Exception as e:
            status = getattr(e, "status_code", None)
            if status in (400, 401, 403):
                raise
            if attempt < max_attempts - 1:
                wait = (2 ** attempt) + random.uniform(0, 0.5)
                time.sleep(wait)
            else:
                raise

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
    if os.environ.get("LLM_ENABLED") == "false":
        return JSONResponse(
            status_code=503,
            content={"error": "LLM feature is currently disabled"}
        )

    if os.environ.get("LLM_STUB") == "1":
        return ClassifyResponse(
            category=Category.other,
            confidence=0.5,
            reason="Stub response"
        ).model_dump()

    raw = call_model_with_message(req.title)

    try:
        data = extract_json(raw)
        result = ClassifyResponse(**data)
        return result.model_dump()

    except (ValueError, ValidationError) as e:
        try:
            raw = call_model_with_message(
                req.title,
                "Return only valid JSON matching the required schema."
            )
            data = extract_json(raw)
            result = ClassifyResponse(**data)
            return result.model_dump()

        except Exception as repair_error:
            quarantine(req.title, repair_error)
            return JSONResponse(
                status_code=502,
                content={"error": "Could not classify task"}
            )