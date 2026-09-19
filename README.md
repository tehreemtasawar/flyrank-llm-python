# Task Classifier API

Adds one endpoint, `POST /classify`, to an existing Task API. It sends a task's title to an LLM and returns a validated category, confidence score, and reason, never raw model text.

## Example

    curl -X POST http://localhost:8000/classify -H "Content-Type: application/json" -d "{\"title\":\"Buy milk\"}"

    {"category":"shopping","confidence":0.95,"reason":"Grocery shopping item"}

## Job Card

See `JOB-CARD.md`.

## Provider

OpenRouter, model `openrouter/free`. Environment variables needed: `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL` (see `.env.example`).

## Eval Score

Run with `python src/run_eval.py` after starting the server. Latest result: 8/8 correct, prompt version v1.

## Cost

One call uses roughly 150-250 tokens total. At 10,000 requests/day, this is approximately 1.5-2.5 million tokens/day, well within free-tier limits on OpenRouter's free models, though a paid model at scale would need this tracked against a real budget.

## What I'd Fix With More Time

Add caching for repeated identical titles, and expand the eval set to cover more ambiguous edge cases.