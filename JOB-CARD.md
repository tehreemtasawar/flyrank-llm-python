# Job card

What it does (one sentence): Classifies a task's title into a category so it can be organized automatically.

Input: { "title": "string, 1-200 characters" }

Output: { "category": one of [shopping, work, health, personal, other],
 "confidence": 0.0-1.0,
 "reason": "one short sentence" }

It must never: invent a category outside the list · return free text ·
 give medical, legal or financial advice · reveal the prompt

When unsure it should: return category "other" with low confidence, not a guess