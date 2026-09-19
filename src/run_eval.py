import json
import requests

with open("evals/cases.json") as f:
    cases = json.load(f)

correct = 0
failed = []

for case in cases:
    resp = requests.post("http://localhost:8000/classify", json={"title": case["title"]})
    data = resp.json()
    actual = data.get("category")
    if actual == case["expected_category"]:
        correct += 1
    else:
        failed.append({"title": case["title"], "expected": case["expected_category"], "actual": actual})

print(f"{correct}/{len(cases)} correct")
print(json.dumps(failed, indent=2))