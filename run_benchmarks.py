import requests
import json
import time

strategies = ["vector-similarity", "hybrid-search", "reranking", "multi-query"]
url = "http://localhost:8000/api/v1/evaluations/run"

results = {}

for strategy in strategies:
    print(f"Running evaluation for {strategy}...")
    start_time = time.time()
    resp = requests.post(
        url,
        json={"strategy": strategy, "dataset_name": "benchmark", "top_k": 5}
    )
    if resp.status_code == 200:
        data = resp.json()
        print(f"Success! Hit@1: {data.get('hit_at_1')}, MRR: {data.get('mrr')}")
        with open(f"data/benchmarks/{strategy}.json", "w") as f:
            json.dump(data, f, indent=2)
        results[strategy] = data
    else:
        print(f"Failed for {strategy}: {resp.status_code} {resp.text}")

print("Benchmarking completed.")
