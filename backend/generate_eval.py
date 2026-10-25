import json
import uuid

questions_data = [
    ("What is Retrieval-Augmented Generation (RAG)?", "rag_fundamentals.txt"),
    ("Why is RAG used instead of relying solely on LLM parameters?", "rag_fundamentals.txt"),
    ("What are the 5 key steps of the RAG process?", "rag_fundamentals.txt"),
    ("What happens during the Document Ingestion step?", "rag_fundamentals.txt"),
    ("How is the query processed in RAG?", "rag_fundamentals.txt"),
    ("What metric is commonly used to compare query embeddings and document embeddings?", "rag_fundamentals.txt"),
    ("What happens during the Context Assembly step?", "rag_fundamentals.txt"),
    ("How does the Generation step in RAG ensure the response is grounded?", "rag_fundamentals.txt"),
    ("What is the main purpose of vector databases?", "rag_fundamentals.txt"),
    ("How do vector databases differ from traditional databases?", "rag_fundamentals.txt"),
    ("What is Approximate Nearest Neighbor (ANN) search used for?", "rag_fundamentals.txt"),
    ("What distance metrics are supported by vector databases?", "rag_fundamentals.txt"),
    ("Name some scalable indexing structures used in vector databases.", "rag_fundamentals.txt"),
    ("Which PostgreSQL extension provides vector similarity search capabilities?", "rag_fundamentals.txt"),
    ("What is document chunking?", "rag_fundamentals.txt"),
    ("Why is chunk size important for RAG performance?", "rag_fundamentals.txt"),
    ("What happens if chunks are too large?", "rag_fundamentals.txt"),
    ("What happens if chunks are too small?", "rag_fundamentals.txt"),
    ("Why is overlap between chunks useful?", "rag_fundamentals.txt"),
    ("What is fixed-size chunking?", "rag_fundamentals.txt"),
    ("What is recursive splitting based on?", "rag_fundamentals.txt"),
    ("What is semantic chunking?", "rag_fundamentals.txt"),
    ("What is document-aware chunking?", "rag_fundamentals.txt"),
    ("How is cosine similarity calculated?", "rag_fundamentals.txt"),
    ("What is the range of cosine similarity values?", "rag_fundamentals.txt"),
    ("What does a cosine similarity of 0 indicate?", "rag_fundamentals.txt"),
    ("What do higher cosine similarity scores indicate?", "rag_fundamentals.txt"),
    ("Why is cosine similarity invariant to vector magnitude?", "rag_fundamentals.txt"),
    ("What does dense retrieval use to capture semantic meaning?", "rag_fundamentals.txt"),
    ("What methods does sparse retrieval use?", "rag_fundamentals.txt"),
    ("What are the characteristics of sparse vectors in sparse retrieval?", "rag_fundamentals.txt"),
    ("What is the main difference between dense and sparse retrieval regarding exact keyword matches?", "rag_fundamentals.txt"),
    ("Which retrieval method excels at exact keyword matching?", "rag_fundamentals.txt"),
    ("What do hybrid retrieval approaches combine?", "rag_fundamentals.txt"),
    ("What is the purpose of reranking in a RAG system?", "rag_fundamentals.txt"),
    ("What type of model is commonly used for reranking?", "rag_fundamentals.txt"),
    ("How does the reranking process work step-by-step?", "rag_fundamentals.txt"),
    ("What is the difference between cross-encoders and bi-encoders?", "rag_fundamentals.txt"),
    ("Why are cross-encoders more suitable for reranking small candidate sets rather than initial retrieval?", "rag_fundamentals.txt"),
    ("What is Reciprocal Rank Fusion (RRF)?", "rag_fundamentals.txt"),
    ("How is the RRF score calculated for a document?", "rag_fundamentals.txt"),
    ("What is the typical value for the constant k in the RRF formula?", "rag_fundamentals.txt"),
    ("What are the advantages of using RRF?", "rag_fundamentals.txt"),
    ("Why doesn't RRF need score normalization?", "rag_fundamentals.txt"),
    ("What does the Hit@K metric measure?", "rag_fundamentals.txt"),
    ("What is Mean Reciprocal Rank (MRR)?", "rag_fundamentals.txt"),
    ("Why does MRR reward retrieving relevant documents at higher positions?", "rag_fundamentals.txt"),
    ("What is the goal of multi-query retrieval?", "rag_fundamentals.txt"),
    ("How does multi-query retrieval generate alternative queries?", "rag_fundamentals.txt"),
    ("What types of queries benefit most from multi-query retrieval?", "rag_fundamentals.txt")
]

cases = []
for i, (q, src) in enumerate(questions_data):
    cases.append({
        "case_id": f"benchmark_{i+1:03d}",
        "question": q,
        "expected_source": src,
        "relevant_chunk_ids": []
    })

with open("data/evaluation/benchmark.json", "w") as f:
    json.dump({"cases": cases}, f, indent=2)
print(f"Generated {len(cases)} cases.")
