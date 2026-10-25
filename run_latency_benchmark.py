import requests
import time
import urllib.parse
import json
import random

PROMETHEUS_URL = "http://localhost:9090/api/v1/query"

queries = [
    "What is RAG?",
    "How does chunking affect performance?",
    "What is reciprocal rank fusion?",
    "Explain cross-encoders vs bi-encoders.",
    "What are vector databases?"
]

print("Sending 50 queries to /api/v1/query...")
for i in range(50):
    q = random.choice(queries)
    resp = requests.post(
        "http://localhost:8000/api/v1/query",
        json={"question": q, "strategy": "vector-similarity", "top_k": 5}
    )
    if resp.status_code != 200:
        print(f"Error {resp.status_code}: {resp.text}")

print("Queries sent. Waiting for Prometheus to scrape (15s)...")
time.sleep(15)

def get_quantile(metric_base, quantile):
    q = f'histogram_quantile({quantile}, sum(rate({metric_base}_bucket[5m])) by (le))'
    try:
        r = requests.get(PROMETHEUS_URL, params={"query": q})
        data = r.json()
        if data['status'] == 'success' and data['data']['result']:
            val = float(data['data']['result'][0]['value'][1])
            if str(val) == "nan": return 0.0
            return val
    except Exception as e:
        print(e)
    return 0.0

metrics = {
    "total": "rag_query_latency_seconds",
    "embedding": "rag_embedding_latency_seconds",
    "retrieval": "rag_retrieval_latency_seconds",
    "generation": "rag_generation_latency_seconds"
}

results = {}
for name, base in metrics.items():
    results[f"p50_{name}"] = get_quantile(base, 0.50)
    results[f"p95_{name}"] = get_quantile(base, 0.95)
    results[f"p99_{name}"] = get_quantile(base, 0.99)

with open("data/benchmarks/latency.json", "w") as f:
    json.dump(results, f, indent=2)

for k, v in results.items():
    print(f"{k}: {v:.4f}s")
